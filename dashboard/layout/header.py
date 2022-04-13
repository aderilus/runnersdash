from dash import html
from utils import get_column_extremas, get_latest_daily_agg
import dash_bootstrap_components as dbc

daily_data = get_latest_daily_agg()
min_date, max_date = get_column_extremas(daily_data, 'index')
min_year = min_date.year
max_year = max_date.year

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
