""" Object and function definitions for running habits component of
dashboard.
"""

from dash import dcc, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from math import ceil
from pandas import NamedAgg
from dashboard.assets.custom_themes import custom_theme1
from dashboard.layout.graphing import add_error_bands
from utils import (get_column_extremas,
                   get_running_logs,
                   get_resampled_runs,
                   colmapper,
                   get_unit_from_string)


# --- dcc COMPONENTS --- #
rh_title = html.H5(children="Running Habits", id='running-habits-title')
rh_dow = dcc.Graph(id='running-habits-dow')  # Day of Week histogram
rh_tod = dcc.Graph(id='running-habits-tod')  # Time of day histogram
rh_run_distance = dcc.Graph(id='running-habits-rundist')  # Run distance histogram


def generate_plot_title(title_prefix, input_year):
    """ Returns a string.
    """
    title_suffix = input_year if type(input_year) == int else "across all years"
    return f"{title_prefix} {title_suffix}"


# --- PLOT BUILDING FUNCTIONS --- #
def build_dow_histogram(yr):
    """ Returns a plotly.graph_objects instance. Creates histogram of runs
    and distance per run according to their day of the week, across
    the input year.

    Args:
        yr (int): Year.

    Returns:
        A plotly.graph_objects instance. This figure is a 2-row plot, where the
        first row is the histogram.
    """

    data = get_running_logs()
    # Filter data
    dfiltered = data[data['startDate'].dt.year == yr].copy() if type(yr) == int else data.copy()

    # Get total distance column
    total_dist = colmapper('Total Distance', dfiltered.columns)

    fig = make_subplots(rows=2, cols=1,
                        vertical_spacing=0.08,
                        # column_widths=[0.2, 0.4, 0.2],
                        )

    # Day of Week (x1, y1)
    dows_ordered = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    if 'DOW numeric' not in dfiltered.columns:
        dfiltered['DOW numeric'] = dfiltered['startDate'].dt.dayofweek
        dfiltered['Day of Week'] = dfiltered['DOW numeric'].map(dict(zip(range(7), dows_ordered)))

    # Day of Week histogram (r1, c1)
    fig.add_trace(
        go.Histogram(
            x=dfiltered['Day of Week'],
            nbinsx=7,
            name="Day of Week",
        ),
        row=1, col=1,
    )

    # Distance per run for each day of the week (r2, c1) (x4, y4)
    avgdistperdow = dfiltered[['DOW numeric', total_dist]].copy().groupby(['DOW numeric']).agg(
        mean=NamedAgg(column=total_dist, aggfunc='mean'),
        std=NamedAgg(column=total_dist, aggfunc='std')
    )
    avgdistperdow.columns = [[total_dist, total_dist], avgdistperdow.columns]
    avgdistperdow['Day of Week'] = avgdistperdow.index.map(dict(zip(range(7), dows_ordered)))

    # Error bands
    fig = add_error_bands(fig, error_type='std',
                          xcol=avgdistperdow['Day of Week'],
                          ycol=avgdistperdow[total_dist],
                          r=2, c=1, linetype='spline')

    # Avg distance per day of week
    fig.add_trace(
        go.Scatter(
            x=avgdistperdow['Day of Week'],
            y=avgdistperdow[total_dist]['mean'],
            xaxis="x2",
            yaxis="y2",
            name=f"Avg. Distance ({get_unit_from_string(total_dist)}) per run",
            mode='lines+markers',
            line_shape='spline',
        ),
        row=2, col=1,
    )

    x1_axis_settings = dict(
        type='category',
        nticks=7,
        categoryorder='array',
        categoryarray=dows_ordered,
    )

    fig.update_layout(
        title="Day of Week",
        showlegend=False,
        template=custom_theme1,
        xaxis=x1_axis_settings,  # Day of week histogram
        xaxis2=x1_axis_settings,  # Avg. Distance per DOW
        yaxis=dict(title_text="# of runs"),
        yaxis2=dict(title_text=f"Avg. distance ({get_unit_from_string(total_dist)}) per run"),
        bargap=0.03,
    )

    fig.update_layout(
        xaxis2=dict(title_text="Day of week of run")
    )

    return fig


def build_tod_histogram(yr):
    """ Returns a plotly.graph_objects instance. Creates histogram of runs
    and distance per run according to their start hour (time of day), across
    the input year.

    Args:
        yr (int): Year.

    Returns:
        A plotly.graph_objects instance. This figure is a 2-row plot, where the
        first row is the histogram.
    """

    # Load data
    data = get_running_logs()
    # Filter data
    dfiltered = data[data['startDate'].dt.year == yr].copy() if type(yr) == int else data.copy()

    # Get total distance column
    total_dist = colmapper('Total Distance', dfiltered.columns)

    fig = make_subplots(rows=2, cols=1,
                        vertical_spacing=0.08,
                        )

    # Time of Day Histogram (r1, c1)
    dfiltered.loc[:, 'runStartHour'] = dfiltered['startDate'].dt.hour

    fig.add_trace(
        go.Histogram(
            x=dfiltered['runStartHour'],
            nbinsx=24,
            name="Run Start Hour",
            xaxis="x1",
            yaxis="y1",
        ),
        row=1, col=1,
    )

    # Distance run per time of day (r2, c1)
    avgdistperhour = dfiltered[['runStartHour', total_dist]].copy().groupby(['runStartHour']).agg(
        mean=NamedAgg(column=total_dist, aggfunc='mean'),
        std=NamedAgg(column=total_dist, aggfunc='std')
    )
    avgdistperhour.columns = [[total_dist, total_dist], avgdistperhour.columns]

    # Distance per run time - error band
    fig = add_error_bands(fig,
                          error_type='std',
                          xcol=avgdistperhour.index,
                          ycol=avgdistperhour[total_dist],
                          r=2, c=1,
                          linetype='spline',
                          )

    # Distance per run time
    fig.add_trace(
        go.Scatter(
            x=avgdistperhour.index,
            y=avgdistperhour[total_dist]['mean'],
            xaxis="x2",
            yaxis="y2",
            name=f"Avg. Distance ({get_unit_from_string(total_dist)}) per run",
            mode='lines+markers',
            line_shape='spline',
        ),
        row=2, col=1,
    )

    x_axis_settings = dict(
        tickmode='array',
        tickvals=list(range(24)),
        ticktext=list(range(24)),
        range=[0, 24],
    )

    fig.update_layout(
        title="Run Start Hour",
        showlegend=False,
        template=custom_theme1,
        xaxis=x_axis_settings,  # Time of day histogram
        xaxis2=x_axis_settings,
        yaxis=dict(title_text="# of runs"),
        yaxis2=dict(title_text=f"Avg. distance ({get_unit_from_string(total_dist)}) per run"),
        bargap=0.03,
    )

    fig.update_layout(
        xaxis2=dict(title_text="Hour of day of run start time")
    )

    return fig


def build_runmetric_histogram(yr):
    """ Returns a plotly.graph_objects instance. Creates histograms of runs
    across the input year, according to
            1) total distance
            2) total duration
            3) avg. METs

    Args:
        yr (int): Year.

    Returns:
        A plotly.graph_objects instance. This figure is a 3-column plot.
    """
    # Load data
    data = get_resampled_runs()
    # Filter out empty rows (days with no runs)
    data = data[data['startDate'].notna()]
    # Filter data by selected year
    dfiltered = data[data.index.year == yr].copy() if type(yr) == int else data.copy()

    # Get column names
    total_dist = colmapper('Total Distance', dfiltered.columns)
    total_dur = colmapper('Duration', dfiltered.columns)
    avg_mets = colmapper('METs', dfiltered.columns)

    units = {i: get_unit_from_string(i) for i in [total_dist, total_dur, avg_mets]}

    fig = make_subplots(rows=1, cols=3,
                        horizontal_spacing=0.03,
                        # column_widths=[0.33, 0.33, 0.33]
                        )

    # Distance per run histogram (r1, c1)
    dist_bin_start = 0
    dist_bin_end = max(50, get_column_extremas(dfiltered, total_dist)[1])
    dist_bin_delta = 2.5
    fig.add_trace(
        go.Histogram(
            x=dfiltered[total_dist],
            xbins=dict(start=dist_bin_start, end=dist_bin_end, size=dist_bin_delta),
            name=f"Distance ({units[total_dist]})",
            xaxis="x1",
            yaxis="y1",
        )
    )

    # Duration per run histogram (r1, c2)
    dur_bin_start = 0
    dur_bin_end = ceil(get_column_extremas(dfiltered, total_dur)[1])
    dur_bin_delta = 15
    fig.add_trace(
        go.Histogram(
            x=dfiltered[total_dur],
            xbins=dict(start=dur_bin_start, end=dur_bin_end, size=None),
            name=f"Duration ({units[total_dur]})",
            xaxis="x2",
            yaxis="y2",
        )
    )

    # Average METs per run histogram (r1, c3)
    fig.add_trace(
        go.Histogram(
            x=dfiltered[avg_mets],
            name=f"Avg METs ({units[avg_mets]})",
            xaxis="x3",
            yaxis="y3",
        )
    )

    # x1 ticks
    dist_range_end = int(dist_bin_end / dist_bin_delta)
    dist_bin_ticks = [i * dist_bin_delta for i in range(dist_bin_start, dist_range_end)]

    # x2 ticks

    fig.update_layout(
        # title="Distance binned",
        showlegend=False,
        template=custom_theme1,
        xaxis=dict(
            title_text=f"Daily total distance ({units[total_dist]})",
            tickmode='array',
            tickvals=[i + (dist_bin_delta / 2) for i in dist_bin_ticks],
            ticktext=[f"[{i}, {i + dist_bin_delta - 0.01}]" for i in dist_bin_ticks],
        ),
        yaxis=dict(title_text="# of runs",),
        xaxis2=dict(title_text=f"Daily total duration ({units[total_dur]})"),
        xaxis3=dict(title_text=f"Daily avg METs ({units[avg_mets]})"),
        bargap=0.03,
    )

    return fig
