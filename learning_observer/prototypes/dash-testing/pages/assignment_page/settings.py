# package imports
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc

prefix = 'teacher-dashboard-settings'
# settings ids
close_settings = f'{prefix}-close'
sort_by_checklist = f'{prefix}-sort-by-checklist'
sort_toggle = f'{prefix}-sort-by-toggle'
sort_icon = f'{prefix}-sort-by-icon'
sort_label = f'{prefix}-sort-by-label'
sort_reset = f'{prefix}-sort-by-reset'

show_hide_settings_open = f'{prefix}-show-hide-open-button'
show_hide_settings_offcanvas = f'{prefix}-show-hide-offcanvcas'
show_hide_settings_checklist = f'{prefix}-show-hide-checklist'
show_hide_settings_metric_collapse = f'{prefix}-show-hide-metric-collapse'
show_hide_settings_metric_checklist = f'{prefix}-show-hide-metric-checklist'
show_hide_settings_text_collapse = f'{prefix}-show-hide-text-collapse'
show_hide_settings_text_radioitems = f'{prefix}-show-hide-text-radioitems'
show_hide_settings_indicator_collapse = f'{prefix}-show-hide-indicator-collapse'
show_hide_settings_indicator_checklist = f'{prefix}-show-hide-indicator-checklist'

open_btn = dbc.Button(
    [
        html.I(className='fas fa-gear'),
        html.Span('Settings', className='ms-1 d-none d-lg-inline'),
    ],
    class_name='btn btn-secondary',
    id=show_hide_settings_open,
    title='Open settings menu to show or hide different student attributes'
)

panel = dbc.Card(
    [
        html.Div(
            [
                html.H4(
                    [
                        html.I(className='fas fa-gear me-2'),
                        'Settings'
                    ], className='d-inline'
                ),
                dbc.Button(
                    html.I(className='fas fa-xmark'),
                    color='white',
                    class_name='float-end text-body',
                    id=close_settings
                )
            ],
            className='m-2'
        ),
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    dbc.Card(
                        [
                            dcc.Checklist(
                                options=[
                                    {'label': 'Transition Words', 'value': 'transition_words'},
                                    {'label': 'Academic Language', 'value': 'academic_language'}
                                ],
                                value=[],
                                id=sort_by_checklist,
                                labelClassName='form-check',
                                inputClassName='form-check-input'
                            ),
                            html.Div(
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            [
                                                dcc.Checklist(
                                                    options=[
                                                        {
                                                            'value': 'checked',
                                                            'label': html.I(id=sort_icon)
                                                        }
                                                    ],
                                                    value=['checked'],
                                                    id=sort_toggle,
                                                    inputClassName='d-none',
                                                    className='d-inline',
                                                ),
                                                html.Span(
                                                    'None',
                                                    id=sort_label,
                                                    className='ms-1'
                                                )
                                            ],
                                            outline=True,
                                            color='primary',
                                            title='Arrange students by attributes',
                                        ),
                                        dbc.Button(
                                            [
                                                html.I(className='fas fa-rotate me-1'),
                                                'Reset Sort'
                                            ],
                                            id=sort_reset,
                                            outline=True,
                                            color='primary'
                                        )
                                    ],
                                    size='sm',
                                    class_name='float-end d-inline'
                                ),
                                className='mt-1'
                            )
                        ],
                        class_name='border-0'
                    ),
                    title='Sort by',
                ),
                dbc.AccordionItem(
                    [
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
                                                            id=show_hide_settings_metric_checklist,
                                                            labelClassName='form-check',
                                                            inputClassName='form-check-input'
                                                        ),
                                                        id=show_hide_settings_metric_collapse,
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
                                                            id=show_hide_settings_text_radioitems
                                                        ),
                                                        id=show_hide_settings_text_collapse,
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
                                                            id=show_hide_settings_indicator_checklist,
                                                            labelClassName='form-check',
                                                            inputClassName='form-check-input'
                                                        ),
                                                        id=show_hide_settings_indicator_collapse,
                                                    )
                                                ],
                                                className='m-2'
                                            ),
                                            'value': 'indicators'
                                        }
                                    ],
                                    value=['text', 'indicators', 'metrics'],
                                    id=show_hide_settings_checklist,
                                    labelClassName='form-check',
                                    inputClassName='form-check-input'
                                ),
                    ],
                    title='Student Card Options',
                    class_name='rounded-bottom'
                ),
            ],
            active_item=[f'item-{i}' for i in range(2)],
            always_open=True,
            flush=True,
            class_name='border-top'
        ),        
    ],
    id=show_hide_settings_offcanvas,
    class_name='m-2 mx-md-0 mb-md-0 mt-md-3 sticky-top'
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='change_sort_direction_icon'),
    Output(sort_icon, 'className'),
    Output(sort_label, 'children'),
    Input(sort_toggle, 'value'),
    Input(sort_by_checklist, 'value')
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='reset_sort_options'),
    Output(sort_by_checklist, 'value'),
    Input(sort_reset, 'n_clicks')
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_indicators_checklist'),
    Output(show_hide_settings_indicator_collapse, 'is_open'),
    Input(show_hide_settings_checklist, 'value')
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_metrics_checklist'),
    Output(show_hide_settings_metric_collapse, 'is_open'),
    Input(show_hide_settings_checklist, 'value')
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_text_checklist'),
    Output(show_hide_settings_text_collapse, 'is_open'),
    Input(show_hide_settings_checklist, 'value')
)
