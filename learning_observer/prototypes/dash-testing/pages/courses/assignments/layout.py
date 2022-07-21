# package imports
import dash
from dash import html
import dash_bootstrap_components as dbc

# local imports
from .course import Course
from .assignment import list_assignments
from .teacher_dashboard import create_teacher_dashboard

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
            dbc.Breadcrumb(
                items=[
                    {'label': 'Courses', 'href': '/courses'},
                    {'label': f'{course.name}', 'href': f'/course/{course.id}', 'active': True}
                ]
            ),
            dashboard
        ]
    )
    return layout
