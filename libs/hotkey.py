#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import re

class HotKeyMap:
    def __init__(self):
        self.hotkey_map = {}

    def add(self, hotkey):
        if hotkey.unicode != "":
            self.hotkey_map[hotkey.unicode] = hotkey
        elif hotkey.key != 0:
            self.hotkey_map[(hotkey.mod,hotkey.key)] = hotkey

    def press(self, event):
        if event.type == KEYDOWN:
            mod = 0
            if event.mod & KMOD_SHIFT:
                mod |= KMOD_SHIFT
            if event.mod & KMOD_CTRL:
                mod |= KMOD_CTRL
            if event.mod & KMOD_ALT:
                mod |= KMOD_ALT
            if event.mod & KMOD_META:
                mod |= KMOD_ALT

            if event.unicode in self.hotkey_map:
                hotkey = self.hotkey_map[event.unicode]
                if hotkey.action != None:
                    hotkey.action.selected(hotkey.attrs)
            elif (mod,event.key) in self.hotkey_map:
                hotkey = self.hotkey_map[(mod, event.key)]
                if hotkey.action != None:
                    hotkey.action.selected(hotkey.attrs)

    def __repr__(self):
        str = ""
        for k in self.hotkey_map:
            str += repr(k) + ": " + repr(self.hotkey_map[k]) + "\n"
        return str

class HotKey:
    keymap = {
        "backspace": K_BACKSPACE,
        "bksp": K_BACKSPACE,
        "tab": K_TAB,
        "return": K_RETURN,
        "escape": K_ESCAPE,
        "esc": K_ESCAPE,
        "delete": K_DELETE,
        "del": K_DELETE,
        "insert": K_INSERT,
        "ins": K_INSERT,
        "home": K_HOME,
        "end": K_END,
        "page up": K_PAGEUP,
        "pgup": K_PAGEUP,
        "page down": K_PAGEDOWN,
        "pgdn": K_PAGEDOWN,
        "0": K_0,
        "1": K_1,
        "2": K_2,
        "3": K_3,
        "4": K_4,
        "5": K_5,
        "6": K_6,
        "7": K_7,
        "8": K_8,
        "9": K_9,
        "f1": K_F1,
        "f2": K_F2,
        "f3": K_F3,
        "f4": K_F4,
        "f5": K_F5,
        "f6": K_F6,
        "f7": K_F7,
        "f8": K_F8,
        "f9": K_F9,
        "f10": K_F10,
        "f11": K_F11,
        "f12": K_F12,
    }
    for i in range(ord("a"), ord("z")+1):
        keymap[chr(i)] = i

    def __init__(self, text=None, action=None, mod=0, key=0, unicode="", id=None, gadget=None, attrs=None):
        hotkeys = text
        self.mod = mod
        self.key = key
        self.unicode = unicode
        if action == None:
            self.action = None
        else:
            self.action = action(id, gadget)
        self.attrs = attrs
        if text != None:
            if re.search("(?i)ctrl-", hotkeys):
                hotkeys = re.sub("(?i)ctrl-", "", hotkeys)
                self.mod |= KMOD_CTRL
            if re.search("(?i)alt-", hotkeys):
                hotkeys = re.sub("(?i)alt-", "", hotkeys)
                self.mod |= KMOD_ALT
            if re.search("(?i)shift-", hotkeys):
                hotkeys = re.sub("(?i)shift-", "", hotkeys)
                self.mod |= KMOD_SHIFT
            if len(hotkeys) == 1 and hotkeys[0] >= "A" and hotkeys[0] <= "Z":
                self.mod |= KMOD_SHIFT
            hotkeys = hotkeys.lower()
            if (hotkeys in HotKey.keymap):
                self.key = HotKey.keymap[hotkeys]
            else:
                self.unicode = hotkeys

    def toKeycaps(self):
        if self.unicode == "":
            c = pygame.key.name(self.key)
            if len(c) > 1:
                c = c.upper()
            s = ""
            if self.mod & KMOD_SHIFT:
                s += "\x84\x85"
                c = c.upper()
            if self.mod & KMOD_CTRL:
                s += "\x80\x81"
            if self.mod & KMOD_ALT:
                s += "\x82\x83"
            return s+c
        else:
            return self.unicode

    def __repr__(self):
        return "mod=%d key=%d unicode=\"%s\"" % (self.mod, self.key, self.unicode)

    def __str__(self):
        if self.unicode == "":
            s = ""
            if self.mod & KMOD_CTRL:
                s += "ctrl-"
            if self.mod & KMOD_ALT:
                s += "alt-"
            if self.mod & KMOD_SHIFT:
                s += "shift-"
            return s+pygame.key.name(self.key)
        else:
            return self.unicode

def testHotKey(str):
    h1 = HotKey(text=str)
    print(h1)
 
def testHotKeyMap(hotkeymap, str):
    hotkeymap.add(HotKey(text=str))

def main():
    pygame.init()
    testHotKey("TAB")
    testHotKey("SHIFT-TAB")
    testHotKey("F10")
    testHotKey("A")
    testHotKey("a")
    testHotKey("ctrl-shift-O")
    testHotKey("ctrl-shift-o")
    testHotKey("ctrl-o")
    testHotKey("ctrl-O")
    testHotKey("<")
    testHotKey("0")
    testHotKey("shift-0")

    print("")
    hotkeymap = HotKeyMap()
    hotkeymap.add(HotKey(text="tab"))
    hotkeymap.add(HotKey(text="shift-tab"))
    hotkeymap.add(HotKey(text="<"))
    hotkeymap.add(HotKey(text="shift-0"))
    print(hotkeymap)

if __name__ == '__main__': main()

