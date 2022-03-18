""" Contains callbacks imports.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from dashboard.index import app
from dashboard.pages import home, heatmapview

from dashboard.layout.callbacks import nav_callbacks
from dashboard.layout.callbacks import timeseries_callbacks
from dashboard.layout.callbacks import heatmap_callbacks


app.layout = html.Div(
    children=[
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
    ]
)
