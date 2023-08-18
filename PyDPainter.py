#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
PyDPainter.py
Build a usable pixel art paint program in pygame
"""

import sys, math, os, random, colorsys

try:
    import contextlib
    with contextlib.redirect_stdout(None):
        import pygame
        from pygame.locals import *

    import numpy
except:
    import tkinter as tk
    root = tk.Tk()
    root.title("PyDPainter Error")

    #Put out a useful message if pygame is not installed
    message = tk.Label(root, text="""
Some required Python modules are not installed:
- pygame
- numpy

For Windows, run 'install_pygame.bat'

For Linux and other systems, see 'installing.txt'

After the modules are successfully installed, re-run PyDPainter.
""")
    message.pack()

    # keep the window displaying
    root.mainloop()
    exit(1)

######################################################

os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"
os.environ["SDL_MOUSE_RELATIVE"] = "0"
os.chdir(os.path.realpath(os.path.dirname(__file__)))

import libs.pixelfont
from libs.pixelfont import PixelFont

from operator import itemgetter

from libs.config import *

if __name__ == "__main__":
    config = pydpainter()
    config.run()
