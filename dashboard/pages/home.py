""" Home page component configurations.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from dashboard.layout.header import navbar, min_year, max_year
from dashboard.layout.timeseriesplots import (highresweeklyplots,
                                              graph_options_container
                                              )
from dashboard.layout.statscard import (week_stats_container,
                                        month_stats_container,)
from dashboard.layout.timeseriessubplots import week_ts_subplot
from dashboard.layout.runninghabits import (rh_dow, rh_tod,
                                            rh_title,
                                            rh_run_distance)
from dashboard.layout.environmentalfactors import (weather_factors_y,
                                                   weather_factors_plot)


# --- CONSTANTS --- #
YEAR_RANGE = list(range(min_year, max_year + 1))
row2_leftcol_size = 8
row2_rightcol_size = 4

# --- TIME-SERIES PLOTS: SELECT YEAR --- #
year_slider = dcc.Slider(
    min=min_year,
    max=max_year,
    step=1,
    value=max_year,
    marks={i: str(i) for i in YEAR_RANGE},
    id="year-slider",
)

# max_year + 1 is the associated value for "All"
vslider_marks = [str(i) for i in YEAR_RANGE]
vslider_marks.append("All")
year_slider_vert = dcc.Slider(
    min=min_year,
    max=max_year + 1,
    step=1,
    value=max_year,
    marks=dict(zip([i for i in range(min_year, max_year + 2)], vslider_marks)),
    id="year-slider-vertical",
    vertical=True,
)


# --- PLOT CONTAINERS/CARDS --- #
main_timeseries_card = dbc.Card(
    children=[
        dbc.CardHeader(
            [html.Div(year_slider,
                      style={'padding': '10px 20px 1px 20px'},
                      ),
             ],
            className="sticky-top",
            style={'background-color': 'rgba(247, 247, 247, 0.8)'},
        ),
        dbc.CardBody(
            [
                html.H5([""],
                        style={"display": "inline-block",
                               "padding-left": "0.75rem", "padding-top": "0.05rem"},
                        id="main-timeseries-title"
                        ),
                html.Div(highresweeklyplots, style={"margin-top": "0.30rem"}),
            ],
            style={"padding-left": "5px", "padding-right": "0px"},
        ),
        dbc.CardFooter(
            [
                html.Div(
                    [
                        html.P([""], id="weekly-download-msg",
                               style={'font-size': '0.80rem', 'flex-grow': '2',
                                      'order': '1', 'padding-top': '0.9rem',
                                      'padding-left': '0.8rem'}),
                        dbc.Button("png", id="png-download-weekly", outline=True,
                                   class_name="downloadbutton",
                                   style={'order': '3'}
                                   ),
                        dbc.Button("svg", id="svg-download-weekly", outline=True,
                                   class_name="downloadbutton",
                                   style={'order': '2'}
                                   ),
                    ],
                    style={'display': 'inline-flex'}
                ),
            ],
            style={'padding': '0'},
            className="download-button-container",
        )
    ],
)

week_subplot_container = html.Div(
    [week_ts_subplot],
    style={"padding": "0.25rem", "padding-top": "1rem"}
)

month_subplot_container = html.Div(
    [],
    style={"padding": "0.25rem", "padding-top": "0.75rem"}
)


rh_dow_card = dbc.Card(
    children=[
        dbc.CardBody(
            [
                rh_dow,
            ],
        ),
    ]
)

rh_tod_card = dbc.Card(
    children=[
        dbc.CardBody(
            [
                rh_tod,
            ],
        ),
    ]
)

rh_dist_card = dbc.Card(
    children=[
        dbc.CardBody(
            [rh_run_distance]
        ),
    ]
)


# --- COLUMNS --- #
# Row 1, left col
module_a = dbc.Col(
    children=[
        main_timeseries_card,
    ],
    width={"size": row2_leftcol_size, "order": "first"},
)

# Row 1, right col
module_b = dbc.Col(
    children=[
        graph_options_container,
        week_stats_container,
        week_subplot_container,
        month_stats_container,
    ],
    width={"size": row2_rightcol_size, "order": "last"},
)

# Row 2, left col
row2_left = dbc.Col(
    children=[
        html.Div(
            [year_slider_vert],
            style={"padding": "0.25rem",
                   "position": 'sticky',
                   },
            className="sticky-top",
        )
    ],
    width={"size": 1},
)

# Row 2, middle col
module_d = dbc.Col(
    children=[
        rh_dow_card,
    ],
    width={"size": 5},
)

# Row 2, right col, top
module_e = dbc.Col(
    children=[
        rh_tod_card
    ],
    width={"size": 7}
)

# Row 2, right col, bottom
module_f = dbc.Col(
    children=[
        rh_dist_card
    ],
)

row2_right = dbc.Col(
    children=[
        dbc.Row(
            children=[
                module_d,
                module_e
            ],
            style={"margin-bottom": '1.5rem'},
        ),
        dbc.Row(
            children=[
                module_f
            ]
        ),
    ],
    width={"size": 11}
)

row3_col = dbc.Col(
    children=[
        dbc.Card(
            children=[
                dbc.CardBody(
                    children=[
                        weather_factors_y,
                        weather_factors_plot,
                    ],
                )
            ],
        )
    ],
    width={"size": 8, "offset": 2},
)

# --- ROWS --- #

# Row 1 = Time series plots
row1 = dbc.Row(
    children=[
        module_a,
        module_b,
    ],
    class_name="g-6",
)

# Row 2 = Running habits
row2 = dbc.Row(
    children=[
        rh_title,
        row2_left,
        row2_right,
    ],
    class_name="gy-6",
)

# Row 3 = Environmental Factors
row3 = dbc.Row(
    children=[
        html.H5("Environmental Factors (outdoor runs)"),
        row3_col
    ],
    class_name="gy-6",
    style={"padding-top": "1.5rem"}
)


# --- LAYOUT --- #
layout = html.Div(
    children=[
        navbar,
        dbc.Container(
            children=[
                row1,
                html.Br(),
                row2,
                html.Br(),
                row3,
                html.Br(),
            ],
        ),
    ],
)
