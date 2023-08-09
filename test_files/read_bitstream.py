import sys
import os
import time
from pynq import Overlay
import csv
import pandas as pd

from pynq import Overlay

bistream_dir = "/run/media/dcs/data2/workspaces/mopshub_board/mopshub_board.runs/"
bistream_file = bistream_dir+"impl_1/mopshub_design_32bus_wrapper.bit"
print(bistream_file)

def _read_bitstream(bitsream_file = None, words_to_parse = 512):
    file =  open(bitsream_file, "rb")
    # read maximum of 255 bytes at once
    # create the csv writer
    bitstream_line = file.readline().translate(None, b'\r\n')
    print(bitstream_line)

    i= 0
    while bitstream_line and i <=10:
        #print(bitstream_line)
        #end_line = bitstream_line.find("\n") + 1
        bitstream_line = file.readline().translate(None, b'\r\n')
        stream.read(bitstream_line, 1 )
        print(bitstream_line)
        i = i+1
    file.close()
    
    #
    #
    #for item in str(bitstream_data[0:10]):
    #    print(item)
    #    print("+++++++++++++++++++")
    #print(f"Byte {i}: 0x{byte:02X}")
    #return bitsream_file

if __name__ == "__main__":
    _read_bitstream(bitsream_file = bistream_file)