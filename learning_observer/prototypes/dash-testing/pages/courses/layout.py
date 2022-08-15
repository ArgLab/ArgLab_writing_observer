# package imports
import dash
from dash import html

# local imports
from .teacher_courses import list_courses

dash.register_page(
    __name__,
    path='/courses',
    title='Courses'
)

role = 'teacher'

def layout():
    if role == 'teacher':
        courses = list_courses()
    elif role == 'student':
        courses = html.Div('Student dashboard')
    else:
        courses = html.Div('No role selcted')

    layout = html.Div(
        [
            courses
        ]
    )
    return layout
