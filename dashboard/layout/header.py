# from dash import html
from dashboard.index import (resampled_runs,
                             min_year,
                             max_year)
import dash_bootstrap_components as dbc


navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/home"),
                    id="home-link",),
        # dbc.NavItem(dbc.NavLink("Detailed view", href="/heatmapview"),
        #             id="heatmapview-link",),
    ],
    brand="Hello! 👋 Here are your running stats from {0} to {1}".format(min_year, max_year),
    brand_href='/',
    color="light",
    dark=False,
    style={"margin-bottom": "1.0rem"},
)
