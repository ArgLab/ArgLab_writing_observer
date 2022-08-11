# package imports
from dash import html
import dash_bootstrap_components as dbc
import random

courses = [
    {
        'id': i,
        'name': '8th Grade Writing',
        'section': f'Sec 00{i+1}',
        'start_time': '10:25 AM',
        'end_time': '11:07 AM',
        'year': 2022,
        'semester': 'Fall',
        'active': bool(random.getrandbits(1))
    } for i in range (4)
]

def create_course_card(course):
    color = 'light'
    if course['active']:
        color = 'secondary'

    card = dbc.Col(
        dbc.Card(
            html.A(
                [
                    dbc.CardBody(
                        [
                            html.H4(course['name']),
                            html.Div(course['section']),
                            html.Small(f'{course["start_time"]}-{course["end_time"]}'),
                            html.Div(
                                dbc.Badge(
                                    f'{course["semester"]} {course["year"]}',
                                    pill=True,
                                    color='primary'
                                )
                            )
                        ]
                    )
                ],
                href=f'/course/{course["id"]}',
                # TODO transfer most of this to css and replace with
                # className='course-card'
                className='text-reset text-decoration-none h-100 d-flex flex-column align-items-stretch',
                title=f'Opens dashboard for {course["name"]}'
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


def list_courses():
    cards = html.Div(
        [
            html.H2('Courses'),
            dbc.Card(
                [
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
                ],
                body=True,
                color='light'
            )
        ]
    )
    return cards
