#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os.path

import contextlib
with contextlib.redirect_stdout(None):
    import pygame, pygame.freetype
    from pygame.locals import *

import pixelfont
from pixelfont import PixelFont

import gadget
from gadget import *

from palreq import *
from toolreq import *

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
        0=right, 1=bottom, 2=left, 3=top
        """
        if self.toolbar.tip_font_size != pygame.display.get_surface().get_height()//50:
            self.toolbar.tip_font_size = pygame.display.get_surface().get_height()//50
            self.toolbar.tip_title_font = pygame.freetype.SysFont(pygame.freetype.get_default_font(), self.toolbar.tip_font_size, bold=True)
            self.toolbar.tip_font = pygame.freetype.SysFont(pygame.freetype.get_default_font(), self.toolbar.tip_font_size)
        title_font = self.toolbar.tip_title_font
        font = self.toolbar.tip_font
        if self.action != None and "get_tip" in dir(self.action):
            tip = self.action.get_tip()
            if tip != None:
                #size box
                wrect = title_font.get_rect("W")
                lineheight = title_font.get_rect("Wg")[1] + wrect.height // 2
                rect = title_font.get_rect(tip[0])
                w = rect.width + wrect.width + 1
                h = rect.height + wrect.height + 1
                for line in tip[1:]:
                    rect = font.get_rect(line)
                    w = max(w, rect.width + wrect.width + 1)
                    h += lineheight

                #box around text
                box = (0,0,w,h-1)
                
                if quadrant == 0: #right
                    #tail
                    tx = w-1
                    th = wrect.height
                    ty = (h - th) // 2
                    tw = wrect.width
                    triangle = [(tx,ty), (tx+tw, ty+(th//2)), (tx,ty+th)]
                    w += wrect.width
                elif quadrant in [0,2]: #right or left
                    w += wrect.width
                elif quadrant in [1,3]: #bottom or top
                    h += wrect.height

                #draw box
                tip_canvas = pygame.Surface((w,h),SRCALPHA)
                pygame.draw.rect(tip_canvas, (255,255,0), box)
                pygame.draw.rect(tip_canvas, (0,0,0), box, 2)

                #draw tail
                pygame.draw.polygon(tip_canvas, (255,255,0), triangle)
                pygame.draw.lines(tip_canvas, (0,0,0), False, triangle, 2)

                #draw text
                xo = wrect.width // 2
                yo = wrect.height // 2
                line_count=0
                for line in tip:
                    line_count += 1
                    if line_count == 1:
                        rect = title_font.render_to(tip_canvas, (xo,yo), line, fgcolor=(0,0,0), bgcolor=(255,255,0))
                    else:
                        rect = font.render_to(tip_canvas, (xo,yo), line, fgcolor=(0,0,0), bgcolor=(255,255,0))
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
    def __init__(self, screen, cursor, rect, image, width=1, height=1, offset=(0,0)):
        self.screen = screen
        self.cursor = cursor
        self.rect = rect
        self.image = image
        self.width = width
        self.height = height
        self.offset = offset
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

    def draw(self, screen=None, offset=(0,0)):
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
                    toolg.draw(screen, None, offset=offset)
            else:
                toolg.draw(screen, None, offset=offset)

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
                if toolg.tool_type == ToolGadget.TT_SINGLE and toolg.state > 0:
                    toolg.state = 0
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
            tip_on = False
            for toolg in self.get_tools_by_coords(x,y):
                if toolg.pointin((x,y), toolg.rect) and "render_tip" in dir(toolg):
                    tip_on = True
                    if self.tipg != toolg:
                        toolg.render_tip()
                        self.wait_for_tip = True
                        self.tipg = toolg
                        pygame.time.set_timer(USEREVENT+7, 1000)
            if not tip_on:
                self.tip_canvas = None
                self.tipg = None
        elif event.type == USEREVENT+7:
            pygame.time.set_timer(USEREVENT+7, 0)
            self.wait_for_tip = False
        return ge

"""
class toolbar:

    "This class renders the toolbar and handles its buttons"
    def __init__(self, screen, cursor, config):
        #load tools palette
        self.tool_selected = 1
        self.subtool_selected = 0

        self.toolbar_canvas = pygame.Surface(screen.get_size(),0, screen)
        self.pal = screen.get_palette()
        self.toolbar_canvas.set_palette(self.pal)
        self.screen = self.toolbar_canvas
        self.config = config
        toolreq_set_config(config)
        self.scaleX = screen.get_width()//320
        self.scaleY = screen.get_height()//200

        self.cursor = cursor
        self.font = PixelFont("jewel32.png", 8)

        #Load toolbar image and scale it down
        surf_array = pygame.surfarray.pixels3d(pygame.image.load(os.path.join('data', 'tools.png')))
        scaled_array = surf_array[1::4, 1::4, ::]
        surf_array = None
        self.tools_image = pygame.surfarray.make_surface(scaled_array)

        if self.scaleX != 1 or self.scaleY != 1:
            self.tools_image = pygame.transform.scale(self.tools_image, (self.tools_image.get_width()*self.scaleX, self.tools_image.get_height()*self.scaleY))
        self.tools_x = self.screen.get_width() - (self.tools_image.get_width()//3)
        self.tools_y = 11
        self.menutitle = "PyDPainter"
        self.menutitle_extra = ""
        self.menulist = "Picture Brush Mode Anim Effect Prefs"
        self.show_menus = False
        self.sl_icons_on = False
        self.sl_icons = pygame.image.load(os.path.join('data', 'scanline_icons.png'))
        self.sl_icon_state = [0,0,0,0,1]
        self.sl_EXPAND = 0
        self.sl_HELP = 1
        self.sl_ZOOM = 2
        self.sl_RASTER = 3
        self.sl_ASPECT = 4
        self.mousedown = False
        self.button1 = False
        self.button2 = False
        self.button3 = False
        self.zoom = 3
        self.zoom_on = False
        self.zoom_max = 8
        self.zoom_center = (50,50)
        self.zoom_pixel_rect = (0,0,0,0)
        self.zoom_left_rect = (0,0,0,0)
        self.zoom_border_rect = (0,0,0,0)
        self.zoom_right_rect = (0,0,0,0)
        self.zoom_xoffset = 0
        self.zoom_yoffset = 0
        self.zoom_mousedown_side = 0
        self.grid_on = False
        self.grid_size = (4,4)
        self.grid_offset = (2,2)
        self.symm_on = False
        self.symm_center = (160,100)
        self.symm_mode = 0
        self.symm_type = 0
        self.symm_num = 2
        self.symm_width = 50
        self.symm_height = 50
        self.menu_on = True
        self.menu_on_prev = False
        self.tools_on = True
        self.tools_on_prev = False
        self.inside = False
        self.palettearrows_image = pygame.image.load(os.path.join('data', 'palettearrows.png'))
        self.palette_page = 0
        self.color = 1
        self.bgcolor = 0
        self.palette_bounds = []
        self.brush_bounds = []
        self.brush_bounds.append(( 2*self.scaleX,2*self.scaleY,  5*self.scaleX, 9*self.scaleY, 1, 1))
        self.brush_bounds.append(( 5*self.scaleX,2*self.scaleY, 10*self.scaleX, 9*self.scaleY, 2, 1))
        self.brush_bounds.append(( 9*self.scaleX,2*self.scaleY, 16*self.scaleX, 9*self.scaleY, 3, 1))
        self.brush_bounds.append((15*self.scaleX,2*self.scaleY, 24*self.scaleX, 9*self.scaleY, 4, 1))

        self.brush_bounds.append((19*self.scaleX,9*self.scaleY, 23*self.scaleX,13*self.scaleY, 1, 2))
        self.brush_bounds.append((14*self.scaleX,9*self.scaleY, 19*self.scaleX,14*self.scaleY, 2, 2))
        self.brush_bounds.append(( 8*self.scaleX,9*self.scaleY, 14*self.scaleX,15*self.scaleY, 3, 2))
        self.brush_bounds.append(( 2*self.scaleX,9*self.scaleY,  8*self.scaleX,16*self.scaleY, 4, 2))

        self.brush_bounds.append(( 4*self.scaleX,15*self.scaleY, 9*self.scaleX,20*self.scaleY, 1, 3))
        self.brush_bounds.append((14*self.scaleX,13*self.scaleY,23*self.scaleX,21*self.scaleY, 2, 3))

        self.tool_bounds = []

        for i in range(0,9):
            self.tool_bounds.append(( 1*self.scaleX, (i*12 + 22)*self.scaleY, 11*self.scaleX+1, (i*12 + 32)*self.scaleY+1))
            self.tool_bounds.append((13*self.scaleX, (i*12 + 22)*self.scaleY, 23*self.scaleX+1, (i*12 + 32)*self.scaleY+1))

    def blit_toolbar(self, pixel_image):
        if self.menu_on:
            pixel_image.blit(self.screen, (0,0), (0,0, self.screen.get_width(), 12))
        if self.tools_on:
            pixel_image.blit(self.screen, (self.screen.get_width()-25*self.scaleX,0), (self.tools_x, 0, 25*self.scaleX, self.screen.get_height()))

    def select_tool(self, tool_selected, subtool_selected):
        if tool_selected >= len(self.tool_bounds):
            return

        x1,y1,x2,y2 = self.tool_bounds[tool_selected]
        x1o = x1
        y1o = y1
        x1 = (x1 + 25*self.scaleX*(subtool_selected+1))
        y1 = y1
        x2 = (x2 + 25*self.scaleX*(subtool_selected+1))
        y2 = y2
        self.screen.blit(self.tools_image, (self.tools_x+x1o, self.tools_y+y1o), (x1,y1, x2-x1,y2-y1))



    def draw(self):
        if self.menu_on:
            self.tools_y = 11

            pygame.draw.rect(self.screen, (255,255,255), (0,0, self.screen.get_width(), 11), 0)
            #textimg = self.font.render("PiedPainter Color", 0, (255,0,0))
            #self.screen.blit(textimg, (10,1))
            if self.show_menus:
                titlestring = self.menulist
            else:
                titlestring = self.menutitle + "  " + str(self.config.drawmode) + " " + self.menutitle_extra
            self.config.last_drawmode = self.config.drawmode

            self.font.blitstring(self.screen, (4,2), titlestring, (0,0,0), (255,255,255))
            pygame.draw.rect(self.screen, (0,0,0), (0,11, self.screen.get_width(), 1), 1)

            self.sl_icon_state[self.sl_EXPAND] = 1 if self.sl_icons_on else 0

            if self.sl_icons_on:
                if self.config.scanlines:
                    self.sl_icon_state[self.sl_RASTER] = 0
                else:
                    self.sl_icon_state[self.sl_RASTER] = 1

                for i in range(0, len(self.sl_icon_state)):
                    self.screen.blit(self.sl_icons, (self.screen.get_width()-1-(10*len(self.sl_icon_state))+i*10, 1), (10*i, 10*self.sl_icon_state[i], 10, 10))
            else:
                for i in range(0, 2):
                    self.screen.blit(self.sl_icons, (self.screen.get_width()-1-(10*2)+i*10, 1), (10*i, 10*self.sl_icon_state[i], 10, 10))
        elif self.menu_on_prev:
            self.tools_y = 0

        if self.tools_on:
            self.screen.blit(self.tools_image, (self.tools_x, self.tools_y), (0,0, 25*self.scaleX, 130*self.scaleY))

            for i in range(0,len(self.brush_bounds)):
                x1,y1,x2,y2,size,type = self.brush_bounds[i]
                if self.config.brush.type == type and self.config.brush.size == size:
                    x1o = x1
                    y1o = y1
                    x1 = (x1 + 25*self.scaleX*(self.subtool_selected+1))
                    y1 = y1
                    x2 = (x2 + 25*self.scaleX*(self.subtool_selected+1))
                    y2 = y2
                    self.screen.blit(self.tools_image, (self.tools_x+x1o, self.tools_y+y1o), (x1,y1, x2-x1,y2-y1))

            self.select_tool(self.tool_selected, self.subtool_selected)

            if self.zoom_on:
                self.select_tool(14, 0)

            if self.grid_on:
                self.select_tool(12, 0)

            if self.symm_on:
                self.select_tool(13, 0)

            #Draw current fg/bg color
            pygame.draw.rect(self.screen, (0,0,0), (self.tools_x,self.tools_y+129*self.scaleY,25*self.scaleX,200), 0)
            pygame.draw.rect(self.screen, self.bgcolor, (self.tools_x,self.tools_y+129*self.scaleY,25*self.scaleX,12*self.scaleY), 0)
            pygame.draw.rect(self.screen, self.color, (self.tools_x+6*self.scaleX,self.tools_y+(130+2)*self.scaleY,12*self.scaleX,6*self.scaleY), 0)

            # Draw color palette
            if self.color < self.palette_page * 32 or self.color >= (self.palette_page+1) * 32:
                self.palette_page = self.color // 32

            curcolor = self.palette_page * 32
            if self.config.NUM_COLORS >= 32:
                color_cols = 4
            elif self.config.NUM_COLORS == 16:
                color_cols = 2
            elif self.config.NUM_COLORS == 8:
                color_cols = 2
            elif self.config.NUM_COLORS <= 4:
                color_cols = 1
                
            colors_shown = 32
            if self.config.NUM_COLORS < colors_shown:
                colors_shown = self.config.NUM_COLORS

            color_rows = colors_shown // color_cols

            color_width = 24 // color_cols
            if self.config.NUM_COLORS > 32:
                color_height = 40 // color_rows
            else:
                color_height = 48 // color_rows

            color_width *= self.scaleX
            color_height *= self.scaleY

            self.palette_bounds = []
            for j in range(0,color_cols):
                for i in range(0,color_rows):
                    self.palette_bounds.append((1+j*color_width,(130+11)*self.scaleY+i*color_height,1+(j+1)*color_width,(130+11)*self.scaleY+(i+1)*color_height, curcolor))
                    pygame.draw.rect(self.screen, curcolor, (self.tools_x+1+j*color_width,self.tools_y+(130+11)*self.scaleY+i*color_height,color_width,color_height), 0)
                    if curcolor == self.color:
                        pygame.draw.rect(self.screen, (255,255,255), (self.tools_x+j*color_width,self.tools_y+(130+10)*self.scaleY+i*color_height,color_width+1,color_height+1), 1)
                    curcolor += 1

            if self.config.NUM_COLORS > 32:
                #draw palette arrows
                self.palette_bounds.append((1,181*self.scaleY,8,189*self.scaleY, -1))
                self.screen.blit(self.palettearrows_image, (self.tools_x+1,self.tools_y+181*self.scaleY), (8*8,0,8,8))
                self.screen.blit(self.palettearrows_image, (self.tools_x+1+8,self.tools_y+181*self.scaleY), (8*self.palette_page,0,8,8))
                self.palette_bounds.append((17,181*self.scaleY,24,189*self.scaleY, -2))
                self.screen.blit(self.palettearrows_image, (self.tools_x+1+16,self.tools_y+181*self.scaleY), (8*9,0,8,8))

        self.tools_on_prev = self.tools_on
        self.menu_on_prev = self.menu_on

    def is_inside(self, mouseX, mouseY):
        return (mouseY <= self.tools_y and self.menu_on) or (mouseX >= self.tools_x and self.tools_on)

    def process_event(self, event):
        mouseX, mouseY = self.config.get_mouse_pointer_pos(event)
        self.inside = self.is_inside(mouseX, mouseY)

        if event.type >= pygame.USEREVENT:
            return False

        processed = False
        shifted = (pygame.key.get_mods() & KMOD_SHIFT) > 0
        button1, button2, button3 = pygame.mouse.get_pressed()

        if event.type == MOUSEMOTION:
            button1, button2, button3 = event.buttons
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                button1 = True
            elif event.button == 2:
                button2 = True
            elif event.button == 3:
                button3 = True
        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:
                button1 = False
            elif event.button == 2:
                button2 = False
            elif event.button == 3:
                button3 = False
 
        self.button1 = button1
        self.button2 = button2
        self.button3 = button3

        if event.type == pygame.MOUSEBUTTONUP:
            #Eat mouse up if mouse down started in toolbar
            if self.mousedown:
                processed = True
                self.config.suppress_undo = True

            self.mousedown = False
        elif event.type == KEYDOWN and self.tool_selected == 11:
            if event.key == K_F10:
                if self.tools_on:
                    self.tools_on = False
                    self.menu_on = False
                else:
                    self.tools_on = True
                    self.menu_on = True
        elif event.type == KEYDOWN and self.tool_selected != 11:
            processed = True
            shifted = (event.mod & KMOD_SHIFT) > 0
            controlkey = (event.mod & KMOD_CTRL) > 0
            if not controlkey:
                if event.key == K_F9:
                    self.menu_on = not self.menu_on
                elif event.key == K_F10:
                    if self.tools_on:
                        self.tools_on = False
                        self.menu_on = False
                    else:
                        self.tools_on = True
                        self.menu_on = True
                elif event.key == K_d:
                    self.tool_selected = 1
                    self.subtool_selected = 0
                elif event.key == K_s:
                    self.tool_selected = 0
                    self.subtool_selected = 0
                elif event.key == K_v:
                    self.tool_selected = 2
                    self.subtool_selected = 0
                elif event.key == K_q:
                    self.tool_selected = 3
                    self.subtool_selected = 0
                elif event.key == K_f:
                    self.tool_selected = 4
                    self.subtool_selected = 0
                elif event.key == K_r:
                    self.tool_selected = 6
                    if shifted:
                        self.subtool_selected = 1
                    else:
                        self.subtool_selected = 0
                elif event.key == K_c:
                    self.tool_selected = 7
                    if shifted:
                        self.subtool_selected = 1
                    else:
                        self.subtool_selected = 0
                elif event.key == K_e:
                    self.tool_selected = 8
                    if shifted:
                        self.subtool_selected = 1
                    else:
                        self.subtool_selected = 0
                elif event.key == K_w:
                    self.tool_selected = 9
                    if shifted:
                        self.subtool_selected = 1
                    else:
                        self.subtool_selected = 0
                elif event.key == K_b:
                    self.tool_selected = 10
                    self.subtool_selected = 0
                elif event.key == K_t:
                    self.tool_selected = 11
                    self.subtool_selected = 0
                elif event.key == K_g:
                    self.tool_selected = 12
                    self.subtool_selected = 0
                elif event.key == K_SLASH:
                    self.tool_selected = 13
                    self.subtool_selected = 0
                elif event.key == K_m:
                    self.tool_selected = 14
                    self.subtool_selected = 0
                    if not self.zoom_on:
                        self.zoom_center = self.config.get_mouse_pixel_pos()
                elif event.key == K_n:
                    self.zoom_center = self.config.get_mouse_pixel_pos()
                elif event.key == K_UP:
                    if self.zoom_on:
                        cx,cy = self.zoom_center
                        self.zoom_center = (cx,cy-4)
                elif event.key == K_DOWN:
                    if self.zoom_on:
                        cx,cy = self.zoom_center
                        self.zoom_center = (cx,cy+4)
                elif event.key == K_LEFT:
                    if self.zoom_on:
                        cx,cy = self.zoom_center
                        self.zoom_center = (cx-4,cy)
                elif event.key == K_RIGHT:
                    if self.zoom_on:
                        cx,cy = self.zoom_center
                        self.zoom_center = (cx+4,cy)
                elif event.key == K_COMMA and shifted:
                    self.zoom -= 1
                    if self.zoom < 2:
                        self.zoom = 2
                elif event.key == K_PERIOD and shifted:
                    self.zoom += 1
                    if self.zoom > self.zoom_max:
                        self.zoom = self.zoom_max
                elif event.key == K_u:
                    self.tool_selected = 16
                    self.subtool_selected = 0
                elif event.key == K_k and shifted:
                    self.tool_selected = 17
                    self.subtool_selected = 0
                elif event.key == K_COMMA:
                    self.tool_selected = 20 #color picker
                elif event.key == K_RIGHTBRACKET:
                    if shifted:
                        self.bgcolor = (self.bgcolor + 1) % self.config.NUM_COLORS
                    else:
                        self.color = (self.color + 1) % self.config.NUM_COLORS
                elif event.key == K_LEFTBRACKET:
                    if shifted:
                        self.bgcolor = (self.bgcolor - 1) % self.config.NUM_COLORS
                    else:
                        self.color = (self.color - 1) % self.config.NUM_COLORS
                elif event.key == K_j:
                    if shifted:
                        pass
                    else:
                        self.config.pixel_canvas, self.config.pixel_spare_canvas = self.config.pixel_spare_canvas, self.config.pixel_canvas
                        self.config.clear_undo()
                elif event.key == K_p:
                    palette_req(self.config.pixel_req_canvas)
                else:
                    processed = False
            else:
                processed = False

        self.sl_icon_state[self.sl_ZOOM] = 0

        self.show_menus = False

        if mouseY <= self.tools_y and self.menu_on:
            self.cursor.shape = 1
            self.show_menus = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                processed = True
                self.mousedown = True
            elif event.type == pygame.MOUSEBUTTONUP:
                processed = True
                self.mousedown = False

                if self.sl_icons_on:
                    mouseX -= self.config.screen_width - len(self.sl_icon_state) * 10 - 1
                else:
                    mouseX -= self.config.screen_width - 2 * 10 - 1

                if mouseX > 0:
                    sl_tool = mouseX//10
                    if sl_tool <= len(self.sl_icon_state):
                        if sl_tool == self.sl_EXPAND:
                            self.sl_icons_on = not self.sl_icons_on
                        elif sl_tool == self.sl_ZOOM:
                            if 10-(mouseX-(10*self.sl_ZOOM)) > mouseY:
                                self.sl_icon_state[self.sl_ZOOM] = 1
                                self.config.scale += 1.0 / self.scaleY
                            else:
                                self.sl_icon_state[self.sl_ZOOM] = 2
                                self.config.scale -= 1.0 / self.scaleY
                                if self.config.scale < 1:
                                    self.config.scale = 1
                            self.config.window_size = (int(self.config.screen_width*self.config.scale*self.config.pixel_aspect), int(self.config.screen_height*self.config.scale))
                            self.config.screen = pygame.display.set_mode(self.config.window_size, RESIZABLE)
                        elif sl_tool == self.sl_RASTER:
                                self.config.scanlines = not self.config.scanlines
                        elif sl_tool == self.sl_ASPECT:
                            if self.sl_icon_state[self.sl_ASPECT] == 0:
                                self.sl_icon_state[self.sl_ASPECT] = 1
                                self.config.pixel_aspect = 10.0/11.0
                            elif self.sl_icon_state[self.sl_ASPECT] == 1:
                                self.sl_icon_state[self.sl_ASPECT] = 0
                                self.config.pixel_aspect = 1.0
                            self.config.window_size = (int(self.config.screen_width*self.config.scale*self.config.pixel_aspect), int(self.config.screen_height*self.config.scale))
                            self.config.screen = pygame.display.set_mode(self.config.window_size, RESIZABLE)

        elif mouseX >= self.tools_x and self.tools_on:
            mouseX -= self.tools_x
            mouseY -= self.tools_y

            self.cursor.shape = 1

            if event.type == pygame.MOUSEBUTTONDOWN:
                processed = True
                self.mousedown = True

                if mouseY <= 20*self.scaleY:
                    #Choose brush
                    for i in range(len(self.brush_bounds)):
                        x1,y1,x2,y2,size,type = self.brush_bounds[i]
                        if mouseX >= x1 and mouseX <= x2 and mouseY >= y1 and mouseY <= y2:
                            self.config.brush.size = size
                            self.config.brush.type = type
                            break
                elif mouseY < 130*self.scaleY:
                    #Choose tool
                    for i in range(len(self.tool_bounds)):
                        x1,y1,x2,y2 = self.tool_bounds[i]
                        if mouseX >= x1 and mouseX <= x2 and mouseY >= y1 and mouseY <= y2:
                            if event.type == MOUSEBUTTONDOWN:
                                tool = i
                                if 12*self.scaleX-(mouseX - x1) > (mouseY - y1):
                                    subtool = 0
                                else:
                                    subtool = 1
                                if event.button == 1:
                                    self.tool_selected = tool
                                    self.subtool_selected = subtool
                                elif event.button == 3:
                                    self.mousedown = False
                                    if tool in [2,3] or (tool in [6,7,8,9] and subtool == 0):
                                        spacing_req(self.config.pixel_req_canvas)
                                    elif tool in [4] or (tool in [1,6,7,8,9] and subtool == 1):
                                        fill_req(self.config.pixel_req_canvas)
                                    elif tool == 12: #Grid
                                        grid_req(self.config.pixel_req_canvas)
                                    elif tool == 13: #Symmetry
                                        symmetry_req(self.config.pixel_req_canvas)
                                if tool == 15: #Zoom out
                                    if event.button == 3:
                                        self.zoom -= 1
                                        if self.zoom < 2:
                                            self.zoom = 2
                elif mouseY < 142*self.scaleY:
                    #Color Picker
                    if button3:
                        palette_req(self.config.pixel_req_canvas)
                        self.mousedown = False
                    else:
                        self.tool_selected = 20
                else:
                    for i in range(len(self.palette_bounds)):
                        x1,y1,x2,y2,colorindex = self.palette_bounds[i]
                        if mouseX >= x1 and mouseX <= x2 and mouseY >= y1 and mouseY <= y2:
                            if colorindex == -1:
                                self.palette_page -= 1
                                self.color = (self.color - 32) % self.config.NUM_COLORS
                                if self.palette_page < 0:
                                    self.palette_page = self.config.NUM_COLORS // 32
                            elif colorindex == -2:
                                self.palette_page += 1
                                self.color = (self.color + 32) % self.config.NUM_COLORS
                                if self.palette_page > self.config.NUM_COLORS // 32:
                                    self.palette_page = 0
                            else:
                                if button1:
                                    self.color = colorindex
                                elif button3:
                                    self.bgcolor = colorindex
                            break
        else:
            self.cursor.shape = 0

        return processed
"""
