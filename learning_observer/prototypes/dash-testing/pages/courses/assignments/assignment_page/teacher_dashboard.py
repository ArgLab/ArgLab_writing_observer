# package imports
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket

# local imports
from .students import create_student_tab
# from .groups import create_group_tab
from .reports import create_reports_tab

def create_teacher_dashboard(course, assignment):
    dashboard = dbc.Spinner(
        # TODO when the tab changes send a message to the websocket to get fresh data update
        # TODO move the websocket here
        dbc.Tabs(
            [
                dbc.Tab(
                    # create_group_tab(assignment, course.students),
                    create_student_tab(assignment, course.students),
                    label='Students',
                    tab_id='students',
                    label_class_name='h2'
                ),
                dbc.Tab(
                    # TODO this tab does the wrong analysis, we actually want to move this up a level
                    # create_reports_tab(course.students),
                    label='Reports',
                    tab_id='reports',
                    label_class_name='h2'
                )
            ],
            active_tab='students'
        ),
        color='primary'
    )
    return dashboard
