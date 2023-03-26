#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import math
import os.path
import random
import re

import numpy as np

from struct import pack, unpack

from chunk import Chunk

from colorrange import *
from prim import *

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
def iff_type(filename):
    retval = ""

    try:
        iff_file = open(filename,'rb')
        header = iff_file.read(4)
        if header == b'FORM':
            iff_file.seek(8)
            ilbm_header = iff_file.read(4)
            if ilbm_header == b'ILBM':
                retval = "ILBM"
            elif ilbm_header == b'ANIM':
                retval = "ANIM"
        iff_file.close()
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

#read in an IFF file
def load_iff(filename, config):
    cranges = []
    pic = None
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
                display_mode = unpack(">I", camg_bytes)[0] & config.OCS_MODES
                if display_mode & config.MODE_HAM:
                    raise Exception("HAM mode not supported")
            elif chunk.getname() == b'BMHD':
                #bitmap header
                bmhd_bytes = chunk.read()
                (w,h,x,y,nPlanes,masking,compression,pad1,transparentColor,xAspect,yAspect,pageWidth,pageHeight) = unpack(">HHhhBBBBHBBhh", bmhd_bytes)
                config.pal = config.pal[0:1<<nPlanes]
                if nPlanes <= 6:
                    config.color_depth = 16
                else:
                    config.color_depth = 256
            elif chunk.getname() == b'CMAP':
                #color map header
                cmap_bytes = chunk.read()
                ncol = len(cmap_bytes)//3
                while len(config.pal) < ncol:
                    config.pal.append((0,0,0))
                for i in range(ncol):
                    config.pal[i] = unpack(">BBB", cmap_bytes[i*3:(i+1)*3])
            elif chunk.getname() == b'BODY':
                #bitmap (interleaved)
                body_bytes = chunk.read()
                pic = pygame.Surface((w2b(w)*8, h),0, depth=8)
                surf_array = pygame.surfarray.pixels2d(pic)  # Create an array from the surface.
                decode_ilbm_body(body_bytes, compression, nPlanes, surf_array)
                surf_array = None

                if display_mode > 0 and display_mode & config.MODE_EXTRA_HALFBRIGHT:
                    for i in range(32):
                        config.pal[i+32] = (config.pal[i][0]//2, config.pal[i][1]//2, config.pal[i][2]//2)

                pic.set_palette(config.pal)
                #pic = pygame.image.load(filename)
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
    config.loadpal = list(config.pal)

    #crop image to actual bitmap size
    if w != w2b(w)*8:
        newpic = pygame.Surface((w, h), 0, pic)
        newpic.set_palette(config.pal)
        newpic.blit(pic, (0,0))
        return newpic

    return pic

def load_pic(filename):
    ifftype = iff_type(filename)
    if ifftype == "ILBM":
        pic = load_iff(filename, config)
        config.pal = config.quantize_palette(config.pal, config.color_depth)
        pic.set_palette(config.pal)
    elif ifftype != "NONE":
        cranges = []
        pic = pygame.image.load(filename)
        if pic.get_bitsize() > 8:
            config.pal = get_truecolor_palette(pic.convert(), 256)
            config.color_depth = 256
            pic = convert8(pic, config.pal, is_bgr=True)
        else:
            config.pal = pic.get_palette()
            config.color_depth = 256
            
        iffinfo_file = re.sub(r"\.[^.]+$", ".iffinfo", filename)
        if iff_type(iffinfo_file) == "ILBM":
            load_iff(iffinfo_file, config)
        else:
            config.display_mode = -1

        config.pal = config.quantize_palette(pic.get_palette(), config.color_depth)
        pic.set_palette(config.pal)

        while len(cranges) < 6:
            cranges.append(colorrange(0,1,0,0))
        config.cranges = cranges
    else:
        pic = config.pixel_canvas

    #Guess display mode
    if config.display_mode < 0:
        config.color_depth = 256
        if pic.get_width() > 320 or pic.get_height() > 200:
            #Assume square pixel VGA
            config.display_mode = config.VGA_MONITOR_ID | config.MODE_HIRES | config.MODE_LACE
            config.scanlines = config.SCANLINES_OFF
        else:
            config.display_mode = config.NTSC_MONITOR_ID # Low Res 320x200

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
def save_iff(filename, config):
    nPlanes = int(math.log(len(config.pal),2))
    newfile = open(filename, 'wb')
    newfile.write(b'FORM\0\0\0\0ILBM')
    
    write_chunk(newfile, b'BMHD', pack(">HHhhBBBBHBBhh", \
        config.pixel_width, config.pixel_height, \
        0,0, \
        nPlanes, \
        0, \
        1, \
        0, \
        0, \
        10, 11, \
        config.pixel_width, config.pixel_height
        ))

    cmap_chunk = b''
    for col in config.truepal:
        cmap_chunk += pack(">BBB", col[0], col[1], col[2])
    write_chunk(newfile, b'CMAP', cmap_chunk)

    write_chunk(newfile, b'CAMG', pack(">I", config.display_mode))

    for crange in config.cranges:
        write_chunk(newfile, b'CRNG', pack(">HHHBB", 0, crange.rate, crange.get_flags(), crange.low, crange.high))

    body = b''
    out_canvas = config.pixel_canvas
    w,h = out_canvas.get_size()
    if w != w2b(w):
        out_canvas = pygame.Surface((w2b(w)*8, h),0, depth=8)
        out_canvas.set_palette(config.pal)
        out_canvas.blit(config.pixel_canvas, (0,0))
    surf_array = pygame.surfarray.pixels2d(out_canvas)  # Create an array from the surface.
    planes_out = c2p(surf_array)
    #body = planes_out[:,:nPlanes,:].tobytes()
    for y in range(0,len(planes_out)):
        for p in range(0,nPlanes):
            body += byterun_encode(planes_out[y,p,:].flatten()).tobytes()

    write_chunk(newfile, b'BODY', body)

    close_iff(newfile)

#save picture
def save_pic(filename, config):
    if '.' not in filename:
        filename += ".iff"
    if (len(filename) > 4 and filename[-4:].lower() == ".iff") or \
       (len(filename) > 5 and filename[-5:].lower() == ".ilbm"):
        save_iff(filename, config)
    else:
        pygame.image.save(config.pixel_canvas, filename)
