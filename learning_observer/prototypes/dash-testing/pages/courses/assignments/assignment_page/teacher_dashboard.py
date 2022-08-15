# package imports
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket

# local imports
from .students import create_student_tab

def create_teacher_dashboard(course, assignment):
    dashboard = dbc.Spinner(
        # TODO when the tab changes send a message to the websocket to get fresh data update
        # TODO move the websocket here
        create_student_tab(assignment, course.students),
        color='primary'
    )
    return dashboard
