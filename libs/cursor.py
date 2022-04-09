#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
cursor.py
Implement a cursor sprite on the screen
"""
import os.path

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

class cursor:
    """This class renders the mouse pointer, which acts as a sprite"""
    CROSS=0
    NORMAL=1
    FILL=2
    DROPPER=3
    RESIZE=4
    ROTATE=5
    LEFT_RIGHT=6
    UP_DOWN=7
    BUSY=8
    def __init__(self, screen, scaleX, scaleY, config, cursor_images):
        self.shape = 0
        self.visible = True
        self.screen = screen
        self.scaleX = scaleX
        self.scaleY = scaleY
        self.config = config
        self.cursor_images = cursor_images
        self.cursor_images = pygame.transform.scale(self.cursor_images, (self.cursor_images.get_width() * scaleX, self.cursor_images.get_height() * scaleY))
        self.center = []
        self.center.append((7,7))
        self.center.append((1,1))
        self.center.append((7,15))
        self.center.append((0,15))
        self.center.append((7,7))
        self.center.append((9,9))
        self.center.append((9,9))
        self.center.append((9,9))
        self.center.append((7,11))

    def draw(self):
        #draw mouse cursor
        if not pygame.mouse.get_focused():
            return

        if not self.visible and self.shape != 1:
            return

        mouseX, mouseY = self.config.get_mouse_pointer_pos()
        centerX, centerY = self.center[self.shape]
        self.screen.blit(self.cursor_images, (mouseX-(centerX*self.scaleX), (mouseY-(centerY*self.scaleY//2))*2), (16*self.shape*self.scaleX,0,16*self.scaleX,self.cursor_images.get_height()))

