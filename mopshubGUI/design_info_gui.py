
import dash
from dash import Dash, html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash_bootstrap_components import themes
from dash_bootstrap_components._components.Button import Button
from dash_bootstrap_components._components.Col import Col
from dash_bootstrap_components._components.NavItem import NavItem
from dash_bootstrap_components._components.Row import Row

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
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yaml
rootdir = os.path.dirname(os.path.abspath(__file__)) 
lib_dir = rootdir[:-8]
config_dir = "config_files/"
mopsub_sm_yaml =config_dir + "mopshub_sm_config.yml" 
mopsub_conf_yaml =config_dir + "mopshub_config.yaml" 

log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format = log_format,name = "Design Info GUI",console_loglevel=logging.INFO, logger_file = False)



class DesignInfoGui:
    def __init__(self, state_machines,transitions_list):
        self.logger = log_call.setup_main_logger()
        self.state_machines = state_machines
        self.transitions_list = transitions_list
        self.app = dash.Dash(__name__)
        self.create_sm_window()


    def update_tree_view(self, selected_state_machine):
        tree_view = self.generate_tree_view(selected_state_machine)
        return tree_view

    def generate_tree_view(self, selected_state_machine):
        state_machine = self.state_machines[selected_state_machine]
        tree_view = html.Div([
            html.H4('MOPSHUB:'),
            html.Div(self.create_tree_node(state_machine))
        ])
        return tree_view
            
    def create_sm_window(self):
        self.app.layout = html.Div([
            html.H1('State Machine Visualization'),
            html.Div(id='state-machine-info'),
            dcc.Dropdown(
                id='state-machine-dropdown',
                options=self._create_dropdown_sm_options(),
                value=list(self.state_machines.keys())[0]
            ),
            dcc.Graph(
                id='state-machine-graph',
                responsive=True, 
                style={'display': 'block'},
                figure = self.blank_fig())
            
            ])

        # Define callback function
        self.app.callback(
            dash.dependencies.Output('state-machine-graph', 'figure'),
            dash.dependencies.Input('state-machine-dropdown', 'value')
        )(self.update_sm_figure)
        
        self.app.callback(
            Output('tree-view', 'children'),
            Input('state-machine-dropdown', 'value')
        )(self.update_tree_view)    
                    
    def blank_fig(self):
        fig = go.Figure(go.Scatter(x=[], y = []))
        fig.update_layout(template = None)
        fig.update_xaxes(showgrid = False, showticklabels = False, zeroline=False)
        fig.update_yaxes(showgrid = False, showticklabels = False, zeroline=False)
        return fig

    def _create_dropdown_sm_options(self):
        dropdown_options = [{'label': sm_data['sm_name'], 'value': sm_id} for sm_id, sm_data in self.state_machines['sm_items'].items()]
        return dropdown_options

    def update_sm_figure(self, selected_state_machine = "0"):
        selected_sm_data = self.state_machines['sm_items'][selected_state_machine]
        states = list(selected_sm_data['sm_subindex_items'].values())
        # Create the FSM graph using NetworkX
        fsm_graph = self.generate_fsm_graph(states, self.transitions_list)
        # Create scatter plot for the FSM nodes
        pos = nx.spring_layout(fsm_graph, seed=42)
         # Manually set the position of the 'waittoact' state to the center
        pos['ST_waittoact'] = [0, 0]
        pos['ST_endwait'] = [-0.3, 0.2]
        pos['ST_Abort'] = [-0.15, 0.15]
        #pos['ST_reset'] = [0.25, 0.25]

        # Generate the transition labels
        transition_labels = {(src, dst): f"{src} -> {dst}" for src, dst in self.transitions_list}

       
        x_values, y_values = zip(*pos.values())

        scatter = go.Scatter(
            x=x_values,
            y=y_values,
            mode='markers',
            marker=dict(size=10, color='blue'),
            text=list(pos.keys()),
            hoverinfo='text',
            showlegend=False,
        )
        
        # Create scatter plot for the FSM edges (transitions)
        edge_x = []
        edge_y = []
        for edge in fsm_graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=0.5, color='black'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )
        layout = go.Layout(
            title=selected_sm_data['sm_name'],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )

        return {'data': [scatter, edge_trace], 'layout': layout}

    def generate_fsm_graph(self, states, transitions):
        fsm_graph = nx.DiGraph()
        #fsm_graph.add_nodes_from(states)
        #fsm_graph.add_edges_from(transitions)
         # Add states to the graph
        for state in states:
            fsm_graph.add_node(state)
        # Add transitions to the graph
        for src, dst in transitions:
            fsm_graph.add_edge(src, dst)
        return fsm_graph
        
        node_colors = []
        for state in fsm_graph.nodes:
            if state == 'ST_waittoact' or state == 'ST_reset':
                node_colors.append('lightgreen')  # Set color for 'State0'
            elif state == 'ST_endwait':
                node_colors.append('red')  # Set color for 'State1'
            else:
                node_colors.append('lightblue')  # Default color for other states   
                
    def get_mopshub_config_info(self):
        with open(mopsub_conf_yaml, 'r') as config_file:
            config_data = yaml.safe_load(config_file)
        return config_data

    def create_banner(self, config_data):
        banner_text = [
            html.H3('MOPSHUB Configuration'),
            html.P(f"Crate ID: {config_data['Crate ID']}"),
            html.P(f"ADC Channel Default Converter: {config_data['ADC Channel Default Converter']}"),
            html.P(f"MOPS Default Location: {config_data['MOPS Default Location']}"),
          #  html.P(f"MOPS Default Status: {config_data['MOPS Default Status']}"),
          #  html.P(f"MOPS Default Port: {config_data['MOPS Default Port']}"),
          #  html.P(f"MOPS Configuration Default Trimming: {config_data['MOPS Configuration Default Trimming']}"),
           # html.H4('CICs to Populate:')
        ]

      #  for cic, cic_data in config_data['MOPSHUB'].items():
      #      banner_text.append(html.H5(f'CIC {cic}:'))
      #      for port, mops_data in cic_data.items():
      #          banner_text.append(html.P(f'Port {port}:'))
      #          for mops, mops_details in mops_data.items():
      #              banner_text.append(html.P(f'MOPS {mops}:'))
      #              for key, value in mops_details.items():
      #                  banner_text.append(html.P(f"{key}: {value}"))

        return html.Div(banner_text)
    
    
    def run(self):
        #reads the data from the mopshub_config.yaml file and stores it in a dictionary. 
        config_data = self.get_mopshub_config_info()
        #formats the data from the dictionary into an HTML banner.
        banner = self.create_banner(config_data)

        self.app.layout.children.insert(1, banner)
        self.app.run_server(debug=True, dev_tools_hot_reload=True)

