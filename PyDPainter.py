#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
PyDPainter.py
Build a usable pixel art paint program in pygame
"""

import sys, math, os, random, colorsys
os.environ['SDL_VIDEO_WINDOW_POS'] = "10,10"

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

sys.path.insert(0, 'libs')

import pixelfont
from pixelfont import PixelFont

from operator import itemgetter

from config import *

if __name__ == "__main__":
    config = pydpainter()
    config.run()
