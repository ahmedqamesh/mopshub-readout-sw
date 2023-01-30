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
import struct
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from analysis_utils      import AnalysisUtils
from uhal_wrapper_main   import UHALWrapper

timeout = 0.1
async def test_uhal_wrapper():
    #print ("=========================regcsr================================")
    #nodecsr = wrapper.get_ual_node(hw =hw, registerName = "regcsr")
    #await wrapper.write_uhal_message(hw = hw, node =nodecsr, data=5, registerName="regcsr", timeout=timeout)
    #await wrapper.read_uhal_message(node =nodecsr, registerName="regcsr", timeout=timeout)
    print ("=========================Read Reg================================")
    nodes = []
    NodeIds = [0,8]
    #for i in np.arange(0,9):
    #    nodes = np.append(nodes,wrapper.get_ual_node(hw =hw, registerName = "reg"+str(i)))
    #    await wrapper.read_uhal_message(hw = hw, node =nodes[i], registerName="reg"+str(i), timeout=timeout)
    #print ("=========================Write Reg================================")
    # while i<=20:
    #await wrapper.write_uhal_mopshub_message(hw =hw,  data=[0x60140240,0x01b00000,0x10000000,0x00000000], reg = ["reg6","reg7","reg8","reg9"], timeout=timeout)
    #await wrapper.write_uhal_mopshub_message(hw =hw, data=[0x600debea,0xdef00bea,0xdde00000,0x00000000], reg = ["reg6","reg7","reg8","reg9"], timeout=timeout)#0xAAAAAAAA
    #     time.sleep(1)
    #     i = i+1
    #
    #await wrapper.read_uhal_mopshub_message(hw =hw, reg = ["reg0","reg1","reg2"], timeout=timeout)   
    #await wrapper.read_uhal_mopshub_message(hw =hw, reg = ["reg3","reg4","reg5"], timeout=timeout)  
    #await wrapper.read_uhal_mopshub_message(hw =hw, reg = ["reg6","reg7","reg8"], timeout=timeout) 


     #Example (3): Read all the ADC channels and Save it to a file in the directory output_data
     # PS. To visualise the data, Users can use the file $HOME/test_files/plot_adc.py
    await wrapper.read_adc_channels(hw =hw, 
                                    file ="mops_config.yml", #Yaml configurations
                                    directory=rootdir+"/config_files", # direstory of the yaml file
                                    nodeId = NodeIds[0], # Node Id
                                    outputname = "adc_data_trial", # Data file name
                                    outputdir = rootdir + "/output_data", # # Data directory
                                    n_readings = 1) # Number of Iterations  
    
    
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
