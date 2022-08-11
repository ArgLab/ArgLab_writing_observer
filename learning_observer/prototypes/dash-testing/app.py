# package imports
import dash
from dash import html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

# local imports
from components import navbar

dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.6/dbc.min.css"
)

load_figure_template('minty')

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.MINTY, # bootstrap styling
        dbc.icons.FONT_AWESOME, # icons
        dbc_css, # dcc bootstrap styling
        'https://epsi95.github.io/dash-draggable-css-scipt/dragula.css' # draggable css
    ],
    external_scripts=[
        'https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.2/dragula.min.js', # draggable javascript
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

app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=True)
