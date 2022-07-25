# package imports
import dash
from dash import html, dcc
import dash_mantine_components as dmc

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
            dmc.Breadcrumbs(
                [
                    dcc.Link('Courses', href='/courses', className='disabled')
                ],
                class_name='mb-2'
            ),
            courses
        ]
    )
    return layout
