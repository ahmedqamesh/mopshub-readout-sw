########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 01.05.2023
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
import csv
from datetime import datetime
import atexit
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')

from analysis_utils      import AnalysisUtils
from analysis            import Analysis
from design_info         import DesignInfo
from mopshubGUI          import design_info_gui
from serial_wrapper_main import SerialServer
from logger_main   import Logger
import logging

log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format = log_format,name = "Test",console_loglevel=logging.INFO, logger_file = False)
logger = log_call.setup_main_logger()

timeout = 0.5
time_now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

output_dir = rootdir+"/output_dir/"+time_now
config_dir = rootdir+"/config_files/"

def debug_mopshub_uart(server =None, dut = "DUT",read_sm = ["0","1","2","3","4","5","6","7"]):   
    return_states = []
    for sm_id in read_sm:
        #Write to Uart 
        server.tx_data(bytearray(bytes.fromhex("0"+sm_id)))
        # Read from Uart
        time.sleep(timeout)
        Byte = server.rx_data() #read one byte
        #print(Byte.hex())
        # print info
        return_states = np.append(return_states,int(Byte.hex(),16))
        DesignInfo().get_sm_info(dut = dut,sm_id = int(sm_id,16), return_state = Byte)
        time.sleep(timeout)
    return return_states
    
def exit_handler():
# This function will be called on script termination
    logger.warning("Closing the program.") 
    sys.exit(0)

def read_mopshub_mopshubreadout_uartcombined(mopshub_server= None, mopshub_readout_server = None):
    mopshub_uart_outname = time_now + "_mopshub_top_16bus_debug"
    mopshub_readout_uart_outputname = time_now + "_mopshub_readout_16bus_debug"
    mopshub_csv_writer, mopshub_csv_file = AnalysisUtils().build_data_base(fieldnames=['Times','elabsed_time',"dec_code_err","dec_disp_err","dec10b_counter","rst_counter","enc10b_counter"],
                                                           outputname = mopshub_uart_outname, 
                                                           directory = output_dir+"_debug")        
    
    mopshub_readout_csv_writer, mopshub_readout_csv_file = AnalysisUtils().build_data_base(fieldnames=['Times','elabsed_time',"dec_code_err","dec_disp_err","dec10b_counter","rst_counter","enc10b_counter"],
                                                           outputname = mopshub_readout_uart_outputname, 
                                                           directory = output_dir+"_debug")  
    
    monitoringTime = time.time()
    i = 0
    # Register the termination signal handler
    atexit.register(exit_handler)
    try:
        while True:
                i = i+1
                mopshub_return_states = debug_mopshub_uart(server=mopshub_server , read_sm = ["0","1","2","3","4","5","6","7","8","9","A","B","C"],dut = "MOPS-Hub")
                mopshub_readout_return_states = debug_mopshub_uart(server=mopshub_readout_server ,read_sm = ["0","1","2","3","4","5","6","7","8","9","A","B","C"],dut = "Readout")
                
                file_time_now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
                ts = time.time()
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
            
        logger.notice("Debug data are saved to %s [%s -%s]" % (output_dir+"_debug",mopshub_uart_outname,mopshub_readout_uart_outputname)) 
             
def read_mopshub_uart_debug_channels(server = None):
    mopshub_uart_outname = time_now + "_mopshub_top_16bus_debug"#datetime.now().strftime('%Y-%m-%d_%H:%M:%S_') + "mopshub_top_16bus_debug"
    mopshub_csv_writer, mopshub_csv_file = AnalysisUtils().build_data_base(fieldnames=['Times','elabsed_time',"dec_code_err","dec_disp_err","dec10b_counter","rst_counter","enc10b_counter"],
                                                           outputname = mopshub_uart_outname, 
                                                           directory = output_dir+"_debug")        
    monitoringTime = time.time()
    i = 0
    # Register the termination signal handler
    atexit.register(exit_handler)
    try:
        while True:
                i = i+1
                mopshub_return_states = debug_mopshub_uart(server = server, read_sm = ["0","1","2","3","4","5","6","7","8","9","A","B","C"])
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
                mopshub_csv_file.flush() # Flush the buffer to update the file
                time.sleep(timeout)
                print(f"--------------------------------------------------------------------")
    except (KeyboardInterrupt):
        #Handle Ctrl+C to gracefully exit the loop
        logger.warning("User interrupted")
        sys.exit(1)      
    finally:
        mopshub_csv_writer.writerow((None,
                     str(None),
                     str(None),
                     str(None),
                     str(None),
                     str(None),
                     "End of Test"))  
    
        logger.notice("Debug data are saved to %s%s" % (output_dir+"_debug",mopshub_uart_outname)) 
    
#FTDI_FT232R_USB_UART_AU05XKFW
if __name__ == '__main__':
    #server = SerialServer(port="/dev/ttyUSB0", baudrate=115200,device =None)#"FT232R USB UART")11.53846
    mopshub_server = SerialServer(baudrate=115200,device = "FT232R USB UART")
    mopshub_readout_server = SerialServer(baudrate=115200,device = "CP2108 Interface 2")
    mopshub_server.list_available_ports(msg = True)

    verilog_files = ["spi_control_sm_fsm",
                    "bus_rec_sm_fsm",
                    "osc_trim_sm_fsm",
                    "can_interface_sm_fsm",
                    "can_elink_bridge_sm_fsm",
                    "elink_interface_tra_sm_fsm",
                    "elink_interface_rec_sm_fsm"]

    #Updating the yaml files with SM information
    DesignInfo().update_design_info(file_path = rootdir[:-18]+"/mopshub/mopshub_lib/hdl/", verilog_files = verilog_files)
    
    #Test Uart
    #debug_mopshub_uart(mopshub_readout_server, read_sm = ["0","1","2","3","4","5","6","7","8","9","A","B","C"])
    #debug_mopshub_uart(mopshub_server, read_sm = ["0","1","2","3","4","5","6","7","8","9","A","B","C"])
    #Loop Uart
    read_mopshub_uart_debug_channels(server = mopshub_server)
    #read_mopshub_mopshubreadout_uartcombined(mopshub_server= mopshub_server, mopshub_readout_server = mopshub_readout_server)
    
    
    