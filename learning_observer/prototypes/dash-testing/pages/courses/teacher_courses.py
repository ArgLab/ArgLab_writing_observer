# package imports
from dash import html
import dash_bootstrap_components as dbc
import random

courses = [
    {
        'id': i,
        'name': f'8th Grade Section {i+1}',
        'active': bool(random.getrandbits(1))
    } for i in range (4)
]

def create_course_card(course):
    color = None
    if course['active']:
        color = 'primary'
    card = dbc.Col(
        dbc.Card(
            html.A(
                [
                    dbc.CardBody(
                        [
                            html.H4(course['name'])
                        ]
                    ),
                    dbc.CardFooter(
                        'Footer',
                        class_name='mb-0'
                    )
                ],
                href=f'/course/{course["id"]}',
                # TODO transfer most of this to css and replace with
                # className='course-card'
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


def list_courses():
    cards = html.Div(
        [
            html.H2('Courses'),
            html.H3('Active'),
            dbc.Row(
                [
                    create_course_card(course)
                    for course in courses if course['active']
                ],
                class_name='g-3'
            ),
            html.H3('Old'),
            dbc.Accordion(
                dbc.AccordionItem(
                    dbc.Row(
                        [
                            create_course_card(course)
                            for course in courses if not course['active']
                        ],
                        class_name='g-3'
                    ),
                    title='Spring 2022'
                ),
                start_collapsed=True,
            )
        ]
    )
    return cards
