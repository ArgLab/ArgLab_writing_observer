# package imports
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket

# local imports
import learning_observer_components as loc

prefix = 'teacher-dashboard'

# add group
add_group_button = f'{prefix}-add-group-button'

# offcanvas options
show_hide_options_open = f'{prefix}-show-hide-open-button'
show_hide_options_offcanvas = f'{prefix}-show-hide-offcanvcas'
show_hide_options_checklist = f'{prefix}-show-hide-checklist'
show_hide_options_progress_collapse = f'{prefix}-show-hide-progress-collapse'
show_hide_options_progress_checklist = f'{prefix}-show-hide-progress-checklist'
offcanvas = dbc.Offcanvas(
    [
        html.H4('Student Card'),
        dcc.Checklist(
            # TODO add tooltips to every option
            options=[
                # TODO make a collapsible metric item
                {
                    'label': 'Metrics',
                    'value': 'metrics'
                },
                {
                    'label': dbc.Badge('# sentences', color='info', class_name='fs-6 m-2'),
                    'value': 'sentences'
                },
                {
                    'label': dbc.Badge('# words in 5 minutes', color='info', class_name='fs-6 m-2'),
                    'value': 'edits_per_min'
                },
                {
                    'label': dbc.Badge('# minutes since last edit', color='info', class_name='fs-6 m-2'),
                    'value': 'since_last_edit'
                },
                # TODO text needs to be more general like first/second paragraph
                {
                    'label': html.Span('Summary text', className='fs-5 m-2'),
                    'value': 'text'
                },
                {
                    'label': html.Span(
                        [
                            html.I(className='fas fa-chart-bar me-1'),
                            'Indicators overview'
                        ],
                        className='fs-5 m-2'
                    ),
                    'value': 'indicators'
                }
            ],
            value=['sentences', 'edits_per_min', 'text', 'indicators', 'metrics'],
            id=show_hide_options_checklist,
            labelClassName='d-block'
        ),
        dbc.Collapse(
            dcc.Checklist(
                # TODO-options abstract the analysis options into a file in /components
                options=[
                    {
                        'label': html.Span('Transition Words', className='fs-6 m-2'),
                        'value': 'transition_words'
                    },
                    {
                        'label': html.Span('Academic Language', className='fs-6 m-2'),
                        'value': 'academic_language'
                    },
                ],
                value=['transition_words', 'academic_language'],
                id=show_hide_options_progress_checklist,
                labelClassName='d-block',
                className='ms-3'
            ),
            id=show_hide_options_progress_collapse
        )
    ],
    id=show_hide_options_offcanvas,
    title='Display options',
    is_open=False
)


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
                        id=add_group_button
                    ),
                    dbc.Button(
                        [
                            html.I(className='fas fa-gear me-1'),
                            'Options'
                        ],
                        class_name='me-2',
                        color='secondary',
                        id=show_hide_options_open
                    ),
                    dbc.Button(
                        [
                            html.I(className='fas fa-sort me-1'),
                            'Sort By: ',
                            html.Span('None', id='sort-by-dropdown-label')
                        ],
                        color='secondary',
                        id='sort-by-dropdown'
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
                                shown=['transition_words', 'academic_language', 'sentences', 'text']
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


# open the offcanvas show/hide options checklist
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='open_offcanvas'),
    Output(show_hide_options_offcanvas, 'is_open'),
    Input(show_hide_options_open, 'n_clicks'),
    State(show_hide_options_offcanvas, 'is_open')
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_indicators_checklist'),
    Output(show_hide_options_progress_collapse, 'is_open'),
    Input(show_hide_options_checklist, 'value')
)

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
    State('sort-by-radioitems', 'options'),
    State('student-counter', 'data'),
    State({'type': 'student-card', 'index': ALL}, 'data')
)

# hide/show attributes
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='show_hide_data'),
    Output({'type': 'student-card', 'index': ALL}, 'shown'),
    Input(show_hide_options_checklist, 'value'),
    Input(show_hide_options_progress_checklist, 'value'),
    State('student-counter', 'data')
)
