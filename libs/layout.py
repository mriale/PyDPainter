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
    def __init__(self, name, size, visible=True):
        self.name = name
        self.size = size
        self.visible = visible
        self.calc_rect = [0, 0, abs(size[0]), abs(size[1])]

    def __repr__(self):
        return f"LayoutTile<name=\"{self.name}\", size={self.size}, calc_rect={self.calc_rect}, visible={self.visible}>"

class LayoutGroup:
    """This class describes a vertically or horizontally tiled layout"""
    VERT = 1
    HORIZ = 2
    def __init__(self, direction, list):
        self.direction = direction
        self.list = list
        self.calc_rect = [0,0,0,0]

    def calc_reset(self):
        for l in self.list:
            if isinstance(l, LayoutGroup):
                l.calc_reset()
            else:
                l.calc_rect = [0, 0, abs(l.size[0]), abs(l.size[1])]

    def calc_max_size(self, layout):
        self.calc_rect = [0,0,0,0]
        for l in self.list:
            if isinstance(l, LayoutGroup):
                l.calc_max_size(layout)
            elif isinstance(l, LayoutTile):
                layout.lookup[l.name] = l
            if self.direction == LayoutGroup.VERT:
                self.calc_rect[3] += l.calc_rect[3]
                if l.calc_rect[2] > 0:
                    self.calc_rect[2] = l.calc_rect[2]
            else:
                self.calc_rect[2] += l.calc_rect[2]
                if l.calc_rect[3] > 0:
                    self.calc_rect[3] = l.calc_rect[3]

    def calc_tile_size(self):
        for l in self.list:
            if isinstance(l, LayoutGroup):
                l.calc_tile_size()
            if l.calc_rect[2] == 0:
                l.calc_rect[2] = self.calc_rect[2]
            if l.calc_rect[3] == 0:
                l.calc_rect[3] = self.calc_rect[3]

    def calc_tile_pos(self):
        pos = [self.calc_rect[0], self.calc_rect[1]]
        for l in self.list:
            l.calc_rect[0:2] = pos
            if self.direction == LayoutGroup.VERT:
                pos[1] += l.calc_rect[3]
            else:
                pos[0] += l.calc_rect[2]
            if isinstance(l, LayoutGroup):
                l.calc_tile_pos()

    def calc(self, layout):
        self.calc_max_size(layout)
        self.calc_tile_size()
        self.calc_tile_pos()

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
    def __init__(self, group, overlap=True):
        self.group = group
        self.lookup = {}
        self.overlap = overlap
        self.last_overlap = overlap
        self.calc_rect = [0,0,0,0]
        self.need_calc = True

    def calc(self):
        if self.last_overlap != self.overlap:
            self.group.calc_reset()
            self.need_calc = True
        if self.need_calc:
            self.group.calc(self)
            if self.overlap:
                # find anchor (non-variable size tile, e.g., "canvas")
                anchor = None
                for tile in self.lookup.values():
                    if tile.size[0] > 0 and tile.size[1] > 0:
                        anchor = tile
                        break
                if anchor:
                    # adjust rects for overlapping
                    cx, cy, cw, ch = anchor.calc_rect
                    for tile in self.lookup.values():
                        if tile == anchor:
                            continue
                        tw, th = tile.size
                        if tw < 0:
                            tile.calc_rect[0] = cx + tw
                            tile.calc_rect[2] = abs(tw)
                        elif tw > 0:
                            tile.calc_rect[0] = cx + cw - tw
                            tile.calc_rect[2] = tw
                        else:
                            tile.calc_rect[0] = cx
                            tile.calc_rect[2] = cw
                        if th < 0:
                            tile.calc_rect[1] = cy + th
                            tile.calc_rect[3] = abs(th)
                        elif th > 0:
                            tile.calc_rect[1] = cy + ch - th
                            tile.calc_rect[3] = th
                        else:
                            tile.calc_rect[1] = cy
                            tile.calc_rect[3] = ch
                    # set group rect to anchor's rect
                    self.group.calc_rect = list(anchor.calc_rect)
            self.need_calc = False
            self.last_overlap = self.overlap

    def get_rect(self, name):
        self.calc()
        tile = self.lookup[name]
        rect = list(tile.calc_rect)
        return rect

    def __repr__(self):
        self.calc()
        outstr = "Layout<"
        outstr += f"group={self.group}"
        outstr += f", overlap={self.overlap}"
        outstr += ">"
        return outstr;

layout = Layout(
            LayoutGroup(LayoutGroup.VERT, [
                LayoutTile("menubar", (0,-11)),
                LayoutGroup(LayoutGroup.HORIZ, [
                    LayoutGroup(LayoutGroup.VERT, [
                        LayoutGroup(LayoutGroup.HORIZ, [
                            LayoutTile("layers", (-25,0)),
                            LayoutTile("canvas", (320,200)),
                            ]),
                        LayoutTile("animbar", (0,11)),
                        ]),
                    LayoutTile("tools", (25,0)),
                    ]),
                ]),
            overlap=False)

print(f"{layout=}")

print(f"\n{layout.overlap=}")
for k in layout.lookup.keys():
    print(f"{k=} {layout.get_rect(k)}")

layout.overlap = True
print(f"\n{layout.overlap=}")
for k in layout.lookup.keys():
    print(f"{k=} {layout.get_rect(k)}")


