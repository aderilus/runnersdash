""" Generates an activity heatmap, with the calendar month in the x-axis,
    and calendar day in the y-axis. The z-axis corresponds to some
    user-selected metric of the activity.
"""


from numpy import sort
from dash import dcc
from utils import get_resampled_runs, get_column_extremas, COLMAPPER
import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

VERBOSE = True
DATA = get_resampled_runs()  # Daily resampled running metricss
DATA_YEAR_RANGE = sort(DATA['Year'].unique().flatten())

# Get extremas of the z-values
Z_OPTIONS = [COLMAPPER['distance'], COLMAPPER['avg pace']]
Z_EXTREMA = dict(zip(Z_OPTIONS, [get_column_extremas(DATA, z) for z in Z_OPTIONS]))
if VERBOSE:
    print(Z_EXTREMA)


def build_heatmap(year, x_col, y_col, z_col, hmap_id, cscale='agsunset_r'):
    """
    Args:
        year (int):
        x_col (str):
        y_col (str):
        z_col (str):
        hmap_id (str):
    Kwargs:
        cscale (str): Plotly colorscale id, default 'agsunset_r'.
            See https://plotly.com/python/builtin-colorscales/
            for more options.
    TODO:
        - Implement checks on arguments
    """
    df = DATA.loc[DATA['Year'] == year]

    hmap = go.Heatmap(
        x=df[x_col],
        y=df[y_col],
        z=df[z_col],
        name=hmap_id,
        colorscale=cscale,
        colorbar=dict(title=dict(text=z_col,
                                 side='right')),
        zmin=Z_EXTREMA[z][0],
        zmax=Z_EXTREMA[z][1],
        xgap=1,
        ygap=1,
    )

    fig = {
        'data': [hmap],
        'layout': go.Layout(
            xaxis=dict(title=x_col,
                       showgrid=False),
            yaxis=dict(title=y_col,
                       showgrid=False,),
            margin=dict(l=20, r=10, t=35, b=10),
        )
    }

    return go.Figure(fig)


# --- HEATMAP INTERACTIVE ELEMENTS --- #
hmap_select_yr = dcc.Dropdown(
    options=[
        {"label": str(i), "value": i} for i in DATA_YEAR_RANGE
    ],
    value=DATA_YEAR_RANGE[-1],
    placeholder="Year",
    id="heatmap-year",
)


hmap_select_z = dcc.Dropdown(
    options=[
        {"label": i, "value": i} for i in Z_OPTIONS
    ],
    value=Z_OPTIONS[0],
    id="heatmap-zaxis",
)
