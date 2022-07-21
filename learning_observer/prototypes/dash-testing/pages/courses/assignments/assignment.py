# package imports
from dash import html
import dash_bootstrap_components as dbc

class Assignment:
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description

def create_assignment_card(assignment, course_id):
    card = dbc.Card(
        html.A(
            [
                dbc.CardHeader(assignment.name),
                dbc.CardBody(
                    assignment.description
                )
            ],
            href=f'/course/{course_id}/assignment/{assignment.id}'
        ),
        outline=True
    )
    return card


def list_assignments(course):
    cards = html.Div(
        [
            create_assignment_card(assignment, course.id)
            for assignment in course.assignments
        ]
    )
    return cards
