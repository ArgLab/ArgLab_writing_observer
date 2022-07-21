# package imports
from dash import html, dcc, clientside_callback, ClientsideFunction, callback, Output, Input, State, MATCH
import dash_bootstrap_components as dbc

prefix = 'teacher-dashboard'

# options
show_hide_options_open = f'{prefix}-show-hide-open-button'
show_hide_options_offcanvas = f'{prefix}-show-hide-offcanvcas'
show_hide_options_checklist = f'{prefix}-show-hide-checklist'

def create_teacher_dashboard(course):
    dashboard = dbc.Tabs(
        [
            dbc.Tab(
                dbc.Spinner(
                    create_assignment_tab(assignment),
                    color='primary'
                ),
                label=assignment.name,
                tab_id=assignment.id
            ) for assignment in course.assignments
        ]
    )
    return dashboard


def create_assignment_tab(assignment):
    id = assignment.id
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
                        id={
                            'type': show_hide_options_open,
                            'index': id
                        }
                    )
                ]
            ),
            dbc.Row(
                [
                    'group1',
                    'group2',
                    'add group'
                ],
                id='group-row',
                class_name='g-3',
                style={'height': '85vh'}
            ),
            create_options_offcanvas(id)
        ]
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
                    [s.name for s in students],
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


def create_options_offcanvas(id):
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
                id={
                    'type': show_hide_options_checklist,
                    'index': id
                },
                labelClassName='d-block'
            )
        ],
        id={
            'type': show_hide_options_offcanvas,
            'index': id
        },
        title='Display options',
        is_open=False
    )
    return offcanvas

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='open_offcanvas'),
    Output({'type': show_hide_options_offcanvas, 'index': MATCH}, 'is_open'),
    Input({'type': show_hide_options_open, 'index': MATCH}, 'n_clicks'),
    State({'type': show_hide_options_offcanvas, 'index': MATCH}, 'is_open')
)
