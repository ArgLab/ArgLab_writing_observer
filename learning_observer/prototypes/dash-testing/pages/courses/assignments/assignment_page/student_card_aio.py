# package imports
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, MATCH
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket

class StudentCardAIO(html.Div):

    class ids:
        card = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'card',
            'aio_id': aio_id
        }
        store = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'store',
            'aio_id': aio_id
        }
        more_info = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'more_info',
            'aio_id': aio_id
        }
        sentence_badge = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'sentence_badge',
            'aio_id': aio_id
        }
        paragraph_badge = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'paragraph_badge',
            'aio_id': aio_id
        }
        time_on_task_badge = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'time_on_task_badge',
            'aio_id': aio_id
        }
        unique_words_badge = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'unique_words_badge',
            'aio_id': aio_id
        }
        text_area = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'text_area',
            'aio_id': aio_id
        }
        progress_div = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'progress_div',
            'aio_id': aio_id
        }
        transition_words = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'transition_words_progress',
            'aio_id': aio_id
        }
        use_of_synonyms = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'use_of_synonyms_progress',
            'aio_id': aio_id
        }
        sv_agreement = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'sv_agreement_progress',
            'aio_id': aio_id
        }
        formal_language = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'formal_language_progress',
            'aio_id': aio_id
        }

    ids = ids

    def __init__(
        self,
        student
    ):
        aio_id = student['id']
        super().__init__(
            [
                dbc.Card(
                    [
                        html.H4(student['name']),
                        dbc.Button(
                            html.I(className='fas fa-up-right-and-down-left-from-center text-body'),
                            id=self.ids.more_info(aio_id),
                            color='white',
                            size='sm',
                            class_name='position-absolute end-0 top-0'
                            # TODO implement functionality of more info
                        ),
                        html.Div(
                            [
                                dbc.Badge(
                                    id=self.ids.sentence_badge(aio_id),
                                    color='info'
                                ),
                                dbc.Badge(
                                    id=self.ids.paragraph_badge(aio_id),
                                    color='info'
                                ),
                                dbc.Badge(
                                    id=self.ids.time_on_task_badge(aio_id),
                                    color='info'
                                ),
                                dbc.Badge(
                                    id=self.ids.unique_words_badge(aio_id),
                                    color='info'
                                )
                            ],
                            className='d-flex justify-content-around flex-wrap'  # need to make sure the badges have gutters
                        ),
                        html.P(
                            id=self.ids.text_area(aio_id)
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        'Transition Words',
                                        dbc.Progress(max=3, id=self.ids.transition_words(aio_id))
                                    ]
                                ),
                                html.Div(
                                    [
                                        'Effective Use of Synonyms',
                                        dbc.Progress(max=3, id=self.ids.use_of_synonyms(aio_id))
                                    ]
                                ),
                                html.Div(
                                    [
                                        'Subject Verb Agreement',
                                        dbc.Progress(max=3, id=self.ids.sv_agreement(aio_id))
                                    ]
                                ),
                                html.Div(
                                    [
                                        'Formal Language',
                                        dbc.Progress(max=3, id=self.ids.formal_language(aio_id))
                                    ]
                                )
                            ],
                            id=self.ids.progress_div(aio_id),
                            className='m-1'
                        )
                    ],
                    body=True,
                    id=self.ids.card(aio_id)
                ),
                dcc.Store(
                    id=self.ids.store(aio_id),
                    data=None
                )
            ],
            className='my-2 mx-1'
        )
    
    # populate student data
    clientside_callback(
        ClientsideFunction(namespace='clientside', function_name='update_student_card'),
        Output(ids.card(MATCH), 'class_name'),
        Output(ids.sentence_badge(MATCH), 'children'),
        Output(ids.paragraph_badge(MATCH), 'children'),
        Output(ids.time_on_task_badge(MATCH), 'children'),
        Output(ids.unique_words_badge(MATCH), 'children'),
        Output(ids.text_area(MATCH), 'children'),
        Output(ids.transition_words(MATCH), 'value'),
        Output(ids.use_of_synonyms(MATCH), 'value'),
        Output(ids.sv_agreement(MATCH), 'value'),
        Output(ids.formal_language(MATCH), 'value'),
        Input(ids.store(MATCH), 'data')
    )

    # change the color of bars based on value
    # each callback uses the same function
    clientside_callback(
        ClientsideFunction(namespace='clientside', function_name='update_student_progress_bars'),
        Output(ids.transition_words(MATCH), 'color'),
        Input(ids.transition_words(MATCH), 'value')
    )
    clientside_callback(
        ClientsideFunction(namespace='clientside', function_name='update_student_progress_bars'),
        Output(ids.use_of_synonyms(MATCH), 'color'),
        Input(ids.use_of_synonyms(MATCH), 'value')
    )
    clientside_callback(
        ClientsideFunction(namespace='clientside', function_name='update_student_progress_bars'),
        Output(ids.sv_agreement(MATCH), 'color'),
        Input(ids.sv_agreement(MATCH), 'value')
    )
    clientside_callback(
        ClientsideFunction(namespace='clientside', function_name='update_student_progress_bars'),
        Output(ids.formal_language(MATCH), 'color'),
        Input(ids.formal_language(MATCH), 'value')
    )
