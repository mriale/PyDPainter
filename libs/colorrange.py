#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

class colorrange:
    def __init__(self, rate=0, flags=1, low=0, high=0):
        if rate < 16384:
            self.rate = rate
        else:
            self.rate = 16384
        self.flags = flags
        if flags & 1 == 0:
            self.low = 0
            self.high = 0
        else:
            self.low = low
            self.high = high
        self.last_timer = 0

    def apply_to_pal(self, pal):
        timer = pygame.time.get_ticks()
        rate_milli = self.rate_to_milli()
        if pal != None and self.rate > 0 and self.flags & 1 and self.low != self.high and self.low < len(pal) and self.high < len(pal):
            if timer // rate_milli != self.last_timer // rate_milli:
                if self.flags & 2:
                    #reverse
                    lowcol = pal[self.low]
                    del pal[self.low]
                    pal.insert(self.high, lowcol)
                else:
                    #normal
                    highcol = pal[self.high]
                    del pal[self.high]
                    pal.insert(self.low, highcol)
        self.last_timer = timer

    def rate_to_milli(self):
        if self.rate == 0:
            return 1
        else:
            return 273067//self.rate

    def get_hz(self):
        if self.is_active():
            return self.rate//273
        else:
            return 0

    def set_hz(self, hz):
        self.rate = hz * 273

    def is_active(self):
        if self.low == self.high and self.low == 0:
            return False
        else:
            return True

    def is_reverse(self):
        if self.flags & 2:
            return True
        else:
            return False

    def set_reverse(self, revflag):
        if revflag:
            self.flags = self.flags | 2
        else:
            self.flags = self.flags & 253

    def get_dir(self):
        if self.is_active():
            if self.flags & 2:
                return -1
            else:
                return 1
        else:
            return 0

    def set_dir(self, dir):
        if dir == -1:
            self.set_reverse(True)
        elif dir == 1:
            self.set_reverse(False)

    def get_flags(self):
        if self.is_active():
            return self.flags | 1
        else:
            return self.flags & 254

    def next_color(self, color_index):
        if color_index >= self.low and color_index <= self.high:
            if self.flags & 2:
                #reverse
                color_index = color_index - 1
                if color_index < self.low:
                    color_index = self.high
            else:
                #normal
                color_index = color_index + 1
                if color_index > self.high:
                    color_index = self.low
        return color_index

    def get_range(self):
        if self.flags & 2:
            #reverse
            return range(self.high, self.low-1, -1)
        else:
            #normal
            return range(self.low, self.high+1, 1)

