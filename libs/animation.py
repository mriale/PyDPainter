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
                wp = w-font.xsize * 6
                for i in range(topi, topi+numlines):
                    if i < len(self.items):
                        framei = int(self.items[i])-1
                        pal = self.frame_work[framei].pal
                        is_pal_key = self.frame_work[framei].is_pal_key
                        self.drawPalKey(screen, pal, (x+xo+2*px, y+yo+2*py+(i-topi)*font.ysize, wp-4*px, font.ysize))
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
        self.frame = [Frame(is_pal_key=True)]
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

    def show_curr_frame(self, doAction=True):
        if self.curr_frame > self.num_frames:
            self.curr_frame = self.num_frames
        elif self.curr_frame < 1:
            self.curr_frame = 1
        f = self.curr_frame-1
        if self.frame[f].image == None:
            config.pixel_canvas.fill(config.bgcolor);
        else:
            self.frame[f].image.set_palette(self.frame[f].pal)
            config.set_all_palettes(self.frame[f].pal)
            config.pal = list(self.frame[f].pal)
            config.truepal = list(self.frame[f].truepal)
            config.loadpal = list(self.frame[f].loadpal)
            config.pixel_canvas.blit(self.frame[f].image, (0,0))

        framestr = f"{self.curr_frame}/{self.num_frames}"
        framestr = ((9-len(framestr)) * " ") + framestr
        config.animtoolbar.tool_id("framecount").label = framestr
        config.animtoolbar.tool_id("frameslider").maxvalue = self.num_frames
        config.animtoolbar.tool_id("frameslider").value = self.curr_frame-1

        config.clear_undo()
        config.save_undo()
        if doAction:
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
        config.animtoolbar.tool_id("addframe").state = 0
        answer = self.num_req(config.pixel_req_canvas, "Add Frames", "Count", 1)
        if answer != None:
            for i in range(answer):
                self.save_curr_frame()
                self.frame.insert(self.curr_frame, self.frame[self.curr_frame-1].copy())
                self.num_frames += 1
                self.next_frame()


    def delete_frame(self):
        config.animtoolbar.tool_id("deleteframe").state = 0
        answer = self.num_req(config.pixel_req_canvas, "Delete Frames", "Count", 1)
        if answer != None:
            for i in range(answer):
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

    def fps_list(self):
        self.fps_list_req(config.pixel_req_canvas)

    def play(self, loop=False, ping_pong=False, reverse=False, stop=False):
        #print(f"play({loop=}, {ping_pong=}, {reverse=}, {stop=})")
        if self.num_frames == 1:
            return
        if stop:
            self.playing = False
            config.animtoolbar.tool_id("play").state = 0
            config.animtoolbar.tool_id("play").redraw = True
            pygame.time.set_timer(config.TOOLEVENT, TIMEROFF)
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
                 [K_g, K_l, K_ESCAPE])

        # restore previous requestor
        config.pixel_req_rect = prr
        config.pixel_req_canvas = prc
        config.cursor.shape = oldcursor

        return retval


    def ask_apply_multi(self, name):
        return self.ask_apply_multi_req(config.pixel_req_canvas, name)

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

    def export_frames(self):
        global progress_req
        config.stop_cycling()
        config.stencil.enable = False
        filename = file_req(config.pixel_req_canvas, "Export Frames", "Save", config.filepath, config.filename, has_type=True)
        if filename != (()) and filename != "":
            progress_req = open_progress_req(config.pixel_req_canvas, "Saving...")
            matches = re.fullmatch(r"^(.*?)([0-9]*)\.([^.]+)$", filename)
            file_root = matches[1]
            file_ext = matches[3]

            self.first_frame()
            self.show_curr_frame(doAction=False)
            for i in range(0, self.num_frames):
                try:
                    load_progress_anim(self.curr_frame / self.num_frames)
                    frame_filename = file_root + ("%04d"%i) + "." + file_ext
                    libs.picio.save_pic(frame_filename, config)
                    self.next_frame()
                    self.show_curr_frame(doAction=False)
                except:
                    close_progress_req(progress_req)
                    io_error_anim_req("Load Error", "Unable to save frame:\n%s", frame_filename)

            close_progress_req(progress_req)

    def save_file(self):
        global progress_req
        config.stop_cycling()
        config.stencil.enable = False
        filename = file_req(config.pixel_req_canvas, "Save Animation", "Save", config.filepath, config.filename)
        if filename != (()) and filename != "":
            progress_req = open_progress_req(config.pixel_req_canvas, "Saving...")
            if True: #try:
                if not libs.picio.save_anim(filename, config, status_func=load_progress_anim, overwrite=False):
                    close_progress_req(progress_req)
                    answer = question_req(config.pixel_req_canvas,
                             "File Exists",
                             "Overwrite this file?",
                             ["Yes","No"],
                             [K_RETURN, K_ESCAPE])
                    if answer == 0:
                        progress_req = open_progress_req(config.pixel_req_canvas, "Saving...")
                        libs.picio.save_anim(filename, config, status_func=load_progress_anim, overwrite=True)
                    else:
                        return

                close_progress_req(progress_req)
                config.filepath = os.path.dirname(filename)
                config.filename = filename
                config.modified_count = 0
                config.anim.show_curr_frame()
            """
            except:
                close_progress_req(progress_req)
                io_error_anim_req("Load Error", "Unable to save anim:\n%s", filename)
            """

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

    def num_req(self, screen, title, prompt, default_num=""):
        req = str2req(title, """

   %s: _____@@@

[Cancel][OK]
"""%(prompt), "@", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
        req.center(screen)
        config.pixel_req_rect = req.get_screen_rect()

        colno = len(prompt) + 5
        numg = req.gadget_id(str(colno)+"_1")
        numg.numonly = True
        numg.value = str(default_num)
        numg.state = 1
        numg.pos = len(numg.value)

        req.draw(screen)
        config.recompose()

        running = 1
        retval = None
        while running:
            event = pygame.event.wait()
            gevents = req.process_event(screen, event)

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = 0 
                elif event.key == K_RETURN:
                    if not req.has_error():
                        if int(numg.value) >= 1:
                            retval = int(numg.value)
                            running = 0

            for ge in gevents:
                if ge.gadget.type == Gadget.TYPE_BOOL:
                    if ge.gadget.label == "OK" and not req.has_error():
                        if int(numg.value) >= 1:
                            retval = int(numg.value)
                            running = 0
                    elif ge.gadget.label == "Cancel":
                        running = 0 

            if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
                req.draw(screen)
                config.recompose()

        config.pixel_req_rect = None
        config.recompose()

        return retval

    def num_frames_req(self, screen):
        answer = self.num_req(screen, "Set Frame Count", "Count", self.num_frames)
        if answer != None:
            self.set_frame_count(answer)

        return

    def ask_frame_req(self, screen):
        answer = self.num_req(screen, "Go To Frame", "Frame", self.curr_frame)
        if answer != None:
            self.save_curr_frame()
            self.curr_frame = answer
            self.frame_bookmark = self.curr_frame
            self.show_curr_frame()

        return

    def get_pal_keys(self, list_itemsg, animframe):
        curr_pal_index = 0
        palkeyframes = []
        frame_work = []
        for i in range(0,config.anim.num_frames):
            f = animframe[i]
            frame_work.append(Frame(None, pal=f.pal, truepal=f.truepal, is_pal_key=f.is_pal_key))
            if f.is_pal_key:
                palkeyframes.append("%5d" % (i+1))
                if i+1 == self.curr_frame:
                    curr_pal_index = len(palkeyframes)-1
            elif i+1 == self.curr_frame:
                palkeyframes.append("%5d" % (i+1))
                curr_pal_index = len(palkeyframes)-1
        list_itemsg.items = palkeyframes
        list_itemsg.top_item = 0
        list_itemsg.value = curr_pal_index
        list_itemsg.frame_work = frame_work
        list_itemsg.need_redraw = True


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
[Copy][Delete]       [Remap]
[Cancel][Undo][OK]
""", "#^@", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=PalKeyListGadget, font=config.font)
        req.center(screen)
        config.pixel_req_rect = req.get_screen_rect()
        self.save_curr_frame()

        MODE_NORMAL = 0
        MODE_COPY = 1
        mode = MODE_NORMAL

        #list items
        list_itemsg = req.gadget_id("0_1")
        self.get_pal_keys(list_itemsg, config.anim.frame)

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

        #remap toggle
        remapg = req.gadget_id("21_11")
        remap = True
        remapg.state = 1

        req.draw(screen)
        config.recompose()

        copy_from_framei = 0
        running = 1
        while running:
            event = pygame.event.wait()
            gevents = req.process_event(screen, event)

            if event.type == KEYDOWN and event.key == K_ESCAPE:
                running = 0

            for ge in gevents:
                if ge.gadget == list_itemsg:
                    if mode == MODE_COPY:
                        mode = MODE_NORMAL
                        listi = list_itemsg.value
                        framei = int(list_itemsg.items[listi])-1
                        frame_work = list_itemsg.frame_work
                        if framei != copy_from_framei:
                            #Copy palette from previously selected palette
                            pal = frame_work[copy_from_framei].pal
                            truepal = frame_work[copy_from_framei].truepal
                            i = framei
                            frame_work[i].is_pal_key = True
                            frame_work[i].pal = list(pal)
                            frame_work[i].truepal = list(truepal)
                            i += 1
                            while i < len(frame_work) and \
                              not frame_work[i].is_pal_key:
                                frame_work[i].pal = list(pal)
                                frame_work[i].truepal = list(truepal)
                                i += 1
                            #Refresh list
                            self.get_pal_keys(list_itemsg, list_itemsg.frame_work)

                if ge.gadget.type == Gadget.TYPE_BOOL:
                    listi = list_itemsg.value
                    framei = int(list_itemsg.items[listi])-1
                    frame_work = list_itemsg.frame_work

                    if ge.gadget.label == "OK":
                        num_key_frames = 0
                        #copy frame_work palettes into frame
                        for i in range(0,config.anim.num_frames):
                            fw = frame_work[i]
                            af = config.anim.frame[i]
                            if fw.is_pal_key:
                                num_key_frames += 1
                            if remap and fw.pal != af.pal:
                                af.image.set_palette(af.pal)
                                af.image = convert8(af.image.convert(), fw.pal)
                            else:
                                af.image.set_palette(fw.pal)
                            af.pal = fw.pal
                            af.truepal = fw.truepal
                            af.is_pal_key = fw.is_pal_key
                        if num_key_frames == 1:
                            config.anim.global_palette = True
                        else:
                            config.anim.global_palette = False
                        running = 0
                    elif ge.gadget.label == "Cancel":
                        running = 0
                    elif ge.gadget.label == "Undo":
                        self.get_pal_keys(list_itemsg, config.anim.frame)
                    elif ge.gadget.label == "Remap":
                        remap = (remap+1) % 2
                    elif ge.gadget.label == "Copy":
                        mode = MODE_COPY
                        copy_from_framei = int(list_itemsg.items[listi])-1
                    elif ge.gadget.label == "Delete":
                        if list_itemsg.value != 0 and \
                           frame_work[framei].is_pal_key:
                            #Copy palette from previous key palette
                            frame_work[framei].is_pal_key = False
                            pal = frame_work[framei-1].pal
                            truepal = frame_work[framei-1].truepal
                            i = framei
                            while i < len(frame_work) and \
                              not frame_work[i].is_pal_key:
                                frame_work[i].pal = list(pal)
                                frame_work[i].truepal = list(truepal)
                                i += 1
                            #Manipulate list
                            list_itemsg.items.pop(listi)
                            if listi >= len(list_itemsg.items):
                                list_itemsg.value -= 1
                            list_itemsg.need_redraw = True

            if mode == MODE_NORMAL:
                config.cursor.shape = config.cursor.NORMAL
            elif mode == MODE_COPY:
                config.cursor.shape = config.cursor.NORMALTO

            if remap:
                remapg.state = 1

            if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
                req.draw(screen)
                config.recompose()

        config.pixel_req_rect = None
        self.show_curr_frame()

        return

    def in_anim_range(self, frame):
        return frame in range(1,self.num_frames+1)

    def get_list_from_range(self, str):
        result = []
        try:
            #Parse string for ranges
            for part in str.split(','):
                if '-' in part:
                    a, b = part.split('-')
                    a, b = int(a), int(b)
                    if self.in_anim_range(a) and self.in_anim_range(b):
                        result.extend(range(a, b + 1))
                    else:
                        return []
                else:
                    a = int(part)
                    if self.in_anim_range(a):
                        result.append(a)
                    else:
                        return []
            #Make list unique
            result = sorted(set(result))
        except:
            result = []

        return result

    def ask_apply_multi_req(self, screen, name):
        req = str2req("Apply to Multiple Frames", """
%s
[All Frames] [Current Frame]

Frames: ___________________

[Cancel][OK]
"""%(name), "@", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
        req.center(screen)
        config.pixel_req_rect = req.get_screen_rect()

        frameg = req.gadget_id("8_3")
        frameg.value = "1-" + str(self.num_frames)

        req.draw(screen)
        config.recompose()

        running = 1
        result = []
        while running:
            event = pygame.event.wait()
            gevents = req.process_event(screen, event)

            if event.type == KEYDOWN and event.key == K_ESCAPE:
                running = 0 

            for ge in gevents:
                if ge.gadget.type == Gadget.TYPE_BOOL:
                    if ge.gadget.label == "All Frames":
                        frameg.value = "1-" + str(self.num_frames)
                        frameg.need_redraw = True
                    elif ge.gadget.label == "Current Frame":
                        frameg.value = str(self.curr_frame)
                        frameg.need_redraw = True
                    elif ge.gadget.label == "OK" and not req.has_error():
                        result = self.get_list_from_range(frameg.value)
                        running = 0
                    elif ge.gadget.label == "Cancel":
                        running = 0 
                elif ge.gadget.type == Gadget.TYPE_STRING:
                    if len(self.get_list_from_range(frameg.value)) == 0:
                        frameg.error = True
                        frameg.need_redraw = True
                    elif frameg.error:
                        frameg.error = False
                        frameg.need_redraw = True

            if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
                req.draw(screen)
                config.recompose()

        config.pixel_req_rect = None
        config.recompose()

        return result


    def format_fps(self, delay):
        fps_str = "  0"
        if delay > 60:
            fps_str = ("%1.2f" % (60 / delay))[-3:]
        elif delay != 0:
            fps_str = "%3d" % (60 // delay)
        return fps_str

    def format_delay(self, delay):
        delay_str = "%4d" % delay
        return delay_str

    def format_range(self, low, high):
        if low == high:
            range_str = "%4d" % (low)
        else:
            range_str = "%4d-%d" % (low, high)
        range_str = range_str + " "*9
        range_str = range_str[:9]
        return range_str

    def get_fps_list(self, list_itemsg, delay_list):
        fps_list = []
        starti = 1
        last_delay = delay_list[0]
        for i in range(len(delay_list)):
            if delay_list[i] != last_delay:
                fps_str = self.format_fps(last_delay)
                delay_str = self.format_delay(last_delay)
                range_str = self.format_range(starti, i)
                fps_list.append("%s %s %s" % (fps_str, delay_str, range_str))
                starti = i+1
                last_delay = delay_list[i]

        if starti <= config.anim.num_frames:
            i = config.anim.num_frames
            fps_str = self.format_fps(delay_list[i-1])
            delay_str = self.format_delay(delay_list[i-1])
            range_str = self.format_range(starti, i)
            fps_list.append("%s %s %s" % (fps_str, delay_str, range_str))

        list_itemsg.items = fps_list
        list_itemsg.top_item = 0
        list_itemsg.value = 0
        list_itemsg.need_redraw = True

    def fps_list_req(self, screen):
        req = str2req("Set Animation Rate", """
    Delay Frame
FPS 1/60s Range
###################^^ FPS:_____
###################@@ Delay:_____
###################@@ [All Frames]
###################@@ [This Frame]
###################@@ ___________
###################@@
###################@@ [Update]
###################@@
###################@@
###################^^
[Cancel][Undo][OK]
""", "#^@", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=ListGadget, font=config.font)
        req.center(screen)
        config.pixel_req_rect = req.get_screen_rect()

        #list items
        list_itemsg = req.gadget_id("0_2")
        delay_list = []
        for i in range(config.anim.num_frames):
            delay_list.append(config.anim.frame[i].delay)
        self.get_fps_list(list_itemsg, delay_list)

        #list up/down arrows
        list_upg = req.gadget_id("19_2")
        list_upg.value = -1
        list_downg = req.gadget_id("19_11")
        list_downg.value = 1

        #list slider
        list_sliderg = req.gadget_id("19_3")
        list_sliderg.value = list_itemsg.top_item

        #all list item gadgets
        listg_list = [list_itemsg, list_upg, list_downg, list_sliderg]
        list_itemsg.listgadgets = listg_list
        list_upg.listgadgets = listg_list
        list_downg.listgadgets = listg_list
        list_sliderg.listgadgets = listg_list

        items = list_itemsg.items[0].split()

        #Frames Per Second
        fpsg = req.gadget_id("26_2")
        fpsg.value = items[0]
        fpsg.numonly = True
        fpsg.need_redraw = True

        #Delay (1/60s)
        delayg = req.gadget_id("28_3")
        delayg.value = items[1]
        delayg.numonly = True
        delayg.need_redraw = True

        #Frame Range
        frangeg = req.gadget_id("22_6")
        frangeg.value = items[2]
        frangeg.maxvalue = 20
        frangeg.need_redraw = True

        req.draw(screen)
        config.recompose()

        running = 1
        refresh_fields = False
        while running:
            event = pygame.event.wait()
            gevents = req.process_event(screen, event)

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = 0
                elif event.key in [K_UP, K_DOWN]:
                    refresh_fields = True

            for ge in gevents:
                if ge.gadget == list_itemsg:
                    refresh_fields = True

                if ge.gadget == fpsg:
                    if re.fullmatch('^\d*\.?\d+$', fpsg.value) and \
                       float(fpsg.value) > 0:
                        delayg.value = str(int(60 / float(fpsg.value)))
                        delayg.need_redraw = True
                elif ge.gadget == delayg:
                    if re.fullmatch('^\d+$', delayg.value) and \
                       int(delayg.value) != 0:
                        fpsg.value = self.format_fps(int(delayg.value)).strip()
                        fpsg.need_redraw = True
                elif ge.gadget.type == Gadget.TYPE_BOOL:
                    listi = list_itemsg.value

                    if ge.gadget.label == "OK" and not req.has_error():
                        for i in range(config.anim.num_frames):
                            config.anim.frame[i].delay = delay_list[i]
                        running = 0
                    elif ge.gadget.label == "Cancel":
                        running = 0
                    elif ge.gadget.label == "Undo":
                        delay_list = []
                        for i in range(config.anim.num_frames):
                            delay_list.append(config.anim.frame[i].delay)
                        self.get_fps_list(list_itemsg, delay_list)
                        refresh_fields = True
                    elif ge.gadget.label == "All Frames":
                        frangeg.value = "1-" + str(config.anim.num_frames)
                        frangeg.need_redraw = True
                    elif ge.gadget.label == "This Frame":
                        frangeg.value = str(config.anim.curr_frame)
                        frangeg.need_redraw = True
                    elif ge.gadget.label == "Update" and not req.has_error():
                        if int(delayg.value) > 0:
                            set_range = self.get_list_from_range(frangeg.value)
                            for frameno in set_range:
                                delay_list[frameno-1] = int(delayg.value)
                            self.get_fps_list(list_itemsg, delay_list)
                            refresh_fields = True

            if refresh_fields:
                listi = list_itemsg.value
                items = list_itemsg.items[listi].split()
                fpsg.value = items[0]
                fpsg.need_redraw = True
                delayg.value = items[1]
                delayg.need_redraw = True
                frangeg.value = items[2]
                frangeg.need_redraw = True
                refresh_fields = False

            if not pygame.event.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
                req.draw(screen)
                config.recompose()

        config.pixel_req_rect = None
        self.show_curr_frame()

        return

