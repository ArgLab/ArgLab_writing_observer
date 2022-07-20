# package imports
from dash import html

courses = [
    {
        'id': i,
        'name': f'8th Grade Section {i+1}'
    } for i in range (3)
]

teacher_courses = html.Div(
    [
        html.H1('Courses'),
        html.Div(
            [
                html.A(course['name'], href=f'/course/{course["id"]}/dashboard', className='me-3')
                for course in courses
            ]
        )
    ]
)
