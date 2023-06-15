#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import numpy as np

config = None

def background_set_config(config_in):
    global config
    config = config_in

class Background:
    def __init__(self):
        self.__enable = False
        self.is_color = None
        self.image = None

    @property
    def enable(self):
        return self.__enable

    @enable.setter
    def enable(self, enable):
        if self.image != None:
            if enable:
                config.clear_pixel_draw_canvas()
                self.image = config.pixel_canvas.copy()
                config.menubar.indicators["background"] = self.draw_indicator
            self.__enable = enable

    def fix(self, screen):
        self.image = screen.copy()
        self.__enable = True
        config.menubar.indicators["background"] = self.draw_indicator

    def free(self):
        config.background.__enable = False
        config.background.image = None
 
    def draw(self, screen):
        if self.__enable and self.image != None:
            screen.blit(self.image, (config.screen_offset_x, config.screen_offset_y))

    def draw_indicator(self, screen):
        if self.__enable:
            px = config.font.xsize // 8
            py = config.font.ysize // 8
            config.font.blitstring(screen, (px*170, py*2), "B", (255,255,255), (0,0,0))

    def set_palette(self, pal):
        if self.image != None:
            self.image.set_palette(pal)
