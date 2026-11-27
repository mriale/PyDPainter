#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""Tests for deterministic color-cycle rendering with a global palette."""

import os
import tempfile
import types
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import numpy as np

from libs import animation, cyclerender, picio
from libs.colorrange import colorrange

import contextlib
with contextlib.redirect_stdout(None):
    import pygame


class CycleConfig:
    """Minimal config stand-in for cycle rendering and GIF export."""

    MODE_EXTRA_HALFBRIGHT = 0x80
    LAYER_INDICATORX = 0

    def __init__(self, ranges, display_mode=0, width=8, height=4):
        self.cranges = ranges
        self.display_mode = display_mode
        self.pal = [(i, (i * 3) % 256, (i * 7) % 256) for i in range(256)]
        self.truepal = [tuple(color) for color in self.pal]
        self.loadpal = [tuple(color) for color in self.pal]
        self.pixel_width = width
        self.pixel_height = height

        self.surface = pygame.Surface((width, height), 0, 8)
        self.surface.set_palette(self.pal)
        pixels = pygame.surfarray.pixels2d(self.surface)
        pixels[:] = (np.arange(width * height) % 256).astype(np.uint8).reshape(
            (width, height))
        del pixels
        self.layers = types.SimpleNamespace(
            get_flattened=lambda exclude=[]: self.surface)

    def _resize_surface(self, image, width, height, resize):
        scaled = pygame.Surface((width, height), 0, 8)
        scaled.set_palette(self.pal)
        pygame.transform.scale(image, (width, height), scaled)
        return scaled

    def new_layer_stack(self, canvas):
        return types.SimpleNamespace(
            get_flattened=lambda exclude=[]: canvas)


def base_pixels(cfg):
    pixels = pygame.surfarray.pixels2d(cfg.surface)
    result = np.array(pixels, copy=True)
    del pixels
    return result


def frame_pixels(frame):
    pixels = pygame.surfarray.pixels2d(frame.image)
    result = np.array(pixels, copy=True)
    del pixels
    return result


def gif_flags(data):
    """Return (global flags, per-image packed flags) from a GIF byte string."""
    assert data[:6] == b"GIF89a"
    global_flags = data[10]
    pos = 13
    if global_flags & 0x80:
        pos += 3 * (2 ** ((global_flags & 0x07) + 1))
    image_flags = []
    while pos < len(data):
        block = data[pos]
        if block == 0x3B:
            break
        if block == 0x21:  # extension: label followed by sub-blocks
            pos += 2
            while data[pos] != 0:
                pos += 1 + data[pos]
            pos += 1
        elif block == 0x2C:  # image descriptor
            packed = data[pos + 9]
            image_flags.append(packed)
            pos += 10
            if packed & 0x80:
                pos += 3 * (2 ** ((packed & 0x07) + 1))
            pos += 1  # LZW minimum code size
            while data[pos] != 0:
                pos += 1 + data[pos]
            pos += 1
        else:
            raise AssertionError("unknown GIF block 0x%02x at %d" % (block, pos))
    return global_flags, image_flags


class CycleIndexLutTest(unittest.TestCase):
    def assert_lut_matches_palette(self, cfg, plan, frame_index):
        rotated_pal, _ = cyclerender.cycle_palette_at(cfg, plan, frame_index)
        lut = cyclerender.cycle_index_lut(cfg, plan, frame_index)
        for old_index, color in enumerate(rotated_pal):
            self.assertEqual(tuple(cfg.pal[int(lut[old_index])]),
                             tuple(color),
                             "frame %d, palette index %d" % (frame_index, old_index))

    def test_frame_zero_is_identity(self):
        cfg = CycleConfig([colorrange(5120, 1, 3, 7)])
        plan = cyclerender.compute_cycle_plan(cfg)
        np.testing.assert_array_equal(cyclerender.cycle_index_lut(cfg, plan, 0),
                                      np.arange(256, dtype=np.uint8))

    def test_forward_direction(self):
        cfg = CycleConfig([colorrange(5120, 1, 3, 7)])
        plan = cyclerender.compute_cycle_plan(cfg)
        lut = cyclerender.cycle_index_lut(cfg, plan, 1)
        self.assertEqual(int(lut[3]), 7)
        self.assertEqual(int(lut[7]), 6)

    def test_reverse_direction(self):
        cfg = CycleConfig([colorrange(5120, 3, 3, 7)])
        plan = cyclerender.compute_cycle_plan(cfg)
        lut = cyclerender.cycle_index_lut(cfg, plan, 1)
        self.assertEqual(int(lut[3]), 4)
        self.assertEqual(int(lut[7]), 3)

    def test_forward_and_slow_ranges(self):
        cfg = CycleConfig([colorrange(5120, 1, 3, 7),
                           colorrange(2560, 1, 10, 13)])
        plan = cyclerender.compute_cycle_plan(cfg)
        self.assertEqual(plan["fps"], [1, 2])
        for frame_index in range(6):
            self.assert_lut_matches_palette(cfg, plan, frame_index)

    def test_reverse_and_halfbright(self):
        cfg = CycleConfig([colorrange(5120, 3, 3, 7)],
                          display_mode=CycleConfig.MODE_EXTRA_HALFBRIGHT)
        plan = cyclerender.compute_cycle_plan(cfg)
        for frame_index in range(5):
            self.assert_lut_matches_palette(cfg, plan, frame_index)


class CycleFrameRenderTest(unittest.TestCase):
    def setUp(self):
        self.cfg = CycleConfig([colorrange(5120, 1, 3, 7),
                                colorrange(2560, 1, 10, 13)])
        animation.animation_set_config(self.cfg)
        self.plan = cyclerender.compute_cycle_plan(self.cfg)
        self.base = base_pixels(self.cfg)
        self.frames, self.w, self.h = animation._build_cycle_frames(
            self.cfg, num_frames=4, delay=6)

    def test_frames_share_base_palette(self):
        for frame in self.frames:
            self.assertEqual(frame.pal, self.cfg.pal)
            self.assertEqual(frame.truepal, self.cfg.truepal)
            self.assertEqual(frame.loadpal, self.cfg.loadpal)

    def test_frames_remap_indices(self):
        np.testing.assert_array_equal(frame_pixels(self.frames[0]), self.base)
        for i, frame in enumerate(self.frames[1:], start=1):
            lut = cyclerender.cycle_index_lut(self.cfg, self.plan, i)
            np.testing.assert_array_equal(frame_pixels(frame), lut[self.base])
            self.assertFalse(frame.is_pal_key)

    def test_rendered_anim_uses_global_palette(self):
        anim = animation.build_cycle_animation(self.cfg, num_frames=4, delay=6)
        self.assertTrue(anim.global_palette)

    def test_cycle_gif_has_no_local_palettes(self):
        anim = animation.build_cycle_animation(self.cfg, num_frames=4, delay=6)
        save_config = types.SimpleNamespace(
            pixel_width=self.w, pixel_height=self.h,
            pal=self.cfg.pal, truepal=self.cfg.truepal, anim=anim)

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "cycle.gif")
            picio.save_gif_anim(filename, save_config)
            with open(filename, "rb") as f:
                data = f.read()

        global_flags, image_flags = gif_flags(data)
        self.assertTrue(global_flags & 0x80)
        self.assertEqual(len(image_flags), 4)
        self.assertTrue(all(not flags & 0x80 for flags in image_flags))


if __name__ == "__main__":
    unittest.main()
