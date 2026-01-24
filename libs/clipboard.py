#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import sys
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

try:
    import xerox  # NOTE use https://github.com/clach04/xerox/  -- python -m pip install git+https://github.com/clach04/xerox.git
except ImportError:
    xerox = None

is_win = sys.platform.startswith('win')
is_android = "getandroidapilevel" in dir(sys)
is_pygamece = getattr(pygame, "IS_CE", False)

def clipboard_init():
    if is_android:
        return
    if not is_pygamece and "scrap" in dir(pygame) and "init" in dir(pygame.scrap):
        # pygame
        pygame.scrap.init()
        pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)

def clipboard_get_text():
    if xerox:
        clipboard_text = xerox.paste()
    elif is_pygamece:
        # pygame-ce
        clipboard_text = pygame.scrap.get_text()
    else:
        # pygame
        for t in pygame.scrap.get_types():
            if "text/plain" in t and pygame.scrap.get(t) != None:  # probably; 'text/plain;charset=utf-8'
                if is_win:
                    clipboard_text = pygame.scrap.get(t).decode("utf-16-le", "ignore")  # under windows its utf16-le! and null terminated
                else:
                    clipboard_text = pygame.scrap.get(t).decode("utf-8", "ignore")
                break
        if clipboard_text:
            if clipboard_text.endswith('\x00'):
                clipboard_text = clipboard_text[:-1]

    return clipboard_text


