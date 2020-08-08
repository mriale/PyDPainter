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

def screen_format_req(screen):
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
            if bdepth > 5:
                bdepth = 5
                apply_bdepth()
            gDepth[4].enabled = True
            gDepth[4].need_redraw = True
            gDepth[5].enabled = True
            gDepth[5].need_redraw = True
        gres[res].state = 1
    apply_mode()

    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()
    req.draw(screen)
    config.recompose()

    running = 1
    reinit = False
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
                if ge.gadget.label == "OK" and not req.has_error():
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
                    config.display_mode = dmode
                    config.color_depth = cdepth
                    config.NUM_COLORS = 2**bdepth
                    config.truepal = config.get_default_palette(config.NUM_COLORS)
                    config.pal = list(config.truepal)
                    config.pixel_canvas = pygame.Surface((px, py),0,8)
                    reinit = True
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
    if reinit:
        config.initialize_surfaces()
    else:
        config.recompose()

    return

