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

    def __repr__(self):
        return f"LayoutTile<name=\"{self.name}\", size={self.size}, calc_rect={self.calc_rect}, anchor={self.anchor}, show={self.show}>"

class LayoutGroup:
    """This class describes a vertically or horizontally tiled layout"""
    VERT = 1
    HORIZ = 2
    def __init__(self, direction, list):
        self.direction = direction
        self.list = list

    def __repr__(self):
        if self.direction == LayoutGroup.VERT:
            dir_str = "VERT"
        else:
            dir_str = "HORIZ"
        outstr = f"LayoutGroup<direction={dir_str} ["
        for item in self.list:
            outstr += f"{item}, "
        outstr = outstr.rstrip(", ")
        outstr += "]>"
        return outstr

class Layout:
    """This class describes a layout of windows"""
    def __init__(self, overlap=True):
        self.list = list()
        self.overlap = overlap
        self.last_overlap = overlap
        self.max_size = [0,0]
        self.need_calc = True

    def add(self, list):
        self.list.extend(list)
        self.need_calc = True

    def calc(self):
        if self.need_calc or self.last_overlap != self.overlap:
            self.need_calc = False
            self.last_overlap = self.overlap

    def get_rect(self, name):
        self.calc()
        rect = self.list[name].calc_rect
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
                    ]),
                ]),
                LayoutTile("animbar", (-1,11)),
                ]),
            ])

print(f"{layout=}")
