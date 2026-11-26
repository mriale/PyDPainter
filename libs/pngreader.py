#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""Minimal PNG reader for indexed images.

Unlike pygame's general PNG loader, this keeps the raw palette indices even
when several palette entries have identical RGB colors (color cycling relies
on those indices staying distinct).  Files it can't handle -- truecolor,
interlaced or malformed images -- return None so the caller can fall back to
pygame.
"""

import struct
import zlib

from libs.pngwriter import PNG_SIGNATURE

_MAX_DIMENSION = 65536


class IndexedPNG:
    """Decoded indexed PNG: row-major indices, palette and optional tRNS."""
    __slots__ = ("width", "height", "indices", "palette", "transparency")

    def __init__(self, width, height, indices, palette, transparency):
        self.width = width
        self.height = height
        self.indices = indices
        self.palette = palette
        self.transparency = transparency


def _unfilter(raw, width, height, bit_depth):
    """Undo PNG scanline filters; return one bytes object per row."""
    stride = (width * bit_depth + 7) // 8
    bpp = 1  # indexed pixels are packed into bytes, so one byte per filter
    pos = 0
    prev = bytearray(stride)
    rows = []
    for _ in range(height):
        if pos + 1 + stride > len(raw):
            return None
        filter_type = raw[pos]
        pos += 1
        row = bytearray(raw[pos:pos + stride])
        pos += stride

        if filter_type == 0:  # None
            pass
        elif filter_type == 1:  # Sub
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i - bpp]) & 0xFF
        elif filter_type == 2:  # Up
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 0xFF
        elif filter_type == 3:  # Average
            for i in range(stride):
                left = row[i - bpp] if i >= bpp else 0
                row[i] = (row[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif filter_type == 4:  # Paeth
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                if pa <= pb and pa <= pc:
                    predictor = a
                elif pb <= pc:
                    predictor = b
                else:
                    predictor = c
                row[i] = (row[i] + predictor) & 0xFF
        else:
            return None

        rows.append(row)
        prev = row
    return rows


def decode_indexed_png(data):
    """Return an IndexedPNG, or None when pygame should handle the file."""
    data = bytes(data)
    if data[:8] != PNG_SIGNATURE:
        return None

    ihdr = None
    plte = None
    trns = None
    compressed = bytearray()
    pos = 8
    while pos + 12 <= len(data):
        length = struct.unpack_from(">I", data, pos)[0]
        tag = data[pos + 4:pos + 8]
        if pos + 12 + length > len(data):
            return None
        payload = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if tag == b"IHDR":
            ihdr = payload
        elif tag == b"PLTE":
            plte = payload
        elif tag == b"tRNS":
            trns = payload
        elif tag == b"IDAT":
            compressed += payload
        elif tag == b"IEND":
            break

    if ihdr is None or plte is None or not compressed or len(ihdr) != 13:
        return None
    width, height, depth, color_type, compression, filtering, interlace = \
        struct.unpack(">IIBBBBB", ihdr)
    if color_type != 3 or compression != 0 or filtering != 0 or interlace != 0:
        return None
    if depth not in (1, 2, 4, 8):
        return None
    if not (1 <= width <= _MAX_DIMENSION and 1 <= height <= _MAX_DIMENSION):
        return None
    if len(plte) % 3 or not plte:
        return None

    palette = [tuple(plte[i:i + 3]) for i in range(0, len(plte), 3)]
    try:
        raw = zlib.decompress(bytes(compressed))
    except zlib.error:
        return None
    rows = _unfilter(raw, width, height, depth)
    if rows is None:
        return None

    indices = bytearray()
    if depth == 8:
        for row in rows:
            indices += row
    else:
        mask = (1 << depth) - 1
        for row in rows:
            count = 0
            for byte in row:
                for shift in range(8 - depth, -1, -depth):
                    if count >= width:
                        break
                    indices.append((byte >> shift) & mask)
                    count += 1
                if count >= width:
                    break
    if len(indices) != width * height or max(indices) >= len(palette):
        return None
    return IndexedPNG(width, height, bytes(indices), palette, trns)
