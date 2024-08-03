#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

from libs.toolbar import *
from libs.toolreq import *
from libs.gadget import *
from libs.tiptext import *

config = None

palette_key_labels = ["Global (same for all)", "None ({}-{})", "Local ({}-{})"]

class LayerToolAction(Action):
    def get_tip(self):
        if self.gadget.id in tiptext:
            return tiptext[self.gadget.id]
        else:
            return [self.gadget.id]

def refresh_layer_gadgets(minitoolbar=None):
    if minitoolbar is None:
        minitoolbar = config.layertoolbar

    # Backup tools states
    tool_names = ["merge", "clone", "movelayer", "addlayer", "dellayer"]
    all_prev_tools_state = {}
    all_tools_state = {}
    for tname in tool_names:
        state = minitoolbar.tool_id(tname).state
        all_prev_tools_state[tname] = state
        all_tools_state[tname] = state

    tools_state = all_tools_state["dellayer"]

    opacity = 0
    special_layer = False

    for i in range(0,11):
        layer_name = config.layers.get_priority_name(i)
        if config.layers.has_key(layer_name):
            layer = config.layers.get(layer_name)
        else:
            layer = None
            layer_name = f"layer{i}"

        prev_layer_select = minitoolbar.tool_id(f"layer{i}").state
        prev_layer_visible = minitoolbar.tool_id(f"visible{i}").state

        if layer_name == config.layers.current_layer_name:
            if i == 0 or i == 10:
                special_layer = True
            if layer is None:
                layer_select = 3
                layer_visible = 5
                tools_state = 2
            elif layer.visible:
                layer_select = 1
                layer_visible = 1
                tools_state = 0
                opacity = layer.opacity
            else:
                layer_select = 1
                layer_visible = 3
                tools_state = 0
                opacity = layer.opacity
        else:
            if layer is None:
                layer_select = 2
                layer_visible = 4
            elif layer.visible:
                layer_select = 0
                layer_visible = 0
            else:
                layer_select = 0
                layer_visible = 2
                
        if prev_layer_select != layer_select:
            minitoolbar.tool_id(f"layer{i}").state = layer_select
            minitoolbar.tool_id(f"layer{i}").need_redraw = True

        if prev_layer_visible != layer_visible:
            minitoolbar.tool_id(f"visible{i}").state = layer_visible
            minitoolbar.tool_id(f"visible{i}").need_redraw = True

    if special_layer:
        all_tools_state["merge"] = 2
        all_tools_state["clone"] = 2
        all_tools_state["movelayer"] = 2
    else:
        all_tools_state["merge"] = tools_state
        all_tools_state["clone"] = tools_state
        all_tools_state["movelayer"] = tools_state
    
    all_tools_state["addlayer"] = (tools_state+2)%4
    all_tools_state["dellayer"] = tools_state
    minitoolbar.tool_id("opacityslider").enabled = not(tools_state & 2)
    minitoolbar.tool_id("opacityslider").need_redraw = True
    minitoolbar.tool_id("opacityslider").value = opacity // 16

    # Redraw tools only if needed
    for tname in tool_names:
        if all_prev_tools_state[tname] != all_tools_state[tname]:
            minitoolbar.tool_id(tname).state = all_tools_state[tname]
            minitoolbar.tool_id(tname).need_redraw = True

class DoVisible(LayerToolAction):
    """
    Change visiblity
    """
    def selected(self, attrs):
        self.clicked(attrs)

    def deselected(self, attrs):
        self.clicked(attrs)

    def clicked(self, attrs):
        print(attrs)
        print(f"{self.gadget.id=}")
        print(f"{self.gadget.state=}")
        gadget_num = int(self.gadget.id[7:])
        print(f"{gadget_num=}")
        layer_name = config.layers.get_priority_name(gadget_num)
        if config.layers.has_key(layer_name):
            layer = config.layers.get(layer_name)
            layer.visible = not layer.visible

class DoLayer(LayerToolAction):
    """
    Change current layer
    """
    def selected(self, attrs):
        self.clicked(attrs)

    def deselected(self, attrs):
        self.clicked(attrs)

    def clicked(self, attrs):
        print(attrs)
        print(f"{self.gadget.id=}")
        print(f"{self.gadget.state=}")
        gadget_num = int(self.gadget.id[5:])
        print(f"{gadget_num=}")
        layer_name = config.layers.get_priority_name(gadget_num)
        if not config.layers.has_key(layer_name):
            layer_name = f"layer{gadget_num}"
        config.layers.current_layer_name = layer_name

class DoMerge(LayerToolAction):
    """
    Merge layer down
    """
    def selected(self, attrs):
        print("DoMerge")

class DoClone(LayerToolAction):
    """
    Clone layer to another slot
    """
    def selected(self, attrs):
        print("DoClone")

class DoAddLayer(LayerToolAction):
    """
    Clone layer to another slot
    """
    def selected(self, attrs):
        print("DoAddLayer")

class DoDelLayer(LayerToolAction):
    """
    Clone layer to another slot
    """
    def selected(self, attrs):
        print("DoDelLayer")

class DoMoveLayer(LayerToolAction):
    """
    Clone layer to another slot
    """
    def selected(self, attrs):
        print("DoMoveLayer")


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
        minitoolbar.tool_id(f"layer{i}").has_subtool = False
        minitoolbar.tool_id(f"layer{i}").state = 2
        minitoolbar.tool_id(f"visible{i}").has_subtool = False
        minitoolbar.tool_id(f"visible{i}").state = 4

    #Add frame slider to toolbar
    gx,gy,gw,gh = minitoolbar.tools[0].rect
    gx = scaleX
    gw = scaleX*8
    gh = scaleY * (5) * 11
    sliderg = Gadget(Gadget.TYPE_PROP_VERT, "-", (gx,gy,gw,gh), maxvalue=16, id="opacityslider")
    minitoolbar.tools.append(sliderg)
    minitoolbar.add_coords(sliderg)

    minitoolbar.visible = False

    return minitoolbar

def draw_layertoolbar(screen_rgb):
    scaleX = config.fontx // 8
    scaleY = config.fonty // 12

    #if config.anim.num_frames == 1:
    #    config.layertoolbar.visible = False
    if config.layertoolbar.visible:
        refresh_layer_gadgets()

        #atbh = config.menubar.rect[3]
        #atby = config.screen_height - atbh
        atby = config.menubar.rect[3]
        atbh = config.screen_height - atby
        atbw = 23 * scaleX
        pygame.draw.rect(screen_rgb, (119,119,119), (atbw+1*scaleX,atby,scaleX,atbh))
        pygame.draw.rect(screen_rgb, (0,0,0), (atbw+2*scaleX,atby,scaleX,atbh))
        pygame.draw.rect(screen_rgb, (160,160,160), (0,atby,atbw+scaleX,atbh))
        config.layertoolbar.tool_id("opacityslider").need_redraw = True
        for i in range(1,10):
            config.layertoolbar.tool_id(f"layer{i}").need_redraw = True

        screen_rgb.set_clip((0,atby,atbw,atbh))
        config.layertoolbar.draw(screen_rgb, font=config.font, offset=(0,atby))
        screen_rgb.set_clip(None)

        config.layertoolbar.screenrect = (0,atby,atbw+2*scaleX,atbh)

