#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os.path, colorsys

import gadget
from gadget import *

from prim import *

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

config = None

def toolreq_set_config(config_in):
    global config
    config = config_in


class FontList(Gadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        if label == "^":
            scaleX = config.pixel_width // 320
            scaleY = config.pixel_height // 200
            scaledown = 4 // min(scaleX,scaleY)
            self.crng_arrows = imgload('crng_arrows.png', scaleX=scaleX, scaleY=scaleY, scaledown=scaledown)
            value = 0
        elif label == "#":
            self.items = pygame.font.get_fonts()
            self.items.sort()
            self.top_item = 0
        super(FontList, self).__init__(type, label, rect, value, maxvalue, id)

    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo
        self.screenrect = (x+xo,y+yo,w,h)
        px = font.xsize//8
        py = font.ysize//8

        if self.type == Gadget.TYPE_CUSTOM:
            if not self.need_redraw:
                return

            self.need_redraw = False
            #List text
            if self.label == "#":
                screen.set_clip(self.screenrect)
                for i in range(self.top_item, min(len(self.items), self.top_item+(h//font.ysize))):
                    fg = fgcolor
                    bg = bgcolor
                    if i == self.value: #highlight current
                        fg = bgcolor
                        bg = fgcolor
                    font.blitstring(screen, (x+xo+2*px,y+yo+2*py+(i-self.top_item)*font.ysize), self.items[i], fg, bg)
                pygame.draw.rect(screen, fgcolor, (x+xo,y+yo,w,h), 1)
                screen.set_clip(None)
            #List up/down arrows
            elif self.label == "^":
                pygame.draw.rect(screen, bgcolor, self.screenrect, 0)
                if self.state == 0:
                    pygame.draw.rect(screen, fgcolor, (x+xo+1,y+yo,w-1,h), 1)
                    pygame.draw.line(screen, hcolor, (x+xo+1,y+yo), (x+xo+w-2,y+yo))
                    pygame.draw.line(screen, hcolor, (x+xo+1,y+yo), (x+xo+1,y+yo+h-1))
                else:
                    pygame.draw.rect(screen, hcolor, (x+xo+1,y+yo,w-1,h), 1)
                    pygame.draw.line(screen, fgcolor, (x+xo+1,y+yo), (x+xo+w-2,y+yo))
                    pygame.draw.line(screen, fgcolor, (x+xo+1,y+yo), (x+xo+1,y+yo+h-1))

                ah = self.crng_arrows.get_height()
                aw = self.crng_arrows.get_width() // 4

                if self.value == 1:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (aw*0,0,aw,ah))
                elif self.value == -1:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (aw*1,0,aw,ah))
                elif self.value == -2:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (aw*2,0,aw,ah))
                elif self.value == 2:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (aw*3,0,aw,ah))
            #List slider
            elif self.label == "@":
                sh = max((h-2*py) // self.maxvalue, font.ysize//2)
                so = (h-2*py) * self.value // self.maxvalue
                pygame.draw.rect(screen, fgcolor, (x+xo+px,y+yo,w-px,h), 0)
                pygame.draw.rect(screen, bgcolor, (x+xo+3*px,y+yo+py+so,w-5*px,sh), 0)
            #Font preview
            elif self.label == "%":
                pygame.draw.rect(screen, fgcolor, (x+xo,y+yo,w,h), 0)
        else:
            super(FontList, self).draw(screen, font, offset)

def font_req(screen):
    req = str2req("Choose Font", """
#################^^ [System]
#################@@ [AmigaFont]
#################@@ Size:____
#################@@ Style:
#################@@ [Bold]
#################@@ [Italic]
#################^^ [Underline]
Preview
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
[Cancel][OK]
""", "%#^@", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=FontList, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    #list items
    list_itemsg = req.gadget_id("0_0")
    list_itemsg.top_item = 30
    list_itemsg.value = 35

    #list up/down arrows
    list_upg = req.gadget_id("17_0")
    list_upg.value = -1
    list_downg = req.gadget_id("17_6")
    list_downg.value = 1

    #list slider
    list_sliderg = req.gadget_id("17_1")
    list_sliderg.value = 30
    list_sliderg.maxvalue = len(list_itemsg.items)

    #font type
    system_fontg = req.gadget_id("20_0")
    system_fontg.state = 1
    amiga_fontg = req.gadget_id("20_1")
    amiga_fontg.enabled = False

    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = pygame.event.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0

        system_fontg.state = 1
        if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return


def place_point(symm_center):
    point_coords = (0,0)
    pixel_req_rect_bak = config.pixel_req_rect
    config.pixel_req_rect = None
    config.recompose()
    point_placed = False
    first_time = True
    while not point_placed:
        event = pygame.event.poll()
        while event.type == pygame.MOUSEMOTION and pygame.event.peek((MOUSEMOTION)):
            #get rid of extra mouse movements
            event = pygame.event.poll()

        if event.type == pygame.NOEVENT and not first_time:
            event = pygame.event.wait()

        mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
        if event.type == MOUSEMOTION:
            pass
        elif event.type == MOUSEBUTTONUP:
            point_coords = (mouseX, mouseY)
            point_placed = True
        config.clear_pixel_draw_canvas()
        #old center
        scx,scy = symm_center
        ph = config.pixel_canvas.get_height()
        pw = config.pixel_canvas.get_width()
        drawline(config.pixel_canvas, 1,
            (scx,scy-(ph//10)), (scx,scy+(ph//10)),
            xormode=True)
        drawline(config.pixel_canvas, 1,
            (scx-int(ph/(10*config.pixel_aspect)),scy), (scx+int(ph/(10*config.pixel_aspect)),scy),
            xormode=True)
        #current center
        drawline(config.pixel_canvas, 1,
            (mouseX,0), (mouseX,config.pixel_canvas.get_height()),
            xormode=True)
        drawline(config.pixel_canvas, 1,
            (0,mouseY), (config.pixel_canvas.get_width(),mouseY),
            xormode=True)
        config.recompose()
        first_time = False

    config.pixel_req_rect = pixel_req_rect_bak
    config.clear_pixel_draw_canvas()
    config.recompose()

    return point_coords

def place_grid(gcoords):
    n = 4
    w = gcoords[2]
    ow = w
    h = gcoords[3]
    oh = h
    point_coords = (0,0)
    mpoint_coords = point_coords
    pixel_req_rect_bak = config.pixel_req_rect
    config.pixel_req_rect = None
    config.recompose()
    dragging = False
    point_placed = False
    first_time = True
    while not point_placed:
        event = pygame.event.poll()
        while event.type == pygame.MOUSEMOTION and pygame.event.peek((MOUSEMOTION)):
            #get rid of extra mouse movements
            event = pygame.event.poll()

        if event.type == pygame.NOEVENT and not first_time:
            event = pygame.event.wait()

        mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
        if not dragging:
            point_coords = (mouseX-(n*w), mouseY-(n*h))
            mpoint_coords = (mouseX, mouseY)
        if event.type == MOUSEMOTION:
            if dragging:
                diffX = mouseX - mpoint_coords[0]
                diffY = mouseY - mpoint_coords[1]
                h = oh + (diffY // n)
                if h == 0:
                    h = 1
                w = ow + (diffX // n)
                if w == 0:
                    w = 1
        elif event.type == MOUSEBUTTONDOWN:
            dragging = True
        elif event.type == MOUSEBUTTONUP:
            point_placed = True
        config.clear_pixel_draw_canvas()

        pcx,pcy = point_coords
        for x in range(0,n+1):
            drawline(config.pixel_canvas, 1,
                (pcx+(x*w),pcy), (pcx+(x*w),pcy+(n*h)),
                xormode=True)
        for y in range(0,n+1):
            drawline(config.pixel_canvas, 1,
                (pcx+(n*w),pcy+(y*h)), (pcx,pcy+(y*h)),
                xormode=True)

        config.menutitle_extra = str(pcx) + ", " + str(pcy) + ", " + str(w) + ", " + str(h)
        config.recompose()
        first_time = False

    config.menutitle_extra = ""
    config.pixel_req_rect = pixel_req_rect_bak
    config.clear_pixel_draw_canvas()
    config.recompose()

    w = int(abs(w))
    h = int(abs(h))
    return (point_coords[0]%w, point_coords[1]%h, w, h)

def grid_req(screen):
    req = str2req("Grid", """
          X     Y
Size:   _____ _____
Offset: _____ _____
[Visual]
[Cancel][OK]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    sizeXg = req.gadget_id("8_1")
    sizeYg = req.gadget_id("14_1")
    offsetXg = req.gadget_id("8_2")
    offsetYg = req.gadget_id("14_2")
    visualg = req.gadget_id("0_3")

    sizeXg.value = str(config.grid_size[0])
    sizeXg.numonly = True
    sizeYg.value = str(config.grid_size[1])
    sizeYg.numonly = True
    offsetXg.value = str(config.grid_offset[0])
    offsetXg.numonly = True
    offsetYg.value = str(config.grid_offset[1])
    offsetYg.numonly = True

    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = pygame.event.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.grid_size = (int(sizeXg.value), int(sizeYg.value))
                    config.grid_offset = (int(offsetXg.value)%int(sizeXg.value), int(offsetYg.value)%int(sizeYg.value))
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0 
                elif ge.gadget == visualg and not req.has_error():
                    gcoords = place_grid((int(offsetXg.value)%int(sizeXg.value), int(offsetYg.value)%int(sizeYg.value), int(sizeXg.value), int(sizeYg.value)))
                    offsetXg.value = str(gcoords[0])
                    offsetXg.need_redraw = True
                    offsetYg.value = str(gcoords[1])
                    offsetYg.need_redraw = True
                    sizeXg.value = str(gcoords[2])
                    sizeXg.need_redraw = True
                    sizeYg.value = str(gcoords[3])
                    sizeYg.need_redraw = True
                    req.draw(screen)

        if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return

def symmetry_tile_req(screen):
    req = str2req("Symmetry", """
[Point ][ Tile ]

Width:   ____
Height:  ____
[Cancel][OK]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    pointg = req.gadget_id("0_0")
    tileg = req.gadget_id("8_0")

    cyclicg = req.gadget_id("0_1")
    mirrorg = req.gadget_id("8_1")

    widthl = req.gadget_id("0_2")
    widthg = req.gadget_id("9_2")

    heightl = req.gadget_id("0_3")
    heightg = req.gadget_id("9_3")

    widthg.value = str(config.symm_width)
    widthg.numonly = True
    heightg.value = str(config.symm_height)
    heightg.numonly = True
    tileg.state = 1
    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = pygame.event.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.symm_mode = 1
                    config.symm_width = int(widthg.value)
                    config.symm_height = int(heightg.value)
                    running = 0 
                elif ge.gadget.label == "Cancel":
                    running = 0 
                elif ge.gadget == pointg:
                    return 0

        tileg.state = 1
        if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()
    return -1

def symmetry_point_req(screen):
    req = str2req("Symmetry", """
[Point ][ Tile ]
[Cyclic][Mirror]
Order:   ___
        [Place ]
[Cancel][OK]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    pointg = req.gadget_id("0_0")
    tileg = req.gadget_id("8_0")

    cyclicg = req.gadget_id("0_1")
    mirrorg = req.gadget_id("8_1")

    orderl = req.gadget_id("0_2")
    orderg = req.gadget_id("9_2")

    placeg = req.gadget_id("8_3")

    orderg.value = str(config.symm_num)
    orderg.numonly = True
    pointg.state = 1

    if config.symm_type == 0:
        cyclicg.state = 1
    elif config.symm_type == 1:
        mirrorg.state = 1

    symm_center = config.symm_center

    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = pygame.event.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.symm_mode = 0
                    config.symm_num = int(orderg.value)
                    config.symm_center = symm_center
                    running = 0 
                elif ge.gadget.label == "Cancel":
                    running = 0 
                elif ge.gadget == tileg:
                    return 1
                elif ge.gadget == cyclicg:
                    config.symm_type = 0
                elif ge.gadget == mirrorg:
                    config.symm_type = 1
                elif ge.gadget == placeg:
                    symm_center = place_point(symm_center)

        pointg.state = 1

        if config.symm_type == 0:
            cyclicg.state = 1
        elif config.symm_type == 1:
            mirrorg.state = 1

        if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()
    return -1


def symmetry_req(screen):
    symm_mode = config.symm_mode

    while symm_mode >= 0:
        if symm_mode == 0:
            symm_mode = symmetry_point_req(screen)
        elif symm_mode == 1:
            symm_mode = symmetry_tile_req(screen)

    config.pixel_req_rect = None

def spacing_req(screen):
    req = str2req("Spacing", """
[N Total]      ____
[Every Nth dot]____
[Airbrush]     ____
[Continuous]
[Cancel][OK]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    n_totalg = req.gadget_id("0_0")
    n_total_valueg = req.gadget_id("15_0")
    n_total_valueg.numonly = True
    n_total_valueg.value = str(config.primprops.drawmode.n_total_value)

    every_ng = req.gadget_id("0_1")
    every_n_valueg = req.gadget_id("15_1")
    every_n_valueg.numonly = True
    every_n_valueg.value = str(config.primprops.drawmode.every_n_value)

    airbrushg = req.gadget_id("0_2")
    airbrush_valueg = req.gadget_id("15_2")
    airbrush_valueg.numonly = True
    airbrush_valueg.value = str(config.primprops.drawmode.airbrush_value)

    continuousg = req.gadget_id("0_3")

    spacing = config.primprops.drawmode.spacing
    button_list = [continuousg, n_totalg, every_ng, airbrushg]
    button_list[spacing].state = 1

    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = pygame.event.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        button_list[spacing].state = 1

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.primprops.drawmode.spacing = spacing
                    config.primprops.drawmode.n_total_value = int(n_total_valueg.value)
                    config.primprops.drawmode.every_n_value = int(every_n_valueg.value)
                    config.primprops.drawmode.airbrush_value = int(airbrush_valueg.value)
                    if config.primprops.drawmode.n_total_value < 2:
                        config.primprops.drawmode.n_total_value = 2
                    if config.primprops.drawmode.every_n_value < 1:
                        config.primprops.drawmode.every_n_value = 1
                    if config.primprops.drawmode.airbrush_value < 1:
                        config.primprops.drawmode.airbrush_value = 1
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0 
                elif ge.gadget in button_list:
                    button_list[spacing].state = 0
                    button_list[spacing].needs_redraw = True
                    spacing = button_list.index(ge.gadget)
                    ge.gadget.state = 1
                    ge.gadget.needs_redraw = True

        if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return


class FillGadget(Gadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        super(FillGadget, self).__init__(type, label, rect, value, maxvalue, id)

    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo
        self.screenrect = (x+xo,y+yo,w,h)
        if self.maxvalue == None:
            current_range = 1
        else:
            current_range = self.maxvalue

        if self.type == Gadget.TYPE_CUSTOM:
            if not self.need_redraw:
                return

            self.need_redraw = False
            if self.label == "#":
                if self.value != None:
                    primprops = copy.copy(config.primprops)
                    primprops.fillmode = copy.copy(config.primprops.fillmode)
                    primprops.fillmode.gradient_dither = self.value
                    primprops.fillmode.value = self.fillmode_value
                    primprops.fillmode.predraw = False
                    primprops.handlesymm = False
                    rx,ry,rw,rh = self.screenrect
                    cw = rw//2
                    ch = rh//2
                    cx = rx + cw
                    cy = ry + ch
                    fillellipse(screen, config.color, (cx,cy), cw, ch, primprops=primprops)
        else:
            super(FillGadget, self).draw(screen, font, offset)


def fill_req(screen):
    config.stop_cycling()
    req = str2req("Fill Type", """
[Solid]      #########
[Brush]      #########
[Wrap]       #########
[Pattern]    #########
             #########
             #########
Gradient: [\x88\x89~\x8a\x8b~\x8c\x8d~\x8e\x8f]
Dither:-------------00
[Cancel][OK]
""", "%#", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=FillGadget, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    for g in req.gadgets:
        #print("%s: %s" % (g.id, g.label))
        if g.label == str(config.fillmode):
            g.state = 1

    ditherg = req.gadget_id("7_7")
    ditherg.maxvalue = 22
    ditherg.value = config.fillmode.gradient_dither + 1
    ditherg.need_redraw = True

    dithervalg = req.gadget_id("20_7")
    if ditherg.value > 0:
        dithervalg.label = "%2d" % (ditherg.value-1)
    else:
        dithervalg.label = "\x90\x91"
    dithervalg.need_redraw = True

    dithersampleg = req.gadget_id("13_0")
    dithersampleg.value = config.fillmode.gradient_dither
    dithersampleg.fillmode_value = config.fillmode.value
    dithersampleg.need_redraw = True

    fillmode_value = config.fillmode.value
    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = pygame.event.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.fillmode.value = fillmode_value
                    config.fillmode.gradient_dither = ditherg.value - 1
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0
                elif ge.type == GadgetEvent.TYPE_GADGETUP and ge.gadget.label in FillMode.LABEL_STR:
                    fillmode_value = FillMode.LABEL_STR.index(ge.gadget.label)
                    dithersampleg.fillmode_value = fillmode_value
                    dithersampleg.need_redraw = True
            elif ge.gadget == ditherg:
                if ditherg.value > 0:
                    dithervalg.label = "%2d" % (ditherg.value-1)
                else:
                    dithervalg.label = "\x90\x91"
                dithervalg.need_redraw = True
                dithersampleg.value = ditherg.value - 1
                dithersampleg.need_redraw = True

        if len(gevents) == 0:
            if event.type == MOUSEBUTTONDOWN:
                mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
                if config.toolbar.is_inside((mouseX, mouseY)):
                    palg = config.toolbar.tool_id("palette")
                    palg.process_event(screen, event, config.get_mouse_pixel_pos)
                    dithersampleg.need_redraw = True
                elif not req.is_inside((mouseX, mouseY)):
                    config.color = config.pixel_canvas.get_at_mapped((mouseX, mouseY))
                    dithersampleg.need_redraw = True

        for g in req.gadgets:
            if g.label == FillMode.LABEL_STR[fillmode_value]:
                g.state = 1

        if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return

