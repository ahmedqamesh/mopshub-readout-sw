#!/bin/env python
import math
import random # For randint
import sys # For sys.argv and sys.exit
import numpy as np
import time
import os
import binascii
#import asyncio
import struct
from asyncio.tasks import sleep
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from analysis_utils      import AnalysisUtils
from analysis            import Analysis
from uhal_wrapper_main   import UHALWrapper

timeout = 0.01
def test_uhal_wrapper():
    #print ("=========================regcsr================================")
    #nodecsr = wrapper.get_ual_node(hw =hw, registerName = "regcsr")
    #await wrapper.write_uhal_message(hw = hw, node =nodecsr, data=5, registerName="regcsr", timeout=timeout)
    #await wrapper.read_uhal_message(node =nodecsr, registerName="regcsr", timeout=timeout)
    print ("=========================Read Reg================================")
    nodes = []
    NodeIds = [0,0]
    #for i in np.arange(0,9):
    #    nodes = np.append(nodes,wrapper.get_ual_node(hw =hw, registerName = "reg"+str(i)))
    #    await wrapper.read_uhal_message(hw = hw, node =nodes[i], registerName="reg"+str(i), timeout=timeout)
    #print ("=========================Write Reg================================")
    #power off the bus
    #for i in np.arange(33,0,-1):
    i =  1
    spi_select_1 = Analysis().binToHexa(bin(i)[2:].zfill(8)[4:8])
    spi_select_0 = Analysis().binToHexa(bin(i)[2:].zfill(8)[0:4])
    
    reg6_hex = Analysis().binToHexa(bin(0x91)[2:].zfill(8)+
                                    bin(i)[2:].zfill(8)+
                                    bin(0)[2:].zfill(8)+
                                    bin(0)[2:].zfill(8)) 
                                    
                                        
   # print(hex(i),bin(i)[2:].zfill(8),bin(i)[2:].zfill(8)[0:3], bin(i)[2:].zfill(8)[3:8], spi_select_0, spi_select_1)
   # wrapper.write_uhal_mopshub_message(hw =hw, data=[reg6_hex,reg6_hex,reg6_hex,0x1], reg = ["reg6","reg7","reg8","reg9"], timeout=timeout)
    # count, count_limit = 0, 5
    #irq_tra_sig = 0x0
    #while (count !=count_limit):
    # while True:
    #     wrapper.write_uhal_mopshub_message(hw =hw, data=[0x60040240,0xd01000,0x00000000,0xA], reg = ["reg6","reg7","reg8","reg9"], timeout=timeout)#0xAAAAAAAA
    #     time.sleep(0.1)
    #     #wait for interrupt
    #     wrapper.read_uhal_mopshub_message(reg = ["reg0","reg1","reg2"], timeout=timeout)
    #     time.sleep(1) 
    #     count= count+1
    #Flush The FIFO
    # wrapper.write_uhal_message(hw = hw, 
    #                                   node =wrapper.get_ual_node(hw =hw, registerName = "reg11"), 
    #                                   registerName="reg11", 
    #                                   data = 0x1, 
    #                                   timeout=0.1)     
     #check the situation
    # wrapper.read_uhal_message(hw = hw, 
    #                           node =wrapper.get_ual_node(hw =hw, registerName = "reg3"),
    #                           registerName="reg3", timeout=0.1)

    # else:
    #     print("nothing detected")
    #await wrapper.read_uhal_mopshub_message(hw =hw, reg = ["reg3","reg4","reg5"], timeout=timeout)  
    #await wrapper.read_uhal_mopshub_message(hw =hw, reg = ["reg6","reg7","reg8"], timeout=timeout) 

    #Example (2): write/read SDO message

    # data_point, reqmsg, requestreg, respmsg,responsereg , status =  wrapper.read_sdo_uhal(hw = hw,
    #                                                                                       SDO_TX = 0X900,
    #                                                                                       nodeId=0, 
    #                                                                                       index=int(str(hex(i)),16),
    #                                                                                       subindex=0x0,
    #                                                                                       bus = 0,
    #                                                                                       timeout=timeout, 
    #                                                                                       out_msg =True)
    #while True:    
    data_point, reqmsg, requestreg, respmsg,responsereg , status =  wrapper.read_sdo_uhal(hw = hw,
                                                                                            nodeId=NodeIds[0], 
                                                                                            index=0x2400,
                                                                                            subindex=0xD,
                                                                                            bus = 1,
                                                                                            timeout=timeout, 
                                                                                            out_msg =True)

    # print(data_point, reqmsg, requestreg, respmsg,responsereg , status)
    #time.sleep(1)
    # #  #Example (3): Read all the ADC channels and Save it to a file in the directory output_data
    # #  # PS. To visualise the data, Users can use the file $HOME/test_files/plot_adc.py
    # await wrapper.write_uhal_message(hw = hw, 
    #                                  node =wrapper.get_ual_node(hw =hw, registerName = "reg11"), 
    #                                  registerName="reg11", 
    #                                  data = 0x1, 
    #                                  timeout=0.1)
    
    # wrapper.read_mopshub_adc_channels(hw =hw,
    #                                 bus_range = [1],#range(1,2), 
    #                                 file ="mops_config.yml", #Yaml configurations
    #                                 directory=rootdir+"/config_files", # direstory of the yaml file
    #                                 nodeId = NodeIds, # Node Id
    #                                 outputname = "mopshub_top_32bus", # Data file name
    #                                 outputdir = rootdir + "/output_data", # # Data directory
    #                                 n_readings = 1,
    #                                 timeout = timeout) # Number of Iterations  

if __name__ == '__main__':
    # PART 1: Argument parsing
    uri = "ipbusudp-2.0://192.168.200.16:50001"
    addressFilePath = "config_files/ipbus_example.xml"
    wrapper = UHALWrapper(load_config = True)
    # PART 2: Creating the HwInterface
    hw = wrapper.config_uhal_hardware()
    test_uhal_wrapper()
    # loop = asyncio.get_event_loop()
    # try:
    #     asyncio.ensure_future(test_uhal_wrapper())
    #     loop.run_until_complete(loop.shutdown_asyncgens())
    #     loop.run_forever()
    # finally: 
    #     loop.close()
