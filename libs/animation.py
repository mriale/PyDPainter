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


class Animation:
    def __init__(self):
        self.num_frames = 1
        self.curr_frame = 1
        self.frame_rate = 30
        self.frame = [None]
        self.frame_delay = [0]

    def save_curr_frame(self):
        self.frame[self.curr_frame-1] = config.undo_image[config.undo_index].copy()
        if config.cycling:
            self.frame[self.curr_frame-1].set_palette(config.backuppal)

    def show_curr_frame(self):
        if self.curr_frame > self.num_frames:
            self.curr_frame = self.num_frames
        if self.frame[self.curr_frame-1] == None:
            config.pixel_canvas.fill(config.bgcolor);
        else:
            self.frame[self.curr_frame-1].set_palette(config.pal)
            config.pixel_canvas.blit(self.frame[self.curr_frame-1], (0,0))

        if self.num_frames > 1:
            config.menubar.title = f"{self.curr_frame}/{self.num_frames}" + (" " * 10)
            config.menubar.title = config.menubar.title[:10]
        else:
            config.menubar.title = "PyDPainter"

        config.clear_undo()
        config.save_undo()
        config.doKeyAction()

    def first_frame(self):
        if self.curr_frame != 1:
            self.save_curr_frame()
            self.curr_frame = 1
            self.show_curr_frame()

    def last_frame(self):
        if self.curr_frame != self.num_frames:
            self.save_curr_frame()
            self.curr_frame = self.num_frames
            self.show_curr_frame()

    def prev_frame(self):
        self.save_curr_frame()
        self.curr_frame -= 1
        if self.curr_frame < 1:
            self.curr_frame = self.num_frames
        self.show_curr_frame()

    def next_frame(self):
        self.save_curr_frame()
        self.curr_frame += 1
        if self.curr_frame > self.num_frames:
            self.curr_frame = 1
        self.show_curr_frame()

    def add_frame(self):
        self.save_curr_frame()
        self.frame.insert(self.curr_frame, self.frame[self.curr_frame-1].copy())
        self.frame_delay.insert(self.curr_frame, self.frame_delay[self.curr_frame-1])
        self.num_frames += 1
        self.next_frame()

    def delete_frame(self):
        if self.num_frames > 1:
            self.save_curr_frame()
            del self.frame[self.curr_frame-1]
            del self.frame_delay[self.curr_frame-1]
            self.num_frames -= 1
            if self.curr_frame > self.num_frames:
                self.curr_frame = self.num_frames
            self.show_curr_frame()

    def copy_frame_to_all(self):
        self.save_curr_frame()
        frame = self.frame[self.curr_frame-1]
        delay = self.frame_delay[self.curr_frame-1]
        for i in range(self.num_frames):
            self.frame[i] = frame
            self.frame_delay[i] = delay
        self.show_curr_frame()

    def delete_all_frames(self):
        self.set_frame_count(1)

    def set_frame_count(self, count):
        self.save_curr_frame()
        if count > self.num_frames:
            while self.num_frames < count:
                self.frame.insert(self.curr_frame, self.frame[self.curr_frame-1].copy())
                self.frame_delay.insert(self.curr_frame, self.frame_delay[self.curr_frame-1])
                self.num_frames += 1
        elif count < self.num_frames:
            while self.num_frames > count:
                del self.frame[self.curr_frame-1]
                del self.frame_delay[self.curr_frame-1]
                self.num_frames -= 1
                if self.curr_frame > self.num_frames:
                    self.curr_frame = self.num_frames

        self.show_curr_frame()

    def ask_frame(self):
        return

    def play(self):
        return

    def remember_frame(self):
        return

    def open_file(self):
        global progress_req
        config.stop_cycling()
        config.stencil.enable = False
        filename = file_req(config.pixel_req_canvas, "Open Picture", "Open", config.filepath, config.filename)
        if filename != (()) and filename != "":
            progress_req = open_progress_req(config.pixel_req_canvas, "Loading...")
            try:
                config.pixel_canvas = load_pic(filename, config, status_func=load_progress_anim, is_anim=True)
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


