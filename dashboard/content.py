""" Contains callbacks imports.
"""

from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

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


monthbyday_heatmap = dbc.Col(
    # class_name="col-8",
    children=[
        html.H6("World"),
        hmap_select_yr,
        hmap_select_z,
        hmap_select_type,
        dcc.Graph(id="monthbyday-heatmap")
    ],
    width={"size": 8, "order": "last", },
)

main_container = dbc.Container(
    class_name="testmaincontainer",
    children=[
        dbc.Row(
            children=[
                left_col,
                monthbyday_heatmap,
            ],
        ),
        dbc.Row(
            children=[
                html.H6("What's up"),
            ],
            class_name="testrightcol",
        ),
    ],
    fluid=False,  # fluid=True to remove margins that dbc.Container sets up
)

app.layout = html.Div(
    children=[
        header,
        navcontainer,
        main_container,
    ])
