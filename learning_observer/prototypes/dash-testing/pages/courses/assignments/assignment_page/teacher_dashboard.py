# package imports
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket

# local imports
from .groups import create_group_tab
from .reports import create_reports_tab

def create_teacher_dashboard(course, assignment):
    dashboard = dbc.Spinner(
        # TODO when the tab changes send a message to the websocket to get fresh data update
        # TODO move the websocket here
        dbc.Tabs(
            [
                dbc.Tab(
                    # create_group_tab(assignment, course.students),
                    'disabled',
                    label='Groups',
                    tab_id='groups',
                    label_class_name='h2'
                ),
                dbc.Tab(
                    create_reports_tab(course.students),
                    label='Reports',
                    tab_id='reports',
                    label_class_name='h2'
                )
            ],
            active_tab='reports'
        ),
        color='primary'
    )
    return dashboard
