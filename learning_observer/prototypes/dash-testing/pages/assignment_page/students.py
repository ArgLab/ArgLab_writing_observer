# package imports
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket

# local imports
import learning_observer_components as loc
from . import settings

prefix = 'teacher-dashboard'
student_card = f'{prefix}-student-card'
student_col = f'{prefix}-student_col'
student_grid = f'{prefix}-student-grid'
settings_collapse = f'{prefix}-settings-collapse'
websocket = f'{prefix}-websocket'
student_counter = f'{prefix}-student-counter'

def create_student_tab(assignment, students):
    container = dbc.Container(
        [
            html.Div(
                [
                    html.H3(
                        [
                            html.I(className='fas fa-file-lines me-2'),
                            assignment.name
                        ],
                        className='d-inline'
                    ),
                    html.Div(
                        [
                            settings.open_btn
                        ],
                        className='float-end'
                    ),
                    html.Br(),
                    html.P(assignment.description, className='font-size-sm')
                ],
                className='my-1'
            ),
            dbc.Row(
                [
                    dbc.Collapse(
                        dbc.Col(
                            settings.panel,
                            class_name='w-100 h-100'
                        ),
                        id=settings_collapse,
                        class_name='collapse-horizontal col-xxl-3 col-lg-4 col-md-6',
                        is_open=False
                    ),
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Col(
                                    loc.StudentOverviewCard(
                                        id={
                                            'type': student_card,
                                            'index': s['id']
                                        },
                                        name=s['name'],
                                        data={
                                            'indicators': [],
                                            'metrics': [],
                                            'text': ''
                                        },
                                        shown=['transition_words', 'academic_language', 'sentences', 'text'],
                                        class_name='shadow-card'
                                    ),
                                    id={
                                        'type': student_col,
                                        'index': s['id']
                                    },
                                ) for s in students
                            ],
                            class_name='g-3 p-1 p-md-3 w-100'
                        ),
                        id=student_grid,
                        # classname set in callback
                    )
                ],
                class_name='g-0'
            ),
            WebSocket(
                id=websocket,
                url=f'ws://127.0.0.1:5000/courses/students/{len(students)}'
            ),
            dcc.Store(
                id=student_counter,
                data=len(students)
            )
        ],
        fluid=True
    )
    return container

    
# open the offcanvas show/hide options checklist
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='open_offcanvas'),
    Output(settings_collapse, 'is_open'),
    Output({'type': student_col, 'index': ALL}, 'class_name'),
    Output(student_grid, 'class_name'),
    Input(settings.show_hide_settings_open, 'n_clicks'),
    Input(settings.close_settings, 'n_clicks'),
    State(settings_collapse, 'is_open'),
    State(student_counter, 'data')
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='populate_student_data'),
    Output({'type': student_card, 'index': ALL}, 'data'),
    Input(websocket, 'message'),
    State({'type': student_card, 'index': ALL}, 'data'),
    State(student_counter, 'data')
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='sort_students'),
    Output({'type': student_col, 'index': ALL}, 'style'),
    Input(settings.sort_by_checklist, 'value'),
    Input(settings.sort_toggle, 'value'),
    Input({'type': student_card, 'index': ALL}, 'data'),
    State(settings.sort_by_checklist, 'options'),
    State(student_counter, 'data')
)

# hide/show attributes
# TODO add the text radio items to this callback
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='show_hide_data'),
    Output({'type': student_card, 'index': ALL}, 'shown'),
    Input(settings.show_hide_settings_checklist, 'value'),
    Input(settings.show_hide_settings_metric_checklist, 'value'),
    Input(settings.show_hide_settings_indicator_checklist, 'value'),
    State(student_counter, 'data')
)
