# package imports
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

# local imports
from .course import Course
from .assignment import list_assignments

dash.register_page(
    __name__,
    path_template='/course/<course_id>',
    title='Dashboard'
)

def layout(course_id=None):
    role = 'teacher'
    course = Course(course_id, role)
    if role == 'teacher':
        # TODO abstract this into its own file, teacher course
        dashboard = dbc.Spinner(
            dbc.Tabs(
                [
                    dbc.Tab(
                        list_assignments(course),
                        label='Assignments',
                        label_class_name='h2'
                    ),
                    dbc.Tab(
                        html.Div(
                            [
                                html.H3('Student Progress'),
                                html.Img(
                                    src='/assets/assignment-by-assignment.png',
                                    className='w-75'
                                )
                            ],
                        ),
                        label='Reports',
                        label_class_name='h2'
                    )
                ]
            ),
            color='primary'
        )
    elif role == 'student':
        dashboard = 'Student'
    else:
        dashboard = 'No role'
    layout = html.Div(
        [
            dmc.Breadcrumbs(
                [
                    dcc.Link('Courses', href='/courses', refresh=True),
                    dcc.Link(f'{course.name}', href=f'/course/{course.id}', className='disabled')
                ],
                class_name='mb-2'
            ),
            dashboard
        ]
    )
    return layout
