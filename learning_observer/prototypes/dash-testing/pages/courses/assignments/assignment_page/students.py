# package imports
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket

# local imports
import learning_observer_components as loc
from .options_offcanvas import offcanvas, open_btn, show_hide_options_checklist, show_hide_options_metric_checklist, show_hide_options_indicator_checklist

prefix = 'teacher-dashboard'

# add group
add_group_button = f'{prefix}-add-group-button'

def create_student_tab(assignment, students):
    # TODO remove the assignment parameter
    container = dbc.Container(
        [
            html.Div(
                [
                    dbc.Button(
                        [
                            html.I(className='fas fa-circle-plus me-1'),
                            'Create Groups'
                        ],
                        class_name='me-2',
                        color='secondary',
                        id=add_group_button,
                        title='Open create groups menu'
                    ),
                    open_btn,
                    dbc.Button(
                        [
                            html.I(className='fas fa-sort me-1'),
                            'Sort By: ',
                            html.Span('None', id='sort-by-dropdown-label')
                        ],
                        color='secondary',
                        id='sort-by-dropdown',
                        title='Arrange students by attributes'
                    ),
                    dbc.Popover(
                        [
                            dbc.PopoverHeader('Indicators:'),
                            dbc.PopoverBody(
                                dbc.RadioItems(
                                    options=[
                                        {'label': 'None', 'value': 'none'},
                                        {'label': 'Transition Words', 'value': 'transition_words'},
                                        {'label': 'Academic Language', 'value': 'academic_language'}
                                    ],
                                    value='none',
                                    id='sort-by-radioitems'
                                )
                            )
                        ],
                        target='sort-by-dropdown',
                        trigger='hover',
                        placement='bottom'
                    )
                ],
                className='my-2'
            ),
            dbc.Card(
                dbc.Row(
                    [
                        dbc.Col(
                            loc.StudentOverviewCard(
                                id={
                                    'type': 'student-card',
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
                                'type': 'student-col',
                                'index': s['id']
                            },
                            xxl=3,
                            lg=4,
                            md=6
                        ) for s in students
                    ],
                    class_name='g-3 p-3 w-100'
                ),
                color='light'
            ),
            # TODO change this to a variable instead of hard-coding
            # might want to move this to the the tab location as well to be used for all communication
            # on the teacher dashboard
            WebSocket(
                id='course-websocket',
                url=f'ws://127.0.0.1:5000/courses/students/{len(students)}'
            ),
            offcanvas,
            # TODO change this to a variable instead of hard-coding
            dcc.Store(
                id='student-counter',
                data=len(students)
            )
        ],
        fluid=True
    )
    return container


clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='populate_student_data'),
    Output({'type': 'student-card', 'index': ALL}, 'data'),
    Input('course-websocket', 'message'),
    State({'type': 'student-card', 'index': ALL}, 'data'),
    State('student-counter', 'data')
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='sort_students'),
    Output({'type': 'student-col', 'index': ALL}, 'class_name'),
    Output('sort-by-dropdown-label', 'children'),
    Input('sort-by-radioitems', 'value'),
    Input({'type': 'student-card', 'index': ALL}, 'data'),
    State('sort-by-radioitems', 'options'),
    State('student-counter', 'data')
)

# hide/show attributes
# TODO add the text information to this callback
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='show_hide_data'),
    Output({'type': 'student-card', 'index': ALL}, 'shown'),
    Input(show_hide_options_checklist, 'value'),
    Input(show_hide_options_metric_checklist, 'value'),
    Input(show_hide_options_indicator_checklist, 'value'),
    State('student-counter', 'data')
)
