# package imports
import dash
from dash import html

# local imports
from components.course import Course
from .teacher_dashboard import create_teacher_dashboard

dash.register_page(
    __name__,
    path_template='/course/<course_id>/assignment/<assignment_id>',
    title='Dashboard'
)

def layout(course_id=None, assignment_id=None):
    role = 'teacher'
    course = Course(course_id, role)
    if not role or not course_id or not assignment_id:
        return 'BRUH'
    if role == 'teacher':
        dashboard = create_teacher_dashboard(course, course.assignments[0])
    elif role == 'student':
        dashboard = 'Student'
    else:
        dashboard = 'No role'
    layout = html.Div(
        [
            dashboard
        ]
    )
    return layout
