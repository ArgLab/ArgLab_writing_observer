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
                    'Dashboard',
                    href='/dashboard',
                    class_name='text-light'
                )
            )
        ]
    ),
    sticky='fixed',
    color='primary',
    dark=True
)
