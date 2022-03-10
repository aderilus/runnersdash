import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
from pandas import to_datetime
from dash import html, dcc
from calendar import monthrange
from math import floor, ceil
from utils import (get_column_extremas, get_latest_daily_agg,
                   get_latest_weekly_agg, get_weeks_of_month,
                   DAY_MAP)

AXES_OFFSET = 0.4

# --- INDIVIDUAL STATS --- #

week_stat1 = html.Div(
    [
        dbc.Alert(
            [
                html.P("Total Distance"),
                html.H5(children=[],
                        id="week-stat-distance"),
            ],
            color="primary",
        ),
    ]
)

week_stat2 = html.Div(
    [
        dbc.Alert(
            [
                html.P("Total Duration"),
                html.H5(children=[],
                        id="week-stat-duration"),
            ],
            color="warning",
        )
    ]
)

week_stat3 = html.Div(
    [
        dbc.Alert(
            [
                html.P("Avg. Pace"),
                html.H5(children=[],
                        id="week-stat-pace"),
            ],
            color="secondary",
        )
    ]
)

week_stat_container = dbc.Row(
    [
        dbc.Col([week_stat1]),
        dbc.Col([week_stat2]),
        dbc.Col([week_stat3]),
    ],
    style={"display": "flex",
           "justify-content": "center",
           "padding": "1.5rem",
           },
)

# --- GRAPHS --- #
week_time_series = dcc.Graph(id="week-time-series")


# --- FUNCTIONS --- #
def get_weekly_stat(metric, on_week):
    """
    Args:
        metric (str): Column name of the metric.
        on_week(datetime.date): The start date of the week,
                                formatted as '%Y-%m-%d'.

    """
    data = get_latest_weekly_agg()
    dfiltered = data[data['Week'] == on_week]

    return dfiltered[metric].iloc[0]


# --- GRAPH FUNCTIONS --- #
def build_weekly_timeseries(start_date, y1col, y2col=None):
    """ Returns a bar graph of a week's view of running data.

    Args:
        start_date (datetime.date): Date of the start of week.
        y1col (str): Name of the column to plot (bar). Must match
                     with that of the daily aggregate file.
        y2col (str): Name of another column to plot (line+scatter).
    """

    df = get_latest_daily_agg()
    end_date = start_date + timedelta(days=6)
    dfiltered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    # dfiltered = df.loc[idx:idx + 6]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # -- Y1 (Bar) -- #
    # For legend label, remove units. The axis label will have it.
    y1_label_sans_unit = y1col.split('(')[0]
    fig.add_trace(
        go.Bar(x=dfiltered['Date'], y=dfiltered[y1col],
               name=y1_label_sans_unit,
               ),
        secondary_y=False,
    )

    # update x-axis label and ticks
    xvalues = [start_date + timedelta(days=i) for i in range(7)]
    xlabels = ["{0} {2}/{1}".format(DAY_MAP[d.isoweekday()], d.day, d.month) for d in xvalues]
    fig.update_layout(
        xaxis=dict(
            title='',
            tickmode='array',
            tickvals=xvalues,
            ticktext=xlabels,
        ),
        margin=dict(l=20, r=10, t=35, b=10),
        height=400,
    )

    # Implement absolute y scale across the weeks based on min, max y-values
    # across the same month as start_date
    start_dates_of_each_week = get_weeks_of_month(start_date.month, start_date.year)
    start_timestamps = [to_datetime(i) for i in start_dates_of_each_week]
    first_date = start_timestamps[0]
    last_date = start_timestamps[-1] + timedelta(days=7)
    df_current_month = df[(df['Date'] >= first_date) & (df['Date'] < last_date)]

    y1_min, y1_max = get_column_extremas(df_current_month, y1col)

    fig.update_yaxes(
        secondary_y=False,
        range=[floor(y1_min), ceil(y1_max)],
        title_text=y1col,
    )

    # --- Y2 (Scatter) --- #
    if y2col is not None:

        # Implement an absolute scale based on min, max y2 values
        # within the same month of start_date
        try:
            y2_min, y2_max = get_column_extremas(df_current_month, y2col)

            y2_label_sans_unit = y2col.split('(')[0]
            fig.add_trace(
                go.Scatter(x=dfiltered['Date'], y=dfiltered[y2col],
                           name=y2_label_sans_unit, mode='lines+markers',
                           connectgaps=True),
                secondary_y=True,
            )

            fig.update_yaxes(
                secondary_y=True,
                range=[floor(y2_min - AXES_OFFSET), ceil(y2_max + AXES_OFFSET)]
            )
        except IndexError as e:
            print("build_weekly_timeseries(): ", e)

    return fig
