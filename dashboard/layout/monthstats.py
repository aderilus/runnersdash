import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import html, dcc
from math import floor, ceil
from plotly.subplots import make_subplots
from utils import (get_latest_monthly_agg,
                   get_latest_weekly_agg,
                   get_weeks_of_month,
                   get_column_extremas,
                   MONTHS_MAP)

AXES_OFFSET = 0.4

# --- MONTH STATS --- #
month_stat1 = html.Div(
    [
        dbc.Alert(
            [
                html.P("Total Distance"),
                html.H5("[#] [unit]",
                        id="month-stat-distance"),
            ],
            color="primary",
        ),
    ]
)

month_stat2 = html.Div(
    [
        dbc.Alert(
            [
                html.P("Total Duration"),
                html.H5("[#] min",
                        id="month-stat-duration"),
            ],
            color="warning",
        )
    ]
)

month_stat3 = html.Div(
    [
        dbc.Alert(
            [
                html.P("Avg. Pace"),
                html.H5("00'00\"",
                        id="month-stat-pace"),
            ],
            color="secondary",
        )
    ]
)

month_stat4 = html.Div(
    [
        dbc.Alert(
            [
                html.P("Avg. Resting Heart Rate"),
                html.H5("", id="month-stat-rhr"),
            ],
            color="danger",
        ),
    ]
)

month_stat_container = dbc.Row(
    [
        dbc.Col([month_stat1]),
        dbc.Col([month_stat2]),
        dbc.Col([month_stat3]),
        dbc.Col([month_stat4])
    ],
    style={"display": "flex",
           "justify-content": "center",
           "padding": "1.5rem",
           },
)

# --- GRAPHS --- #
month_time_series = dcc.Graph(id="month-time-series")


# --- FUNCTIONS --- #
def get_monthly_stats(metric, input_month, input_year):
    """
    Args:
        metric (str): Name of the column of metric.
        input_month (int): The month formatted as an integer.
                           (E.g: 3 = March)
        input_year (int): The given year.
    """
    data = get_latest_monthly_agg()
    dfiltered = data[(data['Year'] == input_year) & (data['Month'] == input_month)]

    return dfiltered[metric].iloc[0]


# --- GRAPH FUNCTIONS --- #
def build_monthly_timeseries(input_month, input_year, y1col, y2col=None):
    """
    Args:
        input_month (int): Month formatted as an int.
        input_year (int): Year as an int.
        y1col (str): Column name containing y1-values.
        y2col (str): Column name containing y2-values.

    Returns:
        plotly.graph_objects figure.
    """

    data = get_latest_weekly_agg()  #
    week_start = get_weeks_of_month(input_month, input_year)
    dfiltered = data[data['Week'].isin(week_start)]

    x_labels = ["{0} {1}".format(MONTHS_MAP[w.month][:3], w.day) for w in dfiltered['Week']]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # -- Y1 (Bar) -- #
    # For legend label, remove units. The axis label will have it.
    y1_label = y1col.split('(')[0]
    fig.add_trace(
        go.Bar(x=dfiltered['Week'], y=dfiltered[y1col],
               name=y1_label),
        secondary_y=False,
    )

    # Update plot margins and x-axis
    fig.update_layout(
        xaxis=dict(
            title='{0} {1}'.format(MONTHS_MAP[input_month], input_year),
            tickmode='array',
            tickvals=dfiltered['Week'],
            ticktext=x_labels,
        ),
        margin=dict(l=20, r=10, t=35, b=10),
    )

    # Implement absolute y-scale, get min y, max y in weekly
    # aggregates within the same year
    df_current_year = data[data['Week'].dt.year == input_year]
    y1_min, y1_max = get_column_extremas(df_current_year, y1col)

    fig.update_yaxes(
        secondary_y=False,
        range=[floor(y1_min), ceil(y1_max)],
        title_text=y1col,
    )

    # --- Y2 (Scatter) --- #
    if y2col is not None:
        data_within_year = data[data['Week'].dt.year == input_year]

        try:
            y2_min, y2_max = get_column_extremas(data_within_year, y2col)

            y2_label = y2col.split('(')[0]
            fig.add_trace(
                go.Scatter(x=dfiltered['Week'], y=dfiltered[y2col],
                           name=y2_label, mode='lines+markers',
                           connectgaps=True),
                secondary_y=True,
            )

            fig.update_yaxes(
                secondary_y=True,
                range=[floor(y2_min - AXES_OFFSET), ceil(y2_max + AXES_OFFSET)],
            )
        except IndexError as e:
            print("build_monthly_timeseries(): ", e)

    return fig
