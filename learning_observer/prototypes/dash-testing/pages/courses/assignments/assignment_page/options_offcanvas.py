# package imports
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc

prefix = 'teacher-dashboard'
# offcanvas options
show_hide_options_open = f'{prefix}-show-hide-open-button'
show_hide_options_offcanvas = f'{prefix}-show-hide-offcanvcas'
show_hide_options_checklist = f'{prefix}-show-hide-checklist'
show_hide_options_metric_collapse = f'{prefix}-show-hide-metric-collapse'
show_hide_options_metric_checklist = f'{prefix}-show-hide-metric-checklist'
show_hide_options_text_collapse = f'{prefix}-show-hide-text-collapse'
show_hide_options_text_radioitems = f'{prefix}-show-hide-text-radioitems'
show_hide_options_indicator_collapse = f'{prefix}-show-hide-indicator-collapse'
show_hide_options_indicator_checklist = f'{prefix}-show-hide-indicator-checklist'

open_btn = dbc.Button(
    [
        html.I(className='fas fa-gear me-1'),
        'Options'
    ],
    class_name='me-2',
    color='secondary',
    id=show_hide_options_open
)

offcanvas = dbc.Offcanvas(
    [
        html.H4('Student Card'),
        dcc.Checklist(
            # TODO add tooltips to every option
            options=[
                {
                    'label': html.Span(
                        [
                            html.Span(
                                [
                                    html.I(className='fas fa-hashtag me-1'),
                                    'Metrics overview'
                                ],
                                className='font-size-lg'
                            ),
                            dbc.Collapse(
                                dcc.Checklist(
                                    options=[
                                        {
                                            'label': dbc.Badge('# sentences', color='info'),
                                            'value': 'sentences'
                                        },
                                        {
                                            'label': dbc.Badge('# words in 5 minutes', color='info'),
                                            'value': 'edits_per_min'
                                        },
                                        {
                                            'label': dbc.Badge('# minutes since last edit', color='info'),
                                            'value': 'since_last_edit'
                                        }
                                    ],
                                    value=['sentences', 'edits_per_min'],
                                    id=show_hide_options_metric_checklist,
                                    labelClassName='form-check',
                                    inputClassName='form-check-input'
                                ),
                                id=show_hide_options_metric_collapse,
                            )
                        ],
                        className='m-2'
                    ),
                    'value': 'metrics'
                },
                {
                    'label': html.Span(
                        [
                            html.Span(
                                [
                                    html.I(className='fas fa-file me-1'),
                                    'Summary text',
                                ],
                                className='font-size-lg'
                            ),
                            dbc.Collapse(
                                dbc.RadioItems(
                                    options=[
                                        {
                                            'label': 'Topic Sentence',
                                            'value': 'text_topic'
                                        },
                                        {
                                            'label': '1st Paragraph',
                                            'value': 'paragraph_1'
                                        },
                                        {
                                            'label': '2nd Paragraph',
                                            'value': 'paragraph_2'
                                        },
                                        {
                                            'label': '3rd Paragraph',
                                            'value': 'paragraph_3'
                                        },
                                        {
                                            'label': '4th Paragraph',
                                            'value': 'paragraph_4'
                                        },
                                        {
                                            'label': '5th Paragraph',
                                            'value': 'paragraph_5'
                                        },
                                    ],
                                    value='text_topic',
                                    id=show_hide_options_text_radioitems
                                ),
                                id=show_hide_options_text_collapse,
                            )
                        ],
                        className='m-2'
                    ),
                    'value': 'text'
                },
                {
                    'label': html.Span(
                        [
                            html.Span(
                                [
                                    html.I(className='fas fa-chart-bar me-1'),
                                    'Indicators overview',
                                ],
                                className='font-size-lg'
                            ),
                            dbc.Collapse(
                                dcc.Checklist(
                                    options=[
                                        {
                                            'label': html.Span('Transition Words', className='fs-6 m-1'),
                                            'value': 'transition_words'
                                        },
                                        {
                                            'label': html.Span('Academic Language', className='fs-6 m-1'),
                                            'value': 'academic_language'
                                        },
                                    ],
                                    value=['transition_words', 'academic_language'],
                                    id=show_hide_options_indicator_checklist,
                                    labelClassName='form-check',
                                    inputClassName='form-check-input'
                                ),
                                id=show_hide_options_indicator_collapse,
                            )
                        ],
                        className='m-2'
                    ),
                    'value': 'indicators'
                }
            ],
            value=['text', 'indicators', 'metrics'],
            id=show_hide_options_checklist,
            labelClassName='form-check',
            inputClassName='form-check-input'
        ),
    ],
    id=show_hide_options_offcanvas,
    title='Display options',
    is_open=False
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
    ClientsideFunction(namespace='clientside', function_name='toggle_indicators_checklist'),
    Output(show_hide_options_indicator_collapse, 'is_open'),
    Input(show_hide_options_checklist, 'value')
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_metrics_checklist'),
    Output(show_hide_options_metric_collapse, 'is_open'),
    Input(show_hide_options_checklist, 'value')
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_text_checklist'),
    Output(show_hide_options_text_collapse, 'is_open'),
    Input(show_hide_options_checklist, 'value')
)
