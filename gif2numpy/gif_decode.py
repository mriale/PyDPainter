#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#gif_decode.py

"""
This is an excerpt from the gif2numpy project:
https://github.com/bunkahle/gif2numpy

The module was not usable in its complete form because of
additional dependencies.

gif2numpy is licensed with the MIT license included in this
directory in the file LICENSE
"""

#================================================================
# Bit-level operations
#================================================================
class BitReader(object):
    '''Reads bits from a byte string'''
    
    __slots__ = [
        "_str",
        "_ptr",
        "_len",
    ]

    #------------------------------------------------
    # Construction
    #------------------------------------------------
    def __init__(self, byte_string):
        '''Initialize the reader with a complete byte string'''
        if not isinstance(byte_string, bytes):
            raise TypeError("Requires bytelike object")
        self._str = bytes(byte_string)
        self._ptr = 0
        self._len = len(byte_string) * 8
    
    #------------------------------------------------
    # Bit operations
    #------------------------------------------------
    def read(self, amount):
        '''Read bits from the byte string and returns int'''
        #--- Initialize indices ---
        byte_start, start = divmod(self._ptr, 8)
        byte_end, end = divmod(min(self._ptr+amount, self._len), 8)
        #Error check
        if byte_start > self._len:
            return 0
        
        #--- Read bits ---
        if byte_start == byte_end:
            #Reading from one byte
            byte = self._str[byte_start]
            if start:
                byte >>= start
            byte &= ~(-1 << (end - start))
            #Adjust pointer
            self._ptr = (byte_end << 3) | end
            bit_str = byte
        else:
            #Reading from many bytes
            bit_str = 0
            bit_index = 0
            i = byte_start
            #Read remaining piece of the start
            if start:
                bit_str |= self._str[i] >> start
                bit_index += (8 - start)
                i += 1
            #Grab entire bytes if necessary
            while i < byte_end:
                bit_str |= (self._str[i] << bit_index)
                bit_index += 8
                i += 1
            #Read beginning piece of end byte
            if end:
                byte = self._str[i] & (~(-1 << end))
                bit_str |= (byte << bit_index)
                bit_index += end
        
        #--- Update pointer ---
        self._ptr = (byte_end << 3) | end
        return bit_str


#================================================================
# LZW compression algorithms
#================================================================
def lzw_decompress(raw_bytes, lzw_min):
    '''Decompress the LZW data and yields output'''
    #Initialize streams
    code_in = BitReader(raw_bytes)
    idx_out = []
    #Set up bit reading
    bit_size = lzw_min + 1
    bit_inc = (1 << (bit_size)) - 1
    #Initialize special codes
    CLEAR = 1 << lzw_min
    END = CLEAR + 1
    code_table_len = END + 1
    #Begin reading codes
    code_last = -1
    while code_last != END:
        #Get the next code id
        code_id = code_in.read(bit_size)
        #Check the next code
        if code_id == CLEAR:
            #Reset size readers
            bit_size = lzw_min + 1
            bit_inc = (1 << (bit_size)) - 1
            code_last = -1
            #Clear the code table
            code_table = [-1] * code_table_len
            for x in range(code_table_len):
                code_table[x] = (x,)
        elif code_id == END:
            #End parsing
            break
        elif code_id < len(code_table) and code_table[code_id] is not None:
            current = code_table[code_id]
            #Table has code_id - output code
            idx_out.extend(current)
            k = (current[0],)
        elif code_last not in (-1, CLEAR, END):
            previous = code_table[code_last]
            #Code not in table
            k = (previous[0],)
            idx_out.extend(previous + k)
        #Check increasing the bit size
        if len(code_table) == bit_inc and bit_size < 12:
            bit_size += 1
            bit_inc = (1 << (bit_size)) - 1
        #Update the code table with previous + k
        if code_last not in (-1, CLEAR, END):
            code_table.append(code_table[code_last] + k)
        code_last = code_id
    return idx_out

