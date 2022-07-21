# package imports
import dash
from dash import html
import dash_bootstrap_components as dbc

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
        courses = teacher_courses
    elif role == 'student':
        courses = html.Div('Student dashboard')
    else:
        courses = html.Div('No role selcted')

    layout = html.Div(
        [
            dbc.Breadcrumb(
                items=[
                    {'label': 'Courses', 'href': '/courses', 'active': True}
                ]
            ),
            courses
        ]
    )
    return layout
