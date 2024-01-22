#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os.path

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import libs.pixelfont
from libs.pixelfont import PixelFont

import libs.gadget
from libs.gadget import *

from libs.palreq import *
from libs.toolreq import *

#Workaround for pygame timer bug:
#  https://github.com/pygame/pygame/issues/3128
#  https://github.com/pygame/pygame/pull/3062
TIMEROFF = int((2**31)-1)

class ToolGadget(Gadget):
    """This class abstracts a gadget representing a tool on a toolbar"""
    TT_GROUP = 0
    TT_TOGGLE = 1
    TT_SINGLE = 2
    TT_CUSTOM = 3
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None, toolbar=None, tool_type=TT_GROUP, has_subtool=True, hotkeys="", action=None):
        self.group_list = []
        self.tool_type = tool_type
        self.has_subtool = has_subtool
        self.toolbar = toolbar
        self.hotkeys = hotkeys
        if action == None:
            self.action = None
        else:
            self.action = action(id=id, gadget=self)

        super(ToolGadget, self).__init__(type, label, rect, value, maxvalue, id)

    def process_event(self, screen, event, mouse_pixel_mapper):
        ge = []
        return ge

    def render_tip(self, quadrant=0):
        """
        Render a tooltip into a canvas with speech bubble in quadrant.
        0=left, 1=bottom, 2=right, 3=top
        """
        if self.toolbar.tip_font_size != pygame.display.get_surface().get_height()//50:
            self.toolbar.tip_font_size = pygame.display.get_surface().get_height()//50
            self.toolbar.tip_title_font = pygame.font.Font(os.path.join('data', 'FreeSansBold.ttf'), self.toolbar.tip_font_size)
            self.toolbar.tip_font = pygame.font.Font(os.path.join('data', 'FreeSans.ttf'), self.toolbar.tip_font_size)
        title_font = self.toolbar.tip_title_font
        font = self.toolbar.tip_font
        if self.action != None and "get_tip" in dir(self.action):
            tip = self.action.get_tip()
            if tip != None:
                if len(tip) == 0:
                    self.toolbar.tip_canvas = None
                    return
                #size box
                wrect = title_font.size("W")
                lineheight = title_font.get_linesize()
                rect = title_font.size(tip[0])
                w = rect[0] + wrect[0] + 1
                h = rect[1] + wrect[1] + 1
                for line in tip[1:]:
                    rect = font.size(line)
                    w = max(w, rect[0] + wrect[0] + 1)
                    h += lineheight

                if quadrant == 0: #left
                    #box around text
                    box = (0,0,w,h-1)

                    #tail
                    tx = w-2
                    th = wrect[1]
                    ty = (h - th) // 2
                    tw = wrect[0]
                    triangle = [(tx,ty), (tx+tw, ty+(th//2)), (tx,ty+th)]
                    w += wrect[0]
                elif quadrant == 2: #right
                    #tail
                    tx = wrect[0]-1
                    th = wrect[1]
                    ty = (h - th) // 2
                    tw = wrect[0]
                    triangle = [(tx,ty), (tx-tw, ty+(th//2)), (tx,ty+th)]
                    w += wrect[0]

                    #box around text
                    box = (wrect[0]-2,0,w-wrect[0],h-1)
                elif quadrant in [1,3]: #bottom or top
                    h += wrect[1]

                #draw box
                tip_canvas = pygame.Surface((w,h),SRCALPHA)
                pygame.draw.rect(tip_canvas, (255,255,0), box)
                pygame.draw.rect(tip_canvas, (0,0,0), box, 2)

                #draw tail
                pygame.draw.polygon(tip_canvas, (255,255,0), triangle)
                pygame.draw.lines(tip_canvas, (0,0,0), False, triangle, 2)

                #draw text
                xo = wrect[0] // 2 + box[0]
                yo = wrect[1] // 2
                line_count=0
                for line in tip:
                    line_count += 1
                    if line_count == 1:
                        timg = title_font.render(line, True, (0,0,0), (255,255,0))
                    else:
                        timg = font.render(line, True, (0,0,0), (255,255,0))
                    rect = timg.get_size()
                    tip_canvas.blit(timg, (xo,yo))
                    yo += lineheight

                self.toolbar.tip_canvas = tip_canvas
                self.toolbar.tip_x = self.rect[0]
                self.toolbar.tip_y = self.rect[1] + (self.rect[3] // 2)

    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        xo,yo = offset
        dx = xo + self.rect[0]
        dy = yo + self.rect[1]
        w = self.rect[2]
        h = self.rect[3]
        if self.toolbar.width > 1:
            sx = self.toolbar.image.get_width() // self.toolbar.width * self.state + self.rect[0]
            sy = self.rect[1]
        else:
            sx = self.rect[0]
            sy = self.toolbar.image.get_height() // self.toolbar.height * self.state + self.rect[1]

        if self.state > 0:
            screen.blit(self.toolbar.image, (dx,dy), area=(sx,sy,w,h+1))

    def process_draw_event(self, screen, event):
        pass

class Toolbar:
    """This class abstracts a generic toolbar"""
    def __init__(self, screen, cursor, rect, image, width=1, height=1, offset=(0,0), tip_event=pygame.USEREVENT):
        self.screen = screen
        self.cursor = cursor
        self.rect = rect
        self.image = image
        self.width = width
        self.height = height
        self.offset = offset
        self.tip_event = tip_event
        self.tools = []
        self.hotkey_map = {}
        self.coord_map = {}
        self.wait_for_mouseup = [False, False, False, False]
        self.visible = True
        self.tip_font_size = 0
        self.tip_title_font = None
        self.tip_font = None
        self.tip_canvas = None
        self.tip_x = 0
        self.tip_y = 0
        self.tip_quadrant = 0
        self.wait_for_tip = False
        self.tipg = None

    def hash_coords(self, x, y):
        return "%dx_%dx" % (x//10,y//10)

    def add_coords(self, toolg):
        gx,gy,gw,gh = toolg.rect
        for x in range(gx,gx+gw+11,10):
            for y in range(gy,gy+gh+11,10):
                h = self.hash_coords(x,y)
                if h in self.coord_map:
                    self.coord_map[h].append(toolg)
                else:
                    self.coord_map[h] = [toolg]

    def get_tools_by_coords(self, x, y):
        h = self.hash_coords(x,y)
        if h in self.coord_map:
            return self.coord_map[h]
        else:
            return []

    def add_grid(self, rect, width, height, tool_type=ToolGadget.TT_GROUP, attr_list=None):
        xo,yo,w,h = rect
        count=0
        group_list = []
        for y in range(height):
            for x in range(width):
                gid = None
                hotkeys = ""
                action = None
                if attr_list != None and len(attr_list) >= count:
                    if len(attr_list[count]) > 0:
                        gid = attr_list[count][0]
                    if len(attr_list[count]) > 1:
                        tool_type = attr_list[count][1]
                    if len(attr_list[count]) > 2:
                        hotkeys = attr_list[count][2]
                    if len(attr_list[count]) > 3:
                        action = attr_list[count][3]
                toolg = ToolGadget(Gadget.TYPE_CUSTOM,"",
                                  (xo+(w//width)*x, yo+(h//height)*y,
                                   w//width, h//height),
                                   toolbar=self, tool_type=tool_type,
                                   id=gid, hotkeys=hotkeys, action=action)
                self.tools.append(toolg)
                self.add_coords(toolg)
                for i in range(len(hotkeys)):
                    if hotkeys[i] != " ":
                        self.hotkey_map[hotkeys[i]] = toolg
                if tool_type == ToolGadget.TT_GROUP:
                    group_list.append(toolg)
                count += 1

        for toolg in group_list:
            if toolg.tool_type == ToolGadget.TT_GROUP:
                toolg.group_list = group_list

    def add_corner_list(self, corner_list, tool_type=ToolGadget.TT_GROUP):
        group_list = []
        for corners in corner_list:
            rect = (corners[0], corners[1], corners[2]-corners[0], corners[3]-corners[1])
            gid = None
            action = None
            if len(corners) > 4:
                gid = corners[4]
            hotkeys = ""
            if len(corners) > 5:
                hotkeys = corners[5]
            if len(corners) > 6:
                action = corners[6]
            toolg = ToolGadget(Gadget.TYPE_CUSTOM,"", rect,
                               toolbar=self, tool_type=tool_type,
                               id=gid, hotkeys=hotkeys, action=action)
            self.tools.append(toolg)
            self.add_coords(toolg)
            group_list.append(toolg)
            for i in range(len(hotkeys)):
                if hotkeys[i] != " ":
                    self.hotkey_map[hotkeys[i]] = toolg

        if tool_type == ToolGadget.TT_GROUP:
            for toolg in group_list:
                toolg.group_list = group_list

    def draw(self, screen=None, font=None, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        if screen == None:
            screen = self.screen

        if not self.visible:
            return

        self.offset = offset
        self.screenrect = (self.rect[0]+offset[0],self.rect[1]+offset[1],self.rect[2],self.rect[3])
        screen.blit(self.image, offset, area=self.rect)
        for toolg in self.tools:
            if isinstance(toolg, ToolGadget) and toolg.tool_type != ToolGadget.TT_CUSTOM:
                if toolg.state != 0:
                    toolg.draw(screen, font, offset=offset)
            else:
                toolg.draw(screen, font, offset=offset, fgcolor=fgcolor, bgcolor=bgcolor, hcolor=hcolor)

    def tool_id(self, id):
        for g in self.tools:
            if g.id == id:
                return g
        return None

    def hide(self):
        pass

    def show(self):
        pass

    def is_inside(self, coords):
        if not "screenrect" in dir(self):
            return False
        if not self.visible:
            return False

        gx,gy,gw,gh = self.screenrect
        x, y = coords
        if x >= gx and y >= gy:
            return True
        else:
            return False

    def click(self, toolg, eventtype, subtool=False, rightclick=False):
        ge = []
        attrs = {"subtool":subtool, "rightclick":rightclick, "eventtype":eventtype}
        if toolg.tool_type == ToolGadget.TT_GROUP:
            if not rightclick:
                toolg.state = 2 if subtool else 1
            ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETDOWN, attrs, toolg))
            if toolg.action != None:
                toolg.action.selected(attrs)

        elif toolg.tool_type == ToolGadget.TT_TOGGLE:
            if rightclick:
                ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETDOWN, attrs, toolg))
                if toolg.action != None:
                    toolg.action.selected(attrs)
            elif toolg.state == 0:
                toolg.state = 1
                ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETDOWN, attrs, toolg))
                if toolg.action != None:
                    toolg.action.selected(attrs)
            else:
                toolg.state = 0
                ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, attrs, toolg))
                if toolg.action != None:
                    toolg.action.deselected(attrs)
        elif toolg.tool_type == ToolGadget.TT_SINGLE:
            toolg.state = 2 if subtool else 1
            ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETDOWN, attrs, toolg))
            if toolg.action != None:
                toolg.action.selected(attrs)

        toolg.need_redraw = True
        #print((toolg.id, toolg.tool_type, len(toolg.group_list), subtool, rightclick))

        if toolg.tool_type == ToolGadget.TT_GROUP and not rightclick:
            for g in toolg.group_list:
                if g != toolg and g.tool_type == ToolGadget.TT_GROUP and g.state != 0:
                    g.state = 0
                    ge.insert(0, GadgetEvent(GadgetEvent.TYPE_GADGETUP, None, g))
                    if g.action != None:
                        g.action.deselected(attrs)
        return ge

    def process_event(self, screen, event, mouse_pixel_mapper):
        ge = []
        rightclick = False
        x,y = mouse_pixel_mapper()
        x -= self.offset[0]
        y -= self.offset[1]
        if self.visible and event.type == MOUSEBUTTONDOWN and event.button in [1,3]:
            if event.button == 3:
                rightclick = True
            for toolg in self.get_tools_by_coords(x,y):
                if toolg.pointin((x,y), toolg.rect):
                    self.wait_for_mouseup[event.button] = True
                    if isinstance(toolg, ToolGadget) and toolg.tool_type != ToolGadget.TT_CUSTOM:
                        x1, y1, size, dummy = toolg.rect
                        subtool = False
                        if toolg.tool_type in [ToolGadget.TT_GROUP, ToolGadget.TT_SINGLE]:
                            if toolg.has_subtool:
                                if size-(x - x1) <= (y - y1):
                                    subtool = True
                        ge.extend(self.click(toolg, event.type, subtool=subtool, rightclick=rightclick))
                    else:
                        ge.extend(toolg.process_event(screen, event, mouse_pixel_mapper))
        elif (event.type == MOUSEBUTTONUP and event.button in [1,3]) or \
             event.type == KEYUP:
            if event.type == MOUSEBUTTONUP:
                self.wait_for_mouseup[event.button] = False
            for toolg in self.tools:
                if isinstance(toolg, ToolGadget) and toolg.tool_type == ToolGadget.TT_SINGLE and toolg.state > 0:
                    toolg.state = 0
                else:
                    ge.extend(toolg.process_event(screen, event, mouse_pixel_mapper))
        elif self.visible and event.type == MOUSEBUTTONDOWN and event.button in [4,5]:
            for toolg in self.get_tools_by_coords(x,y):
                if toolg.pointin((x,y), toolg.rect):
                    ge.extend(toolg.process_event(screen, event, mouse_pixel_mapper))
        elif event.type == KEYDOWN and \
             (event.unicode in self.hotkey_map or \
              event.key in self.hotkey_map):
            if event.unicode in self.hotkey_map:
                toolg = self.hotkey_map[event.unicode]
            else:
                toolg = self.hotkey_map[event.key]
            subtool = False
            if len(toolg.hotkeys) > 1 and event.unicode == toolg.hotkeys[1]:
                subtool = True
            elif len(toolg.hotkeys) > 2 and event.unicode == toolg.hotkeys[2]:
                rightclick = True
            ge.extend(self.click(toolg, event.type, subtool=subtool, rightclick=rightclick))
        elif self.visible and event.type == MOUSEMOTION:
            if True in self.wait_for_mouseup and \
               event.buttons == (0,0,0):
                self.wait_for_mouseup = [False, False, False, False]
            elif True in self.wait_for_mouseup:
                for toolg in self.get_tools_by_coords(x,y):
                    if not isinstance(toolg, ToolGadget):
                        ge.extend(toolg.process_event(screen, event, mouse_pixel_mapper))
            tip_on = False
            for toolg in self.get_tools_by_coords(x,y):
                if toolg.pointin((x,y), toolg.rect) and "render_tip" in dir(toolg):
                    tip_on = True
                    if self.tipg != toolg:
                        toolg.render_tip(self.tip_quadrant)
                        self.wait_for_tip = True
                        self.tipg = toolg
                        pygame.time.set_timer(self.tip_event, 1000)
            if not tip_on:
                self.tip_canvas = None
                self.tipg = None
        elif event.type == self.tip_event:
            pygame.time.set_timer(self.tip_event, TIMEROFF)
            self.wait_for_tip = False
        return ge

