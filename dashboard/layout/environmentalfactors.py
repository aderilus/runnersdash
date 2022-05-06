from dash import dcc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dashboard.assets.custom_themes import custom_theme1
from utils import (get_latest_daily_agg,
                   colmapper, get_unit_from_string,
                   )

# Load dataset and get column names
data = get_latest_daily_agg()

# Get column names
indoor_workout = colmapper('Indoor Workout', data.columns)
avg_mets = colmapper('Avg MET', data.columns)
avg_temp = colmapper('Temperature', data.columns)
avg_humid = colmapper('Humidity', data.columns)
avg_pace = colmapper('Avg Pace', data.columns)
tot_dist = colmapper('Total Distance', data.columns)
tot_dur = colmapper('Total Duration', data.columns)
elev_gain = colmapper('Elevation Ascended', data.columns)
vo2 = colmapper('VO2', data.columns)

# dcc Components
y_options = [avg_pace, avg_mets, vo2, tot_dist, tot_dur, elev_gain]
weather_factors_y = dcc.Dropdown(
    options=[
        {"label": i, "value": i} for i in y_options
    ],
    value=y_options[0],
    id='weather-factors-y',
    clearable=False,
)
weather_factors_plot = dcc.Graph(id="weather-factors-plot")


def build_weather_factors_plot(y):

    # # Load and filter dataset
    # data = get_latest_daily_agg()
    # # Get columns
    # indoor_workout = colmapper('Indoor Workout', data.columns)
    # avg_temp = colmapper('Temperature', data.columns)
    # avg_humid = colmapper('Humidity', data.columns)
    # Filter
    dfiltered = data[(data[indoor_workout] < 1) & (data[avg_temp].notna())]

    # Get y units
    y_unit = get_unit_from_string(y)
    humid_unit = get_unit_from_string(avg_humid)
    temp_unit = get_unit_from_string(avg_temp)

    # Figure
    subplot_heights = [0.33, 0.33, 0.33]
    vspace = 0.1
    fig = make_subplots(rows=3, cols=1,
                        vertical_spacing=vspace,
                        row_heights=subplot_heights,
                        )

    # Scatter with y as z-dim
    trace0_name = y.split(' (')[0]
    trace0_hover = ["Date: %{customdata}",
                    "Temp: %{y:.2f}" + f" {temp_unit}",
                    "Humidity: %{x} " + f"{humid_unit}<br>",
                    f"{trace0_name}: " + "%{text:.2f}" + f" {y_unit}"
                    ]
    fig.add_trace(
        go.Scatter(x=dfiltered[avg_humid],
                   y=dfiltered[avg_temp],
                   name=trace0_name,
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
                   hovertemplate=trace0_hover,
                   ),
        row=3, col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=dfiltered[avg_temp],
            y=dfiltered[y],
            name="",
            mode='markers',
            text=dfiltered[y],
            customdata=dfiltered.index.date,
            hovertemplate="<br>".join([trace0_hover[i] for i in [0, 1, 3]]),
            # hovertemplate="<br>".join([
            #     "Date: %{customdata}",
            #     "Temp: %{x}" + f" {temp_unit}",
            #     f"{trace0_name}: " + "%{y:.2f}" + f" {y_unit}",
            # ]),
        ),
        row=1, col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=dfiltered[avg_humid],
            y=dfiltered[y],
            name="",
            mode='markers',
            text=dfiltered[y],
            customdata=dfiltered.index.date,
            hovertemplate="<br>".join([trace0_hover[i] for i in [0, 2, 3]]),
        ),
        row=2, col=1,
    )

    fig.update_layout(
        template=custom_theme1,
        height=700,
        showlegend=False,
        xaxis3=dict(title_text=avg_humid),
        yaxis3=dict(title_text=avg_temp),
        xaxis=dict(title_text=avg_temp),
        yaxis=dict(title_text=y),
        xaxis2=dict(title_text=avg_humid),
        yaxis2=dict(title_text=y)
    )

    return fig
