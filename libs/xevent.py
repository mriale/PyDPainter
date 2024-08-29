#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#gadget.py
"""
xevent.py
Library for extending pygame events
"""

import pygame
from pygame.locals import *

config = None

def xevent_set_config(config_in):
    global config
    config = config_in

class Xevent(object):
    MOD_KEYS = [K_NUMLOCK, K_CAPSLOCK, K_SCROLLOCK, K_RSHIFT, K_LSHIFT,
                K_RCTRL, K_LCTRL, K_RALT, K_LALT, K_RMETA, K_LMETA,
                K_LSUPER, K_RSUPER,
               ]

    def __init__(self):
        self.last_key = None
        self.xq = []
        self.keys_down = []

    def dedup_new(self, new_xevents):
        for e in list(new_xevents):
            if e.type == KEYDOWN:
                if not e.key in self.keys_down:
                    self.keys_down.append(e.key)
                if e.key == self.last_key and e.key in self.MOD_KEYS:
                    new_xevents.remove(e)
                    continue
                self.last_key = e.key
            elif e.type == KEYUP:
                if e.key in self.keys_down:
                    self.keys_down.remove(e.key)
                self.last_key = None
        return new_xevents

    def pump(self):
        new_xevents = pygame.event.get()
        self.xq.extend(self.dedup_new(new_xevents))

    def custom_type(self):
        return pygame.event.custom_type()

    def get(self):
        self.pump()
        xevents = self.xq
        self.xq = list()
        return xevents

    def peek(self, types=None):
        self.pump()
        for e in self.xq:
            if types is None:
                return True
            elif isinstance(types, list) and e.type in types:
                return True
            elif isinstance(types, tuple) and e.type in types:
                return True
            elif isinstance(types, int) and e.type == types:
                return True
        return False

    def poll(self):
        self.pump()
        xevent = lambda: None
        xevent.type = pygame.NOEVENT
        if len(self.xq) > 0:
            xevent = self.xq.pop(0)
        return xevent

    def wait(self):
        xevent = lambda: None
        xevent.type = pygame.NOEVENT
        while xevent.type == pygame.NOEVENT:
            self.pump()
            if len(self.xq) > 0:
                xevent = self.xq.pop(0)
            else:
                self.xq.extend(self.dedup_new([pygame.event.wait()]))
        return xevent
