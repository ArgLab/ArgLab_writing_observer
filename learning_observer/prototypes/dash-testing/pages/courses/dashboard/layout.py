# package imports
import dash
from dash import html

# local imports
from .teacher_dashboard import create_teacher_dashboard

dash.register_page(
    __name__,
    path_template='/course/<course_id>/dashboard',
    title='Dashboard'
)

role = 'teacher'

def layout(course_id=None):
    if role == 'teacher':
        return create_teacher_dashboard(course_id)
    elif role == 'student':
        return html.Div('Student course info')
    return html.Div('No role selcted')
