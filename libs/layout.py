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
    def __init__(self, name, size, anchor=False, show=True):
        self.name = name
        self.size = size
        self.anchor = anchor
        self.show = show
        self.calc_rect = [0, 0, size[0], size[1]]
        self.parent = None

    def __repr__(self):
        return f"LayoutTile<name=\"{self.name}\", size={self.size}, calc_rect={self.calc_rect}, anchor={self.anchor}, show={self.show}>"

class LayoutGroup:
    """This class describes a vertically or horizontally tiled layout"""
    VERT = 1
    HORIZ = 2
    def __init__(self, direction, list):
        self.direction = direction
        self.list = list
        self.calc_rect = [0,0,0,0]
        self.parent = None

    def calc_max_size(self, layout):
        self.calc_rect = [0,0,0,0]
        for l in self.list:
            if isinstance(l, LayoutGroup):
                l.calc_max_size(layout)
            elif isinstance(l, LayoutTile):
                layout.lookup[l.name] = l
                l.parent = self
            if self.direction == LayoutGroup.VERT:
                self.calc_rect[3] += l.calc_rect[3]
                if l.calc_rect[2] > 0:
                    self.calc_rect[2] = l.calc_rect[2]
            else:
                self.calc_rect[2] += l.calc_rect[2]
                if l.calc_rect[3] > 0:
                    self.calc_rect[3] = l.calc_rect[3]
        #print(f"{self.calc_rect=}")

    def calc_tile_size(self):
        for l in self.list:
            if isinstance(l, LayoutGroup):
                l.calc_tile_size()
            if l.calc_rect[2] < 0:
                l.calc_rect[2] = self.calc_rect[2]
            if l.calc_rect[3] < 0:
                l.calc_rect[3] = self.calc_rect[3]

    def calc_tile_pos(self, parent):
        self.parent = parent
        pos = 0
        for l in self.list:
            if isinstance(l, LayoutGroup):
                l.calc_tile_pos(self)
                if self.direction == LayoutGroup.VERT:
                    l.calc_rect[1] = pos
                    pos += l.calc_rect[3]
                else:
                    l.calc_rect[0] = pos
                    pos += l.calc_rect[2]
            elif isinstance(l, LayoutTile):
                l.parent = self
                if self.direction == LayoutGroup.VERT:
                    l.calc_rect[1] = pos
                    pos += l.calc_rect[3]
                else:
                    l.calc_rect[0] = pos
                    pos += l.calc_rect[2]

    def calc(self, layout):
        self.calc_max_size(layout)
        self.calc_tile_size()
        self.calc_tile_pos(None)

    def __repr__(self):
        if self.direction == LayoutGroup.VERT:
            dir_str = "VERT"
        else:
            dir_str = "HORIZ"
        outstr = f"LayoutGroup<direction={dir_str}, ["
        for item in self.list:
            outstr += f"{item}"
        outstr = outstr.rstrip(", ")
        outstr += "]"
        outstr += f", calc_rect={self.calc_rect}"
        outstr += ">"
        return outstr

class Layout:
    """This class describes a layout of windows"""
    def __init__(self, overlap=True):
        self.list = list()
        self.lookup = {}
        self.overlap = overlap
        self.last_overlap = overlap
        self.calc_rect = [0,0,0,0]
        self.need_calc = True

    def add(self, list):
        self.list.extend(list)
        self.need_calc = True

    def calc(self):
        if self.need_calc or self.last_overlap != self.overlap:
            anchor_tile = None
            for l in self.list:
                if isinstance(l, LayoutGroup):
                    l.calc(self)
                elif isinstance(l, LayoutTile):
                    print(f"layout tile: {l}")

            self.need_calc = False
            self.last_overlap = self.overlap

    def get_rect(self, name):
        self.calc()
        tile = self.lookup[name]
        rect = list(tile.calc_rect)
        lg = tile.parent
        while not lg is None:
            if lg.direction == LayoutGroup.VERT:
                rect[1] += lg.calc_rect[1]
            else:
                rect[0] += lg.calc_rect[0]
            lg = lg.parent
        return rect

    def __repr__(self):
        self.calc()
        outstr = "Layout<"
        outstr += "list=["
        for g in self.list:
            outstr += f"{g}, "
        outstr = outstr.rstrip(", ")
        outstr += "]"
        outstr += f", overlap={self.overlap}"
        outstr += ">"
        return outstr;

layout = Layout()
layout.add([LayoutGroup(LayoutGroup.VERT, [
                LayoutTile("menubar", (-1,11)),
                LayoutGroup(LayoutGroup.HORIZ, [
                    LayoutGroup(LayoutGroup.VERT, [
                        LayoutGroup(LayoutGroup.HORIZ, [
                            LayoutTile("layers", (25,-1)),
                            LayoutTile("canvas", (320,200), anchor=True),
                            ]),
                        LayoutTile("animbar", (-1,11)),
                        ]),
                    LayoutTile("tools", (25,-1)),
                    ]),
                ]),
            ])

print(f"{layout=}")

for k in layout.lookup.keys():
    print(f"{k=} {layout.get_rect(k)}")

