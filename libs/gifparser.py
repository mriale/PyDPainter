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

class LzwEntry:
    def __init__(self, byte=None, prev=-1, len=1):
        self.byte = byte
        self.prev = prev
        self.len = len

class GIFParser:
    def __init__(self, filename):
        self.file = open(filename, "rb")
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
        #print(f"{hex(block_id)=}")
        while block_id != TRAILER:
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
        while ext_id != 0:
            #print(f"{ext_id=}")
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
            #ignore chunk
            else:
                chunk_len = int(self.file.read(1)[0])
                self.file.seek(chunk_len, 1)

            ext_id = int(self.file.read(1)[0])

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
        input = list(input_data)
        code_length = key_size
        input_length = len(input_data)
        out = []

        maxbits = 0
        i = 0
        idi = 0
        outi = 0
        bit = 0
        code = -1
        prev = -1
        dictionary = {}
        dictionary_ind = 0
        mask = 0x01
        reset_code_length = code_length
        clear_code = 1 << code_length
        stop_code = clear_code + 1
        match_len = 0

        # Initialize the first 2^code_len entries of the dictionary with their
        # indices. The rest of the entries will be built up dynamically.

        for dictionary_ind in range(1 << code_length):
            dictionary[dictionary_ind] = LzwEntry(dictionary_ind)

        # 2^code_len + 1 is the special "end" code; don't give it an entry here
        dictionary_ind = (1 << code_length) + 2

        while input_length > 0:
            code = 0x0
            # Always read one more bit than the code length
            for i in range(code_length + 1):
                bit = 1 if input_data[idi] & mask else 0
                mask <<= 1

                if mask == 0x100:
                    mask = 0x01
                    idi += 1;
                    input_length -= 1

                code = code | (bit << i)

            if code == clear_code:
                code_length = reset_code_length;
                for dictionary_ind in range(1 << code_length):
                    dictionary[dictionary_ind] = LzwEntry(dictionary_ind)
                dictionary_ind = (1 << code_length) + 2
                prev = -1
                continue
            elif code == stop_code:
                break

            # Update the dictionary with this character plus the _entry_
            # (character or string) that came before it
            if prev > -1 and code_length < 12:
                if code > dictionary_ind:
                    #print("code = %.02x, but dictionary_ind = %.02x\n"%(code, dictionary_ind))
                    return []

                # Special handling for KwKwK
                ptr = code
                if code == dictionary_ind:
                    ptr = prev;

                while dictionary[ptr].prev != -1:
                    ptr = dictionary[ptr].prev
                dictionary[dictionary_ind] = LzwEntry(dictionary[ptr].byte,prev, dictionary[prev].len + 1)
                dictionary_ind += 1

                # GIF89a mandates that this stops at 12 bits
                if dictionary_ind == (1 << (code_length + 1)) and code_length < 11:
                    code_length += 1

            prev = code

            # Now copy the dictionary entry backwards into "out"
            match_len = dictionary[code].len
            while code != -1:
                maxout = outi + dictionary[code].len
                if maxout > len(out):
                    out.extend((maxout - len(out)) * [0])
                out[outi + dictionary[code].len - 1] = dictionary[code].byte;
                if dictionary[code].prev == code:
                    #print("Internal error; self-reference.")
                    return []
                code = dictionary[code].prev;

            outi += match_len;

        return out

    def get_frames(self):
        frames = []

        while self.file.tell() < os.fstat(self.file.fileno()).st_size:
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

        return frames

