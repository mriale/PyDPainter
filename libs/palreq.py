#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os.path, colorsys

import gadget
from gadget import *

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

config = None

def palreq_set_config(config_in):
    global config
    config = config_in

palette_page = 0

class PPGadget(Gadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        if label == "^":
            scaleX = rect[2] // 16
            scaleY = rect[3] // 8
            scaledown = 4 // min(scaleX,scaleY)
            self.crng_arrows = imgload('crng_arrows.png', scaleX=scaleX, scaleY=scaleY, scaledown=scaledown)
            value = 0
        super(PPGadget, self).__init__(type, label, rect, value, maxvalue, id)

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

            if self.label == ":":
                #Draw vertical rule marks
                for i in range(0,16):
                    ticlen = config.fontx
                    if i%4 == 0:
                        ticlen = config.fontx-1
                    elif i%2 == 0:
                        ticlen = config.fontx//2 - 1 
                    else:
                        ticlen = config.fontx//4 - 1
                    propo = (h-config.fontx) * (16-1-i) // (16-1)
                    ticstart = (config.fontx-ticlen) // 2
                    pygame.draw.line(screen, fgcolor, (x+xo+ticstart,y+yo+(config.fontx//2)+propo), (x+xo+ticstart+ticlen-1, y+yo+(config.fontx//2)+propo))
                    pygame.draw.line(screen, hcolor, (x+xo+ticstart,y+yo+1+(config.fontx//2)+propo), (x+xo+ticstart+ticlen-1, y+yo+1+(config.fontx//2)+propo))
            elif self.label == "#":
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
                color_height = int(round(h*1.0 / color_rows))

                if self.value == None:
                    self.value = 1

                screen.set_clip(self.screenrect)
                curcolor = palette_page
                self.palette_bounds = []
                for j in range(0,color_cols):
                    for i in range(0,color_rows):
                        self.palette_bounds.append((x+xo+1+j*color_width,y+yo+1+i*color_height,color_width-1,color_height, curcolor))
                        pygame.draw.rect(screen, config.pal[curcolor], (x+xo+1+j*color_width,y+yo+1+i*color_height,color_width-1,color_height), 0)
                        if curcolor == self.value:
                            if x+xo+j*color_width+color_width+1 < x+xo+w: #fits in gadget
                                pygame.draw.rect(screen, (255,255,255), (x+xo+j*color_width,y+yo+i*color_height,color_width+1,color_height+2), 1)
                            else:
                                pygame.draw.rect(screen, (255,255,255), (x+xo+j*color_width,y+yo+i*color_height,color_width,color_height+2), 1)
                        if curcolor == self.value+1 and i > 0:
                            pygame.draw.rect(screen, (255,255,255), (x+xo+j*color_width,y+yo+1+(i)*color_height,color_width,1), 1)
                        if config.cranges[current_range].low != \
                           config.cranges[current_range].high:
                            if curcolor >= config.cranges[current_range].low and \
                               curcolor <= config.cranges[current_range].high:
                                pygame.draw.rect(screen, (255,255,255), (x+xo+j*color_width,y+yo+1+i*color_height,1,color_height), 1)
                            if curcolor == config.cranges[current_range].low:
                                pygame.draw.rect(screen, (255,255,255), (x+xo+j*color_width,y+yo+i*color_height,color_width//2,1), 1)
                            if curcolor == config.cranges[current_range].high:
                                pygame.draw.rect(screen, (255,255,255), (x+xo+j*color_width,y+yo+1+(i+1)*color_height,color_width//2,1), 1)
                            if curcolor == config.cranges[current_range].high + 1 and i > 0:
                                pygame.draw.rect(screen, (255,255,255), (x+xo+j*color_width,y+yo+1+(i)*color_height,color_width//2,1), 1)
                        curcolor += 1
                #fill in remaining line at bottom of palette
                pygame.draw.line(screen, bgcolor, (x+xo,y+yo+h-1), (x+xo+w,y+yo+h-1))
                screen.set_clip(None)

            elif self.label == "%": # color swatch
                if self.value != None:
                    pygame.draw.rect(screen, config.pal[self.value], self.screenrect, 0)
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
            super(PPGadget, self).draw(screen, font, offset)

    def process_event(self, screen, event, mouse_pixel_mapper):
        global palette_page
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
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if g.label == "#":
                        for i in range(len(self.palette_bounds)):
                            x1,y1,x2,y2,colorindex = self.palette_bounds[i]
                            if x >= x1 and x <= x1+x2-1 and y >= y1 and y <= y1+y2-1:
                                g.need_redraw = True
                                g.value = colorindex
                                ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
                    elif g.label == "^":
                        g.state = 1
                        g.need_redraw = True
            if event.type == MOUSEBUTTONUP and event.button == 1:
                if g.label == "^":
                    if g.pointin((x,y), g.screenrect) and g.state == 1:
                        if abs(g.value) == 1:
                            g.value = -g.value
                        elif g.value == -2:
                            palette_page -= 32
                            if palette_page < 0:
                                palette_page = 0
                        elif g.value == 2:
                            palette_page += 32
                            if palette_page >= config.NUM_COLORS:
                                palette_page = config.NUM_COLORS - 32
                    g.state = 0
                    g.need_redraw = True
                    ge.append(GadgetEvent(GadgetEvent.TYPE_GADGETUP, event, g))
        else:
            ge.extend(super(PPGadget, self).process_event(screen, event, mouse_pixel_mapper))
        return ge

def get_rgb_sliders(rg, gg, bg):
    if config.color_depth == 16:
        return (rg.value * 17, gg.value * 17, bg.value * 17)
    else:
        return (rg.value, gg.value, bg.value)

def set_rgb_sliders(rgb, rg, gg, bg):
    if config.color_depth == 16:
        rg.value = rgb[0] // 16
        gg.value = rgb[1] // 16
        bg.value = rgb[2] // 16
    else:
        rg.value = rgb[0]
        gg.value = rgb[1]
        bg.value = rgb[2]

    rg.need_redraw = True
    gg.need_redraw = True
    bg.need_redraw = True

def get_hsv_sliders(hg, sg, vg):
    if config.color_depth == 16:
        r,g,b = colorsys.hsv_to_rgb(hg.value/127.0, sg.value/15.0, vg.value/15.0)
        return (int(round(r * 255.0)), int(round(g * 255.0)), int(round(b * 255.0)))
        #return (int(round(r * 15.0)), int(round(g * 15.0)), int(round(b * 15.0)))
    else:
        r,g,b = colorsys.hsv_to_rgb(hg.value/2047.0, sg.value/255.0, vg.value/255.0)
        return (int(round(r * 255.0)), int(round(g * 255.0)), int(round(b * 255.0)))

def set_hsv_sliders(rgb, hg, sg, vg):
    h,s,v = colorsys.rgb_to_hsv(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    if config.color_depth == 16:
        hg.value = int(round(h * 127.0))
        sg.value = int(round(s * 15.0))
        vg.value = int(round(v * 15.0))
    else:
        hg.value = int(round(h * 2047.0))
        sg.value = int(round(s * 255.0))
        vg.value = int(round(v * 255.0))

    hg.need_redraw = True
    sg.need_redraw = True
    vg.need_redraw = True

def rgb_to_hex(rgb):
    return hex(rgb[0]*256*256 + rgb[1]*256 + rgb[2])[2:].zfill(6)

def hex_to_rgb(hexstr):
    try:
        r = int("0x" + hexstr[0:2], 16)
        g = int("0x" + hexstr[2:4], 16)
        b = int("0x" + hexstr[4:6], 16)
        return (r,g,b)
    except:
        return None

def palette_req(screen):
    global palette_page
    config.stop_cycling()

    backuppal = list(config.truepal)
    config.pal = list(config.truepal)
    color = config.color
    req = str2req("Color Palette", """
 R G B H S V %%%%%%
:|:|:|:|:|:| ######
:|:|:|:|:|:| ######
:|:|:|:|:|:| ######
:|:|:|:|:|:| ######
:|:|:|:|:|:| ######
:|:|:|:|:|:| ######
:|:|:|:|:|:| ######
_______      ^^ A^^
[Spread]   [Ex~Copy]
[Range][1~2~3~4~5~6]
Speed---------___^^
[Cancel] [Undo] [OK]
""", "%#:^", mouse_pixel_mapper=config.get_mouse_pointer_pos, custom_gadget_type=PPGadget, font=config.font)

    (rx,ry,rw,rh) = req.rect
    rx += 20
    ry += int(config.menubar.rect[3] * 1.5)
    req.rect = (rx,ry,rw,rh)
    config.pixel_req_rect = req.get_screen_rect()
    req.draggable = True
    #req.center(screen)

    #palette page
    palette_page = 0
    palpageg = req.gadget_id("16_8")
    ppx,ppy,ppw,pph = palpageg.rect
    palpageg.rect = (ppx-(config.fontx//2),ppy,ppw,pph)
    palpage_lg = req.gadget_id("13_8")
    palpage_lg.value = -2
    palpage_rg = req.gadget_id("17_8")
    palpage_rg.value = 2

    if len(config.pal) > 32 and not config.display_mode & config.MODE_EXTRA_HALFBRIGHT:
        palpageg.enabled = True
        palpage_lg.enabled = True
        palpage_rg.enabled = True
    else:
        palpageg.enabled = False
        palpage_lg.enabled = False
        palpage_rg.enabled = False

    #color sliders
    colorg = req.gadget_id("13_0")
    palg = req.gadget_id("13_1")
    strg = req.gadget_id("0_8")
    rg = req.gadget_id("1_1")
    gg = req.gadget_id("3_1")
    bg = req.gadget_id("5_1")
    hg = req.gadget_id("7_1")
    sg = req.gadget_id("9_1")
    vg = req.gadget_id("11_1")
    rg.maxvalue = config.color_depth
    gg.maxvalue = config.color_depth
    bg.maxvalue = config.color_depth
    hg.maxvalue = config.color_depth * 8
    sg.maxvalue = config.color_depth
    vg.maxvalue = config.color_depth

    #color range gadgets
    range_numg = []
    range_numg.append(req.gadget_id("7_10"))
    range_numg.append(req.gadget_id("9_10"))
    range_numg.append(req.gadget_id("11_10"))
    range_numg.append(req.gadget_id("13_10"))
    range_numg.append(req.gadget_id("15_10"))
    range_numg.append(req.gadget_id("17_10"))
    current_range = 0
    range_numg[current_range].state = 1
    speedg = req.gadget_id("5_11")
    speedg.maxvalue = 61
    speedg.value = config.cranges[current_range].get_hz()
    speed_dirg = req.gadget_id("17_11")
    speed_dirg.value = config.cranges[current_range].get_dir()
    speed_numg = req.gadget_id("14_11")
    if config.cranges[current_range].is_active():
        speed_numg.value = str(speedg.value)
    else:
        speed_numg.value = ""
        speedg.enabled = False
        speed_numg.enabled = False
        speed_dirg.enabled = False

    config.cursor.shape = 1
    running = 1

    color = config.color
    colorg.value = color
    palg.value = color
    palg.maxvalue = current_range
    set_rgb_sliders(config.pal[color], rg, gg, bg)
    strg.value = rgb_to_hex(config.pal[color])
    strg.need_redraw = True
    set_hsv_sliders(config.pal[color], hg, sg, vg)
    from_color = -1
    color_action = 0
    req.draw(screen)
    config.recompose()

    while running:
        event = pygame.event.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 
            config.pal = list(backuppal)
            config.set_all_palettes(config.pal)

        #Get color from pixel canvas
        if event.type == MOUSEBUTTONUP and event.button == 1:
            x,y = config.get_mouse_pixel_pos(event)
            if x < rx or y < ry or x > rx+rw or y > ry+rh:
                x1,y1 = config.get_mouse_pixel_pos(event, ignore_req=True)
                if x1 >= 0 and y1 >= 0 and \
                   x1<config.pixel_canvas.get_width() and \
                   y1<config.pixel_canvas.get_height():
                    color = config.pixel_canvas.get_at_mapped((x1,y1))
                    palg.value = color
                    palg.need_redraw = True
                    colorg.value = color
                    colorg.need_redraw = True
                    palette_page = color // 32 * 32
                    palpageg.label = chr(65+(palette_page//32))
                    palpageg.need_redraw = True
                    set_rgb_sliders(config.pal[color], rg, gg, bg)
                    strg.value = rgb_to_hex(config.pal[color])
                    strg.need_redraw = True
                    set_hsv_sliders(config.pal[color], hg, sg, vg)

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK":
                    running = 0 
                elif ge.gadget.label == "Cancel":
                    running = 0 
                    config.pal = list(backuppal)
                    config.set_all_palettes(config.pal)
                elif ge.gadget.label == "Undo":
                    config.pal = list(backuppal)
                    config.set_all_palettes(config.pal)
                    set_rgb_sliders(config.pal[color], rg, gg, bg)
                    strg.value = rgb_to_hex(config.pal[color])
                    strg.need_redraw = True
                    set_hsv_sliders(config.pal[color], hg, sg, vg)
                elif ge.gadget.label == "Spread":
                    from_color = color
                    ge.gadget.state = 1
                    color_action = 1
                    config.cursor.shape = config.cursor.NORMALTO
                elif ge.gadget.label == "Ex":
                    from_color = color
                    ge.gadget.state = 1
                    color_action = 2
                    config.cursor.shape = config.cursor.NORMALTO
                elif ge.gadget.label == "Copy":
                    from_color = color
                    ge.gadget.state = 1
                    color_action = 3
                    config.cursor.shape = config.cursor.NORMALTO
                elif ge.gadget.label == "Range":
                    from_color = color
                    ge.gadget.state = 1
                    color_action = 4
                    config.cursor.shape = config.cursor.NORMALTO
                elif ge.gadget.label >= "1" and ge.gadget.label <= "6":
                    current_range = int(ge.gadget.label)-1
                    palg.maxvalue = current_range
                    palg.need_redraw = True
                    speedg.value = config.cranges[current_range].get_hz()
                    speedg.need_redraw = True
                    if config.cranges[current_range].is_active():
                        speed_numg.value = str(speedg.value)
                        speedg.enabled = True
                        speed_numg.enabled = True
                        speed_dirg.enabled = True
                    else:
                        speed_numg.value = ""
                        speedg.enabled = False
                        speed_numg.enabled = False
                        speed_dirg.enabled = False
                    speed_numg.need_redraw = True
                    speed_dirg.value = config.cranges[current_range].get_dir()
                    speed_dirg.need_redraw = True
            elif ge.gadget.type == Gadget.TYPE_CUSTOM:
                if ge.gadget.label == "#":
                    if ge.gadget.value >= 0 and ge.gadget.value < len(config.pal):
                        color = ge.gadget.value
                        colorg.value = color
                        colorg.need_redraw = True
                        set_rgb_sliders(config.pal[color], rg, gg, bg)
                        strg.value = rgb_to_hex(config.pal[color])
                        strg.need_redraw = True
                        set_hsv_sliders(config.pal[color], hg, sg, vg)
                        to_color = color
                        if color_action >= 0:
                            if color < from_color and color_action != 3:
                                to_color = from_color
                                from_color = color
                            # spread
                            if color_action == 1:
                                numcol = to_color - from_color + 1
                                #print(config.pal[from_color])
                                #print(config.pal[to_color])
                                for i in range(1,numcol-1):
                                    config.pal[from_color+i] = \
                                        (int(round((config.pal[from_color][0]*(numcol-i) + config.pal[to_color][0]*i)/(numcol))), \
                                         int(round((config.pal[from_color][1]*(numcol-i) + config.pal[to_color][1]*i)/(numcol))), \
                                         int(round((config.pal[from_color][2]*(numcol-i) + config.pal[to_color][2]*i)/(numcol))))
                            # exchange
                            elif color_action == 2:
                                config.pal[from_color], config.pal[to_color] = \
                                    config.pal[to_color], config.pal[from_color]
                            # copy
                            elif color_action == 3:
                                config.pal[to_color] = config.pal[from_color]
                            # range
                            elif color_action == 4:
                                if from_color == to_color:
                                    config.cranges[current_range].low = 0
                                    config.cranges[current_range].high = 0
                                else:
                                    config.cranges[current_range].low = from_color
                                    config.cranges[current_range].high = to_color

                                speedg.value = config.cranges[current_range].get_hz()
                                speedg.need_redraw = True
                                if config.cranges[current_range].is_active():
                                    speed_numg.value = str(speedg.value)
                                    speedg.enabled = True
                                    speed_numg.enabled = True
                                    speed_dirg.enabled = True
                                else:
                                    speed_numg.value = ""
                                    speedg.enabled = False
                                    speed_numg.enabled = False
                                    speed_dirg.enabled = False
                                speed_numg.need_redraw = False
                                speed_dirg.value = config.cranges[current_range].get_dir()
                                speed_dirg.need_redraw = True
                                speed_numg.need_redraw = True

                            config.pal = config.quantize_palette(config.pal, config.color_depth)
                            config.set_all_palettes(config.pal)
                            color_action = 0
                            from_color = -1
                            config.cursor.shape = config.cursor.NORMAL
                elif ge.gadget.label == "^":
                    config.cranges[current_range].set_dir(speed_dirg.value)
                    speed_dirg.need_redraw = True
                    palpageg.label = chr(65+(palette_page//32))
                    palpageg.need_redraw = True
            elif ge.gadget.type == Gadget.TYPE_PROP_VERT:
                if ge.gadget.id == rg.id or ge.gadget.id == gg.id or ge.gadget.id == bg.id:
                    set_hsv_sliders(get_rgb_sliders(rg, gg, bg), hg, sg, vg)
                else:
                    set_rgb_sliders(get_hsv_sliders(hg, sg, vg), rg, gg, bg)

                rgb = get_rgb_sliders(rg, gg, bg)
                strg.value = rgb_to_hex(rgb)
                strg.need_redraw = True
                colorg.need_redraw = True
                palg.need_redraw = True
                config.pal[color] = rgb
                config.pal = config.quantize_palette(config.pal, config.color_depth)
                config.set_all_palettes(config.pal)
            elif ge.gadget.type == Gadget.TYPE_PROP:
                if ge.gadget.id == speedg.id:
                    if config.cranges[current_range].is_active():
                        if ge.event.type == MOUSEBUTTONUP:
                            config.stop_cycling()
                        else:
                            config.start_cycling()
                        config.cranges[current_range].set_hz(ge.gadget.value)
                        speed_numg.value = str(speedg.value)
                        speed_numg.need_redraw = True
                    else:
                        speedg.value = 0
                        speedg.need_redraw = True
            elif ge.gadget.type == Gadget.TYPE_STRING and ge.type == GadgetEvent.TYPE_GADGETUP:
                rgb = hex_to_rgb(strg.value)
                if rgb == None:
                    strg.value = rgb_to_hex(get_rgb_sliders(rg, gg, bg))
                    strg.need_redraw = True
                else:
                    set_rgb_sliders(rgb, rg, gg, bg)
                    rgb = get_rgb_sliders(rg, gg, bg)
                    set_hsv_sliders(rgb, hg, sg, vg)
                    strg.value = rgb_to_hex(rgb)
                    strg.need_redraw = True
                    config.pal[color] = rgb
                    config.pal = config.quantize_palette(config.pal, config.color_depth)
                    config.set_all_palettes(config.pal)
        range_numg[current_range].state = 1
        if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            colorg.need_redraw = True
            palg.need_redraw = True

            #keep requestor within screen
            (rx,ry,rw,rh) = req.rect
            if ry < 14:
                ry = 14
            if ry > screen.get_height()-20:
                ry = screen.get_height()-20
            if rx < -rw+20:
                rx = -rw+20
            if rx > screen.get_width()-40:
                rx = screen.get_width()-40
            req.rect = (rx,ry,rw,rh)
            config.pixel_req_rect = req.get_screen_rect()
            req.draw(screen)
            config.recompose()
    config.pixel_req_rect = None

    config.truepal = list(config.pal)
    config.pal = config.unique_palette(config.pal)
    config.set_all_palettes(config.pal)


