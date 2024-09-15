#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import struct, os
import numpy as np

EXTENSION_INTRODUCER = 0x21
IMAGE_DESCRIPTOR     = 0x2C
TRAILER              = 0x3B

GRAPHIC_CONTROL       = 0xF9
APPLICATION_EXTENSION = 0xFF
COMMENT_EXTENSION     = 0xFE
PLAINTEXT_EXTENSION   = 0x01

class BitReader(object):
    def __init__(self, byte_string):
        if not isinstance(byte_string, bytes):
            raise TypeError("Requires bytelike object")
        self._str = bytes(byte_string)
        self._ptr = 0
        self._len = len(byte_string) * 8
    def read(self, amount):
        byte_start, start = divmod(self._ptr, 8)
        byte_end, end = divmod(min(self._ptr+amount, self._len), 8)
        if byte_start > self._len:
            return 0
        if byte_start == byte_end:
            byte = self._str[byte_start]
            if start:
                byte >>= start
            byte &= ~(-1 << (end - start))
            self._ptr = (byte_end << 3) | end
            bit_str = byte
        else:
            bit_str = 0
            bit_index = 0
            i = byte_start
            if start:
                bit_str |= self._str[i] >> start
                bit_index += (8 - start)
                i += 1
            while i < byte_end:
                bit_str |= (self._str[i] << bit_index)
                bit_index += 8
                i += 1
            if end:
                byte = self._str[i] & (~(-1 << end))
                bit_str |= (byte << bit_index)
                bit_index += end
        self._ptr = (byte_end << 3) | end
        return bit_str

class GIFParser:
    def __init__(self, filename, status_func=None):
        self.file = open(filename, "rb")
        self.status_func = status_func
        self.header = self.read_header()
        #print(f"{self.header=}")
        self.global_palette = None
        if self.header["global_color_table"]:
            self.global_palette = self.read_palette(self.header["global_num_colors"])
        #print(f"{self.global_palette=}")
        self.frames = self.get_frames()
        #print(f"{len(self.frames)=}")
        #print(f"{self.frames=}")

    def read_header(self):
        header = self.file.read(13)
        flags = header[10]
        global_color = (flags & 0x80) >> 7
        num_colors = 1 << ((flags & 0x07) + 1)
        return {
            "signature": header[0:3],
            "version": header[3:6],
            "width": struct.unpack("<H", header[6:8])[0],
            "height": struct.unpack("<H", header[8:10])[0],
            "global_color_table_flags": header[10],
            "global_color_table": global_color,
            "global_num_colors": num_colors,
            "background_color_index": header[11],
            "pixel_aspect_ratio": header[12],
        }

    def read_palette(self, num_colors):
        clut = self.file.read(3*num_colors)
        pal = []
        for i in range(num_colors):
            pal.append([clut[i*3], clut[i*3+1], clut[i*3+2]])
        return pal

    def read_data_blocks(self):
        blocks = {}
        block_id = int(self.file.read(1)[0])
        while block_id != TRAILER:
            #print(f"{hex(block_id)=} {self.file.tell()=}")
            if block_id == EXTENSION_INTRODUCER:
                ext = self.read_extension()
                if len(ext) > 0:
                    blocks |= ext
            elif block_id == IMAGE_DESCRIPTOR:
                break

            block_id = int(self.file.read(1)[0])
        return blocks

    def read_extension(self):
        blocks = {}
        ext_id = int(self.file.read(1)[0])
        #print(f"{hex(ext_id)=} {self.file.tell()=}")

        if ext_id == GRAPHIC_CONTROL:
            chunk_len = int(self.file.read(1)[0])
            chunk = self.file.read(chunk_len)
            flags = chunk[0]
            disposal_method = (flags & 0x1C) >> 2
            transparency = flags & 0x1
            blocks |= {
                "disposal_method": int(disposal_method),
                "transparency": int(transparency),
                "delay_time": struct.unpack("<H", chunk[1:3])[0],
                "transparent_color_index": int(chunk[3]),
            }
        #ignore other extensions
        else:
            chunk_len = int(self.file.read(1)[0])
            chunk = self.file.read(chunk_len)

        #read and discard all data after block
        chunk_len = int(self.file.read(1)[0])
        while (chunk_len):
            chunk = self.file.read(chunk_len)
            chunk_len = int(self.file.read(1)[0])

        #print(blocks)
        return blocks

    def read_image_descriptor(self):
        descriptor = self.file.read(9)
        flags = descriptor[8]
        local_color = (flags & 0x80) >> 7
        interlace = (flags & 0x40) >> 6
        num_colors = 1 << ((flags & 0x07) + 1)
        pal = None
        if local_color:
            pal = self.read_palette(num_colors)
            if self.global_palette != None and num_colors < len(self.global_palette):
                pal.extend([[0,0,0]] * (len(self.global_palette) - num_colors))
            elif self.global_palette != None and num_colors > len(self.global_palette):
                pal = pal[:len(self.global_palette)]
        return {
            "image_left_position": struct.unpack("<H", descriptor[0:2])[0],
            "image_top_position": struct.unpack("<H", descriptor[2:4])[0],
            "image_width": struct.unpack("<H", descriptor[4:6])[0],
            "image_height": struct.unpack("<H", descriptor[6:8])[0],
            "local_color_table_flag": local_color,
            "interlace_flag": interlace,
            "local_palette": pal,
        }

# GIF decoding routine from:
#  https://commandlinefanatic.com/cgi-bin/showarticle.cgi?article=art011
    def decode_lzw_data(self, input_data, key_size):
        code_in = BitReader(input_data)
        idx_out = []
        bit_size = key_size + 1
        bit_inc = (1 << (bit_size)) - 1
        CLEAR = 1 << key_size
        END = CLEAR + 1
        code_table_len = END + 1
        code_last = -1
        code_table = [-1] * code_table_len
        for x in range(code_table_len):
            code_table[x] = (x,)
        while code_last != END:
            code_id = code_in.read(bit_size)
            if code_id == CLEAR:
                bit_size = key_size + 1
                bit_inc = (1 << (bit_size)) - 1
                code_last = -1
                code_table = code_table[:code_table_len]
            elif code_id == END:
                break
            elif code_id < len(code_table) and code_table[code_id] is not None:
                current = code_table[code_id]
                idx_out.extend(current)
                k = (current[0],)
            elif code_last not in (-1, CLEAR, END):
                previous = code_table[code_last]
                k = (previous[0],)
                idx_out.extend(previous + k)
            if len(code_table) == bit_inc and bit_size < 12:
                bit_size += 1
                bit_inc = (1 << (bit_size)) - 1
            if code_last not in (-1, CLEAR, END):
                code_table.append(code_table[code_last] + k)
            code_last = code_id
        return idx_out
    def get_frames(self):
        frames = []

        while self.file.tell() < os.fstat(self.file.fileno()).st_size:
            #print(f"frame={len(frames)+1}")
            data_blocks = self.read_data_blocks()
            #print(f"{data_blocks=}")

            #print(f"{self.file.tell()}/{os.fstat(self.file.fileno()).st_size}")
            if self.file.tell() == os.fstat(self.file.fileno()).st_size:
                break

            descriptor = self.read_image_descriptor()
            if descriptor["image_width"] == 0 and descriptor["image_height"] == 0:
                # End of GIF
                break
            #print(descriptor)

            key_size = int(self.file.read(1)[0])
            chunk_len = int(self.file.read(1)[0])

            lzw_data = b""
            while chunk_len != 0:
                #print(f"*****{chunk_len=}*****")
                lzw_data += self.file.read(chunk_len)
                chunk_len = int(self.file.read(1)[0])

            pic_data = np.asarray(list(self.decode_lzw_data(lzw_data, key_size)))
            width = descriptor["image_width"]
            height = descriptor["image_height"]
            pic_data = np.reshape(pic_data, (height, width)).transpose()
            if descriptor["interlace_flag"]:
                pic_out = pic_data.copy()
                pic_out[:,0:height:8] = pic_data[:,0:((height-1)//8)+1]
                pic_out[:,4:height:8] = pic_data[:,((height-1)//8)+1:((height-1)//4)+1]
                pic_out[:,2:height:4] = pic_data[:,((height-1)//4)+1:((height-1)//2)+1]
                pic_out[:,1:height:2] = pic_data[:,((height-1)//2)+1:height]
                pic_data = pic_out

            #print(f"{len(pic_data)=}")
            #print(f"{pic_data=}")
            frames.append(data_blocks | descriptor | {"image_data": pic_data})
            if self.status_func != None:
                self.status_func(self.file.tell() / os.fstat(self.file.fileno()).st_size)

        return frames

