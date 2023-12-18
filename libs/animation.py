#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import libs.gadget
from libs.gadget import *

from libs.prim import *
from libs.menureq import *
from libs.picio import *

config = None

def animation_set_config(config_in):
    global config
    config = config_in

def io_error_anim_req(title, message, filename, linelen=33):
    if len(filename) > linelen:
        short_file = "..." + filename[-(linelen-3):]
    else:
        short_file = filename
    dummy = question_req(config.pixel_req_canvas,
             title,
             message % (short_file),
             ["OK"],
             [K_RETURN])

prev_time = 0
progress_req = None
def load_progress_anim(percent):
    global prev_time

    curr_time = pygame.time.get_ticks()
    if curr_time - prev_time > 33:
        prev_time = curr_time
        update_progress_req(progress_req, config.pixel_req_canvas, percent)

#Draw palettes with list
class PalKeyListGadget(ListGadget):
    def drawGhost(self, screen, bgcolor, rect):
        x,y,w,h = rect
        fadesurf = pygame.Surface((w,h), SRCALPHA)
        fadesurf.fill((bgcolor[0],bgcolor[1],bgcolor[2],76))
        for i in range(0, w, 2):
            for j in range(0, h+1, 4):
                pygame.draw.rect(fadesurf, (bgcolor[0],bgcolor[1],bgcolor[2],180), (i,j,1,1), 0)
        for i in range(1, w, 2):
            for j in range(2, h+1, 4):
                pygame.draw.rect(fadesurf, (bgcolor[0],bgcolor[1],bgcolor[2],180), (i,j,1,1), 0)
        screen.blit(fadesurf, (x,y), (0,0,w,h))

    def drawPalKey(self, screen, pal, prect):
        x,y,w,h = prect
        colorw = w / len(pal)
        pali = 0
        cx = x
        while x < x+w and pali < len(pal):
            pygame.draw.rect(screen, pal[pali], (int(cx), y, max(1,math.ceil(colorw)), h))
            pali += 1
            cx += colorw
    
    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        need_redraw = self.need_redraw
        super(PalKeyListGadget, self).draw(screen, font, offset, fgcolor, bgcolor, hcolor)
        x,y,w,h = self.rect
        xo, yo = offset
        px = font.xsize//8
        py = font.ysize//8
        self.fontx = font.xsize
        self.fonty = int(font.ysize * 1.5)
        self.fonth = font.ysize

        if self.type == Gadget.TYPE_CUSTOM:
            if not need_redraw:
                return

            #List text
            if self.label == "#":
                screen.set_clip(self.screenrect)
                topi = self.top_item
                numlines = self.numlines
                xo += font.xsize * 6
                for i in range(topi, topi+numlines):
                    if i < len(self.items):
                        framei = int(self.items[i])-1
                        pal = config.anim.frame[framei].pal
                        is_pal_key = config.anim.frame[framei].is_pal_key
                        self.drawPalKey(screen, pal, (x+xo+2*px, y+yo+2*py+(i-topi)*font.ysize, w-offset[0]-x-12*px, font.ysize))
                        if not is_pal_key:
                            self.drawGhost(screen, bgcolor, [x+offset[0]+2*px, y+offset[1]+2*py+(i-topi)*font.ysize, w-4*px, font.ysize])
                screen.set_clip(None)

        

class Frame:
    def __init__(self, image=None, delay=3, pal=None, truepal=None, is_pal_key = False):
        self.image = image
        if delay < 1:
            self.delay = 3
        else:
            self.delay = delay

        self.is_pal_key = is_pal_key

        if pal == None:
            self.pal = list(config.pal)
        else:
            self.pal = list(pal)

        if truepal == None:
            self.truepal = list(config.truepal)
        else:
            self.truepal = list(truepal)

        self.loadpal = list(config.loadpal)
        self.backuppal = list(self.pal)

    def copy(self):
        image = None
        if self.image != None:
            image = self.image.copy()

        return Frame(image, self.delay, self.pal, self.truepal)

class Animation:
    def __init__(self):
        self.num_frames = 1
        self.curr_frame = 1
        self.frame_rate = 10
        self.frame = [Frame()]
        self.playing = False
        self.play_loop=False
        self.play_ping_pong=False
        self.play_reverse=False
        self.currdir = 0
        self.repeat = False
        self.frame_bookmark = -1
        self.global_palette = True

    def save_curr_frame(self):
        f = self.curr_frame-1
        self.frame[f].image = config.undo_image[config.undo_index].copy()
        self.frame[f].pal = list(config.pal)
        self.frame[f].truepal = list(config.truepal)
        self.frame[f].loadpal = list(config.loadpal)
        self.frame[f].backuppal = list(config.backuppal)

    def show_curr_frame(self):
        if self.curr_frame > self.num_frames:
            self.curr_frame = self.num_frames
        f = self.curr_frame-1
        if self.frame[f].image == None:
            config.pixel_canvas.fill(config.bgcolor);
        else:
            self.frame[f].image.set_palette(self.frame[f].pal)
            config.set_all_palettes(self.frame[f].pal)
            config.pal = list(self.frame[f].pal)
            config.truepal = list(self.frame[f].truepal)
            config.loadpal = list(self.frame[f].loadpal)
            config.backuppal = list(self.frame[f].backuppal)
            config.pixel_canvas.blit(self.frame[f].image, (0,0))

        framestr = f"{self.curr_frame}/{self.num_frames}"
        framestr = ((9-len(framestr)) * " ") + framestr
        config.animtoolbar.tool_id("framecount").label = framestr
        config.animtoolbar.tool_id("frameslider").maxvalue = self.num_frames
        config.animtoolbar.tool_id("frameslider").value = self.curr_frame-1

        config.clear_undo()
        config.save_undo()
        config.doKeyAction()

    def first_frame(self):
        if self.num_frames == 1:
            return
        if self.curr_frame != 1:
            self.save_curr_frame()
            self.curr_frame = 1
            self.show_curr_frame()

    def last_frame(self):
        if self.num_frames == 1:
            return
        if self.curr_frame != self.num_frames:
            self.save_curr_frame()
            self.curr_frame = self.num_frames
            self.show_curr_frame()

    def prev_frame(self):
        if self.num_frames == 1:
            return
        self.save_curr_frame()
        self.curr_frame -= 1
        if self.curr_frame < 1:
            self.curr_frame = self.num_frames
        self.show_curr_frame()

    def next_frame(self):
        if self.num_frames == 1:
            return
        self.save_curr_frame()
        self.curr_frame += 1
        if self.curr_frame > self.num_frames:
            self.curr_frame = 1
        self.show_curr_frame()

    def add_frame(self):
        self.save_curr_frame()
        self.frame.insert(self.curr_frame, self.frame[self.curr_frame-1].copy())
        self.num_frames += 1
        self.next_frame()

    def delete_frame(self):
        if self.num_frames > 1:
            self.save_curr_frame()
            del self.frame[self.curr_frame-1]
            self.num_frames -= 1
            if self.curr_frame > self.num_frames:
                self.curr_frame = self.num_frames
            self.show_curr_frame()

    def copy_frame_to_all(self):
        self.save_curr_frame()
        frame = self.frame[self.curr_frame-1]
        for i in range(self.num_frames):
            self.frame[i] = frame
        self.show_curr_frame()

    def delete_all_frames(self):
        self.set_frame_count(1)

    def set_frame_count(self, count):
        self.save_curr_frame()
        if count > self.num_frames:
            while self.num_frames < count:
                self.frame.insert(self.curr_frame, self.frame[self.curr_frame-1].copy())
                self.num_frames += 1
        elif count < self.num_frames:
            while self.num_frames > count:
                del self.frame[self.curr_frame-1]
                self.num_frames -= 1
                if self.curr_frame > self.num_frames:
                    self.curr_frame = self.num_frames

        self.show_curr_frame()

    def ask_frame(self):
        self.ask_frame_req(config.pixel_req_canvas)

    def pal_keyframe_list(self):
        self.pal_keyframe_list_req(config.pixel_req_canvas)

    def play(self, loop=False, ping_pong=False, reverse=False, stop=False):
        #print(f"play({loop=}, {ping_pong=}, {reverse=}, {stop=})")
        if self.num_frames == 1:
            return
        if stop:
            self.playing = False
            config.animtoolbar.tool_id("play").state = 0
            config.animtoolbar.tool_id("play").redraw = True
        else:
            self.play_loop=loop
            self.play_ping_pong=ping_pong
            self.play_reverse=reverse
            self.playing = True
            self.currdir = 1
            if self.play_reverse:
                self.currdir = -1
            config.animtoolbar.tool_id("play").state = 1
            config.animtoolbar.tool_id("play").redraw = True
            config.menubar.title_right = ""  # get rid of coords
            pygame.time.set_timer(config.TOOLEVENT, 1000//self.frame_rate)

    def remember_frame(self):
        if self.frame_bookmark > 0:
            self.save_curr_frame()
            self.curr_frame = self.frame_bookmark
            self.show_curr_frame()

    def pal_key_range(self, frameno=-1):
        if frameno < 1:
            frameno = self.curr_frame
        from_key = 1
        to_key = 1
        if frameno > 0 and frameno <= len(self.frame):
            if self.frame[frameno-1].is_pal_key:
                from_key = frameno
            else:
                from_key = frameno
                while from_key > 1 and not self.frame[from_key-1].is_pal_key:
                    from_key -= 1
            to_key = frameno + 1
            while to_key <= len(self.frame) and not self.frame[to_key-1].is_pal_key:
                to_key += 1
            to_key -= 1
            to_key = min(to_key, len(self.frame))
        return [from_key, to_key]

    def ask_global_palette(self, numframes):
        # save previous requestor
        prr = config.pixel_req_rect
        prc = config.pixel_req_canvas.copy()
        oldcursor = config.cursor.shape
        config.cursor.shape = config.cursor.NORMAL

        retval = question_req(config.pixel_req_canvas,
                 "Import frames into anim",
                 "About to import %d frames.\nPalette type:" % (numframes),
                 ["Global", "Local", "Cancel"],
                 [K_g, K_l, K_RETURN])

        # restore previous requestor
        config.pixel_req_rect = prr
        config.pixel_req_canvas = prc
        config.cursor.shape = oldcursor

        return retval


    def open_file(self):
        global progress_req
        config.stop_cycling()
        config.stencil.enable = False
        filename = file_req(config.pixel_req_canvas, "Open Animation", "Open", config.filepath, config.filename)
        if filename != (()) and filename != "":
            progress_req = open_progress_req(config.pixel_req_canvas, "Loading...")
            try:
                config.pixel_canvas = libs.picio.load_pic(filename, config, status_func=load_progress_anim, is_anim=True)
                config.bgcolor = 0
                config.color = 1
                close_progress_req(progress_req)
                config.truepal = list(config.pal)
                config.pal = config.unique_palette(config.pal)
                config.initialize_surfaces()
                config.filepath = os.path.dirname(filename)
                config.filename = filename
                config.modified_count = 0
                config.anim.show_curr_frame()
            except:
                close_progress_req(progress_req)
                io_error_anim_req("Load Error", "Unable to open anim:\n%s", filename)

    def import_frames(self):
        global progress_req
        config.stop_cycling()
        config.stencil.enable = False
        filename = file_req(config.pixel_req_canvas, "Import Frames", "Open", config.filepath, config.filename)
        if filename != (()) and filename != "":
            progress_req = open_progress_req(config.pixel_req_canvas, "Loading...")
            try:
                config.pixel_canvas = libs.picio.load_pic(filename, config, status_func=load_progress_anim, import_frames=True)
                config.bgcolor = 0
                config.color = 1
                close_progress_req(progress_req)
                config.truepal = list(config.pal)
                config.pal = config.unique_palette(config.pal)
                config.initialize_surfaces()
                config.filepath = os.path.dirname(filename)
                config.filename = filename
                config.modified_count = 0
                config.anim.show_curr_frame()
            except:
                close_progress_req(progress_req)
                io_error_anim_req("Load Error", "Unable to import frames:\n%s", filename)

    def save_file(self):
        io_error_anim_req("Not Implemented", "Saving ANIM files\nis not implemented yet.%s", "")

    def handle_events(self, event):
        if event.type == KEYDOWN:
            if not event.mod & KMOD_SHIFT and not event.mod & KMOD_CTRL:
                if event.key == K_1:
                    self.prev_frame()
                elif event.key == K_2:
                    self.next_frame()
                elif event.key == K_3:
                    self.ask_frame()
                elif event.key == K_4:
                    self.play(loop=True)
                elif event.key == K_5:
                    self.play()
                elif event.key == K_6:
                    self.play(ping_pong=True)
                elif event.key == K_7:
                    pass #animbrush prev
                elif event.key == K_8:
                    pass #animbrush next
                elif self.playing and (event.key == K_ESCAPE or event.key == K_SPACE):
                    self.play(stop=True)
                elif event.key == K_PAGEUP:
                    self.prev_frame()
                elif event.key == K_PAGEDOWN:
                    self.next_frame()
            elif event.mod & KMOD_SHIFT and not event.mod & KMOD_CTRL:
                if event.key == K_1:
                    self.first_frame()
                elif event.key == K_2:
                    self.last_frame()
                elif event.key == K_3:
                    self.remember_frame()
                elif event.key == K_4:
                    self.play(loop=True, reverse=True)
                elif event.key == K_5:
                    self.play(reverse=True)
                elif event.key == K_6:
                    self.play(ping_pong=True)
                elif event.key == K_7:
                    pass #animbrush first
                elif event.key == K_8:
                    pass #animbrush last
            elif not event.mod & KMOD_SHIFT and event.mod & KMOD_CTRL:
                if event.key == K_HOME:
                    self.first_frame()
                elif event.key == K_END:
                    self.last_frame()
        elif event.type == config.TOOLEVENT:
            if self.playing:
                if self.currdir > 0:
                    self.next_frame()
                elif self.currdir < 0:
                    self.prev_frame()
                if self.play_ping_pong:
                    if (self.currdir > 0 and self.curr_frame == self.num_frames) or \
                       (self.currdir < 0 and self.curr_frame == 1):
                        self.currdir = -self.currdir
                if not self.play_ping_pong and not self.play_loop and (\
                   (not self.play_reverse and self.curr_frame == self.num_frames) or \
                   (self.play_reverse and self.curr_frame == 1)):
                    self.play(stop=True)
                else:
                    pygame.time.set_timer(config.TOOLEVENT, config.anim.frame[self.curr_frame-1].delay * 1000 // 60)

    def process_animtoolbar_events(self, mta_list, event):
        for ge in mta_list:
            if ge.gadget.id == "frameslider":
                self.save_curr_frame()
                self.curr_frame = ge.gadget.value + 1
                self.show_curr_frame()
            elif ge.gadget.id == "framecount":
                if ge.type == ge.TYPE_GADGETDOWN:
                    self.ask_frame()
            elif ge.gadget.id == "prev":
                if self.playing:
                    self.currdir = -1
                else:
                    pygame.time.set_timer(config.TOOLEVENT, 500)
                    self.repeat = True
            elif ge.gadget.id == "next":
                if self.playing:
                    self.currdir = 1
                else:
                    pygame.time.set_timer(config.TOOLEVENT, 500)
                    self.repeat = True
            elif ge.gadget.id == "play":
                if ge.gadget.state == 0:
                    self.playing = False
                else:
                    self.playing = True
                    pygame.time.set_timer(config.TOOLEVENT, config.anim.frame[self.curr_frame-1].delay * 1000 // 60)
        if len(mta_list) == 0 and event.type == config.TOOLEVENT:
            if config.animtoolbar.tool_id("prev").state == 1:
                self.prev_frame()
                pygame.time.set_timer(config.TOOLEVENT, 50)
            elif config.animtoolbar.tool_id("next").state == 1:
                self.next_frame()
                pygame.time.set_timer(config.TOOLEVENT, 50)
            elif self.repeat:
                pygame.time.set_timer(config.TOOLEVENT, TIMEROFF)
                self.repeat = False

    def num_frames_req(self, screen):
        req = str2req("Set Frame Count", """

   Count: ____@@@@

[Cancel][OK]
""", "@", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
        req.center(screen)
        config.pixel_req_rect = req.get_screen_rect()

        countg = req.gadget_id("10_1")
        countg.numonly = True
        countg.value = str(self.num_frames)

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
                        if int(countg.value) >= 1:
                            self.set_frame_count(int(countg.value))
                            running = 0
                    elif ge.gadget.label == "Cancel":
                        running = 0 

            if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
                req.draw(screen)
                config.recompose()

        config.pixel_req_rect = None
        config.recompose()

        return

    def ask_frame_req(self, screen):
        req = str2req("Go To Frame", """

   Frame: ____@@@@

[Cancel][OK]
""", "@", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
        req.center(screen)
        config.pixel_req_rect = req.get_screen_rect()

        frameg = req.gadget_id("10_1")
        frameg.numonly = True
        frameg.value = str(self.curr_frame)

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
                        if int(frameg.value) >= 1:
                            self.save_curr_frame()
                            self.curr_frame = int(frameg.value)
                            self.frame_bookmark = self.curr_frame
                            self.show_curr_frame()
                            running = 0
                    elif ge.gadget.label == "Cancel":
                        running = 0 

            if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
                req.draw(screen)
                config.recompose()

        config.pixel_req_rect = None
        config.recompose()

        return

    def pal_keyframe_list_req(self, screen):
        req = str2req("Color Keyframes", """
Frame Colors
############################^^
############################@@
############################@@
############################@@
############################@@
############################@@
############################@@
############################@@
############################@@
############################^^
[Copy][Paste][Delete]
[Cancel][OK]
""", "#^@", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=PalKeyListGadget, font=config.font)
        req.center(screen)
        config.pixel_req_rect = req.get_screen_rect()

        #get palette keyframes
        curr_pal_range = self.pal_key_range()
        curr_pal_index = 0
        palkeyframes = []
        for i in range(0,config.anim.num_frames):
            if config.anim.frame[i].is_pal_key:
                palkeyframes.append("%5d" % (i+1))
                if i+1 == self.curr_frame:
                    curr_pal_index = len(palkeyframes)-1
            elif i+1 == self.curr_frame:
                palkeyframes.append("%5d" % (i+1))
                curr_pal_index = len(palkeyframes)-1

        #list items
        list_itemsg = req.gadget_id("0_1")
        list_itemsg.items = palkeyframes
        list_itemsg.top_item = 0
        list_itemsg.value = curr_pal_index

        #list up/down arrows
        list_upg = req.gadget_id("28_1")
        list_upg.value = -1
        list_downg = req.gadget_id("28_10")
        list_downg.value = 1

        #list slider
        list_sliderg = req.gadget_id("28_2")
        list_sliderg.value = list_itemsg.top_item

        #all list item gadgets
        listg_list = [list_itemsg, list_upg, list_downg, list_sliderg]
        list_itemsg.listgadgets = listg_list
        list_upg.listgadgets = listg_list
        list_downg.listgadgets = listg_list
        list_sliderg.listgadgets = listg_list

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
                        """
                        if int(frameg.value) >= 1:
                            self.save_curr_frame()
                            self.curr_frame = int(frameg.value)
                            self.frame_bookmark = self.curr_frame
                            self.show_curr_frame()
                        """
                        running = 0
                    elif ge.gadget.label == "Cancel":
                        running = 0

            if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
                req.draw(screen)
                config.recompose()

        config.pixel_req_rect = None
        config.recompose()

        return


