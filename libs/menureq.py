#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os.path, colorsys

import gadget
from gadget import *

from prim import *

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

config = None

def menureq_set_config(config_in):
    global config
    config = config_in

def screen_format_req(screen, new_clicked=False):
    req = str2req("Choose Screen Format", """
                     Number of
      Format:         Colors:
[Lo-Res     320x200] [  2][ 32]
[Med-Res    640x200] [  4][ 64]
[Interlace  320x400] [  8][128]
[Hi-Res     640x400] [ 16][256]
                      Out of:
[NTSC~PAL]           [4096~16M]

[Cancel][OK][Make Default]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)

    #Get PAL/NTSC from current display mode
    if config.display_mode & config.PAL_MONITOR_ID == config.PAL_MONITOR_ID:
        aspect = 2
    else:
        aspect = 1

    #Get color depth (16 = 4096 colors and 256 = 16M colors)
    cdepth = config.color_depth

    #Get bitplane depth from current number of colors
    global bdepth
    bdepth = int(math.log(config.NUM_COLORS,2))

    #Gather bitplane depth gadgets and sort in numeric order
    gDepth = []
    for g in req.gadgets:
        if g.label.lstrip() in ['2','4','8','16','32','64','128','256']:
            gDepth.append(g)
    gDepth.sort(key=lambda g: g.label)

    #Gather NTSC/PAL gadgets
    gNTSC = req.gadget_id("0_7")
    gPAL = req.gadget_id("5_7")

    #Gather (OCS)ECS/AGA gadgets
    g12bit = req.gadget_id("21_7")
    g24bit = req.gadget_id("26_7")

    #Get resolution from current screen mode
    if config.display_mode & config.MODE_HIRES:
        if config.display_mode & config.MODE_LACE:
            res = 3
        else:
            res = 1
    else:
        if config.display_mode & config.MODE_LACE:
            res = 2
        else:
            res = 0

    #Gather screen mode gadgets
    gres = []
    for g in req.gadgets:
        if re.search(r'\dx\d\d\d$', g.label):
            gres.append(g)

    gDepth[bdepth-1].state = 1

    def apply_aspect():
        if aspect == 1:
            gNTSC.state = 1
            for g in gres:
                g.label = g.label.replace("256", "200")
                g.label = g.label.replace("512", "400")
                g.need_redraw = True
        else:
            gPAL.state = 1
            for g in gres:
                g.label = g.label.replace("200", "256")
                g.label = g.label.replace("400", "512")
                g.need_redraw = True
    apply_aspect()

    def apply_cdepth():
        if cdepth == 16:
            g12bit.state = 1
            gDepth[5].label = "EHB"
            gDepth[5].need_redraw = True
            gDepth[6].enabled = False
            gDepth[6].need_redraw = True
            gDepth[7].enabled = False
            gDepth[7].need_redraw = True
        else:
            g24bit.state = 1
            gDepth[4].enabled = True
            gDepth[4].need_redraw = True
            gDepth[5].enabled = True
            gDepth[5].need_redraw = True
            gDepth[5].label = " 64"
            gDepth[5].need_redraw = True
            gDepth[6].enabled = True
            gDepth[6].need_redraw = True
            gDepth[7].enabled = True
            gDepth[7].need_redraw = True
    apply_cdepth()

    def apply_bdepth():
        gDepth[bdepth-1].state = 1
        gDepth[bdepth-1].need_redraw = True

    def apply_mode():
        global bdepth
        #Apply limits to screen mode/bitplane depth
        if cdepth == 16 and res in [1,3]:
            if bdepth > 4:
                bdepth = 4
                apply_bdepth()
            gDepth[4].enabled = False
            gDepth[4].need_redraw = True
            gDepth[5].enabled = False
            gDepth[5].need_redraw = True
        elif cdepth == 16 and res in [0,2]:
            if bdepth > 6:
                bdepth = 6
                apply_bdepth()
            gDepth[4].enabled = True
            gDepth[4].need_redraw = True
            gDepth[5].enabled = True
            gDepth[5].need_redraw = True
        gres[res].state = 1
    apply_mode()

    def get_top_colors(num_colors):
        surf_array = pygame.surfarray.pixels2d(config.pixel_canvas)
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
        return colorlist

    def get_top_pal(pal, colorlist, num_colors, halfbright):
        num_top_colors = num_colors
        if halfbright:
            num_top_colors = 32

        #assign top colors to new palette
        newpal = []
        for i in range(0,num_top_colors):
            if i < len(colorlist):
                newpal.append(pal[colorlist[i]])
            else:
                newpal.append(pal[i])

        #adjust halfbright colors
        if halfbright:
            for i in range(0,32):
                newpal.append(((newpal[i][0] & 0xee) // 2,
                               (newpal[i][1] & 0xee) // 2,
                               (newpal[i][2] & 0xee) // 2))

        #fill in upper palette with background color
        for i in range(num_colors,256):
            newpal.append(newpal[0])

        return newpal


    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()
    req.draw(screen)
    config.recompose()

    running = 1
    reinit = False
    ok_clicked = False
    while running:
        event = pygame.event.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        for ge in gevents:
            if ge.gadget == gNTSC:
                aspect = 1
                apply_aspect()
            elif ge.gadget == gPAL:
                aspect = 2
                apply_aspect()
            elif ge.gadget in gres:
                for i in range(len(gres)):
                    if ge.gadget == gres[i]:
                        res = i
                apply_mode()
            elif ge.gadget in gDepth:
                for i in range(len(gDepth)):
                    if ge.gadget == gDepth[i]:
                        bdepth = i+1
            elif ge.gadget == g12bit:
                cdepth = 16
                apply_cdepth()
                apply_mode()
            elif ge.gadget == g24bit:
                cdepth = 256
                apply_cdepth()
                apply_mode()
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label in ["OK","Make Default"] and not req.has_error():
                    ok_clicked = True
                    num_colors = 2**bdepth
                    if bdepth == 6 and cdepth == 16:
                        halfbright = True
                    else:
                        halfbright = False

                    if new_clicked:
                        reinit = True
                    elif num_colors < config.NUM_COLORS:
                        #reduce palette to higest frequency color indexes
                        reinit = False

                        num_top_colors = num_colors
                        if halfbright:
                            num_top_colors = 32

                        colorlist = get_top_colors(num_top_colors)

                        newpal = get_top_pal(config.pal, colorlist, num_colors, halfbright)

                        #convert colors to reduced palette using blit
                        new_pixel_canvas = pygame.Surface((config.pixel_width, config.pixel_height),0,8)
                        new_pixel_canvas.set_palette(newpal)
                        new_pixel_canvas.blit(config.pixel_canvas, (0,0))

                        #substitute new canvas for the higher color one
                        config.pixel_canvas = new_pixel_canvas
                        config.truepal = get_top_pal(config.truepal, colorlist, num_colors, halfbright)[0:num_colors]
                        config.truepal = config.quantize_palette(config.truepal, cdepth)
                        config.pal = list(config.truepal)
                        config.pal = config.unique_palette(config.pal)
                        config.backuppal = list(config.pal)
                        config.pixel_canvas.set_palette(config.pal)
                    elif num_colors == config.NUM_COLORS:
                        reinit = False
                    elif num_colors > config.NUM_COLORS:
                        reinit = False

                        config.truepal = config.quantize_palette(config.truepal, cdepth)
                        newpal = config.get_default_palette(num_colors)
                        config.truepal.extend(newpal[config.NUM_COLORS:num_colors])
                        if halfbright:
                            for i in range(0,32):
                                config.truepal[i+32] = \
                                          ((config.truepal[i][0] & 0xee) // 2,
                                           (config.truepal[i][1] & 0xee) // 2,
                                           (config.truepal[i][2] & 0xee) // 2)
                        config.pal = list(config.truepal)
                        config.pal = config.unique_palette(config.pal)
                        config.backuppal = list(config.pal)
                        config.pixel_canvas.set_palette(config.pal)

                    dmode = 0
                    px = 320
                    py = 200
                    if res in [1,3]:
                        dmode |= config.MODE_HIRES
                        px *= 2
                    if res in [2,3]:
                        dmode |= config.MODE_LACE
                        py *= 2

                    if aspect == 1:
                        dmode |= config.NTSC_MONITOR_ID
                    else:
                        dmode |= config.PAL_MONITOR_ID
                        py = py * 128 // 100

                    if halfbright:
                        dmode |= config.MODE_EXTRA_HALFBRIGHT

                    if not new_clicked and (px != config.pixel_width or py != config.pixel_height):
                        new_pixel_canvas = pygame.transform.scale(config.pixel_canvas, (px, py))
                        new_pixel_canvas.set_palette(config.pal)
                        config.pixel_canvas = new_pixel_canvas
                        reinit = False

                    config.display_mode = dmode
                    config.pixel_width = px
                    config.pixel_height = py
                    config.color_depth = cdepth
                    config.NUM_COLORS = num_colors
                    if ge.gadget.label == "Make Default":
                        config.saveConfig()
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0 

        apply_bdepth()

        if aspect == 1:
            gNTSC.state = 1
        else:
            gPAL.state = 1

        gres[res].state = 1

        if cdepth == 16:
            g12bit.state = 1
        else:
            g24bit.state = 1

        if running and not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    if ok_clicked:
        config.initialize_surfaces(reinit=reinit)
    else:
        config.recompose()

    return


class PPpic(Gadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        self.pic = imgload('logo.png')
        super(PPpic, self).__init__(type, label, rect, value, maxvalue, id)
        
    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo
        self.screenrect = (x+xo,y+yo,w,h)

        if self.type == Gadget.TYPE_CUSTOM:
            if not self.need_redraw:
                return

            self.need_redraw = False

            if self.label == "#":
                screen.set_clip(self.screenrect)
                screen.blit(pygame.transform.smoothscale(self.pic, (w, h)), (x+xo,y+yo))
        else:
            super(PPpic, self).draw(screen, font, offset)

def about_req(screen):
    req = str2req("About", """
PyDPainter       ############
\xA92020 Mark Riale ############
Version %-8s ############
                 ############
Licensed under   ############
GPL 3 or later.  ############
See LICENSE for  ############
more details.    ############
             [OK]
""" % (config.version), "#", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=PPpic, font=config.font)

    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()
    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = pygame.event.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK":
                    running = 0 

        if running and not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return
