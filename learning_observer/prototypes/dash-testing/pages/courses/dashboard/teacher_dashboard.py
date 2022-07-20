# package imports
from dash import html
import dash_bootstrap_components as dbc

# local imports



def create_assignment_tab(assignment):
    contents = 'Contents'
    tab = dbc.Tab(
        contents,
        label=assignment['label'],
        tab_id=assignment['id']
    )
    return tab


def create_teacher_dashboard(course):
    # fetch assignments
    # for each assignment create an assignment tab
    assignments = [
        {
            'id': i,
            'label': f'Assignment {i}'
        } for i in range(4)
    ]

    dashboard = dbc.Tabs(
        [
            create_assignment_tab(assignment)
            for assignment in assignments
        ]
    ),
    return dashboard
