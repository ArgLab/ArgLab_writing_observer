# package imports
from dash import html
import dash_bootstrap_components as dbc
import datetime
import platform
import random

date_format = '%B %#d, %G' if platform.system() == 'Windows' else '%B %-d, %G'
# as long as we don't have callbacks involve the
# functions could easily be turned into class methods
class Assignment:
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description
        self.essay_type = random.choice(['Narrative', 'Argumentative', 'Other'])
        self.start_date = datetime.datetime(2022, 7, 1)
        self.end_date = random.choice([datetime.date(2022, 8, 1), datetime.date(2022, 7, 14), datetime.date(2022, 7, 22)])
        self.active = bool(random.getrandbits(1))

def create_assignment_card(assignment, course_id):
    if assignment.active:
        color='primary'
    else:
        color = 'light'

    card = dbc.Col(
        dbc.Card(
            html.A(
                [
                    dbc.CardBody(
                        [
                            html.H4(assignment.name),
                            html.Div(
                                dbc.Badge(
                                    assignment.essay_type,
                                    pill=True
                                ),
                                className='my-1'
                            )
                        ]
                    )
                ],
                # TODO transfer most of this to css and replace with
                # className='assignment-card'
                href=f'/course/{course_id}/assignment/{assignment.id}',
                className='text-decoration-none text-body h-100 d-flex flex-column align-items-stretch',
                title=f'Opens dashboard for {assignment.name}'
            ),
            class_name='shadow-card h-100 bg-opacity-25',
            color=color
        ),
        xxl=2,
        lg=3,
        md=4,
        sm=6,
        align='stretch'
    )
    return card
