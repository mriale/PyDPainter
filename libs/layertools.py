#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import re

from libs.toolbar import *
from libs.toolreq import *
from libs.gadget import *
from libs.tiptext import *

config = None

palette_key_labels = ["Global (same for all)", "None ({}-{})", "Local ({}-{})"]

# Sprite columns in layertools.png.  Column 0 is a normal, enabled button;
# the layer toolbar is drawn with draw_state_zero so it is visible.
STATE_NORMAL = 0
STATE_PRESSED = 1
STATE_DISABLED = 2

class LayerToolAction(Action):
    def get_tip(self):
        if self.gadget.id in tiptext:
            return tiptext[self.gadget.id]
        else:
            return [self.gadget.id]

    def current_layer(self):
        return config.layers.get()

    def current_user_layer(self):
        layer = self.current_layer()
        if layer is not None and layer.kind == "user":
            return layer
        return None

    def store_undo(self, structural=False):
        config.save_undo(structural=structural)
        config.doKeyAction()

def refresh_layer_gadgets(minitoolbar=None):
    if minitoolbar is None:
        minitoolbar = config.layertoolbar

    layers = config.layers
    current_name = layers.current_layer_name

    opacity = 0
    opacity_enabled = False

    for i in range(0, 11):
        layer_name = layers.get_priority_name(i)
        layer = layers.get(layer_name) if layer_name is not None else None
        is_current = layer_name is not None and layer_name == current_name

        if layer is None:
            layer_select = 3 if is_current else 2
            layer_visible = 5 if is_current else 4
        elif i == 10: #stencil
            # The stencil's own enable flag is authoritative.
            layer.visible = config.stencil.enable

            if config.stencil.mask is None:
                layer_select = 2
            else:
                layer_select = 0
            if config.stencil.enable:
                layer_visible = 0
            else:
                if config.stencil.mask is None:
                    layer_visible = 4
                else:
                    layer_visible = 2
        else:
            layer_select = 1 if is_current else 0
            if layer.visible:
                layer_visible = 1 if is_current else 0
            else:
                layer_visible = 3 if is_current else 2
            if is_current:
                opacity = layer.opacity
                opacity_enabled = layer.kind in ("canvas", "user", "background") and \
                                  isinstance(layer.image, pygame.Surface)

        layer_gadget = minitoolbar.tool_id(f"layer{i}")
        if layer_gadget is not None and layer_gadget.state != layer_select:
            layer_gadget.state = layer_select
            layer_gadget.need_redraw = True

        visible_gadget = minitoolbar.tool_id(f"visible{i}")
        if visible_gadget is not None and visible_gadget.state != layer_visible:
            visible_gadget.state = layer_visible
            visible_gadget.need_redraw = True

    current = layers.get()
    is_user = current is not None and current.kind == "user"
    free_slot = config.first_free_layer_slot() is not None
    can_merge = False
    if is_user:
        for other in layers.sorted_layers():
            if other.priority >= current.priority:
                break
            if isinstance(other.image, pygame.Surface):
                can_merge = True

    tool_enabled = {
        "merge": can_merge,
        "clone": is_user and free_slot,
        "movelayer": is_user,
        "addlayer": free_slot,
        "dellayer": is_user,
    }
    for tname, enabled in tool_enabled.items():
        gadget = minitoolbar.tool_id(tname)
        state = STATE_NORMAL if enabled else STATE_DISABLED
        if gadget is not None and gadget.state != state:
            gadget.state = state
            gadget.need_redraw = True

    opacity_gadget = minitoolbar.tool_id("opacityslider")
    if opacity_gadget is not None:
        opacity_gadget.enabled = opacity_enabled
        opacity_gadget.need_redraw = True
        opacity_gadget.value = max(0, min(15, int(round(opacity / 17.0))))

class DoVisible(LayerToolAction):
    """
    Change visiblity
    """
    def selected(self, attrs):
        self.clicked(attrs)

    def deselected(self, attrs):
        self.clicked(attrs)

    def clicked(self, attrs):
        gadget_num = int(self.gadget.id[7:])
        layer_name = config.layers.get_priority_name(gadget_num)
        if gadget_num == 10:
            config.stencil.enable = not config.stencil.enable
            config.set_layer_visible("fg", config.stencil.enable)
        elif layer_name is not None:
            layer = config.layers.get(layer_name)
            # Visibility belongs to the layer, not to one animation frame.
            config.set_layer_visible(layer_name, not layer.visible)
        else:
            return
        self.store_undo()

class DoLayer(LayerToolAction):
    """
    Change current layer
    """
    def selected(self, attrs):
        self.clicked(attrs)

    def deselected(self, attrs):
        # Layer rows use more than two visual states (visible, hidden, empty),
        # so a click can arrive as a deselection.  Treat both as a click.
        self.clicked(attrs)

    def clicked(self, attrs):
        gadget_num = int(self.gadget.id[5:])
        layer_name = config.layers.get_priority_name(gadget_num)

        # Drop any brush preview left on the previously selected layer before
        # switching, and give the new layer a fresh preview baseline.
        config.clear_pixel_draw_canvas()

        if layer_name is None:
            if 2 <= gadget_num <= 9 and config.layer_slot_is_free(gadget_num):
                # Selecting an empty user slot creates it, like Deluxe Paint.
                config.stash_structural()
                layer_name = config.add_layer(priority=gadget_num)
                if layer_name is not None:
                    config.save_undo(structural=True)
            elif gadget_num == 10 and not config.layers.has_key("fg"):
                config.layers.set("fg", config.stencil, priority=10,
                                  visible=config.stencil.enable, kind="stencil")
                layer_name = "fg"

        if layer_name is not None:
            if config.select_layer(layer_name):
                config.reset_draw_baseline()

class DoMerge(LayerToolAction):
    """
    Merge layer down
    """
    def selected(self, attrs):
        layer = self.current_user_layer()
        if layer is None:
            return
        config.stash_structural()
        if config.merge_layer_down(config.layers.current_layer_name):
            self.store_undo(structural=True)

class DoClone(LayerToolAction):
    """
    Clone layer to another slot
    """
    def selected(self, attrs):
        if self.current_user_layer() is None:
            return
        if config.first_free_layer_slot() is None:
            return
        config.stash_structural()
        if config.clone_layer() is not None:
            self.store_undo(structural=True)

class DoAddLayer(LayerToolAction):
    """
    Add a new empty layer
    """
    def selected(self, attrs):
        slot = None
        # If an empty slot is selected, add the layer there.
        match = re.fullmatch(r"layer([2-9])", config.layers.current_layer_name or "")
        if match is not None:
            slot = int(match.group(1))
            if not config.layer_slot_is_free(slot):
                slot = None
        if slot is None:
            slot = config.first_free_layer_slot()
        if slot is None:
            return

        config.stash_structural()
        if config.add_layer(priority=slot) is not None:
            self.store_undo(structural=True)

class DoDelLayer(LayerToolAction):
    """
    Delete the current layer
    """
    def selected(self, attrs):
        layer = self.current_user_layer()
        if layer is None:
            return
        config.stash_structural()
        if config.delete_layer(config.layers.current_layer_name):
            self.store_undo(structural=True)

class DoMoveLayer(LayerToolAction):
    """
    Move the current layer up or down.

    The toolbar button shows an up arrow in its top half and a down arrow in
    its bottom half; clicking a half moves the layer that way.  Right-click
    still moves down, and the menu action always moves up.
    """
    def selected(self, attrs):
        layer = self.current_user_layer()
        if layer is None:
            return
        if "top_half" in attrs:
            direction = 1 if attrs["top_half"] else -1
        elif attrs.get("rightclick"):
            direction = -1
        else:
            direction = 1
        target = layer.priority + direction
        if target < 2 or target > 9:
            return
        name = layer.parent.get_priority_name(layer.priority)
        config.stash_structural()
        if config.move_layer(name, target):
            self.store_undo(structural=True)


class LayerToolbar(Toolbar):
    def is_inside(self, coords):
        if not "screenrect" in dir(self):
            return False
        if not self.visible:
            return False

        gx,gy,gw,gh = self.screenrect
        x, y = coords
        if x >= gx and y >= gy and x <= gx+gw and y <= gy+gh:
            return True
        else:
            return False

def init_layertoolbar(config_in):
    global config
    config = config_in

    scaleX = config.fontx // 8
    scaleY = config.fonty // 12
    scaledown = 4 // min(scaleX,scaleY)
    minitools_image = imgload('layertools.png', scaleX=scaleX, scaleY=scaleY, scaledown=scaledown)
    numtools=16
    numsubtools=6
    h = minitools_image.get_height()
    w = minitools_image.get_width() // numsubtools
    mt_width = w
    mt_height = config.screen_height - config.menubar.rect[3]
    minitoolbar_canvas = pygame.Surface((mt_width,mt_height),0)

    minitoolbar = LayerToolbar(minitoolbar_canvas, config.cursor, (0,0,mt_width,mt_height), minitools_image, width=numsubtools, tip_event=config.TOOLTIPEVENT)
    minitoolbar.tip_quadrant = 2 #tip on right
    # Column 0 is the normal (unpressed) button state for this panel.
    minitoolbar.draw_state_zero = True

    minitoolbar.add_grid((9*scaleX,0, w-9*scaleX,h), 1, numtools, attr_list=[
        ["merge",      ToolGadget.TT_TOGGLE, "", DoMerge],
        ["clone",      ToolGadget.TT_TOGGLE, "", DoClone],
        ["addlayer",   ToolGadget.TT_TOGGLE, "", DoAddLayer],
        ["dellayer",   ToolGadget.TT_TOGGLE, "", DoDelLayer],
        ["movelayer",  ToolGadget.TT_TOGGLE, "", DoMoveLayer],
        ["visible10",  ToolGadget.TT_TOGGLE, "", DoVisible],
        ["visible9",   ToolGadget.TT_TOGGLE, "", DoVisible],
        ["visible8",   ToolGadget.TT_TOGGLE, "", DoVisible],
        ["visible7",   ToolGadget.TT_TOGGLE, "", DoVisible],
        ["visible6",   ToolGadget.TT_TOGGLE, "", DoVisible],
        ["visible5",   ToolGadget.TT_TOGGLE, "", DoVisible],
        ["visible4",   ToolGadget.TT_TOGGLE, "", DoVisible],
        ["visible3",   ToolGadget.TT_TOGGLE, "", DoVisible],
        ["visible2",   ToolGadget.TT_TOGGLE, "", DoVisible],
        ["visible1",   ToolGadget.TT_TOGGLE, "", DoVisible],
        ["visible0",   ToolGadget.TT_TOGGLE, "", DoVisible],
    ])

    minitoolbar.add_grid((0,5*11*scaleY, 9*scaleX,h-5*11*scaleY), 1, 11, attr_list=[
        ["layer10",  ToolGadget.TT_TOGGLE, "", DoLayer],
        ["layer9",   ToolGadget.TT_TOGGLE, "", DoLayer],
        ["layer8",   ToolGadget.TT_TOGGLE, "", DoLayer],
        ["layer7",   ToolGadget.TT_TOGGLE, "", DoLayer],
        ["layer6",   ToolGadget.TT_TOGGLE, "", DoLayer],
        ["layer5",   ToolGadget.TT_TOGGLE, "", DoLayer],
        ["layer4",   ToolGadget.TT_TOGGLE, "", DoLayer],
        ["layer3",   ToolGadget.TT_TOGGLE, "", DoLayer],
        ["layer2",   ToolGadget.TT_TOGGLE, "", DoLayer],
        ["layer1",   ToolGadget.TT_TOGGLE, "", DoLayer],
        ["layer0",   ToolGadget.TT_TOGGLE, "", DoLayer],
    ])

    minitoolbar.tool_id("merge").has_subtool = False
    minitoolbar.tool_id("clone").has_subtool = False
    minitoolbar.tool_id("addlayer").has_subtool = False
    minitoolbar.tool_id("dellayer").has_subtool = False
    minitoolbar.tool_id("movelayer").has_subtool = False
    for i in range(0,11):
        #readjust size of tools to not overlap
        lrect = list(minitoolbar.tool_id(f"layer{i}").rect)
        lrect[3] -= scaleY
        minitoolbar.tool_id(f"layer{i}").rect = list(lrect)
        lrect = list(minitoolbar.tool_id(f"visible{i}").rect)
        lrect[3] -= scaleY
        minitoolbar.tool_id(f"visible{i}").rect = list(lrect)

    #Add frame slider to toolbar
    gx,gy,gw,gh = minitoolbar.tools[0].rect
    gx = scaleX
    gy = scaleY
    gw = scaleX*8
    gh = scaleY * (5) * 11
    sliderg = Gadget(Gadget.TYPE_PROP_VERT, "-", (gx,gy,gw,gh), maxvalue=16, id="opacityslider")
    minitoolbar.tools.append(sliderg)
    minitoolbar.add_coords(sliderg)

    minitoolbar.visible = False

    return minitoolbar

def draw_layertoolbar(screen_rgb, rect):
    scaleX = config.fontx // 8
    scaleY = config.fonty // 12

    if config.layertoolbar.visible:
        refresh_layer_gadgets()
        pygame.draw.rect(screen_rgb, (160,160,160), rect)
        pygame.draw.rect(screen_rgb, (0,0,0), (rect[2]-scaleX,rect[1],scaleX,rect[3]))
        config.layertoolbar.tool_id("opacityslider").need_redraw = True
        for i in range(0,11):
            config.layertoolbar.tool_id(f"layer{i}").need_redraw = True
            config.layertoolbar.tool_id(f"visible{i}").need_redraw = True

        screen_rgb.set_clip(rect)
        config.layertoolbar.draw(screen_rgb, font=config.font, offset=(rect[0],rect[1]))
        screen_rgb.set_clip(None)

        config.layertoolbar.screenrect = list(rect)
