""" Functions and components associated with environmental factors section
of the dashboard.
"""

from dash import dcc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly import colors
from pandas import cut, IntervalIndex, Interval
from numpy import arange
from math import floor, ceil
from dashboard.assets.custom_themes import custom_theme1
from utils import (get_latest_daily_agg,
                   colmapper, get_unit_from_string,
                   )

# Load dataset and get column names
data = get_latest_daily_agg()

# Get column names
indoor_workout = colmapper('Indoor Workout', data.columns)
avg_temp = colmapper('Temperature', data.columns)
avg_humid = colmapper('Humidity', data.columns)
avg_mets = colmapper('Avg MET', data.columns)
avg_pace = colmapper('Avg Pace', data.columns)
tot_dist = colmapper('Total Distance', data.columns)
tot_dur = colmapper('Total Duration', data.columns)
elev_gain = colmapper('Elevation Ascended', data.columns)
vo2 = colmapper('VO2', data.columns)
hrvar = colmapper('Heart Rate Variability', data.columns)
resrate = colmapper('Respiratory Rate', data.columns)

# --- dcc COMPONENTS --- #
y_options = [avg_pace, avg_mets, vo2, hrvar, resrate, tot_dist, tot_dur, elev_gain]
weather_factors_y = dcc.Dropdown(
    options=[
        {"label": i, "value": i} for i in y_options
    ],
    value=y_options[0],
    id='weather-factors-y',
    clearable=False,
)
weather_factors_plot = dcc.Graph(id="weather-factors-plot")


# --- PLOT BUILDING FUNCTIONS --- #
def build_weather_factors_plot(y):

    # Filter dataset to 1) outdoor workouts, 2) where Temp is not null
    dfiltered = data[(data[indoor_workout] < 1) & (data[avg_temp].notna())]

    # Get units
    y_unit = get_unit_from_string(y)
    humid_unit = get_unit_from_string(avg_humid)
    temp_unit = get_unit_from_string(avg_temp)

    # Figure configs and definition
    subplot_heights = [0.33, 0.33, 0.33]
    vspace = 0.1
    fig = make_subplots(rows=3, cols=1,
                        vertical_spacing=vspace,
                        row_heights=subplot_heights,
                        )

    # Trace configs
    trace_name = y.split(' (')[0]
    trace_hover = ["Date: %{customdata}",
                   "Temp: %{y:.2f}" + f" {temp_unit}",
                   "Humidity: %{x} " + f"{humid_unit}<br>",
                   f"{trace_name}: " + "%{text:.2f}" + f" {y_unit}"
                   ]

    # (x: Avg. Humidity, y: Avg. Temp, z: y parameter)
    fig.add_trace(
        go.Scatter(x=dfiltered[avg_humid],
                   y=dfiltered[avg_temp],
                   name=trace_name,
                   mode='markers',
                   marker=dict(
                       size=7,
                       color=dfiltered[y],
                       colorscale='sunset',
                       colorbar=dict(title=dict(text=y,
                                                side='right'),
                                     len=subplot_heights[2],
                                     y=(subplot_heights[2] - vspace) * 0.65),
                       showscale=True),
                   text=dfiltered[y],
                   customdata=dfiltered.index.date,
                   hovertemplate=trace_hover,
                   showlegend=False,
                   ),
        row=3, col=1,
    )

    # Averaged y binned across temperature (x: Avg. temp, y: y parameter)
    # The following DataFrame is used for both temp and humidity box plots
    dbinned = dfiltered[[avg_temp, avg_humid, y]].copy()

    # Build temperature intervals
    tintervals = f'Avg. Temp Interval ({temp_unit})'
    t_delta = 5
    tbin_start = floor(dbinned[avg_temp].min())
    tbin_start -= tbin_start % 10
    tbin_end = ceil(dbinned[avg_temp].max())
    tbin_end += 10 - (tbin_end % 10)
    tbins = arange(start=tbin_start,
                   stop=tbin_end,
                   step=t_delta,
                   )
    dbinned[tintervals] = cut(dbinned[avg_temp], bins=tbins, right=False)
    dbinned['T_Left'] = IntervalIndex(dbinned[tintervals]).left
    t_cscale = colors.sample_colorscale(colors.sequential.thermal,
                                        samplepoints=len(tbins))
    for idx, i in enumerate(tbins):
        tfiltered = dbinned[dbinned['T_Left'] == i]
        fig.add_trace(
            go.Box(
                x=tfiltered['T_Left'],
                y=tfiltered[y],
                name=f"[{i}, {i + 5}) {temp_unit}",
                showlegend=False,
                marker_color=t_cscale[idx],
                hoverinfo='name+y',
            ),
            row=1, col=1
        )

    # Averaged y binned across humidity (x: Avg. Humidity, y: y param)
    # Build humidity bins
    hintervals = f"Avg. Humidity Interval ({humid_unit})"
    hbin_start = floor(dbinned[avg_humid].min())
    hbin_end = ceil(dbinned[avg_humid].max())
    h_delta = 1000
    hbins = arange(start=hbin_start,
                   stop=hbin_end,
                   step=h_delta)
    dbinned[hintervals] = cut(dbinned[avg_humid], bins=hbins, right=False)
    dbinned['H_Left'] = IntervalIndex(dbinned[hintervals]).left
    for idx, j in enumerate(hbins):
        hfiltered = dbinned[dbinned['H_Left'] == j]
        fig.add_trace(
            go.Box(
                x=hfiltered['H_Left'],
                y=hfiltered[y],
                name=f"[{j}, {j + h_delta}) {humid_unit}",
                showlegend=False,
                marker_color='#6AACB9',
                hoverinfo='name+y',
            ),
            row=2, col=1,
        )

    # Axis configs
    x2_ticktext = [str(i) for i in hbins]
    x2_ticktext[0] = f"[{hbins[0]},<br>{hbins[0] + h_delta})"
    fig.update_layout(
        template=custom_theme1,
        height=750,
        xaxis=dict(
            title_text=f'Avg. temp interval ({temp_unit}), ΔT = {t_delta}',
            tickmode='array',
            tickvals=tbins,
            ticktext=[f"[{i}, {i + t_delta})" for i in tbins]),
        yaxis=dict(title_text=y),
        xaxis2=dict(title_text=f'Avg. humidity interval ({humid_unit}), ΔH = {h_delta}',
                    tickmode='array',
                    tickvals=hbins,
                    ticktext=x2_ticktext),
        yaxis2=dict(title_text=y),
        xaxis3=dict(title_text=avg_humid),
        yaxis3=dict(title_text=avg_temp),
    )

    return fig
