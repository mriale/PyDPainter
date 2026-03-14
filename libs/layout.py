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
        self.rect = [0, 0, abs(size[0]), abs(size[1])]
        self.drawable = drawable
        self.overlap_offset = list(overlap_offset) #top, right, bottom, left

    def __repr__(self):
        return f"LayoutTile<name=\"{self.name}\", size={self.size}, rect={self.rect}, visible={self.visible}, drawable={self.drawable}, overlap_offset={self.overlap_offset}>"

class LayoutGroup:
    """This class describes a vertically or horizontally tiled layout"""
    VERT = 1
    HORIZ = 2
    def __init__(self, direction, list):
        self.direction = direction
        self.list = list
        self.rect = [0,0,0,0]
        self.overlap_offset = [0,0,0,0] #top, right, bottom, left

    def calc_reset(self):
        for l in self.list:
            if isinstance(l, LayoutGroup):
                l.calc_reset()
            else:
                l.rect = [0, 0, abs(l.size[0]), abs(l.size[1])]

    def calc_max_size(self, layout):
        self.rect = [0,0,0,0]
        for l in self.list:
            if isinstance(l, LayoutGroup):
                l.calc_max_size(layout)
            elif isinstance(l, LayoutTile):
                if not l.visible:
                    continue
                layout.lookup[l.name] = l
                self.overlap_offset = l.overlap_offset
            if self.direction == LayoutGroup.VERT:
                self.rect[3] += l.rect[3] - l.overlap_offset[0] - l.overlap_offset[2]
                if l.rect[2] > 0:
                    self.rect[2] = l.rect[2]
            else:
                self.rect[2] += l.rect[2] - l.overlap_offset[1] - l.overlap_offset[3]
                if l.rect[3] > 0:
                    self.rect[3] = l.rect[3]

    def calc_tile_size(self):
        for l in self.list:
            if isinstance(l, LayoutGroup):
                l.calc_tile_size()
            elif isinstance(l, LayoutTile):
                if not l.visible:
                    continue
            if l.rect[2] == 0:
                l.rect[2] = self.rect[2]
            if l.rect[3] == 0:
                l.rect[3] = self.rect[3]

    def calc_tile_pos(self):
        pos = [self.rect[0], self.rect[1]]
        for l in self.list:
            if isinstance(l, LayoutTile):
                if not l.visible:
                    continue
            l.rect[0:2] = pos
            if self.direction == LayoutGroup.VERT:
                pos[1] += l.rect[3]
            else:
                pos[0] += l.rect[2]
            if isinstance(l, LayoutGroup):
                l.calc_tile_pos()

    def calc(self, layout):
        self.calc_max_size(layout)
        self.calc_tile_size()
        self.calc_tile_pos()

    def find_tile(self, name):
        retval = None
        for l in self.list:
            if isinstance(l, LayoutGroup):
                retval = l.find_tile(name)
            elif isinstance(l, LayoutTile):
                if name == l.name:
                    return l
        return retval

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
        outstr += f", rect={self.rect}, overlap_offset={self.overlap_offset}"
        outstr += ">"
        return outstr

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
                        self.anchor = tile
                        break
                if anchor:
                    # adjust rects for overlapping
                    cx, cy, cw, ch = anchor.rect
                    for tile in self.lookup.values():
                        tw, th = tile.size
                        if tw < 0:
                            tile.rect[0] = 0
                            tile.rect[2] = abs(tw)
                        elif tw > 0:
                            tile.rect[0] = 0 + cw - tw
                            tile.rect[2] = tw
                        else:
                            tile.rect[0] = 0
                            tile.rect[2] = cw
                        if th < 0:
                            tile.rect[1] = 0
                            tile.rect[3] = abs(th)
                        elif th > 0:
                            tile.rect[1] = 0 + ch - th
                            tile.rect[3] = th
                        else:
                            tile.rect[1] = 0
                            tile.rect[3] = ch
                    # set anchor (canvas) to 0,0
                    anchor.rect = [0, 0, cw, ch]
                    # set group rect to anchor's rect
                    self.group.rect = [0, 0, cw, ch]
                    # find total fixed sizes in the layout
                    top_fixed_h = 0
                    bottom_fixed_h = 0
                    right_fixed_w = 0
                    for t in self.lookup.values():
                        if t.size[1] < 0:
                            top_fixed_h += abs(t.size[1])
                        elif t.size[1] > 0 and t != anchor:
                            bottom_fixed_h += t.size[1]
                        if t.size[0] > 0 and t != anchor:
                            right_fixed_w += t.size[0]
                    # set rects for overlapping based on size signs, with adjustments for fill
                    for tile in self.lookup.values():
                        tw, th = tile.size
                        if tw < 0:
                            tile.rect[0] = 0
                            tile.rect[2] = abs(tw)
                        elif tw > 0:
                            tile.rect[0] = cw - tw
                            tile.rect[2] = tw
                        else:
                            tile.rect[0] = 0
                            if th > 0:
                                tile.rect[2] = cw - right_fixed_w
                            else:
                                tile.rect[2] = cw
                        if th < 0:
                            tile.rect[1] = 0
                            tile.rect[3] = abs(th)
                        elif th > 0:
                            tile.rect[1] = ch - th
                            tile.rect[3] = th
                        else:
                            tile.rect[1] = top_fixed_h
                            if tw < 0:
                                tile.rect[3] = ch - top_fixed_h - bottom_fixed_h
                            elif tw > 0:
                                tile.rect[3] = ch - top_fixed_h
                            else:
                                tile.rect[3] = ch
                            # else keep cw
            self.need_calc = False
            self.last_overlap = self.overlap

    def get_rect(self, name):
        self.calc()
        if name in self.lookup.keys():
            tile = self.lookup[name]
            rect = list(tile.rect)
            rect[0] -= tile.overlap_offset[3]
            rect[1] -= tile.overlap_offset[0]
            return rect
        else:
            return list([0,0,0,0])

    def set_visible(self, name, value):
        self.calc()
        tile = self.group.find_tile(name)
        tile.visible = value
        if tile.drawable is not None and "visible" in dir(tile.drawable):
            tile.drawable.visible = value
        self.need_calc = True
        if value == False and name in self.lookup.keys():
            del self.lookup[name]
        self.group.calc_reset()
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
        outstr = "Layout<"
        outstr += f"group={self.group}"
        outstr += f", overlap={self.overlap}"
        outstr += ">"
        return outstr;

if __name__ == "__main__":
    layout = Layout(
                LayoutGroup(LayoutGroup.VERT, [
                    LayoutTile("menubar", (0,-12), overlap_offset=[0,0,1,0]),
                    LayoutGroup(LayoutGroup.HORIZ, [
                        LayoutGroup(LayoutGroup.VERT, [
                            LayoutGroup(LayoutGroup.HORIZ, [
                                LayoutTile("layers", (-25,0), overlap_offset=[1,0,0,0]),
                                LayoutTile("canvas", (320,200)),
                                ]),
                            LayoutTile("animbar", (0,12), overlap_offset=[1,0,0,0]),
                            ]),
                        LayoutTile("tools", (25,0), overlap_offset=[1,0,0,0]),
                        ]),
                    ]),
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

