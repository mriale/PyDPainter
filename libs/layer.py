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

config = None

def layer_set_config(config_in):
    global config
    config = config_in

class Layer:
    """This class is one layer in a stack of bitmaps"""
    def __init__(self, image, priority=0, visible=True, parent=None, indicator=""):
        self.image = image
        self.visible = visible
        self.priority = priority
        self.parent = parent
        self.indicator = indicator

    def __repr__(self):
        return f"Layer {hex(id(self))}: visible={self.visible} priority={self.priority} image={self.image} indicator={self.indicator}"

    def copy(self, parent=None):
        img = None
        if not self.image is None:
            img = self.image.copy()
        if parent is None:
            parent = self.parent
        newlayer = Layer(img, priority=self.priority, visible=self.visible, parent=parent, indicator=self.indicator)
        return newlayer

    def blit(self, screen, offset=(0,0), rect=None):
        if self.visible:
            if isinstance(self.image, pygame.Surface):
                screen.blit(self.image, offset, rect)
            elif not screen is None and not self.image is None:
                self.image.draw(screen, offset, rect)


class LayerStack:
    """This class composites a stack of Layer bitmaps"""
    def __init__(self, layers=None, indicatorx=0):
        if layers is None:
            self.layers = {}
        else:
            self.layers = layers
        self.indicatorx = indicatorx

    def copy(self):
        ls = LayerStack(indicatorx = self.indicatorx)
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

    def set(self, name, image, priority=0, visible=True, parent=None, indicator=""):
        if parent is None:
            parent = self
        self.layers[name] = Layer(image, priority, visible, parent=parent, indicator=indicator)

    def delete(self, name):
        del(self.layers, name)

    def blit(self, screen, offset=(0,0), rect=None, exclude=[]):
        lowest_layer = True
        for key in sorted(self.layers, key=lambda l: self.layers[l].priority):
            layer = self.layers[key]
            if layer.visible and not layer.indicator in exclude:
                if not layer.image is None and isinstance(layer.image, pygame.Surface):
                    if lowest_layer:
                        layer.image.set_colorkey(None)
                    else:
                        layer.image.set_colorkey(0)
                    lowest_layer = False
                    layer.blit(screen, offset, rect)

    def get_at(self, coords):
        image = config.pixel_canvas.copy().convert()
        self.blit(image, (0,0))
        return tuple(image.get_at(coords))[0:3]

    def set_palette(self, pal):
        for key in self.layers:
            layer = self.layers[key]
            if "set_palette" in dir(layer.image) and \
               "get_bytesize" in dir(layer.image) and layer.image.get_bytesize() == 1:
                layer.image.set_palette(pal)

    def draw_indicator(self, screen):
        xpos = self.indicatorx
        px = config.font.xsize // 8
        py = config.font.ysize // 8
        pw = config.font.xsize
        for key in sorted(self.layers, key=lambda l: self.layers[l].priority):
            layer = self.layers[key]
            if layer.visible and len(layer.indicator) > 0:
                config.font.blitstring(screen, (px*xpos, py*2), layer.indicator, (255,255,255), (0,0,0))
                xpos += pw*len(layer.indicator)

    def get_flattened(self, exclude=[]):
        pic = config.pixel_canvas.copy()
        self.blit(pic, exclude=exclude)
        return pic
