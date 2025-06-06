#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import math
import os.path
import random
import re

import numpy as np

from struct import pack, unpack
from operator import attrgetter

from libs.colorrange import *
from libs.prim import *
from libs.animation import *
from libs.gifparser import *
from libs.gifwriter import *

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

config = None

def picio_set_config(config_in):
    global config
    config = config_in

#width to bytes
def w2b(w):
    return (w+15)//16*2

#check to see if a file is an IFF file
def pic_type(filename):
    retval = ""

    try:
        pic_file = open(filename,'rb')
        header = pic_file.read(4)
        if header == b'FORM':
            pic_file.seek(8)
            ilbm_header = pic_file.read(4)
            if ilbm_header == b'ILBM':
                retval = "ILBM"
            elif ilbm_header == b'PBM ':
                retval = "PBM"
            elif ilbm_header == b'ANIM':
                retval = "ANIM"
        elif header == b'GIF8':
            retval = "GIF"
        pic_file.close()
    except:
        retval = "NONE"

    return retval

#planar to chunky using numpy
def p2c(planes_in, surf_array):
    #get dimensions of bitplanes
    h, nPlanes, w = planes_in.shape

    #loop through 8 bits
    for bit in range(7,-1,-1):
        #pick off one bit through all the planes
        planes = np.copy(planes_in)
        for i in range(nPlanes):
            planes[:,i,:] &= 1<<bit

            #shift bits into proper place for the plane
            shift = bit - i
            if shift > 0:
                planes[:,i,:] >>= shift
            elif shift < 0:
                planes[:,i,:] <<= -shift

        #flatten shifted bits into bytes
        flatten = np.zeros((h,w), dtype=np.uint8)
        for i in range(nPlanes):
            flatten |= planes[:,i,:]

        #copy flattened bytes into surface 8 apart
        surf_array[7-bit::8,:] = flatten.transpose()

#decode byterun1 ILBM encoding
def byterun_decode(bytes_in, bytes_out):
    #LOOP until produced the desired number of bytes
    bin=0
    bout=0
    while bout < len(bytes_out) and bin < len(bytes_in):
        # Read the next source byte into n
        n = bytes_in[bin] - 256 if bytes_in[bin] > 127 else bytes_in[bin]
        # SELECT n FROM
        if n >= 0:
            # [0..127] => copy the next n+1 bytes literally
            bytes_out[bout:bout+n+1] = bytes_in[bin+1:bin+n+2]
            bin += n+2
            bout += n+1
        elif n > -128:
            # [-1..-127] => replicate the next byte -n+1 times
            n = -n
            bytes_out[bout:bout+n+1] = [bytes_in[bin+1]] * (n+1)
            bin += 2
            bout += n+1
        else:
            # -128 => no operation
            bin += 1

#read bytes into bitmap
def decode_ilbm_body(body_bytes, compression, nPlanes, surf_array):
    w = len(surf_array)
    h = len(surf_array[0])

    if compression:
        raw_array = bytearray(w2b(w)*h*nPlanes)
        byterun_decode(body_bytes, raw_array)
        planes_in = np.asarray(raw_array,dtype=np.uint8).reshape(h,nPlanes,w2b(w))
    else:
        planes_in = np.frombuffer(body_bytes,dtype=np.uint8).reshape(h,nPlanes,w2b(w))

    p2c(planes_in, surf_array)

#read bytes into bitmap
def decode_pbm_body(body_bytes, compression, nPlanes, surf_array):
    w = len(surf_array)
    h = len(surf_array[0])

    if compression:
        raw_array = bytearray(w*h)
        byterun_decode(body_bytes, raw_array)
        surf_array[:,:] = np.asarray(raw_array,dtype=np.uint8).reshape(h,w).transpose()
    else:
        surf_array[:,:] = np.frombuffer(body_bytes,dtype=np.uint8).reshape(h,w).transpose()

class Chunk(object):
    """This class implements IFF chunk reading"""
    def __init__(self, iff_file):
        self.iff_file = iff_file
        self.name = iff_file.read(4)
        if len(self.name) == 0:
            raise EOFError
        len_bytes = iff_file.read(4)
        if len(len_bytes) == 0:
            raise EOFError
        len_tuple = unpack(">I", len_bytes)
        self.length = len_tuple[0]

    def getname(self):
        return self.name

    def read(self):
        retval = self.iff_file.read(self.length)
        if self.length & 1 == 1:
            self.iff_file.seek(1, 1) #make sure word-aligned
        return retval

    def skip(self):
        self.iff_file.seek(self.length, 1)
        if self.length & 1 == 1:
            self.iff_file.seek(1, 1) #make sure word-aligned

#read in an IFF file
def load_iff(filename, config, ifftype, pic=None, is_brush=False):
    cranges = []
    display_mode = -1
    try:
        iff_file = open(filename,'rb')
        iff_file.seek(12)
        chunk = Chunk(iff_file)

        while chunk:
            if chunk.getname() == b'CRNG':
                #create color range from chunk
                crng_bytes = chunk.read()
                (pad, rate, flags, low, high) = unpack(">HHHBB", crng_bytes)
                if len(cranges) < 6:
                    cranges.append(colorrange(rate,flags,low,high))
            elif chunk.getname() == b'CCRT':
                #Graphicraft color range
                ccrt_bytes = chunk.read()
                (dir, low, high, sec, micro, pad) = unpack(">hBBiih", ccrt_bytes)
                flags = 1
                if dir > 0:
                    flags |= 2
                cranges.append(colorrange(273067//(micro//1000+sec*1000),flags,low,high))
            elif chunk.getname() == b'CAMG':
                #Amiga graphics mode
                camg_bytes = chunk.read()
                display_mode = unpack(">I", camg_bytes)[0]
                if display_mode & config.MODE_HAM:
                    iff_file.close()
                    pic = load_pygame_pic(filename, config)
                    display_mode &= ~config.MODE_HAM
                    if display_mode >= 0 and display_mode & config.MONITOR_ID_MASK == 0:
                        display_mode |= config.NTSC_MONITOR_ID
                    config.display_mode = display_mode
                    return pic
            elif chunk.getname() == b'BMHD':
                #bitmap header
                bmhd_bytes = chunk.read()
                (w,h,x,y,nPlanes,masking,compression,pad1,transparentColor,xAspect,yAspect,pageWidth,pageHeight) = unpack(">HHhhBBBBHBBhh", bmhd_bytes)
                config.pal = config.pal[0:1<<nPlanes]
                if is_brush and masking == 2:
                    config.bgcolor = transparentColor
                #load 24-bit IFF using PyGame loader
                if nPlanes > 8:
                    iff_file.close()
                    return load_pygame_pic(filename, config)
            elif chunk.getname() == b'CMAP':
                #color map header
                cmap_bytes = chunk.read()
                ncol = len(cmap_bytes)//3
                while len(config.pal) < ncol:
                    config.pal.append((0,0,0))
                for i in range(ncol):
                    config.pal[i] = unpack(">BBB", cmap_bytes[i*3:(i+1)*3])
                config.color_depth = config.guess_color_depth(config.pal)
                config.truepal = config.quantize_palette(config.pal, config.color_depth)
                config.pal = config.unique_palette(config.truepal)
                config.loadpal = list(config.pal)
            elif chunk.getname() == b'BODY':
                #bitmap (interleaved)
                body_bytes = chunk.read()
                if ifftype == "ILBM":
                    pic = pygame.Surface((w2b(w)*8, h),0, depth=8)
                    surf_array = pygame.surfarray.pixels2d(pic)  # Create an array from the surface.
                    decode_ilbm_body(body_bytes, compression, nPlanes, surf_array)
                elif ifftype == "PBM":
                    if w & 1:
                        we = w + 1   # make sure width is even
                    else:
                        we = w       # width is already even
                    pic = pygame.Surface((we, h),0, depth=8)
                    surf_array = pygame.surfarray.pixels2d(pic)  # Create an array from the surface.
                    decode_pbm_body(body_bytes, compression, nPlanes, surf_array)
                surf_array = None

                if display_mode > 0 and display_mode & config.MODE_EXTRA_HALFBRIGHT:
                    for i in range(32):
                        config.pal[i+32] = (config.pal[i][0]//2, config.pal[i][1]//2, config.pal[i][2]//2)

                pic.set_palette(config.pal)
            else:
                chunk.skip()
            chunk = Chunk(iff_file)
    except EOFError:
        pass

    if display_mode >= 0 and display_mode & config.MONITOR_ID_MASK == 0:
        display_mode |= config.NTSC_MONITOR_ID
    config.display_mode = display_mode

    while len(cranges) < 6:
        cranges.append(colorrange(0,1,0,0))

    config.cranges = cranges

    #crop image to actual bitmap size
    if w != w2b(w)*8:
        newpic = pygame.Surface((w, h), 0, pic)
        newpic.set_palette(config.pal)
        newpic.blit(pic, (0,0))
        pic = newpic

    return pic

#read in FORM header
def read_form(file):
    form_length = 0
    form_name = b''
    form_id = file.read(4)
    if len(form_id) == 0:
        raise EOFError

    #Skip over random chunks
    while form_id != b'FORM':
        len_bytes = file.read(4)
        chunk_len = unpack(">I", len_bytes)[0]
        if chunk_len & 1: #word align chunk
           chunk_len += 1
        file.seek(chunk_len, 1) #skip chunk
        form_id = file.read(4)
 
    if form_id == b'FORM':
        len_bytes = file.read(4)
        if len(len_bytes) == 0:
            raise EOFError
        len_tuple = unpack(">I", len_bytes)
        form_length = len_tuple[0]
        form_name = file.read(4)
        if len(form_name) == 0:
            raise EOFError

    return (str(form_name), form_length)

#read in an IFF ANIM file
def load_anim(filename, config, ifftype, status_func=None):
    cranges = []
    pic = None
    display_mode = -1
    num_CMAP = 0
    is_pal_key = False

    #initialize anim header
    anim_mode, anim_mask, anim_w, anim_h, anim_x, anim_y, anim_abstime, anim_reltime, anim_interleave, anim_pad0, anim_bits, anim_pad8a, anim_pad8b = (0,0,0,0,0,0,0,0,0,0,0,0,0)
    dpan_version, dpan_numframes, dpan_global_fps, dpan_global_delay = (0,0,0,0)
    xor_anim = False

    try:
        filesize = os.path.getsize(filename)
        iff_file = open(filename,'rb')
        iff_file.seek(12)
        form_name, form_len = read_form(iff_file)
        chunk = Chunk(iff_file)

        while chunk:
            #print(form_name + ": " + chunk.getname().decode(encoding='utf-8'))
            if chunk.getname() == b'FORM':
                iff_file.seek(-8,1) # seek before FORM header
                form_name, form_len = read_form(iff_file)
            elif chunk.getname() == b'CRNG':
                #create color range from chunk
                crng_bytes = chunk.read()
                (pad, rate, flags, low, high) = unpack(">HHHBB", crng_bytes)
                if len(cranges) < 6:
                    cranges.append(colorrange(rate,flags,low,high))
            elif chunk.getname() == b'CCRT':
                #Graphicraft color range
                ccrt_bytes = chunk.read()
                (dir, low, high, sec, micro, pad) = unpack(">hBBiih", ccrt_bytes)
                flags = 1
                if dir > 0:
                    flags |= 2
                cranges.append(colorrange(273067//(micro//1000+sec*1000),flags,low,high))
            elif chunk.getname() == b'CAMG':
                #Amiga graphics mode
                camg_bytes = chunk.read()
                display_mode = unpack(">I", camg_bytes)[0]
                if display_mode & config.MODE_HAM:
                    raise Exception("HAM mode not supported")
            elif chunk.getname() == b'GRAB':
                #brush specific chunk
                grab_bytes = chunk.read()
                xor_anim = True
            elif chunk.getname() == b'DPAN':
                #Deluxe Paint specific chunk
                dpan_bytes = chunk.read()
                (dpan_version, dpan_numframes, dpan_global_fps, d1,d2,d3) = unpack(">HHBBBB", dpan_bytes)
                #print(f"{(dpan_version, dpan_numframes, dpan_global_fps, d1,d2,d3)=}")
                if dpan_version < 3:
                    dpan_global_fps = 0
                if dpan_global_fps > 0:
                    dpan_global_delay = 60 // dpan_global_fps
            elif chunk.getname() == b'BMHD':
                #bitmap header
                bmhd_bytes = chunk.read()
                (w,h,x,y,nPlanes,masking,compression,pad1,transparentColor,xAspect,yAspect,pageWidth,pageHeight) = unpack(">HHhhBBBBHBBhh", bmhd_bytes)
                config.pal = config.pal[0:1<<nPlanes]
                if masking == 2:
                    config.bgcolor = transparentColor
            elif chunk.getname() == b'CMAP':
                #color map header
                num_CMAP += 1
                is_pal_key = True
                cmap_bytes = chunk.read()
                ncol = len(cmap_bytes)//3
                while len(config.pal) < ncol:
                    config.pal.append((0,0,0))
                for i in range(ncol):
                    config.pal[i] = unpack(">BBB", cmap_bytes[i*3:(i+1)*3])
                config.color_depth = config.guess_color_depth(config.pal)
                config.truepal = config.quantize_palette(config.pal, config.color_depth)
                config.pal = config.unique_palette(config.truepal)
                config.loadpal = list(config.pal)
            elif chunk.getname() == b'BODY':
                #bitmap (interleaved)
                body_bytes = chunk.read()
                if ifftype == "ANIM":
                    pic = pygame.Surface((w2b(w)*8, h),0, depth=8)
                    surf_array = pygame.surfarray.pixels2d(pic)  # Create an array from the surface.
                    decode_ilbm_body(body_bytes, compression, nPlanes, surf_array)
                    surf_array = None
                if display_mode > 0 and display_mode & config.MODE_EXTRA_HALFBRIGHT:
                    for i in range(32):
                        config.pal[i+32] = (config.pal[i][0]//2, config.pal[i][1]//2, config.pal[i][2]//2)

                pic.set_palette(config.pal)
                config.anim.curr_frame = 1
                config.anim.num_frames = 1
                if anim_reltime == 0:
                    anim_reltime = dpan_global_delay
                config.anim.frame = [Frame(pic, pal=config.pal, is_pal_key=True, delay=anim_reltime)]
                is_pal_key = False
            elif chunk.getname() == b'ANHD':
                #animation header
                anhd_bytes = chunk.read()
                (anim_mode, anim_mask, anim_w, anim_h, anim_x, anim_y, anim_abstime, anim_reltime, anim_interleave, anim_pad0, anim_bits, anim_pad8a, anim_pad8b) = unpack(">BBHHhhLLBBLQQ", anhd_bytes)
                #print(f"{anim_reltime=} {anim_abstime=}")
                if anim_abstime == 0 and dpan_global_delay != 0:
                    anim_reltime = dpan_global_delay
                if anim_bits & 0x02:
                    xor_anim = True
            elif chunk.getname() == b'DLTA':
                #Read in column pointers
                dlta_bytes = chunk.read()
                (p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15) = unpack(">LLLLLLLLLLLLLLLL", dlta_bytes[:64])
                pdelta = (p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15)
                #print(pdelta)
                if anim_mode == 5:
                    if config.anim.num_frames == 1:
                        config.anim.frame.append(Frame(pic.copy()))
                    else:
                        if anim_interleave == 0:
                            bframes = 2
                        else:
                            bframes = anim_interleave
                        config.anim.frame.append(config.anim.frame[config.anim.num_frames-bframes].copy())
                    if anim_reltime == 0:
                        anim_reltime = dpan_global_delay
                    config.anim.frame[-1].delay = anim_reltime
                    config.anim.frame[-1].pal = list(config.pal)
                    config.anim.frame[-1].truepal = list(config.truepal)
                    config.anim.frame[-1].loadpal = list(config.loadpal)
                    config.anim.frame[-1].is_pal_key = is_pal_key
                    config.anim.num_frames += 1
                    is_pal_key = False

                    #convert working frame to planes
                    surf_array = pygame.surfarray.pixels2d(config.anim.frame[-1].image)
                    #Convert image to height x depth x width array
                    planes = c2p(surf_array)
                    #print(f"{planes.shape=}")
                    ph, pd, pw = planes.shape

                    #print(f"{config.anim.num_frames=}")
                    for pli in range(len(pdelta)-1):
                        if pli > 7:
                            break
                        if pdelta[pli] == 0:
                            continue
                        #print(f"{pli=}")
                        p = pdelta[pli]
                        pn = pdelta[pli+1]
                        if pn == 0:
                            pn = len(dlta_bytes)
                        colno = 0
                        while p < pn and p < len(dlta_bytes) and colno < pw:
                            opcount = dlta_bytes[p]
                            #print(f"{colno=} {opcount=}")
                            p += 1
                            pp = 0
                            while opcount:
                                #Unique
                                if dlta_bytes[p] & 0x80:
                                    count = dlta_bytes[p] & 0x7f
                                    p+=1
                                    if p >= len(dlta_bytes):
                                        break
                                    if p+count >= len(dlta_bytes):
                                        count = len(dlta_bytes)-p
                                    #print(f"{p:5d}: {pp:5d} uniq {count=} {dlta_bytes[p:p+count]=}")
                                    if xor_anim:
                                        planes[pp:pp+count, pli, colno] ^= np.array(list(dlta_bytes[p:p+count]), dtype='uint8')
                                    else:
                                        planes[pp:pp+count, pli, colno] = list(dlta_bytes[p:p+count])
                                    p += count
                                    pp += count
                                #Skip
                                elif dlta_bytes[p] != 0:
                                    count = dlta_bytes[p]
                                    #print(f"{p:5d}: {pp:5d} skip {count=}")
                                    pp += count
                                    p+=1
                                #Same
                                else:
                                    p+=1
                                    if p >= len(dlta_bytes):
                                        break
                                    count = dlta_bytes[p]
                                    p+=1
                                    if p >= len(dlta_bytes):
                                        break
                                    value = dlta_bytes[p]
                                    #print(f"{p:5d}: {pp:5d} same {count=} {value=}")
                                    if xor_anim:
                                        planes[pp:pp+count, pli, colno] ^= value
                                    else:
                                        planes[pp:pp+count, pli, colno] = value
                                    pp += count
                                    p+=1
                                opcount -= 1
                            colno += 1

                    #Turn array back into image
                    p2c(planes, surf_array)
                    surf_array = None
                elif anim_mode == 7:
                    raise Exception(f"IFF ANIM mode {anim_mode} not supported")
                elif anim_mode == 8:
                    raise Exception(f"IFF ANIM mode {anim_mode} not supported")
                else:
                    raise Exception(f"IFF ANIM mode {anim_mode} not supported")
                if status_func != None:
                    status_func(iff_file.tell() / filesize)
            else:
                chunk.skip()
            chunk = Chunk(iff_file)
    except EOFError:
        pass

    if display_mode >= 0 and display_mode & config.MONITOR_ID_MASK == 0:
        display_mode |= config.NTSC_MONITOR_ID
    config.display_mode = display_mode

    while len(cranges) < 6:
        cranges.append(colorrange(0,1,0,0))

    config.cranges = cranges

    if dpan_numframes > 0:
        #take frame 0 delay from looping frame to be trimmed
        if config.anim.num_frames - dpan_numframes == 2:
            config.anim.frame[0].delay = config.anim.frame[-2].delay
        
        #trim final frames of looping animation
        while config.anim.num_frames > dpan_numframes:
            del config.anim.frame[-1]
            config.anim.num_frames -= 1

    config.anim.global_palette = (num_CMAP == 1)
    config.pal = config.anim.frame[0].pal

    #crop image to actual bitmap size
    if w != w2b(w)*8:
        newpic = pygame.Surface((w, h), 0, pic)
        newpic.set_palette(config.pal)
        newpic.blit(pic, (0,0))
        pic = newpic

        #crop anim images to actual bitmap size
        for i in range(config.anim.num_frames):
            pic2 = config.anim.frame[i].image
            newpic = pygame.Surface((w, h), 0, pic2)
            newpic.set_palette(pic2.get_palette())
            newpic.blit(pic2, (0,0))
            config.anim.frame[i].image = newpic

    return pic

def pal_power_2(palin):
    ncol = len(palin)
    #Copy palette to avoid tuple that we can't append to
    pal = []
    for color in palin:
        r,g,b = color
        pal.append((r,g,b))

    #Get default palette to append to end
    defpal = config.get_default_palette(256)

    #Add colors to bring count up to a power of 2
    while ncol < 2 or (math.ceil(math.log2(ncol)) != math.floor(math.log2(ncol))):
        pal.append(defpal[len(pal)])
        ncol += 1

    return pal

def load_pygame_pic(filename, config, status_func=None, force_pal=None):
    config.cranges = []
    pic = pygame.image.load(filename)
    if force_pal != None:
        pic = pic.convert() #convert to high color to change palette
    if pic.get_bitsize() > 8:
        if force_pal != None:
            config.pal = list(force_pal)
        else:
            config.pal = get_truecolor_palette(pic.convert(), 256)
            config.pal = pal_power_2(config.pal)
        pic = convert8(pic, config.pal, status_func=status_func)
    else:
        #Clone bitmap and blit back so colors can be added to palette
        newpic = pygame.Surface(pic.get_size(), 0, pic)
        if force_pal != None:
            config.pal = list(force_pal)
        else:
            config.pal = pal_power_2(pic.get_palette())
        pic.set_palette(config.pal)
        newpic.set_palette(config.pal)
        newpic.blit(pic,(0,0))
        pic = newpic
 
    config.color_depth = config.guess_color_depth(config.pal)

    iffinfo_file = re.sub(r"\.[^.]+$", ".iffinfo", filename)
    if pic_type(iffinfo_file) == "ILBM":
        load_iff(iffinfo_file, config, "ILBM", pic)
    else:
        config.display_mode = -1

    pal = config.quantize_palette(config.pal, config.color_depth)
    upal = config.unique_palette(pal)
    config.pal = list(upal)
    config.loadpal = list(upal)
    config.truepal = list(pal)
    pic.set_palette(config.pal)

    while len(config.cranges) < 6:
        config.cranges.append(colorrange(0,1,0,0))

    return pic


def load_pic(filename_in, config, status_func=None, is_anim=False, cmd_load=False, import_frames=False, is_brush=False):
    filename = filename_in
    pic = config.pixel_canvas

    if config.anim.num_frames > 1:
        #Get rid of animation
        config.anim = libs.animation.Animation()

    #Check for series of numbered files
    seq_matches = re.findall(r'[^0-9]([0-9]{3,})\.[a-zA-Z]+$', filename)

    frameno = -1
    firstframe = -1
    maxframe = -1
    global_palette = None
    pictype = pic_type(filename)
    if import_frames:
        if len(seq_matches) == 1 and import_frames and pictype != "NONE":
            frameno = int(seq_matches[0])
            firstframe = frameno
            maxframe = firstframe+1
            #Find number of frames
            while os.path.exists(filename_in.replace(seq_matches[0], (len(seq_matches[0]) - len(str(maxframe))) * "0" + str(maxframe))):
                maxframe += 1
            maxframe -= 1

            #Ask whether to use a global palette or a local one
            palette_type = config.anim.ask_global_palette(maxframe-firstframe+1)
            if palette_type == 0: # global palette
                # grab global palette from a frame 1/3 of the way through the sequence
                palframe = ((maxframe - firstframe) // 3) + firstframe
                answer = config.anim.num_req(config.pixel_req_canvas, "Palette From Frame", "Frame", palframe)
                if answer == None:
                    return
                else:
                    palframe = answer
                palfilename = filename_in.replace(seq_matches[0], (len(seq_matches[0]) - len(str(palframe))) * "0" + str(palframe))
                pic = load_pygame_pic(palfilename, config)
                global_palette = list(config.pal)
            elif palette_type == 1: # local palette
                pass
            else: # cancel
                return config.pixel_canvas
        else:
            raise Exception("Load error")
    elif not cmd_load and ((is_anim and not pictype in ["ANIM", "GIF"]) or (not is_anim and pictype == "ANIM")):
        raise Exception("Load error")

    while pictype != "NONE":
        if pictype in ["ILBM", "PBM"] and not import_frames:
            pic = load_iff(filename, config, pictype, is_brush=is_brush)
            config.pal = pal_power_2(config.pal)
            config.pal = config.quantize_palette(config.pal, config.color_depth)
            pic.set_palette(config.pal)
        elif pictype == "ANIM":
            pic = load_anim(filename, config, pictype, status_func=status_func)
            config.pal = pal_power_2(config.pal)
            config.pal = config.quantize_palette(config.pal, config.color_depth)
            pic.set_palette(config.pal)
        elif pictype == "GIF":
            num_CMAP = 0
            gif_status_func = status_func
            if import_frames:
                gif_status_func = None
                if status_func != None:
                    status_func(frameno / maxframe)
            gif = GIFParser(filename, status_func=gif_status_func)
            w = gif.header["width"]
            h = gif.header["height"]
            pic = pygame.Surface((w,h), 0, depth=8)
            if gif.global_palette != None:
                pal = gif.global_palette
            else:
                pal = gif.frames[0]["local_palette"]
            config.color_depth = config.guess_color_depth(pal)
            pal = config.quantize_palette(pal, config.color_depth)
            upal = config.unique_palette(pal)
            config.pal = list(upal)
            config.loadpal = list(upal)
            config.truepal = list(pal)
            pic.set_palette(config.pal)
            surf_array = pygame.surfarray.pixels2d(pic)
            surf_array[:] = gif.frames[0]["image_data"][:]
            surf_array = None
            if len(gif.frames) > 1:
                config.anim.frame = [Frame(pic, delay=int(round(gif.frames[0]["delay_time"]*60/100)), pal=config.pal, is_pal_key=True)]
            for i in range(1,len(gif.frames)):
                dx = gif.frames[i]["image_left_position"]
                dy = gif.frames[i]["image_top_position"]
                dw = gif.frames[i]["image_width"]
                dh = gif.frames[i]["image_height"]
                dm = gif.frames[i]["disposal_method"]
                is_trans = gif.frames[i]["transparency"]
                trans_color = gif.frames[i]["transparent_color_index"]

                diffpic = pygame.Surface((dw,dh), 0, depth=8)
                if gif.frames[i]["local_palette"] != None:
                    pal = gif.frames[i]["local_palette"]
                    num_CMAP += 1
                else:
                    pal = gif.global_palette
                diffpic.set_palette(pal)
                surf_array = pygame.surfarray.pixels2d(diffpic)
                surf_array[:] = gif.frames[i]["image_data"][:]
                surf_array = None

                if dm in [0,1]:
                    # Overlay previous frame
                    framepic = pygame.Surface((w,h), 0, depth=8)
                    framepic.set_palette(pal)
                    framepic.blit(config.anim.frame[i-1].image, (0,0))
                    if is_trans:
                        diffpic.set_colorkey(trans_color)
                    framepic.blit(diffpic, (dx,dy))
                elif dm == 2:
                    # Set to BG color
                    framepic = pygame.Surface((w,h), 0, depth=8)
                    framepic.set_palette(pal)
                    framepic.fill(gif.header["background_color_index"])
                    if is_trans:
                        diffpic.set_colorkey(trans_color)
                    framepic.blit(diffpic, (dx,dy))
                elif dm == 3:
                    # Overlay first frame
                    framepic = pygame.Surface((w,h), 0, depth=8)
                    framepic.set_palette(pal)
                    framepic.blit(config.anim.frame[0].image, (0,0))
                    if is_trans:
                        diffpic.set_colorkey(trans_color)
                    framepic.blit(diffpic, (dx,dy))
                else:
                    # Don't overlay previous frame
                    framepic = diffpic
                delay = int(round(gif.frames[i]["delay_time"]*60/100))
                upal = config.unique_palette(pal)
                is_pal_key = False
                pal1 = pal
                if gif.frames[i-1]["local_palette"] != None:
                    pal0 = gif.frames[i-1]["local_palette"]
                else:
                    pal0 = gif.global_palette
                if pal0 != pal1:
                    is_pal_key = True
                config.anim.frame.append(Frame(framepic, delay=delay, pal=upal, truepal=pal, is_pal_key=is_pal_key))
            if len(gif.frames) > 1:
                config.anim.curr_frame = 1
                config.anim.num_frames = len(gif.frames)
                config.anim.global_palette = (num_CMAP <= 1)
            if "comment" in gif.frames[0]:
                if gif.frames[0]['comment'].startswith("PyDPainter options:"):
                    options = gif.frames[0]['comment'].split(":")
                    for option in options[1:]:
                        optkey,optval = option.split("=")
                        if optkey == "bgcolor":
                            config.bgcolor = int(optval)
            elif is_brush and gif.frames[0]["transparency"]:
                config.bgcolor = gif.frames[0]["transparent_color_index"]
            config.display_mode = -1
            config.cranges = 6 * [colorrange(0,1,0,0)]
        elif pictype != "NONE":
            pic = load_pygame_pic(filename, config, force_pal=global_palette)
            if status_func != None:
                status_func(frameno / maxframe)

        if frameno >= 0:
            if config.anim.num_frames == 1:
                if pictype == "GIF":
                    delay = gif.frames[0]["delay_time"]
                else:
                    delay = 4
                config.anim.frame = [Frame(pic, delay=delay, is_pal_key=True)]
            else:
                is_pal_key = True
                config.anim.frame.append(Frame(pic))
                if config.anim.frame[-1].pal == config.anim.frame[-2].pal:
                    is_pal_key = False
                config.anim.frame[-1].is_pal_key = is_pal_key

            frameno += 1
            config.anim.num_frames += 1
            filename = filename_in.replace(seq_matches[0], (len(seq_matches[0]) - len(str(frameno))) * "0" + str(frameno))
            pictype = pic_type(filename)
        else:
            pictype = "NONE"

    if frameno >= 0:
        # Find max number of colors in the frames
        num_colors = 0
        for frame in config.anim.frame:
            num_colors = max(len(frame.pal), num_colors)

        # Extend number of colors to max number of colors
        for frame in config.anim.frame:
            pal = None
            if num_colors != len(frame.pal):
                if num_colors > len(frame.pal):
                    # extend palette
                    pal = list(frame.truepal)
                    pal.extend([[0,0,0]]*(num_colors-len(pal)))
                upal = config.unique_palette(pal)
                frame.truepal = list(pal)
                frame.loadpal = list(pal)
                frame.pal = list(upal)
                frame.image.set_palette(upal)
        config.anim.curr_frame = 1
        config.anim.num_frames = len(config.anim.frame)
        pic = config.anim.frame[0].image
        config.pal = config.anim.frame[0].pal
        config.truepal = config.anim.frame[0].truepal
        if config.anim.pal_key_range(1) == [1,config.anim.num_frames]:
            config.anim.global_palette = True
        else:
            config.anim.global_palette = False

    if config.anim.num_frames > 1:
        # Add layers to all frames
        for i in range(len(config.anim.frame)):
            config.anim.frame[i].layers.set("canvas", config.anim.frame[i].image, priority=1)

    config.color_depth = config.guess_color_depth(config.truepal)
    config.truepal = config.quantize_palette(config.truepal, config.color_depth)
    config.pal = config.quantize_palette(config.pal, config.color_depth)

    #Guess display mode
    if config.display_mode < 0 or config.display_info.get_id(config.display_mode) == None:
        sm = config.display_info.match_resolution(pic.get_width(), pic.get_height())
        if sm != None:
            config.display_mode = sm.mode_id
        elif pic.get_width() > 320 or pic.get_height() > 200:
            #Assume square pixel VGA
            config.display_mode = config.VGA_MONITOR_ID | config.MODE_HIRES | config.MODE_LACE
            config.scanlines = config.SCANLINES_OFF
        else:
            config.display_mode = config.NTSC_MONITOR_ID # Low Res 320x200

    config.loadpal = list(config.pal)

    return pic

#write an IFF chunk to a file
def write_chunk(f,name,data):
    f.write(name + pack(">I", len(data)) + data)
    #pad odd bytes
    if len(data) & 1 == 1:
        f.write(b'\0')

#close IFF file and update length
def close_iff(f):
    f.seek(0,2) # seek to end
    fsize = f.tell() - 8
    f.seek(4) # seek until after FORM
    f.write(pack(">I", fsize)) # write length into FORM
    f.close()

#save color ranges to a file
def save_iffinfo(filename):
    crngfile = re.sub(r"\.[^.]+$", ".iffinfo", filename)
    newfile = open(crngfile, 'wb')
    newfile.write(b'FORM\0\0\0\0ILBM')
    
    write_chunk(newfile, b'BMHD', pack(">HHhhBBBBHBBhh", \
        config.pixel_width, config.pixel_height, \
        0,0, \
        int(math.log(len(config.pal),2)), \
        0, \
        0, \
        0, \
        0, \
        10, 11, \
        config.pixel_width, config.pixel_height
        ))

    write_chunk(newfile, b'CAMG', pack(">I", config.display_mode))

    for crange in config.cranges:
        write_chunk(newfile, b'CRNG', pack(">HHHBB", 0, crange.rate, crange.get_flags(), crange.low, crange.high))
    close_iff(newfile)

#encode byterun1 ILBM encoding
def byterun_encode(inarray):
    #Byte run encoding for IFF files
    ia = np.asarray(inarray,dtype=np.uint8)
    n = len(ia)
    if n == 0: 
        return None

    y = np.array(ia[1:] != ia[:-1])     # pairwise unequal (string safe)
    i = np.append(np.where(y), n - 1)   # must include last element position
    z = np.diff(np.append(-1, i))       # run lengths
    vals = ia[i]

    oa = np.array([], dtype=np.uint8)
    #print(z)
    #print(vals)

    z = np.append(z,0)
    j = 0
    while j < len(z):
        #repeated values of 128 or more
        if z[j] >= 128:
            oa = np.append(oa,[129,vals[j]])
            z[j] -= 128
        #repeated values > 2 and < 128
        elif z[j] > 2:
            oa = np.append(oa,[256-z[j]+1,vals[j]])
            j += 1
        #copy values verbatim up to 127
        elif z[j] in [1,2]:
            copy_count = 0
            copy_bytes = np.array([], dtype=np.uint8)
            while j < len(z) and z[j] in [1,2] and copy_count+z[j] <= 127:
                copy_count += z[j]
                copy_bytes = np.append(copy_bytes,[vals[j]])
                if z[j] == 2:
                    copy_bytes = np.append(copy_bytes,[vals[j]])
                j += 1
            oa = np.append(oa,[copy_count-1])
            oa = np.append(oa,copy_bytes)
        else:
            j += 1
    oa = np.asarray(oa,dtype=np.uint8)
    return(oa)

#chunky to planar using numpy
def c2p(surf_array):
    w = len(surf_array)
    h = len(surf_array[0])
    pic = np.array(surf_array).transpose()
    bits = np.unpackbits(pic, axis=0)
    return np.packbits(bits).reshape(h,8,w2b(w))[:,::-1,:]

#save IFF file
def save_iff(filename, config, ifftype, bgcolor=-1):
    nPlanes = int(math.log(len(config.pal),2))
    newfile = open(filename, 'wb')
    newfile.write(b'FORM\0\0\0\0')
    if ifftype == "PBM":
        newfile.write(b'PBM ')
        nplanes = 8
        pal = list(config.truepal)
        defpal = config.get_default_palette(256)
        while len(pal) < 256:
            pal.append(defpal[len(pal)])
    else:
        newfile.write(b'ILBM')
        pal = config.truepal
 
    write_chunk(newfile, b'BMHD', pack(">HHhhBBBBHBBhh", \
        config.pixel_width, config.pixel_height, \
        0,0, \
        nPlanes, \
        2 if bgcolor>=0 else 0, \
        1, \
        0, \
        max(0, bgcolor), \
        10, 11, \
        config.pixel_width, config.pixel_height
        ))

    cmap_chunk = b''
    for col in pal:
        cmap_chunk += pack(">BBB", col[0], col[1], col[2])
    write_chunk(newfile, b'CMAP', cmap_chunk)

    write_chunk(newfile, b'CAMG', pack(">I", config.display_mode))

    for crange in config.cranges:
        write_chunk(newfile, b'CRNG', pack(">HHHBB", 0, crange.rate, crange.get_flags(), crange.low, crange.high))

    body = b''
    out_canvas = config.pixel_canvas
    w,h = out_canvas.get_size()
    if ifftype == "ILBM":
        if w != w2b(w):   # make sure width is divisible by 16
            out_canvas = pygame.Surface((w2b(w)*8, h),0, depth=8)
            out_canvas.set_palette(config.pal)
            out_canvas.blit(config.pixel_canvas, (0,0))
        surf_array = pygame.surfarray.pixels2d(out_canvas)  # Create an array from the surface.
        planes_out = c2p(surf_array)

        # write out bitplanes interleaved one line at a time
        for y in range(0,len(planes_out)):
            for p in range(0,nPlanes):
                body += byterun_encode(planes_out[y,p,:].flatten()).tobytes()
    elif ifftype == "PBM":
        if w & 1:
            we = w + 1   # make sure width is even
            out_canvas = pygame.Surface((we, h),0, depth=8)
            out_canvas.set_palette(config.pal)
            out_canvas.blit(config.pixel_canvas, (0,0))
        else:
            we = w       # width is already even
        surf_array = pygame.surfarray.pixels2d(out_canvas)  # Create an array from the surface.
        chunky_out = surf_array.transpose()

        # write out chunky bitmap one line at a time
        for y in range(0,len(chunky_out)):
            body += byterun_encode(chunky_out[y,:].flatten()).tobytes()

    write_chunk(newfile, b'BODY', body)

    close_iff(newfile)


def save_gif(filename, config, bgcolor=-1):
    header = {
        "width": config.pixel_width,
        "height": config.pixel_height,
        "global_num_colors": len(config.pal),
        "global_color_table": 1,
    }
    surf_array = pygame.surfarray.pixels2d(config.pixel_canvas)
    frame = {"local_palette": None,
             "image_data": surf_array,
    }

    if bgcolor >= 0:
        frame["transparency"] = True
        frame["transparent_color_index"] = bgcolor

    gif = GIFWriter(filename, header, config.truepal)
    gif.write_frame(frame)
    surf_array = None

#save picture
def save_pic(filename, config, overwrite=True, bgcolor=-1):
    if '.' not in filename:
        filename += ".iff"

    # Check if file exists
    if overwrite == False and os.path.isfile(filename):
        return False

    if (len(filename) > 4 and filename[-4:].lower() == ".iff") or \
       (len(filename) > 5 and filename[-5:].lower() == ".ilbm"):
        save_iff(filename, config, "ILBM", bgcolor=bgcolor)
    elif len(filename) > 4 and filename[-4:].lower() == ".lbm":
        save_iff(filename, config, "PBM", bgcolor=bgcolor)
    elif len(filename) > 4 and filename[-4:].lower() == ".gif":
        save_gif(filename, config, bgcolor=bgcolor)
    else:
        pygame.image.save(config.pixel_canvas, filename)

    return True

FORM_pos=[]
def start_FORM(f, name):
    f.write(b'FORM\0\0\0\0' + bytearray(name, 'utf-8'))
    FORM_pos.append(f.tell()-4) # add position to stack

def end_FORM(f):
    fsize = f.tell() - FORM_pos[-1]
    f.seek(FORM_pos[-1] - 4) # seek to the size after FORM
    f.write(pack(">I", fsize)) # write length into FORM
    f.seek(0,2) # seek to end
    FORM_pos.pop() # remove position from stack

def image16(image):
    out_image = image
    w,h = out_image.get_size()

    # adjust canvas width to be divisible by 16
    if w != w2b(w)*8:
        out_image = pygame.Surface((w2b(w)*8, h),0, depth=8)
        out_image.set_palette(image.get_palette())
        out_image.blit(image, (0,0))

    return out_image

def vsame(col_data, start):
    count = 1
    cdata = col_data[start]
    col = start+1
    while col < len(col_data) and col_data[col] == cdata:
        count += 1
        col += 1
    return count

def anim5_col_diff(diffmap, col_data):
    MSKIP, MUNIQ, MSAME = range(3)
    MAXRUN = 127
    opcount = 0
    ops = b''
    row = 0
    start_row = row
    mode = MSKIP
    same_val = 0
    #print(f"{diffmap=}")
    while row < len(col_data):
        #print(f"{row=}")
        if mode == MSKIP:
            if diffmap[row]:
                if row != start_row:
                    #write out skip op
                    #print("SKIP " + str(row-start_row))
                    ops += pack(">b", row-start_row)
                    opcount += 1
                #what op is next?
                start_row = row
                if vsame(col_data, row) > 3:
                    mode = MSAME
                    same_val = col_data[row]
                else:
                    mode = MUNIQ
            else:
                if row-start_row >= MAXRUN:
                    #write out skip op and continue
                    #print("SKIP " + str(MAXRUN))
                    ops += pack(">b", MAXRUN)
                    opcount += 1
                    start_row += MAXRUN
        if mode == MUNIQ:
            if diffmap[row]:
                if vsame(col_data, row) > 3:
                    #end uniq and write out uniq op
                    #print("UNIQ " + str(row-start_row))
                    ops += pack(">B", 128 + (row-start_row))
                    ops += bytes(col_data[start_row:row])
                    opcount += 1
                    #switch to same op
                    start_row = row
                    mode = MSAME
                    same_val = col_data[row]
                else:
                    if row-start_row >= MAXRUN:
                        #write out uniq op and continue
                        #print("UNIQ " + str(MAXRUN))
                        ops += pack(">B", 128 + MAXRUN)
                        ops += bytes(col_data[start_row:row])
                        opcount += 1
                        start_row += MAXRUN
            else:
                #write out uniq op
                #print("UNIQ " + str(row-start_row))
                ops += pack(">B", 128 + (row-start_row))
                ops += bytes(col_data[start_row:row])
                opcount += 1
                start_row = row
                mode = MSKIP
        if mode == MSAME:
            if same_val != col_data[row]:
                #write out same op
                #print("SAME " + str(row-start_row) + " " + str(same_val))
                ops += pack(">bbB", 0, row-start_row, same_val)
                opcount += 1
                #what op is next?
                start_row = row
                if diffmap[row]:
                    mode = MUNIQ
                else:
                    mode = MSKIP
            else:
                if row-start_row >= MAXRUN:
                    #write out same op and continue
                    #print("SAME " + str(row-start_row) + " " + str(same_val))
                    ops += pack(">bbB", 0, MAXRUN, same_val)
                    opcount += 1
                    start_row += MAXRUN
        row += 1
    # write out final op
    if mode == MUNIQ:
        #write out uniq op
        #print("UNIQ " + str(row-start_row))
        ops += pack(">B", 128 + (row-start_row))
        ops += bytes(col_data[start_row:row])
        opcount += 1
    elif mode == MSAME:
        #write out same op
        #print("SAME " + str(row-start_row) + " " + str(same_val))
        ops += pack(">bbB", 0, row-start_row, same_val)
        opcount += 1

    return (opcount, ops)

def anim5_plane_diff(plane0, plane1, anim_xor):
    pl_diff = b''
    # set up column counts
    ncol = len(plane0[0])
    opcount_sum = 0
    col = 0

    diffmap = (plane0 != plane1)
    #print(f"{diffmap=}")

    # diff a column at a time
    while col < ncol:
        #print(f"{col=}")
        opcount = 0
        ops = b''
        if np.all(diffmap[:,col] == False):
            # no diffs in column
            pass
        else:
            #diff one column
            if anim_xor:
                opcount, ops = anim5_col_diff(diffmap[:,col], plane0[:,col] ^ plane1[:,col])
            else:
                opcount, ops = anim5_col_diff(diffmap[:,col], plane1[:,col])
        pl_diff += pack(">B", opcount)
        pl_diff += ops
        opcount_sum += opcount
        col += 1
            
    if opcount_sum == 0:
        # no diffs in plane
        return b''
    else:
        return pl_diff

def save_iff_anim(filename, config, status_func=None, animbrush=False, transparent_color=-1):
    nPlanes = int(math.log(len(config.pal),2))
    newfile = open(filename, 'wb')
    start_FORM(newfile, "ANIM")

    ####### Write first frame

    start_FORM(newfile, "ILBM")
    pal = config.truepal
    
    masking = 0
    if transparent_color >= 0:
        masking = 2
    else:
        transparent_color = 0

    write_chunk(newfile, b'BMHD', pack(">HHhhBBBBHBBhh", \
        config.pixel_width, config.pixel_height, \
        0,0, \
        nPlanes, \
        masking, \
        1, \
        0, \
        transparent_color, \
        10, 11, \
        config.sm.x, config.sm.y
        ))

    cmap_chunk = b''
    for col in pal:
        cmap_chunk += pack(">BBB", col[0], col[1], col[2])
    write_chunk(newfile, b'CMAP', cmap_chunk)

    if animbrush:
        write_chunk(newfile, b'GRAB', pack(">HH",
            config.pixel_width//2, config.pixel_height//2 # X,Y of center of brush
            ))

    for crange in config.cranges:
        write_chunk(newfile, b'CRNG', pack(">HHHBB", 0, crange.rate, crange.get_flags(), crange.low, crange.high))

    global_fps = 20
    mindelay = min(config.anim.frame, key=attrgetter('delay')).delay
    if mindelay > 0:
        global_fps = 60 // mindelay

    write_chunk(newfile, b'DPAN', pack(">HHBBBB",
        3, #version used in DPaint V
        config.anim.num_frames,
        global_fps,
        0,0,0 #flags
        ))

    anim_abstime = config.anim.frame[0].delay

    anim_interleave = 0
    anim_bits = 0
    anim_xor = False
    if animbrush:
        anim_interleave = 1
        anim_bits |= 0x02
        anim_xor = True

    if not animbrush:
        write_chunk(newfile, b'ANHD', pack(">BBHHhhLLBBLQQ",
            0, 0, # anim_mode, anim_mask
            config.pixel_width, config.pixel_height, # anim_w, anim_h
            0, 0, # anim_x, anim_y
            anim_abstime, config.anim.frame[0].delay, # anim_abstime, anim_reltime
            anim_interleave, 0, # anim_pad0
            anim_bits, 0, 0 # anim_pad8a, anim_pad8b
            ))

    write_chunk(newfile, b'CAMG', pack(">I", config.display_mode))

    body = b''
    out_canvas = image16(config.anim.frame[0].layers.get_flattened())
    surf_array = pygame.surfarray.pixels2d(out_canvas)  # Create an array from the surface.
    planes_out = c2p(surf_array)

    # write out bitplanes interleaved one line at a time
    for y in range(0,len(planes_out)):
        for p in range(0,nPlanes):
            body += byterun_encode(planes_out[y,p,:].flatten()).tobytes()

    write_chunk(newfile, b'BODY', body)

    end_FORM(newfile)

    ####### Write animation diffs

    previ = 0
    for i in range(1,config.anim.num_frames+2):
        curri = i
        if i >= config.anim.num_frames:
            curri = i - config.anim.num_frames
        #print(f"{previ=} {curri=}")
        localpal = None
        if config.anim.global_palette:
            localpal = None
        elif config.anim.frame[curri].is_pal_key:
            localpal = config.anim.frame[curri].truepal

        anim_abstime += config.anim.frame[curri].delay

        start_FORM(newfile, "ILBM")

        write_chunk(newfile, b'ANHD', pack(">BBHHhhLLBBLQQ", \
            5, 0, # anim_mode, anim_mask
            config.pixel_width, config.pixel_height, # anim_w, anim_h
            0, 0, # anim_x, anim_y
            anim_abstime, config.anim.frame[curri].delay, # anim_abstime, anim_reltime
            anim_interleave, 0, # anim_pad0
            anim_bits, 0, 0 # anim_pad8a, anim_pad8b
            ))

        if localpal != None:
            cmap_chunk = b''
            for col in localpal:
                cmap_chunk += pack(">BBB", col[0], col[1], col[2])
            write_chunk(newfile, b'CMAP', cmap_chunk)

        dlta_bytes = b''
        pdelta = [0] * 16

        out_canvas1 = image16(config.anim.frame[curri].layers.get_flattened())
        out_canvas0 = image16(config.anim.frame[previ].layers.get_flattened())

        # make previous and current frames into bitplanes
        surf_array0 = pygame.surfarray.pixels2d(out_canvas0)
        planes0 = c2p(surf_array0)
        surf_array0 = None
        surf_array1 = pygame.surfarray.pixels2d(out_canvas1)
        planes1 = c2p(surf_array1)
        surf_array1 = None
        nplanes = len(planes1[0])

        # finds diffs between previous and current bitplane
        pl_diff = [b''] * 8
        for pli in range(nplanes):
            pl_diff[pli] = anim5_plane_diff(planes0[:,pli,:], planes1[:,pli,:], anim_xor)

        # set pdelta pointers
        p = 16*4 # past end of delta pointers
        for pli in range(nplanes):
            if len(pl_diff[pli]) > 0:
                pdelta[pli] = p
            else:
                pdelta[pli] = 0
            p += len(pl_diff[pli])

        # build DLTA chunk

        # plane pointers are at beginning of DLTA chunk
        for p in pdelta:
            dlta_bytes += pack(">L", p)

        # plane diffs are the rest of the DLTA chunk
        for pli in range(nplanes):
            dlta_bytes += pl_diff[pli]

        write_chunk(newfile, b'DLTA', dlta_bytes)

        end_FORM(newfile)

        if status_func:
            status_func(i / (config.anim.num_frames+2))

        if anim_interleave == 0:
            previ = curri - 1
        else:
            previ = curri - anim_interleave + 1

    ####### End of file

    end_FORM(newfile)
    newfile.close()

def save_gif_anim(filename, config, status_func=None, transparent_color=-1):
    header = {
        "width": config.pixel_width,
        "height": config.pixel_height,
        "global_num_colors": len(config.pal),
        "global_color_table": int(config.anim.global_palette),
    }
    pal = None
    if config.anim.global_palette:
        pal = config.truepal
    gif = GIFWriter(filename, header, pal)

    for i in range(config.anim.num_frames):
        if config.anim.global_palette:
            localpal = None
        else:
            localpal = config.anim.frame[i].truepal
        surf_array = pygame.surfarray.pixels2d(config.anim.frame[i].layers.get_flattened())
        disposal_method = 0
        transparency = 0
        transparent_color_index = 0
        image_data_lzh = None
        xcoord = 0
        ycoord = 0
        image_width = config.pixel_width
        image_height = config.pixel_height
        # frame compression using differences
        if i > 0 and not config.anim.frame[i].is_pal_key:
            # Do difference from previous frame
            prev_array = pygame.surfarray.pixels2d(config.anim.frame[i-1].layers.get_flattened())
            surf_diff = np.equal(prev_array, surf_array)
            surf_diff_ne = np.not_equal(prev_array, surf_array)

            # Find background color not in the difference
            all_256 = np.arange(256, dtype=np.uint8)
            surf_unique = np.unique(surf_array[surf_diff_ne])
            surf_notin = np.setdiff1d(all_256, surf_unique, assume_unique=True)
            if len(surf_notin) > 0:
                bgcolor = surf_notin[0]
                surf_diff_array = surf_array.copy()
                surf_diff_array[surf_diff] = bgcolor
                # find bounds of diff
                diff_indexes = np.argwhere(surf_diff_ne)
                if len(diff_indexes) == 0:
                    #frame has no differences so make it one pixel
                    minx,miny = (0,0)
                    maxx,maxy = (0,0)
                else:
                    minx,miny = diff_indexes.min(axis=0)
                    maxx,maxy = diff_indexes.max(axis=0)
                # trim to bounds
                surf_diff_array_cropped = surf_diff_array[minx:maxx+1,miny:maxy+1]
                surf_array_cropped = surf_array[minx:maxx+1,miny:maxy+1]
                # try compressing diff and overwrite to see which is smaller
                surf_diff_lzw = gif.encode_lzw_data(bytes(surf_diff_array_cropped.transpose().flatten()))
                surf_lzw = gif.encode_lzw_data(bytes(surf_array_cropped.transpose().flatten()))

                xcoord = minx
                ycoord = miny
                image_width = maxx - minx + 1
                image_height = maxy - miny + 1

                if len(surf_diff_lzw) < len(surf_lzw):
                    image_data_lzh = surf_diff_lzw
                    disposal_method = 1
                    transparency = 1
                    transparent_color_index = bgcolor
                else:
                    image_data_lzh = surf_lzw
            else:
                surf_diff_lzw = gif.encode_lzw_data(bytes(surf_diff_array.transpose().flatten()))
                image_data_lzh = surf_lzw

        frame = {"local_palette": localpal,
                 "image_data": surf_array,
                 "image_data_lzh": image_data_lzh,
                 "delay_time": int(round(100 * config.anim.frame[i].delay / 60)),
                 "disposal_method": disposal_method,
                 "transparency": transparency,
                 "transparent_color_index": transparent_color_index,
                 "image_left_position": xcoord,
                 "image_top_position": ycoord,
                 "image_width": image_width,
                 "image_height": image_height,
        }

        if i == 0 and transparent_color >= 0:
            frame["comment"] = f"PyDPainter options:bgcolor={transparent_color}"

        gif.write_frame(frame)
        surf_array = None
        if status_func:
            status_func(i / config.anim.num_frames)

def save_anim(filename, config, status_func=None, overwrite=True, transparent_color=-1):
    if '.' not in filename:
        filename += ".anim"

    # Check if file exists
    if overwrite == False and os.path.isfile(filename):
        return False

    if (len(filename) > 5 and filename[-5:].lower() == ".anim"):
        save_iff_anim(filename, config, status_func=status_func)
    elif (len(filename) > 5 and filename[-5:].lower() == ".anbr"):
        save_iff_anim(filename, config, status_func=status_func, animbrush=True, transparent_color=transparent_color)
    elif (len(filename) > 5 and filename[-5:].lower() == ".anmb"):
        save_iff_anim(filename, config, status_func=status_func, animbrush=True, transparent_color=transparent_color)
    elif len(filename) > 4 and filename[-4:].lower() == ".gif":
        save_gif_anim(filename, config, status_func=status_func, transparent_color=transparent_color)
    else:
        raise Exception("Unrecognized anim format")

    return True
