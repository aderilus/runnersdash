""" Callbacks associated with components defined in statscard.py
"""
from select import select
from dash.dependencies import Input, Output
from dashboard.index import app
from datetime import datetime
from collections import OrderedDict
from dashboard.layout.statscard import (get_list_of_stats)


@app.callback(
    [Output("week-stat-distance", "children"),
     Output("week-stat-duration", "children"),
     Output("week-stat-avgpace", "children"),
     Output("week-stat-avgdistance", "children"),
     Output("week-stat-avgvo2", "children"),
     Output("week-stat-avgrhr", "children"),
     Output("week-stats-title", "children")],
    [Input("weekly-time-series", "clickData")],
    prevent_initial_call=True
)
def update_weekly_stats(click_data):
    if click_data is None:
        return [''] * 7
    else:
        clicked_data_dump = click_data['points'][0]
        selected_date = datetime.strptime(clicked_data_dump['x'], '%Y-%m-%d')

    title_msg = "Week of {}".format(selected_date.strftime('%b %d %Y'))

    return (*get_list_of_stats('week', selected_date), title_msg)


@app.callback(
    [Output("month-stat-distance", "children"),
     Output("month-stat-duration", "children"),
     Output("month-stat-avgpace", "children"),
     Output("month-stat-avgdistance", "children"),
     Output("month-stat-avgvo2", "children"),
     Output("month-stat-avgrhr", "children"),
     Output("month-stats-title", "children")],
    [Input("weekly-time-series", "clickData")],
    prevent_initial_call=True
)
def update_monthly_stats(click_data):
    if click_data is None:
        return [''] * 6
    else:
        clicked_data_dump = click_data['points'][0]
        # type(clicked_data_dump['x']) is str, formatted as %Y-%m-%d
        selected_date = datetime.strptime(clicked_data_dump['x'], '%Y-%m-%d')

    title_msg = "Month of {}".format(selected_date.strftime('%b %Y'))

    return (*get_list_of_stats('month', selected_date), title_msg)
