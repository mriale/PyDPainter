#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import struct, os
import numpy as np
import math

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

class GIFWriter:
    def __init__(self, filename, header, global_palette, status_func=None):
        self.file = open(filename, "wb")
        self.status_func = status_func
        self.header = header
        self.frame = None
        self.global_palette = global_palette
        #print(f"{self.header=}")
        self.write_header()
        if self.header["global_color_table"]:
            self.write_palette(self.global_palette)
        #print(f"{len(self.frame)=}")
        #print(f"{self.frame=}")
        self.first_frame = True

    def __del__(self):
        self.file.write(struct.pack("B", TRAILER)) # End of file
        self.file.close()

    def write_header(self):
        header = b"GIF89a"
        header += struct.pack("<HH", self.header["width"], self.header["height"])
        num_colors = self.header["global_num_colors"]
        global_color = self.header["global_color_table"]
        flags = 0x70
        flags |= (int(math.log(num_colors,2)) - 1)
        flags |= global_color << 7
        header += struct.pack("B", flags)
        header += b'\x00\x00'
        self.file.write(header)

    def write_palette(self, pal):
        for rgb in pal:
            self.file.write(struct.pack("BBB", rgb[0], rgb[1], rgb[2]))

    def write_extensions(self):
        if self.first_frame:
            self.file.write(struct.pack("B", EXTENSION_INTRODUCER))
            self.file.write(struct.pack("B", APPLICATION_EXTENSION))
            self.file.write(struct.pack("B", 11)) # 11 bytes app name
            self.file.write(b'NETSCAPE2.0') # app name for compatibility
            self.file.write(struct.pack("B", 3)) # 3 bytes to follow
            self.file.write(struct.pack("B", 1)) # index of sub-block
            self.file.write(struct.pack("<H", 0)) # repeat counter (infinite)
            self.file.write(b"\x00") # End of blocks
            self.first_frame = False

        self.file.write(struct.pack("B", EXTENSION_INTRODUCER))
        self.file.write(struct.pack("B", GRAPHIC_CONTROL))
        self.file.write(b"\x04") # 4 bytes to follow
        flags = 0x00
        if "disposal_method" in self.frame:
            flags |= self.frame["disposal_method"] << 2
        if "transparency" in self.frame:
            flags |= self.frame["transparency"]
        delay_time = 100*4//60
        if "delay_time" in self.frame:
            delay_time = self.frame["delay_time"]
        tcolor_i = 0
        if "transparent_color_index" in self.frame:
            tcolor_i = self.frame["transparent_color_index"]
        self.file.write(struct.pack("B", flags))
        self.file.write(struct.pack("<H", delay_time)) # Delay time
        self.file.write((struct.pack("B", tcolor_i))) # Transparent color index
        self.file.write(b"\x00") # End of blocks

    def write_image_descriptor(self):
        self.file.write(struct.pack("B", IMAGE_DESCRIPTOR))
        self.file.write(b"\x00\x00\x00\x00") # x,y coords
        self.file.write(struct.pack("<HH", self.header["width"], self.header["height"]))
        if self.header["global_color_table"]:
            pal = None
        else:
            pal = self.frame["local_palette"]
        flags = 0
        if pal != None:
            flags |= (int(math.log(len(pal),2)) - 1)
            flags |= 0x80 
            self.file.write(struct.pack("B", flags))
            self.write_palette(pal)
        else:
            self.file.write(b"\x00") # No flags set and no palette


    def write_bits(self, code, code_length):
        out = b''

        mask_pos = 0

        while code_length > 0:
            # Set the appropriate bit in the buffer
            self.static_buf |= (1 if code & (1 << mask_pos) else 0) << self.static_bufpos
            mask_pos += 1
            self.static_bufpos += 1

            # Flush the buffer if it's full
            if self.static_bufpos == 8:
                out += struct.pack("B", self.static_buf)
                self.static_buf = 0x0
                self.static_bufpos = 0

            code_length -= 1

        return out

    def encode_lzw_data(self, buf):
        buflen = len(buf)
        dictionary = {}  # Use a dictionary for efficient lookups
        dictionary_ind = 258
        code_length = 9
        inp = buf
        out = b''
        self.static_buf = 0x0
        self.static_bufpos = 0

        # Initialize first 256 entries with their own values
        for i in range(256):
            dictionary[struct.pack("B", i)] = i

        out += self.write_bits(256, code_length) # clear code

        # Compress until there's no more data
        while buflen > 0:
            # Find the longest match in the dictionary
            longest_match = b''
            i = 1
            while i <= len(inp) and inp[0:i] in dictionary:
                longest_match = inp[0:i]
                code = dictionary[inp[0:i]]
                i += 1

            # Write the code to output
            out += self.write_bits(code, code_length)

            # Advance the input pointer
            inp = inp[len(longest_match):]
            buflen -= len(longest_match)

            # Expand the dictionary if necessary
            if dictionary_ind == 1 << code_length:
                code_length += 1

            if len(inp) > 0:
                # Add the longest match plus the next character to the dictionary
                dictionary[longest_match + struct.pack("B", inp[0])] = dictionary_ind
                dictionary_ind += 1

            # Reset dictionary if necessary
            if dictionary_ind >= 4094:
                out += self.write_bits(256, code_length) # clear code
                dictionary = {}
                for i in range(256):
                    dictionary[struct.pack("B", i)] = i
                dictionary_ind = 258
                code_length = 9

        out += self.write_bits(257, code_length) # end of info
        out += self.write_bits(0, 8) # flush bits
        return out

    def write_image(self):
        pic_data = np.copy(self.frame["image_data"])
        pic_bytes = bytes(pic_data.transpose().flatten())
        lzw_data = self.encode_lzw_data(pic_bytes)
        self.file.write(struct.pack("B", 8)) # LZW starting code size

        # Write out image data blocks
        data_left = len(lzw_data)
        while data_left > 255:
            start = len(lzw_data) - data_left
            end = start + 255
            self.file.write(struct.pack("B", 255))
            #print(f"{start=} {end=} {lzw_data[start:end]=}")
            self.file.write(lzw_data[start:end])
            data_left -= 255
        if data_left > 0:
            #print(f"{data_left=} {lzw_data[-data_left:]=}")
            self.file.write(struct.pack("B", data_left))
            self.file.write(lzw_data[-data_left:])
        self.file.write(struct.pack("B", 0)) # End of blocks
            

    def write_frame(self, frame):
        self.frame = frame
        self.write_extensions()
        self.write_image_descriptor()
        self.write_image()

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

