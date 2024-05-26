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
        self.__enable = False
        self.is_color = None
        self.image = None
        self.mask = None

    def copy(self):
        st = Stencil()
        st.__enable = self.__enable
        st.is_color = self.is_color
        if not self.image is None:
            st.image = self.image.copy()
        st.mask = self.mask

    @property
    def enable(self):
        return self.__enable

    @enable.setter
    def enable(self, enable):
        if self.image != None:
            if enable:
                config.clear_pixel_draw_canvas()
                self.image = config.pixel_canvas.copy()
                config.menubar.indicators["stencil"] = self.draw_indicator
            self.__enable = enable

    def clear(self):
        self.__enable = False
        self.is_color = np.array([False] * config.NUM_COLORS, dtype=bool)
        self.image = None

    def make(self, screen, is_stencil_color):
        self.is_color[:] = is_stencil_color[:]
        self.remake(screen)

    def remake(self, screen):
        self.image = screen.copy()
        #create mask
        surf_array = pygame.surfarray.pixels2d(self.image)
        self.mask = np.where(self.is_color[surf_array])
        surf_array = None
        self.__enable = True
        config.menubar.indicators["stencil"] = self.draw_indicator

    def lock_fg(self, screen):
        self.image = screen.copy()
        #create mask
        surf_array = pygame.surfarray.pixels2d(self.image)
        self.mask = np.where(surf_array != 0)
        surf_array = None
        self.__enable = True
        config.menubar.indicators["stencil"] = self.draw_indicator

    def reverse(self):
        if self.mask != None:
            self.image = config.pixel_canvas.copy()
            #Draw mask and reverse it
            mask_image = config.pixel_canvas.copy()
            surf_array = pygame.surfarray.pixels2d(mask_image)
            surf_array[:,:] = 0
            surf_array[self.mask] = 1
            self.mask = np.where(surf_array == 0)
            surf_array = None
            self.is_color = np.invert(self.is_color)

    def free(self):
        config.stencil.__enable = False
        config.stencil.image = None
        config.stencil.mask = None
 
    def draw(self, screen):
        if self.__enable and self.image != None and self.mask != None:
            surf_array = pygame.surfarray.pixels2d(screen)
            surf_array2 = pygame.surfarray.pixels2d(self.image)
            surf_array[self.mask] = surf_array2[self.mask]
            surf_array = None
            surf_array2 = None

    def draw_indicator(self, screen):
        if self.__enable:
            px = config.font.xsize // 8
            py = config.font.ysize // 8
            config.font.blitstring(screen, (px*160, py*2), "S", (255,255,255), (0,0,0))

    def set_palette(self, pal):
        if self.image != None:
            self.image.set_palette(pal)
