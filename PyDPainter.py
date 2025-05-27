#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
PyDPainter.py
Build a usable pixel art paint program in pygame
"""

import sys, math, os, random, colorsys, traceback, datetime, platform

try:
    import contextlib
    with contextlib.redirect_stdout(None):
        import pygame
        from pygame.locals import *

    import numpy
except:
    import tkinter as tk
    root = tk.Tk()
    root.title("PyDPainter Error")

    #Put out a useful message if pygame is not installed
    message = tk.Label(root, text="""
Some required Python modules are not installed:
- pygame
- numpy

For Windows, run 'install_pygame.bat'

For Linux and other systems, see 'installing.txt'

After the modules are successfully installed, re-run PyDPainter.
""")
    message.pack()

    # keep the window displaying
    root.mainloop()
    exit(1)

######################################################

os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"
os.environ["SDL_MOUSE_RELATIVE"] = "0"
os.environ["TK_SILENCE_DEPRECATION"] = "1"
os.chdir(os.path.realpath(os.path.dirname(__file__)))

import libs.pixelfont
from libs.pixelfont import PixelFont

from libs.picio import *

from operator import itemgetter

from libs.config import *

root = None
do_recover = ""

def write_recover():
    now = datetime.datetime.now()
    datestr = now.strftime('%Y-%m-%d_%H%M%S')
    recover_path = os.path.join(os.path.expanduser('~'), ".pydpainter-recover", datestr)
    os.makedirs(recover_path, exist_ok=True)
    os.chdir(recover_path)
    with open("stackdump.txt", "w") as f:
        f.write(traceback.format_exc())
    print(traceback.format_exc())
    pygame.image.save(config.undo_image[config.undo_index], "recover.bmp")
    pygame.image.save(config.undo_image[config.undo_index], "recover.png")
    save_iffinfo("recover.bmp")
    with open("platform.txt", "w") as f:
        f.write(str(platform.uname()))

def recover_file(dir_name):
    global do_recover
    recover_path = os.path.join(os.path.expanduser('~'), ".pydpainter-recover", dir_name)
    do_recover = recover_path
    root.destroy()

def remove_files():
    from tkinter.messagebox import askyesno
    import shutil
    answer = askyesno(title='Remove Recovery Files?',
                    message='Are you sure that you want to remove all PyDPainter recovery files?')
    if answer:
        recover_path = os.path.join(os.path.expanduser('~'), ".pydpainter-recover")
        shutil.rmtree(recover_path)
        root.destroy()

def check_recover():
    global root
    import tkinter as tk
    root = tk.Tk()
    recover_path = os.path.join(os.path.expanduser('~'), ".pydpainter-recover")
    if os.path.exists(recover_path):
        dir_list = os.listdir(recover_path)
        if len(dir_list) >= 1:
            root.title("Recovery")
            heading = tk.Label(root, text="PyDPainter Recovery", font="Helvetica 16 bold")
            heading.pack()
            message = tk.Label(root, text="Recover from:")
            message.pack()
            buttons = []
            pics = []
            for dir_name in sorted(dir_list):
                if os.path.exists(os.path.join(recover_path, dir_name, "recover.png")):
                    try:
                        pics.append(tk.PhotoImage(file=os.path.join(recover_path, dir_name, "recover.png")).subsample(4, 4))
                        buttons.append(tk.Button(root, text=dir_name, image=pics[-1], compound=tk.LEFT, command=lambda dn=dir_name: recover_file(dn)))
                    except:
                        buttons.append(tk.Button(root, text=dir_name, compound=tk.LEFT, command=lambda dn=dir_name: recover_file(dn)))

            buttons.append(tk.Button(root, text="Delete all", command=remove_files))
            buttons.append(tk.Button(root, text="Continue without recovering", command=root.destroy))

            for b in buttons:
                b.pack()

            # keep the window displaying
            root.mainloop()
    else:
        root.withdraw

if __name__ == "__main__":
    check_recover()
    config = pydpainter(do_recover)
    try:
        config.run()
    except Exception:
        write_recover()
