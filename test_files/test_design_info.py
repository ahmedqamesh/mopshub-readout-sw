########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 01.05.2023
"""
########################################################
import dash
from dash import Dash, html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash_bootstrap_components import themes
from dash_bootstrap_components._components.Button import Button
from dash_bootstrap_components._components.Col import Col
from dash_bootstrap_components._components.NavItem import NavItem
from dash_bootstrap_components._components.Row import Row
import plotly.graph_objects as go

import networkx as nx

class DesignInfoGui:
    def __init__(self, state_machines, transitions):
        self.state_machines = state_machines
        self.transitions = transitions
        self.app = dash.Dash(__name__)
        self.app.layout = html.Div([
            dcc.Dropdown(
                id='state-machine-dropdown',
                options=self._create_dropdown_options(),
                value=list(state_machines['state_machines'].keys())[0]
            ),
            dcc.Graph(id='state-machine-graph')
        ])

        # Define callback function
        self.app.callback(
            dash.dependencies.Output('state-machine-graph', 'figure'),
            dash.dependencies.Input('state-machine-dropdown', 'value')
        )(self.update_figure)

    def _create_dropdown_options(self):
        dropdown_options = [{'label': sm_data['sm_name'], 'value': sm_id} for sm_id, sm_data in self.state_machines['state_machines'].items()]
        return dropdown_options

    def generate_fsm_graph(self, state_machine_id):
        state_machine = self.state_machines['state_machines'][state_machine_id]
        transitions = self.transitions

        G = nx.DiGraph()
        for state_id, state_name in state_machine['sm_subindex_items'].items():
            G.add_node(state_name)

        for from_state, to_state in transitions:
            if from_state in state_machine['sm_subindex_items'].values() and to_state in state_machine['sm_subindex_items'].values():
                G.add_edge(from_state, to_state)

        return G

    def update_figure(self, selected_state_machine):
        selected_sm_data = self.state_machines['state_machines'][selected_state_machine]
        states = list(selected_sm_data['sm_subindex_items'].values())

        G = self.generate_fsm_graph(selected_state_machine)

        pos = nx.spring_layout(G, seed=42)

        scatter = go.Scatter(
            x=[pos[state][0] for state in states],
            y=[pos[state][1] for state in states],
            mode='markers',
            marker=dict(size=10, color='blue'),
            text=states,
            hoverinfo='text',
            showlegend=False,
        )

        arrows = self._create_arrows(G, pos, states)

        layout = go.Layout(
            title=selected_sm_data['sm_name'],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=arrows,
        )

        return {'data': [scatter], 'layout': layout}

    def _create_arrows(self, G, pos, states):
        arrows = []
        for from_state, to_state in G.edges():
            if from_state in states and to_state in states:
                x0, y0 = pos[from_state]
                x1, y1 = pos[to_state]
                arrow = dict(
                    xref='x',
                    yref='y',
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    arrowhead=3,
                    arrowsize=1.5,
                    arrowwidth=2,
                    arrowcolor='black',
                )
                arrows.append(arrow)
        return arrows

    def run(self):
        self.app.run_server(debug=True)

# Sample state machines and transitions as dictionaries
state_machines = {
    'state_machines': {
        '0': {
            'sm_name': 'State Machine 1',
            'file_name': 'can_elink_bridge_sm_fsm',
            'sm_subindex_items': {'0': 'State A', '1': 'State B', '2': 'State C'},
            'description_items': 'The Main State Machine'
        },
        '7': {
            'sm_name': 'State Machine 2',
            'file_name': 'None_sm_s',
            'sm_subindex_items': {'0': 'State X', '1': 'State Y', '2': 'State Z'},
            'description_items': 'The None State Machine'
        }
    }
}

transitions = [('State A', 'State B'), ('State B', 'State C'), ('State C', 'State A')]

# Create DesignInfoGui instance and run the app
design_gui = DesignInfoGui(state_machines, transitions)
design_gui.run()

