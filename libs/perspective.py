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
        self.pos = [160,100,0]
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

    def project(self, v):
        d = self.dist
        v2 = np.copy(v)
        v2[:,0] /= (v2[:,2]+d)/d
        v2[:,1] /= (v2[:,2]+d)/d
        return v2

    def draw_cursor(self):
        # Calculate perspective of points of rectangle
        w, h = self.xysize
        w2 = w / 2
        h2 = h / 2
        cx, cy, cz = self.pos

        points = np.matrix( [
                #bounding box
                [cx-w2, cy-h2, cz, 1],
                [cx+w2, cy-h2, cz, 1],
                [cx+w2, cy+h2, cz, 1],
                [cx-w2, cy+h2, cz, 1],
                #grid
                [cx, cy-h2, cz, 1],
                [cx, cy+h2, cz, 1],
                [cx-w2, cy, cz, 1],
                [cx+w2, cy, cz, 1],
                #Y
                [cx-w/8, cy-h2+h/16, cz, 1],
                [cx+w/8, cy-h2+h/16, cz, 1],
                [cx, cy-h/4, cz, 1],
                [cx, cy-h/8, cz, 1],
                #X
                [cx+w2-w/16, cy-h/8, cz, 1],
                [cx+w2-w/4, cy-h/8, cz, 1],
                [cx+w2-w/16, cy+h/8, cz, 1],
                [cx+w2-w/4, cy+h/8, cz, 1],
                ])

        lines = np.matrix( [
            #bounding box
            [0,1],
            [1,2],
            [2,3],
            [3,0],
            #grid
            [4,5],
            [6,7],
            #Y
            [8,10],
            [9,10],
            [10,11],
            #X
            [12,15],
            [13,14],
            ])

        # Transform points
        points = points @ self.screen2world
        points = self.project(points) @ self.world2screen

        screen = config.pixel_canvas
        color = 1
        config.clear_pixel_draw_canvas()

        # Draw lines for 3D cursor
        for i in range(lines.shape[0]):
            drawline(screen, color, (points[lines[i,0],0],points[lines[i,0],1]), (points[lines[i,1],0],points[lines[i,1],1]),xormode=1, handlesymm=False)

        config.recompose()


    def cursor2pos(self, coords):
        # Convert screen coords into position of 3D cursor
        x,y = coords
        z = 0
        p = np.matrix([[x, y, z, 1.0]])
        # Take mouse coords and convert to world coords
        p = p @ np.linalg.inv(self.world2screen)
        # Unproject the world coords
        d = self.dist
        p2 = np.copy(p)
        p2[:,0] *= (p2[:,2]+d)/d
        p2[:,1] *= (p2[:,2]+d)/d
        p2[:,2] *= (p2[:,2]+d)/d
        p2 = p2 @ np.linalg.inv(self.screen2world)
        return [p2[0,0], p2[0,1], p2[0,2]]

    def do_mode(self):
        #Disable perspective for now
        return

        running = 1
        delta = 0.05
        distdelta = 10
        update_cursor = True
        x,y = config.get_mouse_pixel_pos()
        self.center[0] = x
        self.center[1] = y

        while running:
            if update_cursor:
                self.screen2world = self.calc_screen2world()
                self.world2screen = self.calc_world2screen()
                self.draw_cursor()
                update_cursor = False

            event = config.xevent.wait()
            if event.type == pygame.MOUSEMOTION and config.xevent.peek((MOUSEMOTION)):
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
                elif event.unicode == ';':
                    self.center[2] += 2
                elif event.unicode == '\'':
                    self.center[2] -= 2
                else:
                    update_cursor = False
            elif event.type == MOUSEMOTION:
                self.pos = self.cursor2pos(config.get_mouse_pixel_pos(event))
                update_cursor = True

            if event.type == KEYDOWN and update_cursor:
                self.pos = self.cursor2pos(config.get_mouse_pixel_pos(event))
                update_cursor = True
                """
                x,y = config.get_mouse_pixel_pos(event)
                self.center[0] = x
                self.center[1] = y
                """
