#!/bin/env python
import math
import random # For randint
import sys # For sys.argv and sys.exit
import numpy as np
import time
import os
import binascii
import struct
import serial
import time
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from analysis_utils      import AnalysisUtils
from analysis            import Analysis
from design_info         import DesignInfo
from uhal_wrapper_main   import UHALWrapper

timeout = 0.2
sm_info = DesignInfo()

def test_uart(bitrate = 115200, read_sm = ["0","1","2","3","4","5","6","7"]):
    ser = serial.Serial('/dev/ttyUSB2', parity=serial.PARITY_NONE,baudrate= bitrate, timeout=1
                       , bytesize=serial.EIGHTBITS,
                       stopbits=serial.STOPBITS_ONE)
    #Write to Uart
    
    if not ser.isOpen():
        ser.open()
    for sm_id in read_sm: 
        ser.write(bytearray(bytes.fromhex("0"+sm_id)))
        #ser.write('6'.encode())
        # Read from Uart
        time.sleep(0.2)
        Byte = ser.read() #read one byte
        #Byte = ser.readline()
        sm_info.get_sm_info(sm_id = int(sm_id), return_state = Byte)
        #time.sleep(0.5)
    
def power_control(bus = None):
    #power On/off the bus
    print ("=========================Powering OFF================================")
    power_state = 0x31 -1
    power_reg6_hex = Analysis().binToHexa(bin(power_state)[2:].zfill(8)+
                                          bin(bus)[2:].zfill(8)+
                                          bin(0)[2:].zfill(8)+
                                          bin(0)[2:].zfill(8)) 
    wrapper.write_uhal_mopshub_message(hw =hw, data=[power_reg6_hex,power_reg6_hex,power_reg6_hex,0xa], reg = ["reg6","reg7","reg8","reg9"], timeout=timeout)
    time.sleep(5)
    print ("=========================Powering ON================================")
    power_state = 0x31  
    power_reg6_hex = Analysis().binToHexa(bin(power_state)[2:].zfill(8)+
                                          bin(bus)[2:].zfill(8)+
                                          bin(0)[2:].zfill(8)+
                                          bin(0)[2:].zfill(8)) 
    wrapper.write_uhal_mopshub_message(hw =hw, data=[power_reg6_hex,power_reg6_hex,power_reg6_hex,0xa], reg = ["reg6","reg7","reg8","reg9"], timeout=timeout)  
    time.sleep(10)

def read_adc_iterations(n_readings = 1, bus_range = [1],NodeIds = None): 
    print ("=========================READ ADC================================")
    #  #Example (3): Read all the ADC channels and Save it to a file in the directory output_data    
    csv_writer = wrapper.create_mopshub_adc_data_file(outputname = "mopshub_top_32bus", # Data file name
                                        outputdir = rootdir + "/output_data") # # Data directory)
    #while True:
    wrapper.read_mopshub_adc_channels(hw =hw,
                                    bus_range = bus_range,#range(1,2), 
                                    file ="mops_config.yml", #Yaml configurations
                                    directory=rootdir+"/config_files", # direstory of the yaml file
                                    nodeId = NodeIds, # Node Id
                                    n_readings = n_readings,
                                    csv_writer =csv_writer,
                                    outputname = "mopshub_top_32bus", # Data file name
                                    outputdir = rootdir + "/output_data",
                                    timeout = timeout) # Number of Iterations          
def read_mon_values():
    adc_result = []
    #adc_result = [[int(), int()] for _ in range(4)]
    adc_out = []
    channel_value = ("UH", "IMON", "VCAN", "Temperature")
    address_byte = [0x80, 0x88, 0x90, 0x98, 0x80]    
    #wrapper.read_adc(hw =hw,bus_id = 0x0,timeout= timeout)
    print ("=========================READ Mon 0x88================================")
    cobid_ret, spi_id_ret, spi_reg_ret, adc_out =  wrapper.read_monitoring_uhal(hw =hw,
                                                                                 cobid =0x20,
                                                                                 spi_reg =0x88,
                                                                                 spi_id=0x0,
                                                                                 timeout=timeout, 
                                                                                 out_msg =True)
    for address in address_byte:
         time.sleep(0.1)
         print ("=========================READ Mon %d================================"%address)
         cobid_ret, spi_id_ret, spi_reg_ret, adc_out =  wrapper.read_monitoring_uhal(hw =hw,
                                                                                      cobid = 0x20,
                                                                                      spi_reg =address,
                                                                                      spi_id=0x0,
                                                                                      timeout=timeout, 
                                                                                      out_msg =True) 
def flush_mopshub_fifo():
    #Flush The FIFO
    print ("======================Flush The FIFO================================")
    wrapper.write_uhal_message(hw = hw, 
                                      node =wrapper.get_ual_node(hw =hw, registerName = "reg11"), 
                                      registerName="reg11", 
                                      data = 0x1, 
                                      timeout=timeout)  

def test_uhal_wrapper(bus = None,nodeId = None):
    #print ("=========================regcsr================================")
    #nodecsr = wrapper.get_ual_node(hw =hw, registerName = "regcsr")
    #await wrapper.write_uhal_message(hw = hw, node =nodecsr, data=5, registerName="regcsr", timeout=timeout)
    #await wrapper.read_uhal_message(node =nodecsr, registerName="regcsr", timeout=timeout)
    #print ("=========================Read Reg================================")

    print ("=========================read SDO================================")
    # data_point, reqmsg, requestreg, respmsg,responsereg , status =  wrapper.read_sdo_uhal(hw =hw,
    #                                                                                       SDO_TX = 0x600,
    #                                                                                       nodeId=nodeId, 
    #                                                                                       index=int(str(hex(0)),16),
    #                                                                                       subindex=0x0,
    #                                                                                       bus = bus,
    #                                                                                       timeout=timeout, 
    #                                                                                       out_msg =True)


    #Example (1): Read some Reg 
    #wait for interrupt
    print ("=========================READ Reg [reg0,reg1,reg2]================")
    #cobid, _, respmsg, responsereg, t = wrapper.read_uhal_mopshub_message(reg = ["reg0","reg1","reg2"], timeout=timeout)
    #check the situation
    #wrapper.read_uhal_message(hw = hw, node =wrapper.get_ual_node(hw =hw, registerName = "reg3"), registerName="reg3", timeout=0.1)
    print ("=========================READ Reg [reg3,reg4,reg5]================")
   # wrapper.read_uhal_mopshub_message(reg = ["reg3","reg4","reg5"], timeout=timeout)  
    print ("=========================READ Reg [reg6,reg7,reg8]================")
    #wrapper.read_uhal_mopshub_message(reg = ["reg6","reg7","reg8"], timeout=timeout) 
 
    #Example (2): write/read SDO message   
    print ("=========================write SDO message================")
    subindex=0xA
    data_point, reqmsg, requestreg, respmsg,responsereg , status =  wrapper.read_sdo_uhal(hw =hw,
                                                                                            nodeId=nodeId, 
                                                                                            index=0x2400,
                                                                                            subindex=subindex,
                                                                                            bus = bus,
                                                                                            timeout=timeout, 
                                                                                            out_msg =True)
    print(data_point, reqmsg, requestreg, respmsg,responsereg , status)

    # #  # PS. To visualise the data, Users can use the file $HOME/test_files/plot_adc.py
if __name__ == '__main__':
    # PART 1: Argument parsing
    uri = "ipbusudp-2.0://192.168.200.16:50001"
    addressFilePath = "config_files/ipbus_example.xml"
    wrapper = UHALWrapper(load_config = True)
    
    # PART 2: Creating the HwInterface
    hw = wrapper.config_uhal_hardware()
    bus = 1
    NodeIds = [0]
    #power On/off the bus
    #power_control(bus = bus)
    flush_mopshub_fifo()
    read_adc_iterations(n_readings = 10,bus_range = [1],NodeIds = NodeIds)
    #read_mon_values()
    #Test Uart
    #test_uart(bitrate = 115200)
