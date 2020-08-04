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

[NTSC~PAL]

[Cancel][OK][Make Default]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)

    aspect = 1

    for g in req.gadgets:
        print (g.id + " " + g.label)
    gNTSC = req.gadget_id("0_7")
    gPAL = req.gadget_id("5_7")

    res = 0
    gres = []
    for g in req.gadgets:
        if re.search(r'\dx\d\d\d$', g.label):
            gres.append(g)
            print(g.label)
    gres[res].state = 1

    if aspect == 1:
        gNTSC.state = 1
    else:
        gPAL.state = 1

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
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0 

        if aspect == 1:
            gNTSC.state = 1
        else:
            gPAL.state = 1

        gres[res].state = 1

        if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return

