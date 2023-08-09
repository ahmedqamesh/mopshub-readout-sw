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
lib_dir = rootdir
config_dir = "config_files/"
mopsub_sm_yaml =config_dir + "mopshub_sm_config.yml" 
from analysis_utils      import AnalysisUtils
from analysis            import Analysis
from design_info         import DesignInfo
from mopshubGUI          import design_info_gui
from uhal_wrapper_main   import UHALWrapper

timeout = 0.05
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
    
    
if __name__ == '__main__':
    # Sample state machines
    design_sm_info = AnalysisUtils().open_yaml_file(file= mopsub_sm_yaml, directory=lib_dir)
    _state_machines_dict = design_sm_info["state_machines"]
    
    verilog_files = ["spi_control_sm_fsm",
                    "bus_rec_sm_fsm",
                    "osc_trim_sm_fsm",
                    "can_interface_sm_fsm",
                    "can_elink_bridge_sm_fsm",
                    "elink_interface_tra_sm_fsm",
                    "elink_interface_rec_sm_fsm"]

    #Test Uart
    test_uart(bitrate = 115200)
 
    sm_info.update_design_info(file_path = rootdir[:-18]+"/mopshub/mopshub_lib/hdl/", 
                               verilog_files = verilog_files)
    
     # Main code
    verilog_file = rootdir[:-18]+"/mopshub/mopshub_lib/hdl/can_elink_bridge_sm_fsm.v"  # Path to your Verilog file
    output_file =  rootdir[:-18]+"/mopshub/mopshub_lib/hdl/can_elink_bridge_sm_fsm.png"  # Output image file
    states_dict = sm_info.extract_states(verilog_file = verilog_file)
    _, transitions_list = sm_info.extract_transitions(verilog_file = verilog_file)
    #states, transitions = sm_info.parse_verilog(verilog_file, states_dict)
    
    #sm_info.generate_fsm_graph(states_dict.values(), transitions_list, output_file)    

    # Create DesignInfoGui instance and run the app
    #sm_info_gui = design_info_gui.DesignInfoGui(state_machines = _state_machines_dict, transitions_list = transitions_list)
    #sm_info_gui.update_sm_figure(selected_state_machine = "0")
    #sm_info_gui.run()
    
    
    