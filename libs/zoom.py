#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
zoom.py
Implement a class for the magnify feature
"""
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

config = None

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

class Zoom:
    """This class handles the magnify feature"""
    def __init__(self, config_in):
        global config
        config = config_in

        self.on = False
        self.center = [0,0]
        self.left_rect = (0,0,0,0)
        self.right_rect = (0,0,0,0)
        self.pixel_rect = (0,0,0,0)
        self.border_rect = (0,0,0,0)
        self.mousedown_side = 1
        self.xoffset = 0
        self.yoffset = 0
        self.factor = 4
        self.factor_min = 2
        self.factor_max = 8
        self.box_on = False

    def process_event(self, screen, e):
        gotkey = False
        x,y = self.center
        if e.key == K_n:
            gotkey = True
            x,y = config.get_mouse_pixel_pos(e)
        elif e.key == K_UP:
            gotkey = True
            y -= 20 // self.factor
        elif e.key == K_DOWN:
            gotkey = True
            y += 20 // self.factor
        elif e.key == K_LEFT:
            gotkey = True
            x -= 20 // self.factor
        elif e.key == K_RIGHT:
            gotkey = True
            x += 20 // self.factor
        self.center = [x,y]
        return gotkey

    def region(self, coords):
        if self.on:
            #check regions
            return 0
        else:
            return 0
