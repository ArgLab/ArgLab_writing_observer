# package imports
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket

# local imports
from .student_card_aio import StudentCardAIO

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
                {
                    'label': dbc.Badge('# sentences', color='info', class_name='fs-6 m-2'),
                    'value': 'sentences'
                },
                {
                    'label': dbc.Badge('# paragraphs', color='info', class_name='fs-6 m-2'),
                    'value': 'paragraphs'
                },
                {
                    'label': dbc.Badge('time on task', color='info', class_name='fs-6 m-2'),
                    'value': 'time_on_task'
                },
                {
                    'label': dbc.Badge('# unique words', color='info', class_name='fs-6 m-2'),
                    'value': 'unique_words'
                },
                {
                    'label': html.Span('Summary text', className='fs-5 m-2'),
                    'value': 'text'
                },
                {
                    'label': html.Span(
                        [
                            html.I(className='fas fa-chart-bar me-1'),
                            'Metric overview'
                        ],
                        className='fs-5 m-2'
                    ),
                    'value': 'progress'
                }
            ],
            value=['sentences', 'paragraphs', 'text', 'progress'],
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
                        'label': html.Span('Effective Use of Synonyms', className='fs-6 m-2'),
                        'value': 'use_of_synonyms'
                    },
                    {
                        'label': html.Span('Subject Verb Agreement', className='fs-6 m-2'),
                        'value': 'sv_agreement'
                    },
                    {
                        'label': html.Span('Formal Language', className='fs-6 m-2'),
                        'value': 'formal_language'
                    },
                ],
                value=['transition_words', 'use_of_synonyms', 'sv_agreement', 'formal_language'],
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
                                        {'label': 'Use of Synonyms', 'value': 'use_of_synonyms'}
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
                        StudentCardAIO(s) for s in students
                    ],
                    class_name='g-3 p-3'
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


# make groups draggable
# TODO fix draggability on this page
# clientside_callback(
#     ClientsideFunction(namespace='clientside', function_name='make_draggable'),
#     Output('group-row', 'data-drag'),
#     Input({'type': 'group-card', 'index': ALL}, 'id')
# )

# open the offcanvas show/hide options checklist
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='open_offcanvas'),
    Output(show_hide_options_offcanvas, 'is_open'),
    Input(show_hide_options_open, 'n_clicks'),
    State(show_hide_options_offcanvas, 'is_open')
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_progress_checklist'),
    Output(show_hide_options_progress_collapse, 'is_open'),
    Input(show_hide_options_checklist, 'value')
)

# update store
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='populate_student_data'),
    Output(StudentCardAIO.ids.store(ALL), 'data'),
    Input('course-websocket', 'message'),
    State(StudentCardAIO.ids.store(ALL), 'data'),
    State('student-counter', 'data')
)

# update store
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='sort_students'),
    Output(StudentCardAIO.ids.order(ALL), 'data'),
    Output('sort-by-dropdown-label', 'children'),
    Input('sort-by-radioitems', 'value'),
    State('sort-by-radioitems', 'options'),
    State('student-counter', 'data')
)

# hide/show attributes
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='hide_show_attributes'),
    Output(StudentCardAIO.ids.sentence_badge(ALL), 'className'),
    Output(StudentCardAIO.ids.paragraph_badge(ALL), 'className'),
    Output(StudentCardAIO.ids.time_on_task_badge(ALL), 'className'),
    Output(StudentCardAIO.ids.unique_words_badge(ALL), 'className'),
    Output(StudentCardAIO.ids.text_area(ALL), 'className'),
    Output(StudentCardAIO.ids.progress_div(ALL), 'className'),
    Output(StudentCardAIO.ids.transition_words_wrapper(ALL), 'className'),
    Output(StudentCardAIO.ids.use_of_synonyms_wrapper(ALL), 'className'),
    Output(StudentCardAIO.ids.sv_agreement_wrapper(ALL), 'className'),
    Output(StudentCardAIO.ids.formal_language_wrapper(ALL), 'className'),
    Input(show_hide_options_checklist, 'value'),
    Input(show_hide_options_progress_checklist, 'value'),
    State('student-counter', 'data')
)