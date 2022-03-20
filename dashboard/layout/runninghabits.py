""" Object and function definitions for running habits component of
dashboard.
"""

from unicodedata import category
from dash import dcc
from pandas import Timestamp
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import get_column_extremas, get_resampled_runs, COLMAPPER, DAY_MAP, get_unit_from_string
from dashboard.assets.custom_themes import custom_theme1, toggle_colorway


running_habit_plots = dcc.Graph(id="running-habits-plots")


def build_habit_plots(input_year):
    """

    Args:
        input_year (int or str): Takes in year as an int, or the string "All".
    """
    v_space = 0.08
    h_space = 0.04
    title_prefix = "Your running habits across {0}"
    plot_title = title_prefix.format(input_year) if type(input_year) == int else title_prefix.format("all years")

    # Load data
    data = get_resampled_runs()
    ran = COLMAPPER['distance']
    data = data[(data[ran].notna()) | (data[ran] > 0)]

    date_col = 'Date'
    dfiltered = data[data[date_col].dt.year == input_year].copy() if type(input_year) == int else data.copy()

    fig = make_subplots(rows=2, cols=3, vertical_spacing=v_space,
                        horizontal_spacing=h_space,
                        column_widths=[0.2, 0.4, 0.2],
                        )

    # Day of Week (x1, y1)
    dows_ordered = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    fig.add_trace(
        go.Histogram(
            x=dfiltered['Day of Week'],
            nbinsx=7,
            name="Day of Week",
        ),
        row=1, col=1,
    )

    # Time of Day Histogram (x2, y2)
    dfiltered.loc[:, 'runStartHour'] = dfiltered['runStartTime'].dt.hour

    fig.add_trace(
        go.Histogram(
            x=dfiltered['runStartHour'],
            nbinsx=24,
            name="Run Start Hour",
            xaxis="x2",
            yaxis="y2",
        ),
        row=1, col=2,
    )

    # Distance per run histogram (x3, y3)
    dist_bin_start = 0
    dist_bin_end = max(50, get_column_extremas(dfiltered, ran)[1])
    dist_bin_delta = 2.5
    fig.add_trace(
        go.Histogram(
            x=dfiltered[ran],
            xbins=dict(start=dist_bin_start, end=dist_bin_end, size=dist_bin_delta),
            name="Avg. distance per run",
            xaxis="x3",
            yaxis="y3",
        )
    )

    # Distance per run for each day of the week (x4, y4)
    dfiltered.loc[:, 'DOW numeric'] = dfiltered.loc[:, 'Date'].copy().dt.day_of_week
    avgdistperdow = dfiltered[['DOW numeric', ran]].copy().groupby(['DOW numeric']).mean()
    avgdistperdow.loc[:, 'Day of Week'] = avgdistperdow.index.map(dict(zip(range(7), dows_ordered)))

    fig.add_trace(
        go.Scatter(
            x=avgdistperdow['Day of Week'],
            y=avgdistperdow[ran],
            xaxis="x4",
            yaxis="y4",
            name=f"Avg. Distance ({get_unit_from_string(ran)}) per run",
            mode='lines+markers',
            line_shape='spline',
        ),
        row=2, col=1,
    )

    # Distance run per time of day (x5, y5)
    avgdistperhour = dfiltered[['runStartHour', ran]].copy().groupby(['runStartHour']).mean()

    fig.add_trace(
        go.Scatter(
            x=avgdistperhour.index,
            y=avgdistperhour[ran],
            xaxis="x5",
            yaxis="y5",
            name=f"Avg. Distance ({get_unit_from_string(ran)}) per run",
            mode='lines+markers',
            line_shape='spline',
        ),
        row=2, col=2,
    )

    # Update axes
    x1_axis_settings = dict(
        type='category',
        nticks=7,
        categoryorder='array',
        categoryarray=dows_ordered,
    )

    x2_axis_settings = dict(
        tickmode='array',
        tickvals=list(range(24)),
        ticktext=list(range(24)),
        range=[0, 24],
    )

    # xaxis3
    dist_range_end = int(dist_bin_end / dist_bin_delta)
    dist_bin_ticks = [i * dist_bin_delta for i in range(dist_bin_start, dist_range_end)]

    fig.update_layout(
        title=plot_title,
        showlegend=False,
        template=custom_theme1,
        xaxis=x1_axis_settings,  # Day of week histogram
        xaxis2=x2_axis_settings,  # Time of day histogram
        xaxis3=dict(
            title_text=f"{COLMAPPER['avg distance']} per run",
            tickmode='array',
            tickvals=[i + (dist_bin_delta / 2) for i in dist_bin_ticks],
            ticktext=[f"[{i}, {i + dist_bin_delta - 0.01}]" for i in dist_bin_ticks],
        ),
        xaxis4=x1_axis_settings,  # Distance/run per day of week
        xaxis5=x2_axis_settings,  # Distance run per hour of day
        yaxis=dict(
            title_text="# of runs",
        ),
        yaxis3=dict(
            title_text="# of runs",
        ),
        yaxis4=dict(
            title_text=f"Avg. distance ({get_unit_from_string(ran)}) per run"
        ),
        bargap=0.03,
    )

    fig.update_layout(
        xaxis4=dict(title_text="Day of week of run"),
        xaxis5=dict(title_text="Hour of day of run start time")
    )

    return fig
