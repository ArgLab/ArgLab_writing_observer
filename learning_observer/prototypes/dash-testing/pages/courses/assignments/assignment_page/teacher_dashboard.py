# package imports
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc

# local imports
from .student_card_aio import StudentCardAIO

prefix = 'teacher-dashboard'

# add group
add_group_button = f'{prefix}-add-group-button'
add_group_card = dbc.Col(
    dbc.Card(
        dbc.Button(
            html.I(className='far fa-plus display-5'),
            class_name='m-auto',
            color='secondary',
            id=add_group_button
        ),
        color='light',
        class_name='h-100'
    ),
    class_name='h-100',
    xxl=3,
    lg=4,
    md=6
)


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

def create_teacher_dashboard(course, assignment):
    dashboard = dbc.Spinner(
        create_assignment_board(assignment, course.students),
        color='primary'
    )
    return dashboard


def create_assignment_board(assignment, students):
    container = dbc.Container(
        [
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
                        id=show_hide_options_open
                    )
                ]
            ),
            dbc.Row(
                [
                    create_group_card('Group 1', students[:10]),
                    create_group_card('Group 2', students[10:20]),
                    create_group_card('Group 3', students[20:]),
                    add_group_card
                ],
                id='group-row',
                style={'height': '85vh'}
            ),
            offcanvas
        ],
        class_name='m-0'
    )
    return container


def create_group_card(name, students):
    card = dbc.Col(
        dbc.Card(
            [
                html.H3(
                    name,
                    className='text-center my-2'
                ),
                html.Div(
                    [StudentCardAIO(s) for s in students],
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
        xxl=3,
        lg=4,
        md=6
    )
    return card


# make groups draggable
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='make_draggable'),
    Output('group-row', 'data-drag'),
    Input({'type': 'group-card', 'index': ALL}, 'id')
)

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

# hide/show attributes
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='hide_show_attributes'),
    Output(StudentCardAIO.ids.sentence_badge(ALL), 'className'),
    Output(StudentCardAIO.ids.paragraph_badge(ALL), 'className'),
    Output(StudentCardAIO.ids.time_on_task_badge(ALL), 'className'),
    Output(StudentCardAIO.ids.unique_words_badge(ALL), 'className'),
    Output(StudentCardAIO.ids.text_area(ALL), 'className'),
    Output(StudentCardAIO.ids.progress_div(ALL), 'className'),
    Output(StudentCardAIO.ids.transition_words(ALL), 'className'),
    Output(StudentCardAIO.ids.use_of_synonyms(ALL), 'className'),
    Output(StudentCardAIO.ids.sv_agreement(ALL), 'className'),
    Output(StudentCardAIO.ids.formal_language(ALL), 'className'),
    Input(show_hide_options_checklist, 'value'),
    Input(show_hide_options_progress_checklist, 'value')
)
