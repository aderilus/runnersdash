""" Contains callbacks imports.
"""

from dash import html, dcc
# import dash_bootstrap_components as dbc

from dashboard.index import app
from dashboard.pages import home, heatmapview

from dashboard.layout.callbacks import (nav_callbacks,
                                        timeseries_callbacks,
                                        heatmap_callbacks,
                                        statscard_callbacks,
                                        runninghabits_callbacks)


app.layout = html.Div(
    children=[
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
    ]
)
