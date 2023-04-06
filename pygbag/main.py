import numpy
import asyncio
import sys, math, os, random, colorsys
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import pixelfont
from pixelfont import PixelFont

from operator import itemgetter

from config import *

if __name__ == "__main__":
    config = pydpainter()
    asyncio.run(config.run())
