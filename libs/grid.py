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

def grid_row_offset(row, size_x):
    """X offset of a row in an isometric grid."""
    return (row % 2) * (size_x // 2)

def grid_snap_point(x, y):
    """Snap a canvas coordinate to the nearest grid point."""
    gsx, gsy = config.grid_size
    gox, goy = config.grid_offset
    if gsx <= 0 or gsy <= 0:
        return (x, y)

    row = (y - goy + gsy // 2) // gsy
    xoff = grid_row_offset(row, gsx) if config.grid_iso else 0
    sx = (x - gox - xoff + gsx // 2) // gsx * gsx + gox + xoff
    return (sx, row * gsy + goy)

def grid_iso_segments(origin, size, cols, rows, start_row=0):
    """Yield the diagonal segments of an isometric diamond grid.

    origin is the x coordinate of column 0 and the y coordinate of
    start_row. Each row is staggered by half a cell in alternating
    directions, and its points are joined to the next row.
    """
    ox, oy = origin
    gsx, gsy = size
    for row in range(start_row, start_row + rows):
        y0 = oy + (row - start_row) * gsy
        y1 = y0 + gsy
        off0 = grid_row_offset(row, gsx)
        delta = grid_row_offset(row + 1, gsx) - off0
        #the other nearest point below is one cell to the left or
        #right, depending on which way this row is staggered
        delta_other = delta - gsx if delta >= 0 else delta + gsx
        for col in range(cols):
            x = ox + off0 + col * gsx
            yield ((x, y0), (x + delta, y1))
            yield ((x, y0), (x + delta_other, y1))

def draw_grid_segment(surface, color, p0, p1, dotted):
    """Draw one grid segment, optionally as alternating pixels."""
    if not dotted:
        pygame.draw.line(surface, color, p0, p1, 1)
        return

    x, y = p0
    x1, y1 = p1
    dx = abs(x1 - x)
    dy = abs(y1 - y)
    sx = 1 if x < x1 else -1
    sy = 1 if y < y1 else -1
    err = dx - dy
    width, height = surface.get_size()
    #dotted lines need a mask that alternates along the diagonal;
    #using the coordinate with the larger span keeps 2:1 grids dotted
    use_x = dx >= dy
    while True:
        if ((x if use_x else y) % 2 == 0) and \
           0 <= x < width and 0 <= y < height:
            surface.set_at((x, y), color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

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
            dotted = config.grid_style == GRID_DOTTED

            if config.grid_iso:
                #diamond grid - join each staggered grid point to the
                #two points below it. Extend past the canvas edges so
                #the diagonals reaching into view are drawn as well.
                row0 = (0 - goy) // gsy - 1
                row1 = (ph - goy) // gsy + 1
                col0 = -2
                col1 = pw // gsx + 2
                segments = grid_iso_segments(
                    (gox + col0 * gsx, goy + row0 * gsy), (gsx, gsy),
                    col1 - col0, row1 - row0 + 1, start_row=row0)
                for p0, p1 in segments:
                    draw_grid_segment(grid_surface, gcolor, p0, p1, dotted)
            else:
                #draw solid lines - pygame.draw does not blend on an
                #SRCALPHA surface, it writes the RGBA color directly
                for x in range(gox % gsx, pw, gsx):
                    pygame.draw.line(grid_surface, gcolor, (x, 0), (x, ph-1), 1)
                for y in range(goy % gsy, ph, gsy):
                    pygame.draw.line(grid_surface, gcolor, (0, y), (pw-1, y), 1)

                if dotted:
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
        if not config.grid_visible:
            return
        params = (config.pixel_canvas.get_size(), config.grid_size,
                  config.grid_offset, config.grid_style, config.grid_iso,
                  tuple(config.grid_color), config.grid_alpha)
        if self.grid_surface == None or params != self.cached_params:
            self.grid_surface = self.make_grid_surface()
            self.cached_params = params
        screen.blit(self.grid_surface, offset, rect)
