

from mopshub.logger_main import Logger 
from mopshub.analysis_utils import AnalysisUtils
import logging
import os
import numpy as np
import re
from graphviz import Digraph
import networkx as nx
import matplotlib.pyplot as plt
import mpldatacursor
rootdir = os.path.dirname(os.path.abspath(__file__)) 
lib_dir = rootdir[:-8]
config_dir = "config_files/"
mopsub_sm_yaml =config_dir + "mopshub_sm_config.yml" 

try:
    from logger_main   import Logger
except (ImportError, ModuleNotFoundError):
    from .logger_main   import Logger  
import logging
log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format = log_format,name = "Design Info ",console_loglevel=logging.INFO, logger_file = False)

class DesignInfo(object):
    def __init__(self,
                 file_loglevel=logging.INFO):
       
        super(DesignInfo, self).__init__()  # super keyword to call its methods from a subclass: 
        self._design_sm_info = AnalysisUtils().open_yaml_file(file= mopsub_sm_yaml, directory=lib_dir)
        self.logger = log_call.setup_main_logger()
    
    def get_sm_info(self, dut = "UART", sm_id = 0,return_state = None):
        _state_machines_dict = self._design_sm_info["state_machines"]
        _sm_items =  list(_state_machines_dict["sm_items"])
        _sm_name =  AnalysisUtils().get_info_yaml(dictionary=_state_machines_dict["sm_items"] , index=_sm_items[sm_id], subindex="sm_name")
        _file_name =  AnalysisUtils().get_info_yaml(dictionary=_state_machines_dict["sm_items"] , index=_sm_items[sm_id], subindex="file_name")
        _description_items = AnalysisUtils().get_info_yaml(dictionary=_state_machines_dict["sm_items"] , index=_sm_items[sm_id], subindex="description_items")
        _sm_subindex_items = list(AnalysisUtils().get_subindex_yaml(dictionary=_state_machines_dict["sm_items"], index=_sm_items[sm_id], subindex="sm_subindex_items"))
        _sm_return_state =AnalysisUtils().get_info_yaml(dictionary=_state_machines_dict["sm_items"], index=_sm_items[sm_id], subindex="sm_subindex_items")
        #print(_sm_return_state[return_state.hex()])
        try: 
            if sm_id !=7:_return_state = str(int(return_state.hex(),16))
            else:               
                try:_return_state = str(return_state.hex())
                except:
                    _return_state = "INVALID"
                    self.logger.warning(f'Detect invalid pattern {_return_state}')
            _return_state_int = str(int(return_state.hex(),16))
            self.logger.info(f'{dut}- ({_sm_items[sm_id]}) {_description_items}: {_sm_return_state[_return_state]} [{return_state.hex().upper()}]')
        except:
            _return_state_int = str(int(return_state.hex(),16))
            self.logger.info(f'{dut}- ({_sm_items[sm_id]}) {_description_items}: {_return_state}[{return_state.hex().upper()}]')
        
    def extract_transitions(self,verilog_file = None):
        file_name = os.path.basename(verilog_file)
        self.logger.report(f'Extracting Transitions between states in {file_name[:-2]}')
        with open(verilog_file, 'r') as file:
            
            #verilog_code = file.read()
            lines = file.readlines()
            # Process each line and extract the parameter values
            in_block = False
            next_state_block = False
            save_transition  = False
            result_dict = {}
            block_lines = []
            child_array = []
           
            parent_line = ''
            child_line = ''
            for i in range(len(lines)):
                line= lines[i].strip()  # Remove leading/trailing whitespaces
                if line.startswith(r'begin : next_state_block_proc'):
                    next_state_block = True
                if line.startswith(r'case (current_state)') and next_state_block:
                    in_block = True
                    continue
                elif line.startswith('default') or line.startswith('endcase'):
                    if in_block:
                        in_block = False
                        next_state_block = False
                        if block_lines:         
                            # Process the lines within the block and extract values                            
                            for block_line in block_lines:
                                parent_cond = (block_line.endswith('begin') 
                                               and not block_line.startswith('if') 
                                               and not block_line.startswith('else')
                                               )
                                child_cond= ('next_state' in block_line)
                                if child_cond:
                                    child_line = block_line.replace("next_state = ", "")
                                    
                                elif parent_cond:
                                    parent_line = block_line.replace(': begin', "") 
                                 # Assign values to "child" and "parent" in the block_dict
                                if parent_line:
                                    child_array = []
                                    parent_key = parent_line
                                    result_dict[parent_key] = child_array
                                elif parent_key:
                                    if child_line and child_line != parent_key:
                                        child_array.append(child_line)
                                # Reset child_line and parent_line variables
                                child_line = ''
                                parent_line = ''
                            block_lines.clear()

                    continue  
                if in_block:
                    line = line.rstrip(',;')  #Remove "," or ";" from the end of the line
                    block_lines.append(line)            
            transitions_list = [(src_state, dst_state) for src_state, dst_states in result_dict.items() for dst_state in dst_states]
            #for key, value in result_dict.items():
            #    print(key, ':', value)            
           # print(result_dict)    
        return result_dict, transitions_list


            
    def extract_states(self,verilog_file = None):
        with open(verilog_file, 'r') as file:
            #verilog_code = file.read()
            lines = file.readlines()
            # Define a dictionary to store the parameter values
            parameters = {}
            # Process each line and extract the parameter values
            parameter_found = False
            result_dict = {}
            for i in range(len(lines)):
                line= lines[i].strip()  # Remove leading/trailing whitespaces
                if line.startswith('parameter') and i < len(lines) - 1:
                    parameter_found = True
                elif parameter_found:
                    if line.endswith(';'):
                        line = line.rstrip(',;')  # Remove "," or ";" from the end of the line
                        key, value = line.split('=')  # Split the line at "="
                        key = key.strip()  # Remove leading/trailing whitespaces from the key
                        value = value.strip()  # Remove leading/trailing whitespaces from the value
                        for i in np.arange(4,10): value = value.replace(str(i)+"'d", "")#depends on the size of the statedeb
                        result_dict[value] = key
                        break      
                    else:
                        line = line.rstrip(',;')  # Remove "," or ";" from the end of the line
                        key, value = line.split('=')  # Split the line at "="
                        key = key.strip()  # Remove leading/trailing whitespaces from the key
                        value = value.strip()  # Remove leading/trailing whitespaces from the value
                        #value = value.replace("8'd", "")
                        for i in np.arange(4,10): value = value.replace(str(i)+"'d", "")#depends on the size of the statedeb
                        result_dict[value] = key

            # Print the dictionary
            #for key, value in result_dict.items():
            #    print(key, ':', value)
        return result_dict
                            
    def update_design_info(self,file_path = None, verilog_files = None):
        # Open the file and read its contents
        for file_name in verilog_files:
            states_dict = self.extract_states(verilog_file = file_path+file_name+".v") 
            #check the File match
            _state_machines_dict = self._design_sm_info["state_machines"]
            _sm_items =  list(_state_machines_dict["sm_items"])
            for sm_id in  _sm_items:
                _file_name =  AnalysisUtils().get_info_yaml(dictionary=_state_machines_dict["sm_items"] , index=_sm_items[int(sm_id)], subindex="file_name")
                if file_name == _file_name:
                    self.logger.info("Updating %s State Machine"%(_file_name))
                    for sm_key, sm_value in _state_machines_dict["sm_items"][sm_id].items():
                        if sm_key == "sm_subindex_items":
                            
                            self._design_sm_info["state_machines"]["sm_items"][sm_id]["sm_subindex_items"] = states_dict 
                            #print(_state_machines_dict["sm_items"][sm_id]["sm_subindex_items"])
                            AnalysisUtils().dump_yaml_file(file=mopsub_sm_yaml,
                                                           loaded = self._design_sm_info,
                                                           directory=lib_dir)
                else: 
                    pass
        self.logger.success("Saving State Machine Info to the file %s"%(mopsub_sm_yaml))
        
    def parse_verilog(self, verilog_file,states_dict):
        file_name = os.path.basename(verilog_file)
        self.logger.report(f'Parsing Transitions and States in {file_name[:-2]}')
        state_regex = r'state\s*(\w+)\s*;\s*'
        transition_regex = r'\s*([a-zA-Z_]\w*)\s*<=\s*(\w+)\s*;\s*'
        #case_regex = r'case\s*\(current_state\)\s*((?:\s*\w+\s*:\s*begin\s*\n\s*next_state\s*=\s*\w+;\s*\n\s*end\s*\n)+)\s*endcase'
        case_regex = r'case\s*\(current_state\)\s*([\s\S]*?)\s*endcase'
        states = set(states_dict.values())
        transitions = []
    
        with open(verilog_file, 'r') as f:
            content = f.read()
            transition_matches = re.findall(transition_regex, content)  
            for src, dst in transition_matches:
                src_state = states_dict.get(src)
                dst_state = states_dict.get(dst)
                if src_state and dst_state:
                    transitions.append((src_state, dst_state))
            
            case_match = re.search(case_regex, content)
            #print(case_match)
            if case_match:
                case_content = case_match.group(1)
                case_transitions = re.findall(transition_regex, case_content)
                #print("case_transitions",case_transitions)
                for src, dst in case_transitions:
                    
                    src_state = states_dict.get(src)
                    dst_state = states_dict.get(dst)
                    if src_state and dst_state:
                        transitions.append((src_state, dst_state))
    
        return states, transitions

    def generate_fsm_graph(self, states, transitions, output_file):
        file_name = os.path.basename(output_file)
        G = nx.DiGraph()
        # Add states to the graph
        for state in states:
            G.add_node(state)
        # Add transitions to the graph
        for src, dst in transitions:
            G.add_edge(src, dst)
        
        ## Generate the graph visualization
        #k (optimal distance between nodes)
        # iterations (number of iterations for the spring layout algorithm) parameters.
        pos = nx.spring_layout(G, seed=30, k=2, iterations=500)
        #pos = nx.random_layout(G)
        # Manually set the position of the 'waittoact' state to the center
        pos['ST_waittoact'] = [0, 0]
        pos['ST_endwait'] = [-0.3, 0.2]
        pos['ST_Abort'] = [-0.15, 0.15]
        #pos['ST_reset'] = [0.25, 0.25]
        node_colors = []
        for state in G.nodes:
            if state == 'ST_waittoact' or state == 'ST_reset':
                node_colors.append('lightgreen')  # Set color for 'State0'
            elif state == 'ST_endwait':
                node_colors.append('red')  # Set color for 'State1'
            else:
                node_colors.append('lightblue')  # Default color for other states
                
        # Generate the transition labels
        transition_labels = {(src, dst): f"{src} -> {dst}" for src, dst in transitions}
        
        plt.figure(figsize=(12, 8))
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color=node_colors, edgecolors='black')
        nx.draw_networkx_labels(G, pos, font_size=8)
        # Draw the edges with reversed order to change the direction of the arrows
        for dst, src in G.edges:
            nx.draw_networkx_edges(G, pos, edgelist=[(src, dst)], arrowstyle='->', arrowsize=6, edge_color='gray', arrows=True)
        labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, font_size=8, label_pos=0.3, rotate=False)
        # Create initial node labels
        state_labels = {state for state in states}
        
        def onclick(event,node_labels):
            # Generate the initial positions for the nodes
            pos = nx.spring_layout(G, seed=42, k=1.2, iterations=100)

            x, y = event.xdata, event.ydata
            if x is not None and y is not None:
                clicked_state = None
                for state, pos in pos.items():
                    dist = (pos[0] - x) ** 2 + (pos[1] - y) ** 2
                    if dist < 0.01:  # Adjust this threshold based on the desired click accuracy
                        clicked_state = state
                        break
        
                if clicked_state:
                    node_labels[clicked_state] = f"({x:.2f}, {y:.2f})"
                    plt.cla()
                    plt.axis('off')
                    nx.draw_networkx_nodes(G, pos, node_size=500, node_color='lightblue', edgecolors='black')
                    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)
                    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True)
                    mpldatacursor.datacursor(hover=True, point_labels=node_labels)

        #mpldatacursor.datacursor(hover=True,point_labels=transition_labels, formatter=lambda **kwargs: kwargs['label'])
    
        # Register the click event handler
        fig = plt.gcf()
        #fig.canvas.mpl_connect('button_press_event', lambda event: onclick(event, state_labels))

        plt.axis('off')
        #plt.show()
        # Save the graph to an image file
        plt.savefig(output_file, format='png', bbox_inches='tight')
        self.logger.success(f'Saving {file_name} State Machine plot at {output_file}')
        #plt.show()
        plt.clf() 
        plt.close(fig)
  
  
  