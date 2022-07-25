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
        footer = f'Due: {assignment.end_date.strftime(date_format)}'
        today = datetime.date.today()
        if assignment.end_date < today:
            color = 'danger'
        elif assignment.end_date == today:
            color = 'warning'
        else:
            color='primary'
    else:
        footer = 'Completed'
        color = None

    card = dbc.Col(
        dbc.Card(
            html.A(
                [
                    dbc.CardBody(
                        [
                            html.H4(assignment.name),
                            assignment.description
                        ]
                    ),
                    dbc.CardFooter(
                        footer,
                        class_name='mb-0'
                    )
                ],
                # TODO transfer most of this to css and replace with
                # className='assignment-card'
                href=f'/course/{course_id}/assignment/{assignment.id}',
                className='text-reset text-decoration-none h-100 d-flex flex-column align-items-stretch'
            ),
            outline=True,
            class_name='shadow-card border-2 h-100',
            color=color
        ),
        xxl=3,
        lg=4,
        md=6,
        align='stretch'
    )
    return card


def list_assignments(course):
    cards = html.Div(
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
        ]
    )
    return cards
