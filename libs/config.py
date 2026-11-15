#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
config.py
Implement the global area of PyDPainter
"""

import sys, math, os.path, random, colorsys, platform, re, datetime
import argparse

from libs.clipboard import *
from libs.colorrange import *
from libs.cursor import *
from libs.displayinfo import *
from libs.toolbar import *
from libs.hotkey import *
from libs.prim import *
from libs.palreq import *
from libs.picio import *
from libs.layer import *
from libs.layout import *
from libs.stencil import *
from libs.grid import *
from libs.tools import *
from libs.minitools import *
from libs.animtools import *
from libs.layertools import *
from libs.menubar import *
from libs.menus import *
from libs.perspective import *
from libs.animation import *
from libs.version import *
from libs.xevent import *
from libs.zoom import *

import numpy as np

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

fonty = 12
fontx = 8

config = None

#Workaround for pygame timer bug:
#  https://github.com/pygame/pygame/issues/3128
#  https://github.com/pygame/pygame/pull/3062
TIMEROFF = int((2**31)-1)

custom_event_counter = 0

def get_at_mapped(screen, coord):
    if "get_at_mapped" in dir(screen):
        return screen.get_at_mapped(coord)
    else:
        x, y = coord
        surf_array = pygame.surfarray.pixels2d(screen)  # Create an array from the surface.
        return int(surf_array[x,y])

def cycle():
    if config.drawmode.value == DrawMode.CYCLE:
        color = config.color
        for crange in config.cranges:
           color = crange.next_color(color)
        config.color = color

def quantize_palette(pal, color_depth=16):
    if color_depth == 16:
        newpal = []
        if color_depth == 16 and len(pal) == 64:
            #handle extra halfbright
            for i in range(0,32):
                r,g,b = pal[i]
                newpal.append((r//16*17, g//16*17, b//16*17))
            for i in range(0,32):
                newpal.append(((newpal[i][0] & 0xee) // 2,
                               (newpal[i][1] & 0xee) // 2,
                               (newpal[i][2] & 0xee) // 2))
        else:
            for i in range(0,len(pal)):
                r,g,b = pal[i]
                newpal.append((r//16*17, g//16*17, b//16*17))

        return newpal
    else:
        newpal = []
        for i in range(0,len(pal)):
            r,g,b = pal[i]
            newpal.append((r, g, b))

        logpal = int(math.log(len(newpal), 2.0))
        if 2**logpal != len(newpal):
            logpal += 1
            while len(newpal) < 2**logpal:
                newpal.append((0,0,0))

        return newpal

color_skew=[]
for r in range(2,30):
    for g in range(1,r+1):
        for b in range(1,g+1):
            color_skew.append(((r//2)*((r%2)*2-1), \
                               (g//2)*((g%2)*2-1), \
                               (b//2)*((b%2)*2-1)))

def unique_palette(pal):
    newpal = []
    paldict = {}
    #print("len(pal): " + str(len(pal)))
    for i in range(0,len(pal)):
        col = pal[i]
        j = 0
        out_of_range = False
        #print("color[" + str(i) + "]: " + str(col))
        while out_of_range or str(col) in paldict:
            #print("dup color: " + str(col))
            out_of_range = False
            r = pal[i][0] + color_skew[j][0]
            g = pal[i][1] + color_skew[j][1]
            b = pal[i][2] + color_skew[j][2]
            if r < 0 or r > 255 or g < 0 or g > 255 or b < 0 or b > 255:
                out_of_range = True
            col = (r,g,b)
            j = j + 1
        newpal.append(col)
        paldict[str(col)] = 1
    #pal256.extend([pal[0]] * (256-len(pal)))
    return newpal

def setBIBrush():
    brushnames = ["","circle","square","spray"]
    newid = brushnames[config.brush.type] + str(config.brush.size)
    group_list = config.toolbar.tool_id("circle1").group_list
    for g in group_list:
        if g.id == newid:
            g.state = 1
        else:
            g.state = 0
        g.need_redraw = True
    return


prev_time = 0
progress_req = None
def drop_load_progress(percent):
    global prev_time

    curr_time = pygame.time.get_ticks()
    if curr_time - prev_time > 33:
        prev_time = curr_time
        update_progress_req(progress_req, config.pixel_req_canvas, percent)

class Project:
    def __init__(self):
        self.filename = ""
        self.filepath = ""
        self.pixel_canvas = None
        self.modified_count = -1
        self.anim = None
        self.layers = None
        self.stencil = None
        self.indicators = None

class pydpainter:

    def __init__(self, do_recover):
        global config
        config = self
        prim_set_config(self)
        palreq_set_config(self)
        toolreq_set_config(self)
        menureq_set_config(self)
        picio_set_config(self)
        stencil_set_config(self)
        grid_set_config(self)
        layer_set_config(self)
        colorrange_set_config(self)
        version_set_config(self)
        perspective_set_config(self)
        animation_set_config(self)
        xevent_set_config(self)
        pygame.init()
        pygame.mixer.quit() #hack to stop 100% CPU ultilization
        
        #parse command line
        parser = argparse.ArgumentParser(description='A usable pixel art program written in Python')
        parser.add_argument('filename',
                            help='filename of picture to load',
                            nargs='?')
        parser.add_argument('--config',
                            action='store',
                            default=os.path.join(os.path.expanduser('~'),".pydpainter"),
                            help='configuration file to use',
                            required=False)
        config.args = parser.parse_args()

        #initialize system
        self.dinfo = pygame.display.Info()
        self.initialize()
        clipboard_init()  # clipboard.clipboard_init()

        #load picture if recovered
        if do_recover != "":
            filename = os.path.join(do_recover, "recover.bmp")
            config.pixel_canvas = load_pic(filename, config)
            config.truepal = list(config.pal)
            config.pal = config.unique_palette(config.pal)
            config.layers_loaded = True
            config.initialize_surfaces()
            config.modified_count = 0

        #load picture if specified from command line
        elif config.args.filename:
            filename = config.args.filename
            config.pixel_canvas = load_pic(filename, config, cmd_load=True)
            config.truepal = list(config.pal)
            config.pal = config.unique_palette(config.pal)
            config.layers_loaded = True
            config.initialize_surfaces()
            config.filepath = os.path.dirname(filename)
            config.filename = filename
            config.modified_count = 0
            if config.anim.num_frames > 1:
                config.anim.show_curr_frame()

    def closest_scale4(self,maxnum,num):
        if num >= maxnum:
            return maxnum
        if num >= maxnum // 2:
            return maxnum // 2
        return maxnum // 4

    def scale_dec(self):
        if config.scale <= 1:
            config.scale /= 2.0
        else:
            currscale = math.floor(config.scale * 2.0) / 2.0
            if abs(config.scale - currscale) < .01:
                config.scale = currscale - 0.5
            else:
                config.scale = currscale

    def scale_inc(self):
        if config.scale < 1:
            config.scale *= 2.0
        else:
            currscale = math.ceil(config.scale * 2.0) / 2.0
            if abs(config.scale - currscale) < .01:
                config.scale = currscale + 0.5
            else:
                config.scale = currscale

    def set_aspect(self, mode):
        if config.force_1_to_1_pixels:
            mode = 0
            config.minitoolbar.tool_id("aspect").state = 0
        self.pixel_mode = self.pixel_modes[mode]
        self.pixel_aspect = self.pixel_aspects[mode]
        if self.display_mode & self.MODE_LACE:
            self.pixel_aspect *= 2.0
        if self.display_mode & self.MODE_HIRES:
            self.pixel_aspect /= 2.0

    def closest_scale(self, size=None):
        #estimate scale from size
        limit = 20
        if size != None:
            ow, oh = size
        else:
            dinfo = pygame.display.Info()
            ow = dinfo.current_w
            oh = dinfo.current_h
        pw = config.screen_width
        ph = config.screen_height
        pa = config.pixel_aspect

        sx = ow / (pw*pa)
        sy = oh / ph

        if sx < sy:
            s = sx
        else:
            s = sy

        if s < 0.51 or s > limit:
            s = config.scale

        return s

    def lerp(self, b, a, frac):
        return a * frac + (1-frac) * b

    def resize_display(self, resize_window=True, first_init=False, force=False, grab=True):
        if config.fullscreen:
            if force:
                if grab:
                    pygame.event.set_grab(True)
                    if "set_keyboard_grab" in dir(pygame.event):
                        pygame.event.set_keyboard_grab(True)
                config.scale_bak = config.scale
            pygame.display.set_mode((0,0), FULLSCREEN|HWSURFACE|DOUBLEBUF)
            config.screen = pygame.display.get_surface()
            config.max_width, config.max_height = config.screen.get_size()
            scale = min(config.max_height / config.screen_height,\
                        config.max_width / config.screen_width / config.pixel_aspect)
            new_window_size = (int(config.screen_width*scale*config.pixel_aspect), int(config.screen_height*scale))
            config.window_size = new_window_size
            return
        elif force:
            pygame.event.set_grab(False)
            if "set_keyboard_grab" in dir(pygame.event):
                pygame.event.set_keyboard_grab(False)
            config.scale = config.scale_bak
            config.max_width, config.max_height = (config.max_width_init, config.max_height_init)

        config.scale = max(1.0, config.scale)
        new_window_size = (int(config.screen_width*config.scale*config.pixel_aspect), int(config.screen_height*config.scale))

        if 'SDL_VIDEO_WINDOW_POS' in os.environ:
            del os.environ['SDL_VIDEO_WINDOW_POS']

        if "toolbar" in dir(config):
           config.toolbar.tip_canvas = None
        if "minitoolbar" in dir(config):
           config.minitoolbar.tip_canvas = None
        if "animtoolbar" in dir(config):
           config.animtoolbar.tip_canvas = None
        if "layertoolbar" in dir(config):
           config.layertoolbar.tip_canvas = None

        display_flags = HWSURFACE|DOUBLEBUF|RESIZABLE

        if not force and "window_size" in dir(config) and \
           (new_window_size[0] == config.window_size[0] and new_window_size[1] == config.window_size[1]):
            pass
        else:
            if force or resize_window or pygame.version.vernum[0] == 1:
                #Wait for mouse buttons to be released before resizing window
                config.xevent.get()
                while True in pygame.mouse.get_pressed():
                    config.xevent.get()
                pygame.display.set_mode(new_window_size, display_flags)
                if pygame.version.vernum[0] == 1:
                    pygame.time.wait(300)
 
            config.screen = pygame.display.get_surface()
            config.window_size = new_window_size

    def get_range(self, color):
        for crange in config.cranges:
            if crange.is_active() and color >= crange.low and color <= crange.high:
                return crange
        return None

    def new_layer_stack(self, canvas):
        """Create a fresh layer stack containing the canvas and stencil."""
        ls = LayerStack(indicatorx=self.LAYER_INDICATORX)
        ls.config = self
        if self.stencil is None:
            self.stencil = Stencil()
        ls.set("canvas", canvas, priority=1, kind="canvas")
        ls.current_layer_name = "canvas"
        ls.set("fg", self.stencil, priority=10, visible=self.stencil.enable, kind="stencil")
        return ls

    def reset_layers(self, canvas=None):
        """Discard all layers and start again with a single canvas layer."""
        if canvas is None:
            canvas = self.pixel_canvas
        self.layers = self.new_layer_stack(canvas)
        self.set_active_canvas(canvas)
        if "proj" in dir(self):
            self.proj[self.proj_index].layers = self.layers

    def set_active_canvas(self, surface):
        """Bind config.pixel_canvas to the active layer's surface.

        This is the only supported way to replace pixel_canvas: all tools,
        undo and file operations draw on pixel_canvas, so the active layer
        must own the very same Surface object.
        """
        if surface is None:
            return
        self.pixel_canvas = surface
        if self.layers is None:
            return
        layer = self.layers.get()
        if layer is not None and layer.kind in ("canvas", "user") and \
           isinstance(layer.image, pygame.Surface):
            layer.image = surface

    def select_layer(self, name):
        """Select a layer and make its surface the active drawing canvas."""
        if self.layers is None or not self.layers.has_key(name):
            return False
        layer = self.layers.get(name)
        if layer.kind not in ("canvas", "user"):
            return False
        if not isinstance(layer.image, pygame.Surface):
            return False
        self.layers.current_layer_name = name
        self.set_active_canvas(layer.image)
        # Layer selection is a property of the whole animation, not of one
        # frame.  Keep every frame pointing at the same layer so animpaint
        # (ALT + draw) stamps onto the selected layer in all frames.
        for st in self.layer_stacks():
            other = st.get(name) if st is not None and st.has_key(name) else None
            if other is not None and other.kind in ("canvas", "user"):
                st.current_layer_name = name
        return True

    def set_layer_visible(self, name, visible):
        """Show or hide the same layer in every animation frame."""
        for st in self.layer_stacks():
            layer = st.get(name) if st is not None and st.has_key(name) else None
            if layer is not None:
                layer.visible = visible

    def set_layer_opacity(self, name, opacity):
        """Set the same layer opacity in every animation frame."""
        for st in self.layer_stacks():
            layer = st.get(name) if st is not None and st.has_key(name) else None
            if layer is not None:
                layer.opacity = opacity

    def reset_draw_baseline(self):
        """Re-point the current undo tip at the active layer's pixels.

        Tools use ``clear_pixel_draw_canvas()`` to erase their on-screen
        preview between mouse moves.  That only works when the undo tip was
        captured for the layer being drawn on.  Selecting a different layer
        used to leave the tip tagged with the old layer, so every preview
        stayed on the new layer and looked like a held-down mouse button.
        Refresh just the tip; older undo history is left untouched.
        """
        idx = self.undo_index
        if idx < 0 or idx >= len(self.undo_image):
            return
        if not isinstance(self.pixel_canvas, pygame.Surface):
            return
        img = pygame.Surface(self.pixel_canvas.get_size(), 0, self.pixel_canvas)
        img.set_palette(self.pal)
        img.blit(self.pixel_canvas, (0, 0))
        self.undo_image[idx] = img
        while len(self.undo_layer) <= idx:
            self.undo_layer.append(None)
        self.undo_layer[idx] = self.layers.current_layer_name
        while len(self.undo_meta) <= idx:
            self.undo_meta.append(None)
        self.undo_meta[idx] = self._undo_meta()
        self.drawing_interrupted = False

    def layer_stacks(self):
        """Yield every layer stack in this project (current and animation)."""
        seen = set()
        stacks = [self.layers]
        anim = getattr(self, "anim", None)
        if anim is not None:
            stacks.extend([f.layers for f in anim.frame])
        for st in stacks:
            if st is not None and id(st) not in seen:
                seen.add(id(st))
                yield st

    def frame_layer_stacks(self):
        """Return the stacks that represent the visible animation frames.

        Single-frame pictures are edited through the live stack only; for
        animations every frame owns its own live stack.
        """
        if self.anim is None or self.anim.num_frames <= 1 or \
           len(self.anim.frame) <= 1:
            return [self.layers]
        return [self.ensure_frame_layers(f) for f in self.anim.frame]

    def ensure_frame_layers(self, frame):
        if frame.image is None:
            frame.image = pygame.Surface((self.pixel_width, self.pixel_height), 0, 8)
            frame.image.set_palette(self.pal)
        if frame.layers is None or not frame.layers.has_key("canvas"):
            frame.layers = self.new_layer_stack(frame.image)
        return frame.layers

    def first_free_layer_slot(self):
        used = set()
        for st in self.layer_stacks():
            for name in st.layers:
                layer = st.get(name)
                if layer.kind == "user":
                    used.add(layer.priority)
        for slot in range(2, 10):
            if slot not in used:
                return slot
        return None

    def layer_slot_is_free(self, slot):
        for st in self.layer_stacks():
            name = st.get_priority_name(slot)
            if name is not None and st.get(name).kind == "user":
                return False
        return True

    def add_layer(self, name=None, priority=None):
        if priority is None:
            priority = self.first_free_layer_slot()
        if priority is None:
            return None
        if name is None:
            name = f"layer{priority}"
        base = name
        n = 2
        while self.layers.has_key(name):
            name = f"{base}_{n}"
            n += 1
        surface = pygame.Surface((self.pixel_width, self.pixel_height), 0, 8)
        surface.set_palette(self.pal)
        surface.fill(0)
        self.layers.set(name, surface, priority=priority, kind="user")
        for st in self.layer_stacks():
            if st is self.layers:
                continue
            if not st.has_key("canvas"):
                continue
            if not st.has_key(name):
                img = pygame.Surface((self.pixel_width, self.pixel_height), 0, 8)
                img.set_palette(self.pal)
                img.fill(0)
                st.set(name, img, priority=priority, kind="user")
        self.select_layer(name)
        return name

    def delete_layer(self, name=None):
        if name is None:
            name = self.layers.current_layer_name
        layer = self.layers.get(name)
        if layer is None or layer.kind != "user":
            return False
        for st in self.layer_stacks():
            st.delete(name)
        if not self.select_layer("canvas"):
            # fall back to the topmost remaining user layer
            for st in [self.layers]:
                for other in reversed(st.sorted_layers()):
                    if other.kind == "user" and self.select_layer(st.get_priority_name(other.priority)):
                        break
        return True

    def move_layer(self, name, priority):
        """Move a layer to another slot, swapping with any layer already there."""
        layer = self.layers.get(name)
        if layer is None or layer.kind != "user" or priority in (0, 1, 10):
            return False
        if priority < 2 or priority > 9:
            return False
        old_priority = layer.priority
        other_name = self.layers.get_priority_name(priority)
        for st in self.layer_stacks():
            moving = st.get(name)
            if moving is None:
                continue
            other = st.get(other_name) if other_name is not None else None
            moving.priority = priority
            if other is not None and other is not moving:
                other.priority = old_priority
        self.layers.current_layer_name = name
        return True

    def clone_layer(self, name=None):
        if name is None:
            name = self.layers.current_layer_name
        layer = self.layers.get(name)
        if layer is None or layer.kind != "user":
            return None
        slot = self.first_free_layer_slot()
        if slot is None:
            return None
        new_name = self.add_layer(priority=slot)
        new_layer = self.layers.get(new_name)
        if new_layer is not None and isinstance(layer.image, pygame.Surface):
            new_layer.image.blit(layer.image, (0, 0))
        # Give the same starting image to the other frames.
        for st in self.layer_stacks():
            if st is self.layers:
                continue
            target = st.get(new_name)
            if target is not None and isinstance(target.image, pygame.Surface):
                target.image.blit(layer.image, (0, 0))
        return new_name

    def merge_layer_down(self, name=None):
        if name is None:
            name = self.layers.current_layer_name
        merged = False
        for st in self.layer_stacks():
            if st.has_key(name):
                if st is self.layers:
                    merged = st.merge_down(name)
                else:
                    # Merge into the layer below without disturbing the selection.
                    old_current = st.current_layer_name
                    st.current_layer_name = name
                    st.merge_down(name)
                    st.current_layer_name = old_current
                    if not st.has_key(st.current_layer_name):
                        st.current_layer_name = "canvas"
        if self.layers.has_key(name):
            self.layers.delete(name)
        if not self.layers.has_key(self.layers.current_layer_name):
            self.select_layer("canvas")
        return merged

    def transform_layers(self, func, kinds=("canvas", "user", "background", "reference")):
        """Apply a surface transformation to every 8-bit layer."""
        for st in self.layer_stacks():
            for name in list(st.layers.keys()):
                layer = st.get(name)
                if layer is None or layer.kind not in kinds:
                    continue
                if isinstance(layer.image, pygame.Surface):
                    layer.image = func(layer.image)
                    if layer.image.get_bytesize() == 1:
                        layer.image.set_palette(self.pal)
        current = self.layers.current_layer_name
        if not self.select_layer(current):
            self.select_layer("canvas")

    def fit_layers_to_page(self, scale=True):
        """Resize every layer (except the canvas) to the current page size."""
        w, h = self.pixel_width, self.pixel_height
        for st in self.layer_stacks():
            for name, layer in list(st.layers.items()):
                if name == "canvas" or not isinstance(layer.image, pygame.Surface):
                    continue
                if layer.image.get_size() == (w, h):
                    continue
                layer.image = self._resize_surface(layer.image, w, h, scale)

    def bootstrap_layers(self):
        """Bind the layer stack to the freshly loaded pixel canvas.

        Called from initialize_surfaces() after a picture has been loaded,
        resized or a new screen format has been selected.
        """
        pending = getattr(self, "pending_ora_layers", None)
        if pending:
            self.layers = self.new_layer_stack(self.pixel_canvas)
            canvas_image = self.pixel_canvas
            for item in pending:
                name = item.get("name", "layer")
                img = item.get("image")
                if img is not None and img.get_bytesize() == 1:
                    img.set_palette(self.pal)
                if name == "canvas":
                    # Replace the canvas that new_layer_stack() just made.
                    self.layers.set("canvas", img, priority=1,
                                    visible=item.get("visible", True),
                                    opacity=item.get("opacity", 255),
                                    kind="canvas",
                                    indicator=item.get("indicator", ""))
                    canvas_image = img
                    continue
                while self.layers.has_key(name):
                    name += "_"
                self.layers.set(name, img, priority=item.get("priority", 2),
                                visible=item.get("visible", True),
                                opacity=item.get("opacity", 255),
                                kind=item.get("kind", "user"),
                                indicator=item.get("indicator", ""))
            self.layers.current_layer_name = "canvas"
            self.pixel_canvas = canvas_image
            self.pending_ora_layers = None
            self.layers_loaded = False
        elif self.layers_loaded or self.layers is None or \
             not self.layers.has_key("canvas"):
            # A new picture was loaded: discard the old layer structure.
            self.layers = self.new_layer_stack(self.pixel_canvas)
            self.layers_loaded = False
        else:
            # Resizing / screen-format change: keep the existing layers.
            self.layers.set("fg", self.stencil, priority=10,
                            visible=self.stencil.enable, kind="stencil")
            canvas_layer = self.layers.get("canvas")
            if canvas_layer is None or not isinstance(canvas_layer.image, pygame.Surface):
                self.layers.set("canvas", self.pixel_canvas, priority=1, kind="canvas")
            if not self.layers.has_key(self.layers.current_layer_name):
                self.layers.current_layer_name = "canvas"
            self.fit_layers_to_page(scale=False)

        self.set_active_canvas(self.pixel_canvas)
        if "anim" in dir(self) and self.anim is not None and \
           0 <= self.anim.curr_frame-1 < len(self.anim.frame):
            # The frame the editor is showing must share the live stack.
            frame = self.anim.frame[self.anim.curr_frame-1]
            frame.layers = self.layers
            canvas_layer = self.layers.get("canvas")
            if canvas_layer is not None and \
               isinstance(canvas_layer.image, pygame.Surface):
                frame.image = canvas_layer.image
        if "proj" in dir(self):
            self.proj[self.proj_index].layers = self.layers
            self.proj[self.proj_index].pixel_canvas = self.pixel_canvas

    def initialize_surfaces(self, reinit=False, first_init=False):
        sm = config.display_info.get_id(self.display_mode)
        if sm is None:
            self.display_mode = 0x00011000
            sm = config.display_info.get_id(self.display_mode)
        pixel_size = self.pixel_canvas.get_size()
        if pixel_size[0] >= sm.x and pixel_size[0] <= sm.max_x and \
           pixel_size[1] >= sm.y and pixel_size[1] <= sm.max_y:
            #overscan
            self.screen_width = pixel_size[0]
            self.screen_height = pixel_size[1]
        else:
            self.screen_width = sm.x
            self.screen_height = sm.y

        if config.force_1_to_1_pixels:
            self.pixel_aspect = sm.aspect_y / sm.aspect_x
            self.pixel_mode = "square"
        else:
            self.pixel_aspect = sm.aspect
            self.pixel_mode = sm.get_pixel_mode()
        self.aspectX = sm.aspect_x
        self.aspectY = sm.aspect_y
        self.sm = sm

        if reinit:
            config.anim = libs.animation.Animation()
            config.truepal = config.get_default_palette(config.NUM_COLORS)
            config.pal = list(config.truepal)
            config.pixel_canvas = pygame.Surface((self.screen_width, self.screen_height),0,8)

        self.pixel_width, self.pixel_height = self.pixel_canvas.get_size()

        self.screen_offset_x = 0
        self.screen_offset_y = 0
        if self.pixel_width < self.screen_width:
            self.screen_offset_x = (self.screen_width - self.pixel_width) // 2
        if self.pixel_height < self.screen_height:
            self.screen_offset_y = (self.screen_height - self.pixel_height) // 2

        self.pixel_req_canvas = pygame.Surface((self.screen_width, self.screen_height))
        self.pixel_req_rect = None

        self.symm_center = (self.pixel_width//2, self.pixel_height//2)

        self.bootstrap_layers()

        #adjust fonts
        self.fontx = self.closest_scale4(32, self.screen_width // 40)
        self.fonty = self.closest_scale4(32, self.screen_height // 25)
        self.font = PixelFont("jewel32.png", sizeX=self.fontx, sizeY=self.fonty)
        self.fonty = int(self.fonty * 1.5)

        if first_init:
            config.scale = round(config.closest_scale())
            config.resize_display()
        else:
            config.scale = config.closest_scale()
            config.resize_display(False)

        self.primprops = PrimProps()
        self.matte_erase = False
        self.last_drawmode = 2
        self.drawmode = self.primprops.drawmode
        self.fillmode = self.primprops.fillmode
        config.color = 1
        config.bgcolor = 0

        #Turn off toggle tools
        config.grid_on = False
        config.symm_on = False
        config.zoom.on = False
        config.zoom.box_on = False

        #Keep project canvas if same size as new image
        for i in range(len(self.proj)):
            if i == self.proj_index:
                continue
            if self.proj[i].pixel_canvas:
                sw, sh = self.proj[i].pixel_canvas.get_size()
                if sw == self.pixel_width and sh == self.pixel_height:
                    self.proj[i].pixel_canvas.set_palette(self.pal)
                else:
                    self.proj[i].pixel_canvas = pygame.Surface((self.pixel_width, self.pixel_height),0, self.pixel_canvas)
            else:
                self.proj[i].pixel_canvas = pygame.Surface((self.pixel_width, self.pixel_height),0, self.pixel_canvas)
            if self.proj[i].anim.num_frames == 1:
                self.proj[i].anim.frame = [Frame(self.proj[i].pixel_canvas)]

        self.scaled_image = pygame.Surface((self.screen_width, self.screen_height*2))
        cursor_images = pygame.image.load(os.path.join('data', 'cursors.png'))
        self.cursor = cursor(self.sm.scaleX, self.sm.scaleY*2, self, cursor_images)
        self.toolbar = init_toolbar(config)
        self.menubar = init_menubar(config)
        self.minitoolbar = init_minitoolbar(config)
        self.animtoolbar = init_animtoolbar(config)
        self.layertoolbar = init_layertoolbar(config)
        self.all_toolbars = [
            self.toolbar,
            self.menubar,
            self.minitoolbar,
            self.animtoolbar,
            self.layertoolbar,
        ]
        self.smooth_example_image = pygame.image.load(os.path.join('data', 'smooth_example.png'))

        px = self.font.xsize // 8
        py = self.font.ysize // 8

        self.layout = Layout([
                LayoutTile("menubar", (0,self.menubar.rect[3]), drawable=self.menubar, overlap_offset=[0,0,py,0]),
                LayoutTile("layertoolbar", (self.layertoolbar.rect[2],0), visible=False, drawable=self.layertoolbar, overlap_offset=[0,0,0,0]),
                LayoutTile("canvas", (self.screen_width,self.screen_height)),
                LayoutTile("animtoolbar", (0,self.animtoolbar.rect[3]), visible=False, drawable=self.animtoolbar, overlap_offset=[py*2,0,0,0]),
                LayoutTile("toolbar", (self.toolbar.rect[2],0), drawable=self.toolbar, overlap_offset=[py,0,0,0]),
                ],
            overlap=not config.toolbars_outside)

        self.scanline_canvas = pygame.Surface((self.screen_width, self.screen_height*2), SRCALPHA)
        for i in range(0, self.screen_height*2, 2):
            pygame.draw.line(self.scanline_canvas, Color(0,0,0,100), (0,i), (self.screen_width,i), 1)

        self.NUM_COLORS = len(self.pal)
        self.set_all_palettes(self.pal)
        for i in range(len(self.proj)):
            self.proj[i].stencil.clear()
            self.proj[i].stencil.free()

        self.perspective = Perspective()

        # set prefs
        self.menubar.menu_id("prefs").menu_id("coords").menu_id("show").checked = self.coords_on
        self.menubar.menu_id("prefs").menu_id("coords").menu_id("flip").checked = self.coords_flip
        self.menubar.menu_id("prefs").menu_id("coords").menu_id("1based").checked = self.coords_1based
        self.menubar.menu_id("prefs").menu_id("autotransp").checked = self.auto_transp_on
        self.menubar.menu_id("prefs").menu_id("multicycle").checked = self.multicycle
        self.menubar.menu_id("prefs").menu_id("exclbrush").checked = self.exclbrush
        self.menubar.menu_id("prefs").menu_id("hidemenus").checked = self.hide_menus
        self.menubar.menu_id("prefs").menu_id("forcepixels").checked = self.force_1_to_1_pixels
        self.menubar.menu_id("prefs").menu_id("truesymmetry").checked = self.true_symmetry
        self.menubar.menu_id("prefs").menu_id("sysfiledialog").checked = self.sys_file_dialog
        self.menubar.menu_id("prefs").menu_id("ctrlpickoverride").checked = self.ctrl_pick_override
        self.menubar.menu_id("prefs").menu_id("toolbarsoutside").checked = self.toolbars_outside
        self.menubar.hide_menus = self.hide_menus

        self.brush = Brush()

        self.clear_undo()
        config.toolbar.click(config.toolbar.tool_id("draw"), MOUSEBUTTONDOWN)
        config.toolbar.click(config.toolbar.tool_id("circle1"), MOUSEBUTTONDOWN)
        config.save_undo()

    def inside_toolbars(self, toolbar_list, coords):
        inside = False
        for tb in toolbar_list:
            if tb.is_inside(coords):
                inside = True
                break
        return inside

    def guess_color_depth(self, pal):
        # pictures with more than 32 colors are not Amiga OCS/ECS
        if len(pal) > 32:
            return 256

        #check for colors not in 4096 palette
        is_mod16 = True
        for i in range(len(pal)):
            if pal[i][0] % 16 == 0 and pal[i][1] % 16 == 0 and pal[i][2] % 16 == 0:
                pass
            else:
                is_mod16 = False
        is_mod17 = True
        for i in range(len(pal)):
            if pal[i][0] % 17 == 0 and pal[i][1] % 17 == 0 and pal[i][2] % 17 == 0:
                pass
            else:
                is_mod17 = False
        if is_mod16 or is_mod17:
            color_depth = 16
        else:
            color_depth = 256
        return color_depth

    def get_default_palette(self, numcols=32):
        if numcols == 64 and config.display_mode & config.MODE_EXTRA_HALFBRIGHT:
            newpal = [
                (0,0,0), (238,204,170), (255,0,0), (204,0,0), (170,0,0), (0,221,0),
                (0,170,0), (0,136,0), (0,0,255), (0,0,204), (0,0,170), (255,255,68),
                (204,204,17), (153,153,17), (0,255,255), (0,187,187), (0,153,153),
                (238,0,153), (187,0,119), (153,0,102), (221,68,17), (170,51,17),
                (136,34,17), (0,153,255), (0,102,204), (0,68,153), (17,204,136),
                (17,153,102), (68,119,85), (255,255,255), (204,204,204), (153,153,153),
                (0,0,0), (119,102,85), (119,0,0), (102,0,0), (85,0,0), (0,102,0),
                (0,85,0), (0,68,0), (0,0,119), (0,0,102), (0,0,85), (119,119,34),
                (102,102,0), (68,68,0), (0,119,119), (0,85,85), (0,68,68), (119,0,68),
                (85,0,51), (68,0,51), (102,34,0), (85,17,0), (68,17,0), (0,68,119),
                (0,51,102), (0,34,68), (0,102,68), (0,68,51), (34,51,34), (119,119,119),
                (102,102,102), (68,68,68)]
        else:
            newpal = [(0,0,0), (224,192,160), (224,0,0), (160,0,0), (208,128,0), (240,224,0),
            (128,240,0), (0,128,0), (0,196,96), (0,208,208), (0,160,240), (0,112,192),
            (0,0,240), (112,0,240), (192,0,224), (198,0,128), (96,32,0), (224,80,32),
            (160,80,32), (240,192,160), (48,48,48), (64,64,64), (80,80,80), (96,96,96),
            (112,112,112), (128,128,128), (144,144,144), (160,160,160), (192,192,192),
            (208,208,208), (224,224,224), (240,240,240),
            #colors from the Windows palette to fill out the rest
            (42,255,0),(42,255,85),(42,255,170),(42,255,255),(85,0,0),(85,0,85),
            (85,0,170),(85,0,255),(85,31,0),(85,31,85),(85,31,170),(85,31,255),
            (85,63,0),(85,63,85),(85,63,170),(85,63,255),
            (85,95,0),(85,95,85),(85,95,170),(85,95,255),(85,127,0),(85,127,85),
            (85,127,170),(85,127,255),(85,159,0),(85,159,85),(85,159,170),(85,159,255),
            (85,191,0),(85,191,85),(85,191,170),(85,191,255),
            (85,223,0),(85,223,85),(85,223,170),(85,223,255),(85,255,0),(85,255,85),
            (85,255,170),(85,255,255),(127,0,0),(127,0,85),(127,0,170),(127,0,255),
            (127,31,0),(127,31,85),(127,31,170),(127,31,255),
            (127,63,0),(127,63,85),(127,63,170),(127,63,255),(127,95,0),(127,95,85),
            (127,95,170),(127,95,255),(127,127,0),(127,127,85),(127,127,170),(127,127,255),
            (127,159,0),(127,159,85),(127,159,170),(127,159,255),
            (127,191,0),(127,191,85),(127,191,170),(127,191,255),(127,223,0),(127,223,85),
            (127,223,170),(127,223,255),(127,255,0),(127,255,85),(127,255,170),(127,255,255),
            (170,0,0),(170,0,85),(170,0,170),(170,0,255),
            (170,31,0),(170,31,85),(170,31,170),(170,31,255),(170,63,0),(170,63,85),
            (170,63,170),(170,63,255),(170,95,0),(170,95,85),(170,95,170),(170,95,255),
            (170,127,0),(170,127,85),(170,127,170),(170,127,255),
            (170,159,0),(170,159,85),(170,159,170),(170,159,255),(170,191,0),(170,191,85),
            (170,191,170),(170,191,255),(170,223,0),(170,223,85),(170,223,170),(170,223,255),
            (170,255,0),(170,255,85),(170,255,170),(170,255,255),
            (212,0,0),(212,0,85),(212,0,170),(212,0,255),(212,31,0),(212,31,85),
            (212,31,170),(212,31,255),(212,63,0),(212,63,85),(212,63,170),(212,63,255),
            (212,95,0),(212,95,85),(212,95,170),(212,95,255),
            (212,127,0),(212,127,85),(212,127,170),(212,127,255),(212,159,0),(212,159,85),
            (212,159,170),(212,159,255),(212,191,0),(212,191,85),(212,191,170),(212,191,255),
            (212,223,0),(212,223,85),(212,223,170),(212,223,255),
            (212,255,0),(212,255,85),(212,255,170),(212,255,255),(255,0,85),(255,0,170),
            (255,31,0),(255,31,85),(255,31,170),(255,31,255),(255,63,0),(255,63,85),
            (255,63,170),(255,63,255),(255,95,0),(255,95,85),
            (255,95,170),(255,95,255),(255,127,0),(255,127,85),(255,127,170),(255,127,255),
            (255,159,0),(255,159,85),(255,159,170),(255,159,255),(255,191,0),(255,191,85),
            (255,191,170),(255,191,255),(255,223,0),(255,223,85),
            (255,223,170),(255,223,255),(255,255,85),(255,255,170),(204,204,255),(255,204,255),
            (51,255,255),(102,255,255),(153,255,255),(204,255,255),(0,127,0),(0,127,85),
            (0,127,170),(0,127,255),(0,159,0),(0,159,85),
            (0,159,170),(0,159,255),(0,191,0),(0,191,85),(0,191,170),(0,191,255),
            (0,223,0),(0,223,85),(0,223,170),(0,223,255),(0,255,85),(0,255,170),
            (42,0,0),(42,0,85),(42,0,170),(42,0,255),
            (42,31,0),(42,31,85),(42,31,170),(42,31,255),(42,63,0),(42,63,85),
            (255,251,240),(160,160,164),(128,128,128),(255,0,0),(0,255,0),(255,255,0),
            (0,0,255),(255,0,255),(0,255,255),(255,255,255)]

        return newpal[0:numcols]

    def saveConfig(self):
        try:
            sm = config.display_info.get_id(self.display_mode)
            f = open(config.args.config,"w")
            f.write("display_mode=%08x\n" % (self.display_mode))
            f.write("pixel_width=%d\n" % (self.pixel_width))
            f.write("pixel_height=%d\n" % (self.pixel_height))
            f.write("screen_width=%d\n" % (self.screen_width))
            f.write("screen_height=%d\n" % (self.screen_height))
            f.write("color_depth=%d\n" % (self.color_depth))
            f.write("NUM_COLORS=%d\n" % (self.NUM_COLORS))
            f.write("pixel_mode=%s\n" % (self.pixel_mode))
            f.write("pixel_aspect=%f\n" % (self.pixel_aspect))
            f.write("aspectX=%f\n" % (sm.aspect_x))
            f.write("aspectY=%f\n" % (sm.aspect_y))
            f.write("filepath=%s\n" % (self.filepath))
            f.write("fullscreen=%s\n" % (self.fullscreen))
            f.write("scale=%f\n" % (self.scale))
            f.write("scanlines=%d\n" % (self.scanlines))
            f.write("coords_on=%s\n" % (self.coords_on))
            f.write("coords_flip=%s\n" % (self.coords_flip))
            f.write("coords_1based=%s\n" % (self.coords_1based))
            f.write("auto_transp_on=%s\n" % (self.auto_transp_on))
            f.write("multicycle=%s\n" % (self.multicycle))
            f.write("exclbrush=%s\n" % (self.exclbrush))
            f.write("hide_menus=%s\n" % (config.menubar.hide_menus))
            f.write("force_1_to_1_pixels=%s\n" % (self.force_1_to_1_pixels))
            f.write("true_symmetry=%s\n" % (self.true_symmetry))
            f.write("sys_file_dialog=%s\n" % (self.sys_file_dialog))
            f.write("ctrl_pick_override=%s\n" % (self.ctrl_pick_override))
            f.write("toolbars_outside=%s\n" % (self.toolbars_outside))
            for k in self.user_hotkeys.keys():
                h = self.user_hotkeys[k]
                f.write("hotkey_%s=%s\n" % (str(h), str(h.attrs["map_to"])))
            f.close()
        except:
            pass

    def readConfig(self):
        try:
            f = open(config.args.config,"r")
            for line in f:
                if len(line) < 1 or line.find("=") < 0:
                    continue
                if line.lstrip()[0] == '#':
                    continue
                vars = line.strip().split("=")
                if len(vars) == 2:
                    if vars[0] == "display_mode":
                        self.display_mode = int(vars[1], 16)
                    elif vars[0] == "pixel_width":
                        self.pixel_width = int(vars[1])
                    elif vars[0] == "pixel_height":
                        self.pixel_height = int(vars[1])
                    elif vars[0] == "screen_width":
                        self.screen_width = int(vars[1])
                    elif vars[0] == "screen_height":
                        self.screen_height = int(vars[1])
                    elif vars[0] == "color_depth":
                        self.color_depth = int(vars[1])
                    elif vars[0] == "NUM_COLORS":
                        self.NUM_COLORS = int(vars[1])
                    elif vars[0] == "pixel_mode":
                        self.pixel_mode = vars[1]
                    elif vars[0] == "pixel_aspect":
                        self.pixel_aspect = float(vars[1])
                    elif vars[0] == "aspectX":
                        self.aspectX = float(vars[1])
                    elif vars[0] == "aspectY":
                        self.aspectY = float(vars[1])
                    elif vars[0] == "filepath":
                        self.filepath = vars[1]
                    elif vars[0] == "fullscreen":
                        self.fullscreen = True if vars[1] == "True" else False
                    elif vars[0] == "scale":
                        self.scale = float(vars[1])
                        config.resize_display()
                    elif vars[0] == "scanlines":
                        self.scanlines = int(vars[1])
                    elif vars[0] == "coords_on":
                        self.coords_on = True if vars[1] == "True" else False
                    elif vars[0] == "coords_flip":
                        self.coords_flip = True if vars[1] == "True" else False
                    elif vars[0] == "coords_1based":
                        self.coords_1based = True if vars[1] == "True" else False
                    elif vars[0] == "auto_transp_on":
                        self.auto_transp_on = True if vars[1] == "True" else False
                    elif vars[0] == "multicycle":
                        self.multicycle = True if vars[1] == "True" else False
                    elif vars[0] == "exclbrush":
                        self.exclbrush = True if vars[1] == "True" else False
                    elif vars[0] == "hide_menus":
                        self.hide_menus = True if vars[1] == "True" else False
                    elif vars[0] == "force_1_to_1_pixels":
                        self.force_1_to_1_pixels = True if vars[1] == "True" else False
                    elif vars[0] == "true_symmetry":
                        self.true_symmetry = True if vars[1] == "True" else False
                    elif vars[0] == "sys_file_dialog":
                        self.sys_file_dialog = True if vars[1] == "True" else False
                    elif vars[0] == "ctrl_pick_override":
                        self.ctrl_pick_override = True if vars[1] == "True" else False
                    elif vars[0] == "toolbars_outside":
                        self.toolbars_outside = True if vars[1] == "True" else False
                    elif vars[0][:7] == "hotkey_":
                        map_to = vars[0][7:]
                        map_from = vars[1]
                        self.user_hotkeys.add(HotKey(map_to, attrs={"map_to": HotKey(map_from)}))
            f.close()
            return True
        except:
            pass
        return False

    def new_custom_event(self):
        global custom_event_counter
        user_event = None
        if "custom_type" in dir(pygame.event):
            user_event = config.xevent.custom_type()
        else:
            user_event = USEREVENT + custom_event_counter
            custom_event_counter += 1
        self.ALLCUSTOMEVENTS.append(user_event)
        return user_event

    def initialize(self):
        self.clock = pygame.time.Clock()
        self.debug = False

        self.MODE_LACE               = 0x0004
        self.MODE_EXTRA_HALFBRIGHT   = 0x0080
        self.MODE_HAM                = 0x0800
        self.MODE_HIRES              = 0x8000
        self.NTSC_MONITOR_ID         = 0x00011000
        self.PAL_MONITOR_ID          = 0x00021000
        self.VGA_MONITOR_ID          = 0x00031000
        self.MONITOR_ID_MASK         = 0x00031000
        self.MODE_VGA_MCGA_KEY       = 0x00031000
        self.MODE_VGA_VGA_KEY        = 0x00039004
        self.MODE_VGA_SVGA_KEY       = 0x00039005
        self.MODE_VGA_XGA_KEY        = 0x00039006
        self.OCS_MODES = self.MODE_LACE | self.MODE_EXTRA_HALFBRIGHT | self.MODE_HAM | self.MODE_HIRES | self.NTSC_MONITOR_ID | self.PAL_MONITOR_ID

        self.display_info = DisplayInfo()

        self.pygame_version = "pygame"
        if "print_debug_info" in dir(pygame):
            self.pygame_version += "-ce"
        self.pygame_version += f" {pygame.version.ver}"

        self.xevent = Xevent()
        self.fontx = fontx
        self.fonty = fonty
        self.text_tool_font_name = re.sub(r'\..{1,3}$', '', pygame.font.get_default_font())
        self.text_tool_font_name = re.sub(r'bold$', '', self.text_tool_font_name)
        self.text_tool_font_type = 0
        self.text_tool_font_size = 16
        self.text_tool_font_antialias = True
        self.text_tool_font_bold = False
        self.text_tool_font_italic = False
        self.text_tool_font_underline = False
        self.text_tool_font = pygame.font.Font(pygame.font.match_font(self.text_tool_font_name), self.text_tool_font_size)
        self.last_recompose_timer = 0
        self.window_canvas_rect = [0,0,1,1]
        self.max_width = self.dinfo.current_w
        self.max_height = self.dinfo.current_h
        self.max_width_init = self.dinfo.current_w
        self.max_height_init = self.dinfo.current_h
        #Setup the pygame screen
        self.pixel_width = 320
        self.pixel_height = 200
        self.screen_width = self.pixel_width
        self.screen_height = self.pixel_height
        self.screen_offset_x = 0
        self.screen_offset_y = 0
        self.screen_width_min = 320
        self.screen_height_min = 200
        self.screen_width_max = 640
        self.screen_height_max = 512
        self.pixel_modes = ["square","NTSC","PAL"]
        self.pixel_aspects = [1.0, 10.0/11.0, 59.0/54.0]
        self.pixel_mode = "NTSC"
        self.pixel_aspect = 10.0/11.0 #NTSC
        self.aspectX = 1
        self.aspectY = 1
        self.color_depth = 16
        self.fullscreen = False
        self.display_mode = config.getPalNtscDefault()
        if self.display_mode & self.PAL_MONITOR_ID == self.PAL_MONITOR_ID:
            self.pixel_height = 256
            self.screen_height_min = 256
            self.pixel_mode = "PAL"
            self.pixel_aspect = 59.0/54.0 #PAL

        self.LAYER_INDICATORX = 170
        self.LAYER_BG_PRIORITY = 0

        self.scale = 3
        self.scale_bak = 3
        self.SCANLINES_ON = 0
        self.SCANLINES_OFF = 1
        self.SCANLINES_NOSMOOTH = 2
        self.scanlines = self.SCANLINES_ON
        self.brush = Brush()
        self.brush_req_props = BrushReqProps()

        self.primprops = PrimProps()
        self.matte_erase = False
        self.last_drawmode = 2
        self.drawmode = self.primprops.drawmode
        self.fillmode = self.primprops.fillmode
        self.color = 1
        self.bgcolor = 0
        self.drawing_interrupted = False

        self.proj = [Project(), Project()]
        self.proj_index = 0
        self.palette_page = 0
        self.NUM_COLORS = 32
        self.filename = ""
        self.filepath = os.path.expanduser("~")
        self.proj[0].filename = self.filename
        self.proj[0].filepath = self.filepath
        self.proj[1].filename = self.filename
        self.proj[1].filepath = self.filepath
        self.toolmode = 0
        self.tool_selected = 0
        self.subtool_selected = 0
        self.zoom = Zoom(config)
        self.grid_on = False
        self.grid_size = (10,10)
        self.grid_offset = (0,0)
        self.grid_visible = False
        self.grid_style = GRID_DOTTED
        self.grid_color = (255,255,255)
        self.grid_alpha = 128
        self.grid = Grid()
        self.symm_on = False
        self.symm_center = (160,100)
        self.symm_mode = 0
        self.symm_type = 1
        self.symm_num = 6
        self.symm_width = 50
        self.symm_height = 50
        self.enable_constrain = True
        self.constrain_x = -1
        self.constrain_y = -1
        self.help_on = True
        self.p1 = None
        self.polylist = []
        self.airbrush_size = 10
        self.coords_on = False
        self.coords_flip = False
        self.coords_1based = False
        self.auto_transp_on = False
        self.multicycle = False
        self.exclbrush = False
        self.hide_menus = False
        self.force_1_to_1_pixels = False
        self.true_symmetry = False
        self.sys_file_dialog = False
        self.ctrl_pick_override = False
        self.toolbars_outside = False
        self.user_hotkeys = HotKeyMap()
        config.resize_display()
        pygame.display.set_caption("PyDPainter")
        pygame.display.set_icon(pygame.image.load(os.path.join('data', 'logo.png')))
        pygame.key.set_repeat(500, 50)

        self.pixel_canvas = pygame.Surface((self.pixel_width, self.pixel_height),0,8)
        self.pal = self.get_default_palette()
        self.pal = quantize_palette(self.pal, self.color_depth)
        self.backuppal = list(self.pal)
        self.truepal = list(self.pal)
        self.loadpal = list(self.pal)
        self.pixel_canvas.set_palette(self.pal)

        self.layers = LayerStack(indicatorx=self.LAYER_INDICATORX)
        self.layers.set("canvas", self.pixel_canvas, priority=1, kind="canvas")
        self.layers.current_layer_name = "canvas"
        self.stencil = Stencil()
        self.layers.set("fg", self.stencil, 10, visible=self.stencil.enable, kind="stencil")

        self.anim = Animation()
        self.proj[0].anim = self.anim
        self.proj[1].anim = Animation()
        self.proj[0].layers = self.layers
        self.proj[1].layers = LayerStack(indicatorx=self.LAYER_INDICATORX)
        self.proj[0].stencil = self.stencil
        self.proj[1].stencil = Stencil()

        self.cycling = False
        self.cycle_handled = False
        self.cranges = [colorrange(5120,1,20,31), colorrange(2560,1,3,7), colorrange(2560,1,0,0), colorrange(2560,1,0,0), colorrange(2560,1,0,0), colorrange(2560,1,0,0)]

        self.meta_alt = 0
        self.last_mouse_nudge_time = 0
        self.nudge_accel = 1
        self.NUDGE_ACCEL_MAX = 20
        self.busy_start_time = 0
        self.busy_last_coords = (0,0)
        self.BUSY_LAG_TIME = 500

        self.dropper = False
        self.pick_canvas = None
        self.pick_canvas_offset = [0,0]
        self.pick_canvas_font = None
        self.pick_canvas_font_size = 0

        #Allocate user events
        self.ALLCUSTOMEVENTS = []

        #Tool user event - airbrush spray, text cursor blink, etc
        self.TOOLEVENT = config.new_custom_event()

        #Color cycling user events
        self.CYCLEEVENTS = []
        for i in range(len(self.cranges)):
            self.CYCLEEVENTS.append(config.new_custom_event())

        #Tool tip delay user event
        self.TOOLTIPEVENT = config.new_custom_event()

        self.window_title = "PyDPainter"
        self.modified_count = -1
        self.proj[0].modified_count = -1
        self.proj[1].modified_count = -1
        self.UNDO_INDEX_MAX = 256
        self.undo_image = []
        self.undo_layer = []
        self.undo_stack = []
        self.undo_meta = []
        self.undo_index = -1
        self.layers_loaded = False
        self.pending_ora_layers = None
        self.suppress_undo = False
        self.suppress_redraw = False
        self.running = True

        self.tool_visibility_state = 1
        self.tool_visibility_states = [
            #toolbar, menubar, animtoolbar, layertoolbar
            [ #animation
                (False,False,False,False),
                (True,True,True,None),
                (True,True,False,None),
                (False,True,False,None),
                (False,False,True,None),
            ],
            [ # single frame
                (False,False,False,False),
                (True,True,False,None),
            ],
            [ # animation playing
                (False,False,False,False),
                (False,False,True,None),
            ],
        ]

        self.wait_for_mouseup = [False, False]

        reinit = self.readConfig()

        self.initialize_surfaces(reinit=reinit, first_init=True)
        pygame.mouse.set_visible(False)

    def get_mouse_pressed(self, e=None):
        if e != None and "mods" in dir(e):
            mods = e.mods
        else:
            mods =  pygame.key.get_mods()
        config.meta_alt = 0
        if mods & KMOD_META:
            if mods & KMOD_LALT:
                config.meta_alt = 1
            if mods & KMOD_RALT:
                config.meta_alt = 3

        if config.meta_alt == 0:
            if e != None and "buttons" in dir(e):
                buttons = e.buttons
            else:
                buttons = pygame.mouse.get_pressed()
        elif config.meta_alt == 1:
            buttons = (1,0,0)
        elif config.meta_alt == 3:
            buttons = (0,0,1)
        return buttons

    def doKeyAction(self, curr_action=None):
        if not config.anim.playing:
            if curr_action == None:
                curr_action = config.toolbar.tool_id(config.tool_selected).action
            if self.get_mouse_pressed() == (0,0,0):
                curr_action.move(config.get_mouse_pixel_pos())
            else:
                curr_action.drag(config.get_mouse_pixel_pos(), self.get_mouse_pressed())

    def getPalNtscDefault(self):
        display_mode = self.PAL_MONITOR_ID

        #guess PAL or NTSC default by time zone
        UTC_offset = int(round((datetime.datetime.now() - datetime.datetime.utcnow()).seconds/60/60,2))
        if UTC_offset > 12:
            UTC_offset -= 24

        if UTC_offset >= -10 and UTC_offset <= -4: #North/South America
            display_mode = self.NTSC_MONITOR_ID
        elif UTC_offset == 9: #Japan
            display_mode = self.NTSC_MONITOR_ID

        return display_mode

    def setDrawMode(self, dm):
        mg = config.menubar.menu_id("mode")
        if config.brush.type == Brush.CUSTOM:
            mg.menug_list[0].enabled = True
            mg.menug_list[2].enabled = True
        else:
            mg.menug_list[0].enabled = False
            mg.menug_list[2].enabled = False

        g = config.menubar.menu_id("mode").menu_id(str(DrawMode(dm)))
        if g != None:
            g.action.selected({})
        return

    def quantize_palette(self, pal, color_depth=16):
        return quantize_palette(pal, color_depth)

    def unique_palette(self, pal):
        return unique_palette(pal)

    def set_anim_palettes(config, anim, pal_in, pal, truepal):
        # Set colors for animation frames
        if anim.global_palette:
            for frame in anim.frame:
                frame.pal = list(pal_in)
                if truepal != None:
                    frame.truepal = list(truepal)
                if frame.image != None:
                    frame.image.set_palette(pal)
        else:
            from_key, to_key = anim.pal_key_range()
            for frame in anim.frame[from_key-1:to_key]:
                frame.pal = list(pal_in)
                if truepal != None:
                    frame.truepal = list(truepal)
                if frame.image != None:
                    frame.image.set_palette(pal)

    def set_all_palettes(config, pal_in, truepal=None):
        if len(pal_in) == 256:
            pal = pal_in
        else:
            #Fill upper palette with BG color so smoothing gets valid colors
            pal = list(pal_in)
            pal.extend([pal_in[0]] * (256 - len(pal)))

        # Collect every layer stack: live stack, animation frames, and the
        # spare project.  Previously only stale copies were updated, so an
        # 8-bit background kept its old palette after a colour change.
        stacks = []
        seen = set()
        def add_stack(st):
            if st is not None and id(st) not in seen:
                seen.add(id(st))
                stacks.append(st)

        add_stack(config.layers)
        if config.anim is not None:
            for frame in config.anim.frame:
                add_stack(frame.layers)
        for proj in config.proj:
            add_stack(proj.layers)
            if proj.anim is not None:
                for frame in proj.anim.frame:
                    add_stack(frame.layers)
            if proj.pixel_canvas is not None:
                proj.pixel_canvas.set_palette(pal)
            if proj.anim is not None:
                config.set_anim_palettes(proj.anim, pal_in, pal, truepal)

        config.pixel_canvas.set_palette(pal)
        for st in stacks:
            st.set_palette(pal)

        config.brush.set_palettes(pal)

        for img in config.undo_image:
            if isinstance(img, pygame.Surface):
                img.set_palette(pal)

        config.set_anim_palettes(config.anim, pal_in, pal, truepal)

    def calc_tool_visibility_state(self):
        #Set mode: 0=animation, 1=single frame, 2=animation playing
        mode=0
        state = config.tool_visibility_state

        if config.toolbars_outside:
            if config.anim.num_frames == 1:
                mode=1
            if state > 1:
                state = 0
        elif config.anim.playing:
            mode=2
        elif config.anim.num_frames == 1:
            mode=1

        state = state % len(config.tool_visibility_states[mode])

        config.layout.set_visible("toolbar", config.tool_visibility_states[mode][state][0])
        config.layout.set_visible("menubar", config.tool_visibility_states[mode][state][1])
        config.layout.set_visible("animtoolbar", config.tool_visibility_states[mode][state][2])
        layer_state = config.tool_visibility_states[mode][state][3]
        if layer_state is not None:
            config.layout.set_visible("layertoolbar", layer_state)

        if config.menubar.visible:
            if config.animtoolbar.visible or config.anim.num_frames == 1:
                config.menubar.title = "PyDPainter"
            else:
                title = f"{config.anim.curr_frame}/{config.anim.num_frames}" + (" " * 10)
                config.menubar.title = title[:10]

        config.tool_visibility_state = state

    def set_screen_offset(self, x, y):
        # calculate offsets for toolbars and menubar if visible
        menubar, layers, canvas, animbar, tools = config.layout.calc_assign_vars()

        if config.layout.overlap:
            vp_width = canvas.w - (layers.w + layers.ovr + tools.w + tools.ovl)
            vp_x = layers.w + layers.ovr
            vp_height = canvas.h - (menubar.h + menubar.ovb + animbar.h + animbar.ovt)
            vp_y = menubar.h

            #Restrict to left of page
            if self.screen_offset_x > vp_x:
                self.screen_offset_x = vp_x

            #Restrict to top of page
            if self.screen_offset_y > vp_y:
                self.screen_offset_y = vp_y

            #Restrict to bottom of page
            if self.screen_offset_y < -(config.pixel_height - vp_height - vp_y):
                self.screen_offset_y = -(config.pixel_height - vp_height - vp_y)

            #Restrict to right of page
            if self.screen_offset_x < -(config.pixel_width - vp_width - vp_x):
                self.screen_offset_x = -(config.pixel_width - vp_width - vp_x)

            #Center canvas if smaller than the screen
            if self.pixel_width < vp_width:
                self.screen_offset_x = layers.w + layers.ovr + (vp_width - self.pixel_width) // 2
            if self.pixel_height < vp_height:
                self.screen_offset_y = menubar.h + menubar.ovb + (vp_height - self.pixel_height) // 2
        else:
            #Restrict to left of page
            if self.screen_offset_x > canvas.x:
                self.screen_offset_x = canvas.x

            #Restrict to top of page
            if self.screen_offset_y > canvas.y:
                self.screen_offset_y = canvas.y

            #Restrict to bottom of page
            if self.screen_offset_y < -(config.pixel_height - canvas.h - canvas.y):
                self.screen_offset_y = -(config.pixel_height - canvas.h - canvas.y)

            #Restrict to right of page
            if self.screen_offset_x < -(config.pixel_width - canvas.w - canvas.x):
                self.screen_offset_x = -(config.pixel_width - canvas.w - canvas.x)

            #Center canvas if smaller than the screen
            if self.pixel_width < canvas.w:
                self.screen_offset_x = canvas.x + (canvas.w - self.pixel_width) // 2
            if self.pixel_height < canvas.h:
                self.screen_offset_y = canvas.y + (canvas.h - self.pixel_height) // 2

    def get_win_pos_from_pixel(self, coords):
        cx, cy = coords
        ox,oy,screenX,screenY = config.window_canvas_rect
        #scale pixel coords to window coords
        wx = (cx * screenX // self.screen_width) + ox
        wy = (cy * screenY // self.screen_height) + oy
        return((wx, wy))

    def get_mouse_pointer_pos(self, event=None):
        mouseX, mouseY = pygame.mouse.get_pos()
        if not event is None and (event.type == MOUSEMOTION or event.type == MOUSEBUTTONUP or event.type == MOUSEBUTTONDOWN):
            mouseX, mouseY = event.pos
        ox,oy,screenX,screenY = config.window_canvas_rect

        #constrain mouse to edge of screen
        mouseX = max(ox, mouseX)
        mouseX = min(mouseX, screenX+ox-1)
        mouseY = max(oy, mouseY)
        mouseY = min(mouseY, screenY+oy-1)

        #scale window mouse coords to pixel coords
        mouseX = (mouseX-ox) * self.screen_width // screenX
        mouseY = (mouseY-oy) * self.screen_height // screenY
        return((mouseX, mouseY))

    def calc_page_pos(self, mouseX, mouseY):
        mouseX -= self.screen_offset_x
        mouseY -= self.screen_offset_y

        #make sure coords don't go off page
        mouseX = max(mouseX,0)
        mouseY = max(mouseY,0)
        mouseX = min(mouseX,self.pixel_width-1)
        mouseY = min(mouseY,self.pixel_height-1)

        return mouseX, mouseY


    def nudge_mouse_pixel(self, x, y):
        mouseX, mouseY = pygame.mouse.get_pos()
        if config.fullscreen:
            screenX, screenY = self.max_width, self.max_height
        else:
            screenX, screenY = self.window_size
        mouseX += x * screenX // self.screen_width
        mouseY += y * screenY // self.screen_height
        pygame.mouse.set_pos(mouseX, mouseY)


    def get_mouse_pixel_pos(self, event=None, ignore_grid=False, ignore_req=False):
        mouseX, mouseY = pygame.mouse.get_pos()

        if not event is None and (event.type == MOUSEMOTION or event.type == MOUSEBUTTONUP or event.type == MOUSEBUTTONDOWN):
            mouseX, mouseY = event.pos

        ox,oy,screenX,screenY = config.window_canvas_rect

        mouseX = (mouseX-ox) * self.screen_width // screenX
        mouseY = (mouseY-oy) * self.screen_height // screenY

        mouseside = 0

        if self.zoom.on and (self.pixel_req_rect == None or ignore_req):
            x0,y0,xw,yh = self.zoom.left_rect
            if (mouseX < x0+xw or self.zoom.mousedown_side == 1) and self.zoom.mousedown_side != 2:
                mouseside = 1
                mouseX += self.zoom.xoffset
                mouseY += self.zoom.yoffset
            else:
                mouseside = 2
                x0,y0,xw,yh = self.zoom.right_rect
                zx0,zy0, zoom_width,zoom_height = self.zoom.pixel_rect
                if xw == 0:
                    mouseX = 0
                else:
                    mouseX = ((mouseX - x0) * zoom_width // xw) + zx0

                if yh == 0:
                    mouseY = 0
                else:
                    mouseY = (((mouseY - y0) * zoom_height) // yh) + zy0

            #make sure coords don't go off page
            mouseX = max(mouseX,0)
            mouseY = max(mouseY,0)
            mouseX = min(mouseX,self.pixel_width-1)
            mouseY = min(mouseY,self.pixel_height-1)
        else:
            self.zoom.mousedown_side = 0
            #Don't apply page offset to reqestors
            if self.pixel_req_rect != None:
                rx,ry,rw,rh = self.pixel_req_rect
                if mouseX >= rx and mouseX < rx+rw and \
                   mouseY >= ry and mouseY < ry+rh:
                    pass
                else:
                    mouseX, mouseY = self.calc_page_pos(mouseX, mouseY)
            else:
                mouseX, mouseY = self.calc_page_pos(mouseX, mouseY)

        if not event is None and event.type == MOUSEBUTTONDOWN:
            self.zoom.mousedown_side = mouseside
        if not True in config.get_mouse_pressed():
            self.zoom.mousedown_side = 0

        #turn constrain on or off
        if pygame.key.get_mods() & KMOD_SHIFT and self.enable_constrain:
            if self.constrain_x < 0 and self.constrain_y < 0:
                if "rel" in dir(event):
                    if abs(event.rel[0]) > abs(event.rel[1]):
                        self.constrain_y = mouseY
                    else:
                        self.constrain_x = mouseX
        else:
            self.constrain_x = -1
            self.constrain_y = -1

        #apply constrain
        if self.constrain_x >= 0:
            mouseX = self.constrain_x
        elif self.constrain_y >= 0:
            mouseY = self.constrain_y

        if self.grid_on and self.pixel_req_rect == None and not ignore_grid:
            go = self.grid_offset
            gs = self.grid_size
            mouseX = (mouseX - go[0] + (gs[0]//2)) // gs[0] * gs[0] + go[0]
            mouseY = (mouseY - go[1] + (gs[1]//2)) // gs[1] * gs[1] + go[1]

        return((mouseX, mouseY))

    def has_event(self, timeout=16):
        return config.xevent.peek((KEYDOWN,
                            MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION)) and \
               pygame.time.get_ticks() - self.last_recompose_timer > timeout

    def is_busy(self):
        ticks = pygame.time.get_ticks()
        retval = False
        if ticks - self.busy_start_time > self.BUSY_LAG_TIME and \
           self.busy_last_coords == pygame.mouse.get_pos():
            self.busy_start_time = ticks - self.BUSY_LAG_TIME
            retval = True
        self.busy_last_coords = pygame.mouse.get_pos()
        return retval

    def try_recompose(self):
        if pygame.time.get_ticks() - self.last_recompose_timer > 16:
            old_cursor = config.cursor.shape
            if self.is_busy() and old_cursor == config.cursor.CROSS:
                config.cursor.shape = config.cursor.BUSY
            config.recompose()
            if old_cursor == config.cursor.CROSS:
                config.cursor.shape = config.cursor.CROSS

    def redraw_window_title(self):
        new_window_title = f"PyDPainter {config.version} - "
        if config.filename == "":
            new_window_title += "Untitled" 
        else:
            new_window_title += os.path.basename(config.filename)

        if config.modified_count >= 1:
            new_window_title += " (modified)"

        if new_window_title != config.window_title:
            config.window_title = new_window_title
            pygame.display.set_caption(config.window_title)

    def recompose(self):
        scaleX = config.fontx // 8
        scaleY = config.fonty // 12


        self.calc_tool_visibility_state()

        if self.cycling:
            for crange in config.cranges:
                crange.apply_to_pal(self.pal)
            self.set_all_palettes(self.pal)

        self.menubar.indicators["layers"] = self.layers.draw_indicator

        self.redraw_window_title()
        rect = config.layout.get_rect()
        self.screen_width = rect[2]
        self.screen_height = rect[3]
        if self.scaled_image.get_width() != self.screen_width or \
           self.scaled_image.get_height() != self.screen_height * 2:
            self.scaled_image = pygame.Surface((self.screen_width, self.screen_height*2))
            self.scanline_canvas = pygame.Surface((self.screen_width, self.screen_height*2), SRCALPHA)
            for i in range(0, self.screen_height*2, 2):
                pygame.draw.line(self.scanline_canvas, Color(0,0,0,100), (0,i), (self.screen_width,i), 1)

        # Keep the stencil pseudo-layer in sync.  The active drawing layer is
        # never rebound here: config.pixel_canvas already *is* that layer.
        config.layers.set("fg", config.stencil, priority=10,
                          visible=config.stencil.enable, kind="stencil")
        if not config.layers.has_key(config.layers.current_layer_name):
            config.select_layer("canvas")

        screen_rgb = None
        if self.zoom.on:
            screen_rgb = pygame.Surface((self.screen_width, self.screen_height),0)
            w = self.screen_width // 3
            zxc,zyc = self.zoom.center
            zoom_width = w*2 // self.zoom.factor
            zoom_height = self.screen_height // self.zoom.factor

            menu_bar_height = 0
            atbh = 0
            if self.toolbar.visible:
                zoom_width -= self.toolbar.rect[2] // self.zoom.factor
            if self.menubar.visible:
                zoom_height -= self.menubar.rect[3] // self.zoom.factor
                menu_bar_height = self.menubar.rect[3]
            if self.animtoolbar.visible and self.anim.num_frames > 1:
                atbh = self.animtoolbar.rect[3] + 3*scaleY
                zoom_height -= int(math.ceil(atbh / self.zoom.factor))

            self.zoom.xoffset = zxc - (w//2)
            self.zoom.yoffset = zyc - ((self.screen_height-menu_bar_height) // 2)

            if self.zoom.xoffset < 0:
                self.zoom.xoffset = 0
            elif self.zoom.xoffset > self.pixel_width - w + 6:
                self.zoom.xoffset = self.pixel_width - w + 6

            if self.zoom.yoffset < -menu_bar_height:
                self.zoom.yoffset = -menu_bar_height
            elif self.zoom.yoffset > self.pixel_height - self.screen_height + atbh:
                self.zoom.yoffset = self.pixel_height - self.screen_height + atbh

            zx0 = zxc-(zoom_width//2)
            zy0 = zyc-(zoom_height//2)

            if zx0+zoom_width > self.pixel_width:
                zx0 = self.pixel_width - zoom_width
            if zx0 < 0:
                zx0 = 0

            if zy0+zoom_height > self.pixel_height:
                zy0 = self.pixel_height - zoom_height
            if zy0 < 0:
                zy0 = 0

            #Fix zoom center to be back in range
            zxc = zx0+(zoom_width//2)
            zyc = zy0+(zoom_height//2)
            self.zoom.center = (zxc,zyc)

            self.zoom.pixel_rect = (zx0,zy0, zoom_width,zoom_height)

            self.zoom.left_rect = (0,menu_bar_height, w,self.screen_height)
            self.zoom.border_rect = (w-6,0,6,self.screen_height)
            self.zoom.right_rect = (w,menu_bar_height, zoom_width*self.zoom.factor,zoom_height*self.zoom.factor)
            zxsize = min(zx0+zoom_width, self.pixel_width)*self.zoom.factor
            zysize = min(zy0+zoom_height, self.pixel_height)*self.zoom.factor

            # Draw left unzoomed image
            pygame.draw.rect(screen_rgb, (128,128,128), (0,0,w,self.screen_height))
            config.layers.blit(screen_rgb, (0,0), (self.zoom.xoffset,self.zoom.yoffset, w,self.screen_height))
            self.grid.draw(screen_rgb, (0,0), (self.zoom.xoffset,self.zoom.yoffset, w,self.screen_height))

            # Draw right zoomed image
            pygame.draw.rect(screen_rgb, (128,128,128), (w,menu_bar_height,self.screen_width,self.screen_height))
            zoom_canvas = pygame.Surface((zoom_width, zoom_height),0, screen_rgb)
            config.layers.blit(zoom_canvas, (0,0), (zx0,zy0,zoom_width,zoom_height))
            self.grid.draw(zoom_canvas, (0,0), (zx0,zy0,zoom_width,zoom_height))
            zoom_canvas_scaled = pygame.transform.scale(zoom_canvas, (zoom_width*self.zoom.factor,zoom_height*self.zoom.factor))
            screen_rgb.blit(zoom_canvas_scaled, (w,menu_bar_height), (0,0,zxsize,zysize))

            # Draw divider
            pygame.draw.rect(screen_rgb, (0,0,0), (w-6,0,6,self.screen_height))
            pygame.draw.rect(screen_rgb, (128,128,128), (w-5,0,4,self.screen_height))
        else:
            self.set_screen_offset(self.screen_offset_x, self.screen_offset_y)

            screen_rgb = pygame.Surface((self.screen_width, self.screen_height),0)
            screen_rgb.fill((128,128,128)); # out of page bounds
            config.layers.blit(screen_rgb, (self.screen_offset_x, self.screen_offset_y))
            self.grid.draw(screen_rgb, (self.screen_offset_x, self.screen_offset_y))

        #blit requestor layer
        if self.pixel_req_rect != None:
            if self.cursor.shape not in [self.cursor.NORMAL, self.cursor.NORMALTO, self.cursor.DROPPER, self.cursor.BUSY]:
                self.cursor.shape = self.cursor.NORMAL
            screen_rgb.blit(self.pixel_req_canvas, self.pixel_req_rect, self.pixel_req_rect)
            self.toolbar.tip_canvas = None
            self.minitoolbar.tip_canvas = None
            self.animtoolbar.tip_canvas = None
            self.layertoolbar.tip_canvas = None

        #blit toolbar layer
        rect = config.layout.get_rect("toolbar")
        self.toolbar.draw(screen_rgb, rect=rect)

        #blit layertoolbar layer
        rect = config.layout.get_rect("layertoolbar")
        draw_layertoolbar(screen_rgb, rect=rect)

        #blit menu layer
        rect = config.layout.get_rect("menubar")
        self.menubar.draw(screen_rgb, rect=rect)

        #blit minitoolbar layer
        if self.menubar.visible:
            if config.minitoolbar.tool_id("expand").state == 1:
                mtbx = self.screen_width-self.minitoolbar.rect[2]
            else:
                mtbx = self.screen_width-(self.minitoolbar.rect[2]//len(self.minitoolbar.tools)*2)
            self.minitoolbar.draw(screen_rgb, offset=(mtbx, 0))

        #blit animtoolbar layer
        rect = config.layout.get_rect("animtoolbar")
        draw_animtoolbar(screen_rgb, rect)

        #scale image double height
        pygame.transform.scale(screen_rgb, (self.screen_width, self.screen_height*2), self.scaled_image)

        #draw mouse cursor
        self.cursor.draw(self.scaled_image)

        if self.scanlines == self.SCANLINES_ON:
            #blit scanlines onto double-high image
            self.scaled_image.blit(self.scanline_canvas, (0,0))
            #scale up screen to window resolution, blurring for retro effect
            scaledup = pygame.transform.smoothscale(self.scaled_image, self.window_size)
        elif self.scanlines == self.SCANLINES_OFF:
            scaledup = pygame.transform.smoothscale(self.scaled_image, self.window_size)
        elif self.scanlines == self.SCANLINES_NOSMOOTH:
            scaledup = pygame.transform.scale(self.scaled_image, self.window_size)

        self.screen.fill((0,0,0))
        ox = (self.screen.get_width() - scaledup.get_width()) // 2
        oy = (self.screen.get_height() - scaledup.get_height()) // 2
        config.window_canvas_rect = [ox,oy, self.window_size[0], self.window_size[1]]
        self.screen.blit(scaledup,(ox,oy))
        scaledup = None

        #blit tooltip layer
        if not self.toolbar.wait_for_tip and \
           self.toolbar.tip_canvas != None and \
           self.toolbar.visible and \
           config.help_on:
            tx = self.screen_width-self.toolbar.rect[2]+self.toolbar.tip_x
            ty = (self.fonty-1 if self.menubar.visible else 0) + self.toolbar.tip_y
            t_size = self.toolbar.tip_canvas.get_size()
            sx = ox + (tx * self.window_size[0] // self.screen_width) - t_size[0]
            sy = oy + (ty * self.window_size[1] // self.screen_height) - (t_size[1]//2)
            self.screen.blit(self.toolbar.tip_canvas, (sx,sy))

        #blit minitoolbar tooltip layer
        if not self.minitoolbar.wait_for_tip and \
           self.minitoolbar.tip_canvas != None and \
           self.menubar.visible and \
           config.help_on:
            tx = mtbx + self.minitoolbar.tip_x
            ty = self.minitoolbar.tip_y
            t_size = self.minitoolbar.tip_canvas.get_size()
            sx = ox + (tx * self.window_size[0] // self.screen_width) - t_size[0]
            sy = oy + (ty * self.window_size[1] // self.screen_height) - (t_size[1]//2)
            self.screen.blit(self.minitoolbar.tip_canvas, (sx,sy))

        #blit animtoolbar tooltip layer
        if self.animtoolbar.visible and \
           not self.animtoolbar.wait_for_tip and \
           self.animtoolbar.tip_canvas != None and \
           self.menubar.visible and \
           config.help_on:
            px = config.font.xsize // 8
            tx = self.animtoolbar.tip_x + px*11
            atby = config.screen_height - config.menubar.rect[3]
            ty = atby + self.animtoolbar.tip_y
            t_size = self.animtoolbar.tip_canvas.get_size()
            sx = ox + (tx * self.window_size[0] // self.screen_width)
            sy = oy + (ty * self.window_size[1] // self.screen_height) - (t_size[1]//2)
            self.screen.blit(self.animtoolbar.tip_canvas, (sx,sy))

        #blit layertoolbar tooltip layer
        if self.layertoolbar.visible and \
           not self.layertoolbar.wait_for_tip and \
           self.layertoolbar.tip_canvas != None and \
           self.menubar.visible and \
           config.help_on:
            px = config.font.xsize // 8
            tx = self.layertoolbar.tip_x + px*11
            atby = config.menubar.rect[3]
            ty = atby + self.layertoolbar.tip_y
            t_size = self.layertoolbar.tip_canvas.get_size()
            sx = ox + (tx * self.window_size[0] // self.screen_width)
            sy = oy + (ty * self.window_size[1] // self.screen_height) - (t_size[1]//2)
            self.screen.blit(self.layertoolbar.tip_canvas, (sx,sy))

        #blit pick RGB layer
        if not config.pick_canvas is None:
            self.screen.blit(config.pick_canvas, config.pick_canvas_offset)

        pygame.display.flip()
        self.last_recompose_timer = pygame.time.get_ticks()


    def _stack_undo_meta(self, stack):
        """Cheap structural metadata for one stack (no image copies)."""
        if stack is None:
            return []
        meta = []
        for name in stack.names():
            layer = stack.get(name)
            meta.append((name, layer.priority, layer.visible, layer.opacity,
                         layer.kind, layer.indicator, layer.transparent_index))
        return meta

    def _undo_meta(self):
        """Metadata for the live stack and every animation frame.

        Visibility and opacity are shared by all frames, so an undo entry
        has to remember them for every frame, not just the one on screen.
        """
        frames = []
        if self.anim is not None:
            frames = [self._stack_undo_meta(f.layers) for f in self.anim.frame]
        return {"live": self._stack_undo_meta(self.layers), "frames": frames}

    def _apply_stack_undo_meta(self, stack, meta):
        if stack is None or not meta:
            return
        for (name, priority, visible, opacity, kind, indicator,
             transparent_index) in meta:
            if not stack.has_key(name):
                continue
            layer = stack.get(name)
            layer.priority = priority
            layer.visible = visible
            layer.opacity = opacity
            layer.kind = kind
            layer.indicator = indicator
            layer.transparent_index = transparent_index

    def _apply_undo_meta(self, meta):
        if not meta:
            return
        if isinstance(meta, dict):
            self._apply_stack_undo_meta(self.layers, meta.get("live"))
            if self.anim is not None:
                frames = meta.get("frames") or []
                for i, frame in enumerate(self.anim.frame):
                    if i < len(frames):
                        self._apply_stack_undo_meta(frame.layers, frames[i])
        else:
            # Older list-shaped metadata only covers the live stack.
            self._apply_stack_undo_meta(self.layers, meta)

    def _snapshot_stacks(self):
        """Deep-copy every stack a structural operation can touch.

        Layer operations apply to all animation frames, so an undo has to
        restore all of them; otherwise frames would end up with different
        layer structures.
        """
        snapshot = {"live": self.layers.copy(), "frames": []}
        if self.anim is not None and self.anim.num_frames > 1:
            for frame in self.anim.frame:
                if frame.layers is None:
                    snapshot["frames"].append(None)
                else:
                    snapshot["frames"].append(frame.layers.copy())
        return snapshot

    def stash_structural(self):
        """Remember the current stack before a structural layer change.

        Called by layer operations so that a later undo can restore the
        layers that were added, deleted or reordered.
        """
        if not hasattr(self, "undo_stack"):
            return
        idx = self.undo_index
        while len(self.undo_stack) <= idx:
            self.undo_stack.append(None)
            self.undo_meta.append([])
            self.undo_layer.append(None)
        if 0 <= idx:
            self.undo_stack[idx] = self._snapshot_stacks()
            self.undo_meta[idx] = self._undo_meta()
            self.undo_layer[idx] = self.layers.current_layer_name

    def save_undo(self, structural=False):
        if self.suppress_undo:
            self.suppress_undo = False
            return

        self.modified_count += 1

        #Backup for undo
        self.undo_index = self.undo_index + 1
        if self.undo_index > self.UNDO_INDEX_MAX:
            self.undo_index = self.UNDO_INDEX_MAX
            for lst in (self.undo_image, self.undo_layer,
                        self.undo_stack, self.undo_meta):
                lst.pop(0)

        for lst in (self.undo_image, self.undo_layer,
                    self.undo_stack, self.undo_meta):
            while self.undo_index > len(lst)-1:
                lst.append("" if lst is self.undo_image else None)
            while len(lst)-1 > self.undo_index:
                lst.pop()

        config.stencil.draw(self.pixel_canvas)
        self.undo_image[self.undo_index] = pygame.Surface(self.pixel_canvas.get_size(),0, self.pixel_canvas)
        self.undo_image[self.undo_index].set_palette(self.pal)
        self.undo_image[self.undo_index].blit(self.pixel_canvas, (0,0))
        self.undo_layer[self.undo_index] = self.layers.current_layer_name
        self.undo_meta[self.undo_index] = self._undo_meta()
        self.undo_stack[self.undo_index] = self._snapshot_stacks() if structural else None

    def clear_undo(self):
        self.suppress_undo = False
        self.undo_image = []
        self.undo_layer = []
        self.undo_stack = []
        self.undo_meta = []
        self.undo_index = -1
        self.save_undo()
        self.suppress_undo = True

    def _restore_undo_image(self):
        idx = self.undo_index
        if idx < 0 or idx >= len(self.undo_image):
            return
        snapshot = self.undo_stack[idx]
        if snapshot is not None:
            # Structural change: restore the whole layer stack (and every
            # animation frame's stack).
            if isinstance(snapshot, dict):
                live = snapshot.get("live")
                if live is not None:
                    self.layers = live.copy()
                frames = snapshot.get("frames") or []
                if self.anim is not None:
                    if frames:
                        for i, frame in enumerate(self.anim.frame):
                            if i >= len(frames) or frames[i] is None:
                                continue
                            restored = frames[i].copy()
                            if i == self.anim.curr_frame - 1:
                                self.layers = restored
                            frame.layers = restored
                            if restored.has_key("canvas"):
                                frame.image = restored.get("canvas").image
                    elif 0 <= self.anim.curr_frame - 1 < len(self.anim.frame):
                        frame = self.anim.frame[self.anim.curr_frame - 1]
                        frame.layers = self.layers
                        if self.layers.has_key("canvas"):
                            frame.image = self.layers.get("canvas").image
            else:
                self.layers = snapshot.copy()
            self.proj[self.proj_index].layers = self.layers
            name = self.undo_layer[idx]
            if not self.select_layer(name):
                self.select_layer("canvas")
        else:
            if idx < len(self.undo_meta):
                self._apply_undo_meta(self.undo_meta[idx])
            name = self.undo_layer[idx] if idx < len(self.undo_layer) else None
            if name is not None and self.layers.has_key(name):
                self.select_layer(name)
        img = self.undo_image[idx]
        if isinstance(img, pygame.Surface) and \
           img.get_size() == self.pixel_canvas.get_size():
            self.pixel_canvas.blit(img, (0,0))

    def redo(self):
        config.undo_index = config.undo_index + 1
        if config.undo_index > len(config.undo_image) - 1:
            config.undo_index = len(config.undo_image) - 1
        config._restore_undo_image()
        if config.stencil.enable:
            # Recalculate stencil
            config.stencil.enable = True
        config.doKeyAction()

    def undo(self):
        config.undo_index = config.undo_index - 1
        if config.undo_index < 0:
            config.undo_index = 0
        config._restore_undo_image()
        if config.stencil.enable:
            # Recalculate stencil
            config.stencil.enable = True
        config.doKeyAction()

    def airbrush_coords(self, xc, yc, size=-1):
        if size < 0:
            size = self.airbrush_size
        angle = random.random() * 2.0 * 3.14159
        dist = random.random() * float(size)
        x = int(dist*config.aspectX * math.cos(angle))
        y = int(dist*config.aspectY * math.sin(angle))
        return ((xc+x, yc+y))

    def clear_pixel_draw_canvas(self):
        idx = self.undo_index
        if 0 <= idx < len(self.undo_image):
            # Only restore a snapshot that belongs to the layer being drawn
            # on; otherwise an undo entry from another layer would be copied
            # into this one.
            name = self.undo_layer[idx] if idx < len(self.undo_layer) else None
            if name is None or name == self.layers.current_layer_name:
                img = self.undo_image[idx]
                if isinstance(img, pygame.Surface) and \
                   img.get_size() == self.pixel_canvas.get_size():
                    self.pixel_canvas.blit(img, (0,0))
        self.drawing_interrupted = False

    def stop_cycling(self):
        if self.cycling:
            self.cycling = False
            self.pal = list(self.backuppal)
            self.set_all_palettes(self.pal)
            config.brush.size = config.brush.size #invalidate bruch cache
            for rangenum, crange in enumerate(self.cranges):
                pygame.time.set_timer(self.CYCLEEVENTS[rangenum], TIMEROFF)

    def start_cycling(self):
        if config.anim.num_frames > 1 and config.anim.global_palette == False:
            return
        if not self.cycling:
            self.backuppal = list(self.pal)
            self.cycling = True
        for rangenum, crange in enumerate(self.cranges):
            if crange.low < crange.high and crange.rate > 0:
                pygame.time.set_timer(self.CYCLEEVENTS[rangenum], TIMEROFF)
                pygame.time.set_timer(self.CYCLEEVENTS[rangenum], crange.rate_to_milli())

    def _resize_surface(self, image, width, height, resize):
        new_image = pygame.Surface((width, height), 0, 8)
        new_image.set_palette(self.pal)
        if resize:
            src = image
            if src.get_bytesize() != 1:
                # transform.scale() requires matching formats.  Reference
                # backgrounds can be RGB, so convert them to the palette first.
                src = pygame.Surface(src.get_size(), 0, 8)
                src.set_palette(self.pal)
                src.blit(image, (0, 0))
            pygame.transform.scale(src, (width, height), new_image)
        else:
            new_image.blit(image, (0, 0))
        return new_image

    def _resize_stack_layers(self, st, width, height, resize):
        for name, layer in list(st.layers.items()):
            if not isinstance(layer.image, pygame.Surface):
                continue
            if layer.image.get_size() == (width, height):
                continue
            layer.image = self._resize_surface(layer.image, width, height, resize)

    def size_canvas(self, width, height, resize):
        # Resize every layer of every frame in this project.
        for st in self.layer_stacks():
            self._resize_stack_layers(st, width, height, resize)
        for frame in self.anim.frame:
            if frame.layers is not None and frame.layers.has_key("canvas"):
                frame.image = frame.layers.get("canvas").image

        # Resize the spare project's layers too.
        for i, proj in enumerate(self.proj):
            if i == self.proj_index:
                continue
            stacks = []
            if proj.layers is not None:
                stacks.append(proj.layers)
            if proj.anim is not None:
                for frame in proj.anim.frame:
                    if frame.layers is not None:
                        stacks.append(frame.layers)
            seen = set()
            for st in stacks:
                if id(st) in seen:
                    continue
                seen.add(id(st))
                self._resize_stack_layers(st, width, height, resize)
            if proj.anim is not None:
                for frame in proj.anim.frame:
                    if frame.layers is not None and frame.layers.has_key("canvas"):
                        frame.image = frame.layers.get("canvas").image
            if proj.layers is not None and proj.layers.has_key("canvas"):
                proj.pixel_canvas = proj.layers.get("canvas").image

        self.pixel_width = width
        self.pixel_height = height
        self.symm_center = (width // 2, height // 2)

        name = self.layers.current_layer_name
        if not self.select_layer(name):
            self.select_layer("canvas")
        self.proj[self.proj_index].pixel_canvas = self.pixel_canvas
        self.proj[self.proj_index].layers = self.layers

        self.stencil.clear()
        self.stencil.free()

        config.clear_undo()
        config.save_undo()

    def xpos_display(self, x):
        if config.coords_1based:
            x = x + 1
        return x

    def ypos_display(self, y):
        if not config.coords_flip:
            y = config.pixel_height - y - 1
        if config.coords_1based:
            y = y + 1
        return y

    def xpos_undisplay(self, x):
        if config.coords_1based:
            x = x - 1
        return x

    def ypos_undisplay(self, y):
        if config.coords_1based:
            y = y - 1
        if not config.coords_flip:
            y = config.pixel_height - y - 1
        return y

    def xypos_display(self, coords):
        x,y = coords
        x = config.xpos_display(x)
        y = config.ypos_display(y)
        return (x,y)

    def xypos_string(self, coords):
        x,y = config.xypos_display(coords)
        if config.coords_flip:
            str = "%4d\x94%4d\x96" % ((x, y))
        else:
            str = "%4d\x94%4d\x95" % ((x, y))
        return str

    def draw_rgb_dropper(self, cxy, color):
        cx,cy = cxy
        bg = (200,200,200)
        fg = (0,0,0)
        if isinstance(color, tuple):
            rgb = list(color)
            color_str = "N/A"
        else:
            rgb = config.truepal[color]
            color_str = "%d" % (color)

        #load font and get text size
        win_ox,win_oy,win_w,win_h = config.window_canvas_rect
        calc_font_size = win_h//50
        if config.pick_canvas_font_size != calc_font_size:
            config.pick_canvas_font_size = calc_font_size
            config.pick_canvas_font = pygame.font.Font(os.path.join('data', 'FreeSansBold.ttf'), config.pick_canvas_font_size)

        #size box
        title_font = config.pick_canvas_font
        wrect = title_font.size("W")
        lineheight = title_font.get_linesize()
        w = wrect[0]*16
        h = wrect[1]*4
        rect = [0,0, w,h]

        #create surface
        config.pick_canvas = pygame.Surface((w,h),SRCALPHA)
        config.pick_canvas.fill(bg)

        #calc offset
        pick_ox, pick_oy = self.get_win_pos_from_pixel(cxy)
        cursor_yo = int(config.cursor.center[config.cursor.shape][1] * config.cursor.scaleY * config.scale // 2)
        if pick_ox + w >= win_ox + win_w:
            pick_ox = win_ox + win_w - w
        if pick_oy < win_oy + h + wrect[1] + cursor_yo:
            pick_oy = pick_oy + h - cursor_yo
        else:
            pick_oy = pick_oy - h - wrect[1] - cursor_yo
        config.pick_canvas_offset = [pick_ox, pick_oy]

        #render rectangles
        pygame.draw.rect(config.pick_canvas, fg, [0,0,w,h], wrect[0]//6)
        pygame.draw.rect(config.pick_canvas, rgb, [wrect[0]//2, wrect[0]//2, wrect[1]*3, h-wrect[0]])
        pygame.draw.rect(config.pick_canvas, fg, [wrect[0]//2, wrect[0]//2, wrect[1]*3, h-wrect[0]], wrect[0]//6)

        #render text
        tx = wrect[0] + wrect[1] * 3
        ty = wrect[1] // 2
        timg = title_font.render("Color Index: %s" % (color_str), True, fg, bg)
        config.pick_canvas.blit(timg, (tx,ty))
        ty += wrect[1] + wrect[1] // 8
        timg = title_font.render("RGB: %d, %d, %d" % (rgb[0],rgb[1],rgb[2]), True, fg, bg)
        config.pick_canvas.blit(timg, (tx,ty))
        ty += wrect[1] + wrect[1] // 8
        timg = title_font.render("Hex: %02X%02X%02X" % (rgb[0], rgb[1], rgb[2]), True, fg, bg)

        config.pick_canvas.blit(timg, (tx,ty))

    def run(self):
        """
        This method is the main application loop.
        """

        config = self
        startX = 0
        startY = 0
        stopX = 0
        stopY = 0
        text_string = ""
        buttons = list(config.get_mouse_pressed())
        zoom_drag = None
        pan_drag = None
        curr_action = None

        last_wait_for_mouseup_gui = False

        self.recompose()

        #main loop
        while config.running:
            e = config.xevent.wait()

            if self.tool_selected != "text":
                config.user_hotkeys.process_remap(e)

            if e.type == pygame.MOUSEMOTION and config.xevent.peek((MOUSEMOTION)):
                #get rid of extra mouse movements
                continue

            if e.type == pygame.VIDEORESIZE and config.xevent.peek((VIDEORESIZE)):
                #get rid of extra resize events
                continue

            if e.type in self.ALLCUSTOMEVENTS:
                if  config.xevent.peek(self.ALLCUSTOMEVENTS):
                    #get rid of extraneous color cycle and other user events
                    continue

            if e.type == pygame.QUIT:
                config.running = False

            if e.type == VIDEORESIZE:
                if not config.fullscreen:
                    config.scale = config.closest_scale((e.w, e.h))
                    config.resize_display(False)
                    self.recompose()
                continue

            #Load in droppped file
            if e.type == DROPFILE:
                filename = e.file
                if filename != (()) and filename != "":
                    global progress_req
                    progress_req = open_progress_req(config.pixel_req_canvas, "Loading...")
                    try:
                        config.pixel_canvas = load_pic(filename, config, status_func=drop_load_progress, cmd_load=True)
                        config.bgcolor = 0
                        config.color = 1
                        close_progress_req(progress_req)
                        config.truepal = list(config.pal)
                        config.pal = config.unique_palette(config.pal)
                        config.layers_loaded = True
                        config.initialize_surfaces()
                        config.filepath = os.path.dirname(filename)
                        config.filename = filename
                        config.modified_count = 0
                        if config.anim.num_frames > 1:
                            config.anim.show_curr_frame()
                    except Exception as ex:
                        close_progress_req(progress_req)
                        io_error_req("Load Error", "Unable to open image:\n%s\n%s", filename, str(ex))


            #Intercept keys for toolbar
            if e.type in [KEYDOWN,KEYUP] and not config.anim.playing:
                if curr_action != None:
                    key_handled = False
                    if e.type == KEYDOWN:
                        key_handled = curr_action.keydown(e.key, e.mod, e.unicode)
                    elif e.type == KEYUP:
                        key_handled = curr_action.keyup(e.key, e.mod)
                    if key_handled:
                        self.recompose()
                        continue

            #Keep track of button states
            if e.type == MOUSEMOTION:
                buttons = list(config.get_mouse_pressed(e))
            elif e.type == MOUSEBUTTONDOWN:
                if e.button <= len(buttons):
                    buttons[e.button-1] = True
            elif e.type == MOUSEBUTTONUP:
                if e.button <= len(buttons):
                    buttons[e.button-1] = False

            #Show system mouse pointer if outside of screen
            if e.type == MOUSEMOTION:
                ox,oy,screenX,screenY = config.window_canvas_rect
                x,y = e.pos
                if config.fullscreen:
                    pygame.mouse.set_visible(False)
                elif x < ox or x > ox+screenX or y < oy or y > oy+screenY:
                    pygame.mouse.set_visible(True)
                else:
                    pygame.mouse.set_visible(False)

            if not config.anim.playing:
                #Get toolbar events if any and set current action to tool selected
                te_list = self.toolbar.process_event(self.screen, e, self.get_mouse_pointer_pos)
                if len(te_list) > 0:
                    self.cycle_handled = True
                curr_action = None
                if config.zoom.box_on:
                    curr_action = config.toolbar.tool_id("magnify").action
                elif config.toolbar.tool_id(config.tool_selected) != None and \
                   config.toolbar.tool_id(config.tool_selected).action != None:
                    curr_action = config.toolbar.tool_id(config.tool_selected).action

            #Get minitoolbar events if any
            if self.menubar.visible:
                mte_list = self.minitoolbar.process_event(self.screen, e, self.get_mouse_pointer_pos)
            else:
                mte_list = []

            if not config.anim.playing:
                #Get menubar events if any
                if len(mte_list) > 0:
                    me_list = []
                else:
                    me_list = self.menubar.process_event(self.screen, e, self.get_mouse_pointer_pos)

            #Get animtoolbar events if any
            if self.animtoolbar.visible:
                mta_list = self.animtoolbar.process_event(self.screen, e, self.get_mouse_pointer_pos)
                config.anim.process_animtoolbar_events(mta_list, e)
            else:
                mta_list = []

            #Get layertoolbar events if any
            if self.layertoolbar.visible:
                mtl_list = self.layertoolbar.process_event(self.screen, e, self.get_mouse_pointer_pos)
                config.layers.process_layertoolbar_events(mtl_list, e)
            else:
                mtl_list = []

            wait_for_mouseup_gui = True in config.toolbar.wait_for_mouseup or True in config.minitoolbar.wait_for_mouseup or True in config.menubar.wait_for_mouseup or True in config.animtoolbar.wait_for_mouseup or True in config.layertoolbar.wait_for_mouseup

            if wait_for_mouseup_gui:
                self.cycle_handled = True

            #Decide if in draw area
            if not True in config.wait_for_mouseup and \
               (self.toolbar.is_inside(self.get_mouse_pointer_pos(e)) or \
               self.menubar.is_inside(self.get_mouse_pointer_pos(e)) or \
               self.animtoolbar.is_inside(self.get_mouse_pointer_pos(e)) or \
               self.layertoolbar.is_inside(self.get_mouse_pointer_pos(e)) or \
               wait_for_mouseup_gui):
                self.cursor.shape = self.cursor.NORMAL
                hide_draw_tool = True
                config.menubar.title_right = ""
            elif self.tool_selected == "fill":
                self.cursor.shape = self.cursor.FILL
                hide_draw_tool = False
            else:
                self.cursor.shape = self.cursor.CROSS
                hide_draw_tool = False

            if not config.anim.playing:
                #Do move action for toolbar events
                if curr_action != None and not hide_draw_tool:
                    for te in te_list:
                        #print(te)
                        if te.gadget.tool_type == ToolGadget.TT_TOGGLE or \
                           te.gadget.tool_type == ToolGadget.TT_GROUP:
                            if e.type == KEYDOWN:
                                if self.get_mouse_pressed() == (0,0,0):
                                    curr_action.move(self.get_mouse_pixel_pos(e))
                                else:
                                    curr_action.drag(self.get_mouse_pixel_pos(e), self.get_mouse_pressed())
                            else:
                                curr_action.move(self.get_mouse_pixel_pos(e))
                elif curr_action != None and hide_draw_tool:
                    curr_action.hide()

            #process middle mouse button for pan
            if not config.zoom.on and e.type == MOUSEBUTTONDOWN and e.button == 2:
                pan_drag = self.get_mouse_pixel_pos(e)
            if e.type == MOUSEBUTTONUP and e.button == 2:
                pan_drag = None
            if not config.zoom.on and buttons[1] and pan_drag != None:
                x,y = self.get_mouse_pixel_pos(e)
                cx,cy = (config.screen_offset_x, config.screen_offset_y)
                dx,dy = pan_drag
                (config.screen_offset_x, config.screen_offset_y) = (cx-dx+x, cy-dy+y)

            #process mouse wheel for zoom and pan
            if config.zoom.on and e.type == MOUSEBUTTONDOWN and e.button in [2, 4,5] and not self.animtoolbar.is_inside(self.get_mouse_pointer_pos(e)) and not self.layertoolbar.is_inside(self.get_mouse_pointer_pos(e)) and not self.toolbar.is_inside(self.get_mouse_pointer_pos(e)):
                if e.button == 2: #middle drag
                    zoom_drag = self.get_mouse_pixel_pos(e)
                elif e.button == 4: #scroll up
                    if config.zoom.factor < config.zoom.factor_max:
                        config.zoom.factor += 1
                elif e.button == 5: #scroll down
                    if config.zoom.factor > config.zoom.factor_min:
                        config.zoom.factor -= 1
            if e.type == MOUSEBUTTONUP and e.button == 2:
                zoom_drag = None
            if config.zoom.on and buttons[1] and zoom_drag != None:
                x,y = self.get_mouse_pixel_pos(e)
                cx,cy = config.zoom.center
                dx,dy = zoom_drag
                config.zoom.center = (cx+dx-x,cy+dy-y)

            #process mouse wheel in toolbar for brush size
            if e.type == MOUSEBUTTONDOWN and e.button in [4,5] and self.toolbar.is_inside(self.get_mouse_pointer_pos(e)):
                scaleY = config.fonty // 12
                x,y = self.get_mouse_pixel_pos(e)
                if y < self.toolbar.offset[1] + (22 * scaleY):
                    if e.button == 4: #scroll up
                        config.brush.size += 1
                    elif e.button == 5: #scroll down
                        config.brush.size -= 1
                    setBIBrush()

            #process global keys
            if e.type == KEYDOWN:
                self.cycle_handled = True
                gotkey = False
                if e.mod & KMOD_CTRL and (e.unicode == "+" or e.unicode == "="):
                    gotkey = True
                    config.dropper = False
                    config.toolbar.click(config.minitoolbar.tool_id("scale"), MOUSEBUTTONDOWN)
                elif e.mod & KMOD_CTRL and e.unicode == "-":
                    gotkey = True
                    config.dropper = False
                    config.toolbar.click(config.minitoolbar.tool_id("scale"), MOUSEBUTTONDOWN, subtool=True)
                elif e.mod & KMOD_CTRL and e.key == K_RETURN:
                    config.dropper = False
                    config.perspective.do_mode()
                    gotkey = True
                elif e.key == K_KP_ENTER:
                    config.perspective.do_mode()
                    gotkey = True
                elif e.unicode == ".":
                    gotkey = True
                elif e.unicode == "+" or e.unicode == "=":
                    gotkey = True
                    if self.tool_selected == "airbrush":
                        self.airbrush_size += 1
                        if self.airbrush_size > 50:
                            self.airbrush_size = 50
                    else:
                        self.brush.size += 1
                        setBIBrush()
                elif e.unicode == "-":
                    gotkey = True
                    if self.tool_selected == "airbrush": #Airbrush
                        self.airbrush_size -= 1
                        if self.airbrush_size < 5:
                            self.airbrush_size = 5
                    else:
                        self.brush.size -= 1
                        setBIBrush()
                elif e.key == K_0 and not e.mod & KMOD_CTRL:
                    gotkey = True
                    rot = self.brush.rotate
                    if e.mod & KMOD_SHIFT:
                        rot = 0
                    else:
                        rot += 1
                    self.brush.rotate = rot
                elif e.key == K_9 and not e.mod & KMOD_CTRL:
                    gotkey = True
                    rot = self.brush.rotate
                    if e.mod & KMOD_SHIFT:
                        rot = 0
                    else:
                        rot -= 1
                    self.brush.rotate = rot
                elif e.unicode == "]":
                    gotkey = True
                    self.color = (self.color + 1) % config.NUM_COLORS
                elif e.unicode == "}":
                    gotkey = True
                    self.bgcolor = (self.bgcolor + 1) % config.NUM_COLORS
                elif e.unicode == "[":
                    gotkey = True
                    self.color = (self.color - 1) % config.NUM_COLORS
                elif e.unicode == "{":
                    gotkey = True
                    self.bgcolor = (self.bgcolor - 1) % config.NUM_COLORS
                elif e.unicode == ",":
                    gotkey = True
                    config.toolbar.tool_id('swatch').pick_color()
                elif e.unicode == "\\":
                    gotkey = True
                    if config.minitoolbar.tool_id("expand").state == 1:
                        config.minitoolbar.tool_id("expand").state = 0
                    else:
                        config.minitoolbar.tool_id("expand").state = 1
                elif e.mod & KMOD_META:
                    ticks = pygame.time.get_ticks()
                    if ticks - config.last_mouse_nudge_time < 100:
                        config.nudge_accel += 2
                        if config.nudge_accel > config.NUDGE_ACCEL_MAX:
                            config.nudge_accel = config.NUDGE_ACCEL_MAX
                    else:
                        config.nudge_accel = 1
                    if e.key == K_RIGHT:
                        self.nudge_mouse_pixel(config.nudge_accel, 0)
                    elif e.key == K_LEFT:
                        self.nudge_mouse_pixel(-config.nudge_accel, 0)
                    elif e.key == K_DOWN:
                        self.nudge_mouse_pixel(0, config.nudge_accel)
                    elif e.key == K_UP:
                        self.nudge_mouse_pixel(0, -config.nudge_accel)
                    config.last_mouse_nudge_time = pygame.time.get_ticks()
                elif e.key == K_RIGHT and not config.zoom.on:
                    gotkey = True
                    config.screen_offset_x -= 5
                elif e.key == K_LEFT and not config.zoom.on:
                    gotkey = True
                    config.screen_offset_x += 5
                elif e.key == K_DOWN and not config.zoom.on:
                    gotkey = True
                    config.screen_offset_y -= 5
                elif e.key == K_UP and not config.zoom.on:
                    gotkey = True
                    config.screen_offset_y += 5
                elif e.unicode == "n" and not config.zoom.on:
                    gotkey = True
                    mouseX, mouseY = self.get_mouse_pixel_pos(e, ignore_grid=True)
                    config.screen_offset_x = (config.screen_width // 2) - mouseX
                    config.screen_offset_y = (config.screen_height // 2) - mouseY
                elif e.key >= K_F1 and e.key <= K_F8 and e.mod & KMOD_SHIFT:
                    gotkey = True
                    if e.key == K_F1:
                        config.fillmode.value = FillMode.PATTERN
                    elif e.key == K_F2:
                        config.fillmode.value = FillMode.SOLID
                    elif e.key == K_F3:
                        config.fillmode.value = FillMode.CIRCULAR
                    elif e.key == K_F4:
                        config.fillmode.value = FillMode.VERT_FIT
                    elif e.key == K_F5:
                        config.fillmode.value = FillMode.LINEAR
                    elif e.key == K_F6:
                        config.fillmode.value = FillMode.HORIZ_FIT
                    elif e.key == K_F7:
                        config.fillmode.value = FillMode.BOTH_FIT
                    elif e.key == K_F8:
                        config.fillmode.value = FillMode.SMOOTH
                    config.menubar.indicators["fillmode"] = draw_fill_indicator
                    draw_fill_indicator(None)
                elif e.key == K_F10:
                    self.tool_visibility_state += 1
                elif e.key == K_F11:
                    config.fullscreen = not config.fullscreen
                    config.minitoolbar.tool_id("fullscreen").state = 1 if config.fullscreen else 0
                    config.resize_display(force=True, grab=(e.mod & KMOD_SHIFT == 0))
                elif e.key == K_DELETE:
                    config.cursor.visible = not config.cursor.visible
                elif e.mod & KMOD_CTRL and e.mod & KMOD_SHIFT and e.key == K_z:
                    config.dropper = False
                    config.redo()
                elif e.mod & KMOD_CTRL and e.key == K_z:
                    config.dropper = False
                    config.undo()
                elif e.mod & KMOD_CTRL and e.key == K_y:
                    config.dropper = False
                    config.redo()
                elif config.xevent.intl_backtick_press(e) == 1:
                    gotkey = True
                    config.stencil.enable = not config.stencil.enable
                    config.doKeyAction()
                elif config.xevent.intl_backtick_press(e) == 2:
                    gotkey = True
                    config.menubar.menu_id("effect").menu_id("stencil").menu_id("make").action.selected("")
                    config.doKeyAction()
                elif e.key == K_F12:
                    if e.mod & KMOD_SHIFT:
                        print("\n***********Debug************")
                        print(f"{config.layers=}")
                        print("")
                        print(f"{config.layout=}")
                        config.debug = not config.debug
                    else:
                        config.toolbar.click(config.minitoolbar.tool_id("scanlines"), MOUSEBUTTONDOWN)

                if config.zoom.on:
                    gotkey |= config.zoom.process_event(self.screen, e)

                if gotkey:
                    self.set_screen_offset(self.screen_offset_x, self.screen_offset_y)
                    self.doKeyAction(curr_action)

            #process CTRL dropper
            mouseXY = config.get_mouse_pointer_pos(e)
            in_toolbars = config.inside_toolbars(config.all_toolbars, mouseXY)
            if e.type == KEYDOWN:
                if e.key in [K_LCTRL, K_RCTRL] and not True in buttons \
                   and not in_toolbars \
                   and (config.tool_selected in ["dot","draw"] \
                        or (config.ctrl_pick_override and config.tool_selected in [
                            "line","curve","fill","airbrush","rect","circle", "ellipse","poly"])):
                    config.dropper = True
                    config.clear_pixel_draw_canvas()
            if config.dropper and not config.xevent.is_key_down([K_LCTRL, K_RCTRL]) and not True in buttons:
                config.dropper = False
                config.pick_canvas = None
                if e.type != MOUSEBUTTONUP:
                    self.doKeyAction(curr_action)
            if config.dropper:
                if in_toolbars or config.menubar.menus_on:
                    config.pick_canvas = None
                else:
                    cx,cy = self.get_mouse_pixel_pos(e)
                    color = config.layers.get_at_index((cx,cy))
                    if buttons[0]:
                        config.color = color
                    elif buttons[2]:
                        config.bgcolor = color
                    config.cursor.shape = config.cursor.PICK
                    config.draw_rgb_dropper(mouseXY, color)
            else:
                config.pick_canvas = None

            #process keyboard mouse clicks
            if e.type == KEYDOWN:
                if e.mod & KMOD_META and e.mod & KMOD_ALT:
                    if e.key in [K_LALT, K_RALT, K_LMETA, K_RMETA] and config.meta_alt == 0:
                        config.get_mouse_pressed(e)
                        if config.meta_alt != 0:
                            curr_action.mousedown(self.get_mouse_pixel_pos(e), config.meta_alt)
            if e.type == KEYUP:
                if e.key in [K_LALT, K_RALT, K_LMETA, K_RMETA] and config.meta_alt != 0:
                    curr_action.mouseup(self.get_mouse_pixel_pos(e), config.meta_alt)
                    config.get_mouse_pressed(e)

            #Process events for animation
            config.anim.handle_events(e)

            if not config.anim.playing:
                #No toolbar event so process event as action on selected tool
                if curr_action != None and len(te_list) == 0 and \
                   len(mte_list) == 0 and len(me_list) == 0 and \
                   len(mta_list) == 0 and len(mtl_list) == 0 and \
                   not config.dropper and \
                   not wait_for_mouseup_gui and not hide_draw_tool:
                    if config.coords_on:
                        cx,cy = self.get_mouse_pixel_pos(e)
                        if config.p1 != None and True in self.get_mouse_pressed():
                            config.menubar.title_right = "%4d\x94%4d\x96" % (abs(cx-config.p1[0])+1, abs(cy-config.p1[1])+1)
                        else:
                            config.menubar.title_right = config.xypos_string((cx, cy))
                            config.p1 = None
                    else:
                        config.menubar.title_right = ""
                    if e.type == MOUSEMOTION:
                        mbuttons = self.get_mouse_pressed(e)
                        if mbuttons == (0,0,0):
                            curr_action.move(self.get_mouse_pixel_pos(e))
                        else:
                            curr_action.drag(self.get_mouse_pixel_pos(e), mbuttons)
                    elif e.type == MOUSEBUTTONDOWN and buttons[0] != buttons[2]:
                        zoom_region = config.zoom.region(e.pos)
                        config.wait_for_mouseup[zoom_region] = True
                        curr_action.mousedown(self.get_mouse_pixel_pos(e), e.button)
                    elif e.type == MOUSEBUTTONUP and buttons[0] == buttons[2]:
                        if last_wait_for_mouseup_gui:
                            curr_action.move(self.get_mouse_pixel_pos(e))
                        else:
                            curr_action.mouseup(self.get_mouse_pixel_pos(e), e.button)
                            config.wait_for_mouseup = [False] * len(config.wait_for_mouseup)
                    elif e.type == self.TOOLEVENT:
                        if buttons[0] or buttons[2]:
                            curr_action.drag(self.get_mouse_pixel_pos(e), buttons)
                        else:
                            curr_action.move(self.get_mouse_pixel_pos(e))

            last_wait_for_mouseup_gui = wait_for_mouseup_gui

            if buttons[0] and not e.type in self.ALLCUSTOMEVENTS and not self.cycle_handled:
                cycle()
            self.cycle_handled = False

            self.recompose()
            
            if not config.running and config.modified_count >= 1:
                answer = question_req(config.pixel_req_canvas,
                         "Unsaved Changes",
                         "Are you sure you want\nto quit PyDPainter?",
                         ["Yes","No"],
                         [K_RETURN, K_ESCAPE])
                if answer == 1:
                    config.running = True
