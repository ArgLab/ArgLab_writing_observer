# package imports
import dash
from dash import html, dcc, clientside_callback, ClientsideFunction, callback, Output, Input, State, ALL, MATCH
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket

# local imports
from data import students as s_data

dash.register_page(
    __name__,
    path='/dashboard',
    title='Dashboard'
)

def create_analysis_card(analysis):
    id = analysis.get('id')
    card = dbc.Col(
        dbc.Card(
            [
                dcc.Graph(
                    id={
                        'type': 'analysis-graph',
                        'index': id
                    },
                    className='m-2'
                ),
                WebSocket(
                    id={
                        'type': 'analysis-ws',
                        'index': id
                    },
                    url=f'ws://127.0.0.1:5000/analysis/{id}'
                )
            ],
            color='light',
            class_name='h-100'
        ),
        class_name='h-100',
        xxl=6,
        lg=6
    )
    return card


def create_student_card(s):
    id = s.get('id')
    card = html.Div(
        [
            dbc.Card(
                [
                    html.H4(s.get('name')),
                    html.Div(
                        [
                            dbc.Badge(
                                id={
                                    'type': 'student-card-sentence-badge',
                                    'index': id
                                },
                                color='info'
                            ),
                            dbc.Badge(
                                id={
                                    'type': 'student-card-paragraph-badge',
                                    'index': id
                                },
                                color='info'
                            )
                        ],
                        className='d-flex justify-content-around'
                    ),
                    html.P(
                        id={
                            'type': 'student-card-data',
                            'index': id
                        }
                    )
                ],
                body=True,
                id={
                    'type': 'student-card',
                    'index': id
                }
            ),
            WebSocket(
                id={
                    'type': 'student-ws',
                    'index': id
                },
                url=f'ws://127.0.0.1:5000/student/{id}'
            )
        ],
        className='my-2 mx-1',
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
                    [create_student_card(s) for s in students] if students else [],
                    id={
                        'index': name.lower().replace(' ', '-'),
                        'type': 'group-card'
                    },
                    style={'minHeight': '200px'}
                )
            ],
            color='light',
            class_name='h-100 overflow-auto'
        ),
        class_name='h-100',
        xxl=4,
        lg=4,
        md=6
    )
    return card


assignment_1 = dbc.Container(
    [
        html.H2(
            [
                html.P(
                    'Analysis',
                    className='d-inline'
                ),
                dbc.Button(
                    html.I(className='far fa-plus fs-5'),
                    class_name='ms-2',
                    color='secondary',
                    id='add-analysis-button'
                )
            ]
        ),
        dbc.Row(
            [
                create_analysis_card({'name': 'Sample', 'id': 'scatter'}),
                # dbc.Col(
                #     dbc.Card(
                #         dbc.Button(
                #             html.I(className='far fa-plus display-5 mx-1'),
                #             class_name='m-auto',
                #             color='secondary',
                #             id='add-analysis-button'
                #         ),
                #         color='light',
                #         class_name='h-100'
                #     ),
                #     class_name='h-100',
                #     xxl=4,
                #     lg=6
                # )
            ],
            id='analysis-row',
            class_name='g-3',
        ),
        html.H2(
            [
                html.P(
                    'Groups',
                    className='mt-1 d-inline'
                ),
                dbc.Button(
                    [
                        html.I(className='fas fa-gear me-1'),
                        'Options'
                    ],
                    class_name='ms-2',
                    color='secondary',
                    id='group-options-button'
                )
            ]
        ),
        dbc.Row(
            [
                create_group_card('Ungrouped', s_data),
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
                    class_name='h-100',
                    xxl=4,
                    lg=4,
                    md=6
                )
            ],
            id='group-row',
            class_name='g-3',
            style={'height': '65vh'}
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
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle('Add Analysis')),
                dbc.ModalBody(
                    [
                        html.H6('Type'),
                        dcc.Dropdown(
                            id='add-analysis-modal-dropdown',
                            placeholder='Select analysis type...',
                            options=[
                                {'label': 'Bar chart', 'value': 'bar'},
                                {'label': 'Scatter plot', 'value': 'scatter'},
                            ]
                        )
                    ]
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        [
                            html.I(className='far fa-plus me-2'),
                            'Add'
                        ],
                        id='add-analysis-modal-create-button',
                        color='secondary'
                    )
                )
            ],
            id='add-analysis-modal',
            is_open=False
        ),
        dbc.Offcanvas(
            [
                'Options'
            ],
            id='offcanvas',
            title='Display options',
            is_open=False
        )
    ],
    class_name='mb-5'
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
    Output('add-analysis-modal', 'is_open'),
    Input('add-analysis-button', 'n_clicks'),
    State('add-analysis-modal', 'is_open'),
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open


@callback(
    Output('group-row', 'children'),
    Output('add-group-modal-name', 'value'),
    Output('add-group-modal-student-dropdown', 'value'),
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
    return groups, None, None


@callback(
    Output('analysis-row', 'children'),
    Output('add-analysis-modal-dropdown', 'value'),
    Input('add-analysis-modal-create-button', 'n_clicks'),
    State('add-analysis-modal-dropdown', 'value'),
    State('analysis-row', 'children')
)
def add_analysis(clicks, analysis, items):
    if clicks is None or analysis is None:
        raise PreventUpdate
    
    new_group = create_analysis_card({'name': 'Sample', 'id': analysis})
    items.append(new_group)
    return items, None


# make groups draggable
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='make_draggable'),
    Output('group-row', 'data-drag'),
    Input({'type': 'group-card', 'index': ALL}, 'id')
)
# populate student data
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='update_student_card'),
    Output({'type': 'student-card-data', 'index': MATCH}, 'children'),
    Output({'type': 'student-card', 'index': MATCH}, 'class_name'),
    Output({'type': 'student-card-sentence-badge', 'index': MATCH}, 'children'),
    Output({'type': 'student-card-paragraph-badge', 'index': MATCH}, 'children'),
    Input({'type': 'student-ws', 'index': MATCH}, 'message')
)
# populate graph data
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='update_analysis_data'),
    Output({'type': 'analysis-graph', 'index': MATCH}, 'figure'),
    Input({'type': 'analysis-ws', 'index': MATCH}, 'message')
)
