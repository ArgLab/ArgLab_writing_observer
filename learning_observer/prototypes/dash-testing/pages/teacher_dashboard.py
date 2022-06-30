# package imports
import dash
from dash import html, dcc, clientside_callback, ClientsideFunction, callback, Output, Input, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import random

# local imports
from data import students as s_data

dash.register_page(
    __name__,
    path='/dashboard',
    title='Dashboard'
)

def create_student_card(s):
    card =dbc.Card(
        [
            html.H4(s.get('name')),
            html.P(s.get('text'))
        ],
        outline=True,
        body=True,
        class_name='my-2 mx-1'
    )
    return card


def create_group_card(name, students):
    card = dbc.Col(
        dbc.Card(
            [
                html.H3(
                    name,
                    className='text-center my-2'
                ),
                html.Div(
                    [create_student_card(s) for s in random.sample(s_data, random.randint(1, int(len(s_data)/2)))] if s_data else [],
                    id=name.lower().replace(' ', '-')
                )
            ],
            color='light',
            class_name='h-100 overflow-auto'
        ),
        class_name='h-100',
        xxl=3,
        lg=4,
        md=6
    )
    return card


assignment_1 = dbc.Container(
    [
        dbc.Row(
            [
                create_group_card('Group 1', []),
                create_group_card('Group 2', []),
                dbc.Col(
                    dbc.Card(
                        dbc.Button(
                            html.I(className='far fa-plus display-5 mx-1'),
                            class_name='m-auto',
                            color='secondary',
                            id='add-group-button'
                        ),
                        color='light',
                        class_name='h-100'
                    ),
                    xxl=3,
                    lg=4,
                    md=6
                )
            ],
            id='group-row',
            class_name='g-3 mt-1',
            style={'height': '80vh'}
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle('Add Group')),
                dbc.ModalBody(
                    [
                        html.H6('Group name'),
                        dbc.Input(
                            id='add-group-modal-name',
                            placeholder='Group name...',
                            type='text',
                            class_name='my-2'
                        ),
                        html.H6('Add students'),
                        dcc.Dropdown(
                            id='add-group-modal-student-dropdown',
                            placeholder='Select students...',
                            multi=True
                        )
                    ]
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        [
                            html.I(className='far fa-plus me-2'),
                            'Add'
                        ],
                        id='add-group-modal-create-button',
                        color='secondary'
                    )
                )
            ],
            id='add-group-modal',
            is_open=False
        )
    ]
)

layout = dbc.Tabs(
    [
        dbc.Tab(
            assignment_1,
            label='Assignment 1',
            tab_id='assignment_1'
        ),
        dbc.Tab(
            '',
            label='Assignment 2',
            disabled=True
        )
    ],
    active_tab='assignment_1'
)

@callback(
    Output('add-group-modal', 'is_open'),
    Input('add-group-button', 'n_clicks'),
    State('add-group-modal', 'is_open'),
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open

@callback(
    Output('group-row', 'children'),
    Input('add-group-modal-create-button', 'n_clicks'),
    State('add-group-modal-name', 'value'),
    State('add-group-modal-student-dropdown', 'value'),
    State('group-row', 'children')
)
def add_group(clicks, name, students, groups):
    if clicks is None or name is None:
        raise PreventUpdate
    
    new_group = create_group_card(name, students)
    groups.insert(len(groups)-1, new_group)
    return groups

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='make_draggable'),
    Output('group-row', 'data-drag'),
    Input('group-1', 'id'),
    Input('group-2', 'id')
)
