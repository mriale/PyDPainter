#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# PixelFont bitmap font renderer

import re
import numpy as np
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import gadget

class PixelFont(object):

    def __init__(self, name, sizeY, sizeX=0):
        scaledown = 1
        if sizeX == 0:
            sizeX = sizeY
        matches = re.findall("(\d+)[.][^.]+$", name)
        if len(matches) == 1:
            scaleX = 4 - int(matches[0]) // sizeX
            scaleY = 4 - int(matches[0]) // sizeY
            scaledown = max(int(matches[0]) // sizeX, int(matches[0]) // sizeY)
        self.image = gadget.imgload(name, scaledown=scaledown, scaleX=scaleX, scaleY=scaleY)
        xs,ys = self.image.get_size()
        self.xsize = xs // 32
        self.ysize = ys // 6
        self.image_color = {}

    def calcwidth(self, string):
        return self.xsize * len(string)

    def blitstring(self, surface, destxy, string, fgcolor=None, bgcolor=None):
        destx, desty = destxy
        if fgcolor != None:
            fgcolori = self.image.map_rgb(fgcolor) & 0xffffffff
            if not fgcolori in self.image_color:
                #convert font bitmap to fgcolor
                image_blit = self.image.copy()
                surf_array = pygame.surfarray.pixels2d(image_blit)
                surf_array[np.not_equal(surf_array, 0)] = fgcolori
                surf_array = None
                self.image_color[fgcolori] = image_blit
            elif fgcolori in self.image_color:
                #use cached font bitmap already set to fgcolor
                image_blit = self.image_color[fgcolori]
        else:
            #no fgcolor set so use original font bitmap
            image_blit = self.image

        for c in string:
            yo = ((ord(c) - 32) // 32) * self.ysize
            xo = ((ord(c) - 32) %  32) * self.xsize

            if bgcolor != None:
                pygame.draw.rect(surface, bgcolor, (destx, desty, self.xsize,self.ysize))

            surface.blit(image_blit, (destx, desty), (xo,yo,self.xsize,self.ysize))  
            destx += self.xsize


def char_range(c1, c2):
    """Generates the characters from `c1` to `c2`, inclusive."""
    for c in range(ord(c1), ord(c2)+1):
        yield chr(c)

def main():

    #Initialize the configuration settings
    pygame.init()
        
    sx,sy = 800,300
    
    screen = pygame.display.set_mode((sx,sy))

    pygame.display.set_caption('PixelFont Unit Test')

    f = PixelFont("jewel32.png", 8)
    f2 = PixelFont("jewel32.png", 16)
    f4 = PixelFont("jewel32.png", 32)
    running = 1

    while running:
        
        screen.fill((0,0,0))
        f.blitstring(screen, (0,0), "Jewel 8", fgcolor=(255,255,0), bgcolor=(255,0,0))
        f.blitstring(screen, (0,8), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", fgcolor=(255,0,0))
        f.blitstring(screen, (0,16), "abcdefghijkmlnopqrstuvwxyz", fgcolor=(0,0,255))
        f.blitstring(screen, (0,24), "0123456789")
        for i in range(0,7):
            f.blitstring(screen, (0,32+(i*8)), char_range(chr(i*32),chr(((i+1)*32)-1)))

        f2.blitstring(screen, (0,100), "Jewel 16", fgcolor=(255,255,0), bgcolor=(255,0,0))
        f2.blitstring(screen, (0,116), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", fgcolor=(255,0,0))
        f2.blitstring(screen, (0,132), "abcdefghijkmlnopqrstuvwxyz", fgcolor=(0,0,255))

        f4.blitstring(screen, (0,160), "Jewel 32", fgcolor=(255,255,0), bgcolor=(255,0,0))
        f4.blitstring(screen, (0,192), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", fgcolor=(0,0,255))
        f4.blitstring(screen, (0,224), "abcdefghijkmlnopqrstuvwxyz", fgcolor=(0,0,255))

        for event in pygame.event.get():
            if event.type == QUIT:
                running = 0
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = 0

        pygame.display.flip()        
        pygame.time.delay(10)

if __name__ == '__main__': main()

