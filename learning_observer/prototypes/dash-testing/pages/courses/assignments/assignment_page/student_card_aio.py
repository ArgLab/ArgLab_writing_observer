# package imports
from dash import html, Output, Input, State
import dash_bootstrap_components as dbc

class StudentCardAIO(html.Div):

    class ids:
        card = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'card',
            'aio_id': aio_id
        }
        websocket = lambda aio_id: {
            'component': 'StudentCardAIO',
            'subcomponent': 'websocket',
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
                        html.H4(student['name'])
                    ],
                    body=True,
                    id=self.ids.card(aio_id)
                )
            ],
            className='my-2 mx-1'
        )
