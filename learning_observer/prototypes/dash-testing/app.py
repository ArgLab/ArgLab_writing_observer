# package imports
import dash
from dash import html
import dash_bootstrap_components as dbc

# local imports
from components import navbar

dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css"
)

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.MINTY,
        dbc.icons.FONT_AWESOME,
        dbc_css,
        'https://epsi95.github.io/dash-draggable-css-scipt/dragula.css'
    ],
    external_scripts=[
        'https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.2/dragula.min.js'
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
                class_name='my-2'
            )
        ],
        className='dbc'
    )

app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=True)
