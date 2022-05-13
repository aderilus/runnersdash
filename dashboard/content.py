""" Contains callbacks imports.
"""

from dash import html, dcc

from dashboard.index import app
from dashboard.pages import home

from dashboard.layout.callbacks import (nav_callbacks,
                                        timeseries_callbacks,
                                        heatmap_callbacks,
                                        statscard_callbacks,
                                        runninghabits_callbacks,
                                        environmental_callbacks)


app.layout = html.Div(
    children=[
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
    ]
)
