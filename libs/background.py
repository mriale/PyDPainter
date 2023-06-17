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
        self.is_reference = False
        self.image = None

    @property
    def enable(self):
        return self.__enable

    @enable.setter
    def enable(self, enable):
        if self.image != None:
            if enable:
                config.clear_pixel_draw_canvas()
                config.menubar.indicators["background"] = self.draw_indicator
            self.__enable = enable

    def fix(self, screen):
        self.image = screen.copy()
        self.__enable = True
        self.is_reference = False
        config.menubar.indicators["background"] = self.draw_indicator

    def open(self, filename):
        self.image = pygame.image.load(filename)
        self.image = pygame.transform.smoothscale(self.image.convert(), config.pixel_canvas.get_size())
        self.__enable = True
        self.is_reference = True
        config.menubar.indicators["background"] = self.draw_indicator

    def free(self):
        self.__enable = False
        self.image = None
 
    def draw(self, screen):
        if self.__enable and self.image != None:
            screen.blit(self.image, (config.screen_offset_x, config.screen_offset_y))
        elif not self.__enable and self.image != None:
            screen.fill(config.pal[0])

    def blit(self, screen, coords, rect=None):
        if self.__enable and self.image != None:
            screen.blit(self.image, coords, rect)
        elif not self.__enable and self.image != None:
            pygame.draw.rect(screen, config.pal[0], (coords[0], coords[1], rect[2], rect[3]))

    def draw_indicator(self, screen):
        if self.__enable:
            px = config.font.xsize // 8
            py = config.font.ysize // 8
            config.font.blitstring(screen, (px*170, py*2), "R" if self.is_reference else "B", (255,255,255), (0,0,0))

    def set_palette(self, pal):
        if self.image != None and not self.is_reference:
            self.image.set_palette(pal)
