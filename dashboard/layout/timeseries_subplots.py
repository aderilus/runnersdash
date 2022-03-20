""" Function and dcc component definitions for graphs
triggered by the main time-series graph interactions.

Callbacks for the graphs defined here are located in
timeseries_callbacks.py.
"""
from dash import dcc
from plotly.subplots import make_subplots
from pandas import Timestamp, Timedelta
from dashboard.layout.graphing import simple_time_series
import plotly.graph_objects as go
from utils import (get_latest_daily_agg,
                   get_latest_weekly_agg,
                   )


# --- [Y-VALUE] OVER SELECTED WEEK --- #
week_ts_subplot = dcc.Graph(id="week-ts-subplot")


def build_week_ts_subplot(input_datestring, ycol):
    """ Bar graph showing total distance or other metric across the span of
    a selected week, starting from date_start.

    Associated with graph id="weekly-time-series".

    Args:
        input_datestring (str): Takes in a date formatted as '%Y-%m-%d', or
                                if 'most recent' is passed in, generates
                                the graph from the most recent week in
                                dataset.
        ycol (str): Column name for y-axis metric.

    Returns:
        A plotly.graph_objects.Bar() figure.
    """
    date_col = 'Date'
    sub = make_subplots(rows=1, cols=1)

    if input_datestring == 'most recent':
        start_date = get_latest_weekly_agg()['Week'].iloc[-1]
    else:
        start_date = Timestamp(input_datestring)

    data = get_latest_daily_agg()  # Load entire daily dataset

    # Filter data
    date_end = start_date + Timedelta(days=6)

    dfiltered = data[(data[date_col] >= start_date) & (data[date_col] <= date_end)]
    fig = simple_time_series(sub, dfiltered, date_col, ycol,
                             xlabel=None,
                             ylabel=None,
                             plot_type='Bar',
                             row_idx=None,
                             col_idx=None,
                             width_px=None,
                             height_px=150,
                             bar_text_template="")

    # Update x-axis ticks and plot title
    x_tick_labels = []
    for i, d in enumerate(dfiltered[date_col]):
        if i == 0 or i == len(dfiltered) - 1:
            x_tick_labels.append(f"{d.day_name()[:3]}<br>{d.day} {d.month_name()[:3]}")
        else:
            x_tick_labels.append(f"{d.day_name()[:3]}<br>{d.day}")

    plot_title = "{0} per day of week".format(ycol)

    fig.update_layout(
        xaxis=dict(showgrid=False,
                   tickmode='array',
                   nticks=7,
                   ticks='inside',
                   tickvals=dfiltered[date_col],
                   ticktext=x_tick_labels,
                   ),
        title=dict(pad=dict(t=8, l=4),
                   text=plot_title,
                   font=dict(size=15),
                   ),
    )

    return fig


# --- NUM. OF RUNS IN EACH WEEK OF MONTH --- #
nruns_in_month = dcc.Graph(id="nruns-ts-subplot")


def build_nruns_in_month(input_datestring):  # TODO

    if input_datestring == 'most recent':
        start_date = get_latest_weekly_agg()['Week'].iloc[-1]
    else:
        start_date = Timestamp(input_datestring)

    fig = go.Heatmap()

    return fig
