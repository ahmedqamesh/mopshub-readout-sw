########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 01.05.2023
"""
########################################################
# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')

from analysis_utils      import AnalysisUtils
from design_info         import DesignInfo
from mopshubGUI          import design_info_gui
design_info = DesignInfo()
time_now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
output_dir = rootdir+"/output_dir/"+time_now
config_dir = rootdir+"/config_files/"

if __name__ == '__main__':
    # Create DesignInfoGui instance and run the app
    # Sample state machines
     # Extract Information
    verilog_file = rootdir[:-18]+"/mopshub/mopshub_lib/hdl/can_elink_bridge_sm_fsm.v"  # Path to your Verilog file
    output_file =  rootdir[:-18]+"/mopshub/mopshub_lib/hdl/can_elink_bridge_sm_fsm.png"  # Output image file
    states_dict = design_info.extract_states(verilog_file = verilog_file)
    _, _transitions_dict = design_info.extract_transitions(verilog_file = verilog_file)
    states, transitions = design_info.parse_verilog(verilog_file, states_dict)
    design_info.generate_fsm_graph(states_dict.values(), _transitions_dict, verilog_file[:-1]+"png") 
    
    #design_sm_info = AnalysisUtils().open_yaml_file(file= config_dir + "mopshub_sm_config.yml" , directory=rootdir)
    #_state_machines_dict = design_sm_info["state_machines"]
    #design_info_gui = design_info_gui.DesignInfoGui(state_machines = _state_machines_dict, transitions_list = _transitions_dict)
    #design_info_gui.update_sm_figure(selected_state_machine = "0")
    #design_info_gui.run()
    
    