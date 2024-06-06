#!/bin/env python
import math
import random # For randint
import sys # For sys.argv and sys.exit
import numpy as np
import time
import os
import binascii
import struct
import time
import serial
import atexit
from datetime import datetime
import logging
from collections import deque, Counter
from tqdm import tqdm
import ctypes as ct
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')

from analysis_utils      import AnalysisUtils
from analysis            import Analysis
from design_info         import DesignInfo
from serial_wrapper_main import SerialServer
from logger_main   import Logger
from uhal_wrapper_main import UHALWrapper
log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="UHAL Data", console_loglevel=logging.INFO, logger_file=False)
logger = log_call.setup_main_logger()

timeout = 0.05
time_now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

output_dir = rootdir+"/output_dir/"+time_now
config_dir = rootdir+"/config_files/"

def exit_handler():
# This function will be called on script termination
    logger.warning("Closing the program.") 
    sys.exit(0)

def read_mopshub_mopshubreadout_transmission(mopshub_server= None, mopshub_readout_server = None,nodeIds = [0],bus_range = [0],hw=None):
    mopshub_uart_outname            = time_now + "_mopshub_top_16bus_debug"
    mopshub_readout_uart_outputname = time_now + "_mopshub_readout_16bus_debug"
    mopshub_uhal_outputname         = time_now + "_mopshub_top_16bus_seu_test"
    
    mopshub_csv_writer, mopshub_csv_file = AnalysisUtils().build_data_base(fieldnames=['Times','elabsed_time',"dec_code_err","dec_disp_err","dec10b_counter","rst_counter","enc10b_counter"],
                                                           outputname = mopshub_uart_outname, 
                                                           directory = output_dir+"_debug")        
    
    mopshub_readout_csv_writer, mopshub_readout_csv_file = AnalysisUtils().build_data_base(fieldnames=['Times','elabsed_time',"dec_code_err","dec_disp_err","dec10b_counter","rst_counter","enc10b_counter"],
                                                           outputname = mopshub_readout_uart_outputname, 
                                                           directory = output_dir+"_debug")  
    
    csv_writer_uhal,csv_file_uhal = AnalysisUtils().build_data_base( fieldnames = ['Times','elabsed_time',"test_tx",'bus_id',"nodeId","adc_ch","index","sub_index","adc_data", "adc_data_converted","reqmsg","requestreg","respmsg","responsereg", "status"],
                                                                          outputname = mopshub_uhal_outputname, 
                                                                           directory =output_dir+"_uhal" ) # # Data directory)
        
    dev = AnalysisUtils().open_yaml_file(file="mops_config.yml", directory=config_dir)
    _adc_channels_reg = dev["adc_channels_reg"]["adc_channels"]
    _adc_index = list(dev["adc_channels_reg"]["adc_index"])[0]
    _channelItems = [int(channel) for channel in list(_adc_channels_reg)]
    
       
    monitoringTime = time.time()
    i = 0
    # Register the termination signal handler
    atexit.register(exit_handler)
    try:
        while True:
                i = i+1
                mopshub_return_states = mopshub_server.debug_mopshub_uart(read_sm = ["0","1","2","3","4","5","6","7","8","9","A","B","C"],dut = "MOPS-Hub")
                mopshub_readout_return_states = mopshub_readout_server.debug_mopshub_uart(read_sm = ["0","1","2","3","4","5","6","7","8","9","A","B","C"],dut = "Readout")
                for bus in bus_range:
                    for node in nodeIds:    
                        # Read ADC channels
                        for c in tqdm(np.arange(len(_channelItems)),colour="green"):
                            channel =  _channelItems[c]
                            subindex = channel - 2
                            data_point, reqmsg, requestreg, respmsg,responsereg , status =  wrapper.read_sdo_uhal(hw =hw,
                                                                                                               bus = bus, 
                                                                                                               nodeId= node, 
                                                                                                               index = int(_adc_index, 16), 
                                                                                                               subindex = subindex, 
                                                                                                               timeout = timeout,
                                                                                                               seu_test = True,
                                                                                                               out_msg = False)                   
                            if data_point is not None:
                                adc_converted = Analysis().adc_conversion(_adc_channels_reg[str(channel)], data_point)
                                adc_converted = round(adc_converted, 3)
                                logger.info(f'[{i}|{bus}] Got data for channel {channel} [{hex(subindex)}]: = {adc_converted}')
                            else:
                                adc_converted = None
                                                
                ts = time.time()
                file_time_now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
                elapsedtime = ts - monitoringTime      
                mopshub_csv_writer.writerow((str(file_time_now),
                                     str(elapsedtime),
                                     str(mopshub_return_states[8]),
                                     str(mopshub_return_states[9]),
                                     str(mopshub_return_states[10]), 
                                     str(mopshub_return_states[11]),
                                     str(mopshub_return_states[12])))        
                
                mopshub_readout_csv_writer.writerow((str(file_time_now),
                                     str(elapsedtime),
                                     str(mopshub_readout_return_states[8]),
                                     str(mopshub_readout_return_states[9]),
                                     str(mopshub_readout_return_states[10]), 
                                     str(mopshub_readout_return_states[11]),
                                     str(mopshub_readout_return_states[12])))   
                  
                
                csv_writer_uhal.writerow((str(file_time_now),
                                     str(elapsedtime),
                                     str(1),
                                     str(bus),
                                     str(node),
                                     str(channel),
                                     str(_adc_index),
                                     str(subindex),
                                     str(data_point),
                                     str(adc_converted),
                                     str(reqmsg),
                                     str(requestreg), 
                                     str(respmsg),
                                     str(responsereg), 
                                     status))
                csv_file_uhal.flush() 
                mopshub_csv_file.flush() # Flush the buffer to update the file
                mopshub_readout_csv_file.flush() # Flush the buffer to update the file
                time.sleep(timeout)
                print(f"----------------------------------------------------------------------------")
    except (KeyboardInterrupt):
        #Handle Ctrl+C to gracefully exit the loop
        logger.warning("User interrupted")
        sys.exit(1)      
    finally:
        ts = time.time()
        elapsedtime = ts - monitoringTime  
        mopshub_csv_writer.writerow((str(time_now),
                     str(elapsedtime),
                     str(None),
                     str(None),
                     str(None),
                     str(None),
                     "End of Test"))  

        mopshub_readout_csv_writer.writerow((str(time_now),
                     str(elapsedtime),
                     str(None),
                     str(None),
                     str(None),
                     str(None),
                     "End of Test"))  

        csv_writer_uhal.writerow((str(time_now),
                     str(elapsedtime),
                     str(1),
                     str(None),
                     str(None),
                     str(None),
                     str(None),
                     str(None),
                     str(None),
                     str(None),
                     str(None),
                     str(None), 
                     str(None),
                     str(None), 
                     "End of Test"))  
                        
        logger.notice("Debug data are saved to %s [%s - %s - %s ]" % (output_dir+"_debug",mopshub_uart_outname,mopshub_readout_uart_outputname,mopshub_uhal_outputname)) 

def flush_mopshub_fifo():
    #Flush The FIFO
    logger.info('Flush The FIFO...')
    wrapper.write_uhal_message(hw = hw, 
                                      node =wrapper.get_ual_node(hw =hw, registerName = "reg11"), 
                                      registerName="reg11", 
                                      data = 0x1, 
                                      timeout=timeout)  

if __name__ == '__main__':
    # PART 1: Argument parsing
    wrapper = UHALWrapper(load_config = True)
    mopshub_server = SerialServer(baudrate=115200,device = "FT232R USB UART")
    mopshub_readout_server = SerialServer(baudrate=115200,device = "CP2108 Interface 2")#"FT232R USB UART")
    mopshub_server.avail_ports(msg = True)

    # PART 2: Creating the HwInterface
    hw = wrapper.config_uhal_hardware()
    nodeIds = [0]
    bus_range = [0]#,1,2,3,4,5,6]
    flush_mopshub_fifo()
    read_mopshub_mopshubreadout_transmission(mopshub_server= mopshub_server, mopshub_readout_server = mopshub_readout_server,bus_range = bus_range,nodeIds = nodeIds,hw = hw)
        
    