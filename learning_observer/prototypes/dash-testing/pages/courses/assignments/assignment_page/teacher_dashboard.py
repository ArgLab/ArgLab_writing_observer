# package imports
from re import M
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State
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
offcanvas = dbc.Offcanvas(
    [
        html.H4('Student Card'),
        dcc.Checklist(
            options=[
                {
                    'label': html.Span('Summary text', className='fs-5 m-2'),
                    'value': 'summary'
                },
                {
                    'label': dbc.Badge('# sentences', color='info', class_name='fs-5 m-2'),
                    'value': 'sentences'
                },
                {
                    'label': dbc.Badge('# paragraphs', color='info', class_name='fs-5 m-2'),
                    'value': 'paragraphs'
                },
                {
                    'label': dbc.Badge('time on task', color='info', class_name='fs-5 m-2'),
                    'value': 'time_on_task'
                },
                {
                    'label': dbc.Badge('# unique words', color='info', class_name='fs-5 m-2'),
                    'value': 'unique_words'
                },
                {
                    'label': html.Span(
                        [
                            html.I(className='fas fa-chart-bar me-1'),
                            'Metric overview'
                        ],
                        className='fs-5 m-2'
                    ),
                    'value': 'chart'
                }
            ],
            value=['sentences', 'paragraphs', 'summary', 'chart'],
            id=show_hide_options_checklist,
            labelClassName='d-block'
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
                    create_group_card('Group 1', students[:3]),
                    create_group_card('Group 2', students[3:]),
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


clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='open_offcanvas'),
    Output(show_hide_options_offcanvas, 'is_open'),
    Input(show_hide_options_open, 'n_clicks'),
    State(show_hide_options_offcanvas, 'is_open')
)
