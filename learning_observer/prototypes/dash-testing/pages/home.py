# package imports
import dash
from dash import html
import dash_bootstrap_components as dbc
from flask_login import current_user

# local imports
from components.login import login_card

dash.register_page(
    __name__,
    path='/',
    redirect_from=['/home'],
    title='Learning Observer'
)

loggin_out = dbc.Row(
    dbc.Col(
        login_card,
        md=6,
        lg=4,
        xxl=3,
    ),
    justify='center'
)

logged_in = html.Div(
    [
        html.H1('Welcome to Learning Observer'),
        html.A('Dashboard', href='/dashboard')
    ]
)


def layout():
    if not current_user.is_authenticated:
        return loggin_out
    return logged_in
