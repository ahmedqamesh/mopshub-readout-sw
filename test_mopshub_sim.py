########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 29.08.2023
"""
########################################################
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
import logging
from datetime import datetime
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from analysis_utils      import AnalysisUtils
from analysis            import Analysis
from design_info         import DesignInfo
from uhal_wrapper_main   import UHALWrapper
from logger_main   import Logger
from mopshubSimulation   import sim_mopshub_main, sim_mops_main   


log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="SIM Data", console_loglevel=logging.INFO, logger_file=False)
logger = log_call.setup_main_logger()

timeout = 0.05
time_now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

output_dir = rootdir+"/output_dir/"+time_now      
config_dir = rootdir+"/config_files/" 


def power_control(bus = None, voltage_control = [0x01,0x03,0x0F,0x33,0x3F,0xC3,0xCF,0xF3,0xFF]):
    #power On/off the bus
    for spi_select in bus:
        logger.info(f'Powering OFF[{spi_select:03X}]...')
        cobid = 0x31 -1
        power_reg6_hex = Analysis().binToHexa(bin(cobid)[2:].zfill(8)+
                                              bin(spi_select)[2:].zfill(8)+
                                              bin(0)[2:].zfill(8)+
                                              bin(0)[2:].zfill(8)) 
        sim_wrapper.write_sim_mopshub_message(hw =hw, data=[power_reg6_hex,power_reg6_hex,power_reg6_hex,0xa], reg = ["reg6","reg7","reg8","reg9"], timeout=timeout)
        time.sleep(0.1)
        logger.info(f'Powering ON[{spi_select:03X}]...')
        cobid = 0x31  
        for voltage in voltage_control:
            logger.info(f'Enable voltage:[{voltage:03X}]...')
            power_reg6_hex = Analysis().binToHexa(bin(cobid)[2:].zfill(8)+
                                                  bin(spi_select)[2:].zfill(8)+
                                                  bin(voltage)[2:].zfill(8)+
                                                  bin(0)[2:].zfill(8)) 
            sim_wrapper.write_sim_mopshub_message(hw =hw, data=[power_reg6_hex,power_reg6_hex,power_reg6_hex,0xa], reg = ["reg6","reg7","reg8","reg9"], timeout=timeout)  

def read_adc_iterations(n_readings = 1, bus_range = [1],NodeIds = None): 
    logger.info('Read ADC data...')
    #  #Example (3): Read all the ADC channels and Save it to a file in the directory output_dir    
    outputname = time_now + "mopshub_sim_16bus"
    csv_writer,csv_file = sim_wrapper.create_mopshub_adc_data_file(outputname = outputname, # Data file name
                                        outputdir = output_dir+"_sim") # # Data directory)

    sim_wrapper.read_mopshub_adc_channels(hw =hw,
                                    bus_range = bus_range,#range(1,2), 
                                    file ="mops_config.yml", #Yaml configurations
                                    directory=config_dir, # direstory of the yaml file
                                    nodeId = NodeIds, # Node Id
                                    n_readings = n_readings,
                                    csv_writer =csv_writer,
                                    csv_file = csv_file,
                                    outputname = outputname, # Data file name
                                    outputdir =  output_dir+"_sim",
                                    timeout = timeout) # Number of Iterations        
    
def conf_mon_values(bus=None):
    spi_select = Analysis().binToHexa(bin(bus)[2:].zfill(8))
    print ("=========================READ Mon 0x88================================")
    cobid_ret, spi_select_ret, spi_reg_ret, adc_out =  sim_wrapper.read_monitoring_uhal(hw =hw,
                                                                                 cobid =0x21,
                                                                                 spi_reg =0x88,
                                                                                 spi_select=spi_select,
                                                                                 timeout=timeout, 
                                                                                 out_msg =True)
         #read the response from the socket
    
    _frame  =  sim_wrapper.read_uhal_mopshub_message(reg = ["reg0","reg1","reg2"], 
                                                        timeout=timeout, 
                                                        out_msg = True) 
    _, msg_ret,respmsg_ret, responsereg_ret, t = _frame   
                                                                                
    flush_mopshub_fifo()
    for adc in adc_out[1:]:
        print(bin(adc)[2:].zfill(8))      
    
    return None

def read_mon_values(bus=None):
    adc_result = []
    #adc_result = [[int(), int()] for _ in range(4)]
    adc_out = []
    channel_value = ("UH", "IMON", "VCAN", "Temperature")
    address_byte = [0x80, 0x88, 0x90, 0x98]    
    spi_select = Analysis().binToHexa(bin(bus)[2:].zfill(8))
    #sim_wrapper.read_adc(hw =hw,bus_id = 0x0,timeout= timeout)

    adc_result = []
    for address in address_byte:
         print ("=========================READ Mon %s================================"%str(hex(address)))
         cobid_ret, spi_select_ret, spi_reg_ret, adc_out =  sim_wrapper.read_monitoring_uhal(hw =hw,
                                                                                      cobid = 0x20,
                                                                                      spi_reg =address,
                                                                                      spi_select=spi_select,
                                                                                      timeout=timeout, 
                                                                                      out_msg =True) 
    
    
         for adc in adc_out[1:]:
            print(bin(adc)[2:].zfill(8))   
        # Based on page 29 of the manual checking the last 8bits adc_out[4] will indicate the error and Channel
         # 1110 CI1 CI0 OD OF  this gives the following 3 channels [224(11100000),228(11100100),232 (11101000)] for voltages
         try:
             if adc_out[4] == 224 or adc_out[4] == 228 or adc_out[4] == 232:
                adc_result.append(round(((adc_out[2] * 256 + adc_out[3]) * 0.03814697 / 1000), 3))
                time.sleep(0.1)
             #the fourth channel [236 (11101100)] is for the temp
             elif adc_out[4]==236:
                v_ntc = round(((adc_out[2] * 256 + adc_out[3]) * 0.03814697 / 1000), 3)
                r_ntc = v_ntc * (20 / 4.75)
                # to calculate the resolution
                adc_result.append(round((298.15 / (1 - (298.15 / 3435) * np.log(10 / r_ntc))) - 273.15, 3))
                time.sleep(0.1)
             else:
                v_ntc = round(((adc_out[2] * 256 + adc_out[3]) * 0.03814697 / 1000), 3)
                r_ntc = v_ntc * (20 / 4.75)
                adc_result.append(round((298.15 / (1 - (298.15 / 3435) * np.log(10 / r_ntc))) - 273.15, 3))
                time.sleep(0.1)  
         except:
             pass
         #time.sleep(1)
    print(adc_result)

def test_sim_wrapper(bus = None,nodeId = None):
    # One CAN message requires bus, nodeId, index , subindex, 
    index=0x2400
    subindex=0xA
    data_point, reqmsg, requestreg, respmsg,responsereg , status =  sim_wrapper.read_sdo_sim(hw =hw,
                                                                                            nodeId=nodeId, 
                                                                                            index=index,
                                                                                            subindex=subindex,
                                                                                            bus = bus,
                                                                                            timeout=timeout, 
                                                                                            out_msg =True)
    print(data_point, reqmsg, requestreg, respmsg,responsereg , status)

if __name__ == '__main__':
    # PART 1: Argument parsing
    uri = "ipbusudp-2.0://192.168.200.16:50001"
    addressFilePath = "config_files/ipbus_example.xml"
    sim_wrapper = sim_mopshub_main.SIMMOPSHUB(load_config = True)
    
    # PART 2: Creating the HwInterface
    hw = sim_wrapper.config_sim_hardware()
    bus = 1
    voltage_control = [0x01,0x03,0x0F,0x33,0x3F,0xC3,0xCF,0xF3,0xFF]
    NodeIds = [0]
    #test_sim_wrapper(bus = bus,nodeId = NodeIds[0])
    #power On/off the bus
    #power_control(bus = [bus],voltage_control = [voltage_control[2]])
    read_adc_iterations(n_readings = 2,bus_range = [bus],NodeIds = NodeIds)
    #read_mon_values(bus = 1)
    #conf_mon_values(bus = 1)
