# package imports
import dash
from dash import html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from flask import Flask
from flask_login import LoginManager
import uuid

# local imports
from components import navbar
from components.login import User, login_location

# load in minty templates as default plotly
load_figure_template('minty')

server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.MINTY, # bootstrap styling
        dbc.icons.FONT_AWESOME, # icons
        'https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.6/dbc.min.css', # dcc bootstrap styling
    ],
    external_scripts=[
        'https://cdn.jsdelivr.net/npm/lodash@4.17.21/lodash.min.js' # lodash B)
    ],
    title='Learning Observer',
    suppress_callback_exceptions=True
)

# update secret key
server.config.update(SECRET_KEY=str(uuid.uuid4()))

# configure login information
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

@login_manager.user_loader
def load_user(username):
    return User(username)


# create layout
def serve_layout():
    return html.Div(
        [
            login_location,
            navbar,
            dbc.Container(
                dash.page_container,
                class_name='my-2',
                fluid=True
            )
        ],
        className='dbc'
    )

# register random pages, not created yet
dash.register_page('document', path='/document', layout=html.Div(['This link will take you to the student\'s document in the future.']))
dash.register_page('student', path='/student', layout=html.Div(['This page will provide an overview of a specific student in the future.']))

app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
