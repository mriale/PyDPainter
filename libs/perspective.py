#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import math
import numpy as np

from libs.prim import *

config = None

def perspective_set_config(config_in):
    global config
    config = config_in

class Perspective:
    def __init__(self):
        self.rotate = [0,0,0]
        self.center = [160,100,0]
        self.xypos  = [160,100]
        self.xysize = [40,40]
        self.dist = 100
        self.maxdist = 500
        self.mindist = max(self.xysize)
        self.screen2world = self.calc_screen2world()
        self.world2screen = self.calc_world2screen()

    def calc_screen2world(self):
        c = self.center
        q = self.rotate
        #recalculate matrix
        trans1   = np.matrix([[    1,     0,     0, 0],
                              [    0,     1,     0, 0],
                              [    0,     0,     1, 0],
                              [-c[0], -c[1], -c[2], 1]])
        scale1   = np.matrix([[1/config.aspectX, 0, 0, 0],
                              [0, -1/config.aspectY, 0, 0],
                              [0, 0, 1, 0],
                              [0, 0, 0, 1]])
        rotx     = np.matrix([[ 1,           0,           0, 0],
                              [ 0, math.cos(q[0]),-math.sin(q[0]), 0],
                              [ 0, math.sin(q[0]), math.cos(q[0]), 0],
                              [ 0,           0,           0, 1]])
        roty     = np.matrix([[ math.cos(q[1]), 0, math.sin(q[1]), 0],
                              [           0, 1,           0, 0],
                              [-math.sin(q[1]), 0, math.cos(q[1]), 0],
                              [           0, 0,           0, 1]])
        rotz     = np.matrix([[ math.cos(q[2]),-math.sin(q[2]), 0, 0],
                              [ math.sin(q[2]), math.cos(q[2]), 0, 0],
                              [           0,           0, 1, 0],
                              [           0,           0, 0, 1]])
        return trans1 @ scale1 @ rotx @ roty @ rotz

    def calc_world2screen(self):
        c = self.center
        q = self.rotate
        #recalculate matrix
        scale2   = np.matrix([[config.aspectX, 0, 0, 0],
                              [0, -config.aspectY, 0, 0],
                              [0, 0, 1, 0],
                              [0, 0, 0, 1]])
        trans2   = np.matrix([[    1,     0,     0, 0],
                              [    0,     1,     0, 0],
                              [    0,     0,     1, 0],
                              [ c[0],  c[1],  c[2], 1]])
        return scale2 @ trans2

    def xy2vector(self, coord):
        return np.matrix([coord[0],coord[1],0,1])

    def vector2xy(self, v):
        return (v[0,0], v[0,1])

    def project(self, v):
        d = self.dist
        vx = v[0,0] / ((v[0,2]+d)/d)
        vy = v[0,1] / ((v[0,2]+d)/d)
        return np.matrix([vx,vy,0,1])

    def draw_cursor(self):
        # Calculate perspective of points of rectangle
        w, h = self.xysize
        w2 = w / 2
        h2 = h / 2
        cx, cy = self.xypos
        p1 = self.xy2vector((cx-w2, cy-h2)) @ self.screen2world
        p1 = self.project(p1) @ self.world2screen
        p2 = self.xy2vector((cx+w2, cy-h2)) @ self.screen2world
        p2 = self.project(p2) @ self.world2screen
        p3 = self.xy2vector((cx+w2, cy+h2)) @ self.screen2world
        p3 = self.project(p3) @ self.world2screen
        p4 = self.xy2vector((cx-w2, cy+h2)) @ self.screen2world
        p4 = self.project(p4) @ self.world2screen

        # Draw lines for rectangle
        """
        print(p1.astype(int))
        print(p2.astype(int))
        print(p3.astype(int))
        print(p4.astype(int))
        """
        screen = config.pixel_canvas
        color = 1
        config.clear_pixel_draw_canvas()
        drawline(screen, color, self.vector2xy(p1), self.vector2xy(p2))
        drawline(screen, color, self.vector2xy(p2), self.vector2xy(p3))
        drawline(screen, color, self.vector2xy(p3), self.vector2xy(p4))
        drawline(screen, color, self.vector2xy(p4), self.vector2xy(p1))
        config.recompose()

    def do_mode(self):
        print("perspective mode")
        running = 1
        delta = 0.05
        distdelta = 10
        update_cursor = True
        self.xypos = config.get_mouse_pixel_pos()

        while running:
            if update_cursor:
                self.screen2world = self.calc_screen2world()
                self.world2screen = self.calc_world2screen()
                self.draw_cursor()
                update_cursor = False

            event = pygame.event.wait()
            if event.type == pygame.MOUSEMOTION and pygame.event.peek((MOUSEMOTION)):
                #get rid of extra mouse movements
                continue

            if event.type == KEYDOWN:
                update_cursor = True
                if event.key == K_ESCAPE or \
                     event.key == K_KP_ENTER or \
                     (event.mod &KMOD_CTRL and event.key == K_RETURN):
                    running = 0
                elif event.key == K_KP0 or \
                     (event.mod & KMOD_CTRL and event.key == K_0):
                    self.rotate[0] = 0
                    self.rotate[1] = 0
                    self.rotate[2] = 0
                    self.dist = 100
                elif event.key == K_KP7 or \
                     (event.mod & KMOD_CTRL and event.key == K_7):
                    self.rotate[0] += delta
                elif event.key == K_KP8 or \
                     (event.mod & KMOD_CTRL and event.key == K_8):
                    self.rotate[0] -= delta
                elif event.key == K_KP9 or \
                     (event.mod & KMOD_CTRL and event.key == K_9):
                    self.rotate[0] = 0
                elif event.key == K_KP4 or \
                     (event.mod & KMOD_CTRL and event.key == K_4):
                    self.rotate[1] += delta
                elif event.key == K_KP5 or \
                     (event.mod & KMOD_CTRL and event.key == K_5):
                    self.rotate[1] -= delta
                elif event.key == K_KP6 or \
                     (event.mod & KMOD_CTRL and event.key == K_6):
                    self.rotate[1] = 0
                elif event.key == K_KP1 or \
                     (event.mod & KMOD_CTRL and event.key == K_1):
                    self.rotate[2] += delta
                elif event.key == K_KP2 or \
                     (event.mod & KMOD_CTRL and event.key == K_2):
                    self.rotate[2] -= delta
                elif event.key == K_KP3 or \
                     (event.mod & KMOD_CTRL and event.key == K_3):
                    self.rotate[2] = 0
                elif event.unicode == '>':
                    if self.dist < self.maxdist:
                        self.dist += distdelta
                        print(self.dist)
                elif event.unicode == '<':
                    if self.dist-distdelta > self.mindist:
                        self.dist -= distdelta
                        print(self.dist)
                else:
                    update_cursor = False
            elif event.type == MOUSEMOTION:
                self.xypos = config.get_mouse_pixel_pos(event)
                update_cursor = True

