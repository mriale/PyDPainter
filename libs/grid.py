#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

"""
grid.py
Implement a class for a visible representation of the snap-to-grid
"""

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import numpy as np

config = None

def grid_set_config(config_in):
    global config
    config = config_in

#Grid overlay styles
GRID_DOTTED = 0
GRID_SOLID = 1

class Grid:
    """This class draws the snap-to-grid as a colored overlay on
    top of the composed canvas. It is not part of the LayerStack,
    so it never ends up in the color picker or in saved images."""
    def __init__(self):
        self.grid_surface = None
        self.cached_params = None

    def __repr__(self):
        return f"<Grid {hex(id(self))}: grid_surface=<{hex(id(self.grid_surface))}> >"

    def invalidate(self):
        """Force the grid overlay to be regenerated on the next draw"""
        self.grid_surface = None
        self.cached_params = None

    def make_grid_surface(self):
        """Generate a canvas-sized surface with the grid pixels drawn
        using the current grid settings"""
        pw, ph = config.pixel_canvas.get_size()
        gsx, gsy = config.grid_size
        gox, goy = config.grid_offset
        gcolor = (config.grid_color[0], config.grid_color[1], config.grid_color[2], config.grid_alpha)

        grid_surface = pygame.Surface((pw, ph), SRCALPHA)

        if gsx > 0 and gsy > 0:
            #draw solid lines - pygame.draw does not blend on an
            #SRCALPHA surface, it writes the RGBA color directly
            for x in range(gox % gsx, pw, gsx):
                pygame.draw.line(grid_surface, gcolor, (x, 0), (x, ph-1), 1)
            for y in range(goy % gsy, ph, gsy):
                pygame.draw.line(grid_surface, gcolor, (0, y), (pw-1, y), 1)

            if config.grid_style == GRID_DOTTED:
                #dotted style - punch out every other pixel of the lines
                alpha_array = pygame.surfarray.pixels_alpha(grid_surface)
                xchecker = np.arange(pw).reshape(-1, 1)
                ychecker = np.arange(ph).reshape(1, -1)
                alpha_array[(xchecker + ychecker) % 2 == 1] = 0
                alpha_array = None

        return grid_surface

    def draw(self, screen, offset=(0,0), rect=None):
        """Draw the grid overlay onto a screen using the same offset
        and rect that the LayerStack was blitted with, so that the
        grid lines line up exactly with the pixels they snap to"""
        if not config.grid_on or not config.grid_visible:
            return
        params = (config.pixel_canvas.get_size(), config.grid_size,
                  config.grid_offset, config.grid_style,
                  tuple(config.grid_color), config.grid_alpha)
        if self.grid_surface == None or params != self.cached_params:
            self.grid_surface = self.make_grid_surface()
            self.cached_params = params
        screen.blit(self.grid_surface, offset, rect)
