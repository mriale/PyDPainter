#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""Tests for the dependency-free indexed PNG writer and its picio hooks."""

import io
import os
import struct
import tempfile
import unittest
import zipfile
import zlib

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from libs.pngwriter import encode_indexed_png, surface_png_bytes
from libs.colorrange import colorrange
from libs import picio

import contextlib
with contextlib.redirect_stdout(None):
    import pygame


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def chunks(data):
    """Yield (tag, payload) for each PNG chunk after the signature."""
    assert data[:8] == PNG_SIGNATURE
    pos = 8
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        assert crc == zlib.crc32(tag + payload) & 0xFFFFFFFF
        yield tag, payload
        pos += 12 + length


def iff_chunks(data):
    """Yield (tag, payload) for each chunk of an ILBM file."""
    assert data[:4] == b"FORM" and data[8:12] == b"ILBM"
    pos = 12
    while pos < len(data):
        tag = data[pos:pos + 4]
        length = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        yield tag, data[pos + 8:pos + 8 + length]
        pos += 8 + length + (length & 1)


class IndexedPNGEncoderTest(unittest.TestCase):
    def test_ihdr_palette_and_scanlines(self):
        palette = [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
        indices = bytes([0, 1, 2, 2, 1, 0])
        data = encode_indexed_png(3, 2, indices, palette)
        parts = list(chunks(data))

        self.assertEqual(parts[0][0], b"IHDR")
        self.assertEqual(struct.unpack(">IIBBBBB", parts[0][1]),
                         (3, 2, 8, 3, 0, 0, 0))
        self.assertEqual(parts[1][0], b"PLTE")
        self.assertEqual(parts[1][1], bytes([1, 2, 3, 4, 5, 6, 7, 8, 9]))
        self.assertEqual([tag for tag, _ in parts],
                         [b"IHDR", b"PLTE", b"IDAT", b"IEND"])

        raw = zlib.decompress(parts[2][1])
        self.assertEqual(raw, b"\x00\x00\x01\x02\x00\x02\x01\x00")

    def test_transparency(self):
        palette = [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
        data = encode_indexed_png(1, 1, b"\x00", palette,
                                  transparent_index=1)
        trns = dict(chunks(data)).get(b"tRNS")
        self.assertEqual(trns, b"\xff\x00")

        alpha_palette = [(1, 2, 3, 255), (4, 5, 6, 128)]
        data = encode_indexed_png(1, 1, b"\x01", alpha_palette)
        self.assertEqual(dict(chunks(data))[b"tRNS"], b"\xff\x80")

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            encode_indexed_png(2, 2, b"\x00", [(0, 0, 0)])
        with self.assertRaises(ValueError):
            encode_indexed_png(2, 2, b"\x01\x01\x01\x01", [(0, 0, 0)])


class SurfaceIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.palette = [(i, 255 - i, (i * 7) % 256) for i in range(256)]
        self.surface = pygame.Surface((5, 3), 0, 8)
        self.surface.set_palette(self.palette)
        for y in range(3):
            for x in range(5):
                self.surface.set_at((x, y), (x + y * 5) % 256)

    def test_surface_roundtrip(self):
        data = surface_png_bytes(self.surface)
        self.assertEqual(dict(chunks(data))[b"IHDR"][9], 3)  # color type

        loaded = pygame.image.load(io.BytesIO(data), "roundtrip.png")
        self.assertEqual(loaded.get_bytesize(), 1)
        self.assertEqual(loaded.get_size(), (5, 3))
        self.assertEqual([tuple(c[:3]) for c in loaded.get_palette()],
                         self.palette)
        self.assertEqual(pygame.image.tobytes(loaded, "P"),
                         pygame.image.tobytes(self.surface, "P"))

    def test_save_pic_writes_indexed_png(self):
        surface = self.surface

        class Config:
            pixel_canvas = surface

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "pic.png")
            self.assertTrue(picio.save_pic(filename, Config()))
            with open(filename, "rb") as f:
                data = f.read()
        self.assertEqual(dict(chunks(data))[b"IHDR"][9], 3)
        self.assertEqual(dict(chunks(data))[b"PLTE"],
                         bytes(c for color in self.palette for c in color[:3]))

    def test_save_ora_writes_indexed_pngs(self):
        surface = self.surface

        class Layer:
            image = surface
            visible = True
            opacity = 255
            kind = "canvas"
            indicator = ""
            transparent_index = 0

        class Layers:
            def names(self):
                return ["canvas"]

            def get(self, name):
                return Layer()

            def get_flattened(self, exclude=None):
                return surface

        class Config:
            pixel_width, pixel_height = surface.get_size()
            layers = Layers()

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "pic.ora")
            picio.save_ora(filename, Config())
            with zipfile.ZipFile(filename) as archive:
                layer_png = archive.read("data/layer0.png")
                merged_png = archive.read("mergedimage.png")
                for data in (layer_png, merged_png):
                    self.assertEqual(dict(chunks(data))[b"IHDR"][9], 3)
                    self.assertEqual(dict(chunks(data))[b"PLTE"],
                                     bytes(c for color in self.palette
                                           for c in color[:3]))
                # Layers must advertise index 0 as transparent; the flattened
                # preview stays opaque.
                self.assertEqual(dict(chunks(layer_png))[b"tRNS"], b"\x00")
                self.assertNotIn(b"tRNS", dict(chunks(merged_png)))

            class LoadConfig:
                pixel_width, pixel_height = surface.get_size()
                pal = self.palette
                truepal = self.palette

            merged = picio.load_ora(filename, LoadConfig())
            self.assertEqual(pygame.image.tobytes(merged, "P"),
                             pygame.image.tobytes(surface, "P"))

    def test_ora_iffinfo_metadata_roundtrip(self):
        surface = self.surface
        pal32 = [(i * 4, 255 - i * 4, (i * 7) % 256) for i in range(32)]
        crange = colorrange(7, 3, 4, 11)

        class Layer:
            image = surface
            visible = True
            opacity = 255
            kind = "canvas"
            indicator = ""
            transparent_index = 0

        class Layers:
            def names(self):
                return ["canvas"]

            def get(self, name):
                return Layer()

            def get_flattened(self, exclude=None):
                return surface

        class Config:
            pixel_width, pixel_height = surface.get_size()
            screen_width, screen_height = 400, 300
            layers = Layers()
            pal = pal32
            truepal = pal32
            color_depth = 16
            NUM_COLORS = 32
            display_mode = 0x00011000
            cranges = [crange] + [colorrange() for _ in range(5)]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "pic.ora")
            picio.save_ora(filename, Config())
            with zipfile.ZipFile(filename) as archive:
                parts = list(iff_chunks(archive.read("iffinfo")))
            meta = dict(parts)
            crng_payload = next(p for tag, p in parts if tag == b"CRNG")

            self.assertEqual(struct.unpack(">HHhhBBBBHBBhh", meta[b"BMHD"])[4], 5)
            self.assertEqual(len(meta[b"CMAP"]), 32 * 3)
            self.assertEqual(struct.unpack(">I", meta[b"CAMG"])[0],
                             Config.display_mode)
            self.assertEqual(struct.unpack(">HHH", meta[b"PDPD"][4:]),
                             (1, 16, 32))
            self.assertEqual(struct.unpack(">HHHBB", crng_payload),
                             (0, 7, 3, 4, 11))

            class LoadConfig:
                pixel_width, pixel_height = surface.get_size()
                pal = self.palette
                truepal = self.palette

                def unique_palette(self, pal):
                    return list(pal)

                def guess_color_depth(self, pal):
                    return 256

            cfg = LoadConfig()
            picio.load_ora(filename, cfg)
            self.assertEqual(len(cfg.pal), 32)
            self.assertEqual(cfg.truepal, pal32)
            self.assertEqual(cfg.color_depth, 16)
            self.assertEqual(cfg.NUM_COLORS, 32)
            self.assertEqual(cfg.display_mode, Config.display_mode)
            self.assertEqual((cfg.screen_width, cfg.screen_height), (400, 300))
            self.assertEqual(cfg.cranges[0].rate, 7)
            self.assertTrue(cfg.ora_iffinfo_loaded)


if __name__ == "__main__":
    unittest.main()
