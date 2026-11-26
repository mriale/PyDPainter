#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""Minimal PNG writer for 8-bit indexed images.

The encoder uses only the standard library (``struct`` and ``zlib``).  Pygame
is imported lazily by the Surface helpers, so the core encoder can be used
with plain index data without any image library installed.
"""

import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_chunk(tag, data):
    """Return one PNG chunk with its length and CRC."""
    crc = zlib.crc32(data, zlib.crc32(tag)) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def encode_indexed_png(width, height, indices, palette,
                       transparent_index=None, alphas=None, compress_level=6):
    """Encode an 8-bit indexed PNG as bytes.

    ``indices`` is ``width * height`` bytes of palette indices in scanline
    order (top to bottom, left to right).  ``palette`` is a sequence of up to
    256 ``(r, g, b)`` or ``(r, g, b, a)`` colors.  Each row is written with
    PNG filter type 0 (None), so the decompressed IDAT data contains the exact
    index values with no filtering applied.
    """
    if width < 1 or height < 1:
        raise ValueError("PNG dimensions must be positive")
    indices = bytes(indices)
    if len(indices) != width * height:
        raise ValueError("index data does not match image dimensions")

    colors = []
    palette_alphas = []
    for color in palette[:256]:
        r, g, b = color[:3]
        colors.append(bytes((r & 0xFF, g & 0xFF, b & 0xFF)))
        palette_alphas.append((color[3] if len(color) > 3 else 255) & 0xFF)
    if not colors:
        raise ValueError("an indexed PNG needs at least one palette color")
    # Every byte fits a 256-entry palette; only scan the pixels for shorter
    # palettes (max() over a large bytes object is surprisingly costly).
    if len(colors) < 256 and max(indices) >= len(colors):
        raise ValueError("pixel index is outside the palette")

    if alphas is None:
        alphas = list(palette_alphas)
    else:
        alphas = list(alphas)[:len(colors)]
        if len(alphas) < len(colors):
            alphas.extend([255] * (len(colors) - len(alphas)))
    if transparent_index is not None:
        if not 0 <= transparent_index < len(colors):
            raise ValueError("transparent index is outside the palette")
        alphas[transparent_index] = 0

    # One filter byte ("None") followed by one row of 8-bit indices.
    stride = width
    raw = bytearray((stride + 1) * height)
    for y in range(height):
        start = y * (stride + 1)
        raw[start] = 0
        raw[start + 1:start + 1 + stride] = \
            indices[y * stride:(y + 1) * stride]

    out = bytearray(PNG_SIGNATURE)
    out += png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height,
                                          8, 3, 0, 0, 0))
    out += png_chunk(b"PLTE", b"".join(colors))
    # For color type 3, tRNS holds one alpha byte per palette entry.  Trailing
    # fully opaque entries may be omitted; missing entries default to 255.
    while alphas and alphas[-1] == 255:
        alphas.pop()
    if alphas:
        out += png_chunk(b"tRNS", bytes(alphas))
    out += png_chunk(b"IDAT", zlib.compress(bytes(raw), compress_level))
    out += png_chunk(b"IEND", b"")
    return bytes(out)


def surface_png_bytes(surface, palette=None, transparent_index=None,
                      compress_level=6):
    """Encode an 8-bit pygame Surface as an indexed PNG.

    A non-indexed Surface is converted using ``palette`` (which is then
    required).  If no transparency is specified, the Surface's colorkey and
    any palette alpha values are written into ``tRNS``, matching the
    information pygame's PNG saver would have used.
    """
    import pygame  # lazy import keeps the encoder itself dependency-free

    width, height = surface.get_size()
    if surface.get_bytesize() != 1:
        if palette is None:
            raise ValueError("a truecolor surface needs a palette to convert")
        indexed = pygame.Surface((width, height), 0, 8)
        indexed.set_palette(palette)
        indexed.blit(surface, (0, 0))
        surface = indexed

    if palette is None:
        palette = surface.get_palette()
    if palette is None:
        raise ValueError("an indexed PNG needs a palette")

    indices = pygame.image.tobytes(surface, "P")

    alphas = None
    if any(len(color) > 3 and color[3] != 255 for color in palette):
        alphas = [color[3] if len(color) > 3 else 255 for color in palette]

    if transparent_index is None:
        colorkey = surface.get_colorkey()
        if colorkey is not None:
            if isinstance(colorkey, int):
                transparent_index = colorkey
            else:
                # pygame reports the colorkey of an 8-bit surface as an RGB
                # tuple; map it back to the palette entry it came from.
                key = tuple(colorkey[:3])
                for i, color in enumerate(palette):
                    if tuple(color[:3]) == key:
                        transparent_index = i
                        break

    return encode_indexed_png(width, height, indices, palette,
                              transparent_index=transparent_index,
                              alphas=alphas, compress_level=compress_level)


def save_indexed_png(filename, surface, **kwargs):
    """Write ``surface`` as an indexed PNG to a path or file-like object."""
    data = surface_png_bytes(surface, **kwargs)
    if hasattr(filename, "write"):
        filename.write(data)
    else:
        with open(filename, "wb") as f:
            f.write(data)
