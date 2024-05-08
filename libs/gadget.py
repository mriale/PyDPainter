#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#gadget.py
"""
gadget.py
Library for clickable buttons and sliders on the screen

Boolean (or button) gadgets
Proportional gadgets (slider)
String gadgets
Custom gadgets

                      vert sliders
text1:  ___________    | |
text2:  ___________    | |
slider: -----------    | |

buttons: [OK]  [Cancel]
button group: [A~B~C~D~E~F]
"""

import os.path
import re

import pygame
from pygame.locals import *

import libs.pixelfont
from libs.pixelfont import *

#Workaround for pygame timer bug:
#  https://github.com/pygame/pygame/issues/3128
#  https://github.com/pygame/pygame/pull/3062
TIMEROFF = int((2**31)-1)

fonty = 12
fontx = 8

def imgload(filename, scaleX=0, scaleY=0, scaledown=1):
    imagex1 = pygame.image.load(os.path.join('data', filename))
    ox,oy = imagex1.get_size()

    if scaledown == 1:
        return imagex1
    elif scaledown == 2 or scaledown == 4:
        #convert image to arrays for scaling
        surf_array = pygame.surfarray.array3d(imagex1)
        surf_array_alpha = pygame.surfarray.array_alpha(imagex1)

        #scale image down either by 2 or 4
        if scaledown == 2:
            #scale image up in X if needed
            if scaleX != 0 and scaleX > scaleY:
                scaled_array = surf_array[0::1, 0::2, ::]
                scaled_array_alpha = surf_array_alpha[0::1, 0::2]
            #scale image up in Y if needed
            elif scaleY != 0 and scaleY > scaleX:
                scaled_array = surf_array[0::2, 0::1, ::]
                scaled_array_alpha = surf_array_alpha[0::2, 0::1]
            else:
                scaled_array = surf_array[0::2, 0::2, ::]
                scaled_array_alpha = surf_array_alpha[0::2, 0::2]
        else:
            #scale image up in X if needed
            if scaleX != 0 and scaleX > scaleY:
                scaled_array = surf_array[1::2, 1::4, ::]
                scaled_array_alpha = surf_array_alpha[1::2, 1::4]
            #scale image up in Y if needed
            elif scaleY != 0 and scaleY > scaleX:
                scaled_array = surf_array[1::4, 1::2, ::]
                scaled_array_alpha = surf_array_alpha[1::4, 1::2]
            else:
                scaled_array = surf_array[1::4, 1::4, ::]
                scaled_array_alpha = surf_array_alpha[1::4, 1::4]

        #unlock original bitmap
        surf_array = None
        surf_array_alpha = None

        #convert array back into image and add alpha placeholder
        display =  pygame.display.get_surface()
        if display == None:
             pygame.display.set_mode((10,10))
        imagexx = pygame.surfarray.make_surface(scaled_array).convert_alpha()

        #copy over scaled alpha component
        imagexx_array_alpha = pygame.surfarray.pixels_alpha(imagexx)
        imagexx_array_alpha[::,::] = scaled_array_alpha[::,::]
        imagexx_array_alpha = None

        return imagexx
    else:
        return imagex1

"""
Actions for gadgets and tools
"""
class Action(object):
    def __init__(self, id=None, gadget=None):
        self.id = id
        self.gadget = gadget

    def selected(self, attrs):
        pass

    def deselected(self, attrs):
        pass

    def move(self, coords):
        pass

    def mousedown(self, coords, button):
        pass

    def drag(self, coords, buttons):
        pass

    def mouseup(self, coords, button):
        pass

    def keydown(self, key, mod, unicode):
        return False

    def keyup(self, key, mod):
        return False


class GadgetEvent(object):
    TYPE_GADGETDOWN, TYPE_GADGETUP, TYPE_MOUSEMOVE, TYPE_KEY = range(4)
    typearray = ['TYPE_GADGETDOWN', 'TYPE_GADGETUP', 'TYPE_MOUSEMOVE', 'TYPE_KEY']

    def __init__(self, type, event, gadget):
        self.type = type
        self.gadget = gadget
        self.event = event

    def __repr__(self):
        return "type={} gadgetid={} gadgettype={} event={}".format(self.typearray[self.type], self.gadget.id, self.gadget.typearray[self.gadget.type], self.event)

class Gadget(object):
    TYPE_BOOL, TYPE_IMAGE, TYPE_PROP, TYPE_PROP_VERT, TYPE_STRING, TYPE_CUSTOM, TYPE_LABEL = range(7)
    typearray = ['TYPE_BOOL', 'TYPE_IMAGE', 'TYPE_PROP', 'TYPE_PROP_VERT', 'TYPE_STRING', 'TYPE_CUSTOM', 'TYPE_LABEL']

    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None, enabled=True):
        self.type = type
        self.label = label
        self.rect = rect
        self.screenrect = rect
        self.screenrect2 = rect
        self.visible = False
        self.state = 0
        self.pos = 0
        self.scrollpos = 0
        self.value = value
        self.maxvalue = maxvalue
        self.id = id
        self.enabled = enabled
        self.offsetx = 0
        self.offsety = 0
        self.numonly = False
        self.fontx = fontx
        self.fonty = fonty
        self.fonth = int(fonty / 1.5)
        self.error = False
        self.scrolldelta = 1
        self.need_redraw = True
        if value == None:
            if type == self.TYPE_PROP or type == self.TYPE_PROP_VERT:
                self.value = 0
            elif type == self.TYPE_STRING:
                self.value = ""
        if maxvalue == None:
            if type == self.TYPE_PROP or type == self.TYPE_PROP_VERT:
                self.maxvalue = 100
            elif type == self.TYPE_STRING:
                self.maxvalue = 1
        if id == None:
            self.id = str(rect[0]) + "_" + str(rect[1])

    def coords2prop(self, coords):
        x,y,w,h = self.screenrect
        mousex, mousey = coords
        if self.type == Gadget.TYPE_PROP:
            value = (mousex-x) * (self.maxvalue-1) // (w-fontx)
            if value < 0:
                return 0
            elif value >= self.maxvalue:
                return self.maxvalue - 1
            else:
                return value
        elif self.type == Gadget.TYPE_PROP_VERT:
            value = (h-mousey+y) * (self.maxvalue-1) // (h-fontx)
            if value < 0:
                return 0
            elif value >= self.maxvalue:
                return self.maxvalue - 1
            else:
                return value

    def coords2char(self, coords):
        x,y,w,h = self.screenrect
        mousex, mousey = coords
        if self.type == Gadget.TYPE_STRING:
            value = ((mousex-x) // self.fontx) + self.scrollpos
            if value < 0:
                return 0
            elif value >= len(self.value):
                return len(self.value)
            else:
                return value

    def pointin(self, coords, rect):
        gx,gy,gw,gh = rect
        x, y = coords
        if x >= gx and x < gx+gw and \
           y >= gy and y <= gy+gh:
            return True
        else:
            return False

    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo
        self.screenrect = (x+xo,y+yo,w,h)
        self.fontx = font.xsize
        self.fonty = int(font.ysize * 1.5)
        self.fonth = font.ysize
        if not self.need_redraw:
            return

        self.need_redraw = False
        screen.set_clip(self.screenrect)

        px = self.fontx//8
        py = self.fonth//8

        if self.type == Gadget.TYPE_BOOL:
            strw = font.calcwidth(self.label)
            strxo = (w - strw) // 2
            srx,sry,srw,srh = self.screenrect
            if self.state == 1:
                pygame.draw.rect(screen, hcolor, self.screenrect, 0)
                pygame.draw.rect(screen, bgcolor, (srx+px,sry+py,srw-px-px,srh-py-py), 0)
                font.blitstring(screen, (x+xo+(strxo)+px,y+yo+py+py), self.label, fgcolor, bgcolor)
                pygame.draw.rect(screen, fgcolor, (x+xo,y+yo, w-px, py), 0)
                pygame.draw.rect(screen, fgcolor, (x+xo,y+yo, px, h), 0)
            else:
                pygame.draw.rect(screen, fgcolor, self.screenrect, 0)
                pygame.draw.rect(screen, bgcolor, (srx+px,sry+py,srw-px-px,srh-py-py), 0)
                font.blitstring(screen, (x+xo+(strxo),y+yo+py), self.label, fgcolor, bgcolor)
                pygame.draw.rect(screen, hcolor, (x+xo,y+yo, w-px, py), 0)
                pygame.draw.rect(screen, hcolor, (x+xo,y+yo, px, h), 0)
        elif self.type == Gadget.TYPE_PROP:
            propo = px
            if self.maxvalue-1 != 0:
                propo = (w-self.fontx-px) * self.value // (self.maxvalue-1) + px
            self.screenrect2 = (x+xo+propo, y+yo, self.fontx, h)
            diamond = ((propo+x+xo+(self.fontx//2)-px, y+yo+py+py+py),
                       (propo+x+xo+(self.fontx)-(3*px), y+yo+(self.fonth//2)+py),
                       (propo+x+xo+(self.fontx//2)-px, y+yo+self.fonth-py),
                       (propo+x+xo+px, y+yo+(self.fonth//2)+py))
            rectx,recty,rectw,recth = self.screenrect

            if self.state == 1:
                pygame.draw.rect(screen, fgcolor, (rectx+px,recty+py+py,rectw-px-px,recth-4*py), 0)
                pygame.draw.polygon(screen, hcolor, diamond, 0)
            else:
                pygame.draw.rect(screen, fgcolor, (rectx+px,recty+py+py,rectw-px-px,recth-4*py), 0)
                pygame.draw.polygon(screen, bgcolor, diamond, 0)
                pygame.draw.line(screen, hcolor, diamond[3], diamond[0])
        elif self.type == Gadget.TYPE_PROP_VERT:
            propo = 0
            if self.maxvalue-1 != 0:
                propo = (h-self.fonth) * (self.maxvalue-1-self.value) // (self.maxvalue-1)
            diamond = ((x+xo+(self.fontx//2)-px,y+yo+py+py+propo),
                       (x+xo+w-(3*px), y+yo+(self.fonth//2)+propo),
                       (x+xo+(self.fontx//2)-px,y+yo+self.fonth-py-py+propo),
                       (x+xo+px, y+yo+(self.fonth//2)+propo))
            self.screenrect2 = (x+xo+px, y+yo+py+propo, self.fontx, self.fonth)
            if self.state == 1:
                pygame.draw.rect(screen, fgcolor, (x+xo,y+yo+py,w-px,h-py), 0)
                pygame.draw.polygon(screen, hcolor, diamond, 0)
            else:
                pygame.draw.rect(screen, fgcolor, (x+xo,y+yo+py,w-px,h-py), 0)
                pygame.draw.polygon(screen, bgcolor, diamond, 0)
            pygame.draw.line(screen, hcolor, diamond[3], diamond[0])
        elif self.type == Gadget.TYPE_STRING:
            srx,sry,srw,srh = self.screenrect
            strxo = 0
            pygame.draw.rect(screen, hcolor, self.screenrect, 0)
            pygame.draw.rect(screen, bgcolor, (srx+px,sry+py,srw-px-px,srh-py-py), 0)
            font.blitstring(screen, (x+xo+px,y+yo+py+py), self.value[self.scrollpos:], fgcolor, bgcolor)
            pygame.draw.rect(screen, fgcolor, (x+xo,y+yo, w-px, py), 0)
            pygame.draw.rect(screen, fgcolor, (x+xo,y+yo, px, h), 0)
            if self.state != 0:
                if self.pos < len(self.value):
                    c = self.value[self.pos]
                else:
                    c = " "
                font.blitstring(screen, (x+xo+px+((self.pos-self.scrollpos)*self.fontx),y+yo+py+py), c, hcolor, (255,0,0))
            if self.numonly:
                if not re.fullmatch(r'^-?\d*\.?\d+$', self.value):
                    #numeric error
                    self.error = True
                else:
                    self.error = False
            if self.error:
                font.blitstring(screen, (x+xo+w-self.fontx-px,y+yo+py+py), "!", hcolor, (255,0,0))
        elif self.type == Gadget.TYPE_LABEL:
            font.blitstring(screen, (x+xo,y+yo+2), self.label, fgcolor, bgcolor)
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

        screen.set_clip(None)

    def process_event(self, screen, event, mouse_pixel_mapper):
        ge = []
        if (event.type == MOUSEMOTION or event.type == MOUSEBUTTONDOWN or event.type == MOUSEBUTTONUP) and hasattr(event, "newpos"):
            x,y = event.newpos
        else:
            x,y = mouse_pixel_mapper()
        g = self

        #disabled gadget
        if not g.enabled:
            return ge

        #not selected
        if g.state == 0:
            if g.pointin((x,y), g.screenrect):
                #handle left button
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if g.type == Gadget.TYPE_BOOL:
                        g.need_redraw = True
                        g.state = 1
                    elif g.type == Gadget.TYPE_PROP or g.type == Gadget.TYPE_PROP_VERT:
                        if g.pointin((x,y), g.screenrect2):
                            newvalue = g.coords2prop((x,y))
                            if g.value != newvalue:
                                g.value = newvalue
                            g.need_redraw = True
                            g.state = 1
                            ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETDOWN, event, g))
                        elif g.coords2prop((x,y)) < g.value:
                            g.need_redraw = True
                            g.value -= 1
                            ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
                        elif g.coords2prop((x,y)) > g.value:
                            g.need_redraw = True
                            g.value += 1
                            ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
                    elif g.type == Gadget.TYPE_STRING:
                        g.need_redraw = True
                        g.state = 1
                        g.pos = g.coords2char((x,y))
                        ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETDOWN, event, g))
                    elif g.type == Gadget.TYPE_LABEL:
                        g.state = 1
                        ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETDOWN, event, g))
                #handle scroll up
                elif event.type == MOUSEBUTTONDOWN and event.button == 4 and \
                     g.type in [Gadget.TYPE_PROP, Gadget.TYPE_PROP_VERT]:
                        if g.value + self.scrolldelta <= g.maxvalue-1 and \
                           g.value + self.scrolldelta >= 0:
                            g.need_redraw = True
                            g.value += self.scrolldelta
                            ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
                #handle scroll down
                elif event.type == MOUSEBUTTONDOWN and event.button == 5 and \
                     g.type in [Gadget.TYPE_PROP, Gadget.TYPE_PROP_VERT]:
                        if g.value - self.scrolldelta <= g.maxvalue-1 and \
                           g.value - self.scrolldelta >= 0:
                            g.need_redraw = True
                            g.value -= self.scrolldelta
                            ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))

        #selected
        if g.state == 1:
            if g.type == Gadget.TYPE_BOOL:
                if not g.pointin((x,y), g.screenrect):
                    g.need_redraw = True
                    g.state = 2
                elif event.type == MOUSEBUTTONUP and event.button == 1:
                    g.need_redraw = True
                    g.state = 0
                    ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
            elif g.type == Gadget.TYPE_PROP or g.type == Gadget.TYPE_PROP_VERT:
                newvalue = g.coords2prop((x,y))
                if g.value != newvalue:
                    g.need_redraw = True
                    g.value = newvalue
                    ge.append(GadgetEvent(GadgetEvent.TYPE_MOUSEMOVE, event, g))
                if event.type == MOUSEBUTTONUP and event.button == 1:
                    g.need_redraw = True
                    g.state = 0
                    ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
            elif g.type == Gadget.TYPE_STRING:
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if g.pointin((x,y), g.screenrect):
                        g.need_redraw = True
                        g.pos = g.coords2char((x,y))
                    else:
                        g.need_redraw = True
                        g.state = 0
                        ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
                elif event.type == KEYDOWN:
                    g.need_redraw = True
                    ge.append(GadgetEvent(GadgetEvent.TYPE_KEY, event, g))
                    hi_pos = g.scrollpos + (g.screenrect[2] // fontx) - 1
                    if event.key == K_RIGHT:
                        if self.pos < len(self.value):
                            self.pos += 1
                    elif event.key == K_LEFT:
                        if self.pos > 0:
                            self.pos -= 1
                    elif event.key == K_HOME:
                        self.pos = 0
                    elif event.key == K_END:
                        self.pos = len(self.value)
                    elif event.key == K_BACKSPACE:
                        if self.pos > 0:
                            self.value = self.value[:self.pos-1] + self.value[self.pos:]
                            self.pos -= 1
                    elif event.key == K_DELETE:
                        if self.pos < len(self.value):
                            self.value = self.value[:self.pos] + self.value[self.pos+1:]
                    elif event.key == K_RETURN or event.key == K_KP_ENTER or event.key == K_ESCAPE:
                        self.state = 0
                        ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
                        """
                    elif event.key == K_c and event.mod & KMOD_CTRL:
                        pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)
                        pygame.scrap.put(pygame.SCRAP_TEXT, self.value.encode("utf-8"))
                    elif event.key == K_v and event.mod & KMOD_CTRL:
                        text = None
                        for t in pygame.scrap.get_types():
                            if "text" in t and pygame.scrap.get(t) != None:
                                text = pygame.scrap.get(t).decode("utf-8")
                        if text != None:
                            self.value = self.value[:self.pos] + text + self.value[self.pos:]
                            self.pos += len(text)
                        """
                    elif len(event.unicode) == 1 and ord(event.unicode) >= 32 and ord(event.unicode) < 128:
                        if len(g.value) < self.maxvalue:
                            self.value = self.value[:self.pos] + event.unicode + self.value[self.pos:]
                            self.pos += 1

                    if self.pos > hi_pos:
                        self.scrollpos = self.pos - (g.screenrect[2] // fontx) + 1
                    elif self.pos < self.scrollpos:
                        self.scrollpos = self.pos
            elif g.type == Gadget.TYPE_LABEL:
                g.state = 0
                ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                g.need_redraw = True
                g.state = 0
                ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))

        #handle misc states
        if g.state == 2:
            if g.type == Gadget.TYPE_BOOL:
                #selected but mouse not in it
                if g.pointin((x,y), g.screenrect):
                    g.need_redraw = True
                    g.state = 1
                if event.type == MOUSEBUTTONUP and event.button == 1:
                    g.need_redraw = True
                    g.state = 0

        return ge

class ListGadget(Gadget):
    L_ITEMS, L_UP, L_DOWN, L_SLIDER = range(4)

    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        self.listgadgets = None
        if label == "^":
            scaleX = rect[2] // 16
            scaleY = rect[3] // 8
            arrowcoords = np.array([[16,32], [32,16], [20,16], [20,0], [12,0], [12,16], [0,16]])
            self.arrowdown = arrowcoords * np.array([scaleX/4,scaleY/4])
            self.arrowup = (arrowcoords - np.array([0,32])) * np.array([scaleX/4,-scaleY/4])

            value = 0
        elif label == "#":
            self.items = []
            self.top_item = 0
        elif label == "@":
            self.sliderrect = (0,0,0,0)
            self.clicky = None
        super(ListGadget, self).__init__(type, label, rect, value, maxvalue, id)

    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo
        self.screenrect = (x+xo,y+yo,w,h)
        px = font.xsize//8
        py = font.ysize//8
        self.fontx = font.xsize
        self.fonty = int(font.ysize * 1.5)
        self.fonth = font.ysize

        if self.type == Gadget.TYPE_CUSTOM:
            if not self.need_redraw:
                return

            self.need_redraw = False
            #List text
            if self.label == "#":
                screen.set_clip(self.screenrect)
                pygame.draw.rect(screen, bgcolor, self.screenrect, 0)
                numlines = h//font.ysize
                self.numlines = numlines
                topi = self.top_item
                if topi < 0:
                    topi = 0
                elif topi > len(self.items)-numlines:
                    topi = max(0, len(self.items)-numlines)
                self.top_item = topi

                for i in range(topi, topi+numlines):
                    fg = fgcolor
                    bg = bgcolor
                    if i < len(self.items):
                        if i == self.value: #highlight current
                            fg = bgcolor
                            bg = fgcolor
                        font.blitstring(screen, (x+xo+2*px,y+yo+2*py+(i-topi)*font.ysize), self.items[i], fg, bg)
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

                if self.value == 1:
                    pygame.draw.polygon(screen, fgcolor, self.arrowdown + np.array([x+xo+4*px,y+yo+py]))
                elif self.value == -1:
                    pygame.draw.polygon(screen, fgcolor, self.arrowup + np.array([x+xo+4*px,y+yo+py]))

            #List slider
            elif self.label == "@":
                numlines = self.listgadgets[self.L_ITEMS].screenrect[3] // font.ysize
                self.maxvalue = max(0, len(self.listgadgets[self.L_ITEMS].items) - numlines)
                if self.value < 0:
                    self.value = 0
                elif self.value > self.maxvalue:
                    self.value = self.maxvalue
                if self.maxvalue > 0:
                    sh = min(max(h * numlines // len(self.listgadgets[self.L_ITEMS].items), font.ysize//2), h-2*py)
                    so = (h-2*py-sh) * self.value // self.maxvalue
                else:
                    sh = h-2*py
                    so = 0
                pygame.draw.rect(screen, fgcolor, (x+xo+px,y+yo,w-px,h), 0)
                self.sliderrect = (x+xo+3*px,y+yo+py+so,w-5*px,sh)
                if self.state == 0:
                    pygame.draw.rect(screen, bgcolor, self.sliderrect, 0)
                else:
                    pygame.draw.rect(screen, hcolor, self.sliderrect, 0)
        else:
            super(ListGadget, self).draw(screen, font, offset)

    def scroll_delta(self, delta):
        self.listgadgets[self.L_ITEMS].top_item += delta
        self.listgadgets[self.L_ITEMS].need_redraw = True
        self.listgadgets[self.L_SLIDER].value += delta
        self.listgadgets[self.L_SLIDER].need_redraw = True

    def process_event(self, screen, event, mouse_pixel_mapper):
        ge = []
        x,y = mouse_pixel_mapper()
        g = self
        gx,gy,gw,gh = g.screenrect
        px = self.fontx//8
        py = self.fonty//12

        #disabled gadget
        if not g.enabled:
            return ge

        if self.type == Gadget.TYPE_CUSTOM:
            if g.pointin((x,y), g.screenrect):
                #handle left button
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    #List up/down arrows
                    if g.label == "^":
                        g.state = 1
                        g.need_redraw = True
                        pygame.time.set_timer(USEREVENT, 500)
                    #List text
                    elif g.label == "#":
                        item = (self.numlines * (y-gy-py-py) // (self.numlines * self.fonth)) + self.top_item
                        if item >= len(g.items):
                            item = len(g.items) - 1
                        if item < 0:
                            item = 0
                        g.value = item
                        g.need_redraw = True
                        ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
                    #List slider
                    elif g.label == "@":
                        #drag slider
                        if g.pointin((x,y), g.sliderrect):
                            self.clicky = y - g.sliderrect[1]
                            self.state = 1
                            self.need_redraw = True
                        #page up
                        elif y < g.sliderrect[1]:
                            g.scroll_delta(-g.listgadgets[self.L_ITEMS].numlines)
                        elif y > g.sliderrect[1] + g.sliderrect[3]:
                            g.scroll_delta(g.listgadgets[self.L_ITEMS].numlines)

                #handle mouse wheel
                elif event.type == MOUSEBUTTONDOWN and event.button in [4,5]:
                    #scroll up
                    if event.button == 4:
                        g.scroll_delta(-1)
                    #scroll down
                    elif event.button == 5:
                        g.scroll_delta(1)

            if (event.type == MOUSEBUTTONUP and event.button == 1) or \
               event.type == USEREVENT:
                #List up/down arrows
                if g.label == "^":
                    if g.pointin((x,y), g.screenrect) and g.state == 1:
                        if g.value == -1:
                            g.scroll_delta(-1)
                        elif g.value == 1:
                            g.scroll_delta(1)
                    if event.type == USEREVENT:
                        pygame.time.set_timer(USEREVENT, 100)
                    else:
                        pygame.time.set_timer(USEREVENT, TIMEROFF)
                        g.state = 0
                        g.need_redraw = True
                        ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
                elif g.label == "@" and event.type == MOUSEBUTTONUP:
                    g.clicky = None
                    g.state = 0
                    g.need_redraw = True
            elif (event.type == MOUSEMOTION and event.buttons[0]):
                if g.label == "@" and self.clicky is not None:
                    deltay = y-self.clicky-self.screenrect[1]
                    if self.maxvalue > 0:
                        h = self.screenrect[3]
                        sh = self.sliderrect[3]
                        self.value = (deltay) * self.maxvalue // (h-sh)
                        self.need_redraw = True
                        self.listgadgets[self.L_ITEMS].top_item = self.value
                        self.listgadgets[self.L_ITEMS].need_redraw = True
                    else:
                        self.value = 0
            elif (event.type == KEYDOWN):
                if g.label == "#":
                    numlines = self.screenrect[3] // self.fonth
                    if event.key == K_DOWN:
                        self.value += 1
                        if self.value > len(self.items)-1:
                            self.value = len(self.items)-1
                        if self.value > self.top_item + numlines - 1:
                            self.scroll_delta(1)
                        self.need_redraw = True
                    elif event.key == K_UP:
                        self.value -= 1
                        if self.value < 0:
                            self.value = 0
                        if self.value < self.top_item:
                            self.scroll_delta(-1)
                        self.need_redraw = True
                    elif event.key == K_PAGEDOWN:
                        self.value += numlines
                        if self.value > len(self.items)-1:
                            self.value = len(self.items)-1
                        self.scroll_delta(numlines)
                        self.need_redraw = True
                    elif event.key == K_PAGEUP:
                        self.value -= numlines
                        if self.value < 0:
                            self.value = 0
                        self.scroll_delta(-numlines)
                        self.need_redraw = True
        else:
            ge.extend(super(ListGadget, self).process_event(screen, event, mouse_pixel_mapper))
        return ge


class Requestor(object):
    def __init__(self, label, rect, mouse_pixel_mapper=pygame.mouse.get_pos, fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224), font=None):
        self.label = label
        self.rect = rect
        self.mouse_pixel_mapper = mouse_pixel_mapper
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.hcolor = hcolor
        self.draggable = False
        self.dragpos = None
        self.gadgets = []
        if font == None:
            self.font = PixelFont("jewel32.png", 8)
        else:
            self.font = font

        self.fontx = self.font.xsize
        self.fonty = int(self.font.ysize * 1.5)
        self.need_redraw = True
        x,y,w,h = self.rect
        if self.label != "":
            self.gadgets.append(Gadget(Gadget.TYPE_LABEL, "", (x-2, y-2, w+1, self.fonty), id="__reqtitle"))

    def add(self, gadget):
        self.gadgets.append(gadget)

    def process_event(self, screen, event):
        ge = []
        for g in self.gadgets:
            ge.extend(g.process_event(screen, event, self.mouse_pixel_mapper))

        if self.label != "" and self.draggable:
            x,y = self.mouse_pixel_mapper()
            #handle title bar click
            for i in range(len(ge)):
                if ge[i].gadget.id == "__reqtitle":
                    if ge[i].type == GadgetEvent.TYPE_GADGETDOWN:
                        self.dragpos = (x-self.rect[0],y-self.rect[1])
                        ge[i].gadget.value = 1

            g = self.gadget_id("__reqtitle")
            if g.value == 1:
                if event.type == MOUSEBUTTONUP and event.button == 1:
                    g.value = 0
                self.rect = (x-self.dragpos[0], y-self.dragpos[1], self.rect[2], self.rect[3])
                self.need_redraw = True

        #handle tab on string fields
        if event.type == KEYDOWN and event.key == K_TAB:
            found = False
            glist = None
            if event.mod & KMOD_SHIFT:
                glist = self.gadgets[::-1]
            else:
                glist = self.gadgets
            for g in glist:
                if g.type == Gadget.TYPE_STRING:
                    if not found and g.state == 1 and g.type == Gadget.TYPE_STRING:
                        found = True
                        g.state = 0
                    elif found:
                        g.state = 1
                        g.pos = len(g.value)
                        g.need_redraw = True
                        break

        return ge

    def has_error(self):
        for g in self.gadgets:
            if g.error:
                return True
        return False

    def get_screen_rect(self):
        x,y,w,h = self.rect
        return((x-3,y-3,w+6,h+4))

    def center(self, screen):
        (rx,ry,rw,rh) = self.rect
        (sw,sh) = screen.get_size()
        rx = (sw-rw) // 2
        ry = (sh-rh) // 2
        self.rect = (rx,ry,rw,rh)

    def draw(self, screen, offset=(0,0)):
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo

        if self.need_redraw:
            self.need_redraw = False
            pygame.draw.rect(screen, self.fgcolor, (x+xo-3,y+yo-3,w+6,h+4), 0)
            pygame.draw.rect(screen, self.bgcolor, (x+xo-2,y+yo-2,w+4,h+2), 0)
            if self.label != "":
                cx = (w - (len(self.label) * self.fontx)) // 2
                self.font.blitstring(screen, (x+xo+cx,y+yo), self.label, self.fgcolor, self.bgcolor)
                #draw highlight
                pygame.draw.line(screen, self.hcolor, (x+xo-2, y+yo-2), (x+xo+w+1, y+yo-2))
                pygame.draw.line(screen, self.hcolor, (x+xo-2, y+yo-2), (x+xo-2, y+yo+self.fonty-4))
                #draw dividing line
                pygame.draw.line(screen, self.fgcolor, (x+xo-2, y+yo+self.fonty-3), (x+xo+w+1, y+yo+self.fonty-3))
                pygame.draw.line(screen, self.hcolor, (x+xo-2, y+yo+self.fonty-2), (x+xo+w+1, y+yo+self.fonty-2))
            for g in self.gadgets:
                g.need_redraw = True

        for g in self.gadgets:
            g.draw(screen, self.font, (x+xo, y+yo), self.fgcolor, self.bgcolor, self.hcolor)

    def is_inside(self, coords):
        gx,gy,gw,gh = self.rect
        gx += self.offsetx
        gy += self.offsety
        x, y = coords
        if x >= gx and y >= gy and x <= gx+gw and y <= gy+gh:
            return True
        else:
            return False

    def gadget_id(self, id):
        for g in self.gadgets:
            if g.id == id:
                return g
        return None

def str2req(title, reqstring, custom="", mouse_pixel_mapper=pygame.mouse.get_pos, custom_gadget_type=Gadget, font=None):
    #Split into lines
    reqlines = reqstring.splitlines()

    #Remove first line if nothing on it
    if len(reqlines) > 0 and len(reqlines[0].strip()) == 0:
        reqlines = reqlines[1:]

    if font == None:
        fontx = 8
        fonty = 12
    else:
        fontx = font.xsize
        fonty = int(font.ysize * 1.5)

    #Find X/Y size
    yo = 0
    ysize = len(reqlines) * fonty
    if title != "":
        yo = fonty
        ysize += yo
    maxlen = 0
    for line in reqlines:
        linelen = len(line)
        if linelen > 0 and line[linelen-1] == "]":
            linelen -= 1
        if linelen > maxlen:
            maxlen = linelen
    xsize = maxlen * fontx

    for lineno in range(0,len(reqlines)):
        if len(reqlines[lineno]) < maxlen:
            reqlines[lineno] += " " * (maxlen - len(reqlines[lineno]))

    #print("xsize = {}, ysize = {}".format(xsize, ysize))
    req = Requestor(title, (0,0, xsize,ysize), mouse_pixel_mapper=mouse_pixel_mapper, font=font)

    #Find buttons
    for lineno in range(0,len(reqlines)):
        line = reqlines[lineno]
        bstart = line.find("[")
        bend = line.find("]")
        while bend > bstart and bstart >= 0 and bend >= 0:
            text = line[bstart+1:bend]
            #print("{} - lineno={} bstart={} bend={}".format(text, lineno, bstart, bend))
            bgroup_text = text.split("~")
            bgroup_len = 0
            for s in bgroup_text:
                req.add(Gadget(Gadget.TYPE_BOOL, s, ((bstart+bgroup_len)*fontx,yo+lineno*fonty, (len(s)+1)*fontx,fonty-1), id=str(bstart+bgroup_len)+"_"+str(lineno)))
                bgroup_len += len(s) + 1
            if bstart == 0:
                reqlines[lineno] = (" " * (bend-bstart+1)) + reqlines[lineno][bend+1:]
            else:
                reqlines[lineno] = reqlines[lineno][:bstart] + (" " * (bend-bstart+1)) + reqlines[lineno][bend+1:]
            bstart = line.find("[",bend)
            bend = line.find("]",bstart)

    #Find horizontal sliders
    for lineno in range(0,len(reqlines)):
        line = reqlines[lineno]
        bstart = line.find("-")
        bend = bstart + 1
        while bstart >= 0:
            while bend < len(line) and line[bend] == "-":
                bend += 1
            bend -= 1

            if bstart == 0:
                reqlines[lineno] = (" " * (bend-bstart+1)) + reqlines[lineno][bend+1:]
            else:
                reqlines[lineno] = reqlines[lineno][:bstart] + (" " * (bend-bstart+1)) + reqlines[lineno][bend+1:]

            req.add(custom_gadget_type(Gadget.TYPE_PROP, "-", (bstart*fontx,yo+lineno*fonty, (bend-bstart+1)*fontx,fonty-1), maxvalue=(bend-bstart+1)*2, id=str(bstart)+"_"+str(lineno)))
            #print("slider lineno={} bstart={} bend={}".format(lineno, bstart, bend))
            bstart = line.find("-", bend+1)
            bend = bstart + 1

    #Find vertical sliders
    for lineno in range(0,len(reqlines)):
        line = reqlines[lineno]
        col = line.find("|")
        while col >= 0:
            lstart = lineno
            lend = lineno
            while lend < len(reqlines) and reqlines[lend][col] == "|":
                if col == 0:
                    reqlines[lend] = " " + reqlines[lend][col+1:]
                else:
                    reqlines[lend] = reqlines[lend][:col] + " " + reqlines[lend][col+1:]
                lend += 1

            lend -= 1
            req.add(custom_gadget_type(Gadget.TYPE_PROP_VERT, "|", (col*fontx,yo+lstart*fonty, fontx,(lend-lstart+1)*fonty-1), maxvalue=(lend-lstart+1)*2, id=str(col)+"_"+str(lstart)))
            #print("vert slider col={} lstart={} lend={}".format(col, lstart, lend))
            col = line.find("|", col+1)

    #Find string gadgets
    for lineno in range(0,len(reqlines)):
        line = reqlines[lineno]
        bstart = line.find("_")
        bend = bstart + 1
        while bstart >= 0:
            while bend < len(line) and line[bend] == "_":
                bend += 1
            bend -= 1

            if bstart == 0:
                reqlines[lineno] = (" " * (bend-bstart+1)) + reqlines[lineno][bend+1:]
            else:
                reqlines[lineno] = reqlines[lineno][:bstart] + (" " * (bend-bstart+1)) + reqlines[lineno][bend+1:]

            req.add(custom_gadget_type(Gadget.TYPE_STRING, "-", (bstart*fontx,yo+lineno*fonty, (bend-bstart+1)*fontx,fonty-1), maxvalue=bend-bstart, id=str(bstart)+"_"+str(lineno)))
            #print("slider lineno={} bstart={} bend={}".format(lineno, bstart, bend))
            bstart = line.find("_", bend+1)
            bend = bstart + 1

    #Find custom chars
    for i in range(0,len(custom)):
        c = custom[i]
        #print("custom c={}".format(c))
        for lineno in range(0,len(reqlines)):
            line = reqlines[lineno]
            col = line.find(c)
            while col >= 0:
                #print("custom col={}".format(col))
                lstart = lineno
                colend = col
                while colend < len(line) and line[colend] == c:
                    if colend == 0:
                        reqlines[lineno] = " " + reqlines[lineno][colend+1:]
                    else:
                        reqlines[lineno] = reqlines[lineno][:colend] + " " + reqlines[lineno][colend+1:]
                    colend += 1
                colend -= 1
                lend = lineno + 1
                #print("custom lend={} reqlines[lend][col]={}".format(lend, reqlines[lend][col]))
                while lend < len(reqlines) and reqlines[lend][col] == c:
                    #print("custom lend={}".format(lend))
                    if col == 0:
                        reqlines[lend] = (" "*(colend+1)) + reqlines[lend][colend+1:]
                    else:
                        reqlines[lend] = reqlines[lend][:col] + (" "*(colend-col+1)) + reqlines[lend][colend+1:]
                    lend += 1

                req.add(custom_gadget_type(Gadget.TYPE_CUSTOM, c, (col*fontx,yo+lstart*fonty, (colend-col+1)*fontx,(lend-lstart)*fonty-1), id=str(col)+"_"+str(lstart)))
                #print(e"custom c={} col={} colend={} lstart={} lend={}".format(c, col, colend, lstart, lend))
                col = line.find(c, colend+1)

    #Find remaining text
    for lineno in range(0,len(reqlines)):
        line = reqlines[lineno].rstrip()
        tstart = 0
        while tstart < len(line):
            while tstart < len(line) and line[tstart] == " ":
                tstart += 1
            tend = tstart
            while tend < len(line) and line[tend] != " ":
                tend += 1
            tend -= 1
            text = line[tstart:tend+1]

            req.add(custom_gadget_type(Gadget.TYPE_LABEL, text, (tstart*fontx,yo+lineno*fonty, len(text)*fontx,fonty-1), id=str(tstart)+"_"+str(lineno)))
            tstart = tend + 1

    #for line in reqlines:
    #    print("'" + line + "'")

    return req

