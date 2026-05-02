#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
layout.py
"""
config = None

def layout_set_config(config_in):
    global config
    config = config_in

class LayoutTile:
    """This class describes a single tile in a tiled layout"""
    def __init__(self, name, size, visible=True, drawable=None, overlap_offset=[0,0,0,0]):
        self.name = name
        self.size = size
        self.visible = visible
        self.rect = [0, 0, 0, 0]
        self.drawable = drawable
        self.overlap_offset = list(overlap_offset) #top, right, bottom, left

    @property
    def x(self):
        return self.rect[0]

    @x.setter
    def x(self, value):
        self.rect[0] = value

    @property
    def y(self):
        return self.rect[1]

    @y.setter
    def y(self, value):
        self.rect[1] = value

    @property
    def w(self):
        if self.visible:
            return self.size[0]
        else:
            return 0

    @w.setter
    def w(self, value):
        self.rect[2] = value

    @property
    def h(self):
        if self.visible:
            return self.size[1]
        else:
            return 0

    @h.setter
    def h(self, value):
        self.rect[3] = value

    @property
    def ovt(self):
        if self.visible:
            return self.overlap_offset[0]
        else:
            return 0

    @property
    def ovr(self):
        if self.visible:
            return self.overlap_offset[1]
        else:
            return 0

    @property
    def ovb(self):
        if self.visible:
            return self.overlap_offset[2]
        else:
            return 0

    @property
    def ovl(self):
        if self.visible:
            return self.overlap_offset[3]
        else:
            return 0

    def __repr__(self):
        return f"LayoutTile<name=\"{self.name}\", size={self.size}, rect={self.rect}, visible={self.visible}, drawable={self.drawable}, overlap_offset={self.overlap_offset}>"

class Layout:
    """This class describes a layout of windows"""
    def __init__(self, group, overlap=True):
        self.group = group
        self.lookup = {}
        self.overlap = overlap
        self.last_overlap = overlap
        self.rect = [0,0,0,0]
        self.need_calc = True
        self.anchor = None

    def calc_overlap(self):
        menubar = None
        layers = None
        canvas = None
        animbar = None
        tools = None

        for tile in self.group:
            tile.rect = [0, 0, tile.size[0], tile.size[1]]
            match tile.name:
                case "menubar":
                    menubar = tile
                case "layertoolbar":
                    layers = tile
                case "canvas":
                    canvas = tile
                case "animtoolbar":
                    animbar = tile
                case "toolbar":
                    tools = tile

        menubar.w = canvas.w
        layers.y = menubar.h - menubar.ovb
        layers.h = canvas.h
        animbar.y = canvas.h - animbar.h - animbar.ovt
        animbar.w = canvas.w - tools.w
        tools.x = canvas.w - tools.w
        tools.y = menubar.h - menubar.ovb
        tools.h = canvas.h - menubar.h
        self.anchor = canvas
        self.rect = list(canvas.rect)

    def calc_no_overlap(self):
        menubar = None
        layers = None
        canvas = None
        animbar = None
        tools = None

        for tile in self.group:
            tile.rect = [0, 0, tile.size[0], tile.size[1]]
            match tile.name:
                case "menubar":
                    menubar = tile
                case "layertoolbar":
                    layers = tile
                case "canvas":
                    canvas = tile
                case "animtoolbar":
                    animbar = tile
                case "toolbar":
                    tools = tile

        menubar.w = layers.w + canvas.w + tools.w
        layers.y = menubar.h - menubar.ovb
        layers.h = menubar.h + canvas.h + animbar.h
        canvas.x = layers.w
        canvas.y = menubar.h - menubar.ovb
        animbar.y = menubar.h + canvas.h - animbar.ovt
        animbar.w = layers.w + canvas.w
        tools.x = layers.w + canvas.w
        tools.y = menubar.h - menubar.ovb
        tools.h = canvas.h + animbar.h
        self.anchor = None
        self.rect = [0, 0, layers.w + canvas.w + tools.w, menubar.h + canvas.h + animbar.h]

    def calc(self):
        if self.last_overlap != self.overlap:
            self.need_calc = True
        if self.need_calc:
            for tile in self.group:
                if tile.visible:
                    self.lookup[tile.name] = tile
            if self.overlap:
                self.calc_overlap()
            else:
                self.calc_no_overlap()

            self.need_calc = False
            self.last_overlap = self.overlap

    def get_rect(self, name=None):
        self.calc()
        if name is None:
            return list(self.rect)
        if name in self.lookup.keys():
            tile = self.lookup[name]
            rect = list(tile.rect)
            return rect
        else:
            return list([0,0,0,0])

    def set_visible(self, name, value):
        self.calc()
        for tile in self.group:
            if tile.name == name:
                break
        tile.visible = value
        if tile.drawable is not None and "visible" in dir(tile.drawable):
            tile.drawable.visible = value
        self.need_calc = True
        if value == False and name in self.lookup.keys():
            del self.lookup[name]
        self.need_calc = True
        self.calc()

    def draw(self, screen):
        #draw anchor first
        anchor = self.anchor
        if anchor is not None and anchor.drawable is not None:
            anchor.drawable.draw(screen, rect=anchor.rect)
        #draw rest of tiles
        for tile in self.lookup.values():
            if tile != anchor and tile.drawable is not None:
                tile.drawable.draw(screen, rect=tile.rect)

    def __repr__(self):
        self.calc()
        outstr = f"Layout<overlap={self.overlap}, rect={self.rect}, group={self.group}>"
        return outstr;

if __name__ == "__main__":
    layout = Layout([LayoutTile("menubar", (0,12), overlap_offset=[0,0,1,0]),
                     LayoutTile("layers",  (25,0), overlap_offset=[1,0,0,0]),
                     LayoutTile("canvas",  (320,200)),
                     LayoutTile("animbar", (0,12), overlap_offset=[1,0,0,0]),
                     LayoutTile("tools",   (25,0), overlap_offset=[1,0,0,0]),
                    ],
                    overlap=False)

    print(f"{layout=}")

    print(f"\n{layout.overlap=}")
    for k in layout.lookup.keys():
        print(f"{k=} {layout.get_rect(k)}")

    layout.set_visible("layers", False)
    print(f"\nlayers invisible")
    print(f"{layout=}")
    for k in layout.lookup.keys():
        print(f"{k=} {layout.get_rect(k)}")

    layout.set_visible("layers", True)
    layout.set_visible("menubar", False)
    print(f"\nmenubar invisible")
    print(f"{layout=}")
    layout.overlap = True
    print(f"\n{layout.overlap=}")
    for k in layout.lookup.keys():
        print(f"{k=} {layout.get_rect(k)}")

    layout.set_visible("menubar", True)
    print(f"\nmenubar visible")
    print(f"{layout=}")
    layout.overlap = True
    print(f"\n{layout.overlap=}")
    for k in layout.lookup.keys():
        print(f"{k=} {layout.get_rect(k)}")

