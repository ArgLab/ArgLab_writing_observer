# package imports
import dash
from dash import html

# local imports
from .teacher_courses import teacher_courses

dash.register_page(
    __name__,
    path='/courses',
    title='Courses'
)

role = 'teacher'

def layout():
    if role == 'teacher':
        return teacher_courses
    elif role == 'student':
        return html.Div('Student dashboard')
    return html.Div('No role selcted')
