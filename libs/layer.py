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


class Layer:
    """This class is one layer in a stack of bitmaps"""
    def __init__(self, image, priority=0, visible=True, parent=None):
        self.image = image
        self.visible = visible
        self.priority = priority
        self.parent = parent

    def __repr__(self):
        return f"Layer {hex(id(self))}: visible={self.visible} priority={self.priority} image={self.image}"

    def copy(self, parent=None):
        img = None
        if not self.image is None:
            img = self.image.copy()
        newlayer = Layer(img, priority=self.priority, visible=self.visible, parent=parent)
        return newlayer

    def blit(self, screen, offset=(0,0), rect=None):
        if self.visible:
            if isinstance(self.image, pygame.Surface):
                screen.blit(self.image, offset, rect)
            elif not screen is None and not self.image is None:
                self.image.draw(screen, offset, rect)


class LayerStack:
    """This class composites a stack of Layer bitmaps"""
    def __init__(self, layers=None):
        if layers is None:
            self.layers = {}
        else:
            self.layers = layers

    def copy(self):
        ls = LayerStack()
        for name in self.layers:
            ls.layers[name] = self.layers[name].copy(ls)
        return ls

    def __repr__(self):
        outstr = f"LayerStack {hex(id(self))}:\n"
        for key in self.layers:
            outstr += f"[\"{key}\"] " + str(self.layers[key]) + "\n"
        outstr = outstr.strip()
        return outstr

    def has_key(self, name):
        return name in self.layers

    def get(self, name):
        return self.layers[name]

    def set(self, name, image, priority=0, visible=True):
        self.layers[name] = Layer(image, priority, visible, self)

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
