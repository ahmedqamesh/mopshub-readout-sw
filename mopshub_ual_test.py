#!/bin/env python
import math
import random # For randint
import sys # For sys.argv and sys.exit
import uhal
import numpy as np
import time
import os
import binascii
import asyncio
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from analysis_utils      import AnalysisUtils
from uhal_wrapper_main   import UHALWrapper

timeout = 0.1
async def test_uhal_wrapper():
    #print ("=========================regcsr================================")
    #nodecsr = wrapper.get_ual_node(hw =hw, registerName = "regcsr")
    #await write_uhal_message(node =nodecsr, data=5, registerName="regcsr", timeout=timeout)
    #await wrapper.read_uhal_message(node =nodecsr, registerName="regcsr", timeout=timeout)
    print ("=========================Read Reg================================")
    nodes = []
    for i in np.arange(0,9):
        nodes = np.append(nodes,wrapper.get_ual_node(hw =hw, registerName = "reg"+str(i)))
        await wrapper.read_uhal_message(hw = hw, node =nodes[i], registerName="reg"+str(i), timeout=timeout)
    print ("=========================Write Reg================================")
    while i<=100:
        await wrapper.write_uhal_mopshub_message(hw =hw, data=[0x600debea,0xdef00bea,0xdde00001,0xdde00000], reg = ["reg6","reg7","reg8","reg8"], timeout=timeout)#0xAAAAAAAA
        time.sleep(1)
        i = i+1
    await wrapper.read_uhal_mopshub_message(hw =hw, reg = ["reg0","reg1","reg2"], timeout=timeout)   
    await wrapper.read_uhal_mopshub_message(hw =hw, reg = ["reg3","reg4","reg5"], timeout=timeout)  
    #await  wrapper.read_uhal_mopshub_message(hw =hw, reg = ["reg6","reg7","reg8"], timeout=timeout) 

if __name__ == '__main__':
    # PART 1: Argument parsing
    uri = "ipbusudp-2.0://192.168.200.16:50001"
    addressFilePath = "config_files/ipbus_example.xml"
    wrapper = UHALWrapper(load_config = True)
    # PART 2: Creating the HwInterface
    hw = wrapper.config_uhal_hardware()
    loop = asyncio.get_event_loop()
    try:
        asyncio.ensure_future(test_uhal_wrapper())
        loop.run_forever()
    finally: 
        loop.close()
