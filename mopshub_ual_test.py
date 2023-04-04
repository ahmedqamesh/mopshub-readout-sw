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

timeout = 0.05
def test_uhal_wrapper():
    #print ("=========================regcsr================================")
    #nodecsr = wrapper.get_ual_node(hw =hw, registerName = "regcsr")
    #await wrapper.write_uhal_message(hw = hw, node =nodecsr, data=5, registerName="regcsr", timeout=timeout)
    #await wrapper.read_uhal_message(node =nodecsr, registerName="regcsr", timeout=timeout)
    print ("=========================Read Reg================================")
    NodeIds = [0,1]
    #Flush The FIFO
    wrapper.write_uhal_message(hw = hw, 
                                      node =wrapper.get_ual_node(hw =hw, registerName = "reg11"), 
                                      registerName="reg11", 
                                      data = 0x1, 
                                      timeout=timeout)  
    #print ("=========================Write Reg================================")
    #power On/off the bus
    #for i in np.arange(33,0,-1):
    i =  0
    power_reg6_hex = Analysis().binToHexa(bin(0x91)[2:].zfill(8)+
                                          bin(i)[2:].zfill(8)+
                                          bin(0)[2:].zfill(8)+
                                          bin(0)[2:].zfill(8)) 
   # wrapper.write_uhal_mopshub_message(hw =hw, data=[power_reg6_hex,power_reg6_hex,power_reg6_hex,0xa], reg = ["reg6","reg7","reg8","reg9"], timeout=timeout)
    
    # data_point, reqmsg, requestreg, respmsg,responsereg , status =  wrapper.read_sdo_uhal(hw =hw,
    #                                                                                       SDO_TX = 0X900,
    #                                                                                       nodeId=n, 
    #                                                                                       index=int(str(hex(i)),16),
    #                                                                                       subindex=0x0,
    #                                                                                       bus = 0,
    #                                                                                       timeout=timeout, 
    #                                                                                       out_msg =True)

    time.sleep(0.1)
    #wait for interrupt
    #cobid, _, respmsg, responsereg, t = wrapper.read_uhal_mopshub_message(reg = ["reg0","reg1","reg2"], timeout=timeout)
    adc_result = []
    #adc_result = [[int(), int()] for _ in range(4)]
    adc_out = []
    channel_value = ("UH", "IMON", "VCAN", "Temperature")
    address_byte = [0x80, 0x88, 0x90, 0x98, 0x80]
    #wrapper.read_adc(hw =hw,bus_id = 0x0,timeout= timeout)
    cobid_ret, spi_id_ret, spi_reg_ret, adc_out =  wrapper.read_monitoring_uhal(hw =hw,
                                                                                 cobid =0X20,
                                                                                 spi_reg =0x88,
                                                                                 spi_id=0x0,
                                                                                 timeout=timeout, 
                                                                                 out_msg =True)
    # for address in address_byte:
    #      #time.sleep(0.1)
    #      cobid_ret, spi_id_ret, spi_reg_ret, adc_out =  wrapper.read_monitoring_uhal(hw =hw,
    #                                                                                   cobid = 0x20,
    #                                                                                   spi_reg =address,
    #                                                                                   spi_id=0x0,
    #                                                                                   timeout=timeout, 
    #                                                                                   out_msg =True)
    #
    #      #adc_out =[float.fromhex(adc_out[i]) for i in range(len(adc_out))] 
    #      if adc_out[4] == 224 or adc_out[4] == 228 or adc_out[4] == 232:
    #         adc_result.append(round(((adc_out[2] * 256 + adc_out[3]) * 0.03814697 / 1000), 3))  
    #      else:
    #         v_ntc = round(((adc_out[2] * 256.0 + adc_out[3]) * 0.03814697 / 1000), 3)
    #         r_ntc = v_ntc * (20.0 / 4.75)
    #         print(adc_out[2],adc_out[3],r_ntc, v_ntc)
    #         adc_result.append(round((298.15 / (1 - (298.15 / 3435) * np.log(10 / r_ntc))) - 273.15, 3))
    # # del adc_result[0]
    # # print(adc_result)
    #check the situation
    # wrapper.read_uhal_message(hw = hw, 
    #                           node =wrapper.get_ual_node(hw =hw, registerName = "reg3"),
    #                           registerName="reg3", timeout=0.1)
    #Example (1): Read some Reg 
    #await wrapper.read_uhal_mopshub_message(hw =hw, reg = ["reg3","reg4","reg5"], timeout=timeout)  
    #await wrapper.read_uhal_mopshub_message(hw =hw, reg = ["reg6","reg7","reg8"], timeout=timeout) 
 
    #Example (2): write/read SDO message   
    # data_point, reqmsg, requestreg, respmsg,responsereg , status =  wrapper.read_sdo_uhal(hw =hw,
    #                                                                                         nodeId=NodeIds[0], 
    #                                                                                         index=0x2400,
    #                                                                                         subindex=0xD,
    #                                                                                         bus = 1,
    #                                                                                         timeout=timeout, 
    #                                                                                         out_msg =True)
    # print(data_point, reqmsg, requestreg, respmsg,responsereg , status)
    # #  #Example (3): Read all the ADC channels and Save it to a file in the directory output_data    
    # csv_writer = wrapper.create_mopshub_adc_data_file(outputname = "mopshub_top_32bus", # Data file name
    #                                      outputdir = rootdir + "/output_data") # # Data directory)
    # while True:
    #     wrapper.read_mopshub_adc_channels(hw =hw,
    #                                     bus_range = [1],#range(1,2), 
    #                                     file ="mops_config.yml", #Yaml configurations
    #                                     directory=rootdir+"/config_files", # direstory of the yaml file
    #                                     nodeId = NodeIds, # Node Id
    #                                     n_readings = 30000,
    #                                     csv_writer =csv_writer,
    #                                     outputname = "mopshub_top_32bus", # Data file name
    #                                     outputdir = rootdir + "/output_data",
    #                                     timeout = timeout) # Number of Iterations  
    # #  # PS. To visualise the data, Users can use the file $HOME/test_files/plot_adc.py
if __name__ == '__main__':
    # PART 1: Argument parsing
    uri = "ipbusudp-2.0://192.168.200.16:50001"
    addressFilePath = "config_files/ipbus_example.xml"
    wrapper = UHALWrapper(load_config = True)
    # PART 2: Creating the HwInterface
    hw = wrapper.config_uhal_hardware()
    test_uhal_wrapper()

