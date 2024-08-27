#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

from libs.menubar import *
from libs.menureq import *
from libs.gadget import *
from libs.picio import *
from libs.stencil import *

config = None

pic_filetype_list = np.array([
["IFF", "Amiga IFF image"],
["ILBM","Amiga IFF image"],
["LBM", "PC IFF PBM image"],
["GIF", "GIF image"],
["BMP", "Windows BMP image"],
["JPG", "JPEG image (lossy)"],
["JPEG","JPEG image (lossy)"],
["PNG", "PNG image"],
["TGA", "Targa image"],
])

class MenuAction(Action):
    def toolHide(self):
        if config.toolbar.tool_id(config.tool_selected) != None and \
           config.toolbar.tool_id(config.tool_selected).action != None:
            config.toolbar.tool_id(config.tool_selected).action.hide()

class MenuActionMulti(MenuAction):
    def get_name(self):
        return ""

    def is_ask_multi(self):
        return True

    def selected(self, attrs):
        if config.anim.num_frames > 1:
            if self.is_ask_multi():
                frame_range = config.anim.ask_apply_multi(self.get_name())
            else:
                frame_range = range(config.anim.num_frames)
            curr_frame_bak = config.anim.curr_frame
            for frame_no in frame_range:
                config.anim.save_curr_frame()
                config.anim.curr_frame = frame_no
                config.anim.show_curr_frame(doAction=False)
                self.selectedMulti(attrs)
                config.save_undo()
            config.anim.save_curr_frame()
            config.anim.curr_frame = curr_frame_bak
            config.anim.show_curr_frame(doAction=False)
        else:
            self.selectedMulti(attrs)
        config.save_undo()
        config.doKeyAction()

class DoDummy(MenuAction):
    def selected(self, attrs):
        pass

class DoNew(MenuAction):
    def selected(self, attrs):
        config.stencil.enable = False
        if screen_format_req(config.pixel_req_canvas,new_clicked=True):
            config.modified_count = 0
            config.filename = ""
            config.anim.__init__()

def io_error_req(title, message, filename, linelen=33):
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
def load_progress(percent):
    global prev_time

    curr_time = pygame.time.get_ticks()
    if curr_time - prev_time > 33:
        prev_time = curr_time
        update_progress_req(progress_req, config.pixel_req_canvas, percent)

class DoOpen(MenuAction):
    def selected(self, attrs):
        global progress_req
        config.stop_cycling()
        config.stencil.enable = False
        filename = file_req(config.pixel_req_canvas, "Open Picture", "Open", config.filepath, config.filename)
        if filename != (()) and filename != "":
            progress_req = open_progress_req(config.pixel_req_canvas, "Loading...")
            try:
                config.pixel_canvas = load_pic(filename, config, status_func=load_progress)
                config.bgcolor = 0
                config.color = 1
                close_progress_req(progress_req)
                config.truepal = list(config.pal)
                config.pal = config.unique_palette(config.pal)
                config.initialize_surfaces()
                config.filepath = os.path.dirname(filename)
                config.filename = filename
                config.modified_count = 0
            except Exception as ex:
                close_progress_req(progress_req)
                io_error_req(str(ex), "Unable to open image:\n%s", filename)

class DoSave(MenuAction):
    def selected(self, attrs):
        config.stop_cycling()
        config.clear_pixel_draw_canvas()
        merge_config = copy.copy(config)
        merge_config.pixel_canvas = config.layers.get_flattened(exclude=["R"])
        filename = config.filename
        if filename == "":
            filename = file_req(config.pixel_req_canvas, "Save Picture", "Save", config.filepath, config.filename, filetype_list=pic_filetype_list)
        if filename != (()) and filename != "":
            try:
                save_pic(filename, merge_config)
                config.filename = filename
                config.modified_count = 0
            except:
                io_error_req("Save Error", "Unable to save image:\n%s", filename)
        config.doKeyAction()

class DoSaveAs(MenuAction):
    def selected(self, attrs):
        config.stop_cycling()
        merge_config = copy.copy(config)
        merge_config.pixel_canvas = config.layers.get_flattened(exclude=["R"])
        filename = file_req(config.pixel_req_canvas, "Save Picture", "Save", config.filepath, config.filename, filetype_list=pic_filetype_list)
        if filename != (()) and filename != "":
            try:
                if not save_pic(filename, merge_config, overwrite=False):
                    answer = question_req(config.pixel_req_canvas,
                             "File Exists",
                             "Overwrite this file?",
                             ["Yes","No"],
                             [K_RETURN, K_ESCAPE])
                    if answer == 0:
                        save_pic(filename, merge_config, overwrite=True)
                    else:
                        return
            except:
                io_error_req("Save Error", "Unable to save image:\n%s", filename)
                return
            config.filename = filename
            config.modified_count = 0

class DoRevert(MenuAction):
    def selected(self, attrs):
        global progress_req
        config.stop_cycling()
        config.stencil.enable = False
        filename = config.filename
        if filename != "":
            if config.modified_count >= 1:
                linelen = 33
                if len(filename) > linelen:
                    short_file = "..." + filename[-(linelen-3):]
                else:
                    short_file = filename
                answer = question_req(config.pixel_req_canvas,
                         "Unsaved Changes",
                         "Are you sure you want to revert\nto file:\n"+short_file,
                         ["Yes","No"],
                         [K_RETURN, K_ESCAPE])
                if answer == 1:
                    return
            else:
                return

            progress_req = open_progress_req(config.pixel_req_canvas, "Loading...")
            try:
                config.pixel_canvas = load_pic(filename, config, status_func=load_progress)
                config.bgcolor = 0
                config.color = 1
                close_progress_req(progress_req)
                config.truepal = list(config.pal)
                config.pal = config.unique_palette(config.pal)
                config.initialize_surfaces()
                config.filepath = os.path.dirname(filename)
                config.filename = filename
                config.modified_count = 0
            except:
                close_progress_req(progress_req)
                io_error_req("Load Error", "Unable to open image:\n%s", filename)

class DoPictureFlipX(MenuActionMulti):
    def get_name(self):
        return "Flip Horizontally"

    def selectedMulti(self, attrs):
        config.clear_pixel_draw_canvas()
        config.stencil.enable = False
        config.pixel_canvas = pygame.transform.flip(config.pixel_canvas, True, False)

class DoPictureFlipY(MenuActionMulti):
    def get_name(self):
        return "Flip Vertically"

    def selectedMulti(self, attrs):
        config.clear_pixel_draw_canvas()
        config.stencil.enable = False
        config.pixel_canvas = pygame.transform.flip(config.pixel_canvas, False, True)

class DoPalette(MenuAction):
    def selected(self, attrs):
        self.toolHide()
        palette_req(config.pixel_req_canvas)
        config.save_undo()
        config.doKeyAction()

def resizePalette(origpal, numcol):
    if len(origpal) < numcol:
        pal = list(origpal)
        defpal = config.get_default_palette(numcol)
        while len(pal) < numcol:
            pal.append(defpal[len(pal)])
    elif len(origpal) > numcol:
        pal = origpal[0:numcol]
    else:
        pal = origpal
    return pal

class DoPictureBrushPalette(MenuAction):
    def selected(self, attrs):
        if config.brush.pal != None:
            config.stop_cycling()
            truepal = resizePalette(config.brush.pal, config.NUM_COLORS)
            pal = config.quantize_palette(truepal, config.color_depth)
            config.pal = list(pal)
            config.truepal = list(truepal)
            config.set_all_palettes(pal, config.truepal)

class DoPictureRestorePalette(MenuAction):
    def selected(self, attrs):
        config.stop_cycling()
        pal = resizePalette(config.loadpal, config.NUM_COLORS)
        config.pal = list(pal)
        config.truepal = list(pal)
        config.set_all_palettes(pal, config.truepal)

class DoPictureDefaultPalette(MenuAction):
    def selected(self, attrs):
        config.stop_cycling()
        pal = config.get_default_palette(config.NUM_COLORS)
        config.pal = list(pal)
        config.truepal = list(pal)
        config.set_all_palettes(pal, config.truepal)

class DoCycle(MenuAction):
    def selected(self, attrs):
        if config.cycling:
            config.stop_cycling()
        else:
            config.start_cycling()

class DoPictureBG2FG(MenuActionMulti):
    def get_name(self):
        return "Copy BG to FG"

    def selectedMulti(self, attrs):
        config.stop_cycling()
        config.stencil.enable = False
        #replace FG color with BG color
        surf_array = pygame.surfarray.pixels2d(config.pixel_canvas)
        bgcolor = config.bgcolor
        color = config.color
        tfarray = np.equal(surf_array, bgcolor)
        surf_array[tfarray] = color
        surf_array = None

class DoPictureBGxFG(MenuActionMulti):
    def get_name(self):
        return "Swap BG and FG"

    def selectedMulti(self, attrs):
        config.stop_cycling()
        config.stencil.enable = False
        #swap FG color with BG color
        surf_array = pygame.surfarray.pixels2d(config.pixel_canvas)
        bgcolor = config.bgcolor
        color = config.color
        bgarray = np.equal(surf_array, bgcolor)
        fgarray = np.equal(surf_array, color)
        surf_array[bgarray] = color
        surf_array[fgarray] = bgcolor
        surf_array = None

class DoPictureRemap(MenuActionMulti):
    def get_name(self):
        return "Remap Palette"

    def selectedMulti(self, attrs):
        config.stop_cycling()
        config.stencil.enable = False
        config.pixel_canvas.set_palette(config.loadpal)
        config.pixel_canvas = convert8(config.pixel_canvas.convert(), config.pal)
        config.set_all_palettes(config.pal)
        config.clear_undo()

class DoSpareSwap(MenuAction):
    def selected(self, attrs):
        config.clear_pixel_draw_canvas()
        config.stencil.enable = False

        #Back up current canvas
        config.anim.save_curr_frame()
        i = config.proj_index
        config.proj[i].pixel_canvas = config.pixel_canvas
        config.proj[i].filepath = config.filepath
        config.proj[i].filename = config.filename
        config.proj[i].modified_count = config.modified_count
        config.proj[i].anim = config.anim
        config.proj[i].layers = config.layers
        config.proj[i].indicators = config.menubar.indicators

        #Switch to new canvas
        config.proj_index = (config.proj_index + 1) % len(config.proj)
        i = config.proj_index
        config.pixel_canvas = config.proj[i].pixel_canvas
        config.filepath = config.proj[i].filepath
        config.filename = config.proj[i].filename
        config.modified_count = config.proj[i].modified_count
        config.anim = config.proj[i].anim
        config.layers = config.proj[i].layers

        if config.layers.has_key("fg"):
            config.stencil = config.layers.get("fg").image
        else:
            config.stencil = Stencil()

        if config.proj[i].indicators is None:
            config.menubar.indicators = {}
        else:
            config.menubar.indicators = config.proj[i].indicators

        config.anim.show_curr_frame(doAction=False)

        config.clear_undo()
        config.save_undo()
        config.doKeyAction()

class DoSpareCopy(MenuAction):
    def selected(self, attrs):
        sparei = (config.proj_index + 1) % len(config.proj)
        config.clear_pixel_draw_canvas()
        config.proj[sparei].pixel_canvas.blit(config.pixel_canvas, (0,0))
        config.proj[sparei].anim.frame[config.proj[sparei].anim.curr_frame-1].image.blit(config.pixel_canvas, (0,0))
        config.clear_undo()
        config.save_undo()

class DoMergeFront(MenuActionMulti):
    def get_name(self):
        return "Merge Spare in Front"

    def selectedMulti(self, attrs):
        sparei = (config.proj_index + 1) % len(config.proj)
        config.clear_pixel_draw_canvas()
        config.proj[sparei].pixel_canvas.set_colorkey(config.bgcolor)
        config.pixel_canvas.blit(config.proj[sparei].pixel_canvas, (0,0))
        config.proj[sparei].pixel_canvas.set_colorkey(None)

class DoMergeBack(MenuActionMulti):
    def get_name(self):
        return "Merge Spare in Back"

    def selectedMulti(self, attrs):
        sparei = (config.proj_index + 1) % len(config.proj)
        config.clear_pixel_draw_canvas()
        newimage = pygame.Surface(config.pixel_canvas.get_size(), 0, config.pixel_canvas)
        newimage.set_palette(config.pal)
        newimage.blit(config.proj[sparei].pixel_canvas, (0,0))
        config.pixel_canvas.set_colorkey(config.bgcolor)
        newimage.blit(config.pixel_canvas, (0,0))
        config.pixel_canvas.set_colorkey(None)
        config.pixel_canvas.blit(newimage, (0,0))
        newimage = None

class DoPageSize(MenuAction):
    def selected(self, attrs):
        config.stencil.enable = False
        page_size_req(config.pixel_req_canvas)

class DoShowPage(MenuAction):
    def selected(self, attrs):
        config.clear_pixel_draw_canvas()
        page_preview_req(config.pixel_req_canvas)
        config.doKeyAction()

class DoScreenFormat(MenuAction):
    def selected(self, attrs):
        config.stencil.enable = False
        screen_format_req(config.pixel_req_canvas)

class DoAbout(MenuAction):
    def selected(self, attrs):
        about_req(config.pixel_req_canvas)

class DoQuit(MenuAction):
    def selected(self, attrs):
        config.running = False

class DoBrushOpen(MenuAction):
    def selected(self, attrs):
        config.stop_cycling()
        filename = file_req(config.pixel_req_canvas, "Open Brush", "Open", config.filepath, config.filename)
        if filename != (()) and filename != "":
            try:
                brush_config = copy.copy(config)
                newimage = load_pic(filename, brush_config)
                newimage.set_palette(config.pal)
                config.brush = Brush(type=Brush.CUSTOM, screen=newimage, bgcolor=config.bgcolor, pal=brush_config.pal)
                reduced = newimage.copy()
                surf_array = pygame.surfarray.pixels2d(reduced)
                surf_array &= config.NUM_COLORS-1
                surf_array = None
                config.brush.image = reduced
                config.brush.image_orig = reduced
                config.setDrawMode(DrawMode.MATTE)
            except:
                io_error_req("Load Error", "Unable to open brush:\n%s", filename)
        config.doKeyAction()

class DoBrushSaveAs(MenuAction):
    def selected(self, attrs):
        config.stop_cycling()
        filename = file_req(config.pixel_req_canvas, "Save Brush", "Save", config.filepath, config.filename, filetype_list=pic_filetype_list)
        if filename != (()) and filename != "":
            brush_config = copy.copy(config)
            brush_config.pixel_canvas = config.brush.image
            brush_config.pixel_width, brush_config.pixel_height = config.brush.image.get_size()
            try:
                if not save_pic(filename, brush_config, overwrite=False):
                    answer = question_req(config.pixel_req_canvas,
                             "File Exists",
                             "Overwrite this file?",
                             ["Yes","No"],
                             [K_RETURN, K_ESCAPE])
                    if answer == 0:
                            save_pic(filename, brush_config, overwrite=True)
                    else:
                        return
            except:
                io_error_req("Save Error", "Unable to save brush:\n%s", filename)
                return

class DoBrushRestore(MenuAction):
    def selected(self, attrs):
        if config.brush.type != config.brush.CUSTOM:
            if not "image_backup" in dir(config.brush):
                return
            config.brush.type = config.brush.CUSTOM
        backup = config.brush.image_backup.copy()
        backup.set_palette(config.pal)
        surf_array = pygame.surfarray.pixels2d(backup)
        surf_array &= config.NUM_COLORS-1
        surf_array = None
        ow,oh = backup.get_size()
        config.brush.aspect = 1.0
        config.brush.image = backup
        config.brush.image_orig = backup
        config.brush.size = oh
        config.setDrawMode(DrawMode.MATTE)
        config.doKeyAction()

class DoBrushStretch(MenuAction):
    def selected(self, attrs):
        if config.brush.type != Brush.CUSTOM:
            return

        sx, sy = (0,0)
        config.brush.handle_type = config.brush.CORNER_LR
        ow,oh = config.brush.image_orig.get_size()
        w,h = config.brush.image.get_size()
        config.cursor.shape = 4
        config.clear_pixel_draw_canvas()
        config.brush.size = config.brush.size
        config.brush.draw(config.pixel_canvas, config.color, config.get_mouse_pixel_pos(ignore_grid=True))
        config.recompose()
        first_time = True
        wait_for_mouseup = 1 + pygame.mouse.get_pressed()[0]
        while wait_for_mouseup:
            event = config.xevent.poll()
            while event.type == pygame.MOUSEMOTION and config.xevent.peek((MOUSEMOTION)):
                #get rid of extra mouse movements
                event = config.xevent.poll()

            if event.type == pygame.NOEVENT and not first_time:
                event = config.xevent.wait()

            mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
            if event.type == MOUSEMOTION:
                config.clear_pixel_draw_canvas()
                if event.buttons[0] and wait_for_mouseup:
                    if mouseX-sx > 0 and mouseY-sy > 0:
                        config.brush.aspect = (mouseX-sx) / ow * oh / (mouseY-sy)
                    config.brush.size = mouseY-sy
                    config.brush.draw(config.pixel_canvas, config.color, (sx, sy))
                else:
                    config.brush.draw(config.pixel_canvas, config.color, (mouseX, mouseY))
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    sx, sy = (mouseX-w, mouseY-h)
                    config.brush.handle_type = config.brush.CORNER_UL
            elif event.type == MOUSEBUTTONUP and wait_for_mouseup:
                if event.button == 1:
                    wait_for_mouseup -= 1

            config.recompose()
            first_time = False

        config.brush.handle_type = config.brush.CENTER
        config.brush.size = config.brush.size
        config.doKeyAction()


class DoBrushHalve(MenuAction):
    def selected(self, attrs):
        config.brush.size //= 2
        config.doKeyAction()

class DoBrushDouble(MenuAction):
    def selected(self, attrs):
        config.brush.size *= 2
        config.doKeyAction()

class DoBrushDoubleHoriz(MenuAction):
    def selected(self, attrs):
        config.brush.aspect *= 2.0
        config.brush.size = config.brush.size
        config.doKeyAction()

class DoBrushDoubleVert(MenuAction):
    def selected(self, attrs):
        config.brush.aspect /= 2.0
        config.brush.size *= 2
        config.doKeyAction()

class DoBrushFlipX(MenuAction):
    def selected(self, attrs):
        if config.brush.type == Brush.CUSTOM:
            config.brush.image = pygame.transform.flip(config.brush.image, True, False)
            config.brush.image_orig = pygame.transform.flip(config.brush.image_orig, True, False)
            config.brush.handle_frac[0] = 1 - config.brush.handle_frac[0]
            config.brush.size = config.brush.size
            config.doKeyAction()

class DoBrushFlipY(MenuAction):
    def selected(self, attrs):
        if config.brush.type == Brush.CUSTOM:
            config.brush.image = pygame.transform.flip(config.brush.image, False, True)
            config.brush.image_orig = pygame.transform.flip(config.brush.image_orig, False, True)
            config.brush.handle_frac[1] = 1 - config.brush.handle_frac[1]
            config.brush.size = config.brush.size
            config.doKeyAction()

class DoBrushOutline(MenuAction):
    def selected(self, attrs):
        if config.brush.type != Brush.CUSTOM:
            return
        if config.color == config.brush.bgcolor:
            return
        w,h = config.brush.image.get_size()

        #create surface to hold new brush
        newimage = pygame.Surface((w+2, h+2),0, config.pixel_canvas)
        newimage.set_palette(config.pal)
        newimage.fill(config.brush.bgcolor)
        newimage.set_colorkey(config.brush.bgcolor)

        #create brush to add edges
        addimage = config.brush.image.copy()
        surf_array = pygame.surfarray.pixels2d(addimage)
        bgcolor = config.brush.bgcolor
        color = config.color
        tfarray = np.not_equal(surf_array, bgcolor)
        surf_array[tfarray] = color
        surf_array[np.logical_not(tfarray)] = bgcolor
        surf_array = None
        addimage.set_colorkey(bgcolor)
 
        #edge up,down,left,right
        newimage.blit(addimage, (0,1))
        newimage.blit(addimage, (2,1))
        newimage.blit(addimage, (1,0))
        newimage.blit(addimage, (1,2))
        #blit original brush
        newimage.blit(config.brush.image, (1,1))

        #put new image in brush
        config.brush.image = newimage
        config.brush.image_orig = newimage
        config.brush.aspect = 1
        config.brush.size = h+2
        config.doKeyAction()

class DoBrushTrim(MenuAction):
    def selected(self, attrs):
        if config.brush.type != Brush.CUSTOM:
            return
        w,h = config.brush.image.get_size()
        if w <= 2 or h <= 2:
            return
        #create surface to hold new brush
        newimage = pygame.Surface((w-2, h-2),0, config.pixel_canvas)
        newimage.set_palette(config.pal)
        newimage.set_colorkey(config.brush.bgcolor)

        #create brush to cut away edges
        cutimage = config.brush.image.copy()
        surf_array = pygame.surfarray.pixels2d(cutimage)
        bgcolor = config.brush.bgcolor
        color = (bgcolor+1) % config.NUM_COLORS
        tfarray = np.not_equal(surf_array, bgcolor)
        surf_array[tfarray] = color
        surf_array[np.logical_not(tfarray)] = bgcolor
        surf_array = None
        cutimage.set_colorkey(color)
 
        #blit original brush
        newimage.blit(config.brush.image, (-1,-1))
        #cut up,down,left,right
        newimage.blit(cutimage, (-1,-2))
        newimage.blit(cutimage, (-1,0))
        newimage.blit(cutimage, (-2,-1))
        newimage.blit(cutimage, (0,-1))

        #put new image in brush
        config.brush.image = newimage
        config.brush.image_orig = newimage
        config.brush.aspect = 1
        config.brush.size = h-2
        config.doKeyAction()

class DoBrushRotate90(MenuAction):
    def selected(self, attrs):
        if config.brush.type == Brush.CUSTOM:
            config.brush.image = pygame.transform.rotate(config.brush.image, -90)
            config.brush.image_orig = pygame.transform.rotate(config.brush.image_orig, -90)
            config.brush.handle_frac = [1-config.brush.handle_frac[1], config.brush.handle_frac[0]]
            config.brush.aspect = 1.0 / config.brush.aspect
            bx,by,bw,bh = config.brush.rect
            config.brush.rect = [by,bx,bh,bw]
            config.brush.size = bw
            config.brush.cache = BrushCache()
            config.brush.size = config.brush.size
            config.doKeyAction()

class DoBrushRotateAny(MenuAction):
    def selected(self, attrs):
        if config.brush.type != Brush.CUSTOM:
            return

        sx, sy = (0,0)
        ow,oh = config.brush.image_orig.get_size()
        w,h = config.brush.image.get_size()
        config.cursor.shape = 5
        config.clear_pixel_draw_canvas()
        config.brush.size = config.brush.size
        config.brush.draw(config.pixel_canvas, config.color, config.get_mouse_pixel_pos(ignore_grid=True))
        config.recompose()
        rotimage = config.brush.image
        first_time = True
        wait_for_mouseup = 1 + pygame.mouse.get_pressed()[0]
        while wait_for_mouseup:
            event = config.xevent.poll()
            while event.type == pygame.MOUSEMOTION and config.xevent.peek((MOUSEMOTION)):
                #get rid of extra mouse movements
                event = config.xevent.poll()

            if event.type == pygame.NOEVENT and not first_time:
                event = config.xevent.wait()

            mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
            if event.type == MOUSEMOTION:
                config.clear_pixel_draw_canvas()
                if event.buttons[0] and wait_for_mouseup:
                    angle = int(mda - (math.atan2(mouseY-sy, mouseX-sx) * 180.0 / math.pi))
                    rotimage = pygame.transform.rotate(config.brush.image, angle)
                    rw,rh = rotimage.get_size()
                    config.pixel_canvas.blit(rotimage, (sx-rw//2,sy-rh//2))
                    config.menubar.title_right = "%d\xB0"%(-angle)
                else:
                    config.pixel_canvas.blit(rotimage, (mouseX-w,mouseY-h))
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    sx, sy = (mouseX-w//2, mouseY-h//2)
                    mda = math.atan2(mouseY-sy, mouseX-sx) * 180.0 / math.pi
            elif event.type == MOUSEBUTTONUP and wait_for_mouseup:
                if event.button == 1:
                    wait_for_mouseup -= 1

            config.recompose()
            first_time = False

        config.menubar.title_right = ""
        config.brush.image = rotimage
        config.brush.image_orig = rotimage
        config.brush.aspect = 1.0
        config.brush.handle_type = config.brush.CENTER
        config.brush.size = rotimage.get_height()
        config.doKeyAction()

class DoBrushShear(MenuAction):
    def selected(self, attrs):
        if config.brush.type != Brush.CUSTOM:
            return

        sx, sy = (0,0)
        ow,oh = config.brush.image_orig.get_size()
        w,h = config.brush.image.get_size()
        config.cursor.shape = 6
        config.clear_pixel_draw_canvas()
        config.brush.size = config.brush.size
        config.brush.draw(config.pixel_canvas, config.color, config.get_mouse_pixel_pos(ignore_grid=True))
        config.recompose()
        shearimage = config.brush.image
        first_time = True
        wait_for_mouseup = 1 + pygame.mouse.get_pressed()[0]
        while wait_for_mouseup:
            event = config.xevent.poll()
            while event.type == pygame.MOUSEMOTION and config.xevent.peek((MOUSEMOTION)):
                #get rid of extra mouse movements
                event = config.xevent.poll()

            if event.type == pygame.NOEVENT and not first_time:
                event = config.xevent.wait()

            mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
            if event.type == MOUSEMOTION:
                config.clear_pixel_draw_canvas()
                if event.buttons[0] and wait_for_mouseup:
                    xoffset = mouseX - mx
                    shearimage = pygame.Surface((w+abs(xoffset), h),0, config.pixel_canvas)
                    shearimage.set_palette(config.pal)
                    shearimage.set_colorkey(config.brush.bgcolor)
                    shearimage.fill(config.brush.bgcolor)
                    clist = drawline(config.pixel_canvas, 1, (0,0), (xoffset,h), coordsonly=True)
                    if xoffset < 0:
                        imgXoffset = -xoffset
                    else:
                        imgXoffset = 0
                    prevy = -1
                    for coord in clist:
                        if prevy != coord[1]:
                            shearimage.blit(config.brush.image, (imgXoffset+coord[0],coord[1]), area=(0,coord[1],w,1))
                            prevy = coord[1]

                    config.pixel_canvas.blit(shearimage, (sx-w//2-imgXoffset,sy-h//2))
                    config.menubar.title_right = "%d"%(xoffset)
                else:
                    config.pixel_canvas.blit(shearimage, (mouseX-w,mouseY-h))
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    sx, sy = (mouseX-w//2, mouseY-h//2)
                    mx = mouseX
            elif event.type == MOUSEBUTTONUP and wait_for_mouseup:
                if event.button == 1:
                    wait_for_mouseup -= 1

            config.recompose()
            first_time = False

        config.menubar.title_right = ""
        config.brush.image = shearimage
        config.brush.image_orig = shearimage
        config.brush.aspect = 1.0
        config.brush.handle_type = config.brush.CENTER
        config.brush.size = shearimage.get_height()
        config.doKeyAction()

class DoBrushBG2FG(MenuAction):
    def selected(self, attrs):
        if config.brush.type != Brush.CUSTOM:
            return
        if config.color == config.brush.bgcolor:
            return
        w,h = config.brush.image.get_size()

        #replace FG color with BG color
        surf_array = pygame.surfarray.pixels2d(config.brush.image)
        bgcolor = config.bgcolor
        color = config.color
        tfarray = np.equal(surf_array, bgcolor)
        surf_array[tfarray] = color
        surf_array = None
 
        #put new image in brush
        config.brush.image_orig = config.brush.image
        config.brush.aspect = 1
        config.brush.size = h
        config.doKeyAction()

class DoBrushBGxFG(MenuAction):
    def selected(self, attrs):
        if config.brush.type != Brush.CUSTOM:
            return
        if config.color == config.brush.bgcolor:
            return
        w,h = config.brush.image.get_size()

        #swap FG color with BG color
        surf_array = pygame.surfarray.pixels2d(config.brush.image)
        bgcolor = config.bgcolor
        color = config.color
        bgarray = np.equal(surf_array, bgcolor)
        fgarray = np.equal(surf_array, color)
        surf_array[bgarray] = color
        surf_array[fgarray] = bgcolor
        surf_array = None
 
        #put new image in brush
        config.brush.image_orig = config.brush.image
        config.brush.aspect = 1
        config.brush.size = h
        config.doKeyAction()

class DoBrushRemap(MenuAction):
    def selected(self, attrs):
        if config.brush.type != Brush.CUSTOM:
            return
        config.brush.image.set_palette(config.brush.pal)
        newimage = convert8(config.brush.image.convert(), config.pal)
        config.brush = Brush(type=Brush.CUSTOM, screen=newimage, bgcolor=config.bgcolor, pal=config.pal)
        config.doKeyAction()

class DoBrushChangeTransp(MenuAction):
    def selected(self, attrs):
        if config.brush.type != Brush.CUSTOM:
            return
        config.brush.image.set_colorkey(config.bgcolor)
        config.brush.bgcolor = config.bgcolor
        config.brush.bgcolor_orig = config.bgcolor
        config.brush.image_orig = config.brush.image
        config.brush.size = config.brush.size
        config.doKeyAction()

class DoBrushBendX(MenuAction):
    def selected(self, attrs):
        if config.brush.type != Brush.CUSTOM:
            return

        sx, sy = (0,0)
        ow,oh = config.brush.image_orig.get_size()
        w,h = config.brush.image.get_size()
        config.cursor.shape = 6
        config.clear_pixel_draw_canvas()
        config.brush.size = config.brush.size
        config.brush.draw(config.pixel_canvas, config.color, config.get_mouse_pixel_pos(ignore_grid=True))
        config.recompose()
        bendimage = config.brush.image
        first_time = True
        wait_for_mouseup = 1 + pygame.mouse.get_pressed()[0]
        while wait_for_mouseup:
            event = config.xevent.poll()
            while event.type == pygame.MOUSEMOTION and config.xevent.peek((MOUSEMOTION)):
                #get rid of extra mouse movements
                event = config.xevent.poll()

            if event.type == pygame.NOEVENT and not first_time:
                event = config.xevent.wait()

            mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
            if event.type == MOUSEMOTION:
                config.clear_pixel_draw_canvas()
                if event.buttons[0] and wait_for_mouseup:
                    xoffset = mouseX - mx
                    bendimage = pygame.Surface((w+abs(xoffset), h),0, config.pixel_canvas)
                    bendimage.set_palette(config.pal)
                    bendimage.set_colorkey(config.brush.bgcolor)
                    bendimage.fill(config.brush.bgcolor)
                    if mouseY-my < -h//2:
                        clist = drawcurve(config.pixel_canvas, 1, (mouseX-mx, 0), (0,h), ((mouseX-mx)//4,h//2), coordsonly=True, handlesymm=False)
                    elif mouseY-my > h//2:
                        clist = drawcurve(config.pixel_canvas, 1, (mouseX-mx, h), (0,0), ((mouseX-mx)//4,h//2), coordsonly=True, handlesymm=False)
                    else:
                        clist = drawcurve(config.pixel_canvas, 1, (0,0), (0,h), (mouseX-mx, mouseY-my+h//2), coordsonly=True, handlesymm=False)
                    if xoffset < 0:
                        imgXoffset = -xoffset
                    else:
                        imgXoffset = 0
                    prevy = -1
                    for seg in clist:
                        for coord in seg:
                            if prevy != coord[1]:
                                bendimage.blit(config.brush.image, (imgXoffset+coord[0],coord[1]), area=(0,coord[1],w,1))
                                prevy = coord[1]

                    config.pixel_canvas.blit(bendimage, (sx-imgXoffset,sy))
                    config.menubar.title_right = "%d"%(xoffset)
                else:
                    config.pixel_canvas.blit(bendimage, (mouseX-w,mouseY-h//2))
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    sx, sy = (mouseX-w, mouseY-h//2)
                    mx, my = (mouseX,mouseY)
            elif event.type == MOUSEBUTTONUP and wait_for_mouseup:
                if event.button == 1:
                    wait_for_mouseup -= 1

            config.recompose()
            first_time = False

        config.menubar.title_right = ""
        config.brush.image = bendimage
        config.brush.image_orig = bendimage
        config.brush.aspect = 1.0
        config.brush.handle_type = config.brush.CENTER
        config.brush.size = bendimage.get_height()
        config.doKeyAction()

class DoBrushBendY(MenuAction):
    def selected(self, attrs):
        if config.brush.type != Brush.CUSTOM:
            return

        sx, sy = (0,0)
        ow,oh = config.brush.image_orig.get_size()
        w,h = config.brush.image.get_size()
        config.cursor.shape = 7
        config.clear_pixel_draw_canvas()
        config.brush.size = config.brush.size
        config.brush.draw(config.pixel_canvas, config.color, config.get_mouse_pixel_pos(ignore_grid=True))
        config.recompose()
        bendimage = config.brush.image
        first_time = True
        wait_for_mouseup = 1 + pygame.mouse.get_pressed()[0]
        while wait_for_mouseup:
            event = config.xevent.poll()
            while event.type == pygame.MOUSEMOTION and config.xevent.peek((MOUSEMOTION)):
                #get rid of extra mouse movements
                event = config.xevent.poll()

            if event.type == pygame.NOEVENT and not first_time:
                event = config.xevent.wait()

            mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
            if event.type == MOUSEMOTION:
                config.clear_pixel_draw_canvas()
                if event.buttons[0] and wait_for_mouseup:
                    yoffset = mouseY - my
                    bendimage = pygame.Surface((w, h+abs(yoffset)),0, config.pixel_canvas)
                    bendimage.set_palette(config.pal)
                    bendimage.set_colorkey(config.brush.bgcolor)
                    bendimage.fill(config.brush.bgcolor)
                    if mouseX-mx < -w//2:
                        clist = drawcurve(config.pixel_canvas, 1, (0, mouseY-my), (w,0), (w//2,(mouseY-my)//4), coordsonly=True, handlesymm=False)
                    elif mouseX-mx > w//2:
                        clist = drawcurve(config.pixel_canvas, 1, (w, mouseY-my), (0,0), (w//2,(mouseY-my)//4), coordsonly=True, handlesymm=False)
                    else:
                        clist = drawcurve(config.pixel_canvas, 1, (0,0), (w,0), (mouseX-mx+w//2, mouseY-my), coordsonly=True, handlesymm=False)
                    if yoffset < 0:
                        imgYoffset = -yoffset
                    else:
                        imgYoffset = 0
                    prevx = -1
                    for seg in clist:
                        for coord in seg:
                            if prevx != coord[0]:
                                bendimage.blit(config.brush.image, (coord[0],imgYoffset+coord[1]), area=(coord[0],0,1,h))
                                prevx = coord[0]

                    config.pixel_canvas.blit(bendimage, (sx,sy-imgYoffset))
                    config.menubar.title_right = "%d"%(yoffset)
                else:
                    config.pixel_canvas.blit(bendimage, (mouseX-w//2,mouseY-h))
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    sx, sy = (mouseX-w//2, mouseY-h)
                    mx, my = (mouseX,mouseY)
            elif event.type == MOUSEBUTTONUP and wait_for_mouseup:
                if event.button == 1:
                    wait_for_mouseup -= 1

            config.recompose()
            first_time = False

        config.menubar.title_right = ""
        config.brush.image = bendimage
        config.brush.image_orig = bendimage
        config.brush.aspect = 1.0
        config.brush.handle_type = config.brush.CENTER
        config.brush.size = bendimage.get_height()
        config.doKeyAction()

class DoBrushHandleCenter(MenuAction):
    def selected(self, attrs):
        config.brush.handle_type = config.brush.CENTER
        config.brush.size = config.brush.size
        config.doKeyAction()

class DoBrushHandleCorner(MenuAction):
    def selected(self, attrs):
        if config.brush.handle_type >= config.brush.CORNER_UL and config.brush.handle_type < config.brush.CORNER_LL:
            config.brush.handle_type += 1
        else:
            config.brush.handle_type = config.brush.CORNER_UL
        config.brush.size = config.brush.size
        config.doKeyAction()

class DoBrushHandlePlace(MenuAction):
    def selected(self, attrs):
        point_coords = config.get_mouse_pixel_pos(ignore_grid=True)
        config.recompose()
        point_placed = False
        first_time = True
        while not point_placed:
            event = config.xevent.poll()
            while event.type == pygame.MOUSEMOTION and config.xevent.peek((MOUSEMOTION)):
                #get rid of extra mouse movements
                event = config.xevent.poll()

            if event.type == pygame.NOEVENT and not first_time:
                event = config.xevent.wait()

            mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
            if event.type == MOUSEMOTION:
                if not event.buttons[0]:
                    point_coords = (mouseX, mouseY)
            elif event.type == MOUSEBUTTONUP:
                point_placed = True
            config.clear_pixel_draw_canvas()
            config.brush.draw(config.pixel_canvas, config.color, point_coords)
            #current center
            drawline(config.pixel_canvas, 1,
                (mouseX,0), (mouseX,config.pixel_canvas.get_height()),
                xormode=True)
            drawline(config.pixel_canvas, 1,
                (0,mouseY), (config.pixel_canvas.get_width(),mouseY),
                xormode=True)
            config.recompose()
            first_time = False

        bxo = point_coords[0]-config.brush.handle[0]
        byo = point_coords[1]-config.brush.handle[1]
        bw,bh = config.brush.get_wh()

        config.brush.handle_type = config.brush.PLACE
        config.brush.handle_frac = [(mouseX-bxo)/bw, (mouseY-byo)/bh]
        config.brush.size = config.brush.size
        config.doKeyAction()

class DoMode(MenuAction):
    def selected(self, attrs):
        if not self.gadget.enabled:
            return
        for menug in self.gadget.parent.menug_list:
            menug.checked = False
        self.gadget.checked = True
        config.drawmode.value = DrawMode.LABEL_STR.index(self.gadget.label.lstrip())
        config.menubar.title_extra = self.gadget.label
        config.doKeyAction()

class DoAnimOpen(MenuAction):
    def selected(self, attrs):
        config.anim.open_file()

class DoAnimSave(MenuAction):
    def selected(self, attrs):
        config.anim.save_file()

class DoAnimFrameImport(MenuAction):
    def selected(self, attrs):
        config.anim.import_frames()

class DoAnimFrameExport(MenuAction):
    def selected(self, attrs):
        config.anim.export_frames()

class DoAnimFrameAdd(MenuAction):
    def selected(self, attrs):
        config.anim.add_frame()

class DoAnimFrameSetNumber(MenuAction):
    def selected(self, attrs):
        config.anim.num_frames_req(config.pixel_req_canvas)

class DoAnimFrameCopyAll(MenuAction):
    def selected(self, attrs):
        config.anim.copy_frame_to_all()

class DoAnimFrameDelete(MenuAction):
    def selected(self, attrs):
        config.anim.delete_frame()

class DoAnimFrameDeleteAll(MenuAction):
    def selected(self, attrs):
        config.anim.delete_all_frames()

class DoAnimControlSetRate(MenuAction):
    def selected(self, attrs):
        config.anim.fps_list_req(config.pixel_req_canvas)

class DoStencilMake(MenuActionMulti):
    def is_ask_multi(self):
        return False

    def selected(self, attrs):
        if stencil_req(config.pixel_req_canvas):
            super().selected(attrs)

    def selectedMulti(self, attrs):
        config.stencil.remake(config.pixel_canvas)

class DoStencilRemake(MenuActionMulti):
    def is_ask_multi(self):
        return False

    def selectedMulti(self, attrs):
        config.stencil.remake(config.pixel_canvas)

class DoStencilLockFG(MenuActionMulti):
    def is_ask_multi(self):
        return False

    def selectedMulti(self, attrs):
        config.stencil.lock_fg(config.pixel_canvas)
        config.doKeyAction()

class DoStencilReverse(MenuAction):
    def selected(self, attrs):
        if config.stencil.enable:
            config.clear_pixel_draw_canvas()
            config.stencil.draw(config.pixel_canvas)
            config.save_undo()
            config.stencil.reverse()
        config.doKeyAction()

class DoStencilOnOff(MenuAction):
    def selected(self, attrs):
        if config.stencil.enable:
            config.clear_pixel_draw_canvas()
            config.stencil.draw(config.pixel_canvas)
            config.save_undo()
        config.stencil.enable = not config.stencil.enable
        config.doKeyAction()

class DoStencilFree(MenuActionMulti):
    def is_ask_multi(self):
        return False

    def selectedMulti(self, attrs):
        if config.stencil.image != None:
            config.clear_pixel_draw_canvas()
            config.stencil.draw(config.pixel_canvas)
            config.save_undo()
        config.stencil.free()

class DoBackgroundFix(MenuAction):
    def selected(self, attrs):
        config.menubar.menu_id("effect").menu_id("background").menu_id("free").action.selected("")
        config.clear_pixel_draw_canvas()
        for frame_no in config.anim:
            bg_img = config.pixel_canvas.copy()
            config.layers.set("background", bg_img, priority=config.LAYER_BG_PRIORITY, visible=True, indicator="B")
            config.brush.pen_down = False
            config.bgcolor = 0;
            config.pixel_canvas.fill(config.bgcolor);
            config.pixel_canvas.set_colorkey(config.bgcolor)
        config.save_undo()
        config.toolbar.tool_id("text").action.cleartext()
        config.doKeyAction()

class DoBackgroundOpen(MenuAction):
    def selected(self, attrs):
        config.menubar.menu_id("effect").menu_id("background").menu_id("free").action.selected("")
        filename = file_req(config.pixel_req_canvas, "Open Background Picture", "Open", config.filepath, config.filename)
        if filename != (()) and filename != "":
            try:
                bg_img = pygame.image.load(filename)
                bg_img = pygame.transform.smoothscale(bg_img.convert(), config.pixel_canvas.get_size())
                for frame_no in config.anim:
                    config.layers.set("background", bg_img, priority=config.LAYER_BG_PRIORITY, visible=True, indicator="R")
                config.bgcolor = 0;
                config.pixel_canvas.set_colorkey(config.bgcolor)
            except:
                io_error_req("Load Error", "Unable to open image:\n%s", filename)
        config.doKeyAction()

class DoBackgroundOnOff(MenuAction):
    def selected(self, attrs):
        if config.layers.has_key("background"):
            if config.layers.get("background").indicator == "":
                return
            opacity = config.layers.get("canvas").opacity
            enable_state = config.layers.get("background").visible
            if enable_state:
                if opacity == 255:
                    opacity = 128
                else:
                    enable_state = False
                    opacity = 255
            else:
                enable_state = True
                opacity = 255

            for f in config.anim.frame:
                if "background" in f.layers.layers:
                    f.layers.get("background").visible = enable_state
                f.layers.get("canvas").opacity = opacity
            config.layers.get("background").visible = enable_state
            config.layers.get("canvas").opacity = opacity
            opacity = config.layers.get("canvas").opacity
            config.doKeyAction()

class DoBackgroundFree(MenuAction):
    def selected(self, attrs):
        if config.layers.has_key("background"):
            config.clear_pixel_draw_canvas()
            for frame_no in config.anim:
                bglayer = config.layers.get("background")
                if bglayer.image != None and bglayer.indicator != "R":
                    config.pixel_canvas.set_colorkey(0)
                    bglayer.image.blit(config.pixel_canvas, (0,0))
                    config.pixel_canvas.blit(bglayer.image, (0,0))
                    config.pixel_canvas.set_colorkey(None)
                    config.save_undo()
                config.layers.delete("background")
                config.layers.get("canvas").opacity = 255
            config.doKeyAction()

class DoPrefsCoords(MenuAction):
    def selected(self, attrs):
        if not self.gadget.enabled:
            return
        self.gadget.checked = not self.gadget.checked
        config.coords_on = self.gadget.checked
        config.doKeyAction()

class DoPrefsFlipCoords(MenuAction):
    def selected(self, attrs):
        if not self.gadget.enabled:
            return
        self.gadget.checked = not self.gadget.checked
        config.coords_flip = self.gadget.checked
        config.doKeyAction()

class DoPrefs1BasedCoords(MenuAction):
    def selected(self, attrs):
        if not self.gadget.enabled:
            return
        self.gadget.checked = not self.gadget.checked
        config.coords_1based = self.gadget.checked
        config.doKeyAction()

class DoPrefsAutoTransp(MenuAction):
    def selected(self, attrs):
        if not self.gadget.enabled:
            return
        self.gadget.checked = not self.gadget.checked
        config.auto_transp_on = self.gadget.checked
        config.doKeyAction()

class DoPrefsMultiCycle(MenuAction):
    def selected(self, attrs):
        if not self.gadget.enabled:
            return
        self.gadget.checked = not self.gadget.checked
        config.multicycle = self.gadget.checked
        config.doKeyAction()

class DoPrefsHideMenus(MenuAction):
    def selected(self, attrs):
        if not self.gadget.enabled:
            return
        self.gadget.checked = not self.gadget.checked
        config.menubar.hide_menus = self.gadget.checked
        config.doKeyAction()

class DoPrefsForce1To1Pixels(MenuAction):
    def selected(self, attrs):
        if not self.gadget.enabled:
            return
        self.gadget.checked = not self.gadget.checked
        config.force_1_to_1_pixels = self.gadget.checked
        if config.force_1_to_1_pixels:
            config.set_aspect(0)
            config.resize_display()
            config.minitoolbar.tool_id("aspect").state = 0
        config.doKeyAction()

class DoPrefsTrueSymmetry(MenuAction):
    def selected(self, attrs):
        if not self.gadget.enabled:
            return
        self.gadget.checked = not self.gadget.checked
        config.true_symmetry = self.gadget.checked
        config.doKeyAction()

class DoPrefsSave(MenuAction):
    def selected(self, attrs):
        config.saveConfig()
        config.doKeyAction()

def init_menubar(config_in):
    global config
    config = config_in

    h = config.fonty
    w = config.screen_width
    menubar_canvas = pygame.Surface((w,h),0)
    menubar = Menubar(menubar_canvas, (0,0,w,h), config.font)
    menubar.title = "PyDPainter"
    menubar.title_extra = " Color"
    menubar.add_menu(
        ["Picture", [
            ["New...", "ctrl-n", DoNew],
            ["Open...", "ctrl-o", DoOpen],
            ["Save", "ctrl-s", DoSave],
            ["Save as...", "ctrl-S", DoSaveAs],
            ["Revert...", "ctrl-alt-z", DoRevert],
            ["Print...", "ctrl-p"],
            ["---"],
            ["Flip", [
                ["Horiz", " ", DoPictureFlipX],
                ["Vert", " ", DoPictureFlipY],
                ]],
            ["Change Color", [
                ["Palette...", "p", DoPalette],
                ["Use Brush Palette", " ", DoPictureBrushPalette],
                ["Restore Palette", " ", DoPictureRestorePalette],
                ["Default Palette", " ", DoPictureDefaultPalette],
                ["Cycle","Tab", DoCycle],
                ["BG -> FG", " ", DoPictureBG2FG],
                ["BG <-> FG", " ", DoPictureBGxFG],
                ["Remap", " ", DoPictureRemap],
                ]],
            ["Spare", [
                ["Swap", "j", DoSpareSwap],
                ["Copy To Spare", "J", DoSpareCopy],
                ["Merge in front", " ", DoMergeFront],
                ["Merge in back", " ", DoMergeBack],
                ]],
            ["Page Size...", " ", DoPageSize],
            ["Show Page", "S", DoShowPage],
            ["Screen Format...", " ", DoScreenFormat],
            ["About...", " ", DoAbout],
            ["Quit", "Q", DoQuit],
        ]])
    menubar.add_menu(
        ["Brush", [
            ["Open...", " ", DoBrushOpen],
            ["Save as...", " ", DoBrushSaveAs],
            ["Restore","B", DoBrushRestore],
            ["Size", [
                ["Stretch", "Z", DoBrushStretch],
                ["Halve", "h", DoBrushHalve],
                ["Double", "H", DoBrushDouble],
                ["Double Horiz", "X", DoBrushDoubleHoriz],
                ["Double Vert", "Y", DoBrushDoubleVert],
                ]],
            ["Flip", [
                ["Horiz", "x", DoBrushFlipX],
                ["Vert", "y", DoBrushFlipY],
                ]],
            ["Edge", [
                ["Outline", "o", DoBrushOutline],
                ["Trim", "O", DoBrushTrim],
                ]],
            ["Rotate", [
                ["90 Degrees", "z", DoBrushRotate90],
                ["Any Angle", " ", DoBrushRotateAny],
                ["Shear", " ", DoBrushShear],
                ]],
            ["Change Color", [
                ["BG -> FG", " ", DoBrushBG2FG],
                ["BG <-> FG", " ", DoBrushBGxFG],
                ["Remap", " ", DoBrushRemap],
                ["Change Transp", " ",DoBrushChangeTransp],
                ]],
            ["Bend", [
                ["Horiz", " ", DoBrushBendX],
                ["Vert", " ", DoBrushBendY],
                ]],
            ["Handle", [
                ["Center","alt-s", DoBrushHandleCenter],
                ["Corner","alt-x", DoBrushHandleCorner],
                ["Place","alt-z", DoBrushHandlePlace],
                ]],
        ]])
    menubar.add_menu(
        ["Mode", [
            ["!/Matte", "F1", DoMode],
            ["\\Color", "F2", DoMode],
            ["!/Repl", "F3", DoMode],
            ["/Smear", "F4", DoMode],
            ["/Shade", "F5", DoMode],
            ["/Blend", "F6", DoMode],
            ["/Cycle", "F7", DoMode],
            ["/Smooth","F8", DoMode],
            ["/Tint", "F9", DoMode],
            ["!/HBrite"],
        ]])

    menubar.add_menu(
        ["Anim", [
            ["Open...", " ", DoAnimOpen],
            ["Save...", " ", DoAnimSave],
            ["Move..."],
            ["Frames", [
                ["Import...", " ", DoAnimFrameImport],
                ["Export...", " ", DoAnimFrameExport],
                ["Set #...", " ", DoAnimFrameSetNumber],
                ["Copy to All", " ", DoAnimFrameCopyAll],
                ["Add Frames", " ", DoAnimFrameAdd],
                ["Delete Frames", " ", DoAnimFrameDelete],
                ["Delete All", " ", DoAnimFrameDeleteAll],
            ]],
            ["Control", [
                ["Set Rate...", " ", DoAnimControlSetRate],
                ["Previous", "1", DoDummy],
                ["Next", "2", DoDummy],
                ["Go to...", "3", DoDummy],
                ["Play", "4", DoDummy],
                ["Play once", "5", DoDummy],
                ["Ping-pong", "6", DoDummy],
            ]],
            ["Anim Brush"],
        ]])

    menubar.add_menu(
        ["Effect", [
            ["Stencil", [
                ["Make...", "~", DoStencilMake],
                ["Remake", " ", DoStencilRemake],
                ["Lock FG", " ", DoStencilLockFG],
                ["Reverse", " ", DoStencilReverse],
                ["On/Off", "`", DoStencilOnOff],
                ["Free", " ", DoStencilFree],
            ]],
            ["Background", [
                ["Fix", " ", DoBackgroundFix],
                ["Open...", " ", DoBackgroundOpen],
                ["On/Off", "ctrl-b", DoBackgroundOnOff],
                ["Free", " ", DoBackgroundFree],
            ]],
            ["!Perspective"],
        ]])

    menubar.add_menu(
        ["Prefs", [
            ["/AutoTransp", " ", DoPrefsAutoTransp],
            ["/MultiCycle", " ", DoPrefsMultiCycle],
            ["/Hide Menus", " ", DoPrefsHideMenus],
            ["/Force 1:1 Pixels", " ", DoPrefsForce1To1Pixels],
            ["/True Symmetry", " ", DoPrefsTrueSymmetry],
            ["/Coords", [
                ["/Show", "|", DoPrefsCoords],
                ["/Flip", " ", DoPrefsFlipCoords],
                ["/1-Based", " ", DoPrefs1BasedCoords],
            ]],
            [" Save Config", " ", DoPrefsSave],
        ]])

    return menubar
