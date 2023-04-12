#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
config.py
Implement the global area of PyDPainter
"""

import sys, math, os.path, random, colorsys, platform, re, datetime

from colorrange import *
from cursor import *
from displayinfo import *
from toolbar import *
from prim import *
from palreq import *
from picio import *
from tools import *
from minitools import *
from menubar import *
from menus import *
from version import *
from zoom import *

import numpy as np

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

fonty = 12
fontx = 8

config = None

#Workaround for pygame timer bug:
#  https://github.com/pygame/pygame/issues/3128
#  https://github.com/pygame/pygame/pull/3062
TIMEROFF = int((2**31)-1)

custom_event_counter = 0

def get_at_mapped(screen, coord):
    if "get_at_mapped" in dir(screen):
        return screen.get_at_mapped(coord)
    else:
        x, y = coord
        surf_array = pygame.surfarray.pixels2d(screen)  # Create an array from the surface.
        return int(surf_array[x,y])

def cycle():
    if config.drawmode.value == DrawMode.CYCLE:
        color = config.color
        for crange in config.cranges:
           color = crange.next_color(color)
        config.color = color

def quantize_palette(pal, color_depth=16):
    if color_depth == 16:
        newpal = []
        if color_depth == 16 and len(pal) == 64:
            #handle extra halfbright
            for i in range(0,32):
                r,g,b = pal[i]
                newpal.append((r//16*17, g//16*17, b//16*17))
            for i in range(0,32):
                newpal.append(((newpal[i][0] & 0xee) // 2,
                               (newpal[i][1] & 0xee) // 2,
                               (newpal[i][2] & 0xee) // 2))
        else:
            for i in range(0,len(pal)):
                r,g,b = pal[i]
                newpal.append((r//16*17, g//16*17, b//16*17))

        return newpal
    else:
        newpal = []
        for i in range(0,len(pal)):
            r,g,b = pal[i]
            newpal.append((r, g, b))

        logpal = int(math.log(len(newpal), 2.0))
        if 2**logpal != len(newpal):
            logpal += 1
            while len(newpal) < 2**logpal:
                newpal.append((0,0,0))

        return newpal

color_skew=[]
for r in range(2,30):
    for g in range(1,r+1):
        for b in range(1,g+1):
            color_skew.append(((r//2)*((r%2)*2-1), \
                               (g//2)*((g%2)*2-1), \
                               (b//2)*((b%2)*2-1)))

def unique_palette(pal):
    newpal = []
    paldict = {}
    #print("len(pal): " + str(len(pal)))
    for i in range(0,len(pal)):
        col = pal[i]
        j = 0
        out_of_range = False
        #print("color[" + str(i) + "]: " + str(col))
        while out_of_range or str(col) in paldict:
            #print("dup color: " + str(col))
            out_of_range = False
            r = pal[i][0] + color_skew[j][0]
            g = pal[i][1] + color_skew[j][1]
            b = pal[i][2] + color_skew[j][2]
            if r < 0 or r > 255 or g < 0 or g > 255 or b < 0 or b > 255:
                out_of_range = True
            col = (r,g,b)
            j = j + 1
        newpal.append(col)
        paldict[str(col)] = 1
    #pal256.extend([pal[0]] * (256-len(pal)))
    return newpal

def setBIBrush():
    brushnames = ["","circle","square","spray"]
    newid = brushnames[config.brush.type] + str(config.brush.size)
    group_list = config.toolbar.tool_id("circle1").group_list
    for g in group_list:
        if g.id == newid:
            g.state = 1
        else:
            g.state = 0
        g.need_redraw = True
    return


class pydpainter:

    def __init__(self):
        global config
        config = self
        prim_set_config(self)
        palreq_set_config(self)
        toolreq_set_config(self)
        menureq_set_config(self)
        picio_set_config(self)
        colorrange_set_config(self)
        version_set_config(self)
        pygame.init()
        pygame.mixer.quit() #hack to stop 100% CPU ultilization
        
        #initialize system
        self.dinfo = pygame.display.Info()
        self.initialize()

        #load picture if specified from command line
        if len(sys.argv) > 1:
            filename = sys.argv[1]
            config.pixel_canvas = load_pic(filename)
            config.truepal = list(config.pal)
            config.pal = config.unique_palette(config.pal)
            config.initialize_surfaces()
            config.filepath = os.path.dirname(filename)
            config.filename = filename
            config.modified_count = 0

    def closest_scale4(self,maxnum,num):
        if num >= maxnum:
            return maxnum
        if num >= maxnum // 2:
            return maxnum // 2
        return maxnum // 4

    def scale_dec(self):
        if config.scale <= 1:
            config.scale /= 2.0
        else:
            currscale = round(config.scale * 2.0) / 2.0
            if abs(config.scale - currscale) < .01:
                config.scale = currscale - 0.5
            else:
                config.scale = currscale

    def scale_inc(self):
        if config.scale < 1:
            config.scale *= 2.0
        else:
            currscale = round(config.scale * 2.0) / 2.0
            if abs(config.scale - currscale) < .01:
                config.scale = currscale + 0.5
            else:
                config.scale = currscale

    def set_aspect(self, mode):
        self.pixel_mode = self.pixel_modes[mode]
        self.pixel_aspect = self.pixel_aspects[mode]
        if self.display_mode & self.MODE_LACE:
            self.pixel_aspect *= 2.0
        if self.display_mode & self.MODE_HIRES:
            self.pixel_aspect /= 2.0

    def closest_scale(self, size=None):
        #estimate scale from size
        limit = 20
        if size != None:
            ow, oh = size
        else:
            dinfo = pygame.display.Info()
            ow = dinfo.current_w
            oh = dinfo.current_h
        pw = config.screen_width
        ph = config.screen_height
        pa = config.pixel_aspect

        sx = ow / (pw*pa)
        sy = oh / ph

        if sx < sy:
            s = sx
        else:
            s = sy

        if s < 0.51 or s > limit:
            s = config.scale

        return s

    def resize_display(self, resize_window=True, first_init=False, force=False):
        if config.fullscreen:
            if force:
                config.scale_bak = config.scale
            scale = min(config.max_height / config.screen_height,\
                        config.max_width / config.screen_width / config.pixel_aspect)
            new_window_size = (int(config.screen_width*scale*config.pixel_aspect), int(config.screen_height*scale))
            pygame.display.set_mode((config.max_width, config.max_height), FULLSCREEN|HWSURFACE|DOUBLEBUF)
            config.screen = pygame.display.get_surface()
            config.window_size = new_window_size
            return
        elif force:
            config.scale = config.scale_bak

        while True:
            new_window_size = (int(config.screen_width*config.scale*config.pixel_aspect), int(config.screen_height*config.scale))
            if (new_window_size[0] > config.max_width or \
                new_window_size[1] > config.max_height):
                    config.scale_dec()
            elif (new_window_size[0] < self.screen_width_min or \
                  new_window_size[1] < self.screen_height_min):
                    config.scale_inc()
            else:
                break

        if 'SDL_VIDEO_WINDOW_POS' in os.environ:
            del os.environ['SDL_VIDEO_WINDOW_POS']

        if "toolbar" in dir(config):
           config.toolbar.tip_canvas = None
        if "minitoolbar" in dir(config):
           config.minitoolbar.tip_canvas = None

        display_flags = HWSURFACE|DOUBLEBUF|RESIZABLE

        if not force and "window_size" in dir(config) and \
           (new_window_size[0] == config.window_size[0] and new_window_size[1] == config.window_size[1]):
            pass
        else:
            if force or resize_window or pygame.version.vernum[0] == 1:
                #Wait for mouse buttons to be released before resizing window
                pygame.event.get()
                while True in pygame.mouse.get_pressed():
                    pygame.event.get()
                new_window_size = (new_window_size[0], min(int(config.max_height * 0.9), new_window_size[1]))
                pygame.display.set_mode(new_window_size, display_flags)
                if pygame.version.vernum[0] == 1:
                    pygame.time.wait(300)
 
            config.screen = pygame.display.get_surface()
            config.window_size = new_window_size

    def initialize_surfaces(self, reinit=False, first_init=False):
        sm = config.display_info.get_id(self.display_mode)
        if not reinit:
            self.screen_width = sm.x
            self.screen_height = sm.y
            self.pixel_aspect = sm.aspect
            self.pixel_mode = sm.get_pixel_mode()
            self.aspectX = sm.aspect_x
            self.aspectY = sm.aspect_y
        self.sm = sm

        if reinit:
            config.truepal = config.get_default_palette(config.NUM_COLORS)
            config.pal = list(config.truepal)
            config.pixel_canvas = pygame.Surface((self.pixel_width, self.pixel_height),0,8)

        self.pixel_width, self.pixel_height = self.pixel_canvas.get_size()

        self.screen_offset_x = 0
        self.screen_offset_y = 0
        if self.pixel_width < self.screen_width:
            self.screen_offset_x = (self.screen_width - self.pixel_width) // 2
        if self.pixel_height < self.screen_height:
            self.screen_offset_y = (self.screen_height - self.pixel_height) // 2

        self.pixel_req_canvas = pygame.Surface((self.screen_width, self.screen_height))
        self.pixel_req_rect = None

        self.symm_center = (self.pixel_width//2, self.pixel_height//2)

        #adjust fonts
        self.fontx = self.closest_scale4(32, self.screen_width // 40)
        self.fonty = self.closest_scale4(32, self.screen_height // 25)
        self.font = PixelFont("jewel32.png", sizeX=self.fontx, sizeY=self.fonty)
        self.fonty = int(self.fonty * 1.5)

        if first_init:
            config.scale = round(config.closest_scale())
            config.resize_display()
        else:
            config.scale = config.closest_scale()
            config.resize_display(False)

        config.color = 1
        config.bgcolor = 0

        #Turn off toggle tools
        config.grid_on = False
        config.symm_on = False
        config.zoom.on = False
        config.zoom.box_on = False

        #Keep spare if same size as new image
        if "pixel_spare_canvas" in dir(self):
            sw, sh = self.pixel_spare_canvas.get_size()
            if sw == self.pixel_width and sh == self.pixel_height:
                self.pixel_spare_canvas.set_palette(self.pal)
            else:
                self.pixel_spare_canvas = pygame.Surface((self.pixel_width, self.pixel_height),0, self.pixel_canvas)
        else:
            self.pixel_spare_canvas = pygame.Surface((self.pixel_width, self.pixel_height),0, self.pixel_canvas)

        self.scaled_image = pygame.Surface((self.screen_width, self.screen_height*2))
        cursor_images = pygame.image.load(os.path.join('data', 'cursors.png'))
        self.cursor = cursor(self.scaled_image, self.sm.scaleX, self.sm.scaleY*2, self, cursor_images)
        self.toolbar = init_toolbar(config)
        self.menubar = init_menubar(config)
        self.minitoolbar = init_minitoolbar(config)

        self.scanline_canvas = pygame.Surface((self.screen_width, self.screen_height*2), SRCALPHA)
        for i in range(0, self.screen_height*2, 2):
            pygame.draw.line(self.scanline_canvas, Color(0,0,0,100), (0,i), (self.screen_width,i), 1)

        self.NUM_COLORS = len(self.pal)
        self.set_all_palettes(self.pal)

        self.clear_undo()
        config.toolbar.click(config.toolbar.tool_id("draw"), MOUSEBUTTONDOWN)
        config.toolbar.click(config.toolbar.tool_id("circle1"), MOUSEBUTTONDOWN)
        config.save_undo()


    def get_default_palette(self, numcols=32):
        if config.display_mode & config.MODE_EXTRA_HALFBRIGHT:
            newpal = [
                (0,0,0), (238,204,170), (255,0,0), (204,0,0), (170,0,0), (0,221,0),
                (0,170,0), (0,136,0), (0,0,255), (0,0,204), (0,0,170), (255,255,68),
                (204,204,17), (153,153,17), (0,255,255), (0,187,187), (0,153,153),
                (238,0,153), (187,0,119), (153,0,102), (221,68,17), (170,51,17),
                (136,34,17), (0,153,255), (0,102,204), (0,68,153), (17,204,136),
                (17,153,102), (68,119,85), (255,255,255), (204,204,204), (153,153,153),
                (0,0,0), (119,102,85), (119,0,0), (102,0,0), (85,0,0), (0,102,0),
                (0,85,0), (0,68,0), (0,0,119), (0,0,102), (0,0,85), (119,119,34),
                (102,102,0), (68,68,0), (0,119,119), (0,85,85), (0,68,68), (119,0,68),
                (85,0,51), (68,0,51), (102,34,0), (85,17,0), (68,17,0), (0,68,119),
                (0,51,102), (0,34,68), (0,102,68), (0,68,51), (34,51,34), (119,119,119),
                (102,102,102), (68,68,68)]
        else:
            newpal = [(0,0,0), (224,192,160), (224,0,0), (160,0,0), (208,128,0), (240,224,0),
            (128,240,0), (0,128,0), (0,196,96), (0,208,208), (0,160,240), (0,112,192),
            (0,0,240), (112,0,240), (192,0,224), (198,0,128), (96,32,0), (224,80,32),
            (160,80,32), (240,192,160), (48,48,48), (64,64,64), (80,80,80), (96,96,96),
            (112,112,112), (128,128,128), (144,144,144), (160,160,160), (192,192,192),
            (208,208,208), (224,224,224), (240,240,240),
            #colors from the Windows palette to fill out the rest
            (42,255,0),(42,255,85),(42,255,170),(42,255,255),(85,0,0),(85,0,85),
            (85,0,170),(85,0,255),(85,31,0),(85,31,85),(85,31,170),(85,31,255),
            (85,63,0),(85,63,85),(85,63,170),(85,63,255),
            (85,95,0),(85,95,85),(85,95,170),(85,95,255),(85,127,0),(85,127,85),
            (85,127,170),(85,127,255),(85,159,0),(85,159,85),(85,159,170),(85,159,255),
            (85,191,0),(85,191,85),(85,191,170),(85,191,255),
            (85,223,0),(85,223,85),(85,223,170),(85,223,255),(85,255,0),(85,255,85),
            (85,255,170),(85,255,255),(127,0,0),(127,0,85),(127,0,170),(127,0,255),
            (127,31,0),(127,31,85),(127,31,170),(127,31,255),
            (127,63,0),(127,63,85),(127,63,170),(127,63,255),(127,95,0),(127,95,85),
            (127,95,170),(127,95,255),(127,127,0),(127,127,85),(127,127,170),(127,127,255),
            (127,159,0),(127,159,85),(127,159,170),(127,159,255),
            (127,191,0),(127,191,85),(127,191,170),(127,191,255),(127,223,0),(127,223,85),
            (127,223,170),(127,223,255),(127,255,0),(127,255,85),(127,255,170),(127,255,255),
            (170,0,0),(170,0,85),(170,0,170),(170,0,255),
            (170,31,0),(170,31,85),(170,31,170),(170,31,255),(170,63,0),(170,63,85),
            (170,63,170),(170,63,255),(170,95,0),(170,95,85),(170,95,170),(170,95,255),
            (170,127,0),(170,127,85),(170,127,170),(170,127,255),
            (170,159,0),(170,159,85),(170,159,170),(170,159,255),(170,191,0),(170,191,85),
            (170,191,170),(170,191,255),(170,223,0),(170,223,85),(170,223,170),(170,223,255),
            (170,255,0),(170,255,85),(170,255,170),(170,255,255),
            (212,0,0),(212,0,85),(212,0,170),(212,0,255),(212,31,0),(212,31,85),
            (212,31,170),(212,31,255),(212,63,0),(212,63,85),(212,63,170),(212,63,255),
            (212,95,0),(212,95,85),(212,95,170),(212,95,255),
            (212,127,0),(212,127,85),(212,127,170),(212,127,255),(212,159,0),(212,159,85),
            (212,159,170),(212,159,255),(212,191,0),(212,191,85),(212,191,170),(212,191,255),
            (212,223,0),(212,223,85),(212,223,170),(212,223,255),
            (212,255,0),(212,255,85),(212,255,170),(212,255,255),(255,0,85),(255,0,170),
            (255,31,0),(255,31,85),(255,31,170),(255,31,255),(255,63,0),(255,63,85),
            (255,63,170),(255,63,255),(255,95,0),(255,95,85),
            (255,95,170),(255,95,255),(255,127,0),(255,127,85),(255,127,170),(255,127,255),
            (255,159,0),(255,159,85),(255,159,170),(255,159,255),(255,191,0),(255,191,85),
            (255,191,170),(255,191,255),(255,223,0),(255,223,85),
            (255,223,170),(255,223,255),(255,255,85),(255,255,170),(204,204,255),(255,204,255),
            (51,255,255),(102,255,255),(153,255,255),(204,255,255),(0,127,0),(0,127,85),
            (0,127,170),(0,127,255),(0,159,0),(0,159,85),
            (0,159,170),(0,159,255),(0,191,0),(0,191,85),(0,191,170),(0,191,255),
            (0,223,0),(0,223,85),(0,223,170),(0,223,255),(0,255,85),(0,255,170),
            (42,0,0),(42,0,85),(42,0,170),(42,0,255),
            (42,31,0),(42,31,85),(42,31,170),(42,31,255),(42,63,0),(42,63,85),
            (255,251,240),(160,160,164),(128,128,128),(255,0,0),(0,255,0),(255,255,0),
            (0,0,255),(255,0,255),(0,255,255),(255,255,255)]

        return newpal[0:numcols]

    def saveConfig(self):
        home = ""
        if 'HOME' in os.environ:
            home = os.environ['HOME']
        try:
            sm = config.display_info.get_id(self.display_mode)
            f = open(os.path.join(home,".pydpainter"),"w")
            f.write("display_mode=%08x\n" % (self.display_mode))
            f.write("pixel_width=%d\n" % (self.pixel_width))
            f.write("pixel_height=%d\n" % (self.pixel_height))
            f.write("screen_width=%d\n" % (self.screen_width))
            f.write("screen_height=%d\n" % (self.screen_height))
            f.write("color_depth=%d\n" % (self.color_depth))
            f.write("NUM_COLORS=%d\n" % (self.NUM_COLORS))
            f.write("pixel_mode=%s\n" % (self.pixel_mode))
            f.write("pixel_aspect=%f\n" % (self.pixel_aspect))
            f.write("aspectX=%f\n" % (sm.aspect_x))
            f.write("aspectY=%f\n" % (sm.aspect_y))
            f.write("fullscreen=%s\n" % (self.fullscreen))
            f.write("scale=%f\n" % (self.scale))
            f.write("scanlines=%d\n" % (self.scanlines))
            f.close()
        except:
            pass

    def readConfig(self):
        home = ""
        if 'HOME' in os.environ:
            home = os.environ['HOME']
        try:
            f = open(os.path.join(home,".pydpainter"),"r")
            for line in f:
                if line.lstrip()[0] == '#':
                    continue
                vars = line.strip().split("=")
                if len(vars) == 2:
                    if vars[0] == "display_mode":
                        self.display_mode = int(vars[1], 16)
                    elif vars[0] == "pixel_width":
                        self.pixel_width = int(vars[1])
                    elif vars[0] == "pixel_height":
                        self.pixel_height = int(vars[1])
                    elif vars[0] == "screen_width":
                        self.screen_width = int(vars[1])
                    elif vars[0] == "screen_height":
                        self.screen_height = int(vars[1])
                    elif vars[0] == "color_depth":
                        self.color_depth = int(vars[1])
                    elif vars[0] == "NUM_COLORS":
                        self.NUM_COLORS = int(vars[1])
                    elif vars[0] == "pixel_mode":
                        self.pixel_mode = vars[1]
                    elif vars[0] == "pixel_aspect":
                        self.pixel_aspect = float(vars[1])
                    elif vars[0] == "aspectX":
                        self.aspectX = float(vars[1])
                    elif vars[0] == "aspectY":
                        self.aspectY = float(vars[1])
                    elif vars[0] == "fullscreen":
                        self.fullscreen = True if vars[1] == "True" else False
                    elif vars[0] == "scale":
                        self.scale = float(vars[1])
                        config.resize_display()
                    elif vars[0] == "scanlines":
                        self.scanlines = int(vars[1])
            f.close()
            return True
        except:
            pass
        return False

    def new_custom_event(self):
        global custom_event_counter
        user_event = None
        if "custom_type" in dir(pygame.event):
            user_event = pygame.event.custom_type()
        else:
            user_event = USEREVENT + custom_event_counter
            custom_event_counter += 1
        self.ALLCUSTOMEVENTS.append(user_event)
        return user_event

    def initialize(self):
        self.clock = pygame.time.Clock()

        self.MODE_LACE               = 0x0004
        self.MODE_EXTRA_HALFBRIGHT   = 0x0080
        self.MODE_HAM                = 0x0800
        self.MODE_HIRES              = 0x8000
        self.NTSC_MONITOR_ID         = 0x00011000
        self.PAL_MONITOR_ID          = 0x00021000
        self.VGA_MONITOR_ID          = 0x00031000
        self.MONITOR_ID_MASK         = 0x00031000
        self.MODE_VGA_MCGA_KEY       = 0x00031000
        self.MODE_VGA_VGA_KEY        = 0x00039004
        self.MODE_VGA_SVGA_KEY       = 0x00039005
        self.MODE_VGA_XGA_KEY        = 0x00039006
        self.OCS_MODES = self.MODE_LACE | self.MODE_EXTRA_HALFBRIGHT | self.MODE_HAM | self.MODE_HIRES | self.NTSC_MONITOR_ID | self.PAL_MONITOR_ID

        self.display_info = DisplayInfo()

        self.fontx = fontx
        self.fonty = fonty
        self.text_tool_font_name = re.sub(r'\..{1,3}$', '', pygame.font.get_default_font())
        self.text_tool_font_name = re.sub(r'bold$', '', self.text_tool_font_name)
        self.text_tool_font_type = 0
        self.text_tool_font_size = 16
        self.text_tool_font_antialias = True
        self.text_tool_font_bold = False
        self.text_tool_font_italic = False
        self.text_tool_font_underline = False
        self.text_tool_font = pygame.font.Font(pygame.font.match_font(self.text_tool_font_name), self.text_tool_font_size)
        self.last_recompose_timer = 0
        self.max_width = self.dinfo.current_w
        self.max_height = self.dinfo.current_h
        #Setup the pygame screen
        self.pixel_width = 320
        self.pixel_height = 200
        self.screen_width = self.pixel_width
        self.screen_height = self.pixel_height
        self.screen_offset_x = 0
        self.screen_offset_y = 0
        self.screen_width_min = 320
        self.screen_height_min = 200
        self.screen_width_max = 640
        self.screen_height_max = 512
        self.pixel_modes = ["square","NTSC","PAL"]
        self.pixel_aspects = [1.0, 10.0/11.0, 59.0/54.0]
        self.pixel_mode = "NTSC"
        self.pixel_aspect = 10.0/11.0 #NTSC
        self.color_depth = 16
        self.fullscreen = False
        self.display_mode = config.getPalNtscDefault()
        if self.display_mode & self.PAL_MONITOR_ID == self.PAL_MONITOR_ID:
            self.pixel_height = 256
            self.screen_height_min = 256
            self.pixel_mode = "PAL"
            self.pixel_aspect = 59.0/54.0 #PAL

        self.scale = 3
        self.scale_bak = 3
        self.SCANLINES_ON = 0
        self.SCANLINES_OFF = 1
        self.SCANLINES_NOSMOOTH = 2
        self.scanlines = self.SCANLINES_ON
        self.brush = Brush()

        self.primprops = PrimProps()
        self.matte_erase = False
        self.last_drawmode = 2
        self.drawmode = self.primprops.drawmode
        self.fillmode = self.primprops.fillmode
        self.color = 1
        self.bgcolor = 0

        self.palette_page = 0
        self.NUM_COLORS = 32
        self.filename = ""
        self.filepath = os.path.expanduser("~")
        self.spare_filename = self.filename
        self.spare_filepath = self.filepath
        self.toolmode = 0
        self.tool_selected = 0
        self.subtool_selected = 0
        self.zoom = Zoom(config)
        self.grid_on = False
        self.grid_size = (10,10)
        self.grid_offset = (0,0)
        self.symm_on = False
        self.symm_center = (160,100)
        self.symm_mode = 0
        self.symm_type = 1
        self.symm_num = 6
        self.symm_width = 50
        self.symm_height = 50
        self.constrain_x = -1
        self.constrain_y = -1
        self.help_on = True
        self.p1 = None
        self.polylist = []
        self.airbrush_size = 10
        self.coords_on = False
        self.coords_flip = False
        self.auto_transp_on = False
        config.resize_display()
        pygame.display.set_caption("PyDPainter")
        pygame.display.set_icon(pygame.image.load(os.path.join('data', 'icon.png')))
        pygame.key.set_repeat(500, 100)

        self.pixel_canvas = pygame.Surface((self.pixel_width, self.pixel_height),0,8)
        self.pal = self.get_default_palette()
        self.pal = quantize_palette(self.pal, self.color_depth)
        self.backuppal = list(self.pal)
        self.truepal = list(self.pal)
        self.loadpal = list(self.pal)
        self.pixel_canvas.set_palette(self.pal)

        self.cycling = False
        self.cycle_handled = False
        self.cranges = [colorrange(5120,1,20,31), colorrange(2560,1,3,7), colorrange(2560,1,0,0), colorrange(2560,1,0,0), colorrange(2560,1,0,0), colorrange(2560,1,0,0)]

        #Allocate user events
        self.ALLCUSTOMEVENTS = []

        #Tool user event - airbrush spray, text cursor blink, etc
        self.TOOLEVENT = config.new_custom_event()

        #Color cycling user events
        self.CYCLEEVENTS = []
        for i in range(len(self.cranges)):
            self.CYCLEEVENTS.append(config.new_custom_event())

        #Tool tip delay user event
        self.TOOLTIPEVENT = config.new_custom_event()

        self.window_title = "PyDPainter"
        self.modified_count = -1
        self.spare_modified_count = -1
        self.UNDO_INDEX_MAX = 20
        self.undo_image = []
        self.undo_index = -1
        self.suppress_undo = False
        self.suppress_redraw = False
        self.running = True

        self.wait_for_mouseup = [False, False]

        reinit = self.readConfig()

        self.initialize_surfaces(reinit=reinit, first_init=True)
        pygame.mouse.set_visible(False)

    def doKeyAction(self, curr_action=None):
        if curr_action == None:
            curr_action = config.toolbar.tool_id(config.tool_selected).action
        if pygame.mouse.get_pressed() == (0,0,0):
            curr_action.move(config.get_mouse_pixel_pos())
        else:
            curr_action.drag(config.get_mouse_pixel_pos(), pygame.mouse.get_pressed())

    def getPalNtscDefault(self):
        display_mode = self.PAL_MONITOR_ID

        #guess PAL or NTSC default by time zone
        UTC_offset = int(round((datetime.datetime.now() - datetime.datetime.utcnow()).seconds/60/60,2))
        if UTC_offset > 12:
            UTC_offset -= 24

        if UTC_offset >= -10 and UTC_offset <= -4: #North/South America
            display_mode = self.NTSC_MONITOR_ID
        elif UTC_offset == 9: #Japan
            display_mode = self.NTSC_MONITOR_ID

        return display_mode

    def setDrawMode(self, dm):
        mg = config.menubar.menu_id("mode")
        if config.brush.type == Brush.CUSTOM:
            mg.menug_list[0].enabled = True
            mg.menug_list[2].enabled = True
        else:
            mg.menug_list[0].enabled = False
            mg.menug_list[2].enabled = False

        g = config.menubar.menu_id("mode").menu_id(str(DrawMode(dm)))
        if g != None:
            g.action.selected({})
        return

    def quantize_palette(self, pal, color_depth=16):
        return quantize_palette(pal, color_depth)

    def unique_palette(self, pal):
        return unique_palette(pal)

    def set_all_palettes(config, pal_in):
        if len(pal_in) == 256:
            pal = pal_in
        else:
            #Fill upper palette with BG color so smoothing gets valid colors
            pal = list(pal_in)
            pal.extend([pal_in[0]] * (256 - len(pal)))
        config.pixel_canvas.set_palette(pal)
        config.pixel_spare_canvas.set_palette(pal)

        if config.brush.image != None:
            config.brush.image.set_palette(pal)
        config.brush.cache = BrushCache()

        for img in config.undo_image:
            img.set_palette(pal)

    def set_screen_offset(self, x, y):
        # calculate offsets for toolbar and menubar if visible
        if config.toolbar.visible:
            tw = config.toolbar.rect[2]
        else:
            tw = 0
        if config.menubar.visible:
            mh = config.menubar.rect[3]
        else:
            mh = 0

        # Center canvas if smaller than the screen
        if self.pixel_width < self.screen_width - tw:
            self.screen_offset_x = (self.screen_width - self.pixel_width - tw) // 2
        if self.pixel_height < self.screen_height - mh:
            self.screen_offset_y = (self.screen_height - self.pixel_height - mh) // 2

        # Restrict scrolling offset to edges of screen
        if self.pixel_width >= self.screen_width - tw:
            if x < self.screen_width - self.pixel_width - tw:
                self.screen_offset_x = self.screen_width - self.pixel_width - tw
            elif x > 0:
                self.screen_offset_x = 0
        if self.pixel_height >= self.screen_height - mh:
            if y < self.screen_height - self.pixel_height:
                self.screen_offset_y = self.screen_height - self.pixel_height
            elif y > mh:
                self.screen_offset_y = mh

    def get_mouse_pointer_pos(self, event=None):
        mouseX, mouseY = pygame.mouse.get_pos()
        if not event is None and (event.type == MOUSEMOTION or event.type == MOUSEBUTTONUP or event.type == MOUSEBUTTONDOWN):
            mouseX, mouseY = event.pos
        if config.fullscreen:
            screenX, screenY = self.max_width, self.max_height
        else:
            screenX, screenY = self.window_size
        mouseX = mouseX * self.screen_width // screenX
        mouseY = mouseY * self.screen_height // screenY
        return((mouseX, mouseY))

    def calc_page_pos(self, mouseX, mouseY):
        mouseX -= self.screen_offset_x
        mouseY -= self.screen_offset_y

        #make sure coords don't go off page
        mouseX = max(mouseX,0)
        mouseY = max(mouseY,0)
        mouseX = min(mouseX,self.pixel_width-1)
        mouseY = min(mouseY,self.pixel_height-1)

        return mouseX, mouseY


    def get_mouse_pixel_pos(self, event=None, ignore_grid=False, ignore_req=False):
        mouseX, mouseY = pygame.mouse.get_pos()

        if not event is None and (event.type == MOUSEMOTION or event.type == MOUSEBUTTONUP or event.type == MOUSEBUTTONDOWN):
            mouseX, mouseY = event.pos

        if config.fullscreen:
            screenX, screenY = self.max_width, self.max_height
        else:
            screenX, screenY = self.window_size
        mouseX = mouseX * self.screen_width // screenX
        mouseY = mouseY * self.screen_height // screenY

        mouseside = 0

        if self.zoom.on and (self.pixel_req_rect == None or ignore_req):
            x0,y0,xw,yh = self.zoom.left_rect
            if (mouseX < x0+xw or self.zoom.mousedown_side == 1) and self.zoom.mousedown_side != 2:
                mouseside = 1
                mouseX += self.zoom.xoffset
                mouseY += self.zoom.yoffset
            else:
                mouseside = 2
                x0,y0,xw,yh = self.zoom.right_rect
                zx0,zy0, zoom_width,zoom_height = self.zoom.pixel_rect
                if xw == 0:
                    mouseX = 0
                else:
                    mouseX = ((mouseX - x0) * zoom_width // xw) + zx0

                if yh == 0:
                    mouseY = 0
                else:
                    mouseY = (((mouseY - y0) * zoom_height) // yh) + zy0
        else:
            self.zoom.mousedown_side = 0
            #Don't apply page offset to reqestors
            if self.pixel_req_rect != None:
                rx,ry,rw,rh = self.pixel_req_rect
                if mouseX >= rx and mouseX < rx+rw and \
                   mouseY >= ry and mouseY < ry+rh:
                    pass
                else:
                    mouseX, mouseY = self.calc_page_pos(mouseX, mouseY)
            else:
                mouseX, mouseY = self.calc_page_pos(mouseX, mouseY)

        if not event is None and event.type == MOUSEBUTTONDOWN:
            self.zoom.mousedown_side = mouseside
        if not event is None and event.type == MOUSEBUTTONUP:
            self.zoom.mousedown_side = 0

        #turn constrain on or off
        if pygame.key.get_mods() & KMOD_SHIFT:
            if self.constrain_x < 0 and self.constrain_y < 0:
                if "rel" in dir(event):
                    if abs(event.rel[0]) > abs(event.rel[1]):
                        self.constrain_y = mouseY
                    else:
                        self.constrain_x = mouseX
        else:
            self.constrain_x = -1
            self.constrain_y = -1

        #apply constrain
        if self.constrain_x >= 0:
            mouseX = self.constrain_x
        elif self.constrain_y >= 0:
            mouseY = self.constrain_y

        if self.grid_on and self.pixel_req_rect == None and not ignore_grid:
            go = self.grid_offset
            gs = self.grid_size
            mouseX = (mouseX - go[0] + (gs[0]//2)) // gs[0] * gs[0] + go[0]
            mouseY = (mouseY - go[1] + (gs[1]//2)) // gs[1] * gs[1] + go[1]

        return((mouseX, mouseY))

    def has_event(self, timeout=16):
        return pygame.event.peek((KEYDOWN,
                            MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION)) and \
               pygame.time.get_ticks() - self.last_recompose_timer > timeout

    def try_recompose(self):
        if pygame.time.get_ticks() - self.last_recompose_timer > 16:
            old_cursor = config.cursor.shape
            if old_cursor == config.cursor.CROSS:
                config.cursor.shape = config.cursor.BUSY
            config.recompose()
            if old_cursor == config.cursor.CROSS:
                config.cursor.shape = config.cursor.CROSS

    def redraw_window_title(self):
        new_window_title = "PyDPainter - "
        if config.filename == "":
            new_window_title += "Untitled" 
        else:
            new_window_title += os.path.basename(config.filename)

        if config.modified_count >= 1:
            new_window_title += " (modified)"

        if new_window_title != config.window_title:
            config.window_title = new_window_title
            pygame.display.set_caption(config.window_title)

    def recompose(self):
        if self.cycling:
            for crange in config.cranges:
                crange.apply_to_pal(self.pal)
            self.set_all_palettes(self.pal)

        self.redraw_window_title()

        screen_rgb = None
        if self.zoom.on:
            screen_rgb = pygame.Surface((self.screen_width, self.screen_height),0)
            w = self.screen_width // 3
            zxc,zyc = self.zoom.center
            zoom_width = w*2 // self.zoom.factor
            zoom_height = self.screen_height // self.zoom.factor

            menu_bar_height = 0
            if self.toolbar.visible:
                zoom_width -= self.toolbar.rect[2] // self.zoom.factor
            if self.menubar.visible:
                zoom_height -= self.menubar.rect[3] // self.zoom.factor
                menu_bar_height = self.menubar.rect[3]

            self.zoom.xoffset = zxc - (w//2)
            self.zoom.yoffset = zyc - ((self.screen_height-menu_bar_height) // 2)

            if self.zoom.xoffset < 0:
                self.zoom.xoffset = 0
            elif self.zoom.xoffset > self.pixel_width - w + 6:
                self.zoom.xoffset = self.pixel_width - w + 6

            if self.zoom.yoffset < -menu_bar_height:
                self.zoom.yoffset = -menu_bar_height
            elif self.zoom.yoffset > self.pixel_height - self.screen_height:
                self.zoom.yoffset = self.pixel_height - self.screen_height

            zx0 = zxc-(zoom_width//2)
            zy0 = zyc-(zoom_height//2)

            if zx0+zoom_width > self.pixel_width:
                zx0 = self.pixel_width - zoom_width
            if zx0 < 0:
                zx0 = 0

            if zy0+zoom_height > self.pixel_height:
                zy0 = self.pixel_height - zoom_height
            if zy0 < 0:
                zy0 = 0

            #Fix zoom center to be back in range
            zxc = zx0+(zoom_width//2)
            zyc = zy0+(zoom_height//2)
            self.zoom.center = (zxc,zyc)

            self.zoom.pixel_rect = (zx0,zy0, zoom_width,zoom_height)

            self.zoom.left_rect = (0,menu_bar_height, w,self.screen_height)
            self.zoom.border_rect = (w-6,0,6,self.screen_height)
            self.zoom.right_rect = (w,menu_bar_height, zoom_width*self.zoom.factor,zoom_height*self.zoom.factor)
            zxsize = min(zx0+zoom_width, self.pixel_width)*self.zoom.factor
            zysize = min(zy0+zoom_height, self.pixel_height)*self.zoom.factor

            # Draw left unzoomed image
            pygame.draw.rect(screen_rgb, (128,128,128), (0,0,w,self.screen_height))
            screen_rgb.blit(self.pixel_canvas, (0,0), (self.zoom.xoffset,self.zoom.yoffset, w,self.screen_height))
            #pygame.draw.rect(screen_rgb, (255,255,255), (zx0-self.zoom.xoffset,zy0-self.zoom.yoffset, zoom_width, zoom_height), 1)

            # Draw right zoomed image
            pygame.draw.rect(screen_rgb, (128,128,128), (w,menu_bar_height,self.screen_width,self.screen_height))
            zoom_canvas = pygame.Surface((zoom_width, zoom_height),0, screen_rgb)
            zoom_canvas.blit(self.pixel_canvas, (0,0), (zx0,zy0,zoom_width,zoom_height))
            zoom_canvas_scaled = pygame.transform.scale(zoom_canvas, (zoom_width*self.zoom.factor,zoom_height*self.zoom.factor))
            screen_rgb.blit(zoom_canvas_scaled, (w,menu_bar_height), (0,0,zxsize,zysize))

            # Draw divider
            pygame.draw.rect(screen_rgb, (0,0,0), (w-6,0,6,self.screen_height))
            pygame.draw.rect(screen_rgb, (128,128,128), (w-5,0,4,self.screen_height))
        else:
            self.set_screen_offset(self.screen_offset_x, self.screen_offset_y)

            screen_rgb = pygame.Surface((self.screen_width, self.screen_height),0)
            screen_rgb.fill((128,128,128)); # out of page bounds
            screen_rgb.blit(self.pixel_canvas, (self.screen_offset_x, self.screen_offset_y))

        #blit requestor layer
        if self.pixel_req_rect != None:
            if self.cursor.shape not in [self.cursor.NORMAL, self.cursor.NORMALTO, self.cursor.BUSY]:
                self.cursor.shape = self.cursor.NORMAL
            screen_rgb.blit(self.pixel_req_canvas, self.pixel_req_rect, self.pixel_req_rect)
            self.toolbar.tip_canvas = None
            self.minitoolbar.tip_canvas = None

        #blit toolbar layer
        self.toolbar.draw(screen_rgb, offset=(self.screen_width-self.toolbar.rect[2], self.fonty-1 if self.menubar.visible else 0))

        #blit menu layer
        self.menubar.draw(screen_rgb)

        #blit minitoolbar layer
        if self.menubar.visible:
            if config.minitoolbar.tool_id("expand").state == 1:
                mtbx = self.screen_width-self.minitoolbar.rect[2]
            else:
                mtbx = self.screen_width-(self.minitoolbar.rect[2]//len(self.minitoolbar.tools)*2)
            self.minitoolbar.draw(screen_rgb, offset=(mtbx, 0))

        #scale image double height
        pygame.transform.scale(screen_rgb, (self.screen_width, self.screen_height*2), self.scaled_image)

        #draw mouse cursor
        self.cursor.draw()

        if self.scanlines == self.SCANLINES_ON:
            #blit scanlines onto double-high image
            self.scaled_image.blit(self.scanline_canvas, (0,0))
            #scale up screen to window resolution, blurring for retro effect
            scaledup = pygame.transform.smoothscale(self.scaled_image, self.window_size)
        elif self.scanlines == self.SCANLINES_OFF:
            scaledup = pygame.transform.smoothscale(self.scaled_image, self.window_size)
        elif self.scanlines == self.SCANLINES_NOSMOOTH:
            scaledup = pygame.transform.scale(self.scaled_image, self.window_size)

        self.screen.fill((0,0,0))
        if config.fullscreen:
            ox = (self.screen.get_width() - scaledup.get_width()) // 2
            oy = (self.screen.get_height() - scaledup.get_height()) // 2
        else:
            ox, oy = 0,0
        self.screen.blit(scaledup,(ox,oy))
        scaledup = None

        #blit tooltip layer
        if not self.toolbar.wait_for_tip and \
           self.toolbar.tip_canvas != None and \
           self.toolbar.visible and \
           config.help_on:
            tx = self.screen_width-self.toolbar.rect[2]+self.toolbar.tip_x
            ty = (self.fonty-1 if self.menubar.visible else 0) + self.toolbar.tip_y
            t_size = self.toolbar.tip_canvas.get_size()
            sx = ox + (tx * self.window_size[0] // self.screen_width) - t_size[0]
            sy = oy + (ty * self.window_size[1] // self.screen_height) - (t_size[1]//2)
            self.screen.blit(self.toolbar.tip_canvas, (sx,sy))

        #blit minitoolbar tooltip layer
        if not self.minitoolbar.wait_for_tip and \
           self.minitoolbar.tip_canvas != None and \
           self.menubar.visible and \
           config.help_on:
            tx = mtbx + self.minitoolbar.tip_x
            ty = self.minitoolbar.tip_y
            t_size = self.minitoolbar.tip_canvas.get_size()
            sx = ox + (tx * self.window_size[0] // self.screen_width) - t_size[0]
            sy = oy + (ty * self.window_size[1] // self.screen_height) - (t_size[1]//2)
            self.screen.blit(self.minitoolbar.tip_canvas, (sx,sy))

        pygame.display.flip()
        self.last_recompose_timer = pygame.time.get_ticks()


    def save_undo(self):
        if self.suppress_undo:
            self.suppress_undo = False
            return

        self.modified_count += 1

        #Backup for undo
        self.undo_index = self.undo_index + 1
        if self.undo_index > self.UNDO_INDEX_MAX:
            self.undo_index = self.UNDO_INDEX_MAX
            self.undo_image.pop(0)

        #print("self.undo_index=" + str(self.undo_index) + "  len(self.undo_image)-1=" + str(len(self.undo_image)-1))

        if self.undo_index > len(self.undo_image)-1:
            self.undo_image.append("")

        while len(self.undo_image)-1 > self.undo_index:
            self.undo_image.pop()

        self.undo_image[self.undo_index] = pygame.Surface(self.pixel_canvas.get_size(),0, self.pixel_canvas)
        self.undo_image[self.undo_index].set_palette(self.pal)
        self.undo_image[self.undo_index].blit(self.pixel_canvas, (0,0))

    def clear_undo(self):
        self.suppress_undo = False
        self.undo_image = []
        self.undo_index = -1
        self.save_undo()
        self.suppress_undo = True

    def redo(self):
        config.undo_index = config.undo_index + 1
        if config.undo_index > len(config.undo_image) - 1:
            config.undo_index = len(config.undo_image) - 1
        config.pixel_canvas.blit(config.undo_image[config.undo_index], (0,0))

    def undo(self):
        config.undo_index = config.undo_index - 1
        if config.undo_index < 0:
            config.undo_index = 0
        config.pixel_canvas.blit(config.undo_image[config.undo_index], (0,0))

    def airbrush_coords(self, xc, yc, size=-1):
        if size < 0:
            size = self.airbrush_size
        angle = random.random() * 2.0 * 3.14159
        dist = random.random() * float(size)
        x = int(dist*config.aspectX * math.cos(angle))
        y = int(dist*config.aspectY * math.sin(angle))
        return ((xc+x, yc+y))

    def clear_pixel_draw_canvas(self):
        self.pixel_canvas.blit(self.undo_image[self.undo_index],(0,0))

    def stop_cycling(self):
        if self.cycling:
            self.cycling = False
            self.pal = list(self.backuppal)
            self.set_all_palettes(self.pal)
            config.brush.size = config.brush.size #invalidate bruch cache
            for rangenum, crange in enumerate(self.cranges):
                pygame.time.set_timer(self.CYCLEEVENTS[rangenum], TIMEROFF)

    def start_cycling(self):
        if not self.cycling:
            self.backuppal = list(self.pal)
            self.cycling = True
            for rangenum, crange in enumerate(self.cranges):
                if crange.low < crange.high and crange.rate > 0:
                    pygame.time.set_timer(self.CYCLEEVENTS[rangenum], crange.rate_to_milli())

    def size_canvas(self, width, height, resize):
        # Crop or expand pixel canvas
        new_pixel_canvas = pygame.Surface((width, height),0,8)
        new_pixel_canvas.set_palette(config.pal)
        if resize:
            pygame.transform.scale(config.pixel_canvas, (width, height), new_pixel_canvas)
        else:
            new_pixel_canvas.blit(config.pixel_canvas, (0,0))
        config.pixel_canvas = new_pixel_canvas
        config.pixel_width = width
        config.pixel_height = height

        # Crop or expand spare pixel canvas
        new_pixel_canvas = pygame.Surface((width, height),0,8)
        new_pixel_canvas.set_palette(config.pal)
        if resize:
            pygame.transform.scale(config.pixel_spare_canvas, (width, height), new_pixel_canvas)
        else:
            new_pixel_canvas.blit(config.pixel_spare_canvas, (0,0))
        config.pixel_spare_canvas = new_pixel_canvas

        config.clear_undo()
        config.save_undo()

    def run(self):
        """
        This method is the main application loop.
        """

        config = self
        startX = 0
        startY = 0
        stopX = 0
        stopY = 0
        text_string = ""
        buttons = list(pygame.mouse.get_pressed())
        zoom_drag = None
        pan_drag = None

        last_wait_for_mouseup_gui = False

        self.recompose()

        #main loop
        while config.running:
            e = pygame.event.wait()

            if e.type == pygame.MOUSEMOTION and pygame.event.peek((MOUSEMOTION)):
                #get rid of extra mouse movements
                continue

            if e.type == pygame.VIDEORESIZE and pygame.event.peek((VIDEORESIZE)):
                #get rid of extra resize events
                continue

            if e.type in self.ALLCUSTOMEVENTS:
                if  pygame.event.peek(self.ALLCUSTOMEVENTS):
                    #get rid of extraneous color cycle and other user events
                    continue

            if e.type == pygame.QUIT:
                config.running = False

            if e.type == VIDEORESIZE:
                config.scale = config.closest_scale((e.w, e.h))
                config.resize_display(False)
                self.recompose()
                continue

            #Intercept keys for toolbar
            if e.type in [KEYDOWN,KEYUP]:
                if curr_action != None:
                    key_handled = False
                    if e.type == KEYDOWN:
                        key_handled = curr_action.keydown(e.key, e.mod, e.unicode)
                    elif e.type == KEYUP:
                        key_handled = curr_action.keyup(e.key, e.mod)
                    if key_handled:
                        self.recompose()
                        continue

            #Keep track of button states
            if e.type == MOUSEMOTION:
                buttons = list(e.buttons)
            elif e.type == MOUSEBUTTONDOWN:
                if e.button <= len(buttons):
                    buttons[e.button-1] = True
            elif e.type == MOUSEBUTTONUP:
                if e.button <= len(buttons):
                    buttons[e.button-1] = False

            #Show system mouse pointer if outside of screen
            if e.type == MOUSEMOTION:
                if config.fullscreen:
                    pygame.mouse.set_visible(False)
                elif e.pos[0] > config.window_size[0] or e.pos[1] > config.window_size[1]:
                    pygame.mouse.set_visible(True)
                else:
                    pygame.mouse.set_visible(False)

            #Get toolbar events if any and set current action to tool selected
            te_list = self.toolbar.process_event(self.screen, e, self.get_mouse_pointer_pos)
            if len(te_list) > 0:
                self.cycle_handled = True
            curr_action = None
            if config.zoom.box_on:
                curr_action = config.toolbar.tool_id("magnify").action
            elif config.toolbar.tool_id(config.tool_selected) != None and \
               config.toolbar.tool_id(config.tool_selected).action != None:
                curr_action = config.toolbar.tool_id(config.tool_selected).action

            #Get mintoolbar events if any
            if self.menubar.visible:
                mte_list = self.minitoolbar.process_event(self.screen, e, self.get_mouse_pointer_pos)
            else:
                mte_list = []

            #Get menubar events if any
            if len(mte_list) > 0:
                me_list = []
            else:
                me_list = self.menubar.process_event(self.screen, e, self.get_mouse_pointer_pos)

            wait_for_mouseup_gui = True in config.toolbar.wait_for_mouseup or True in config.minitoolbar.wait_for_mouseup or True in config.menubar.wait_for_mouseup

            if wait_for_mouseup_gui:
                self.cycle_handled = True

            #Decide if in draw area
            if not True in config.wait_for_mouseup and \
               (self.toolbar.is_inside(self.get_mouse_pointer_pos(e)) or \
               self.menubar.is_inside(self.get_mouse_pointer_pos(e)) or \
               wait_for_mouseup_gui):
                self.cursor.shape = self.cursor.NORMAL
                hide_draw_tool = True
                config.menubar.title_right = ""
            elif self.tool_selected == "fill":
                self.cursor.shape = self.cursor.FILL
                hide_draw_tool = False
            else:
                self.cursor.shape = self.cursor.CROSS
                hide_draw_tool = False

            #Do move action for toolbar events
            if curr_action != None and not hide_draw_tool:
                for te in te_list:
                    #print(te)
                    if te.gadget.tool_type == ToolGadget.TT_TOGGLE or \
                       te.gadget.tool_type == ToolGadget.TT_GROUP:
                        if e.type == KEYDOWN:
                            if pygame.mouse.get_pressed() == (0,0,0):
                                curr_action.move(self.get_mouse_pixel_pos(e))
                            else:
                                curr_action.drag(self.get_mouse_pixel_pos(e), pygame.mouse.get_pressed())
                        else:
                            curr_action.move(self.get_mouse_pixel_pos(e))
            elif curr_action != None and hide_draw_tool:
                curr_action.hide()

            #process middle mouse button for pan
            if not config.zoom.on and e.type == MOUSEBUTTONDOWN and e.button == 2:
                pan_drag = self.get_mouse_pixel_pos(e)
            if e.type == MOUSEBUTTONUP and e.button == 2:
                pan_drag = None
            if not config.zoom.on and buttons[1] and pan_drag != None:
                x,y = self.get_mouse_pixel_pos(e)
                cx,cy = (config.screen_offset_x, config.screen_offset_y)
                dx,dy = pan_drag
                (config.screen_offset_x, config.screen_offset_y) = (cx-dx+x, cy-dy+y)

            #process mouse wheel for zoom and pan
            if config.zoom.on and e.type == MOUSEBUTTONDOWN and e.button in [2, 4,5]:
                if e.button == 2: #middle drag
                    zoom_drag = self.get_mouse_pixel_pos(e)
                elif e.button == 4: #scroll up
                    if config.zoom.factor < config.zoom.factor_max:
                        config.zoom.factor += 1
                elif e.button == 5: #scroll down
                    if config.zoom.factor > config.zoom.factor_min:
                        config.zoom.factor -= 1
            if e.type == MOUSEBUTTONUP and e.button == 2:
                zoom_drag = None
            if config.zoom.on and buttons[1] and zoom_drag != None:
                x,y = self.get_mouse_pixel_pos(e)
                cx,cy = config.zoom.center
                dx,dy = zoom_drag
                config.zoom.center = (cx+dx-x,cy+dy-y)

            #process global keys
            if e.type == KEYDOWN:
                self.cycle_handled = True
                gotkey = False
                if e.key == K_PERIOD:
                    gotkey = True
                elif e.key == K_PLUS or e.key == K_EQUALS:
                    gotkey = True
                    if self.tool_selected == "airbrush":
                        self.airbrush_size += 1
                        if self.airbrush_size > 50:
                            self.airbrush_size = 50
                    else:
                        self.brush.size += 1
                        setBIBrush()
                elif e.key == K_MINUS:
                    gotkey = True
                    if self.tool_selected == "airbrush": #Airbrush
                        self.airbrush_size -= 1
                        if self.airbrush_size < 5:
                            self.airbrush_size = 5
                    else:
                        self.brush.size -= 1
                        setBIBrush()
                elif e.key == K_RIGHTBRACKET:
                    gotkey = True
                    if e.mod & KMOD_SHIFT:
                        self.bgcolor = (self.bgcolor + 1) % config.NUM_COLORS
                    else:
                        self.color = (self.color + 1) % config.NUM_COLORS
                elif e.key == K_LEFTBRACKET:
                    gotkey = True
                    if e.mod & KMOD_SHIFT:
                        self.bgcolor = (self.bgcolor - 1) % config.NUM_COLORS
                    else:
                        self.color = (self.color - 1) % config.NUM_COLORS
                elif e.unicode == ",":
                    gotkey = True
                    config.toolbar.tool_id('swatch').pick_color()
                elif e.key == K_RIGHT and not config.zoom.on:
                    gotkey = True
                    config.screen_offset_x -= 5
                elif e.key == K_LEFT and not config.zoom.on:
                    gotkey = True
                    config.screen_offset_x += 5
                elif e.key == K_DOWN and not config.zoom.on:
                    gotkey = True
                    config.screen_offset_y -= 5
                elif e.key == K_UP and not config.zoom.on:
                    gotkey = True
                    config.screen_offset_y += 5
                elif e.unicode == "n" and not config.zoom.on:
                    gotkey = True
                    mouseX, mouseY = self.get_mouse_pixel_pos(e, ignore_grid=True)
                    config.screen_offset_x = (config.screen_width // 2) - mouseX
                    config.screen_offset_y = (config.screen_height // 2) - mouseY
                elif e.key == K_F9:
                    if config.menubar.visible:
                        config.menubar.visible = False
                    else:
                        config.menubar.visible = True
                elif e.key == K_F10:
                    if config.toolbar.visible:
                        config.toolbar.visible = False
                        config.menubar.visible = False
                    else:
                        config.toolbar.visible = True
                        config.menubar.visible = True
                elif e.key == K_F11:
                    config.fullscreen = not config.fullscreen
                    config.minitoolbar.tool_id("fullscreen").state = 1 if config.fullscreen else 0
                    config.resize_display(force=True)
                elif e.key == K_DELETE:
                    config.cursor.visible = not config.cursor.visible
                elif e.mod & KMOD_CTRL and e.mod & KMOD_SHIFT and e.key == K_z:
                    config.redo()
                elif e.mod & KMOD_CTRL and e.key == K_z:
                    config.undo()
                elif e.mod & KMOD_CTRL and e.key == K_y:
                    config.redo()

                if config.zoom.on:
                    gotkey |= config.zoom.process_event(self.screen, e)

                if gotkey:
                    self.set_screen_offset(self.screen_offset_x, self.screen_offset_y)
                    self.doKeyAction(curr_action)

            #No toolbar event so process event as action on selected tool
            if curr_action != None and len(te_list) == 0 and \
               len(mte_list) == 0 and len(me_list) == 0 and \
               not wait_for_mouseup_gui and not hide_draw_tool:
                if config.coords_on:
                    cx,cy = self.get_mouse_pixel_pos(e)
                    if config.p1 != None and True in pygame.mouse.get_pressed():
                        if config.coords_flip:
                            config.menubar.title_right = "%4d\x94%4d\x96" % (cx-config.p1[0], cy-config.p1[1])
                        else:
                            config.menubar.title_right = "%4d\x94%4d\x95" % (cx-config.p1[0], config.p1[1]-cy)
                    else:
                        if config.coords_flip:
                            config.menubar.title_right = "%4d\x94%4d\x96" % (cx, cy)
                        else:
                            config.menubar.title_right = "%4d\x94%4d\x95" % (cx, config.pixel_height - cy - 1)
                        config.p1 = None
                else:
                    config.menubar.title_right = ""
                if e.type == MOUSEMOTION:
                    if e.buttons == (0,0,0):
                        curr_action.move(self.get_mouse_pixel_pos(e))
                    else:
                        curr_action.drag(self.get_mouse_pixel_pos(e), e.buttons)
                elif e.type == MOUSEBUTTONDOWN and buttons[0] != buttons[2]:
                    zoom_region = config.zoom.region(e.pos)
                    config.wait_for_mouseup[zoom_region] = True
                    curr_action.mousedown(self.get_mouse_pixel_pos(e), e.button)
                elif e.type == MOUSEBUTTONUP and buttons[0] == buttons[2]:
                    if last_wait_for_mouseup_gui:
                        curr_action.move(self.get_mouse_pixel_pos(e))
                    else:
                        curr_action.mouseup(self.get_mouse_pixel_pos(e), e.button)
                        config.wait_for_mouseup = [False] * len(config.wait_for_mouseup)
                elif e.type == self.TOOLEVENT:
                    if buttons[0] or buttons[2]:
                        curr_action.drag(self.get_mouse_pixel_pos(e), buttons)
                    else:
                        curr_action.move(self.get_mouse_pixel_pos(e))

            last_wait_for_mouseup_gui = wait_for_mouseup_gui

            if buttons[0] and not e.type in self.ALLCUSTOMEVENTS and not self.cycle_handled:
                cycle()
            self.cycle_handled = False

            self.recompose()

            if not config.running and config.modified_count >= 1:
                answer = question_req(config.pixel_req_canvas,
                         "Unsaved Changes",
                         "Are you sure you want\nto quit PyDPainter?",
                         ["Yes","No"])
                if answer == 1:
                    config.running = True
