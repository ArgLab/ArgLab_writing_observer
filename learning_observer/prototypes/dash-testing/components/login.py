# package imports
from dash import html, dcc, callback, Output, Input, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask_login import UserMixin, current_user, logout_user, login_user
import json
import os

# read in raw data (no websocket connection)
cwd = os.getcwd()
data_in = os.path.join(cwd, 'data', 'logins.json')
with open(data_in, 'r') as f_obj:
    VALID_USERNAME_PASSWORD = json.load(f_obj)

class User(UserMixin):
    # User data model. It has to have at least self.id as a minimum
    def __init__(self, username):
        self.id = username

login_card = dbc.Card(
    [
        dbc.CardHeader('Login'),
        dbc.CardBody(
            dbc.Form(
                [
                    dbc.Input(
                        placeholder='Username',
                        type='text',
                        id='login-username',
                        class_name='mb-2'
                    ),
                    dbc.Input(
                        placeholder='Password',
                        type='password',
                        id='login-password',
                        class_name='mb-2'
                    ),
                    dbc.Button(
                        'Login',
                        n_clicks=0,
                        type='submit',
                        id='login-button',
                        class_name='float-end'
                    ),
                    dbc.FormText(children='', id='output-state')
                ]
            )
        )
    ]
)

login_location = dcc.Location(id='url-login')
login_info = html.Div(id='user-status-header')
logged_in_info = html.Div(
    [
        dbc.Button(
            html.I(className='fas fa-circle-user fa-xl'),
            id='user-popover',
            outline=True,
            color='light',
            class_name='border-0 user-icon'
        ),
        dbc.Popover(
            [
                dbc.PopoverBody(
                    [
                        dcc.Link(
                            [
                                html.I(className='fas fa-arrow-right-from-bracket me-1'),
                                'Logout'
                            ],
                            href='/logout'
                        )
                    ]
                )
            ],
            target='user-popover',
            trigger='focus',
            placement='bottom'
        )
    ]
)
logged_out_info = dbc.NavItem(
    dbc.NavLink(
        'Login',
        href='/login',
        class_name='text-light'
    )
)

@callback(
    Output('user-status-header', 'children'),
    Input('url-login', 'pathname')
)
def update_authentication_status(path):
    logged_in = current_user.is_authenticated
    if path == '/logout' and logged_in:
        logout_user()
        child = logged_out_info
    elif logged_in:
        child = logged_in_info
    else:
        child = logged_out_info
    return child

@callback(
    Output('output-state', 'children'),
    Output('url-login', 'pathname'),
    Input('login-button', 'n_clicks'),
    State('login-username', 'value'),
    State('login-password', 'value'),
    State('_pages_location', 'pathname'),
    prevent_initial_call=True
)
def login_button_click(n_clicks, username, password, pathname):
    if n_clicks > 0:
        if VALID_USERNAME_PASSWORD.get(username) and VALID_USERNAME_PASSWORD.get(username) == password:
            login_user(User(username))
            return 'Login Successful', '/home'
        return 'Incorrect username or password', pathname
    raise PreventUpdate
