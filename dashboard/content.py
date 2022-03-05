""" Contains callbacks imports
"""

from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

from dashboard.index import app
from dashboard.layout.header import header

nav = dbc.ButtonGroup(
    children=[
        dbc.Button("Main view"),
        dbc.Button("Middle"),
        dbc.Button("Right")
    ],
    class_name="nav-buttons",
)

left_col = dbc.Col(
    class_name="testleftcol",
    children=[
        html.H6("Hello")
    ],
    width="auto",
)

right_col = dbc.Col(
    class_name="testrightcol",
    children=[
        html.H6("World")
    ],
)

main_container = dbc.Container(
    class_name="testmaincontainer",
    children=[
        dbc.Row(
            children=[
                left_col,
                right_col
            ]
        ),
    ],
    fluid=True,
)

app.layout = html.Div(
    children=[
        header,
        nav,
        main_container,
    ])
