#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

"""Render a color-cycling picture into a sequence of palettes.

Color cycling in the editor is driven by pygame timers and wall-clock time,
which makes it unsuitable for generating reproducible frames.  This module
reimplements the exact same palette rotation as ``colorrange.apply_to_pal``
but with an explicit step count, so a picture can be turned into an animation
or an animated GIF deterministically.
"""

import contextlib
import math

with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

# Guard against cycles whose least-common-multiple would be enormous.
CYCLE_MAX_FRAMES = 256


def active_cycle_ranges(cfg):
    """Return color ranges that are active and can actually rotate."""
    result = []
    for crange in cfg.cranges:
        if crange.is_active() and crange.rate > 0 and crange.low < crange.high:
            result.append(crange)
    return result


def compute_cycle_plan(cfg, max_frames=CYCLE_MAX_FRAMES):
    """Describe how to turn the active color ranges into animation frames.

    Returns a dict with:
      ranges - active colorrange objects
      fps    - frames per palette step for each range (keeps relative speeds)
      frames - suggested frame count, capped at ``max_frames``
      period - uncapped cycle length in frames
      delay  - suggested frame delay in 1/60s units
    """
    ranges = active_cycle_ranges(cfg)
    if not ranges:
        return {"ranges": [], "fps": [], "frames": 1, "period": 1, "delay": 6}

    rate_ms = [r.rate_to_milli() for r in ranges]
    base_ms = min(rate_ms)
    # A faster range steps every frame; slower ones step less often so the
    # relative speeds from the live cycling are preserved in the export.
    fps = [max(1, int(round(ms / base_ms))) for ms in rate_ms]

    period = 1
    for r, f in zip(ranges, fps):
        cycle_len = (r.high - r.low + 1) * f
        period = period * cycle_len // math.gcd(period, cycle_len)

    frames = min(period, max_frames)
    delay = max(1, int(round(base_ms * 60 / 1000)))
    return {"ranges": ranges, "fps": fps, "frames": frames,
            "period": period, "delay": delay}


def step_palette(pal, crange, steps=1, halfbright=False):
    """Rotate ``pal`` by ``steps`` for ``crange`` in place.

    This mirrors ``colorrange.apply_to_pal`` without reading the clock, so the
    same step always produces the same palette.
    """
    if steps <= 0:
        return
    low, high = crange.low, crange.high
    for _ in range(steps):
        if crange.reverse:
            lowcol = pal[low]
            del pal[low]
            pal.insert(high, lowcol)
            if halfbright and low + 32 < len(pal):
                lowcol = pal[low + 32]
                del pal[low + 32]
                pal.insert(high + 32, lowcol)
        else:
            highcol = pal[high]
            del pal[high]
            pal.insert(low, highcol)
            if halfbright and high + 32 < len(pal):
                highcol = pal[high + 32]
                del pal[high + 32]
                pal.insert(low + 32, highcol)


def cycle_palette_at(cfg, plan, frame_index, base_pal=None, base_truepal=None):
    """Return ``(pal, truepal)`` rotated to ``frame_index`` of ``plan``."""
    if base_pal is None:
        base_pal = list(cfg.pal)
    if base_truepal is None:
        base_truepal = list(cfg.truepal)
    pal = list(base_pal)
    truepal = list(base_truepal)
    halfbright = bool(cfg.display_mode & cfg.MODE_EXTRA_HALFBRIGHT)
    for crange, f in zip(plan["ranges"], plan["fps"]):
        steps = frame_index // f
        step_palette(pal, crange, steps, halfbright)
        step_palette(truepal, crange, steps, halfbright)
    return pal, truepal


def cycle_settings_req(screen, cfg, plan, show_scale=True):
    """Ask for cycle settings.

    Returns ``(frames, delay, scale)`` when ``show_scale`` is True, otherwise
    ``(frames, delay)``.  Returns None if the requestor was canceled.
    """
    from libs.gadget import str2req, Gadget

    prr = cfg.pixel_req_rect
    prc = cfg.pixel_req_canvas.copy()
    oldcursor = cfg.cursor.shape
    cfg.cursor.shape = cfg.cursor.NORMAL

    info_ranges = "%d active range%s," % (
        len(plan["ranges"]),
        "" if len(plan["ranges"]) == 1 else "s")
    info_period = "full cycle %d frame%s" % (
        plan["period"],
        "" if plan["period"] == 1 else "s")

    scale_row = "\n Scale: [1x~2x~4x~6x]" if show_scale else ""
    req = str2req("Render Color Cycle", """
 %s
 %s

 Frames: _____
 Delay:  _____ (1/60s)%s

[Cancel][OK]
""" % (info_ranges, info_period, scale_row), "", mouse_pixel_mapper=cfg.get_mouse_pixel_pos, font=cfg.font)
    req.center(screen)
    cfg.pixel_req_rect = req.get_screen_rect()

    framesg = req.gadget_id("9_3")
    framesg.numonly = True
    framesg.value = str(plan["frames"])
    framesg.need_redraw = True

    delayg = req.gadget_id("9_4")
    delayg.numonly = True
    delayg.value = str(plan["delay"])
    delayg.need_redraw = True

    # Latched scale buttons, same style as the file requestor.
    gScale = []
    scale_index = 0
    if show_scale:
        for i, column in enumerate([8, 11, 14, 17]):
            g = req.gadget_id("%d_5" % column)
            g.type = Gadget.TYPE_TOGGLE
            g.value = 1 if i == scale_index else 0
            g.need_redraw = True
            gScale.append(g)

    req.draw(screen)
    cfg.recompose()

    running = 1
    retval = None
    while running:
        event = cfg.xevent.wait()
        gevents = req.process_event(screen, event)

        accepted = False
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = 0
            elif event.key == K_RETURN:
                accepted = not req.has_error()

        for ge in gevents:
            if ge.gadget in gScale:
                scale_index = gScale.index(ge.gadget)
                for i, g in enumerate(gScale):
                    g.value = 1 if i == scale_index else 0
                    g.need_redraw = True
                continue
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK":
                    accepted = not req.has_error()
                elif ge.gadget.label == "Cancel":
                    running = 0

        if accepted and running:
            try:
                frames = int(framesg.value)
                delay = int(delayg.value)
                if frames >= 1 and delay >= 1:
                    frames = min(frames, CYCLE_MAX_FRAMES)
                    if show_scale:
                        retval = (frames, delay, [1, 2, 4, 6][scale_index])
                    else:
                        retval = (frames, delay)
                    running = 0
            except ValueError:
                pass

        if running and not cfg.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN,
                                            MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            cfg.recompose()

    cfg.pixel_req_rect = prr
    cfg.pixel_req_canvas.blit(prc, (0, 0))
    cfg.cursor.shape = oldcursor
    cfg.recompose()
    return retval
