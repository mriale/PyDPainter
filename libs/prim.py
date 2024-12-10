#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import math
import numpy as np
from operator import itemgetter
import os.path
import random
import copy
import colorsys
from libs.menureq import *

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

config = None

def prim_set_config(config_in):
    global config
    config = config_in

symm_mat = None
symm_mat_num = 0
symm_center = [0,0]
hlines = []
vlines = {}
ell_mat = None
ell_angle = 0
ell_coords = (-1,-1)

def onscreen(coords):
    w = config.pixel_width
    h = config.pixel_height
    x,y = coords
    if x >= 0 and x < w and \
       y >= 0 and y < h:
        return True
    else:
        return False

#Check if rectangle is at least partially on screen
def rect_onscreen(rect):
    w = config.pixel_width
    h = config.pixel_height

    lx = rect[0]
    ly = rect[1]
    rx = lx + rect[2]
    ry = ly + rect[3]

    #rectangle is to the left or right of the screen
    if lx > w or rx < 0:
        return False

    #rectangle is above or below the screen
    if ly > h or ry < 0:
        return False

    return True

def add_bounds(coords):
    x,y = coords

    if x < config.fillmode.bounds[0]:
        config.fillmode.bounds[0] = x
    if y < config.fillmode.bounds[1]:
        config.fillmode.bounds[1] = y
    if x > config.fillmode.bounds[2]:
        config.fillmode.bounds[2] = x
    if y > config.fillmode.bounds[3]:
        config.fillmode.bounds[3] = y

def start_shape():
    global hlines
    global vlines
    hlines = []
    vlines = {}

def end_shape(screen, color, primprops=None, interrupt=False):
    global vlines
    drawhlines(screen, color, primprops=primprops, interrupt=interrupt)
    hlines = []
    drawvlines(screen, color, primprops=primprops, interrupt=interrupt)
    vlines = {}

def symm_coords_list(coords, handlesymm=True, interrupt=False):
    n = len(coords)
    coords_symm = np.array([],dtype=np.int32)
    symm_len = 0
    last_symm_coords = None
    for i in range(n):
        if interrupt and config.has_event(8) and last_symm_coords != None:
            coords_symm = np.append(coords_symm, last_symm_coords)
        else:
            last_symm_coords = symm_coords(coords[i], handlesymm=handlesymm, interrupt=interrupt)
            coords_symm = np.append(coords_symm, last_symm_coords)
        if i == 0:
            symm_len = len(coords_symm)//2

    coords_symm = coords_symm.reshape(n,symm_len,2).transpose(1,0,2)
    return coords_symm


def symm_coords(coords, handlesymm=True, interrupt=False):
    global symm_mat
    global symm_mat_num
    global symm_center
    x,y = coords
    newcoords = []
    newcoords.append(coords)
    if not handlesymm:
        return newcoords

    if config.symm_on:
        if config.symm_mode == 0:
            cx,cy = config.symm_center
            w,h = (config.pixel_width, config.pixel_height)

            if config.true_symmetry:
                if cx == w // 2 and w % 2 == 0:
                    cx -= 0.5
                if cy == h // 2 and h % 2 == 0:
                    cy -= 0.5
 
            c = (cx,cy)

            if config.symm_num > 0:
                if config.symm_type == 1:
                    x1 = (c[0]*2) - x
                    newcoords.append((x1, y))
                if symm_mat_num != config.symm_num or symm_center != c:
                    symm_mat_num = config.symm_num
                    symm_center = c
                    q = 2.0 * math.pi / config.symm_num
                    #recalculate matrix
                    trans1   = np.matrix([[    1,     0, 0],
                                          [    0,     1, 0],
                                          [-c[0], -c[1], 1]])
                    scale1   = np.matrix([[1/config.aspectX, 0, 0],
                                          [0, 1/config.aspectY, 0],
                                          [0, 0, 1]])
                    rot      = np.matrix([[ math.cos(q), math.sin(q), 0],
                                          [-math.sin(q), math.cos(q), 0],
                                          [           0,           0, 1]])
                    scale2   = np.matrix([[config.aspectX, 0, 0],
                                          [0, config.aspectY, 0],
                                          [0, 0, 1]])
                    trans2   = np.matrix([[ 1, 0, 0],
                                          [ 0, 1, 0],
                                          [ c[0],  c[1], 1]])
                    symm_mat = trans1 @ scale1 @ rot @ scale2 @ trans2
                xf,yf = x,y
                for i in range(config.symm_num-1):
                    if interrupt and config.has_event(8):
                        newcoords.append((int(round(x)), int(round(y))))
                    else:
                        xyvect = np.matmul(np.matrix([[xf,yf,1]]),symm_mat)
                        xf = xyvect[0,0]
                        yf = xyvect[0,1]
                        newcoords.append((int(round(xf)),int(round(yf))))

                        #mirror
                        if config.symm_type == 1:
                            x1 = (c[0]*2) - xf
                            newcoords.append((int(round(x1)), int(round(yf))))
        #tiled
        elif config.symm_mode == 1:
            numcols = (config.pixel_width // config.symm_width) + 1
            numrows = (config.pixel_height // config.symm_height) + 1
            newcoords = []
            x0 = x
            for xr in range(numcols):
                y0 = y
                for yr in range(numrows):
                    newcoords.append((x0,y0))
                    y0 = y0 + config.symm_height
                x0 = x0 + config.symm_width
            x0 = x
            for xr in range(numcols):
                y0 = y
                x0 = x0 - config.symm_width
                for yr in range(numrows):
                    newcoords.append((x0,y0))
                    y0 = y0 + config.symm_height
            x0 = x
            for xr in range(numcols):
                y0 = y
                for yr in range(numrows):
                    y0 = y0 - config.symm_height
                    newcoords.append((x0,y0))
                x0 = x0 + config.symm_width
            x0 = x
            for xr in range(numcols):
                y0 = y
                x0 = x0 - config.symm_width
                for yr in range(numrows):
                    y0 = y0 - config.symm_height
                    newcoords.append((x0,y0))
    return newcoords

def blend_images(img1, img2, blend_trans):
    # Blend two images together and put back into img1
    ia1 = pygame.surfarray.pixels2d(img1)
    ia2 = pygame.surfarray.pixels2d(img2)

    # Use transformation matrix to blend colors
    ia1[:,:] = blend_trans[(ia1[:,:]), (ia2[:,:])]

    ia1 = None
    ia2 = None

def smooth_image(img):
    # Create input and output 24-bit images to smooth
    w,h = img.get_size()
    i24 = pygame.Surface((w+2, h+2), 0, 24)
    i24.blit(img, (1,1))
    i24_array = pygame.surfarray.pixels3d(i24)
    imgain = np.array(i24_array, dtype=np.uint16, copy=True)
    imgaout = np.zeros_like(i24_array, dtype=np.uint16)

    """
    Gaussian blur 3x3 =
    [ 1 2 1 ]
    [ 2 4 2 ]
    [ 1 2 1 ]

    Use convolution to apply 3x3 matrix to pixels.
    We can use bit shifting instead of multiplication since all the values
    in the matrix are powers of 2.
    """

    imgaout[1:-1,1:-1,:] += imgain[0:-2,0:-2,:]
    imgaout[1:-1,1:-1,:] += imgain[1:-1,0:-2,:] << 1
    imgaout[1:-1,1:-1,:] += imgain[2:,  0:-2,:]
    imgaout[1:-1,1:-1,:] += imgain[0:-2,1:-1,:] << 1
    imgaout[1:-1,1:-1,:] += imgain[1:-1,1:-1,:] << 2
    imgaout[1:-1,1:-1,:] += imgain[2:,  1:-1,:] << 1
    imgaout[1:-1,1:-1,:] += imgain[0:-2,2:,  :]
    imgaout[1:-1,1:-1,:] += imgain[1:-1,2:,  :] << 1
    imgaout[1:-1,1:-1,:] += imgain[2:,  2:,  :]
    imgaout >>= 4

    # Assign the output of the smoothing back in the 24-bit version of the input
    i24_array[:,:,:] = imgaout[:,:,:]
    i24_array = None

    # Convert the 24-bit image back to indexed color and blit into original
    i8 = convert8(i24, config.pal)
    img.blit(i8, (-1,-1))

def tint_image(img, tint_trans):
    # Tint the image based on the tint translation array
    ia = pygame.surfarray.pixels2d(img)

    # Use transformation matrix to tint colors
    ia[:] = tint_trans[ia[:]]

    ia = None
    return img

class BrushCache:
    """This class models brush images that are ready to stamp on the screen"""
    def __init__(self):
        self.image = []
        self.type = []
        self.bgcolor = []
        for i in range(257):
            self.image.append(None)
            self.type.append(-1)
            self.bgcolor.append(-1)

class BrushFrame:
    def __init__(self, brush, image):
        self.image = image.copy()
        self.image_orig = image.copy()
        self.image_backup = image.copy()
        self.cache = BrushCache()
        self.size = brush.size
        self.aspect = brush.aspect
        self.rect = brush.rect
        self.handle_frac = brush.handle_frac

class Brush:
    """This class models a brush that can be stamped on the screen"""
    CUSTOM = 0
    CIRCLE = 1
    SQUARE = 2
    SPRAY = 3

    CENTER = 0
    CORNER_UL = 1
    CORNER_UR = 2
    CORNER_LR = 3
    CORNER_LL = 4
    PLACE = 5

    def __init__(self, type=CIRCLE, size=1, screen=None, bgcolor=0, coordfrom=None, coordto=None, pal=None, polylist=None, animbrush=False, image=None):
        self.handle_type = self.CENTER
        if type == Brush.CUSTOM:
            if image is None:
                self.image = self.get_image_from_screen(screen, bgcolor=bgcolor, coordfrom=coordfrom, coordto=coordto, pal=pal, polylist=polylist, animbrush=animbrush)
            else:
                self.image = image.copy()

            w,h = self.image.get_size()
            self.__type = type
            self.bgcolor = bgcolor
            self.image_orig = self.image.copy()
            self.image_backup = self.image.copy()
            self.bgcolor_orig = bgcolor
            self.__size = h
            self.aspect = 1.0
            self.calc_handle(w, h)
            self.frame = list([BrushFrame(self, self.image)])
            self.animbrush = animbrush
        else:
            self.image = None
            self.rect = [0,0,size,size]
            self.__type = type
            self.bgcolor = bgcolor
            self.image_orig = None
            self.bgcolor_orig = bgcolor
            self.__size = size
            self.aspect = 1.0
            self.calc_handle(size, size)
            self.frame = []
            self.animbrush = False

        self.cache = BrushCache()
        self.smear_stencil = None
        self.smear_image = None
        self.smear_count = 0
        self.blend2_image = None
        self.prev_x = None
        self.prev_y = None
        self.pen_down = False
        self.cycle_pos = np.zeros(6, dtype=np.uint8)
        self.cycle_trans = np.arange(0,256, dtype=np.uint8)
        self.cycle_trans_back = np.arange(0,256, dtype=np.uint8)
        self.blend_trans = np.empty((256,256), dtype=np.uint8)
        self.tint_trans = np.empty((256), dtype=np.uint8)
        self.currframe = 0
        self.startframe = 0
        self.endframe = 0

        if pal == None and "pal" in dir(config):
            self.pal = config.pal
        else:
            self.pal = pal

    def get_image_from_screen(self, screen, bgcolor=0, coordfrom=None, coordto=None, pal=None, polylist=None, animbrush=False):
        exclbrush = config.grid_on and config.exclbrush

        # Get bounds of polygon brush
        if polylist != None:
            minx = min(polylist,key=itemgetter(0))[0];
            maxx = max(polylist,key=itemgetter(0))[0];
            miny = min(polylist,key=itemgetter(1))[1];
            maxy = max(polylist,key=itemgetter(1))[1];
            coordfrom = (minx, miny)
            coordto = (maxx, maxy)
        else:
            # Rectangle brush
            if coordfrom == None:
                coordfrom = (0,0)
            if coordto == None:
                coordto = (screen.get_width()-1, screen.get_height()-1)
                exclbrush = False

        x1,y1 = coordfrom
        x2,y2 = coordto

        if x1 > x2:
            x1, x2 = x2, x1

        if y1 > y2:
            y1, y2 = y2, y1

        w = x2-x1
        h = y2-y1

        if not exclbrush:
            w += 1
            h += 1

        image = pygame.Surface((w, h),0, config.pixel_canvas)
        image.set_palette(config.pal)
        image.blit(screen, (0,0), (x1,y1,w,h))
        image.set_colorkey(bgcolor)

        # Handle stencil masking
        if config.stencil.enable:
            brush_pixels = pygame.surfarray.pixels2d(image)
            m = np.array(config.stencil.mask).transpose()
            m -= [x1, y1]
            m = m[ (m[:,0] >= 0) & (m[:,0] <= (w-1)) &
                   (m[:,1] >= 0) & (m[:,1] <= (h-1)) ]
            m = m.transpose()
            m = tuple(m)
            brush_pixels[m] = bgcolor
            brush_pixels = None

        # Handle polygon masking
        if polylist != None:
            # Adjust polylist to brush coords
            pl = []
            for x,y in polylist:
                pl.append((x-x1,y-y1))

            # Create image same size as brush and draw poly into it
            polyimage = pygame.Surface((w, h),0, config.pixel_canvas)
            primprops = PrimProps()
            fillpoly(polyimage, 1, pl, handlesymm=False, primprops=primprops)

            # Create numpy mask out of poly and apply to brush
            surf_array_poly = pygame.surfarray.pixels2d(polyimage)
            poly_mask = np.where(surf_array_poly == 0)
            surf_array_brush = pygame.surfarray.pixels2d(image)
            surf_array_brush[poly_mask] = bgcolor
            surf_array_brush = None
            surf_array_poly = None
            polyimage = None
        return image

    def calc_handle(self, w, h):
        if self.handle_type == self.CENTER:
            self.handle_frac = [0.5, 0.5]
        elif self.handle_type == self.CORNER_UL:
            self.handle_frac = [0.0, 0.0]
        elif self.handle_type == self.CORNER_UR:
            self.handle_frac = [1.0, 0.0]
        elif self.handle_type == self.CORNER_LR:
            self.handle_frac = [1.0, 1.0]
        elif self.handle_type == self.CORNER_LL:
            self.handle_frac = [0.0, 1.0]

        self.handle = [int(w*self.handle_frac[0]), int(h*self.handle_frac[1])]
        self.rect = [-self.handle[0], -self.handle[1], w, h]

    def get_wh(self):
        if self.type == Brush.CUSTOM:
            return self.image.get_size()
        else:
            ax = config.aspectX
            ay = config.aspectY
            if self.type == Brush.SQUARE:
                return ((self.size+1)*ax, (self.size+1)*ay)
            elif self.type == Brush.SPRAY:
                return ((self.size*3*ax+1, self.size*3*ay+1))
            elif self.type == Brush.CIRCLE or self.type == Brush.SPRAY:
                if self.size == 1:
                    return (1, 1)
                else:
                    return (self.size*2*ax, self.size*2*ay)


    def scale(self, image_in):
        size = self.__size
        image = image_in.copy()
        image.set_palette(config.pal)
        w,h = image.get_size()
        if self.aspect != 1.0 or size != h:
            factor = size / h
            w = int(w*factor*self.aspect)
            h = int(h*factor)
            image = pygame.transform.scale(image, (w, h))
        self.calc_handle(w,h)
        return image

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, size):
        if self.type == Brush.CUSTOM:
            if size < 1:
                size = 1
            elif size > 2000:
                size = 2000
            self.__size = size
            self.cache = BrushCache()
            self.image = self.scale(self.image_orig)
        else:
            if size < 1:
                size = 1
                if self.type == Brush.SQUARE or self.type == Brush.SPRAY:
                    self.__type = Brush.CIRCLE
            elif size > 100:
                size = 100
            self.__size = size
            self.cache = BrushCache()

            ax = config.aspectX
            ay = config.aspectY

            if self.type == Brush.SQUARE:
                self.calc_handle((size+1)*ax, (size+1)*ay)
            elif self.type == Brush.CIRCLE or self.type == Brush.SPRAY:
                if size == 1:
                    self.calc_handle(1, 1)
                else:
                    self.calc_handle(size*2*ax, size*2*ay)

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, type):
        if type != self.__type:
            self.__type = type
            self.size = self.__size  #recalc handle and wipe cache

    def set_palettes(self, pal):
        if self.type != Brush.CUSTOM:
            return
        self.image.set_palette(pal)
        for frame in self.frame:
            frame.image.set_palette(pal)
        self.cache = BrushCache()

    def add_frame(self, image):
        self.frame.append(BrushFrame(self, image))

    def save_frame(self):
        if not self.animbrush:
            return
        frameno = self.currframe
        if len(self.frame) > 0:
            self.frame[frameno].image = self.image
            self.frame[frameno].image_orig = self.image_orig
            self.frame[frameno].image_backup = self.image_backup
            self.frame[frameno].size = self.size
            self.frame[frameno].aspect = self.aspect
            self.frame[frameno].cache = self.cache
            self.frame[frameno].rect = list(self.rect)
            self.frame[frameno].handle_frac = list(self.handle_frac)

    def set_frame(self, frameno, doAction=True):
        if not self.animbrush:
            return
        if frameno < 0:
            frameno = len(self.frame)-1
        elif frameno >= len(self.frame):
            frameno = 0

        self.save_frame()
        self.currframe = frameno

        if len(self.frame) > 0:
            self.image = self.frame[frameno].image
            self.image_orig = self.frame[frameno].image_orig
            self.image_backup = self.frame[frameno].image_backup
            self.cache = self.frame[frameno].cache
            self.rect = list(self.frame[frameno].rect)
            self.handle_frac = list(self.frame[frameno].handle_frac)
            self.aspect = self.frame[frameno].aspect
            self.__size = self.frame[frameno].size

        if doAction:
            config.doKeyAction()

    def first_frame(self, doAction=True):
        frameno = 0
        self.set_frame(frameno, doAction)

    def last_frame(self, doAction=True):
        frameno = -1
        self.set_frame(frameno, doAction)

    def next_frame(self, doAction=True):
        frameno = self.currframe + 1
        self.set_frame(frameno, doAction)

    def prev_frame(self, doAction=True):
        frameno = self.currframe - 1
        self.set_frame(frameno, doAction)

    def iter_progress_anim(self, percent):
        curr_time = pygame.time.get_ticks()
        if curr_time - self.iter_prev_time > 33:
            if self.iter_progress_req is None:
                self.iter_progress_req = open_progress_req(config.pixel_req_canvas, "Processing...")
            self.iter_prev_time = curr_time
            update_progress_req(self.iter_progress_req, config.pixel_req_canvas, percent)

    def __iter__(self):
        self.iter_frames = [*range(0,len(self.frame))]
        self.curr_frame_bak = self.currframe
        self.iter_len = len(self.iter_frames)
        self.iter_prev_time = pygame.time.get_ticks()
        self.iter_progress_req = None
        return self

    def __next__(self):
        if len(self.iter_frames) == 0:
            self.set_frame(self.curr_frame_bak, doAction=False)
            if self.iter_progress_req:
                close_progress_req(self.iter_progress_req)
            raise StopIteration
        self.iter_progress_anim((self.iter_len-len(self.iter_frames)) / self.iter_len)
        frame_no = self.iter_frames.pop(0)
        self.set_frame(frame_no, doAction=False)
        return frame_no

    def render_image(self, color):
        ax = config.aspectX
        ay = config.aspectY

        if self.type == Brush.CUSTOM:
            #convert brush image to single color
            image = self.scale(self.image_orig)
            image.set_palette(config.pal)
            surf_array = pygame.surfarray.pixels2d(image)
            bgcolor = self.bgcolor_orig
            if bgcolor == color:
                bgcolor = (color+1) % config.NUM_COLORS
                tfarray = np.not_equal(surf_array, self.bgcolor_orig)
                surf_array[tfarray] = color
                surf_array[np.logical_not(tfarray)] = bgcolor
            else:
                surf_array[np.not_equal(surf_array, bgcolor)] = color
            surf_array = None
            self.color = color
            image.set_colorkey(bgcolor)
            return image
        elif self.type == Brush.CIRCLE:
            if self.size == 1:
                image = pygame.Surface((1,1),0, config.pixel_canvas)
                image.set_palette(config.pal)
                if color == 0:
                    image.set_colorkey(1)
                else:
                    image.set_colorkey(0)
                image.fill(color)
            else:
                image = pygame.Surface((self.size*ax*2+1, self.size*ay*2+1),0, config.pixel_canvas)
                image.set_palette(config.pal)
                if color == 0:
                    image.fill(1)
                    image.set_colorkey(1)
                else:
                    image.set_colorkey(0)
                primprops = PrimProps()
                if ax == ay == 1:
                    fillcircle(image, color, (self.size, self.size), self.size-1, primprops=primprops)
                else:
                    pygame.draw.ellipse(image, color, (1,1,self.size*ax*2-1, self.size*ay*2-1))
            return image
        elif self.type == Brush.SQUARE:
            image = pygame.Surface((self.size*ax+1, self.size*ay+1),0, config.pixel_canvas)
            image.set_palette(config.pal)
            if color == 0:
                image.set_colorkey(1)
            else:
                image.set_colorkey(0)
            image.fill(color)
            return image
        elif self.type == Brush.SPRAY:
            image = pygame.Surface((self.size*3*ax+1, self.size*3*ay+1),0, config.pixel_canvas)
            w,h = image.get_size()
            self.calc_handle(w,h)
            image.set_palette(config.pal)
            
            if color == 0:
                image.set_colorkey(1)
                image.fill(1)
            else:
                image.set_colorkey(0)

            if self.size == 1:
                image.set_at((0,1), color)
                image.set_at((2,0), color)
                image.set_at((2,2), color)
            elif self.size == 2:
                image.set_at((3,0), color)
                image.set_at((0,2), color)
                image.set_at((3,3), color)
                image.set_at((6,3), color)
                image.set_at((3,5), color)
            elif self.size > 2:
                old_state = random.getstate()
                random.seed(self.size)
                for i in range(0, self.size * 3):
                    image.set_at(config.airbrush_coords(w//2, h//2, size=self.size*1.5), color)
                random.setstate(old_state)

            return image

    def draw(self, screen, color, coords, handlesymm=True, primprops=None, erase=False):
        if not rect_onscreen([coords[0]+self.rect[0],
                              coords[1]+self.rect[1],
                              self.rect[2],
                              self.rect[3]]):
            return

        image = None
        if primprops == None:
            primprops = config.primprops
        drawmode = primprops.drawmode.value

        #handle pen state
        if self.pen_down == False:
            if drawmode in (DrawMode.SMEAR, DrawMode.SHADE, DrawMode.BLEND, DrawMode.SMOOTH, DrawMode.TINT):
                self.cache.image[256] = None
                self.prev_x = None
                self.prev_y = None
                self.smear_image = None
            if drawmode == DrawMode.CYCLE and config.multicycle and self.type == Brush.CUSTOM:
                pass
            elif drawmode not in (DrawMode.MATTE, DrawMode.REPLACE):
                drawmode = DrawMode.COLOR

        #handle erase with background color
        if drawmode in (DrawMode.MATTE, DrawMode.SMEAR, DrawMode.BLEND, DrawMode.SMOOTH, DrawMode.TINT) and erase:
            drawmode = DrawMode.COLOR

        if drawmode == DrawMode.MATTE:
            if self.image != None:
                image = self.image
                image.set_colorkey(self.bgcolor_orig)
        elif drawmode == DrawMode.REPLACE:
            if self.image != None:
                if erase:
                    image = pygame.Surface(self.image.get_size(), 0, self.image)
                    image.set_palette(config.pal)
                    image.fill(color)
                else:
                    image = self.image
                    image.set_colorkey(None)
        elif drawmode == DrawMode.CYCLE and config.multicycle and self.type == Brush.CUSTOM:
            #update offset for current cycle range
            crange = config.get_range(color)
            coffset=0
            if crange is None:
                #don't cycle because color not in range
                self.cycle_pos[:] = 0
            else:
                coffset = color - crange.low
                crange_index = config.cranges.index(crange)
                self.cycle_pos[crange_index] = coffset
                #update offsets for other cycle ranges
                for i in range(len(config.cranges)):
                    if i != crange_index:
                        crange = config.cranges[i]
                        self.cycle_pos[i] = crange.curr_color(crange.low, coffset) - crange.low
                
            #set up translation for color cycling
            self.cycle_trans = np.arange(0,256, dtype=np.uint8)
            for crange_index in range(len(config.cranges)):
                crange = config.cranges[crange_index]
                if crange.is_active() and crange.low < crange.high:
                    arange = crange.get_range()
                    for ci in arange:
                        self.cycle_trans[ci] = crange.curr_color(ci, self.cycle_pos[crange_index])
            #Color cycle brush
            image = self.image.copy()
            surf_array = pygame.surfarray.pixels2d(image)
            surf_array2 = self.cycle_trans[surf_array]
            np.copyto(surf_array, surf_array2)
            surf_array = None
            surf_array2 = None
            image.set_colorkey(self.bgcolor_orig)
        elif drawmode in (DrawMode.SMEAR, DrawMode.SHADE, DrawMode.BLEND, DrawMode.SMOOTH, DrawMode.TINT):
            if self.cache.image[256] == None:
                self.cache.image[256] = self.render_image(config.color)
                self.smear_image = None
                self.prev_x = None
                self.prev_y = None

                #create stencil for smear
                self.smear_stencil = self.cache.image[256].copy()
                ckey_rgb = self.smear_stencil.get_colorkey()[0:3]
                ckey = config.pal.index(ckey_rgb)
                surf_array = pygame.surfarray.pixels2d(self.smear_stencil)
                scolor = min(config.NUM_COLORS+1, 255)
                tfarray = np.not_equal(surf_array, ckey)
                surf_array[tfarray] = ckey
                surf_array[np.logical_not(tfarray)] = scolor
                surf_array = None
                self.smear_stencil.set_colorkey(ckey)

                if drawmode == DrawMode.SHADE:
                    #set up cycle translation array
                    self.cycle_trans = np.arange(0,256, dtype=np.uint8)
                    self.cycle_trans_back = np.arange(0,256, dtype=np.uint8)
                    found_range = False
                    for crange in config.cranges:
                        if not found_range and crange.is_active() and \
                           config.color >= crange.low and config.color <= crange.high:
                            found_range = True
                            arange = crange.get_range()
                            for ci in arange[0:-1]:
                                self.cycle_trans[ci] = crange.next_color(self.cycle_trans[ci])
                            crange.set_reverse(not crange.is_reverse())
                            arange = crange.get_range()
                            for ci in arange[0:-1]:
                                self.cycle_trans_back[ci] = crange.next_color(self.cycle_trans_back[ci])
                            crange.set_reverse(not crange.is_reverse())
                    if not found_range:
                        # Didn't find current color in any range so cycle all colors
                        self.cycle_trans[0:config.NUM_COLORS-1] = np.arange(1,config.NUM_COLORS, dtype=np.uint8)
                        self.cycle_trans[config.NUM_COLORS-1] = 0
                        self.cycle_trans_back[1:config.NUM_COLORS] = np.arange(0,config.NUM_COLORS-1, dtype=np.uint8)
                        self.cycle_trans_back[0] = config.NUM_COLORS-1
                elif drawmode == DrawMode.BLEND:
                    #set up blend translation matrix
                    self.blend_trans[:] = np.arange(0,256, dtype=np.uint8)
                    found_range = False
                    for crange in config.cranges:
                        if not found_range and crange.is_active() and \
                           config.color >= crange.low and config.color <= crange.high:
                            found_range = True
                            arange = crange.get_range()
                            for ci in arange:
                                for cj in arange:
                                    self.blend_trans[ci,cj] = (ci + cj) // 2
                    if not found_range:
                        for ci in range(0,256):
                            for cj in range(0,256):
                                self.blend_trans[ci,cj] = (ci + cj) // 2
                elif drawmode == DrawMode.TINT:
                    #set up tint translation matrix
                    self.tint_trans[:] = np.arange(0,256, dtype=np.uint8)
                    #get HSV of current color
                    r,g,b = config.pal[config.color]
                    ch,cs,cv = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                    i=0
                    for r,g,b in config.pal:
                        h,s,v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                        # To tint, keep value but replace hue and saturation
                        tr,tg,tb = colorsys.hsv_to_rgb(ch, cs, v)
                        tr = int(round(tr * 255.0))
                        tg = int(round(tg * 255.0))
                        tb = int(round(tb * 255.0))
                        # Search for nearest color
                        j=0
                        closest=0
                        closest_mag=255*255 + 255*255 + 255*255
                        for sr,sg,sb in config.pal:
                            smag = (sr-tr)*(sr-tr) + (sg-tg)*(sg-tg) + (sb-tb)*(sb-tb)
                            if smag < closest_mag:
                                closest = j
                                closest_mag = smag
                            j += 1
                        self.tint_trans[i] = closest
                        i += 1

            image = self.cache.image[256]
            self.calc_handle(image.get_width(), image.get_height())
        elif drawmode == DrawMode.COLOR or drawmode == DrawMode.CYCLE:
            if self.cache.image[color] == None:
                self.cache.image[color] = self.render_image(color)
            image = self.cache.image[color]

        if config.cycling and not image is None:
            image.set_palette(config.pal)

        for coord in symm_coords(coords, handlesymm=handlesymm):
            x,y = coord
            if not image is None and rect_onscreen([x+self.rect[0],
                                                    y+self.rect[1],
                                                    self.rect[2],
                                                    self.rect[3]]):
                if drawmode == DrawMode.SMEAR:
                    self.smear_count = (self.smear_count + 1) % 2
                    #Get canvas into smear image
                    if self.prev_x != None:
                        self.smear_image.blit(screen, (0,0), [self.prev_x - self.handle[0], self.prev_y - self.handle[1], self.rect[2], self.rect[3]])
                        self.smear_image.blit(self.smear_stencil, (0,0))
                    #Blit last stored brush down
                    if self.smear_image == None:
                        self.smear_image = pygame.Surface((self.rect[2], self.rect[3]),0, screen)
                        self.smear_image.set_palette(config.pal)
                        self.smear_image.set_colorkey(min(config.NUM_COLORS+1, 255))
                    elif self.smear_count == 0:
                        screen.blit(self.smear_image,
                                    (x - self.handle[0], y - self.handle[1]))

                    self.prev_x = x
                    self.prev_y = y
                elif drawmode == DrawMode.BLEND:
                    #Allocate blend2 image if needed
                    if self.blend2_image == None or self.blend2_image.get_size() != self.rect[2:4]:
                        self.blend2_image = pygame.Surface((self.rect[2], self.rect[3]),0, screen)
                        self.blend2_image.set_palette(config.pal)
                        self.blend2_image.set_colorkey(min(config.NUM_COLORS+1, 255))

                    self.smear_count = (self.smear_count + 1) % 2
                    #Get canvas into smear image
                    if self.prev_x != None:
                        self.smear_image.blit(screen, (0,0), [self.prev_x - self.handle[0], self.prev_y - self.handle[1], self.rect[2], self.rect[3]])
                        self.smear_image.blit(self.smear_stencil, (0,0))
                    #Blit last stored brush down
                    if self.smear_image == None:
                        self.smear_image = pygame.Surface((self.rect[2], self.rect[3]),0, screen)
                        self.smear_image.set_palette(config.pal)
                        self.smear_image.set_colorkey(min(config.NUM_COLORS+1, 255))
                    elif self.smear_count == 0:
                        #get canvas under brush
                        self.blend2_image.blit(screen, (0,0), [x - self.handle[0], y - self.handle[1], self.rect[2], self.rect[3]])
                        self.blend2_image.blit(self.smear_stencil, (0,0))
                        blend_images(self.smear_image, self.blend2_image, self.blend_trans)
                        screen.blit(self.smear_image,
                                    (x - self.handle[0], y - self.handle[1]))

                    self.prev_x = x
                    self.prev_y = y
                elif drawmode == DrawMode.SHADE:
                    #Allocate smear image if needed
                    if self.smear_image == None:
                        self.smear_image = pygame.Surface((self.rect[2], self.rect[3]),0, screen)
                        self.smear_image.set_palette(config.pal)
                        self.smear_image.set_colorkey(min(config.NUM_COLORS+1, 255))

                    #Get canvas into smear image
                    self.smear_image.blit(screen, (0,0), [x - self.handle[0], y - self.handle[1], self.rect[2], self.rect[3]])
                    self.smear_image.blit(self.smear_stencil, (0,0))

                    #Color cycle range
                    surf_array = pygame.surfarray.pixels2d(self.smear_image)
                    if color == config.bgcolor:
                        surf_array2 = self.cycle_trans_back[surf_array]
                    else:
                        surf_array2 = self.cycle_trans[surf_array]
                    np.copyto(surf_array, surf_array2)
                    surf_array = None
                    surf_array2 = None

                    #Blit shaded image
                    screen.blit(self.smear_image,
                                (x - self.handle[0], y - self.handle[1]))
                elif drawmode == DrawMode.SMOOTH:
                    #Allocate smooth image if needed
                    if self.smear_image == None:
                        self.smear_image = pygame.Surface((self.rect[2], self.rect[3]),0, screen)
                        self.smear_image.set_palette(config.pal)
                        self.smear_image.set_colorkey(min(config.NUM_COLORS+1, 255))

                    #Get canvas into smear image
                    self.smear_image.blit(screen, (0,0), [x - self.handle[0], y - self.handle[1], self.rect[2], self.rect[3]])
                    #self.smear_image.blit(self.smear_stencil, (0,0))

                    #Smooth image
                    smooth_image(self.smear_image)
                    self.smear_image.blit(self.smear_stencil, (0,0))

                    #Blit smoothed image
                    screen.blit(self.smear_image, (x - self.handle[0], y - self.handle[1]))
                elif drawmode == DrawMode.TINT:
                    #Allocate smooth image if needed
                    if self.smear_image == None:
                        self.smear_image = pygame.Surface((self.rect[2], self.rect[3]),0, screen)
                        self.smear_image.set_palette(config.pal)
                        self.smear_image.set_colorkey(min(config.NUM_COLORS+1, 255))

                    #Get canvas into smear image
                    self.smear_image.blit(screen, (0,0), [x - self.handle[0], y - self.handle[1], self.rect[2], self.rect[3]])

                    #Tint image
                    self.smear_image = tint_image(self.smear_image, self.tint_trans)
                    self.smear_image.blit(self.smear_stencil, (0,0))

                    #Blit tinted image
                    screen.blit(self.smear_image, (x - self.handle[0], y - self.handle[1]))
                else:
                    screen.blit(image, (x - self.handle[0], y - self.handle[1]))

        if self.pen_down and self.animbrush:
            self.next_frame(doAction=False)

    def set_startframe(self, startframe=-1):
        if startframe < 0:
            self.startframe = self.currframe
        else:
            self.startframe = startframe

    def reset_stroke(self):
        self.smear_count = 0
        self.endframe = self.currframe
        self.set_frame(self.startframe, doAction=False)

class CoordList:
    """This class stores a list of coordinates and renders it in the selected drawmode"""
    def __init__(self, numlists):
        self.numlists = numlists
        self.coordlist = []
        for i in range(0,numlists):
            self.coordlist.append([])

    def append(self, listnum, coord):
        self.coordlist[listnum].append(coord)

    def prepend(self, listnum, coord):
        self.coordlist[listnum].insert(0, coord)

    def draw(self, screen, color, drawmode=-1, xormode=-1, handlesymm=-1, interrupt=-1, primprops=None, erase=False, animpaint=True):
        numpoints = 0
        numcolors = 0
        pointspercolor = 0
        cyclemode = False
        cur_crange = None
        if primprops == None:
            drawmode = config.drawmode.value if drawmode == -1 else drawmode
            if xormode == True:
                primprops = PrimProps()
            else:
                primprops = copy.deepcopy(config.primprops)
        else:
            primprops = copy.deepcopy(primprops)
            drawmode = primprops.drawmode.value if drawmode == -1 else drawmode

        xormode = primprops.xor if xormode == -1 else xormode
        handlesymm = primprops.handlesymm if handlesymm == -1 else handlesymm
        interrupt = primprops.interrupt if interrupt == -1 else interrupt

        if animpaint and config.anim.num_frames > 1 and \
           not xormode and \
           config.xevent.is_key_down(config.xevent.ANIM_KEYS):
                if primprops.drawmode.spacing == DrawMode.CONTINUOUS:
                    primprops.drawmode.spacing = DrawMode.N_TOTAL
                    primprops.drawmode.n_total_value = config.anim.num_frames
        else:
            animpaint = False

        #handle color cycling
        arange = []
        if drawmode == DrawMode.CYCLE: 
            for crange in config.cranges:
                if crange.is_active() and color >= crange.low and color <= crange.high:
                    cyclemode = True
                    arange = crange.get_range()
                    numcolors = len(arange)
                    cur_crange = crange
                    color = arange[0]

        for i in range(0,self.numlists):
            numpoints += len(self.coordlist[i])
        numpoints += 1

        if cyclemode:
            pointspercolor = numpoints / numcolors

        currpoint = -1
        config.brush.set_startframe()
        config.brush.reset_stroke()
        for i in range(0,self.numlists):
            for c in self.coordlist[i]:
                currpoint += 1
                if cyclemode and pointspercolor > 0:
                    color = arange[int(currpoint / pointspercolor)]
                if primprops.continuous and primprops.drawmode.spacing == DrawMode.N_TOTAL and numpoints > 1 and currpoint != 0 and int(currpoint / ((numpoints-1) / primprops.drawmode.n_total_value)) == int((currpoint-1) / ((numpoints-1) / primprops.drawmode.n_total_value)):
                    continue
                if not primprops.continuous and primprops.drawmode.spacing == DrawMode.N_TOTAL and numpoints > 1 and currpoint != 0 and currpoint != numpoints-1 and int(currpoint / ((numpoints-1) / (primprops.drawmode.n_total_value-1))) == int((currpoint+1) / ((numpoints-1) / (primprops.drawmode.n_total_value-1))):
                    continue
                if primprops.drawmode.spacing == DrawMode.EVERY_N and currpoint % primprops.drawmode.every_n_value != 0:
                    continue

                if xormode:
                    if c[0] >= 0 and c[0] < screen.get_width() and \
                       c[1] >= 0 and c[1] < screen.get_height():
                        screen.set_at(c, screen.map_rgb(config.pixel_canvas.get_at(c))^(config.NUM_COLORS-1))
                else:
                    if primprops.drawmode.spacing == DrawMode.AIRBRUSH:
                        for j in range(primprops.drawmode.airbrush_value):
                            config.brush.draw(screen, color, config.airbrush_coords(c[0],c[1]), handlesymm=handlesymm, primprops=PrimProps(drawmode=drawmode), erase=erase)
                    else:
                        config.brush.draw(screen, color, c, handlesymm=handlesymm, primprops=PrimProps(drawmode=drawmode), erase=erase)

                    if animpaint and not interrupt:
                        config.save_undo()
                        config.anim.next_frame(doAction=False)
                        screen = config.pixel_canvas

                    if interrupt and config.has_event():
                        config.brush.reset_stroke()
                        return

                config.try_recompose()
        config.brush.reset_stroke()


class DrawMode:
    """This class describes the drawing modes for line drawing"""
    MATTE = 1
    COLOR = 2
    REPLACE = 3
    SMEAR = 4
    SHADE = 5
    BLEND = 6
    CYCLE = 7
    SMOOTH = 8
    TINT = 9
    HBRITE = 10
    LABEL_STR = ["","Matte","Color","Repl","Smear","Shade","Blend","Cycle","Smooth","Tint","HBrite"]

    CONTINUOUS = 0
    N_TOTAL = 1
    EVERY_N = 2
    AIRBRUSH = 3

    def __init__(self, value=2):
        self.value = value
        self.n_total_value = 20
        self.every_n_value = 8
        self.airbrush_value = 16
        self.spacing = DrawMode.CONTINUOUS

    def __str__(self):
        return DrawMode.LABEL_STR[self.value]


class FillMode:
    """This class describes the fill modes for solid shapes"""
    SOLID = 0
    TINT = 1
    BRUSH = 2
    WRAP = 3
    PERSPECTIVE = 4
    PATTERN = 5
    VERTICAL = 6
    VERT_FIT = 7
    HORIZONTAL = 8
    HORIZ_FIT = 9
    BOTH_FIT = 10
    ANTIALIAS = 11
    SMOOTH = 12
    LABEL_STR = ["Solid","Tint","Brush","Wrap","Perspective","Pattern",
                 "\x88\x89","\x8a\x8b","\x8c\x8d","\x8e\x8f", "\x90\x91",
                 "Antialias","Smooth"]
    NOBOUNDS = [65535,65535,-1,-1]
    ORDER4 = np.matrix([[ 0, 8, 2,10],
                        [12, 4,14, 6],
                        [ 3,11, 1, 9],
                        [15, 7,13, 5]], dtype="int8")

    def __init__(self, value=0):
        self.brush = None
        self.value = value
        self.gradient_dither = 4
        self.bounds = copy.copy(FillMode.NOBOUNDS)
        self.predraw = True
    def __str__(self):
        return FillMode.LABEL_STR[self.value]


class PrimProps:
    """This class stores properties for drawing and filling objects"""
    def __init__(self, drawmode=2, fillmode=0):
        self.color = 1
        self.drawmode = DrawMode(drawmode)
        self.fillmode = FillMode(fillmode)
        self.xor = False
        self.coordsonly = False
        self.handlesymm = False
        self.interrupt = False
        self.continuous = False


def calc_ellipse_curves(coords, width, height, handlesymm=True, angle=0):
    global ell_mat
    global ell_angle
    global ell_coords

    ccoords = []

    #Calculate curve segment coords
    xc,yc = coords
    controlw = width*716//1000
    controlh = height*716//1000
    ccoords = [(xc+width,yc),(xc,yc+height),(xc+controlw,yc+controlh),
               (xc,yc+height),(xc-width,yc),(xc-controlw,yc+controlh),
               (xc-width,yc),(xc,yc-height),(xc-controlw,yc-controlh),
               (xc,yc-height),(xc+width,yc),(xc+controlw,yc-controlh)]

    #rotate ellipse if needed
    if angle != 0:
        #recalc matrix only if necessary
        if angle != ell_angle or coords != ell_coords:
            ell_angle = angle
            ell_coords = coords
            q = angle * math.pi / 180.0
            trans1   = np.matrix([[  1,   0, 0],
                                  [  0,   1, 0],
                                  [-xc, -yc, 1]])
            scale1   = np.matrix([[1/config.aspectX, 0, 0],
                                  [0, 1/config.aspectY, 0],
                                  [0, 0, 1]])
            rot      = np.matrix([[ math.cos(q), math.sin(q), 0],
                                  [-math.sin(q), math.cos(q), 0],
                                  [           0,           0, 1]])
            scale2   = np.matrix([[config.aspectX, 0, 0],
                                  [0, config.aspectY, 0],
                                  [0, 0, 1]])
            trans2   = np.matrix([[  1,   0, 0],
                                  [  0,   1, 0],
                                  [ xc,  yc, 1]])
            ell_mat = trans1 @ scale1 @ rot @ scale2 @ trans2

        newcoords = []
        for i in range(len(ccoords)):
            xyvect = np.matmul(np.matrix([[ccoords[i][0],ccoords[i][1],1]]),ell_mat)
            xf = xyvect[0,0]
            yf = xyvect[0,1]
            ccoords[i] = (int(round(xf)),int(round(yf)))

    #run curve coords through symmetry calulations
    coords_out = symm_coords_list(ccoords, handlesymm=handlesymm)
    return coords_out

def drawellipse (screen, color, coords, width, height, filled=0, drawmode=-1, interrupt=False, angle=0, erase=False):
    if filled == 1:
        fillellipse(screen, color, coords, width, height, interrupt=interrupt, angle=angle, erase=erase)
        return

    ecurves = calc_ellipse_curves(coords, width, height, angle=angle)
    for i in range(len(ecurves)):
        cl = CoordList(12)
        for j in range (0,12,3):
            if interrupt and config.has_event():
                return
            coordfrom = (ecurves[i][j][0], ecurves[i][j][1])
            coordto = (ecurves[i][j+1][0], ecurves[i][j+1][1])
            coordcontrol = (ecurves[i][j+2][0], ecurves[i][j+2][1])
            cl.coordlist[j:j+3] = drawcurve(screen, color, coordfrom, coordto, coordcontrol, coordsonly=True, handlesymm=False)
        primprops = copy.copy(config.primprops)
        primprops.continuous = True
        cl.draw(screen, color, drawmode=drawmode, handlesymm=False, interrupt=interrupt, primprops=primprops, erase=erase)


def fillellipse (screen, color, coords, width, height, interrupt=False, primprops=None, angle=0, erase=False):
    if primprops == None:
        primprops = config.primprops
        handlesymm = True
    else:
        handlesymm = primprops.handlesymm

    xc,yc = coords

    if width == 0 and height == 0:
        fillrect(screen, color, (xc,yc), (xc,yc), erase=erase)
        return

    ecurves = calc_ellipse_curves(coords, width, height, handlesymm=handlesymm, angle=angle)
    for i in range(len(ecurves)):
        cl = CoordList(12)
        for j in range (0,12,3):
            coordfrom = (ecurves[i][j][0], ecurves[i][j][1])
            coordto = (ecurves[i][j+1][0], ecurves[i][j+1][1])
            coordcontrol = (ecurves[i][j+2][0], ecurves[i][j+2][1])
            cl.coordlist[j:j+3] = drawcurve(screen, color, coordfrom, coordto, coordcontrol, coordsonly=True, handlesymm=False)
            cl0 = [item for sublist in cl.coordlist for item in sublist]
            npcl = np.array(cl0, dtype=np.int32)
            sl = {}
            for j in range(0,npcl.shape[0]):
                x,y = npcl[j]
                if y in sl:
                    if sl[y][0] > x:
                        sl[y][0] = x
                    elif sl[y][1] < x:
                        sl[y][1] = x
                else:
                    sl[y] = [x,x]

        #find maxima
        config.fillmode.bounds = copy.copy(FillMode.NOBOUNDS)
        sslk = sorted(sl.keys())
        config.fillmode.bounds[1] = sslk[0]
        config.fillmode.bounds[3] = sslk[-1]
        for sly in sslk:
            if sl[sly][0] < config.fillmode.bounds[0]:
                config.fillmode.bounds[0] = sl[sly][0]
            if sl[sly][1] > config.fillmode.bounds[2]:
                config.fillmode.bounds[2] = sl[sly][1]

        start_shape()
        for sly in sslk:
            hline(screen, color, sly, sl[sly][0], sl[sly][1], primprops=primprops, erase=erase)
            if interrupt and config.has_event():
                return
            config.try_recompose()
        end_shape(screen, color, interrupt=interrupt, primprops=primprops)
        

def drawcircle(screen, color, coords_in, radius, filled=0, drawmode=-1, interrupt=False, erase=False):
    if filled == 1:
        fillcircle(screen, color, coords_in, radius, interrupt=interrupt, erase=erase)
        return

    coords_list = symm_coords(coords_in)
    for coords in coords_list:
        cl = CoordList(8)

        #midpoint circle algorithm
        x0,y0 = coords;
        x = 0
        y = radius
        err = (5 - radius*4)/4

        cl.append(0, (x0 + y, y0    ))
        cl.append(2, (x0    , y0 + y))
        cl.append(4, (x0 - y, y0    ))
        cl.append(6, (x0    , y0 - y))

        while x < y:
            if interrupt and config.has_event():
                return
            x = x + 1
            if err < 0:
                err += 2*x + 1
            else:
                y -= 1
                err += 2*(x-y) + 1

            cl.append (0, (x0 + y, y0 + x))
            cl.prepend(1, (x0 + x, y0 + y))
            cl.append (2, (x0 - x, y0 + y))
            cl.prepend(3, (x0 - y, y0 + x))
            cl.append (4, (x0 - y, y0 - x))
            cl.prepend(5, (x0 - x, y0 - y))
            cl.append (6, (x0 + x, y0 - y))
            cl.prepend(7, (x0 + y, y0 - x))

        primprops = copy.copy(config.primprops)
        primprops.continuous = True
        cl.draw(screen, color, drawmode=drawmode, handlesymm=False, interrupt=interrupt, primprops=primprops, erase=erase)

def add_xbounds(xbounds, y, x1, x2):
    if y in xbounds:
        xb1,xb2 = xbounds[y]
        if x1 < xb1:
            xb1 = x1
        if x2 > xb2:
            xb2 = x2
        xbounds[y] = [xb1, xb2]
    else:
        xbounds[y] = [x1, x2]

def fillcircle(screen, color, coords_in, radius, interrupt=False, primprops=None, erase=False):
    handlesymm = True
    if primprops != None:
        handlesymm = primprops.handlesymm

    coords_list = symm_coords(coords_in, handlesymm)
    for coords in coords_list:
        if interrupt and config.has_event():
            return
        x0,y0 = coords;
        x = 0
        y = radius
        err = (5 - radius*4)//4
        config.fillmode.bounds = [x0-radius, y0-radius, x0+radius, y0+radius]

        #Rasterize bounds of circle (sometimes y is repeated)
        xbounds = {}
        add_xbounds(xbounds, y0, x0-y, x0+y)
        while x < y:
            x = x + 1
            if err < 0:
                err += 2*x + 1
            else:
                y -= 1
                err += 2*(x-y) + 1

            add_xbounds(xbounds, y0 + y, x0 - x, x0 + x)
            add_xbounds(xbounds, y0 - y, x0 - x, x0 + x)
            add_xbounds(xbounds, y0 + x, x0 - y, x0 + y)
            add_xbounds(xbounds, y0 - x, x0 - y, x0 + y)

        #Draw the rasterized lines of the circle
        start_shape()
        for y in xbounds:
            x1,x2 = xbounds[y]
            hline(screen, color, y, x1, x2, interrupt=interrupt, primprops=primprops, erase=erase)
            if interrupt and config.has_event():
                return
            config.try_recompose()
        end_shape(screen, color, interrupt=interrupt, primprops=primprops)


def drawline_symm(screen, color, coordfrom, coordto, xormode=False, drawmode=-1, coordsonly=False, handlesymm=False, interrupt=False, skiplast=False, erase=False, animpaint=True):
    if (xormode and not handlesymm):
        coordfrom_list = [coordfrom]
        coordto_list = [coordto]
    else:
        coordfrom_list = symm_coords(coordfrom)
        coordto_list = symm_coords(coordto)
    for i in range(len(coordfrom_list)):
        if interrupt and config.has_event():
            return
        drawline(screen, color, coordfrom_list[i], coordto_list[i], xormode=xormode, drawmode=drawmode, coordsonly=False, handlesymm=False, interrupt=interrupt, skiplast=skiplast, erase=erase, animpaint=animpaint)

def draw_vert_xor_line(screen, x, y, y2, skiplast):
    w,h = screen.get_size()
    if x < 0 or x >= w:
        return
    if (y < 0 and y2 < 0) or (y >= h and y2 >= h):
        return
    if skiplast:
        y2 -= int(math.copysign(1, y2-y))
    if y2 < y:
        y,y2 = (y2,y)
    if y < 0:
        y = 0
    elif y >= h:
        y = h-1
    surf_array = pygame.surfarray.pixels2d(screen)
    vline_XOR(surf_array, x, y, y2+1)
    surf_array = None

def draw_horiz_xor_line(screen, y, x, x2, skiplast):
    w,h = screen.get_size()
    if y < 0 or y >= h:
        return
    if (x < 0 and x2 < 0) or (x >= w and x2 >= w):
        return
    if skiplast:
        x2 -= int(math.copysign(1, x2-x))
    if x2 < x:
        x,x2 = (x2,x)
    if x < 0:
        x = 0
    elif x >= w:
        x = w-1
    surf_array = pygame.surfarray.pixels2d(screen)
    hline_XOR(surf_array, y, x, x2+1)
    surf_array = None

def drawline(screen, color, coordfrom, coordto, xormode=False, drawmode=-1, coordsonly=False, handlesymm=False, interrupt=False, skiplast=False, erase=False, animpaint=True):
    x,y = int(coordfrom[0]), int(coordfrom[1])
    x2,y2 = int(coordto[0]), int(coordto[1])

    if xormode:
        if x == x2:
            draw_vert_xor_line(screen, x, y, y2, skiplast)
            return
        elif y == y2:
            draw_horiz_xor_line(screen, y, x, x2, skiplast)
            return

    cl = CoordList(1)

    #Bresenham line drawing algorithm thanks to:
    # http://tech-algorithm.com/articles/drawing-line-using-bresenham-algorithm/

    w = x2 - x
    h = y2 - y
    dx1 = 0
    dy1 = 0
    dx2 = 0
    dy2 = 0

    if w<0:
        dx1 = -1
    elif w>0:
        dx1 = 1
    if h<0:
        dy1 = -1
    elif h>0:
        dy1 = 1
    if w<0:
        dx2 = -1
    elif w>0:
        dx2 = 1

    longest = abs(w)
    shortest = abs(h)
    if not (longest > shortest):
        longest = abs(h)
        shortest = abs(w)
        if (h<0):
            dy2 = -1
        elif h>0:
            dy2 = 1
        dx2 = 0

    numerator = longest // 2
    if skiplast:
        rangehi = longest
    else:
        rangehi = longest+1
    for i in range(0, rangehi):
        cl.append(0, (x,y))
        numerator += shortest
        if not (numerator<longest):
            numerator -= longest
            x += dx1
            y += dy1
        else:
            x += dx2
            y += dy2

    if coordsonly:
        return cl.coordlist[0]

    cl.draw(screen, color, drawmode=drawmode, xormode=xormode, handlesymm=handlesymm, interrupt=interrupt, erase=erase, animpaint=animpaint)


#Bresenham Quardric Bezier curve algorithm from:
#http://members.chello.at/easyfilter/bresenham.html
def drawcurveseg(screen, color, coordfrom, coordcontrol, coordto):
    x0,y0 = coordfrom
    x1,y1 = coordcontrol
    x2,y2 = coordto
    sx = x2-x1
    sy = y2-y1
    xx = x0-x1
    yy = y0-y1
    xy = 0
    dx = 0.0
    dy = 0.0
    err = 0.0
    cur = float(xx*sy-yy*sx)
    coordlist = []

    if not (xx*sx <= 0 and yy*sy <= 0):
        return coordlist

    if sx*sx+sy*sy > xx*xx+yy*yy:
        x2 = x0
        x0 = sx+x1
        y2 = y0
        y0 = sy+y1
        cur = -cur

    if cur != 0:
        xx += sx

        if x0 < x2:
            sx = 1
        else:
            sx = -1

        xx *= sx
        yy += sy

        if y0 < y2:
            sy = 1
        else:
            sy = -1

        yy *= sy
        xy = 2*xx*yy
        xx *= xx
        yy *= yy

        if cur*sx*sy < 0:
            xx = -xx
            yy = -yy
            xy = -xy
            cur = -cur

        dx = 4.0*sy*cur*(x1-x0)+xx-xy
        dy = 4.0*sx*cur*(y0-y1)+yy-xy
        xx += xx
        yy += yy
        err = dx+dy+xy

        while True:
            coordlist.append((x0,y0))
            if x0 == x2 and y0 == y2:
                return coordlist
            y1 = 2.0*err < dx
            if 2.0*err > dy:
                x0 += sx
                dx -= float(xy)
                dy += float(yy)
                err += float(dy)
            if y1:
                y0 += sy
                dy -= float(xy)
                dx += float(xx)
                err += float(dx)
            if dy >= dx:
                break

    #drawline(screen, color, (x0,y0), (x2,y2))
    coordlist.extend(drawline(screen, color, (x0,y0), (x2,y2), coordsonly=True))
    
    return coordlist


def convert_curve_control(coordfrom, coordto, coordcontrol):
    #make coordcontrol a point on the curve
    x0,y0 = coordfrom
    x1,y1 = coordcontrol
    x2,y2 = coordto
    mx = (x0+x2) // 2
    my = (y0+y2) // 2
    dx = (x1-mx) * 2
    dy = (y1-my) * 2
    xout = dx + mx
    yout = dy + my
    return int(xout), int(yout)


#from: http://stackoverflow.com/questions/31757501/pixel-by-pixel-b%C3%A9zier-curve
def drawcurve(screen, color, coordfrom, coordto, coordcontrol, drawmode=-1, coordsonly=False, handlesymm=True, interrupt=False, erase=False):
    coordfrom_list = symm_coords(coordfrom, handlesymm)
    coordcontrol_list = symm_coords(coordcontrol, handlesymm)
    coordto_list = symm_coords(coordto, handlesymm)
    for j in range(len(coordfrom_list)):
        if interrupt and config.has_event():
            if coordsonly:
                return []
            else:
                return
        x0,y0 = coordfrom_list[j]
        x1,y1 = convert_curve_control(coordfrom_list[j], coordto_list[j], coordcontrol_list[j])
        x2,y2 = coordto_list[j]
        x = x0-x1
        y = y0-y1
        t = float(x0-2*x1+x2)
        r = 0.0

        cl = CoordList(3)

        if x*(x2-x1) > 0:
            if y*(y2-y1) > 0:
                if abs((y0-2*y1+y2)/t*x) > abs(y):
                    x0 = x2
                    x2 = x+x1
                    y0 = y2
                    y2 = y+y1

            t = (x0-x1)/t
            r = (1-t)*((1-t)*y0+2.0*t*y1)+t*t*y2
            t = (x0*x2-x1*x1)*t/(x0-x1)
            x = int(round(t))
            y = int(round(r))
            r = (y1-y0)*(t-x0)/(x1-x0)+y0
            cl.coordlist[0] = drawcurveseg(screen, color, (x0,y0), (x,int(round(r))), (x,y))
            r = (y1-y2)*(t-x2)/(x1-x2)+y2
            x0 = x
            x1 = x
            y0 = y
            y1 = int(round(r))

        if (y0-y1)*(y2-y1) > 0:
            t = float(y0-2*y1+y2)
            t = (y0-y1)/t
            r = (1-t)*((1-t)*x0+2.0*t*x1)+t*t*x2
            t = (y0*y2-y1*y1)*t/(y0-y1)
            x = int(round(r))
            y = int(round(t))
            r = (x1-x0)*(t-y0)/(y1-y0)+x0
            cl.coordlist[2] = drawcurveseg(screen, color, (x0,y0), (int(round(r)),y), (x,y))
            r = (x1-x2)*(t-y2)/(y1-y2)+x2
            x0 = x
            x1 = int(round(r))
            y0 = y
            y1 = y

        cl.coordlist[1] = drawcurveseg(screen, color, (x0,y0), (x1,y1), (x2,y2))

        #sort curve segments

        #find "from" point
        for i in range(0,3):
            if len(cl.coordlist[i]) > 0:
                if cl.coordlist[i][0] == coordfrom_list[j]:
                    cl.coordlist[i], cl.coordlist[0] = cl.coordlist[0], cl.coordlist[i]
                    break
                elif cl.coordlist[i][-1] == coordfrom_list[j]:
                    cl.coordlist[i], cl.coordlist[0] = cl.coordlist[0], list(reversed(cl.coordlist[i]))
                    break

        #find "to" point
        for i in range(0,3):
            if len(cl.coordlist[i]) > 0:
                if cl.coordlist[i][0] == coordto_list[j]:
                    cl.coordlist[i], cl.coordlist[2] = cl.coordlist[2], list(reversed(cl.coordlist[i]))
                    break
                elif cl.coordlist[i][-1] == coordto_list[j]:
                    cl.coordlist[i], cl.coordlist[2] = cl.coordlist[2], cl.coordlist[i]
                    break

        #swap center if needed
        if len(cl.coordlist[1]) > 0:
            if len(cl.coordlist[0]) > 0:
                if cl.coordlist[0][-1] != cl.coordlist[1][0]:
                    cl.coordlist[1].reverse()

        if coordsonly:
            return cl.coordlist

        cl.draw(screen, color, drawmode=drawmode, handlesymm=False, interrupt=interrupt, erase=erase)

def draw_ants(screen, coordfrom, coordto, step=4, offset=0):
    x1,y1 = coordfrom
    x2,y2 = coordto
    offsetr = (step - offset) % step

    #swap so x1,y1 is upper left and x2,y2 is lower right
    if x1 > x2:
        x1,x2 = (x2,x1)
    if y1 > y2:
        y1,y2 = (y2,y1)

    surf_array = pygame.surfarray.pixels2d(screen)
    hline_XOR(surf_array, y1, x1+offset, x2, step=step)
    hline_XOR(surf_array, y1, x1+offset+1, x2, step=step)
    vline_XOR(surf_array, x1, y1+offsetr, y2, step=step)
    vline_XOR(surf_array, x1, y1+offsetr+1, y2, step=step)
    hline_XOR(surf_array, y2, x1+offsetr, x2, step=step)
    hline_XOR(surf_array, y2, x1+offsetr+1, x2, step=step)
    vline_XOR(surf_array, x2, y1+offset, y2, step=step)
    vline_XOR(surf_array, x2, y1+offset+1, y2, step=step)
    surf_array = None

def drawrect(screen, color, coordfrom, coordto, filled=0, xormode=False, drawmode=-1, handlesymm=True, interrupt=False, erase=False):
    if filled:
        if handlesymm:
            fillrect_symm(screen, color, coordfrom, coordto, xormode=xormode, interrupt=interrupt, erase=erase)
        else:
            fillrect(screen, color, coordfrom, coordto, interrupt=interrupt, erase=erase)
        return
    x1,y1 = coordfrom
    x2,y2 = coordto

    drawpoly(screen, color, [(x1,y1), (x2,y1), (x2,y2), (x1,y2), (x1,y1)], xormode=xormode, drawmode=drawmode, handlesymm=handlesymm, interrupt=interrupt, skiplast=True, erase=erase)


def fillrect_symm(screen, color, coordfrom, coordto, xormode=False, handlesymm=True, interrupt=False, erase=False):
    fillrect(screen, color, coordfrom, coordto, interrupt=interrupt, erase=erase)
    x1,y1 = coordfrom
    x2,y2 = coordto

    rectlist = [[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]]
    rectlist_symm = symm_coords_list(rectlist, handlesymm)

    for i in range(1,len(rectlist_symm)):
        fillpoly(screen, color, rectlist_symm[i], handlesymm=False, interrupt=interrupt, erase=erase)
        if interrupt and config.has_event():
            return
        config.try_recompose()

def add_vline(y, xs1, xs2):
    for x in range(xs1,xs2+1):
        # append coords to vertical line lists
        if x in vlines:
            vlfound = False
            for vlx in vlines[x]:
                if y >= vlx[0] and y <= vlx[1]:
                    #fragment already in list
                    vlfound = True
                    break
                elif vlx[0]-1 == y:
                    #extend fragment up
                    vlx[0] = y
                    vlfound = True
                    break
                elif vlx[1]+1 == y:
                    #extend fragment down
                    vlx[1] = y
                    vlfound = True
                    break
            if not vlfound:
                #new fragment
                vlines[x].append([y,y])
        else:
            vlines[x] = [[y,y]]

def hline_XOR(surf_array, y, xs1, xs2, step=1):
    if surf_array.dtype == np.uint8:
        #indexed color
        surf_array[xs1:xs2:step,y] ^= config.NUM_COLORS-1
    else:
        #true color
        surf_array[xs1:xs2:step,y] ^= 0x00ffffff

def vline_XOR(surf_array, x, ys1, ys2, step=1):
    if surf_array.dtype == np.uint8:
        #indexed color
        surf_array[x,ys1:ys2:step] ^= config.NUM_COLORS-1
    else:
        #true color
        surf_array[x,ys1:ys2:step] ^= 0x00ffffff

def hline_SOLID(surf_array, color, y, xs1, xs2):
    #don't draw if off screen
    size = surf_array.shape
    if y<0 or y>=size[1]:
        return
    if xs1<0 and xs2<0:
        return
    if xs1>size[0] and xs2>size[0]:
        return

    #clip to edges of screen
    if xs1<0:
        xs1=0
    if xs2>size[0]-1:
        xs2=size[0]-1

    if surf_array.dtype == np.uint8:
        #indexed color
        surf_array[xs1:xs2+1,y] = color
    else:
        #true color
        surf_array[xs1:xs2+1,y] = (config.pal[color][0] << 16) | (config.pal[color][1] << 8) | (config.pal[color][2])

def hline_BRUSH(surf_array, y, x1, x2, xs1, xs2):
    if config.brush.image == None:
        hline_SOLID(surf_array, config.color, y, xs1, xs2)
        return

    brush_array = pygame.surfarray.pixels2d(config.brush.image)
    bw,bh = config.brush.image.get_size()
    y1 = config.fillmode.bounds[1]
    y2 = config.fillmode.bounds[3]
    h = y2-y1+1
    w = x2-x1+1
    bgcolor = config.brush.bgcolor
    for x in range(xs1, xs2+1):
        color = brush_array[(x-x1)*bw//w, (y-y1)*bh//h]
        if color != bgcolor:
            if surf_array.dtype == np.uint8:
                #indexed color
                surf_array[x,y] = color
        if surf_array.dtype != np.uint8:
            #true color
            surf_array[x,y] = (config.pal[color][0] << 16) | (config.pal[color][1] << 8) | (config.pal[color][2])

#precalc array for WRAP
MAXCALC = 1024
wrap_calc = []
f=-1.0
while f < 1.0:
    wrap_calc.append(MAXCALC//2 + int(math.asin(f) * MAXCALC / math.pi))
    f += 2.0/MAXCALC

def wrap_func(c, maxc):
    if c < 0:
        return c
    if c <= maxc:
        return wrap_calc[MAXCALC*c//maxc] * maxc // MAXCALC
    else:
        return maxc

def hline_WRAP(surf_array, y, x1, x2, xs1, xs2):
    if config.brush.image == None:
        hline_SOLID(surf_array, config.color, y, xs1, xs2)
        return

    brush_array = pygame.surfarray.pixels2d(config.brush.image)
    bw,bh = config.brush.image.get_size()
    y1 = config.fillmode.bounds[1]
    y2 = config.fillmode.bounds[3]
    h = y2-y1+1
    w = x2-x1+1
    bgcolor = config.brush.bgcolor
    for x in range(xs1, xs2+1):
        color = brush_array[wrap_func((x-x1)*bw//w, bw), wrap_func((y-y1)*bh//h, bh)]
        if color != bgcolor:
            if surf_array.dtype == np.uint8:
                #indexed color
                surf_array[x,y] = color
        if surf_array.dtype != np.uint8:
            #true color
            surf_array[x,y] = (config.pal[color][0] << 16) | (config.pal[color][1] << 8) | (config.pal[color][2])

def hline_PATTERN(surf_array, y, x1, x2, xs1, xs2):
    if config.brush.image == None:
        hline_SOLID(surf_array, config.color, y, xs1, xs2)
        return

    brush_array = pygame.surfarray.pixels2d(config.brush.image)
    bw,bh = config.brush.image.get_size()
    y1 = config.fillmode.bounds[1]
    y2 = config.fillmode.bounds[3]
    h = y2-y1+1
    w = x2-x1+1
    bgcolor = config.brush.bgcolor
    for x in range(xs1, xs2+1):
        color = brush_array[x%bw, y%bh]
        if color != bgcolor:
            if surf_array.dtype == np.uint8:
                #indexed color
                surf_array[x,y] = color
        if surf_array.dtype != np.uint8:
            #true color
            surf_array[x,y] = (config.pal[color][0] << 16) | (config.pal[color][1] << 8) | (config.pal[color][2])

def hline_VERT_FIT(surf_array, primprops, color, y, xs1, xs2):
    if primprops.fillmode.predraw or config.get_range(color) == None:
        hline_SOLID(surf_array, color, y, xs1, xs2)
    add_vline(y, xs1, xs2)

def hline_BOTH_FIT(surf_array, primprops, color, y, xs1, xs2):
    if primprops.fillmode.predraw or config.get_range(color) == None:
        hline_SOLID(surf_array, color, y, xs1, xs2)
    hlines.append([y, xs1, xs2])

def hline_ANTIALIAS(surf_array, primprops, color, y, xs1, xs2):
    hlines.append([y, xs1, xs2])

def hline_SMOOTH(surf_array, primprops, color, y, xs1, xs2):
    hlines.append([y, xs1, xs2])

def hline(screen, color_in, y, x1, x2, primprops=None, interrupt=False, erase=False):
    if primprops == None:
        primprops = config.primprops

    size = screen.get_size()
    #VERT_FIT and BOTH_FIT shouldn't be affected by clipping
    if not primprops.fillmode.value in [FillMode.VERT_FIT, FillMode.BOTH_FIT]:
        #don't draw if off screen
        if y<0 or y>=size[1]:
            return
        if x1<0 and x2<0:
            return
        if x1>size[0] and x2>size[0]:
            return

    color = copy.copy(color_in)

    #make sure ascending coords
    if x1 > x2:
        x1,x2 = (x2,x1)
    xs1,xs2 = (x1,x2)

    #VERT_FIT and BOTH_FIT shouldn't be affected by clipping
    if not primprops.fillmode.value in [FillMode.VERT_FIT, FillMode.BOTH_FIT]:
        #clip to edges of screen
        if xs1<0:
            xs1=0
        if xs2>size[0]-1:
            xs2=size[0]-1

    #create array from the surface.
    surf_array = pygame.surfarray.pixels2d(screen)

    if primprops.xor:
        hline_XOR(surf_array, y, xs1, xs2)
    elif primprops.fillmode.value == FillMode.SOLID or erase:
        hline_SOLID(surf_array, color, y, xs1, xs2)
    elif primprops.fillmode.value == FillMode.BRUSH:
        hline_BRUSH(surf_array, y, x1, x2,xs1, xs2)
    elif primprops.fillmode.value == FillMode.WRAP:
        hline_WRAP(surf_array, y, x1, x2, xs1, xs2)
    elif primprops.fillmode.value == FillMode.PATTERN:
        hline_PATTERN(surf_array, y, x1, x2, xs1, xs2)
    elif primprops.fillmode.value == FillMode.VERT_FIT:
        hline_VERT_FIT(surf_array, primprops, color, y, xs1, xs2)
    elif primprops.fillmode.value == FillMode.BOTH_FIT:
        hline_BOTH_FIT(surf_array, primprops, color, y, xs1, xs2)
    elif primprops.fillmode.value == FillMode.ANTIALIAS:
        hline_ANTIALIAS(surf_array, primprops, color, y, xs1, xs2)
    elif primprops.fillmode.value == FillMode.SMOOTH:
        hline_SMOOTH(surf_array, primprops, color, y, xs1, xs2)
    elif primprops.fillmode.value >= FillMode.VERTICAL:
        #get color range
        cyclemode = False
        for crange in config.cranges:
            if crange.is_active() and color >= crange.low and color <= crange.high:
                cyclemode = True
                arange = crange.get_range()
                numcolors = len(arange)
                cur_crange = crange
                color = arange[0]
        if cyclemode:
            if primprops.fillmode.value == FillMode.VERTICAL:
                y1 = config.fillmode.bounds[1]
                y2 = config.fillmode.bounds[3]
                numpoints = y2-y1+1
            elif primprops.fillmode.value == FillMode.HORIZONTAL:
                x1 = config.fillmode.bounds[0]
                x2 = config.fillmode.bounds[2]
                numpoints = x2-x1+1
            else:
                numpoints = x2-x1+1
            if primprops.fillmode.gradient_dither >= 0:
                pointspercolor = numpoints / (numcolors)
            else:
                pointspercolor = numpoints / (numcolors-.9)
            ditherfactor = primprops.fillmode.gradient_dither/3.0 * pointspercolor
            for x in range(xs1,xs2+1):
                if primprops.fillmode.gradient_dither >= 0:
                    dither = int((random.random()*ditherfactor)-(ditherfactor/2))
                else:
                    dither = 0
                if pointspercolor > 0:
                    if primprops.fillmode.value >= FillMode.HORIZONTAL:
                        colori = int(int(x2-(x+dither)) / pointspercolor)
                    elif primprops.fillmode.value == FillMode.VERTICAL:
                        colori = int(int(y2-(y+dither)) / pointspercolor)
                    if primprops.fillmode.gradient_dither < 0:
                        if primprops.fillmode.value >= FillMode.HORIZONTAL:
                            if FillMode.ORDER4[x%4, y%4] > (16 - (16 * (x2-x) / pointspercolor)%16):
                                colori += 1
                        elif primprops.fillmode.value == FillMode.VERTICAL:
                            if FillMode.ORDER4[x%4, y%4] > (16 - (16 * (y2-y) / pointspercolor)%16):
                                colori += 1
                    if colori >= len(arange):
                        colori = len(arange) - 1
                    elif colori < 0:
                        colori = 0
                    color = arange[colori]
                if screen.get_bytesize() == 1:
                    #indexed color
                    surf_array[x,y] = color
                else:
                    #true color
                    surf_array[x,y] = (config.pal[color][0] << 16) | (config.pal[color][1] << 8) | (config.pal[color][2])
        else:
            hline_SOLID(surf_array, color, y, xs1, xs2)

    #free array and unlock surface
    surf_array = None


def drawhlines(screen, color, primprops=None, interrupt=False):
    global hlines
    if primprops == None:
        primprops = config.primprops

    if len(hlines) == 0:
        return

    if primprops.fillmode.value == FillMode.BOTH_FIT:
        #Find color range
        cyclemode = False
        for crange in config.cranges:
            if crange.is_active() and color >= crange.low and color <= crange.high:
                cyclemode = True
                arange = crange.get_range()
                numcolors = len(arange)
                cur_crange = crange
                color = arange[0]
        if not cyclemode:
            return

        #Find bounds of shape
        hlines_min = np.amin(hlines, axis=0)
        hlines_max = np.amax(hlines, axis=0)
        xo = hlines_min[1] - 1
        yo = hlines_min[0] - 1
        w = hlines_max[2] - xo + 2
        h = hlines_max[0] - yo + 2

        #Create numpy array for shape
        surf_array = np.zeros((w,h), dtype=int)

        #Render shape into numpy array
        for y,x1,x2 in hlines:
            surf_array[x1-xo:x2-xo+1,y-yo] = 1
        surf_trim = surf_array.copy()

        #Build up array of number of pixels to the edge
        while (np.count_nonzero(surf_trim) > 0):
            #Create mask to cut away edges
            tfarray = np.equal(surf_trim, 0)
            surf_mask = np.zeros((w,h), dtype=int)
            surf_mask[tfarray] = 1

            #Trim edges of shape
            surf_trim[1:w,1:h] -= surf_mask[0:w-1,0:h-1]
            surf_trim[0:w-1,0:h-1] -= surf_mask[1:w,1:h]
            surf_trim[1:w,0:h-1] -= surf_mask[0:w-1,1:h]
            surf_trim[0:w-1,1:h] -= surf_mask[1:w,0:h-1]
            tfarray = np.not_equal(surf_trim, 1)
            surf_trim[tfarray] = 0

            #Increment shape array pixel count from trimmed shape
            surf_array += surf_trim

            #Interrupt if needed
            if interrupt and config.has_event():
                return
            config.try_recompose()

        #Create mask of finished shape
        tfmask = np.not_equal(surf_array, 0)

        #Map counts to colors in the range
        max_pixels = np.amax(surf_array)
        if cur_crange.get_dir() == -1:
            surf_array[tfmask] = max_pixels - surf_array[tfmask]
        surf_array *= numcolors * 256   # multiply for more precision
        surf_array //= max_pixels + 1
        surf_array += cur_crange.low * 256

        if primprops.fillmode.gradient_dither > 0:
            #Random dither
            dither_range = 32 * primprops.fillmode.gradient_dither
            dither_array = np.random.randint(-dither_range,dither_range,size=(w,h))
            surf_array += dither_array
        elif primprops.fillmode.gradient_dither < 0:
            dither_order4 = (FillMode.ORDER4 - 8) * 16
            dither_array = np.tile(dither_order4, ((w+3)//4,(h+3)//4))
            surf_array += dither_array[0:w,0:h]

        #Force out of range colors back into range
        tfarray = np.less(surf_array, cur_crange.low * 256)
        surf_array[tfarray] = cur_crange.low * 256
        tfarray = np.greater(surf_array, cur_crange.high * 256)
        surf_array[tfarray] = cur_crange.high * 256

        #Find safe BG color
        bgcolor = 0
        if cur_crange.low == 0:
            bgcolor = cur_crange.high + 1

        #Convert to image and blit to screen
        shape_image = pygame.Surface((w, h),0,8)
        shape_image.set_palette(config.pal)
        shape_image.fill(bgcolor)
        shape_image.set_colorkey(bgcolor)
        surf_array2 = pygame.surfarray.pixels2d(shape_image)
        surf_array //= 256
        surf_array2[tfmask] = surf_array[tfmask]
        surf_array2 = None
        screen.blit(shape_image, (xo,yo))

    if primprops.fillmode.value in [FillMode.ANTIALIAS, FillMode.SMOOTH]:
        #Find bounds of shape
        hlines_min = np.amin(hlines, axis=0)
        hlines_max = np.amax(hlines, axis=0)
        xo = hlines_min[1] - 1
        yo = hlines_min[0] - 1
        w = hlines_max[2] - xo + 2
        h = hlines_max[0] - yo + 2

        #Create numpy array for shape
        surf_array = np.zeros((w,h), dtype=int)

        #Render shape into numpy mask
        for y,x1,x2 in hlines:
            surf_array[x1-xo:x2-xo+1,y-yo] = 1
        tfmask = np.not_equal(surf_array, 1)
        smoothed_image = None

        #Grab pixel canvas under shape
        new_image = pygame.Surface((w, h),0,8)
        new_image.set_palette(config.pal)
        new_image.blit(screen, (0,0), (xo,yo,w,h))

        if primprops.fillmode.value == FillMode.ANTIALIAS:
            #Scale image up using Scale2X
            big_image = new_image.convert()
            for i in range(3):
                big_image = pygame.transform.scale2x(big_image)
                #Interrupt if needed
                if interrupt and config.has_event():
                    return
                config.try_recompose()

            #Scale image down again and convert to 8-bit
            smoothed_image = pygame.transform.smoothscale(big_image, (w,h))
            i8 = convert8(smoothed_image, config.pal)

            #Interrupt if needed
            if interrupt and config.has_event():
                return
            config.try_recompose()

        if primprops.fillmode.value == FillMode.SMOOTH:
            smooth_image(new_image)
            i8 = new_image
            #Interrupt if needed
            if interrupt and config.has_event():
                return
            config.try_recompose()

        #Mask off shape and draw into screen
        surf_array = pygame.surfarray.pixels2d(i8)
        surf_array[tfmask] = 0
        surf_array = None
        i8.set_colorkey(0)
        screen.blit(i8, (xo,yo))

def drawvlines(screen, color, primprops=None, interrupt=False):
    global vlines
    if primprops == None:
        primprops = config.primprops

    if primprops.fillmode.value == FillMode.VERT_FIT:
        for x in vlines:
            vlines[x].sort()
            #collapse scanline fragments
            i = 0
            while i < len(vlines[x]):
                j = i+1
                while j < len(vlines[x]):
                    y1i,y2i = vlines[x][i]
                    y1j,y2j = vlines[x][j]
                    if y1i+1 == y2j or y2i-1 == y1j or y2i+1 == y1j or y1i-1 == y2j or \
                       y1i == y2j or y2i == y1j or y2i == y1j or y1i == y2j:
                        #merge fragment
                        vlines[x][i] = [min(y1i,y1j,y2i,y2j),max(y1i,y1j,y2i,y2j)]
                        vlines[x].pop(j)
                        j = i+1
                    else:
                        j += 1
                i += 1
        #get color range
        cyclemode = False
        for crange in config.cranges:
            if crange.is_active() and color >= crange.low and color <= crange.high:
                cyclemode = True
                arange = crange.get_range()
                numcolors = len(arange)
                cur_crange = crange
                color = arange[0]
        size = screen.get_size()
        if cyclemode:
            for x in sorted(vlines.keys()):
                surf_array = pygame.surfarray.pixels2d(screen)  # Create an array from the surface.
                for frag in vlines[x]:
                    y1,y2 = frag
                    if x<0 or x>=size[0]:
                        continue
                    if y1 > y2:
                        y1,y2 = (y2,y1)
                    ys1,ys2 = (y1,y2)
                    if ys1<0:
                        ys1=0
                    if ys2>size[1]-1:
                        ys2=size[1]-1
                    numpoints = y2-y1+1
                    if primprops.fillmode.gradient_dither >= 0:
                        pointspercolor = numpoints / (numcolors)
                    else:
                        pointspercolor = numpoints / (numcolors-.9)
                    ditherfactor = primprops.fillmode.gradient_dither/3.0 * pointspercolor
                    for y in range(ys1,ys2+1):
                        if primprops.fillmode.gradient_dither >= 0:
                            dither = int((random.random()*ditherfactor)-(ditherfactor/2))
                        else:
                            dither = 0
                        if pointspercolor > 0:
                            colori = int(int(y2-(y+dither)) / pointspercolor)
                            if primprops.fillmode.gradient_dither < 0:
                                if FillMode.ORDER4[x%4, y%4] > (16 - (16 * (y2-y) // pointspercolor)%16):
                                    colori += 1
                            if colori >= len(arange):
                                colori = len(arange) - 1
                            elif colori < 0:
                                colori = 0
                            color = arange[colori]
                        if screen.get_bytesize() == 1:
                            surf_array[x,y] = color
                        else:
                            surf_array[x,y] = (config.pal[color][0] << 16) | (config.pal[color][1] << 8) | (config.pal[color][2])
                surf_array = None
                if interrupt and config.has_event():
                    return
                config.try_recompose()

def drawxorcross(screen, x, y, step=1, offset=0):
    #don't draw if off screen
    size = screen.get_size()
    if y<0 or y>=size[1] or x<0 or x>=size[0]:
        return

    offsetr = (step - offset) % step

    #create array from the surface.
    surf_array = pygame.surfarray.pixels2d(screen)

    if surf_array.dtype == np.uint8:
        #indexed color
        surf_array[offsetr:x:step,y] ^= config.NUM_COLORS-1
        surf_array[x+offset:size[0]:step,y] ^= config.NUM_COLORS-1
        surf_array[x,offsetr:y:step] ^= config.NUM_COLORS-1
        surf_array[x,y+offset:size[1]:step] ^= config.NUM_COLORS-1
    else:
        #true color
        surf_array[offsetr:x:step,y] ^= 0x00ffffff
        surf_array[x+offset:size[0]:step,y] ^= 0x00ffffff
        surf_array[x,offsetr:y:step] ^= 0x00ffffff
        surf_array[x,y+offset:size[1]:step] ^= 0x00ffffff

    #free array and unlock surface
    surf_array = None



def fillrect(screen, color, coordfrom, coordto, interrupt=False, primprops=None, erase=False):
    if primprops == None:
        primprops = config.primprops

    x1,y1 = coordfrom
    x2,y2 = coordto

    if x1 > x2:
        x1, x2 = x2, x1

    if y1 > y2:
        y1, y2 = y2, y1

    if not rect_onscreen([x1,y1,x2-x1+1,y2-y1+1]):
        return

    if interrupt and config.has_event():
        return

    if primprops.fillmode.value == FillMode.SOLID:
        pygame.draw.rect(screen, color, (x1,y1,x2-x1+1,y2-y1+1))
    else:
        config.fillmode.bounds = [x1,y1,x2,y2]
        start_shape()
        for y in range(y1, y2+1):
            hline(screen, color, y, x1, x2, primprops=primprops, erase=erase)
            if interrupt and config.has_event():
                return
            config.try_recompose()
        end_shape(screen, color, interrupt=interrupt, primprops=primprops)

def has_sl(sl, x, y):
    slfound = False
    if y in sl:
        for sly in sl[y]:
            if x >= sly[0] and x <= sly[1]:
                #fragment already in list
                slfound = True
                break
    return slfound

def floodfill(surface, fill_color, position, erase=False, bounds_color=-1):
    for x,y in symm_coords(position):
        #Create scanline hash
        sl = {}
        config.fillmode.bounds = copy.copy(FillMode.NOBOUNDS)
        if onscreen((x,y)):
            surface_bak = surface.copy()
            surf_array = pygame.surfarray.pixels2d(surface)  # Create an array from the surface.
            maxx, maxy = config.pixel_width, config.pixel_height
            current_color = surf_array[x,y]
            if bounds_color < 0:
                if fill_color == current_color:
                    if config.fillmode.value == FillMode.SOLID:
                        continue
                    else:
                        for crange in config.cranges:
                            if crange.is_active() and fill_color >= crange.low and fill_color <= crange.high:
                                fill_color = crange.next_color(fill_color)
            elif current_color == bounds_color:
                continue

            frontier = [(x,y)]
            while len(frontier) > 0:
                x, y = frontier.pop()
                if x >= 0 and x < maxx and y >= 0 and y < maxy:
                    if bounds_color < 0:
                        if surf_array[x, y] != current_color:
                            continue
                    else:
                        if surf_array[x, y] == bounds_color or has_sl(sl,x,y):
                            continue
                else:
                    continue
                surf_array[x, y] = fill_color
                add_bounds((x,y))

                # append coords to scanline lists
                if y in sl:
                    slfound = False
                    for sly in sl[y]:
                        if x >= sly[0] and x <= sly[1]:
                            #fragment already in list
                            slfound = True
                            break
                        elif sly[0]-1 == x:
                            #extend fragment left
                            sly[0] = x
                            slfound = True
                            break
                        elif sly[1]+1 == x:
                            #extend fragment right
                            sly[1] = x
                            slfound = True
                            break
                    if not slfound:
                        #new fragment
                        sl[y].append([x,x])
                else:
                    sl[y] = [[x,x]]

                # Then we append the neighbors of the pixel in the current position to our 'frontier' list.
                frontier.append((x + 1, y))  # Right.
                frontier.append((x - 1, y))  # Left.
                frontier.append((x, y + 1))  # Down.
                frontier.append((x, y - 1))  # Up.

            surf_array = None

            for y in sl:
                #collapse scanline fragments
                for i in range(0,len(sl[y])):
                    j = i+1
                    while j < len(sl[y]):
                        x1i,x2i = sl[y][i]
                        x1j,x2j = sl[y][j]
                        if x1i+1 == x2j or x2i-1 == x1j or x2i+1 == x1j or x1i-1 == x2j:
                            #merge fragment
                            sl[y][i] = [min(x1i,x1j,x2i,x2j),max(x1i,x1j,x2i,x2j)]
                            sl[y].pop(j)
                            j = i+1
                        else:
                            j += 1

            start_shape()
            if config.fillmode.value != FillMode.SOLID:
                #Restore pre-filled state
                surface.blit(surface_bak, (0,0))
                for y in sorted (sl.keys()):
                    #draw scanline fragments
                    for frag in sl[y]:
                        hline(surface, fill_color, y, frag[0], frag[1], erase=erase)
                    config.try_recompose()
            end_shape(surface, fill_color)

#from pygame: https://github.com/atizo/pygame/blob/master/src/draw.c
def fillpoly(screen, color, coords, handlesymm=True, interrupt=False, primprops=None, erase=False):
    n = len(coords)
    if n == 0:
        return

    if primprops == None:
        primprops = config.primprops

    coords_symm = symm_coords_list(coords, handlesymm=handlesymm)

    for i in range(len(coords_symm)):
        newcoords = coords_symm[i]

        # Determine maxima
        minx = min(newcoords,key=itemgetter(0))[0];
        maxx = max(newcoords,key=itemgetter(0))[0];
        miny = min(newcoords,key=itemgetter(1))[1];
        maxy = max(newcoords,key=itemgetter(1))[1];
        config.fillmode.bounds = [minx,miny,maxx,maxy]

        # Eliminate last coord if equal to first
        if n > 1 and newcoords[0][0] == newcoords[n-1][0] and newcoords[0][1] == newcoords[n-1][1]:
            n -= 1

        start_shape()
        # Draw, scanning y
        for y in range(miny, maxy+1):
            if interrupt and config.has_event():
                return
            polyints = []
            for i in range(0, n):
                if i == 0:
                    ind1 = n-1
                    ind2 = 0
                else:   
                    ind1 = i-1
                    ind2 = i

                y1 = newcoords[ind1][1]
                y2 = newcoords[ind2][1]

                if y1 < y2:
                    x1 = newcoords[ind1][0]
                    x2 = newcoords[ind2][0]
                elif y1 > y2:
                    y2 = newcoords[ind1][1]
                    y1 = newcoords[ind2][1]
                    x2 = newcoords[ind1][0]
                    x1 = newcoords[ind2][0]
                else:
                    continue

                if y >= y1 and y < y2:
                    polyints.append((y-y1) * (x2-x1) // (y2-y1) + x1)
                elif y == maxy and y > y1 and y <= y2:
                    polyints.append((y-y1) * (x2-x1) // (y2-y1) + x1)

            polyints.sort()

            for i in range(0, len(polyints), 2):
                hline(screen, color, y, polyints[i], polyints[i+1], primprops=primprops, erase=erase)
                if interrupt and config.has_event():
                    return
                config.try_recompose()

            # special case for horizontal line
            if miny == maxy:
                hline(screen, color, miny, minx, maxx, primprops=primprops, erase=erase)
                config.try_recompose()

        end_shape(screen, color, interrupt=interrupt)


def drawpoly(screen, color, coords, filled=0, xormode=False, drawmode=-1, handlesymm=True, interrupt=False, skiplast=False, erase=False):
    if filled:
        fillpoly(screen, color, coords, handlesymm=handlesymm, interrupt=interrupt, erase=erase)
    else:
        coords_symm = symm_coords_list(coords, handlesymm=handlesymm)

        for i in range(len(coords_symm)):
            newcoords = coords_symm[i]
            lastcoord = []
            for coord in newcoords:
                if interrupt and config.has_event():
                    return
                if len(lastcoord) != 0:
                    drawline(screen, color, lastcoord, coord, xormode, drawmode=drawmode, handlesymm=False, interrupt=interrupt, skiplast=(xormode or skiplast), erase=erase)
                lastcoord = coord

def convert8(pixel_canvas_rgb, pal, status_func=None):
    #Decide whether pic is RGB or BGR
    if pixel_canvas_rgb.get_shifts()[0] == 0:
        is_bgr = True
    else:
        is_bgr = False

    #Create color map for all 16 million colors
    cmap = np.zeros(0x1000000, dtype="uint8")

    #convert surface into RGB ints
    pixbuff24 = pygame.surfarray.array2d(pixel_canvas_rgb)
    #get rid of alpha channel
    pixbuff24 &= 0x00FFFFFF

    #create new 8-bit surface
    pixbuff8 = np.zeros_like(pixbuff24, dtype="uint32")

    npal = np.array(pal, dtype=np.int32)

    #find unique colors
    unique_colors = np.unique(pixbuff24)

    color_count = 0
    #loop through unique colors
    for color in unique_colors:
        color_count += 1
        if status_func != None:
            status_func(color_count / len(unique_colors))
        if (is_bgr):
            b,g,r = color>>16, (color>>8)&255, color&255
        else:
            r,g,b = color>>16, (color>>8)&255, color&255
        ncol = np.array([r,g,b], dtype=np.int32)

        # Find color distance
        nrgbdiff = ncol - npal
        ncdiff = np.sum(nrgbdiff*nrgbdiff, axis=1)

        # Find the closest color index
        min_i = np.argmin(ncdiff)

        # Assign color index to color map
        cmap[color] = min_i

    #map colors back to bitmap
    pixbuff8[:] = cmap[pixbuff24[:]]

    #turn array back into surface
    surf8 = pygame.surfarray.make_surface(pixbuff8)
    surf8.set_palette(pal)
    return surf8

def get_truecolor_palette(canvas, num_colors):
    surf_array = pygame.surfarray.pixels2d(canvas)
    #get rid of alpha channel and make 12 bit
    surf_array &= 0x00f0f0f0
    surf_array |= surf_array >> 4
    #find unique color indexes and counts of color indexes in pic
    unique_colors, counts_colors = np.unique(surf_array, return_counts=True)
    surf_array = None
    #put counts and color indexes into matrix together into histogram
    hist_array = np.asarray((unique_colors, counts_colors)).transpose()
    #print(hist_array)
    #sort histogram descending by frequency
    sorted_hist_array = hist_array[np.argsort(-hist_array[:, 1])]
    #print(sorted_hist_array)
    #take first num_colors indexes
    colorlist = np.sort(sorted_hist_array[0:num_colors, 0])
    #make sure to preserve color 0
    if colorlist[0] != 0:
        colorlist = np.sort(sorted_hist_array[0:num_colors-1, 0])
        colorlist = np.insert(colorlist, 0, 0)
    #print(colorlist)
    #convert to palette array
    pal=[]
    for rgb in colorlist:
        r,g,b = rgb>>16, (rgb>>8)&255, rgb&255
        pal.append([r,g,b])
    #print(pal)
    return pal
