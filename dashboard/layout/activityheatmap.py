"""
TODO:
    - Figure out where to run preparedatasets.py
        - Write function get_latest_data() to find the datestring
          of most recent Apple Health data.
"""

from dashboard.layout.layout_utils import get_project_root
from numpy import sort
from dash import dcc
import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc


PROJECT_ROOT = get_project_root()
DATA_PATH = PROJECT_ROOT.joinpath('data', '20220303_Running_resampledDaily.csv')
DATA = pd.read_csv(DATA_PATH, dtype={'Day of Week': str,
                                     'Calendar Week': int,
                                     'Day': int,
                                     'Month': str,
                                     'Year': int})
DATA_YEAR_RANGE = sort(DATA['Year'].unique().flatten())

# TODO: Replace this with a dictionary in utils.py:
#   DISTANCE_COL = 'Total Distance (km)
#   DURATION_COL = 'Total Duration (min)
#   DATA_COLNAMES = {'Distance': DISTANCE_COL, ...}
Z_OPTIONS = ['Total Distance (km)', 'Total Duration (min)']


def build_heatmap(year, x_col, y_col, z_col, hmap_id, cscale='agsunset_r'):
    """ x-axis = Day of Week, y-axis = Calendar Week
        or for heatmap 2:
        x-axis = Month, y-axis = Day
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
    id="heatmap-year"
)

hmap_select_type = dcc.RadioItems(
    options=[
        {"label": i, "value": i} for i in ['By Month', 'By Week']
    ],
    value='By Month',
    id="heatmap-type",
    labelStyle={'display': 'inline-block',
                'marginTop': '5px'},
)

hmap_select_z = dcc.Dropdown(
    options=[
        {"label": i, "value": i} for i in Z_OPTIONS
    ],
    value=Z_OPTIONS[0],
    id="heatmap-zaxis",
)
