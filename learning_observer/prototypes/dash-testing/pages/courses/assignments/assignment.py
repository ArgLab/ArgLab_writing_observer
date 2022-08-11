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
                            assignment.description,
                            html.Div(
                                dbc.Badge(
                                    'Narrative',
                                    pill=True
                                )
                            )
                        ]
                    )
                ],
                # TODO transfer most of this to css and replace with
                # className='assignment-card'
                href=f'/course/{course_id}/assignment/{assignment.id}',
                className=f'text-decoration-none {"text-white" if color=="primary" else "text-body"} h-100 d-flex flex-column align-items-stretch'
            ),
            class_name='shadow-card h-100',
            color=color
        ),
        xxl=2,
        lg=3,
        md=4,
        sm=6,
        align='stretch'
    )
    return card


def list_assignments(course):
    cards = html.Div(
        [
            html.Div(
                [
                    dbc.Button(
                        [
                            html.I(className='fas fa-circle-plus me-1'),
                            'Add Assignment'
                        ],
                        class_name='me-2',
                        color='secondary'
                    ),
                ],
                className='my-2'
            ),
            dbc.Card(
                [
                    html.H3('Active'),
                    dbc.Row(
                        [
                            create_assignment_card(assignment, course.id)
                            for assignment in course.assignments if assignment.active
                        ],
                        class_name='g-3'
                    ),
                    html.H3('Other'),
                    dbc.Row(
                        [
                            create_assignment_card(assignment, course.id)
                            for assignment in course.assignments if not assignment.active
                        ],
                        class_name='g-3'
                    )
                ],
                body=True,
                color='light',
            )
        ]
    )
    return cards
