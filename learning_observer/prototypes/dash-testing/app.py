# package imports
import dash
from dash import html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

# local imports
from components import navbar

# load in minty templates as default plotly
load_figure_template('minty')

app = dash.Dash(
    __name__,
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

def serve_layout():
    return html.Div(
        [
            navbar,
            dbc.Container(
                dash.page_container,
                class_name='my-2',
                fluid=True
            )
        ],
        className='dbc'
    )

dash.register_page('document', path='/document', layout=html.Div(['This link will take you to the student\'s document in the future.']))
dash.register_page('student', path='/student', layout=html.Div(['This page will provide an overview of a specific student in the future.']))

app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=False)
