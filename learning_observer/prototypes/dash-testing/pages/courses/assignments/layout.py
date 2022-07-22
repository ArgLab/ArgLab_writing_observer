# package imports
import dash
from dash import html, dcc
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
        dashboard = list_assignments(course)
    elif role == 'student':
        dashboard = 'Student'
    else:
        dashboard = 'No role'
    layout = html.Div(
        [
            dmc.Breadcrumbs(
                [
                    dcc.Link('Courses', href='/courses'),
                    dcc.Link(f'{course.name}', href=f'/course/{course.id}', className='disabled')
                ]
            ),
            dashboard
        ]
    )
    return layout
