import dash_bootstrap_components as dbc
from dash import html, dcc
from dashboard.layout.header import navbar
from dashboard.layout.activityheatmap import (hmap_select_yr,
                                              hmap_select_z)

# Individual containers
route_container = dbc.Card(
    children=[
        dbc.CardHeader(html.H6("Route")),
        dbc.CardBody(
            [

            ]
        ),
    ],
)

elevation_container = dbc.Card(
    children=[
        dbc.CardHeader(html.H6("Elevation Gain during run")),
        dbc.CardBody(
            [

            ]
        ),

    ],
)

hr_container = dbc.Card(
    children=[
        dbc.CardHeader(html.H6("Heart Rate")),
        dbc.CardBody(
            [

            ]
        ),
    ],
)

pace_container = dbc.Card(
    children=[
        dbc.CardHeader(html.H6("Rolling Pace")),
        dbc.CardBody(
            [

            ]
        ),
    ],
)


# Left column
rundata_column = dbc.Col(
    children=[
        route_container,
        elevation_container,
        hr_container,
        pace_container,
    ],
)


# Right column
heatmap_column = dbc.Col(
    children=[
        # 2. Heatmap
        dbc.Card(
            [
                dbc.CardHeader([html.H6("Running Heatmap")]),
                dbc.CardBody(
                    [
                        dcc.Graph(id="monthbyday-heatmap"),
                    ],
                    style={"padding": "0px"}
                ),
            ]
        ),
    ],
    width={"size": "auto", "order": "last"},
)

# Row(s)
row1 = dbc.Row(
    children=[
        dbc.Col(
            [
                # 1.1 Year dropdown
                html.Div(
                    [hmap_select_yr],
                    style={"width": "33%",
                           "display": "inline-block",
                           "padding-left": "5px"},
                ),
                # 1.2 Z dropdown
                html.Div(
                    [hmap_select_z],
                    style={"width": "65%", "float": "right",
                           "display": "inline-block"},
                ),
            ],
            width={"size": 4, "offset": 8},
        )
    ],
    class_name="g-6"
)

row2 = dbc.Row(
    children=[
        rundata_column,
        heatmap_column
    ],
    class_name="g-8",
)

row3 = dbc.Row(
    children=[
    ]
)

# Page layout
layout = html.Div(
    children=[
        navbar,
        dbc.Container(
            children=[
                row1,
                row2,
            ],
        )
    ],
)
