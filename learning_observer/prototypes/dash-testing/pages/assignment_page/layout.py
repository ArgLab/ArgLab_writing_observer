# package imports
import dash
from dash import html
from flask_login import current_user

# local imports
from components.course import Course
from .teacher_dashboard import create_teacher_dashboard

dash.register_page(
    __name__,
    path_template='/dashboard',
    title='Dashboard'
)

def layout():
    role = 'teacher'
    course_id = 1
    assignment_id = 1
    course = Course(course_id, role)
    if current_user.is_authenticated:
        dashboard = create_teacher_dashboard(course, course.assignments[0])
    else:
        dashboard = html.A('Please login', href='/login')
    layout = html.Div(
        [
            dashboard
        ]
    )
    return layout
