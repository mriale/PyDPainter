#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# PixelFont bitmap font renderer

import sys
import re
import numpy as np
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import libs.gadget as gadget

class PixelFont(object):

    def __init__(self, name, sizeY, sizeX=0):
        scaledown = 1
        if sizeX == 0:
            sizeX = sizeY
        matches = re.findall(r"(\d+)[.][^.]+$", name)
        if len(matches) == 1:
            scaleX = 4 - int(matches[0]) // sizeX
            scaleY = 4 - int(matches[0]) // sizeY
            scaledown = max(int(matches[0]) // sizeX, int(matches[0]) // sizeY)
        self.image = gadget.imgload(name, scaledown=scaledown, scaleX=scaleX, scaleY=scaleY)
        xs,ys = self.image.get_size()
        self.xsize = xs // 32
        self.ysize = ys // 40  #should probably be calculated differently
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
            if ord(c) > 2560 and __debug__: c = "\x7f"
            yo = (ord(c) // 32) * self.ysize
            xo = (ord(c) %  32) * self.xsize

            if bgcolor != None:
                pygame.draw.rect(surface, bgcolor, (destx, desty, self.xsize,self.ysize))

            surface.blit(image_blit, (destx, desty), (xo,yo,self.xsize,self.ysize))  
            destx += self.xsize


def char_range(c1, c2):
    """Generates the characters from `c1` to `c2`, inclusive."""
    for c in range(ord(c1), ord(c2)+1):
        yield chr(c)

ypos = 0
def printrow(screen, font, ypos, string, fgcolor=None, bgcolor=None):
    font.blitstring(screen, (0,ypos), string, fgcolor=fgcolor, bgcolor=bgcolor)
    ypos += font.ysize
    return ypos

def main():

    #Initialize the configuration settings
    pygame.init()
        
    sx,sy = 1280,960
    
    screen = pygame.display.set_mode((sx,sy))

    pygame.display.set_caption('PixelFont Unit Test')

    f = PixelFont("jewel32.png", 8)
    f2 = PixelFont("jewel32.png", 16)
    f4 = PixelFont("jewel32.png", 32)
    running = 1

    yscroll = 0

    if len(sys.argv) == 2:
        with open(sys.argv[1],"r") as textfile:
            displaytext = textfile.read().split("\n") #open text file from command line argument
    else:
        displaytext = ["ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijkmlnopqrstuvwxyz"]
        displaytext += list([''.join(map(chr,range(i*32,(i+1)*32))) for i in range(40)])

    while running:
        screen.fill((0,0,0))
        ypos = -yscroll*8
        yscroll += pygame.key.get_pressed()[K_DOWN] - pygame.key.get_pressed()[K_UP] #arrow keys to scroll

        for font in [f, f2, f4]:
            ypos=printrow(screen, font, ypos, "Jewel "+str(font.ysize), fgcolor=(255,255,0), bgcolor=(255,0,0))
            for textrow in displaytext:
                ypos=printrow(screen, font, ypos, textrow)

        #for event in config.xevent.get():
        for event in pygame.event.get():
            if event.type == QUIT:
                running = 0
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = 0

        pygame.display.flip()        
        pygame.time.delay(10)

if __name__ == '__main__': main()

