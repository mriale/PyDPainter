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

class ToolAction(Action):
    def hide(self):
        config.clear_pixel_draw_canvas()

    def get_tip(self):
        if self.gadget.id in tiptext:
            return tiptext[self.gadget.id]
        else:
            return [self.gadget.id]

class ToolSingleAction(ToolAction):
    pass

class ToolDragAction(ToolAction):
    """
    Generic drag tool
    """
    def drawbefore(self, coords):
        config.brush.draw(config.pixel_canvas, config.color, coords)

    def drawrubber(self, coords, buttons):
        if buttons[0]:
            drawline_symm(config.pixel_canvas, config.color, self.p1, coords, interrupt=True)
        elif buttons[2]:
            drawline_symm(config.pixel_canvas, config.bgcolor, self.p1, coords, interrupt=True)

    def drawfinal(self, coords, button):
        if button == 1:
            drawline_symm(config.pixel_canvas, config.color, self.p1, coords)
        elif button == 3:
            drawline_symm(config.pixel_canvas, config.bgcolor, self.p1, coords)
        config.save_undo()

    def selected(self, attrs):
        if attrs["rightclick"]:
            spacing_req(config.pixel_req_canvas)
        else:
            config.tool_selected = self.id
        if attrs["subtool"]:
            config.subtool_selected = 1
        else:
            config.subtool_selected = 0
        self.p1 = config.get_mouse_pixel_pos()

    def move(self, coords):
        config.clear_pixel_draw_canvas()
        self.drawbefore(coords)

    def mousedown(self, coords, button):
        if not button in [1,3]:
            return
        config.cycle_handled = True
        self.p1 = coords
        buttons = [button==1, button==2, button==3]
        config.clear_pixel_draw_canvas()
        if buttons[0] or buttons[2]:
            self.drawrubber(coords, buttons)

    def drag(self, coords, buttons):
        config.cycle_handled = True
        config.clear_pixel_draw_canvas()
        if buttons[0] or buttons[2]:
            self.drawrubber(coords, buttons)

    def mouseup(self, coords, button):
        if not button in [1,3]:
            return
        config.cycle_handled = True
        config.clear_pixel_draw_canvas()
        self.drawfinal(coords, button)

class DoBIBrush(ToolAction):
    """
    Built-In brushes
    """
    brushnames = {}
    brushnames["circle"] = 1
    brushnames["square"] = 2
    brushnames["spray"] = 3
    def selected(self, attrs):
        size = int(self.id[-1:])
        name = self.id[0:-1]
        config.brush.type = DoBIBrush.brushnames[name]
        config.brush.size = size
        config.setDrawMode(DrawMode.COLOR)

class DoDot(ToolSingleAction):
    """
    Dotted freehand tool
    """
    def hide(self):
        super().hide()

    def selected(self, attrs):
        if attrs["rightclick"]:
            return
        config.tool_selected = self.id
        config.subtool_selected = 0

    def move(self, coords):
        config.clear_pixel_draw_canvas()
        config.brush.draw(config.pixel_canvas, config.color, coords)

    def mousedown(self, coords, button):
        if button == 1:
            config.brush.draw(config.pixel_canvas, config.color, coords)
        elif button == 3:
            config.brush.draw(config.pixel_canvas, config.bgcolor, coords)

    def drag(self, coords, buttons):
        if buttons[0]:
            config.brush.draw(config.pixel_canvas, config.color, coords)
        elif buttons[2]:
            config.brush.draw(config.pixel_canvas, config.bgcolor, coords)

    def mouseup(self, coords, button):
        if button in [1,3]:
            config.save_undo()

class DoDraw(ToolSingleAction):
    """
    Continuous freehand drawing/filled tool
    """
    def selected(self, attrs):
        if attrs["rightclick"]:
            return
        config.tool_selected = self.id
        if attrs["subtool"]:
            config.subtool_selected = 1
            self.polylist = [config.get_mouse_pixel_pos()]
        else:
            config.subtool_selected = 0
        self.last_coords = config.get_mouse_pixel_pos()

    def move(self, coords):
        config.clear_pixel_draw_canvas()
        if config.subtool_selected:
            drawline_symm(config.pixel_canvas, config.color, coords, coords, xormode=1, handlesymm=True)
        else:
            config.brush.draw(config.pixel_canvas, config.color, coords)

    def mousedown(self, coords, button):
        if config.subtool_selected:
            if button in [1,3]:
                drawline_symm(config.pixel_canvas, config.color, coords, coords, xormode=1)
                self.polylist = [coords]
        else:
            if button == 1:
                config.clear_pixel_draw_canvas()
                config.brush.draw(config.pixel_canvas, config.color, coords)
                self.last_coords = coords
            elif button == 3:
                config.clear_pixel_draw_canvas()
                config.brush.draw(config.pixel_canvas, config.bgcolor, coords)
                self.last_coords = coords

    def drag(self, coords, buttons):
        if config.subtool_selected:
            if buttons[0] or buttons[2]:
                drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], coords, xormode=1, handlesymm=True, skiplast=True)
                self.polylist.append(coords)
        else:
            if buttons[0]:
                drawmode = config.drawmode.value
                if drawmode == DrawMode.CYCLE:
                    drawmode = DrawMode.COLOR
                drawline_symm(config.pixel_canvas, config.color, self.last_coords, coords, drawmode=drawmode)
                self.last_coords = coords
            elif buttons[2]:
                drawline_symm(config.pixel_canvas, config.bgcolor, self.last_coords, coords)
                self.last_coords = coords

    def mouseup(self, coords, button):
        if button in [1,3]:
            if config.subtool_selected:
                config.clear_pixel_draw_canvas()
                if button == 1:
                    fillpoly(config.pixel_canvas, config.color, self.polylist)
                elif button == 3:
                    fillpoly(config.pixel_canvas, config.bgcolor, self.polylist)
                self.polylist = [coords]

            config.save_undo()

class DoLine(ToolDragAction):
    """
    Line tool
    """
    def drawbefore(self, coords):
        config.brush.draw(config.pixel_canvas, config.color, coords)

    def drawrubber(self, coords, buttons):
        if buttons[0]:
            drawline_symm(config.pixel_canvas, config.color, self.p1, coords, interrupt=True)
        elif buttons[2]:
            drawline_symm(config.pixel_canvas, config.bgcolor, self.p1, coords, interrupt=True)

    def drawfinal(self, coords, button):
        if button == 1:
            drawline_symm(config.pixel_canvas, config.color, self.p1, coords)
        elif button == 3:
            drawline_symm(config.pixel_canvas, config.bgcolor, self.p1, coords)
        config.save_undo()

class DoCurve(ToolSingleAction):
    """
    Curve tool
    """
    def selected(self, attrs):
        if attrs["rightclick"]:
            spacing_req(config.pixel_req_canvas)
        else:
            config.tool_selected = self.id
        self.line_start = config.get_mouse_pixel_pos()
        self.line_end = None
        self.button = None

    def move(self, coords):
        config.clear_pixel_draw_canvas()
        if self.line_end == None:
            config.brush.draw(config.pixel_canvas, config.color, coords)
        else:
            if self.button == 1:
                drawcurve(config.pixel_canvas, config.color, self.line_start, self.line_end, coords, interrupt=True)
            elif self.button == 3:
                drawcurve(config.pixel_canvas, config.bgcolor, self.line_start, self.line_end, coords, interrupt=True)

    def mousedown(self, coords, button):
        if not button in [1,3]:
            return

        config.cycle_handled = True

        if self.line_end == None:
            self.line_start = coords
            config.clear_pixel_draw_canvas()
            if button == 1:
                config.brush.draw(config.pixel_canvas, config.color, coords)
            elif button == 3:
                config.brush.draw(config.pixel_canvas, config.bgcolor, coords)
            self.button = button
        else:
            config.clear_pixel_draw_canvas()
            if button == 1:
                drawcurve(config.pixel_canvas, config.color, self.line_start, self.line_end, coords)
            elif button == 3:
                drawcurve(config.pixel_canvas, config.bgcolor, self.line_start, self.line_end, coords)
            config.save_undo()
            self.line_start = None
            self.line_end = None

    def drag(self, coords, buttons):
        if not (buttons[0] or butons[2]):
            return

        config.cycle_handled = True
        if self.line_start:
            config.clear_pixel_draw_canvas()
            if buttons[0]:
                drawline_symm(config.pixel_canvas, config.color, self.line_start, coords, interrupt=True)
            elif buttons[2]:
                drawline_symm(config.pixel_canvas, config.bgcolor, self.line_start, coords, interrupt=True)

    def mouseup(self, coords, button):
        if not button in [1,3]:
            return

        config.cycle_handled = True
        if self.line_start:
            config.clear_pixel_draw_canvas()
            if button == 1:
                drawline_symm(config.pixel_canvas, config.color, self.line_start, coords)
            elif button == 3:
                drawline_symm(config.pixel_canvas, config.bgcolor, self.line_start, coords)
            self.line_end = coords

class DoFill(ToolSingleAction):
    """
    Flood Fill tool
    """
    def hide(self):
        super().hide()

    def selected(self, attrs):
        if attrs["rightclick"]:
            fill_req(config.pixel_req_canvas)
        else:
            config.tool_selected = self.id
            config.subtool_selected = 0

    def move(self, coords):
        pass

    def mousedown(self, coords, button):
        if button == 1:
            floodfill(config.pixel_canvas, config.color, coords)
        elif button == 3:
            floodfill(config.pixel_canvas, config.bgcolor, coords)

    def mouseup(self, coords, button):
        if button in [1,3]:
            config.save_undo()

class DoAirbrush(ToolSingleAction):
    """
    Airbrush tool
    """
    def draw(self, color, coords):
        for i in range(0,5):
            config.brush.draw(config.pixel_canvas, color, config.airbrush_coords(coords[0],coords[1]))

    def hide(self):
        super().hide()

    def selected(self, attrs):
        if attrs["rightclick"]:
            spacing_req(config.pixel_req_canvas)
        else:
            config.tool_selected = self.id
            config.subtool_selected = 0

    def move(self, coords):
        config.clear_pixel_draw_canvas()
        config.brush.draw(config.pixel_canvas, config.color, coords)

    def mousedown(self, coords, button):
        if button == 1:
            self.draw(config.color, coords)
            pygame.time.set_timer(pygame.USEREVENT, 15)
        elif button == 3:
            self.draw(config.bgcolor, coords)
            pygame.time.set_timer(pygame.USEREVENT, 15)

    def drag(self, coords, buttons):
        if buttons[0]:
            self.draw(config.color, coords)
        elif buttons[2]:
            self.draw(config.bgcolor, coords)

    def mouseup(self, coords, button):
        if button in [1,3]:
            pygame.time.set_timer(pygame.USEREVENT, 0)
            config.save_undo()

class DoRect(ToolDragAction):
    """
    Rectangle tool
    """
    def drawbefore(self, coords):
        mouseX, mouseY = coords
        drawxorcross(config.pixel_canvas, mouseX, mouseY)
        if config.subtool_selected == 0:
            config.brush.draw(config.pixel_canvas, config.color, coords)

    def drawrubber(self, coords, buttons):
        if buttons[0]:
            drawrect(config.pixel_canvas, config.color, self.p1, coords, filled=config.subtool_selected, interrupt=True)
        elif buttons[2]:
            drawrect(config.pixel_canvas, config.bgcolor, self.p1, coords, filled=config.subtool_selected, interrupt=True)

    def drawfinal(self, coords, button):
        if button == 1:
            drawrect(config.pixel_canvas, config.color, self.p1, coords, filled=config.subtool_selected)
        elif button == 3:
            drawrect(config.pixel_canvas, config.bgcolor, self.p1, coords, filled=config.subtool_selected)
        config.save_undo()

class DoCircle(ToolDragAction):
    """
    Circle tool
    """
    def drawbefore(self, coords):
        mouseX, mouseY = coords
        drawxorcross(config.pixel_canvas, mouseX, mouseY)
        if config.subtool_selected == 0:
            config.brush.draw(config.pixel_canvas, config.color, coords)

    def drawrubber(self, coords, buttons):
        mouseX, mouseY = coords
        startX, startY = self.p1
        ax = config.aspectX
        ay = config.aspectY
        dx = (mouseX-startX)//ax
        dy = (mouseY-startY)//ay
        radius = int(math.sqrt(dx*dx + dy*dy))
        if buttons[0]:
            if ax == ay:
                drawcircle(config.pixel_canvas, config.color, self.p1, radius, filled=config.subtool_selected, interrupt=True)
            else:
                drawellipse(config.pixel_canvas, config.color, self.p1, radius*ax, radius*ay, filled=config.subtool_selected, interrupt=True)
        elif buttons[2]:
            if ax == ay:
                drawcircle(config.pixel_canvas, config.bgcolor, self.p1, radius, filled=config.subtool_selected, interrupt=True)
            else:
                drawellipse(config.pixel_canvas, config.bgcolor, self.p1, radius*ax, radius*ay, filled=config.subtool_selected, interrupt=True)

    def drawfinal(self, coords, button):
        mouseX, mouseY = coords
        startX, startY = self.p1
        ax = config.aspectX
        ay = config.aspectY
        dx = (mouseX-startX)//ax
        dy = (mouseY-startY)//ay
        radius = int(math.sqrt(dx*dx + dy*dy))
        if button == 1:
            if ax == ay:
                drawcircle(config.pixel_canvas, config.color, self.p1, radius, filled=config.subtool_selected)
            else:
                drawellipse(config.pixel_canvas, config.color, self.p1, radius*ax, radius*ay, filled=config.subtool_selected)
        elif button == 3:
            if ax == ay:
                drawcircle(config.pixel_canvas, config.bgcolor, self.p1, radius, filled=config.subtool_selected)
            else:
                drawellipse(config.pixel_canvas, config.bgcolor, self.p1, radiusax, radius*ay, filled=config.subtool_selected)
        config.save_undo()

class DoEllipse(ToolDragAction):
    """
    Ellipse tool
    """
    def drawbefore(self, coords):
        mouseX, mouseY = coords
        drawxorcross(config.pixel_canvas, mouseX, mouseY)
        if config.subtool_selected == 0:
            config.brush.draw(config.pixel_canvas, config.color, coords)

    def drawrubber(self, coords, buttons):
        mouseX, mouseY = coords
        startX, startY = self.p1
        radiusX = int(abs(mouseX-startX))
        radiusY = int(abs(mouseY-startY))
        if buttons[0]:
            drawellipse(config.pixel_canvas, config.color, self.p1, radiusX, radiusY, filled=config.subtool_selected, interrupt=True)
        elif buttons[2]:
            drawellipse(config.pixel_canvas, config.bgcolor, self.p1, radiusX, radiusY, filled=config.subtool_selected, interrupt=True)

    def drawfinal(self, coords, button):
        mouseX, mouseY = coords
        startX, startY = self.p1
        radiusX = int(abs(mouseX-startX))
        radiusY = int(abs(mouseY-startY))
        if button == 1:
            drawellipse(config.pixel_canvas, config.color, self.p1, radiusX, radiusY, filled=config.subtool_selected)
        elif button == 3:
            drawellipse(config.pixel_canvas, config.bgcolor, self.p1, radiusX, radiusY, filled=config.subtool_selected)
        config.save_undo()

class DoPoly(ToolSingleAction):
    """
    Polygon tool dispatcher
    """
    def __init__(self, id=None, gadget=None):
        self.polylist = []
        self.hidden = False
        self.p1w,self.p1h = (2,2)
        self.do_poly_line = DoPolyLine(id=id, gadget=gadget)
        self.do_poly_fill = DoPolyFill(id=id, gadget=gadget)
        super(ToolSingleAction, self).__init__(id=id, gadget=gadget)

    def draw_p1(self):
        if len(self.polylist) == 0:
            return
        p1x,p1y = self.polylist[0]
        w,h = (self.p1w,self.p1h)
        drawrect(config.pixel_canvas, config.color, (p1x-w,p1y-h), (p1x+w,p1y+h), xormode=True, handlesymm=False)

    def in_p1_rect(self, coords):
        if len(self.polylist) == 0:
            return False
        p1x,p1y = self.polylist[0]
        w,h = (self.p1w,self.p1h)
        x,y = coords
        return x >= p1x-w and x <= p1x+w and y >= p1y-h and y <= p1y+h

    def selected(self, attrs):
        if attrs["rightclick"]:
            return

        config.tool_selected = self.id
        if attrs["subtool"]:
            config.subtool_selected = 1
        else:
            config.subtool_selected = 0
        self.do_poly_line.polylist = []
        self.do_poly_fill.polylist = []
        self.do_poly_line.last_coords = config.get_mouse_pixel_pos()
        self.do_poly_fill.last_coords = config.get_mouse_pixel_pos()
        self.do_poly_line.hidden = False
        self.do_poly_fill.hidden = False

    def hide(self):
        if config.subtool_selected:
            self.do_poly_fill.hide()
        else:
            self.do_poly_line.hide()

    def move(self, coords):
        if config.subtool_selected:
            self.do_poly_fill.move(coords)
        else:
            self.do_poly_line.move(coords)

    def mousedown(self, coords, button):
        if config.subtool_selected:
            self.do_poly_fill.mousedown(coords, button)
        else:
            self.do_poly_line.mousedown(coords, button)

    def drag(self, coords, buttons):
        if config.subtool_selected:
            self.do_poly_fill.drag(coords, buttons)
        else:
            self.do_poly_line.drag(coords, buttons)

    def mouseup(self, coords, button):
        if config.subtool_selected:
            self.do_poly_fill.mouseup(coords, button)
        else:
            self.do_poly_line.mouseup(coords, button)

class DoPolyLine(DoPoly):
    """
    Polygon tool - lines
    """
    def __init__(self, id=None, gadget=None):
        self.polylist = []
        self.hidden = False
        self.p1w,self.p1h = (2,2)
        super(ToolSingleAction, self).__init__(id=id, gadget=gadget)

    def hide(self):
        if self.hidden:
            return
        config.clear_pixel_draw_canvas()
        self.hidden = True

    def move(self, coords):
        self.p1w,self.p1h = (config.brush.rect[2]//2+2, config.brush.rect[3]//2+2)
        config.clear_pixel_draw_canvas()
        if len(self.polylist) > 0:
            drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], coords, handlesymm=True, interrupt=True)
            self.draw_p1()
        else:
            config.brush.draw(config.pixel_canvas, config.color, coords)
        self.hidden = False

    def mousedown(self, coords, button):
        if button in [1,3]:
            if len(self.polylist) == 0:
                if button == 1:
                    config.brush.draw(config.pixel_canvas, config.color, coords)
                    self.polylist.append(coords)
                    self.last_coords = coords
                elif button == 3:
                    config.brush.draw(config.pixel_canvas, config.bgcolor, coords)
                    self.polylist.append(coords)
                    self.last_coords = coords
        self.hidden = False

    def drag(self, coords, buttons):
        if buttons[0]:
            config.clear_pixel_draw_canvas()
            if len(self.polylist) > 0:
                drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], coords, handlesymm=True, interrupt=True)
                self.draw_p1()
            else:
                config.brush.draw(config.pixel_canvas, config.color, coords)
            self.last_coords = coords
        elif buttons[2]:
            config.clear_pixel_draw_canvas()
            if len(self.polylist) > 0:
                drawline_symm(config.pixel_canvas, config.bgcolor, self.polylist[-1], coords, handlesymm=True, interrupt=True)
                self.draw_p1()
            else:
                config.brush.draw(config.pixel_canvas, config.bgcolor, coords)
            self.last_coords = coords
        self.hidden = False

    def mouseup(self, coords, button):
        if button in [1,3]:
            if self.in_p1_rect(coords) and len(self.polylist) > 2:
                coords = self.polylist[0]
            if button == 1:
                config.clear_pixel_draw_canvas()
                if len(self.polylist) > 0:
                    drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], coords, handlesymm=True)
                else:
                    config.brush.draw(config.pixel_canvas, config.color, coords)
                config.save_undo()
                self.polylist.append(coords)
                self.last_coords = coords
                if self.in_p1_rect(coords) and len(self.polylist) > 2:
                    self.polylist = []
            elif button == 3:
                config.clear_pixel_draw_canvas()
                if len(self.polylist) > 0:
                    drawline_symm(config.pixel_canvas, config.bgcolor, self.polylist[-1], coords, handlesymm=True)
                else:
                    config.brush.draw(config.pixel_canvas, config.bgcolor, coords)
                config.save_undo()
                self.polylist.append(coords)
                self.last_coords = coords
                if self.in_p1_rect(coords) and len(self.polylist) > 2:
                    self.polylist = []
        self.hidden = False

class DoPolyFill(DoPoly):
    """
    Polygon tool - filled
    """
    def __init__(self, id=None, gadget=None):
        self.polylist = []
        self.hidden = False
        self.p1w,self.p1h = (2,2)
        super(ToolSingleAction, self).__init__(id=id, gadget=gadget)

    def hide(self):
        if self.hidden:
            return
        if len(self.polylist) > 0:
            drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], self.last_coords, xormode=1, handlesymm=True, skiplast=True)
        else:
            config.clear_pixel_draw_canvas()
        self.hidden = True

    def move(self, coords):
        self.p1w,self.p1h = (2,2)
        if len(self.polylist) > 0:
            if self.hidden:
                drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], coords, xormode=1, handlesymm=True, skiplast=True)
            else:
                drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], self.last_coords, xormode=1, handlesymm=True, skiplast=True)
                drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], coords, xormode=1, handlesymm=True, skiplast=True)
        else:
            config.clear_pixel_draw_canvas()
            drawline_symm(config.pixel_canvas, config.color, coords, coords, xormode=1, handlesymm=True)
        self.last_coords = coords
        self.hidden = False

    def mousedown(self, coords, button):
        if button in [1,3]:
            if len(self.polylist) == 0:
                drawline_symm(config.pixel_canvas, config.color, self.last_coords, self.last_coords, xormode=1, handlesymm=True)
                self.polylist.append(coords)
                self.last_coords = coords
                self.draw_p1()
        self.hidden = False

    def drag(self, coords, buttons):
        if buttons[0] or buttons[2]:
            drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], self.last_coords, xormode=1, handlesymm=True, skiplast=True)
            drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], coords, xormode=1, handlesymm=True, skiplast=True)
            self.last_coords = coords
        self.hidden = False

    def mouseup(self, coords, button):
        if button in [1,3]:
            drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], self.last_coords, xormode=1, handlesymm=True, skiplast=True)
            if self.in_p1_rect(coords) and len(self.polylist) > 2:
                coords = self.polylist[0]
            drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], coords, xormode=1, handlesymm=True, skiplast=True)
            self.polylist.append(coords)
            self.last_coords = coords
            if self.in_p1_rect(coords) and len(self.polylist) > 2:
                if button == 1:
                    config.clear_pixel_draw_canvas()
                    fillpoly(config.pixel_canvas, config.color, self.polylist)
                    self.polylist = []
                    config.save_undo()
                elif button == 3:
                    config.clear_pixel_draw_canvas()
                    fillpoly(config.pixel_canvas, config.bgcolor, self.polylist)
                    self.polylist = []
                    config.save_undo()
            else:
                if button == 1:
                    #config.clear_pixel_draw_canvas()
                    if len(self.polylist) > 0:
                        drawline_symm(config.pixel_canvas, config.color, self.polylist[-1], coords, xormode=1, handlesymm=True, skiplast=True)
                    else:
                        drawline_symm(config.pixel_canvas, config.color, coords, coords, xormode=1, handlesymm=True, skiplast=True)
                    #config.save_undo()
                    self.polylist.append(coords)
                    self.last_coords = coords
                elif button == 3:
                    #config.clear_pixel_draw_canvas()
                    if len(self.polylist) > 0:
                        drawline_symm(config.pixel_canvas, config.bgcolor, self.polylist[-1], coords, xormode=1, handlesymm=True, skiplast=True)
                    else:
                        drawline_symm(config.pixel_canvas, config.bgcolor, coords, coords, xormode=1, handlesymm=True, skiplast=True)
                    #config.save_undo()
                    self.polylist.append(coords)
                    self.last_coords = coords
        self.hidden = False

class DoText(ToolSingleAction):
    """
    Text tool
    """
    def __init__(self, id=None, gadget=None):
        self.pos = None
        self.text = ""
        self.font = config.text_tool_font
        self.fontsize = self.font.size("M")
        self.baseline = self.font.get_ascent()
        self.lastblink = 0
        self.box_on = False
        super(ToolSingleAction, self).__init__(id=id, gadget=gadget)

    def hide(self):
        if self.box_on:
            self.drawbox(self.pos)
            self.box_on = False

    def selected(self, attrs):
        if attrs["rightclick"]:
            font_req(config.pixel_req_canvas)
            return

        config.tool_selected = self.id
        config.subtool_selected = 0
        self.pos = None
        self.text = ""

    def deselected(self, attrs):
        self.stamptext()
        pygame.time.set_timer(pygame.USEREVENT, 0)

    def drawbox(self, coords):
        self.font = config.text_tool_font
        self.fontsize = self.font.size("M")
        self.baseline = self.font.get_ascent()
        mx, my = coords
        fw,fh = self.fontsize
        fb = self.baseline
        ssx,ssy = self.font.size(self.text)
        mx += ssx
        drawrect(config.pixel_canvas, config.color,
            (mx, my-fw), (mx+fw, my-fb+fh), xormode=True, handlesymm=False)
        drawline(config.pixel_canvas, config.color,
            (mx+1,my), (mx+fw-1,my), xormode=True, handlesymm=False)

    def drawtext(self, coords):
        if coords != None and self.text != "":
            self.font = config.text_tool_font
            self.fontsize = self.font.size("M")
            self.baseline = self.font.get_ascent()
            mx, my = coords
            my -= self.baseline
            surf = self.font.render(self.text, config.text_tool_font_antialias, config.pixel_canvas.unmap_rgb(config.color))
            pixel_canvas_rgb = pygame.Surface(surf.get_size(),0)
            pixel_canvas_rgb.blit(config.undo_image[config.undo_index], (0,0), (mx,my,surf.get_width(),surf.get_height()))
            pixel_canvas_rgb.blit(surf, (0, 0))
            config.pixel_canvas.blit(convert8(pixel_canvas_rgb, config.pal), (mx,my))

    def stamptext(self):
        config.clear_pixel_draw_canvas()
        if self.text != "":
            self.drawtext(self.pos)
            config.save_undo()
            self.text = ""
        self.pos = None

    def move(self, coords):
        if self.pos == None:
            pygame.time.set_timer(pygame.USEREVENT, 0)
            config.clear_pixel_draw_canvas()
            self.drawbox(coords)
            self.box_on = True
        else:
            if pygame.time.get_ticks() - self.lastblink >= 500:
                self.drawbox(self.pos)
                self.box_on = not self.box_on
                self.lastblink = pygame.time.get_ticks()

    def drag(self, coords, button):
        config.clear_pixel_draw_canvas()
        self.drawbox(coords)
        self.box_on = True
        pygame.time.set_timer(pygame.USEREVENT, 0)

    def mousedown(self, coords, button):
        if button in [1,3]:
            if self.pos == None:
                self.drawbox(coords)
                self.box_on = True
            else:
                self.stamptext()
                self.drawbox(coords)
                self.box_on = True

    def mouseup(self, coords, button):
        if button in [1,3]:
            config.clear_pixel_draw_canvas()
            self.text = ""
            pygame.time.set_timer(pygame.USEREVENT, 100)
            self.pos = coords
            self.drawbox(coords)
            self.box_on = True
            self.lastblink = pygame.time.get_ticks()

    def keydown(self, key, mod, unicode):
        if self.pos == None:
            return False

        if mod & KMOD_CTRL or mod & KMOD_ALT or mod & KMOD_META:
            return False

        if key == K_BACKSPACE:
            self.text = self.text[:-1]
        elif key == K_RETURN:
            pos = self.pos
            self.stamptext()
            self.pos = [pos[0], pos[1]+self.fontsize[1]]
        elif key == K_ESCAPE:
            self.stamptext()
            config.toolbar.click(config.toolbar.tool_id("draw"), MOUSEBUTTONDOWN)
            return True
        else:
            self.text += unicode

        config.clear_pixel_draw_canvas()
        self.drawtext(self.pos)
        self.drawbox(self.pos)
        self.box_on = True
        self.lastblink = pygame.time.get_ticks()
        return True

class DoBrush(ToolDragAction):
    """
    Brush tool
    """
    def drawbefore(self, coords):
        mouseX, mouseY = coords
        drawxorcross(config.pixel_canvas, mouseX, mouseY)

    def drawrubber(self, coords, buttons):
        if buttons[0] or buttons[2]:
            drawrect(config.pixel_canvas, config.color, self.p1, coords, xormode=True, handlesymm=False)

    def drawfinal(self, coords, button):
        if button == 1 or button == 3:
            config.brush = Brush(type=Brush.CUSTOM, screen=config.pixel_canvas, bgcolor=config.bgcolor, coordfrom=self.p1, coordto=coords)
        if button == 1:
            pass
        elif button == 3:
            drawrect(config.pixel_canvas, config.bgcolor, self.p1, coords, filled=True, handlesymm=False)
        if button == 1 or button == 3:
            config.save_undo()
            config.toolbar.click(config.toolbar.tool_id("dot"), MOUSEBUTTONDOWN)
            config.toolbar.tool_id("circle1").state = 0
            config.toolbar.tool_id("circle2").state = 0
            config.toolbar.tool_id("circle3").state = 0
            config.toolbar.tool_id("circle4").state = 0
            config.toolbar.tool_id("square1").state = 0
            config.toolbar.tool_id("square2").state = 0
            config.toolbar.tool_id("square3").state = 0
            config.toolbar.tool_id("square4").state = 0
            config.toolbar.tool_id("spray1").state = 0
            config.toolbar.tool_id("spray2").state = 0
            config.setDrawMode(DrawMode.MATTE)

class DoGrid(ToolAction):
    """
    Grid toggle and grid requestor
    """
    def selected(self, attrs):
        if attrs["rightclick"]:
            grid_req(config.pixel_req_canvas)
        else:
            config.grid_on = True

    def deselected(self, attrs):
        config.grid_on = False

class DoSymm(ToolAction):
    """
    Symmetry toggle and symmetry requestor
    """
    def selected(self, attrs):
        if attrs["rightclick"]:
            symmetry_req(config.pixel_req_canvas)
        else:
            config.symm_on = True

    def deselected(self, attrs):
        config.symm_on = False

class DoMagnify(ToolAction):
    """
    Magnify toggle
    """
    def selected(self, attrs):
        if attrs["rightclick"]:
            return
        if "eventtype" in attrs and attrs["eventtype"] == KEYDOWN:
            config.zoom.center = config.get_mouse_pixel_pos()
            config.zoom.on = True
        else:
            config.zoom.box_on = True

    def deselected(self, attrs):
        config.zoom.on = False
        config.zoom.box_on = False

    def move(self, coords):
        x,y = coords
        w = 100*config.aspectX // config.zoom.factor
        h = 100*config.aspectY // config.zoom.factor
        config.clear_pixel_draw_canvas()
        drawrect(config.pixel_canvas, config.color, (x-w,y-h), (x+w,y+h), xormode=True, handlesymm=False)

    def drag(self, coords, buttons):
        self.move(coords)

    def mouseup(self, coords, button):
        config.clear_pixel_draw_canvas()
        config.zoom.center = coords
        config.zoom.box_on = False
        config.zoom.on = True

class DoZoom(ToolAction):
    """
    Zoom in or out
    """
    def selected(self, attrs):
        if attrs["rightclick"]:
            if config.zoom.factor > config.zoom.factor_min:
                config.zoom.factor -= 1
        else:
            if config.zoom.factor < config.zoom.factor_max:
                config.zoom.factor += 1
        if config.zoom.box_on:
            mag_action = config.toolbar.tool_id("magnify").action
            mag_action.move(config.get_mouse_pixel_pos())


class DoUndo(ToolAction):
    """
    Undo/Redo button
    """
    def selected(self, attrs):
        if attrs["rightclick"]:
            config.redo()
        else:
            config.undo()

class DoClear(ToolAction):
    """
    Clear screen to background color
    """
    def selected(self, attrs):
        config.pixel_canvas.fill(config.bgcolor);
        config.save_undo()

class DoSwatch(ToolAction):
    pass

class DoPalette(ToolAction):
    pass

class PalGadget(ToolGadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None, toolbar=None, action=None):
        self.group_list = []
        if label == "^":
            self.crng_arrows = pygame.image.load(os.path.join('data', 'crng_arrows.png'))
            value = 0
        if label == "#":
            scaleX = config.pixel_width // 320
            scaleY = config.pixel_height // 200
            scaledown = 4 // min(scaleX,scaleY)
            self.palettearrows_image = imgload('palettearrows.png', scaleX=scaleX, scaleY=scaleY, scaledown=scaledown)
        super(PalGadget, self).__init__(type, label, rect, value, maxvalue, id, tool_type=ToolGadget.TT_CUSTOM, toolbar=toolbar, action=action)

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
            #if not self.need_redraw:
            #    return

            self.need_redraw = False

            if self.label == "#":
                pygame.draw.rect(screen, fgcolor, self.screenrect, 0)
                # Draw color palette
                numcolors = len(config.pal)
                if numcolors >= 32:
                    color_cols = 4
                elif numcolors == 16:
                    color_cols = 2
                elif numcolors == 8:
                    color_cols = 2
                elif numcolors <= 4:
                    color_cols = 1

                colors_shown = 32
                if numcolors < colors_shown:
                    colors_shown = numcolors

                color_rows = colors_shown // color_cols
                color_width = w // color_cols
                if numcolors <= 32:
                    color_height = int(round(h*1.0 / color_rows))
                else:
                    color_height = int(round((h-self.palettearrows_image.get_height())*1.0 / color_rows))

                self.value = config.color
                if config.color < config.palette_page or config.color > config.palette_page + 31:
                    config.palette_page = config.color & 0xE0

                screen.set_clip(self.screenrect)
                curcolor = config.palette_page
                self.palette_bounds = []
                curr_rect = (0,0,0,0)
                for j in range(0,color_cols):
                    for i in range(0,color_rows):
                        self.palette_bounds.append((x+xo+1+j*color_width,y+yo+1+i*color_height,color_width,color_height, curcolor))
                        pygame.draw.rect(screen, config.pal[curcolor], (x+xo+1+j*color_width,y+yo+1+i*color_height,color_width,color_height), 0)
                        if curcolor == self.value:
                            curr_rect = (x+xo+j*color_width,y+yo+i*color_height,color_width+2,color_height+2)
                        curcolor += 1
                #highlight current color
                pygame.draw.rect(screen, (255,255,255), curr_rect, 1)

                #draw color pager if > 32 colors
                if numcolors > 32:
                    #draw palette arrows
                    ah = self.palettearrows_image.get_height()
                    aw = self.palettearrows_image.get_width() // 10
                    ax = x+xo+1
                    ay = y+yo+1+color_rows*color_height
                    self.palette_bounds.append((ax,ay,aw,ah,-1))
                    screen.blit(self.palettearrows_image, (ax,ay), (aw*8,0,aw,ah))
                    screen.blit(self.palettearrows_image, (ax+aw,ay), (aw*config.palette_page//32,0,aw,ah))
                    self.palette_bounds.append((ax+aw+aw,ay,aw,ah,-2))
                    screen.blit(self.palettearrows_image, (ax+aw+aw,ay), (aw*9,0,aw,ah))

                screen.set_clip(None)

            elif self.label == "%": # color swatch
                pygame.draw.rect(screen, config.pal[config.bgcolor], self.screenrect, 0)
                swx, swy, sww, swh = self.screenrect
                scx = sww // 2 + swx
                scy = swh // 2 + swy
                ry = swh * 4 // 10
                rx = sww * 4 // 24
                orect = [scx-rx, scy-ry, rx*2, ry*2]
                pygame.draw.ellipse(screen, config.pal[config.color], orect, 0)
            elif self.label == "^": # direction arrow
                pygame.draw.rect(screen, bgcolor, self.screenrect, 0)
                if self.state == 0:
                    pygame.draw.rect(screen, fgcolor, (x+xo+1,y+yo,w-1,h), 1)
                    pygame.draw.line(screen, hcolor, (x+xo+1,y+yo), (x+xo+w-2,y+yo))
                    pygame.draw.line(screen, hcolor, (x+xo+1,y+yo), (x+xo+1,y+yo+h-1))
                else:
                    pygame.draw.rect(screen, hcolor, (x+xo+1,y+yo,w-1,h), 1)
                    pygame.draw.line(screen, fgcolor, (x+xo+1,y+yo), (x+xo+w-2,y+yo))
                    pygame.draw.line(screen, fgcolor, (x+xo+1,y+yo), (x+xo+1,y+yo+h-1))
                if self.value == 1:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (0,0,9,9))
                elif self.value == -1:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (9,0,9,9))
                elif self.value == -2:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (18,0,9,9))
                elif self.value == 2:
                    screen.blit(self.crng_arrows, (x+xo+4,y+yo+1), (27,0,9,9))
            if not self.enabled:
                for i in range(x+xo, x+xo+w+1, 2):
                    for j in range(y+yo, y+yo+h+1, 4):
                        pygame.draw.rect(screen, bgcolor, (i,j,1,1), 0)
                for i in range(x+xo+1, x+xo+w+1, 2):
                    for j in range(y+yo+2, y+yo+h+1, 4):
                        pygame.draw.rect(screen, bgcolor, (i,j,1,1), 0)
                fadesurf = pygame.Surface((w,h), SRCALPHA)
                fadesurf.fill((bgcolor[0],bgcolor[1],bgcolor[2],128))
                screen.blit(fadesurf, self.screenrect)
        else:
            super(PalGadget, self).draw(screen, font, offset)

    def pick_color(self):
        config.cursor.shape = 3
        config.clear_pixel_draw_canvas()
        config.recompose()
        color_picked = False
        first_time = True
        wait_for_mouseup = 1 + pygame.mouse.get_pressed()[0]
        while wait_for_mouseup:
            event = pygame.event.poll()
            while event.type == pygame.MOUSEMOTION and pygame.event.peek((MOUSEMOTION)):
                #get rid of extra mouse movements
                event = pygame.event.poll()

            if event.type == pygame.NOEVENT and not first_time:
                event = pygame.event.wait()

            mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
            if event.type == MOUSEMOTION and True in event.buttons and wait_for_mouseup:
                if event.buttons[0]:
                    config.color = config.pixel_canvas.get_at_mapped((mouseX, mouseY))
                elif event.buttons[2]:
                    config.bgcolor = config.pixel_canvas.get_at_mapped((mouseX, mouseY))
            elif event.type == MOUSEBUTTONDOWN:
                color_picked = True
                if event.button == 1:
                    config.color = config.pixel_canvas.get_at_mapped((mouseX, mouseY))
                elif event.button == 3:
                    config.bgcolor = config.pixel_canvas.get_at_mapped((mouseX, mouseY))
            elif event.type == MOUSEBUTTONUP and wait_for_mouseup:
                wait_for_mouseup -= 1

            config.recompose()
            first_time = False


    def process_event(self, screen, event, mouse_pixel_mapper):
        ge = []
        x,y = mouse_pixel_mapper()
        g = self
        gx,gy,gw,gh = g.screenrect

        #disabled gadget
        if not g.enabled:
            return ge

        if self.type == Gadget.TYPE_CUSTOM:
            if g.pointin((x,y), g.screenrect):
                #handle left button
                if event.type == MOUSEBUTTONDOWN and event.button in [1,3]:
                    if g.label == "#": #Color palette
                        for i in range(len(self.palette_bounds)):
                            x1,y1,x2,y2,colorindex = self.palette_bounds[i]
                            if x >= x1 and x <= x1+x2-1 and y >= y1 and y <= y1+y2-1:
                                g.need_redraw = True
                                if colorindex >= 0:
                                    g.value = colorindex
                                    if event.button == 1:
                                        config.color = colorindex
                                    else:
                                        config.bgcolor = colorindex
                                elif colorindex == -1: #palette page left
                                    if config.palette_page > 0:
                                        config.palette_page -= 32
                                        config.color -= 32
                                elif colorindex == -2: #palette page right
                                    if config.palette_page < config.NUM_COLORS-32:
                                        config.palette_page += 32
                                        config.color += 32
                                ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
                    elif g.label == "%": #Current color swatch
                        if event.button == 1:
                            self.pick_color()
                        elif event.button == 3:
                            palette_req(config.pixel_req_canvas)
                    elif g.label == "^":
                        g.state = 1
                        g.need_redraw = True
                elif event.type == MOUSEMOTION and event.button:
                    tip_on = False
                    if "render_tip" in dir(g):
                        tip_on = True
                        if self.tipg != g:
                            g.render_tip()
                            self.wait_for_tip = True
                            self.tipg = g
                            pygame.time.set_timer(USEREVENT+7, 1000)
                    if not tip_on:
                        self.tip_canvas = None
                elif event.type == USEREVENT+7:
                    pygame.time.set_timer(USEREVENT+7, 0)
                    self.toolbar.wait_for_tip = False
            if event.type == MOUSEBUTTONUP and event.button == 1:
                if g.label == "^":
                    if g.pointin((x,y), g.screenrect) and g.state == 1 and abs(g.value) == 1:
                        g.value = -g.value
                    g.state = 0
                    g.need_redraw = True
                    ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))

        else:
            ge.extend(super(PalGadget, self).process_event(screen, event, mouse_pixel_mapper))
        return ge

def init_toolbar(config_in):
    global config
    config = config_in

    scaleX = config.pixel_width // 320
    scaleY = config.pixel_height // 200
    scaledown = 4 // min(scaleX,scaleY)
    tools_image = imgload('tools.png', scaleX=scaleX, scaleY=scaleY, scaledown=scaledown)
    h = config.pixel_canvas.get_height()
    w = tools_image.get_width()//3
    toolbar_canvas = pygame.Surface((w,h),0)
    toolbar = Toolbar(toolbar_canvas, config.cursor, (0,0,tools_image.get_width()//3, tools_image.get_height()), tools_image, width=3)
    toolbar.add_grid((0,21*scaleY,tools_image.get_width()//3, tools_image.get_height()-21*scaleY), 2, 9, attr_list=[
        ["dot",      ToolGadget.TT_GROUP,  "s", DoDot],
        ["draw",     ToolGadget.TT_GROUP,  "dD", DoDraw],
        ["line",     ToolGadget.TT_GROUP,  "v V", DoLine],
        ["curve",    ToolGadget.TT_GROUP,  "q", DoCurve],
        ["fill",     ToolGadget.TT_GROUP,  "f F", DoFill],
        ["airbrush", ToolGadget.TT_GROUP,  "", DoAirbrush],
        ["rect",     ToolGadget.TT_GROUP,  "rR", DoRect],
        ["circle",   ToolGadget.TT_GROUP,  "cC", DoCircle],
        ["ellipse",  ToolGadget.TT_GROUP,  "eE", DoEllipse],
        ["poly",     ToolGadget.TT_GROUP,  "wW", DoPoly],
        ["brush",    ToolGadget.TT_GROUP,  "b", DoBrush],
        ["text",     ToolGadget.TT_GROUP,  "t", DoText],
        ["grid",     ToolGadget.TT_TOGGLE, "g", DoGrid],
        ["symm",     ToolGadget.TT_TOGGLE, "/", DoSymm],
        ["magnify",  ToolGadget.TT_TOGGLE, "m", DoMagnify],
        ["zoom",     ToolGadget.TT_SINGLE, "> <", DoZoom],
        ["undo",     ToolGadget.TT_SINGLE, "u U", DoUndo],
        ["clear",    ToolGadget.TT_SINGLE, "K", DoClear]
    ])

    toolbar.add_corner_list([
        ( 2*scaleX,2*scaleY,  5*scaleX, 8*scaleY, "circle1", ".", DoBIBrush),
        ( 5*scaleX,2*scaleY, 10*scaleX, 8*scaleY, "circle2", "", DoBIBrush),
        ( 9*scaleX,2*scaleY, 16*scaleX, 8*scaleY, "circle3", "", DoBIBrush),
        (15*scaleX,2*scaleY, 24*scaleX, 8*scaleY, "circle4", "", DoBIBrush),

        (19*scaleX,9*scaleY, 23*scaleX,12*scaleY, "square1", "", DoBIBrush),
        (14*scaleX,9*scaleY, 19*scaleX,13*scaleY, "square2", "", DoBIBrush),
        ( 8*scaleX,9*scaleY, 14*scaleX,14*scaleY, "square3", "", DoBIBrush),
        ( 2*scaleX,9*scaleY,  8*scaleX,15*scaleY, "square4", "", DoBIBrush),

        ( 4*scaleX,15*scaleY, 9*scaleX,19*scaleY, "spray1", "", DoBIBrush),
        (14*scaleX,13*scaleY,23*scaleX,20*scaleY, "spray2", "", DoBIBrush),
        ], tool_type=ToolGadget.TT_GROUP)

    toolbar.tools.append(PalGadget(Gadget.TYPE_CUSTOM, "%",
                         (0, tools_image.get_height(),
                          tools_image.get_width()//3,
                          10 * scaleY), id="swatch", toolbar=toolbar,
                          action=DoSwatch))
    toolbar.add_coords(toolbar.tool_id("swatch"))

    toolbar.tools.append(PalGadget(Gadget.TYPE_CUSTOM, "#",
                         (0, tools_image.get_height() + 10 * scaleY,
                          tools_image.get_width()//3,
                          config.pixel_canvas.get_height() - tools_image.get_height() - 20*scaleY), id="palette", toolbar=toolbar, action=DoPalette))
    toolbar.add_coords(toolbar.tool_id("palette"))

    return toolbar

#Demo of toolbar
def tool_mouse_map():
    x,y = pygame.mouse.get_pos()
    x //= 3
    y //= 3
    return (x,y)

def main():
    #Initialize the configuration settings
    pygame.init()
    clock = pygame.time.Clock()

    sx,sy = 200,200

    scaled_screen = pygame.display.set_mode((sx*3,sy*3), RESIZABLE)
    screen = pygame.Surface((sx,sy),0,8)
    toolbar_screen = pygame.Surface((sx,sy),0,8)
    cursor_images = pygame.image.load(os.path.join('data', 'cursors8.png'))
    cursor_layer = Cursor(cursor_images)
    cursor_layer.set_centers([(7,7), (1,1), (7,15), (0,15)])
    layer = Layer(screen, scaletype=1, sublayers=[Layer(toolbar_screen), cursor_layer])
    #Load toolbar image and scale it down
    surf_array = pygame.surfarray.pixels3d(pygame.image.load(os.path.join('data', 'tools.png')))
    scaled_array = surf_array[1::4, 1::4, ::]
    surf_array = None
    tools_image = pygame.surfarray.make_surface(scaled_array)

    scaleY = 1
    scaleX = 1
    mytoolbar = Toolbar(toolbar_screen, cursor_layer, (0,0,tools_image.get_width()//3, tools_image.get_height()), tools_image, width=3)
    mytoolbar.add_grid((0,22*scaleY,tools_image.get_width()//3, tools_image.get_height()-22*scaleY), 2, 9, attr_list=[
        ["dot",      ToolGadget.TT_GROUP,  "s"],
        ["draw",     ToolGadget.TT_GROUP,  "dD"],
        ["line",     ToolGadget.TT_GROUP,  "v V"],
        ["curve",    ToolGadget.TT_GROUP,  "q"],
        ["fill",     ToolGadget.TT_GROUP,  "f F"],
        ["airbrush", ToolGadget.TT_GROUP],
        ["rect",     ToolGadget.TT_GROUP,  "rR"],
        ["circle",   ToolGadget.TT_GROUP,  "cC"],
        ["ellipse",  ToolGadget.TT_GROUP,  "eE"],
        ["poly",     ToolGadget.TT_GROUP,  "wW"],
        ["brush",    ToolGadget.TT_GROUP,  "b"],
        ["text",     ToolGadget.TT_GROUP,  "t"],
        ["grid",     ToolGadget.TT_TOGGLE, "g", DoGrid],
        ["symm",     ToolGadget.TT_TOGGLE, "/"],
        ["magnify",  ToolGadget.TT_TOGGLE, "m"],
        ["zoom",     ToolGadget.TT_SINGLE, "> <"],
        ["undo",     ToolGadget.TT_SINGLE, "u U"],
        ["clear",    ToolGadget.TT_SINGLE, "K"]
    ])

    mytoolbar.add_corner_list([
        ( 2*scaleX,2*scaleY,  5*scaleX, 9*scaleY, "circle1", "."),
        ( 5*scaleX,2*scaleY, 10*scaleX, 9*scaleY, "circle2"),
        ( 9*scaleX,2*scaleY, 16*scaleX, 9*scaleY, "circle3"),
        (15*scaleX,2*scaleY, 24*scaleX, 9*scaleY, "circle4"),

        (19*scaleX,9*scaleY, 23*scaleX,13*scaleY, "square1"),
        (14*scaleX,9*scaleY, 19*scaleX,14*scaleY, "square2"),
        ( 8*scaleX,9*scaleY, 14*scaleX,15*scaleY, "square3"),
        ( 2*scaleX,9*scaleY,  8*scaleX,16*scaleY, "square4"),

        ( 4*scaleX,15*scaleY, 9*scaleX,20*scaleY, "spray1"),
        (14*scaleX,13*scaleY,23*scaleX,21*scaleY, "spray2"),
        ], tool_type=ToolGadget.TT_GROUP)

    mytoolbar.draw()

    pygame.display.set_caption('Toolbar Test')
    running = 1

    while running:
        
        #screen.fill((0,0,0))

        event = pygame.event.wait()
        if event.type == QUIT:
            running = 0

        #gevents = layer.process_event(screen, event)
        gevents = mytoolbar.process_event(screen, event, tool_mouse_map)

        mytoolbar.draw()
        #cursor_layer.offset = pygame.mouse.get_pos()
        layer.draw(scaled_screen)

        pygame.display.flip()
        #clock.tick(60)
        

if __name__ == '__main__': main()
