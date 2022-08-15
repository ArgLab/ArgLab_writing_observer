# package imports
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket
import plotly.graph_objects as go

prefix = 'teacher-dashboard'

# options
report_checklist = f'{prefix}-report-checklist'
# TODO-options abstract the analysis options into a file in /components
# probably want to do the entire checklist, pass an id to it
# this should probably be an extremely simple AIO component
report_options = [
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
]
report_values = [o['value'] for o in report_options]
student_radiolist = f'{prefix}-student-radiolist'

# TODO remove
sample_fig = go.Figure()
for o in report_values:
    sample_fig.add_trace(go.Scatter(x=[], y=[], name=o))
sample_fig.update_layout(
    title='Student Progress Overview',
    xaxis_title='',
    yaxis_title=''
)
sample_fig.update_yaxes(
    categoryorder='array',
    categoryarray=['Low', 'Mid', 'High']
)

def create_reports_tab(students):
    # Do we need the assignment information for this?
    container = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4('Options:'),
                            dbc.Label('Attributes'),
                            # TODO figure out the styling of DCC radio items
                            # create a PR in the bootstrap css repo
                            # https://github.com/AnnMarieW/dash-bootstrap-templates/blob/main/dbc.css
                            dcc.Checklist(
                                options=report_options,
                                value=report_values,
                                labelClassName='d-block',
                                id=report_checklist
                            ),
                            dbc.Label('Student'),
                            # TODO possibly change this to a table with more basic information
                            dcc.RadioItems(
                                options=[
                                    {
                                        'label': s['name'], 'value': s['id']
                                    } for s in students
                                ],
                                labelClassName='d-block',
                                id=student_radiolist
                            )
                        ],
                        xl=3,
                        lg=4
                    ),
                    dbc.Col(
                        [
                            dcc.Graph(
                                # TODO change this to variable instead of hardcoding
                                id='report-graph',
                                figure=sample_fig
                            )
                        ],
                        xl=9,
                        lg=8
                    )
                ]
            ),
            # TODO move websocket tab level
            WebSocket(
                id='course-websocket',
                url=f'ws://127.0.0.1:5000/analysis/{len(students)}'
            )
        ]
    )
    return container

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='send_websocket'),
    Output('course-websocket', 'send'),
    Input(report_checklist, 'value'),
    Input(student_radiolist, 'value')
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='update_report_graph'),
    Output('report-graph', 'extendData'),
    Input('course-websocket', 'message'),
)
