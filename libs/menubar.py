#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os.path

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import pixelfont
from pixelfont import PixelFont

import gadget
from gadget import *
from hotkey import *

from palreq import *
from menureq import *

class MenuItem(Gadget):
    """This class abstracts a menu item associated with a menubar"""
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None, menubar=None, hotkeys="", menubox=None, parent=None, action=None, hasCheck=False, checked=False, enabled=True):
        self.menubar = menubar
        self.hotkeys = hotkeys
        self.menubox = menubox
        self.parent = parent
        self.hasCheck = hasCheck
        self.checked = checked
        self.menug_list = []
        if action == None:
            self.action = None
        else:
            self.action = action(id=id, gadget=self)

        super(MenuItem, self).__init__(type, label, rect, value, maxvalue, id, enabled=enabled)

    def menu_id(self, id):
        notletter = re.compile('[^a-z]')
        sid = notletter.sub("", id.lower())
        for g in self.menug_list:
            if notletter.sub("", g.label.lower()) == sid:
                return g
        return None

    def process_event(self, screen, event, mouse_pixel_mapper):
        ge = []
        return ge

    def pointin(self, coords, rect):
        gx,gy,gw,gh = rect
        x, y = coords
        if x >= gx and x < gx+gw and \
           y >= gy and y < gy+gh:
            return True
        else:
            return False

    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(255,255,255), hcolor=(220,220,220)):
        xo,yo = offset
        dx = xo + self.rect[0]
        dy = yo + self.rect[1]
        w = self.rect[2]
        h = self.rect[3]
        tx = dx+(font.xsize//2)
        ty = dy+((h-font.ysize)//2)
        menuw = w
        rstr = ""
        rstrx = 0
        self.screenrect = (dx,dy,w,h)

        #if not self.need_redraw:
        #    return

        self.need_redraw = False

        if len(self.menug_list) > 0 and self.parent != None:
            rstr = chr(0xBB); #double right arrow
        if len(self.hotkeys) > 0:
            rstr = self.hotkeys
        if self.parent != None:
            menuw = self.parent.menubox[2]

        if len(rstr) > 0:
            rstrx = dx+menuw-(len(rstr)*font.xsize)-(font.xsize//2)

        if self.label == "---":
            pygame.draw.rect(screen, fgcolor, (dx, dy+(h/2), w, 1))
            return
        if self.state == 0 or not self.enabled:
            font.blitstring(screen, (tx,ty), self.label, fgcolor, bgcolor)
            font.blitstring(screen, (rstrx,ty), rstr, fgcolor, bgcolor)
            if self.hasCheck and self.checked:
                font.blitstring(screen, (tx-font.xsize-2,ty), "\x86\x87", fgcolor)
            x,y,w,h = self.rect
            xo, yo = offset
            self.offsetx = xo
            self.offsety = yo

            if not self.enabled:
                #cache fadesurf if possible
                if self.menubar.fadesurf == None or self.menubar.fadesurf.get_width() < w or self.menubar.fadesurf.get_height() < h:
                    self.menubar.fadesurf = pygame.Surface((w,h), SRCALPHA)
                    self.menubar.fadesurf.fill((bgcolor[0],bgcolor[1],bgcolor[2],76))
                    for i in range(0, w, 2):
                        for j in range(0, h+1, 4):
                            pygame.draw.rect(self.menubar.fadesurf, (bgcolor[0],bgcolor[1],bgcolor[2],180), (i,j,1,1), 0)
                    for i in range(1, w, 2):
                        for j in range(2, h+1, 4):
                            pygame.draw.rect(self.menubar.fadesurf, (bgcolor[0],bgcolor[1],bgcolor[2],180), (i,j,1,1), 0)
                screen.blit(self.menubar.fadesurf, self.screenrect, (0,0,w-4,h))
        elif self.state == 1:
            pygame.draw.rect(screen, hcolor, (dx, dy, w, h-1))
            font.blitstring(screen, (tx,ty), self.label, fgcolor, hcolor)
        elif self.state == 2:
            pygame.draw.rect(screen, fgcolor, (dx+1, dy, w-2, h))
            font.blitstring(screen, (tx,ty), self.label, bgcolor, fgcolor)
            font.blitstring(screen, (rstrx,ty), rstr, bgcolor, fgcolor)
            if self.hasCheck and self.checked:
                font.blitstring(screen, (tx-font.xsize-2,ty), "\x86\x87", bgcolor)
            if self.menubox != None:
                mbx,mby,mbw,mbh = self.menubox
                pygame.draw.rect(screen, fgcolor, (mbx-1,mby-1,mbw+2,mbh+2))
                pygame.draw.rect(screen, bgcolor, self.menubox)
            for g in self.menug_list:
                g.draw(screen, font)

    def process_draw_event(self, screen, event):
        pass

class Menubar:
    """This class abstracts a generic menubar"""
    def __init__(self, screen, rect, font, offset=(0,0)):
        self.screen = screen
        self.rect = rect
        self.font = font
        self.offset = offset
        self.menug_list = []
        self.hotkey_map = HotKeyMap()
        self.visible = True
        self.menus_on = False
        self.wait_for_mouseup = [False, False, False, False]
        self.title = ""
        self.title_extra = ""
        self.title_right = ""
        self.indicators = {}
        self.menulevel = 0
        self.need_redraw = True
        self.fadesurf = None
        self.hide_menus = False

    def add_indicator(self, name, renderer):
        self.indicators[name] = renderer

    def add_submenu(self, menug, menus):
        x,y,w,h = menug.rect
        xo = w

        self.menulevel += 1
        if self.menulevel == 1:
            xo = 0
            y += h

        y0 = y
        menug.menubox = [x+xo, y, 0, 0]
        y += 2
        for m in menus:
            enabled = True
            hasCheck = False
            checked = False
            action = None
            if m[0][0] == "!":
                m[0] = m[0][1:]
                enabled = False
            if m[0][0] == "/":
                m[0] = " " + m[0][1:]
                hasCheck = True
                checked = False
            elif m[0][0] == "\\":
                m[0] = " " + m[0][1:]
                hasCheck = True
                checked = True

            if len(m) > 1 and not type(m[1]) is list:
                hotkeys = m[1]
            else:
                hotkeys = ""

            if len(m) > 2:
                action = m[2]

            if action == None and not (len(m) > 1 and type(m[1]) is list):
                enabled = False

            hk = None
            if hotkeys != "":
                hk = HotKey(text=hotkeys,action=action)
                self.hotkey_map.add(hk)
                hotkeys = hk.toKeycaps()

            submenug = MenuItem(Gadget.TYPE_CUSTOM,m[0],(x+xo,y-1,(len(m[0])+1)*self.font.xsize, self.font.ysize+2), hotkeys=hotkeys, menubar=self, parent=menug, hasCheck=hasCheck, checked=checked, enabled=enabled, action=action)
            menug.menug_list.append(submenug)

            if hk != None:
                hk.gadget = submenug

            if action != None:
                hk.action.gadget = submenug

            if submenug.rect[2]+(len(hotkeys)+1)*self.font.xsize > menug.menubox[2]:
                menug.menubox[2] = submenug.rect[2]+(len(hotkeys)+1)*self.font.xsize
            if len(m) > 1 and type(m[1]) is list:
                #print(("  " * self.menulevel) + m[0] + " >")
                self.add_submenu(submenug, m[1])
            else:
                #print(("  " * self.menulevel) + m[0])
                pass
            y += self.font.ysize + 2
            menug.menubox[3] = y - y0
        self.menulevel -= 1
        for g in menug.menug_list:
            rx,ry,rw,rh = g.rect
            g.rect = (rx,ry,menug.menubox[2],rh)
            if g.menubox != None:
                g.menubox[0] = rx+menug.menubox[2]
                for g2 in g.menug_list:
                    rx2,ry2,rw2,rh2 = g2.rect
                    g2.rect = (rx+menug.menubox[2],ry2,rw2,rh2)

        xdiff = 0
        #if menu off left side of screen, reposition back on
        if menug.menubox[0] < 2:
            xdiff = 2 - menug.menubox[0]
        #if menu off right side of screen, reposition back on
        else:
            xdiff = self.screen.get_width() - (menug.menubox[0] + menug.menubox[2] + 2)
            if xdiff > 0:
                xdiff = 0
        #do menu repositioning
        if xdiff != 0:
            menug.menubox[0] += xdiff
            for g in menug.menug_list:
                rx,ry,rw,rh = g.rect
                rx += xdiff
                g.rect = (rx,ry,rw,rh)
                if g.menubox != None:
                    g.menubox[0] += xdiff
                    for g2 in g.menug_list:
                        rx,ry,rw,rh = g2.rect
                        rx += xdiff
                        g2.rect = (rx,ry,rw,rh)

        #reposition submenus
        xdiff = 0
        for g in menug.menug_list:
            if g.menubox != None:
                xdiff = self.screen.get_width() - (g.menubox[0] + g.menubox[2] + 2)
                if xdiff > 0:
                    xdiff = 0
                if xdiff != 0:
                    g.menubox[0] += xdiff
                    for g2 in g.menug_list:
                        rx,ry,rw,rh = g2.rect
                        rx += xdiff
                        g2.rect = (rx,ry,rw,rh)

    def add_menu(self, menus):
        x,y,w,h = self.rect
        xo = 0

        if len(self.menug_list) > 0:
            xo = self.menug_list[-1].rect[0] + self.menug_list[-1].rect[2] + 1
        menu_text = menus[0]
        if len(menus) > 2:
            action = menus[2]
        else:
            action = None
        menug = MenuItem(Gadget.TYPE_CUSTOM,menu_text,(x+xo,y,(len(menu_text)+1)*self.font.xsize, h), menubar=self, action=action)
        self.menug_list.append(menug)
        if len(menus) > 1:
            self.add_submenu(menug, menus[1])

    def draw(self, screen=None, offset=None, fgcolor=(0,0,0), bgcolor=(255,255,255)):
        if screen == None:
            screen = self.screen
        if offset == None:
            offset = self.offset
        xo, yo = offset
        x,y,w,h = self.rect
        self.screenrect = (x+xo,y+yo,w,h)

        if not self.visible:
            return

        self.need_redraw = False

        pygame.draw.rect(screen, bgcolor, self.screenrect)
        pygame.draw.rect(screen, fgcolor, (x+xo,y+yo+h-1,w,1))
        if self.menus_on:
            for mg in self.menug_list:
                mg.draw(screen, self.font)
            #redraw submenus over parent menu items
            for g in self.menug_list:
                if g.state == 2 and g.menubox != None:
                    for g2 in g.menug_list:
                        if g2.state == 2 and g2.menubox != None:
                            g2.draw(screen, self.font)
        else:
            titlestring = self.title + " " + self.title_extra
            self.font.blitstring(screen, (xo+(self.font.xsize//2), yo+((h-self.font.ysize)//2)), titlestring, fgcolor, bgcolor)
            if len(self.title_right) > 0:
                trw = self.font.xsize * (len(self.title_right) + 2)
                self.font.blitstring(screen, (xo+w-(self.font.xsize//2)-trw, yo+((h-self.font.ysize)//2)), self.title_right, fgcolor, bgcolor)
            for key in self.indicators:
                renderer = self.indicators[key]
                renderer(screen)

    def menu_id(self, id):
        notletter = re.compile('[^a-z]')
        sid = notletter.sub("", id.lower())
        for g in self.menug_list:
            if notletter.sub("", g.label.lower()) == sid:
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
        if x >= gx and y >= gy and x < gx+gw and y < gy+gh:
            return True
        else:
            return False

    def click(self, toolg, eventtype, subtool=False, rightclick=False):
        ge = []
        toolg.state = 2
        toolg.need_redraw = True
        return ge

    def process_event(self, screen, event, mouse_pixel_mapper):
        ge = []
        rightclick = False
        x,y = mouse_pixel_mapper()
        #x -= self.offset[0]
        #y -= self.offset[1]
        if self.visible and event.type == MOUSEBUTTONDOWN and event.button in [1,3]:
            if event.button == 3:
                rightclick = True
            if self.is_inside((x,y)):
                self.menus_on = True
                for mg in self.menug_list:
                    if mg.pointin((x,y), mg.screenrect):
                        mg.state = 2
                    else:
                        mg.state = 0
            for menug in self.menug_list:
                if menug.pointin((x,y), menug.rect):
                    self.wait_for_mouseup[event.button] = True
                    if isinstance(menug, MenuItem):
                        x1, y1, w, h = menug.rect
                        ge.extend(self.click(menug, event.type))
                    else:
                        ge.extend(menug.process_event(screen, event, mouse_pixel_mapper))
        elif (event.type == MOUSEBUTTONUP and event.button in [1,3]) or \
             event.type == KEYUP:
            if event.type == MOUSEBUTTONUP:
                self.wait_for_mouseup[event.button] = False
                self.menus_on = False
                attrs = {}
                for menug in self.menug_list:
                    if menug.state == 2:
                        menug.state = 0
                        if menug.enabled:
                            attrs["menu1"] = menug
                        for menug2 in menug.menug_list:
                            if menug2.state == 2:
                                menug2.state = 0
                                if menug2.enabled:
                                    attrs["menu2"] = menug2
                                for menug3 in menug2.menug_list:
                                    if menug3.state == 2:
                                        menug3.state = 0
                                        if menug3.enabled:
                                            attrs["menu3"] = menug3
                if "menu1" in attrs and attrs["menu1"].action != None:
                    attrs["menu1"].action.selected(attrs)
                    ge.extend("menu1")
                if "menu2" in attrs and attrs["menu2"].action != None:
                    attrs["menu2"].action.selected(attrs)
                    ge.extend("menu2")
                if "menu3" in attrs and attrs["menu3"].action != None:
                    attrs["menu3"].action.selected(attrs)
                    ge.extend("menu3")
        elif event.type == KEYDOWN:
            self.hotkey_map.press(event)
        elif event.type == MOUSEMOTION:
            if event.buttons == (0,0,0):
                self.wait_for_mouseup = [False, False, False, False]
            if not self.hide_menus and self.is_inside((x,y)) and event.buttons == (0,0,0):
                self.menus_on = True
                for mg in self.menug_list:
                    if mg.pointin((x,y), mg.screenrect):
                        mg.state = 1
                    else:
                        mg.state = 0
            elif self.is_inside((x,y)) and True in self.wait_for_mouseup:
                self.menus_on = True
                for mg in self.menug_list:
                    if mg.pointin((x,y), mg.screenrect):
                        mg.state = 2
                    else:
                        mg.state = 0
            elif True in self.wait_for_mouseup:
                for mg in self.menug_list:
                    if mg.state == 2:
                        for smg in mg.menug_list:
                            inssm = False
                            if smg.state == 2:
                                for ssmg in smg.menug_list:
                                    if ssmg.pointin((x,y), ssmg.screenrect):
                                        ssmg.state = 2
                                        inssm = True
                                    else:
                                        ssmg.state = 0
                            if not inssm and smg.pointin((x,y), smg.screenrect):
                                smg.state = 2
                            elif not inssm:
                                smg.state = 0
            else:
                self.menus_on = False
        return ge

