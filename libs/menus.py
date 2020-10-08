#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

from menubar import *
from menureq import *
from gadget import *
from picio import *

from tkinter import *
from tkinter import filedialog

config = None

class MenuAction(Action):
    def toolHide(self):
        if config.toolbar.tool_id(config.tool_selected) != None and \
           config.toolbar.tool_id(config.tool_selected).action != None:
            config.toolbar.tool_id(config.tool_selected).action.hide()

class DoNew(MenuAction):
    def selected(self, attrs):
        screen_format_req(config.pixel_req_canvas,new_clicked=True)

def askOpenFilename():
    pygame.mouse.set_visible(True)
    config.filename = filedialog.asksaveasfilename(initialdir = config.filepath,title = "Save Picture",filetypes = (("IFF file","*.iff"), ("BMP file","*.bmp"),("all files","*.*")))
    pygame.mouse.set_visible(False)

class DoOpen(MenuAction):
    def selected(self, attrs):
        self.toolHide()
        config.recompose()
        pygame.mouse.set_visible(True)
        config.filename = filedialog.askopenfilename(initialdir = config.filepath,title = "Load Picture",filetypes = (("BMP file","*.bmp"),("IFF file","*.iff"),("all files","*.*")))
        pygame.mouse.set_visible(False)
        if config.filename != (()) and config.filename != "":
            try:
                config.pixel_canvas = load_pic(config.filename)
                config.truepal = list(config.pal)
                config.pal = config.unique_palette(config.pal)
                config.initialize_surfaces()
                config.filepath = os.path.dirname(config.filename)
            except:
                pass
        else:
            config.filename = ""

def askSaveFilename():
    pygame.mouse.set_visible(True)
    config.filename = filedialog.asksaveasfilename(initialdir = config.filepath,title = "Save Picture",filetypes = (("IFF file","*.iff"), ("BMP file","*.bmp"),("all files","*.*")))
    pygame.mouse.set_visible(False)

class DoSave(MenuAction):
    def selected(self, attrs):
        self.toolHide()
        config.recompose()
        if config.filename == "":
            askSaveFilename()
        if config.filename != "" and config.filename != (()):
            save_iff(config.filename)
        else:
            config.filename = ""

class DoSaveAs(MenuAction):
    def selected(self, attrs):
        self.toolHide()
        config.recompose()
        askSaveFilename()
        if config.filename != "" and config.filename != (()):
            save_iff(config.filename)
        else:
            config.filename = ""

class DoPalette(MenuAction):
    def selected(self, attrs):
        self.toolHide()
        palette_req(config.pixel_req_canvas)

class DoCycle(MenuAction):
    def selected(self, attrs):
        if config.cycling:
            config.stop_cycling()
        else:
            config.start_cycling()

class DoSpareSwap(MenuAction):
    def selected(self, attrs):
        config.clear_pixel_draw_canvas()
        config.pixel_canvas, config.pixel_spare_canvas = config.pixel_spare_canvas, config.pixel_canvas
        config.clear_undo()
        config.save_undo()

class DoSpareCopy(MenuAction):
    def selected(self, attrs):
        config.clear_pixel_draw_canvas()
        config.pixel_spare_canvas.blit(config.pixel_canvas, (0,0))
        config.clear_undo()
        config.save_undo()

class DoScreenFormat(MenuAction):
    def selected(self, attrs):
        screen_format_req(config.pixel_req_canvas)

class DoBrushFlipX(MenuAction):
    def selected(self, attrs):
        if config.brush.type == Brush.CUSTOM:
            config.brush.image = pygame.transform.flip(config.brush.image, True, False)
            config.brush.image_orig = pygame.transform.flip(config.brush.image_orig, True, False)
            config.brush.handle = [config.brush.rect[2] - config.brush.handle[0], config.brush.handle[1]]
            config.brush.cache = BrushCache()
            config.doKeyAction()

class DoBrushFlipY(MenuAction):
    def selected(self, attrs):
        if config.brush.type == Brush.CUSTOM:
            config.brush.image = pygame.transform.flip(config.brush.image, False, True)
            config.brush.image_orig = pygame.transform.flip(config.brush.image_orig, False, True)
            config.brush.handle = [config.brush.handle[0], config.brush.rect[3] - config.brush.handle[1]]
            config.brush.cache = BrushCache()
            config.doKeyAction()

class DoBrushRotate90(MenuAction):
    def selected(self, attrs):
        if config.brush.type == Brush.CUSTOM:
            config.brush.image = pygame.transform.rotate(config.brush.image, -90)
            config.brush.image_orig = pygame.transform.rotate(config.brush.image_orig, -90)
            config.brush.handle = config.brush.handle[::-1]
            bx,by,bw,bh = config.brush.rect
            config.brush.rect = [by,bx,bh,bw]
            config.brush.cache = BrushCache()
            config.doKeyAction()

class DoMode(MenuAction):
    def selected(self, attrs):
        if not self.gadget.enabled:
            return
        for menug in self.gadget.parent.menug_list:
            menug.checked = False
        self.gadget.checked = True
        config.drawmode.value = DrawMode.LABEL_STR.index(self.gadget.label.lstrip())
        config.menubar.title_extra = self.gadget.label
        config.doKeyAction()


def init_menubar(config_in):
    global config
    config = config_in

    h = config.fonty
    w = config.pixel_canvas.get_width()
    menubar_canvas = pygame.Surface((w,h),0)
    menubar = Menubar(menubar_canvas, (0,0,w,h), config.font)
    menubar.title = "PyDPainter"
    menubar.title_extra = " Color"
    menubar.add_menu(
        ["Picture", [
            ["New...", "ctrl-n", DoNew],
            ["Open...", "ctrl-o", DoOpen],
            ["Save", "ctrl-s", DoSave],
            ["Save as...", "ctrl-S", DoSaveAs],
            ["Print...", "ctrl-p"],
            ["---"],
            ["Flip", [
                ["Horiz"],
                ["Vert"],
                ]],
            ["Change Color", [
                ["Palette...", "p", DoPalette],
                ["Use Brush Palette"],
                ["Restore Palette"],
                ["Default Palette"],
                ["Cycle","Tab", DoCycle],
                ["BG -> FG"],
                ["BG <-> FG"],
                ["Remap"],
                ]],
            ["Spare", [
                ["Swap", "j", DoSpareSwap],
                ["Copy To Spare", "J", DoSpareCopy],
                ["Merge in front"],
                ["Merge in back"],
                ["Delete this page"],
                ]],
            ["Page Size..."],
            ["Show Page", "S"],
            ["Screen Format...", " ", DoScreenFormat],
            ["About..."],
            ["Quit", "Q"],
        ]])
    menubar.add_menu(
        ["Brush", [
            ["Open..."],
            ["Save as..."],
            ["Restore","B"],
            ["Size", [
                ["Stretch", "Z"],
                ["Halve", "h"],
                ["Double", "H"],
                ["Double Horiz"],
                ["Double Vert"],
                ]],
            ["Flip", [
                ["Horiz", "x", DoBrushFlipX],
                ["Vert", "y", DoBrushFlipY],
                ]],
            ["Edge", [
                ["Outline"],
                ["Trim"],
                ]],
            ["Rotate", [
                ["90 Degrees", "z", DoBrushRotate90],
                ["Any Angle"],
                ["Shear"],
                ]],
            ["Change Color", [
                ["BG -> FG"],
                ["BG <-> FG"],
                ["Remap"],
                ["Change Transp"],
                ]],
            ["Bend", [
                ["Horiz"],
                ["Vert"],
                ]],
            ["Handle", [
                ["Center","alt-s"],
                ["Corner","alt-x"],
                ["Place","alt-z"],
                ]],
        ]])
    menubar.add_menu(
        ["Mode", [
            ["!/Matte", "F1", DoMode],
            ["\\Color", "F2", DoMode],
            ["!/Repl", "F3", DoMode],
            ["/Smear", "F4", DoMode],
            ["/Shade", "F5", DoMode],
            ["/Blend", "F6", DoMode],
            ["/Cycle", "F7", DoMode],
            ["/Smooth","F8", DoMode],
            ["/Tint"],
            ["!/HBrite"],
        ]])

    menubar.add_menu(
        ["Anim", [
            ["!Open..."],
            ["!Save..."],
            ["!Move..."],
            ["!Frames"],
            ["!Control"],
            ["!Anim Brush"],
        ]])

    menubar.add_menu(
        ["Effect", [
            ["!Stencil"],
            ["!Background"],
            ["!Perspective"],
        ]])

    menubar.add_menu(
        ["Prefs", [
            ["Coords", "|"],
            ["AutoTransp"],
        ]])

    return menubar
