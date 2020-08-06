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
[Interlace  320x200] [  8][128]
[Hi-Res     640x400] [ 16][256]
                      Out of:
[NTSC~PAL]           [4096~16M]

[Cancel][OK][Make Default]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)

    aspect = 1
    cdepth = 12
    depth = 5

    for g in req.gadgets:
        print (g.id + " " + g.label)

    gDepth = []
    for g in req.gadgets:
        if g.label.lstrip() in ['2','4','8','16','32','64','128','256']:
            gDepth.append(g)
    gDepth.sort(key=lambda g: g.label)

    for g in gDepth:
        print (g.label)

    gNTSC = req.gadget_id("0_7")
    gPAL = req.gadget_id("5_7")

    g12bit = req.gadget_id("21_7")
    g24bit = req.gadget_id("26_7")

    res = 0
    gres = []
    for g in req.gadgets:
        if re.search(r'\dx\d\d\d$', g.label):
            gres.append(g)
            print(g.label)
    gres[res].state = 1

    gDepth[depth-1].state = 1

    if aspect == 1:
        gNTSC.state = 1
    else:
        gPAL.state = 1

    if cdepth == 12:
        g12bit.state = 1
    else:
        g24bit.state = 1

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
            if ge.gadget == gNTSC:
                aspect = 1
                for g in gres:
                    g.label = g.label.replace("256", "200")
                    g.label = g.label.replace("512", "400")
                    g.need_redraw = True
            elif ge.gadget == gPAL:
                aspect = 2
                for g in gres:
                    g.label = g.label.replace("200", "256")
                    g.label = g.label.replace("400", "512")
                    g.need_redraw = True
            elif ge.gadget == g12bit:
                cdepth = 12
            elif ge.gadget == g24bit:
                cdepth = 24
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0 

        gDepth[depth-1].state = 1

        if aspect == 1:
            gNTSC.state = 1
        else:
            gPAL.state = 1

        gres[res].state = 1

        if cdepth == 12:
            g12bit.state = 1
        else:
            g24bit.state = 1

        if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return

