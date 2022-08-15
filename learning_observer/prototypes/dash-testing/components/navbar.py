# package imports
from dash import html, clientside_callback, ClientsideFunction, Input, Output, State
import dash_bootstrap_components as dbc

# local imports
from .assignment import create_assignment_card
from .teacher_courses import courses, create_course_card
from .course import Course

sample_course = Course(0, 'teacher')

navbar = html.Div(
    [
        dbc.Navbar(
            [
                dbc.Container(
                    [
                        dbc.NavbarBrand(
                            'Learning Observer',
                            href='/'
                        ),
                        dbc.NavItem(
                            dbc.NavLink(
                                'Courses',
                                id='courses-open',
                                class_name='text-light'
                            )
                        )
                    ],
                    fluid=True
                )
            ],
            sticky='fixed',
            color='primary',
            dark=True
        ),
        dbc.Collapse(
            dbc.Container(
                [
                    # TODO turn these into nicer carousels. We will need to create our own
                    # TODO show the assignments based on whichever course is being hovered
                    # TODO maybe when we hover on the assignments, we displayed 'Students' and 'Reports'
                    # as buttons with a dark background for them to click. include 'edit'
                    html.H4('Courses'),
                    dbc.Row(
                        [
                            create_course_card(course)
                            for course in courses
                        ],
                        class_name='g-3 pb-2 flex-nowrap overflow-auto'
                    ),
                    html.Hr(),
                    html.H4('Assignments'),
                    dbc.Row(
                        [
                            create_assignment_card(assignment, sample_course.id)
                            for assignment in sample_course.assignments
                        ],
                        class_name='g-3 pb-2 flex-nowrap overflow-auto'
                    )
                ],
                fluid=True,
            ),
            id='course-collapse',
            class_name='pt-0 border-bottom',
            is_open=False
        )     
    ]
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_open_close'),
    Output('course-collapse', 'is_open'),
    Input('courses-open', 'n_clicks'),
    State('course-collapse', 'is_open')
)
