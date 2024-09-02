#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
displayinfo.py
Implement a class for screen mode lookup
"""

config = None

class ScreenMode:
    """This class handles one screen mode"""
    def __init__(self, mode_id, name, x, y, max_x, max_y, aspect, aspect_x, aspect_y, scaleX, scaleY, scaledown, display, platform):
        self.mode_id = mode_id
        self.name = name
        self.x = x
        self.y = y
        self.max_x = max_x
        self.max_y = max_y
        self.aspect = float(aspect)
        self.aspect_x = aspect_x
        self.aspect_y = aspect_y
        self.scaleX = scaleX
        self.scaleY = scaleY
        self.scaledown = scaledown
        self.display = display
        self.platform = platform

    def get_pixel_mode(self):
        if self.display == "VGA" and self.aspect > .999 and self.aspect < 1.001:
            return "square"
        elif self.display == "VGA":
            return "NTSC"
        else:
            return self.display

    def __str__(self):
        return ("mode_id=%05x, name='%s', %d, %d, %d, %d, %f, '%s', '%s'" % (self.mode_id, self.name, self.x, self.y, self.max_x, self.max_y, self.aspect, self.display, self.platform))

class DisplayInfo:
    """This class handles screen modes"""
    def __init__(self):

        self.db = [
            ScreenMode(0x00011000,"Lo-Res",320,200,360,240,0.909090909090909,1,1,1,1,4,"NTSC","Amiga"),
            ScreenMode(0x00019000,"Med-Res",640,200,720,240,0.454545454545455,2,1,2,1,4,"NTSC","Amiga"),
            ScreenMode(0x00011004,"Interlace",320,400,360,480,1.81818181818182,1,2,1,2,4,"NTSC","Amiga"),
            ScreenMode(0x00019004,"Hi-Res",640,400,720,480,0.909090909090909,1,1,2,2,2,"NTSC","Amiga"),
            ScreenMode(0x00021000,"Lo-Res",320,256,360,288,1.09259259259259,1,1,1,1,4,"PAL","Amiga"),
            ScreenMode(0x00029000,"Med-Res",640,256,720,288,0.546296296296296,2,1,2,1,4,"PAL","Amiga"),
            ScreenMode(0x00021004,"Interlace",320,512,360,576,2.18518518518519,1,2,1,2,4,"PAL","Amiga"),
            ScreenMode(0x00029004,"Hi-Res",640,512,720,576,1.09259259259259,1,1,2,2,2,"PAL","Amiga"),
            ScreenMode(0x00031000,"MCGA",320,200,320,200,0.909090909090909,1,1,1,1,4,"VGA","PC"),
            ScreenMode(0x00039004,"VGA",640,480,640,480,1,1,1,2,2,2,"VGA","PC"),
            ScreenMode(0x00039005,"SVGA",800,600,800,600,1,1,1,2,2,2,"VGA","PC"),
            ScreenMode(0x00039006,"XGA",1024,768,1024,768,1,1,1,4,4,1,"VGA","PC"),
        ]

    def __str__(self):
        s=""
        for sm in self.db:
            s += str(sm) + "\n"
        return s

    def get_id(self, id):
        id &= ~0x80 #ignore Extra-Halfbright
        for sm in self.db:
            if sm.mode_id == id:
                return sm
        return None

    def get_display(self, display):
        l=[]
        for sm in self.db:
            if sm.display == display:
                l.append(sm)
        return l

    def match_resolution(self, x, y):
        for sm in self.db:
            if sm.x == x and sm.y == y:
                return sm
        return None
