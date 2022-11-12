#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

from toolbar import *
from toolreq import *
from gadget import *
from tiptext import *

config = None

class MiniToolAction(Action):
    def get_tip(self):
        if self.gadget.id in tiptext:
            return tiptext[self.gadget.id]
        else:
            return [self.gadget.id]

class DoExpand(MiniToolAction):
    """
    Expand and collapse mini toolbar
    """
    pass

class DoHelp(MiniToolAction):
    """
    Toggle help popups
    """
    def selected(self, attrs):
        config.help_on = True
    def deselected(self, attrs):
        config.help_on = False

class DoScale(MiniToolAction):
    """
    Resize window to scale up or down
    """
    def selected(self, attrs):
        if attrs["subtool"]:
            config.scale_dec()
        else:
            config.scale_inc()
        self.gadget.state = 0
        config.resize_display()

class DoScanlines(MiniToolAction):
    """
    Toggle scanline mode
    """
    def selected(self, attrs):
        config.scanlines = False
    def deselected(self, attrs):
        config.scanlines = True

class DoAspect(MiniToolAction):
    """
    Change NTSC/PAL aspect ratio
    """
    def selected(self, attrs):
        if config.display_mode & config.PAL_MONITOR_ID == config.PAL_MONITOR_ID:
            self.gadget.state = 2
            self.gadget.need_redraw = True
        config.set_aspect(self.gadget.state)
        config.resize_display()
    def deselected(self, attrs):
        config.set_aspect(self.gadget.state)
        config.resize_display()

def init_minitoolbar(config_in):
    global config
    config = config_in

    pmode = {}
    pmode["square"] = 0
    pmode["NTSC"] = 1
    pmode["PAL"] = 2

    scaleX = config.fontx // 8
    scaleY = config.fonty // 12
    scaledown = 4 // min(scaleX,scaleY)
    minitools_image = imgload('minitools.png', scaleX=scaleX, scaleY=scaleY, scaledown=scaledown)
    numtools=5
    numsubtools=3
    h = minitools_image.get_height()//numsubtools
    w = minitools_image.get_width()
    minitoolbar_canvas = pygame.Surface((w,h),0)

    minitoolbar = Toolbar(minitoolbar_canvas, config.cursor, (0,0,w,h), minitools_image, height=numsubtools)
    minitoolbar.add_grid((0,0,w,10*scaleY), numtools, 1, attr_list=[
        ["expand",    ToolGadget.TT_TOGGLE, "", DoExpand],
        ["help",      ToolGadget.TT_TOGGLE, "", DoHelp],
        ["scale",     ToolGadget.TT_SINGLE, "", DoScale],
        ["scanlines", ToolGadget.TT_TOGGLE, "", DoScanlines],
        ["aspect",    ToolGadget.TT_TOGGLE, "", DoAspect]
    ])

    minitoolbar.tool_id("help").state = 1 if config.help_on else 0
    minitoolbar.tool_id("scale").has_subtool = True
    minitoolbar.tool_id("scanlines").state = 0 if config.scanlines else 1
    minitoolbar.tool_id("aspect").state = pmode[config.pixel_mode]

    return minitoolbar


