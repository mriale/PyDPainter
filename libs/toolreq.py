#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os.path, colorsys
import numpy as np

import gadget
from gadget import *

from prim import *

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

#Workaround for pygame timer bug:
#  https://github.com/pygame/pygame/issues/3128
#  https://github.com/pygame/pygame/pull/3062
TIMEROFF = int((2**31)-1)

config = None

def toolreq_set_config(config_in):
    global config
    config = config_in


class FontGadget(ListGadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        if label == "&":
            scaleX = rect[2] // 8
            scaleY = rect[3] // 8
            self.arrowup = np.array([[0,16], [16,0], [32,16]]) * np.array([scaleX/4,scaleY/4])
            self.arrowdown = np.array([[0,24], [32,24], [16,40]]) * np.array([scaleX/4,scaleY/4])
            self.font_sizeg = None
        super(FontGadget, self).__init__(type, label, rect, value, maxvalue, id)

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

            #List text
            if self.label == "&":
                self.need_redraw = False
                upcolor = fgcolor
                downcolor = fgcolor
                if self.state == 1:
                    upcolor = hcolor
                elif self.state == -1:
                    downcolor = hcolor
                pygame.draw.polygon(screen, upcolor, self.arrowup + np.array([x+xo,y+yo]))
                pygame.draw.polygon(screen, downcolor, self.arrowdown + np.array([x+xo,y+yo]))
            else:
                super(FontGadget, self).draw(screen, font, offset)
        else:
            super(FontGadget, self).draw(screen, font, offset)

    def process_event(self, screen, event, mouse_pixel_mapper):
        ge = []
        x,y = mouse_pixel_mapper()
        g = self
        gx,gy,gw,gh = g.screenrect
        handled = False

        #disabled gadget
        if not g.enabled:
            return ge

        if self.type == Gadget.TYPE_CUSTOM:
            #Size up/down arrows
            if event.type == MOUSEBUTTONUP and event.button == 1 and \
               g.label == "&" and g.state != 0:
                pygame.time.set_timer(config.TOOLEVENT, TIMEROFF)
                g.state = 0
                g.need_redraw = True
                handled = True

            if g.pointin((x,y), g.screenrect) and g.label == "&":
                handled = True

                #get number from size gadget
                if g.font_sizeg.value.isnumeric() and int(g.font_sizeg.value) > 0 and int(g.font_sizeg.value) <= 500:
                    fontsize = int(g.font_sizeg.value)
                else:
                    fontsize = 0

                #handle left button
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    pygame.time.set_timer(config.TOOLEVENT, 500)
                    if y - gy < gh // 2:
                        #up arrow
                        g.state = 1
                        fontsize += 1
                    else:
                        #down arrow
                        g.state = -1
                        fontsize -= 1

                #handle mouse wheel
                elif event.type == MOUSEBUTTONDOWN and event.button in [4,5]:
                    #scroll up
                    if event.button == 4:
                        fontsize += 1
                    #scroll down
                    elif event.button == 5:
                        fontsize -= 1

                elif event.type == config.TOOLEVENT:
                    pygame.time.set_timer(config.TOOLEVENT, 100)
                    if y - gy < gh // 2:
                        #up arrow
                        g.state = 1
                        fontsize += 1
                    else:
                        #down arrow
                        g.state = -1
                        fontsize -= 1
                    
                #assign back to size gadget
                if fontsize > 0 and fontsize <= 500:
                    g.font_sizeg.value = str(fontsize)
                    g.font_sizeg.need_redraw = True
                    g.need_redraw = True

        if not handled:
            ge.extend(super(FontGadget, self).process_event(screen, event, mouse_pixel_mapper))

        return ge

#Simple filter to get rid of non-latin fonts from the font requester
def is_latin_font(fname):
    retval = True

    if fname[0:7] in ["mathjax","notosan","notoser","notocol","notonas","notomon","notokuf","notomus"]:
        retval = False
    elif fname[0:6] == "samyak":
        retval = False
    elif fname[0:5] in ["kacst","lohit"]:
        retval = False
    return retval

def font_req(screen):
    req = str2req("Choose Font", """
#################^^ [System]
#################@@ [AmigaFont]
#################@@ Size:____&
#################@@ Style:
#################@@ [Bold] [AA]
#################@@ [Italic]
#################^^ [Underline]
Preview
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
[Cancel][OK]
""", "%#^@&", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=FontGadget, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    #list items
    list_itemsg = req.gadget_id("0_0")
    list_itemsg.items = pygame.font.get_fonts()
    list_itemsg.items.sort()
    list_itemsg.items = list(filter(lambda fname: is_latin_font(fname), list_itemsg.items))
    if config.text_tool_font_name in list_itemsg.items:
        list_itemsg.top_item = list_itemsg.items.index(config.text_tool_font_name)
    else:
        list_itemsg.top_item = 0
    list_itemsg.value = list_itemsg.top_item
    last_list_itemsg_value = list_itemsg.value

    #list up/down arrows
    list_upg = req.gadget_id("17_0")
    list_upg.value = -1
    list_downg = req.gadget_id("17_6")
    list_downg.value = 1

    #list slider
    list_sliderg = req.gadget_id("17_1")
    list_sliderg.value = list_itemsg.top_item

    #all list item gadgets
    listg_list = [list_itemsg, list_upg, list_downg, list_sliderg]
    list_itemsg.listgadgets = listg_list
    list_upg.listgadgets = listg_list
    list_downg.listgadgets = listg_list
    list_sliderg.listgadgets = listg_list

    #font type
    system_fontg = req.gadget_id("20_0")
    amiga_fontg = req.gadget_id("20_1")
    amiga_fontg.enabled = False
    fonttype = config.text_tool_font_type
    if fonttype == 0:
        system_fontg.state = 1
        amiga_fontg.state = 0
    else:
        system_fontg.state = 0
        amiga_fontg.state = 1

    #font size
    font_sizeg = req.gadget_id("25_2")
    font_sizeg.value = str(config.text_tool_font_size)
    font_sizeg.numonly = True
    font_size_arrowsg = req.gadget_id("29_2")
    font_size_arrowsg.font_sizeg = font_sizeg

    #font attributes
    font_boldg = req.gadget_id("20_4")
    bold = config.text_tool_font_bold
    font_italicg = req.gadget_id("20_5")
    italic = config.text_tool_font_italic
    font_underlineg = req.gadget_id("20_6")
    underline = config.text_tool_font_underline
    if bold:
        font_boldg.state = 1
    if italic:
        font_italicg.state = 1
    if underline:
        font_underlineg.state = 1

    #antialias
    aa_fontg = req.gadget_id("27_4")
    aa = config.text_tool_font_antialias
    if aa:
        aa_fontg.state = 1

    #take care of non-square pixels
    fontmult = 1
    if config.aspectX != config.aspectY:
        fontmult = 2

    #font preview
    previewg = req.gadget_id("0_8")

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
                    config.text_tool_font_antialias = aa
                    config.text_tool_font_name = list_itemsg.items[list_itemsg.value]
                    config.text_tool_font_type = fonttype
                    config.text_tool_font_size = int(font_sizeg.value)
                    config.text_tool_font_antialias = aa
                    config.text_tool_font_bold = bold
                    config.text_tool_font_italic = italic
                    config.text_tool_font_underline = underline
                    config.text_tool_font = pygame.font.Font(pygame.font.match_font(config.text_tool_font_name, bold=config.text_tool_font_bold, italic=config.text_tool_font_italic), config.text_tool_font_size*fontmult)
                    config.text_tool_font.set_underline(config.text_tool_font_underline)
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0
                elif ge.gadget.label == "System":
                    fonttype = 0
                elif ge.gadget.label == "AmigaFont":
                    fonttype = 1
                elif ge.gadget.label == "AA":
                    aa = not aa
                elif ge.gadget.label == "Bold":
                    bold = not bold
                elif ge.gadget.label == "Italic":
                    italic = not italic
                elif ge.gadget.label == "Underline":
                    underline = not underline

        if fonttype == 0:
            system_fontg.state = 1
        else:
            amiga_fontg.state = 1

        if aa:
            aa_fontg.state = 1

        if bold:
            font_boldg.state = 1
        if italic:
            font_italicg.state = 1
        if underline:
            font_underlineg.state = 1

        if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            #Font preview
            screen.set_clip(previewg.screenrect)
            pygame.draw.rect(screen, (0,0,0), previewg.screenrect, 0)
            if font_sizeg.value.isnumeric() and int(font_sizeg.value) > 0 and int(font_sizeg.value) <= 500:
                try:
                    prefont = pygame.font.Font(pygame.font.match_font(list_itemsg.items[list_itemsg.value], bold=bold, italic=italic), int(font_sizeg.value)*fontmult)
                    prefont.set_underline(underline)
                    surf = prefont.render("The quick brown fox jumps over the lazy dog", aa, (255,255,255))
                    if config.aspectX != config.aspectY:
                        sx,sy = surf.get_size()
                        if config.aspectX == 2:
                            sy //= 2
                        else:
                            sx //= 2
                        if aa:
                            surf = pygame.transform.smoothscale(surf, (sx,sy))
                        else:
                            surf = pygame.transform.scale(surf, (sx,sy))

                    screen.blit(surf, (previewg.screenrect[0], previewg.screenrect[1]))
                    last_list_itemsg_value = list_itemsg.value
                except:
                    #revert back to known good font
                    list_itemsg.value = last_list_itemsg_value
                    list_itemsg.need_redraw = True
                    screen.fill((255,0,0))

            screen.set_clip(None)
 
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return


def place_point(symm_center):
    pixel_req_rect_bak = config.pixel_req_rect
    config.pixel_req_rect = None
    config.recompose()
    ret_coords = list(symm_center)
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
            ret_coords = (mouseX, mouseY)
            point_placed = True
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
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
        config.menubar.title_right = "%4d\x94%4d\x96" % (mouseX, config.ypos_display(mouseY))
        config.recompose()
        first_time = False

    config.menubar.title_right = ""
    config.pixel_req_rect = pixel_req_rect_bak
    config.clear_pixel_draw_canvas()
    config.recompose()

    return ret_coords

def place_grid(gcoords):
    n = 4
    w = gcoords[2]
    ow = w
    h = gcoords[3]
    oh = h
    ret_coords = list(gcoords)
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
            wnew = int(abs(w))
            hnew = int(abs(h))
            ret_coords = [point_coords[0]%wnew, point_coords[1]%hnew, wnew, hnew]
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
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

    return ret_coords

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
X:_____  Y:_____
[Center] [Center]
     [Place]
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

    centerxvalg = req.gadget_id("2_3")
    centeryvalg = req.gadget_id("11_3")

    centerxg = req.gadget_id("0_4")
    centeryg = req.gadget_id("9_4")

    placeg = req.gadget_id("5_5")

    orderg.value = str(config.symm_num)
    orderg.numonly = True
    pointg.state = 1
    centerxvalg.value = str(config.symm_center[0])
    centerxvalg.numonly = True
    centeryvalg.value = str(config.ypos_display(config.symm_center[1]))
    centeryvalg.numonly = True

    if config.symm_type == 0:
        cyclicg.state = 1
    elif config.symm_type == 1:
        mirrorg.state = 1

    symm_center = list(config.symm_center)

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
                    config.symm_center = [int(centerxvalg.value), config.ypos_display(int(centeryvalg.value))]
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
                    if not req.has_error():
                        symm_center = [int(centerxvalg.value), config.ypos_display(int(centeryvalg.value))]
                    symm_center = list(place_point(symm_center))
                    centerxvalg.value = str(symm_center[0])
                    centerxvalg.need_redraw = True
                    centeryvalg.value = str(config.ypos_display(symm_center[1]))
                    centeryvalg.need_redraw = True
                elif ge.gadget == centerxg:
                    symm_center[0] = config.pixel_width // 2
                    centerxvalg.value = str(symm_center[0])
                    centerxvalg.need_redraw = True
                elif ge.gadget == centeryg:
                    symm_center[1] = config.pixel_height // 2
                    centeryvalg.value = str(config.ypos_display(symm_center[1]))
                    centeryvalg.need_redraw = True

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
                    button_list[spacing].need_redraw = True
                    spacing = button_list.index(ge.gadget)
                    ge.gadget.state = 1
                    ge.gadget.need_redraw = True

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
                    fillellipse(screen, config.color, (cx,cy), cw, ch, primprops=primprops, interrupt=True)
                    if config.has_event():
                        #Got interrupted so still needs to redraw
                        self.need_redraw = True
        else:
            super(FillGadget, self).draw(screen, font, offset)

prev_fillmode = None
prev_color = -1
prev_fill_image = None
def draw_fill_indicator(screen):
    global prev_fillmode
    global prev_color
    global prev_fill_image
    need_redraw = True
    px = config.font.xsize // 8
    py = config.font.ysize // 8

    #check for change in fill mode
    if prev_fillmode != None and \
       prev_fillmode.value == config.fillmode.value and \
       prev_fillmode.gradient_dither == config.fillmode.gradient_dither:
        need_redraw = False
    else:
        prev_fillmode = copy.copy(config.fillmode)

    #check for change in color range
    if prev_color != config.color:
        need_redraw = True
        for crange in config.cranges:
            if crange.is_active() and \
               prev_color >= crange.low and prev_color <= crange.high and \
               config.color >= crange.low and config.color <= crange.high:
                need_redraw = False
        prev_color = config.color

    if prev_fill_image == None:
        need_redraw = True

    if need_redraw:
        prev_fill_image = pygame.Surface((px*16,py*9), 0, screen)
        fillrect(prev_fill_image, config.color, (0,0), (px*16, py*9))

    if config.fillmode.value != config.fillmode.SOLID:
        screen.blit(prev_fill_image, (px*180, py))

def fill_req(screen):
    config.stop_cycling()
    req = str2req("Fill Type", """
[Solid]     ###########
[Brush]     ###########
[Wrap]      ###########
[Pattern]   ###########
            ###########
            ###########
            ###########
Gradient: [\x88\x89~\x8a\x8b~\x8c\x8d~\x8e\x8f~\x90\x91]
Dither:----------------00
[Cancel][OK]
""", "%#", mouse_pixel_mapper=config.get_mouse_pointer_pos, custom_gadget_type=FillGadget, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    for g in req.gadgets:
        #print("%s: %s" % (g.id, g.label))
        if g.label == str(config.fillmode):
            g.state = 1

    ditherg = req.gadget_id("7_8")
    ditherg.maxvalue = 22
    ditherg.value = config.fillmode.gradient_dither + 1
    ditherg.need_redraw = True

    dithervalg = req.gadget_id("23_8")
    if ditherg.value > 0:
        dithervalg.label = "%2d" % (ditherg.value-1)
    else:
        dithervalg.label = "\x99\x9a"
    dithervalg.need_redraw = True

    dithersampleg = req.gadget_id("12_0")
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
                    config.menubar.indicators["fillmode"] = draw_fill_indicator
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
                    dithervalg.label = "\x99\x9a"
                dithervalg.need_redraw = True
                dithersampleg.value = ditherg.value - 1
                dithersampleg.need_redraw = True

        if len(gevents) == 0:
            if event.type == MOUSEBUTTONDOWN:
                mouseX, mouseY = config.get_mouse_pointer_pos(event)
                if config.toolbar.is_inside((mouseX, mouseY)):
                    palg = config.toolbar.tool_id("palette")
                    palg.process_event(screen, event, config.get_mouse_pointer_pos)
                    dithersampleg.need_redraw = True
                elif not req.is_inside((mouseX, mouseY)):
                    mouseX2, mouseY2 = config.get_mouse_pixel_pos(event)
                    config.color = config.pixel_canvas.get_at_mapped((mouseX2, mouseY2))
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

