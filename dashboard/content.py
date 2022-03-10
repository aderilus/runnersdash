""" Contains callbacks imports.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from dashboard.index import app
from dashboard.pages import home, heatmapview
# from dashboard.layout.header import header
# from dashboard.layout.weekstats import week_stat_container
# from dashboard.layout.activityheatmap import (hmap_select_yr,
#                                               hmap_select_z)
# from dashboard.layout.recent_views_nav import primary_radio

from dashboard.layout.callbacks import nav_callbacks
from dashboard.layout.callbacks import weekstats_callbacks
from dashboard.layout.callbacks import monthstats_callbacks
from dashboard.layout.callbacks import heatmap_callbacks

# left_col = dbc.Col(
#     children=[
#         html.Div(
#             primary_radio, style={"display": "flex",
#                                   "justify-content": "center"},
#         ),
#         week_stat_container
#     ],
#     width={"order": "first"},
#     class_name="testleftcol",
# )

# monthbyday_heatmap = dbc.Col(
#     html.Div(
#         children=[
#             html.Div(
#                 [
#                     html.Div([hmap_select_yr],
#                              style={"width": "30%", "display": "inline-block"}),
#                     html.Div([hmap_select_z],
#                              style={"width": "65%", "float": "right", "display": "inline-block"}),
#                 ],
#             ),

#             dcc.Graph(id="monthbyday-heatmap",
#                       #   style={"padding-left": "4rem", },
#                       )
#         ],
#     ),
#     width={"size": "auto", "order": "last"},
#     class_name="testrightcol",
# )

# main_container = html.Div(
#     children=[
#         dbc.Row(
#             children=[
#                 left_col,
#                 monthbyday_heatmap,
#             ],
#             class_name="g-6",
#         ),
#         dbc.Row(
#             children=[
#                 html.H6("Row 2"),
#             ],
#         ),
#     ],
# )

# app.layout = html.Div(
#     children=[
#         header,
#         dbc.Container(
#             children=[
#                 main_container,
#             ],
#             fluid=False,  # fluid=True to remove margins that dbc.Container sets up
#         )
#     ])


app.layout = html.Div(
    children=[
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
    ]
)
