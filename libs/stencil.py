#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import numpy as np

config = None

def stencil_set_config(config_in):
    global config
    config = config_in

class Stencil:
    def __init__(self):
        self.enable = False
        self.is_color = None
        self.image = None

    def clear(self):
        self.enable = False
        self.is_color = np.array([False] * config.NUM_COLORS, dtype=bool)
        self.image = None

    def make(self, screen, is_stencil_color):
        self.is_color[:] = is_stencil_color[:]
        self.remake(screen)

    def remake(self, screen):
        self.image = screen.copy()

        #find bgcolor and set colors not in the stencil to it
        off_colors = np.where(self.is_color == False)
        if len(off_colors) > 0 and len(off_colors[0]) > 0:
            bgcolor = int(off_colors[0][0])
            self.image.set_colorkey(bgcolor)
            surf_array = pygame.surfarray.pixels2d(self.image)
            for col in off_colors[0]:
                surf_array[np.where(surf_array == int(col))] = bgcolor
            surf_array = None

        self.enable = True

    def draw(self, screen):
        if self.enable and self.image != None:
            screen.blit(self.image, (0,0))

    def set_palette(self, pal):
        if self.image != None:
            self.image.set_palette(pal)
