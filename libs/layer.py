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

from libs.gadget import GadgetEvent

import numpy as np

config = None

# 4x4 ordered dither matrix used to approximate layer opacity in an
# indexed-color display.  Index 0 in every user layer is transparent.
_BAYER4 = np.array([
    [ 0,  8,  2, 10],
    [12,  4, 14,  6],
    [ 3, 11,  1,  9],
    [15,  7, 13,  5],
], dtype=np.uint8)
_BAYER_THRESHOLD = ((_BAYER4.astype(np.float32) + 0.5) * 255.0 / 16.0)

def layer_set_config(config_in):
    global config
    config = config_in

class Layer:
    """This class is one layer in a stack of bitmaps"""
    def __init__(self, image, priority=0, visible=True, parent=None, indicator="", opacity=255, kind="user", transparent_index=0):
        self.image = image
        self.visible = visible
        self.priority = priority
        self.parent = parent
        self.indicator = indicator
        self.opacity = opacity
        self.kind = kind
        self.transparent_index = transparent_index

    def __repr__(self):
        return f"Layer {hex(id(self))}: visible={self.visible} priority={self.priority} image={self.image} indicator={self.indicator} opacity={self.opacity} kind={self.kind}"

    def copy(self, parent=None):
        img = None
        if not self.image is None:
            if isinstance(self.image, pygame.Surface):
                img = self.image.copy()
            elif "copy" in dir(self.image):
                img = self.image.copy()
        if parent is None:
            parent = self.parent
        newlayer = Layer(img, priority=self.priority, visible=self.visible, parent=parent,
                         indicator=self.indicator, opacity=self.opacity, kind=self.kind,
                         transparent_index=self.transparent_index)
        return newlayer

    def blit(self, screen, offset=(0,0), rect=None):
        """Draw this layer. Only used for non-surface layers such as the stencil."""
        if self.visible:
            if isinstance(self.image, pygame.Surface):
                screen.blit(self.image, offset, rect)
            elif not screen is None and not self.image is None and "draw" in dir(self.image):
                self.image.draw(screen, offset, rect)

class LayerStack:
    """This class composites a stack of Layer bitmaps"""
    def __init__(self, layers=None, indicatorx=0, current_layer_name=""):
        if layers is None:
            self.layers = {}
        else:
            self.layers = layers
        self.indicatorx = indicatorx
        self.repeat = False
        self.current_layer_name = current_layer_name
        self.config = config

    def copy(self):
        ls = LayerStack(indicatorx=self.indicatorx, current_layer_name=self.current_layer_name)
        ls.config = self.config
        for name in self.layers:
            ls.layers[name] = self.layers[name].copy(ls)
        return ls

    def __repr__(self):
        outstr = f"LayerStack {hex(id(self))} current_layer_name=\"{self.current_layer_name}\":\n"
        for key in self.layers:
            outstr += f"[\"{key}\"] " + str(self.layers[key]) + "\n"
        outstr = outstr.strip()
        return outstr

    def has_key(self, name):
        return name in self.layers

    def get(self, name=None):
        if name is None:
            if self.has_key(self.current_layer_name):
                return self.layers[self.current_layer_name]
            else:
                return None
        else:
            return self.layers.get(name)

    def set(self, name, image=None, priority=None, visible=None, parent=None, indicator=None,
            opacity=None, kind=None, transparent_index=None):
        if name in self.layers.keys():
            l = self.layers[name]
            if not image is None:
                l.image = image
            if not priority is None:
                l.priority = priority
            if not visible is None:
                l.visible = visible
            if not parent is None:
                l.parent = parent
            if not indicator is None:
                l.indicator = indicator
            if not opacity is None:
                l.opacity = opacity
            if not kind is None:
                l.kind = kind
            if not transparent_index is None:
                l.transparent_index = transparent_index
        else:
            if priority is None:
                priority = 0
            if visible is None:
                visible = True
            if parent is None:
                parent = self
            if indicator is None:
                indicator = ""
            if opacity is None:
                opacity = 255
            if kind is None:
                kind = "user"
            if transparent_index is None:
                transparent_index = 0
            self.layers[name] = Layer(image, priority, visible, parent=parent, indicator=indicator,
                                      opacity=opacity, kind=kind, transparent_index=transparent_index)

    def delete(self, name):
        if name in self.layers:
            del self.layers[name]

    def get_priority_name(self, priority):
        for key in self.layers:
            if self.layers[key].priority == priority:
                return key
        return None

    def sorted_layers(self):
        return [self.layers[key] for key in sorted(self.layers, key=lambda l: self.layers[l].priority)]

    def names(self):
        return [key for key in sorted(self.layers, key=lambda l: self.layers[l].priority)]

    def user_layer_names(self):
        return [name for name in self.names() if self.layers[name].kind == "user"]

    def has_user_layers(self):
        return len(self.user_layer_names()) > 0

    def get_page_size(self):
        if config is not None:
            w = getattr(config, "pixel_width", 0)
            h = getattr(config, "pixel_height", 0)
            if w > 0 and h > 0:
                return (w, h)
        for layer in self.layers.values():
            if isinstance(layer.image, pygame.Surface):
                return layer.image.get_size()
        return (1, 1)

    def _layer_array(self, layer, size, pal):
        """Return an indexed 8-bit array for a layer, remapping RGB images."""
        img = layer.image
        if img.get_size() != size:
            tmp = pygame.Surface(size, 0, 8)
            tmp.set_palette(pal)
            tmp.blit(img, (0, 0))
            return pygame.surfarray.array2d(tmp)
        if img.get_bytesize() != 1:
            tmp = pygame.Surface(size, 0, 8)
            tmp.set_palette(pal)
            tmp.blit(img, (0, 0))
            return pygame.surfarray.array2d(tmp)
        return pygame.surfarray.array2d(img)

    def composite(self, exclude=[]):
        """Composite all visible layers into a new indexed 8-bit surface.

        The stack is composited from scratch so model surfaces are never
        modified (no set_colorkey/set_alpha on layer images). Index 0 is
        transparent on every layer; the bottom is filled with palette
        index 0.
        """
        pal = self.get_palette()
        if pal is None and config is not None:
            pal = getattr(config, "pal", None)
        size = self.get_page_size()
        pic = pygame.Surface(size, 0, 8)
        if pal is not None:
            pic.set_palette(pal)
        else:
            pal = pic.get_palette()
        # Start from a defined (transparent/background) image; untouched
        # pixels would otherwise be uninitialized surface memory.
        pic.fill(0)

        layers_data = []
        overlays = []
        for layer in self.sorted_layers():
            if not layer.visible or layer.indicator in exclude:
                continue
            if isinstance(layer.image, pygame.Surface):
                if layer.opacity <= 0:
                    continue
                arr = self._layer_array(layer, size, pal)
                # References ("R") are images, not transparent indexed layers.
                keyed = layer.kind != "reference" and layer.indicator != "R"
                layers_data.append((arr, keyed, layer.opacity, layer.transparent_index))
            elif layer.image is not None and "draw" in dir(layer.image):
                overlays.append(layer)

        if layers_data:
            w, h = size
            dst = pygame.surfarray.pixels2d(pic)
            try:
                for arr, keyed, opacity, transparent_index in layers_data:
                    mask = arr != transparent_index if keyed else np.ones(arr.shape, dtype=bool)
                    if opacity < 255:
                        # Ordered dither approximates alpha while staying in
                        # the palette, so flattening matches the display.
                        xx, yy = np.indices((w, h))
                        threshold = _BAYER_THRESHOLD[yy % 4, xx % 4]
                        mask = mask & (threshold < opacity)
                    dst[mask] = arr[mask]
            finally:
                del dst
        else:
            pic.fill(0)

        # Non-surface layers (the stencil) are overlays and drawn last.
        if overlays:
            for layer in overlays:
                layer.blit(pic, (0, 0))
        return pic

    def blit(self, screen, offset=(0,0), rect=None, exclude=[]):
        pic = self.composite(exclude=exclude)
        if rect is None:
            screen.blit(pic, offset)
        else:
            screen.blit(pic, offset, rect)

    def get_at(self, coords):
        image = self.composite()
        return tuple(image.get_at(coords))[0:3]

    def _pixel_index(self, img, x, y, pal):
        """Return the palette index of one pixel of a layer image."""
        if img.get_bytesize() == 1:
            return img.get_at_mapped((x, y))
        tmp = pygame.Surface((1, 1), 0, 8)
        if pal is not None:
            tmp.set_palette(pal)
        tmp.blit(img, (0, 0), (x, y, 1, 1))
        return tmp.get_at_mapped((0, 0))

    def get_at_index(self, coords):
        """Return the composited palette index at one pixel.

        This resolves the pixel directly instead of compositing the whole
        page, because the dropper calls it for every mouse motion event.
        """
        x, y = int(coords[0]), int(coords[1])
        pal = self.get_palette()
        if pal is None and config is not None:
            pal = getattr(config, "pal", None)
        for layer in reversed(self.sorted_layers()):
            if not layer.visible:
                continue
            img = layer.image
            if not isinstance(img, pygame.Surface) or layer.opacity <= 0:
                continue
            if x < 0 or y < 0 or x >= img.get_width() or y >= img.get_height():
                continue
            idx = self._pixel_index(img, x, y, pal)
            keyed = layer.kind != "reference" and layer.indicator != "R"
            if keyed and idx == layer.transparent_index:
                continue
            if layer.opacity < 255:
                threshold = _BAYER_THRESHOLD[y % 4, x % 4]
                if not (threshold < layer.opacity):
                    continue
            return idx
        return 0

    def get_palette(self):
        for key in self.layers:
            layer = self.layers[key]
            if isinstance(layer.image, pygame.Surface) and \
               "get_palette" in dir(layer.image) and \
               "get_bytesize" in dir(layer.image) and layer.image.get_bytesize() == 1:
                pal = layer.image.get_palette()
                if not pal is None:
                    return(pal)
        return None

    def set_palette(self, pal):
        for key in self.layers:
            layer = self.layers[key]
            if isinstance(layer.image, pygame.Surface) and \
               "set_palette" in dir(layer.image) and \
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
        pic = self.composite(exclude=exclude)
        pal = self.get_palette()
        if not pal is None:
            pic.set_palette(pal)
        return pic

    def merge_down(self, name=None):
        """Merge a layer onto the layer immediately below it."""
        if name is None:
            name = self.current_layer_name
        layer = self.get(name)
        if layer is None:
            return False
        below = None
        for other in self.sorted_layers():
            if other.priority >= layer.priority:
                break
            below = other
        if below is None or not isinstance(below.image, pygame.Surface) or \
           not isinstance(layer.image, pygame.Surface):
            return False
        # Merge onto an indexed copy of the lower layer so the result stays
        # in the palette model even if "below" is an RGB reference image.
        below_image = below.image
        if below_image.get_bytesize() != 1:
            converted = pygame.Surface(below_image.get_size(), 0, 8)
            converted.set_palette(config.pal)
            converted.blit(below_image, (0, 0))
            below_image = converted
        # Composite just these two layers, keeping the lower layer opaque.
        result = below_image.copy()
        if layer.opacity < 255:
            pic = pygame.Surface(result.get_size(), 0, 8)
            pic.set_palette(result.get_palette() or config.pal)
            pic.blit(result, (0,0))
            arr = pygame.surfarray.array2d(layer.image)
            src = pygame.surfarray.pixels2d(pic)
            try:
                mask = arr != layer.transparent_index
                if layer.opacity < 255:
                    h, w = arr.shape[1], arr.shape[0]
                    xx, yy = np.indices((w, h))
                    threshold = _BAYER_THRESHOLD[yy % 4, xx % 4]
                    mask = mask & (threshold < layer.opacity)
                src[mask] = arr[mask]
            finally:
                del src
            result = pic
        else:
            top = layer.image.copy()
            top.set_colorkey(layer.transparent_index)
            result.blit(top, (0,0))
        below.image = result
        below.image.set_palette(config.pal)
        self.delete(name)
        self.current_layer_name = self.get_priority_name(below.priority) or ""
        return True

    def process_layertoolbar_events(self, mta_list, event):
        for ge in mta_list:
            if ge.gadget.id == "opacityslider":
                if self.has_key(self.current_layer_name):
                    opacity = max(0, min(255, ge.gadget.value * 17))
                    # Opacity is shared by all animation frames.
                    if config is not None and hasattr(config, "set_layer_opacity"):
                        config.set_layer_opacity(self.current_layer_name, opacity)
                    else:
                        self.get(self.current_layer_name).opacity = opacity
                    if ge.type == GadgetEvent.TYPE_GADGETUP and config is not None:
                        # Record the completed drag so it can be undone.
                        config.save_undo()
                        config.doKeyAction()
