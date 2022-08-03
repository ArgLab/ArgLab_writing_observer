# package imports
import dash_bootstrap_components as dbc

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand(
                'Learning Observer',
                href='/'
            ),
            dbc.NavItem(
                dbc.NavLink(
                    'Courses',
                    href='/courses',
                    class_name='text-light'
                )
            )
        ],
        fluid=True
    ),
    sticky='fixed',
    color='primary',
    dark=True
)
