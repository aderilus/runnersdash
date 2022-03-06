""" Contains callbacks imports.
"""

from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

from preparedatasets import DAYS_OF_WK
from dashboard.index import app
from dashboard.layout.header import header
from dashboard.layout.navigation import navcontainer
from dashboard.layout.activityheatmap import (hmap_select_yr,
                                              hmap_select_type,
                                              hmap_select_z)
from dashboard.layout.callbacks import heatmap_callbacks

left_col = dbc.Col(
    class_name="testleftcol",
    children=[
        html.H6("Hello")
    ],
)


right_col = dbc.Col(
    class_name="testrightcol",
    children=[
        html.H6("World"),
        hmap_select_yr,
        hmap_select_z,
        hmap_select_type,
        dcc.Graph(id="activity-heatmap")
    ],
)

main_container = dbc.Container(
    class_name="testmaincontainer",
    children=[
        dbc.Row(
            children=[
                left_col,
                right_col
            ],
        ),
        dbc.Row(
            children=[

            ],
        ),
    ],
    fluid=True,
)

app.layout = html.Div(
    children=[
        header,
        navcontainer,
        main_container,
    ])
