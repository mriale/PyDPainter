import numpy
import asyncio
import sys, math, os, random, colorsys
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *
import pygame.surfarray

import libs.pixelfont
from libs.pixelfont import PixelFont

from operator import itemgetter

from libs.config import *

if __name__ == "__main__":
    print("init pydpainter")
    config = pydpainter()
    print("config.run()")
    asyncio.run(config.run())
