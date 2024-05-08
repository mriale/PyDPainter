#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
layer.py
Implement a class for layers
"""
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *


class Layer(object):
    """This class is one layer in a stack of bitmaps"""
    def __init__(self, image, priority=0, visible=True):
        self.image = image
        self.visible = visible
        self.priority = priority

    def blit(self, screen, offset=(0,0), rect=None):
        if self.visible:
            if isinstance(self.image, pygame.Surface):
                screen.blit(self.image, offset, rect)
            else:
                self.image.draw(screen, offset, rect)


class LayerStack(object):
    """This class composites a stack of Layer bitmaps"""
    def __init__(self, layers={}):
        self.layers = layers
        print(f"init LayerStack={self}")

    def has_key(self, name):
        return name in self.layers

    def get(self, name):
        return self.layers[name]

    def set(self, name, image, priority=0, visible=True):
        self.layers[name] = Layer(image, priority, visible)

    def delete(self, name):
        del(self.layers, name)

    def blit(self, screen, offset=(0,0), rect=None):
        lowest_layer = True
        for key in sorted(self.layers, key=lambda l: self.layers[l].priority):
            layer = self.layers[key]
            if layer.visible:
                if not layer.image is None and isinstance(layer.image, pygame.Surface):
                    if lowest_layer:
                        layer.image.set_colorkey(None)
                    else:
                        layer.image.set_colorkey(0)
                lowest_layer = False
                layer.blit(screen, offset, rect)

    def set_palette(self, pal):
        for key in self.layers:
            layer = self.layers[key]
            if "set_palette" in dir(layer.image):
                layer.image.set_palette(pal)
