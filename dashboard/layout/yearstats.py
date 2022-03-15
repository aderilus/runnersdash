import plotly.graph_objects as go
from dash import html, dcc
from math import floor, ceil
from plotly.subplots import make_subplots
from utils import (get_latest_monthly_agg,
                   get_column_extremas,
                   MONTHS_MAP)

y1_offset = 10
y2_offset = 2

year_time_series = dcc.Graph(id="year-time-series")


def build_yearview_timeseries(input_year, y1col, y2col=None):
    """
    """
    data = get_latest_monthly_agg()
    dfiltered = data[data['Year'] == input_year]

    x_labels = [MONTHS_MAP[m][:3] for m in dfiltered['Month']]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # --- Y1 --- #
    secondbar = y1col.replace("Total", "Avg.")
    fig.add_trace(
        go.Bar(x=dfiltered['Month'], y=dfiltered[y1col],
               name=y1col, offsetgroup=0,
               ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(x=dfiltered['Month'], y=dfiltered[secondbar],
               name=secondbar, offsetgroup=1),
        secondary_y=False,
    )

    fig.update_layout(
        xaxis=dict(
            title=str(input_year),
            tickmode='array',
            tickvals=dfiltered['Month'],
            ticktext=x_labels,
        ),
        margin=dict(l=20, r=10, t=35, b=10),
    )

    # Implement absolute y-scale across all years
    y1_min, y1_max = get_column_extremas(data, y1col)

    fig.update_yaxes(
        secondary_y=False,
        range=[floor(y1_min), ceil(y1_max + y1_offset)],
        title_text=y1col,
    )

    if y2col is not None:
        y2_min, y2_max = get_column_extremas(data, y2col)

        fig.add_trace(
            go.Scatter(x=dfiltered['Month'], y=dfiltered[y2col],
                       name=y2col, mode='lines+markers',
                       connectgaps=True),
            secondary_y=True,
        )

        fig.update_yaxes(
            secondary_y=True,
            range=[floor(y2_min - y2_offset), ceil(y2_max + y2_offset)]
        )

    return fig
