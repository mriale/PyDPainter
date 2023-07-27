#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import sys, os

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

filename = None
screen_set = False
screen = None

def refresh():
    global screen_set
    global screen

    if True:
        if filename == None:
            sx = 400
            sy = 100
        else:
            imagex1 = pygame.image.load(filename)
            ox,oy = imagex1.get_size()
            sx,sy = ox,oy
            if ox > oy:
                sy *= 3
                x2 = 0
                y2 = oy
                x4 = 0
                y4 = oy*2
            else:
                sx *= 3
                x2 = ox
                y2 = 0
                x4 = ox*2
                y4 = 0

        if not screen_set:
            screen = pygame.display.set_mode((sx,sy))
            screen_set = True
            screen.fill((128,128,128,255))
            pygame.display.set_caption('Multi-scale: Drop image here')
            pygame.display.update()

        if filename == None:
            pygame.display.update()
            return

        screen.blit(imagex1, (0,0))

        surf_array = pygame.surfarray.array3d(imagex1)
        surf_array_alpha = pygame.surfarray.array_alpha(imagex1)
        scaled_array = surf_array[0::2, 0::2, ::]
        scaled_array_alpha = surf_array_alpha[0::2, 0::2]
        surf_array = None
        surf_array_alpha = None
        imagex2 = pygame.transform.scale(pygame.surfarray.make_surface(scaled_array), (ox,oy)).convert_alpha()
        imagex2_array_alpha = pygame.surfarray.pixels_alpha(imagex2)
        for i in range(ox):
            for j in range(oy):
                imagex2_array_alpha[i][j] = scaled_array_alpha[i//2][j//2]
        imagex2_array_alpha = None
        screen.blit(imagex2, (x2,y2))

        surf_array = pygame.surfarray.array3d(imagex1)
        surf_array_alpha = pygame.surfarray.array_alpha(imagex1)
        scaled_array = surf_array[1::4, 1::4, ::]
        scaled_array_alpha = surf_array_alpha[1::4, 1::4]
        surf_array = None
        surf_array_alpha = None
        imagex4 = pygame.transform.scale(pygame.surfarray.make_surface(scaled_array), (ox,oy)).convert_alpha()
        imagex4_array_alpha = pygame.surfarray.pixels_alpha(imagex4)
        for i in range(ox):
            for j in range(oy):
                imagex4_array_alpha[i][j] = scaled_array_alpha[i//4][j//4]
        imagex4_array_alpha = None
        screen.blit(imagex4, (x4,y4))

        pygame.display.update()

    #except:
    #    pass

def main():
    global filename
    global screen_set
    os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"
    os.environ["SDL_MOUSE_RELATIVE"] = "0"

    vertstack = False
    pygame.init()
    pygame.mixer.quit() #hack to stop 100% CPU ultilization
    pygame.event.clear()
    pygame.time.set_timer(pygame.USEREVENT, 1000)

    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = None
    
    refresh()

    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.DROPFILE:
            filename = event.file
            screen_set = False
            refresh()
        elif event.type == pygame.USEREVENT:
            refresh()

#        pygame.time.wait(1000)

if __name__ == '__main__': main()

