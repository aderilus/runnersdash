""" Home page layout component definitions.
"""

from calendar import month
import dash_bootstrap_components as dbc
from dash import html, dcc
from utils import COLMAPPER
from dashboard.layout.header import navbar, min_year, max_year
from dashboard.layout.timeseriesgraphs import (highresweeklyplots,
                                               )
from dashboard.layout.statscard import (week_stats_container,
                                        month_stats_container,)
from dashboard.layout.timeseries_subplots import week_ts_subplot
from dashboard.layout.runninghabits import running_habit_plots


# --- CONSTANTS --- #
YEAR_RANGE = list(range(min_year, max_year + 1))
row2_leftcol_size = 8
row2_rightcol_size = 4

# --- SELECT TIME --- #
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


# --- Y INPUT --- #

# For monthly time-series
# prev_year_toggle = dbc.Switch(
#     id="compare-prev-year",
#     label="Compare against previous year",
#     value=False,
#     label_class_name="body",
# )

y1_options = [COLMAPPER['distance'], COLMAPPER['duration'], COLMAPPER['menstrual flow']]
y1_picker = dcc.Dropdown(
    options=[
        {"label": i.split('(')[0], "value": i} for i in y1_options
    ],
    value=y1_options[0],
    placeholder="Choose y-axis 1",
    clearable=False,
    id='time-series-y1',
)

combined_metrics = [COLMAPPER['avg pace'],
                    COLMAPPER['avg rhr'],
                    COLMAPPER['avg vo2'],
                    COLMAPPER['weight'],
                    ]

y2_options = combined_metrics
y2_picker = dcc.Dropdown(
    options=[
        {"label": i.split('(')[0], "value": i} for i in y2_options
    ],
    value=y2_options[0],
    placeholder="Choose y-axis 2",
    id='time-series-y2',
    clearable=False,
)

y3_options = combined_metrics[1:]
y3_picker = dcc.Dropdown(
    options=[
        {"label": i.split('(')[0], "value": i} for i in y3_options
    ],
    value=y3_options[0],
    placeholder="Choose y-axis 3",
    id='time-series-y3',
    clearable=False,
)

# --- GRAPH OPTIONS CONTAINER --- #
y_options_container = html.Div(
    [
        html.Div([y1_picker],
                 style={"display": "inline-block", "width": "36%",
                        "float": "left", "padding": "0.25rem"}
                 ),
        html.Div([y2_picker],
                 style={"display": "inline-block", "width": "26.5%",
                        "float": "center", "padding": "0.25rem"},
                 ),
        html.Div([y3_picker],
                 style={"display": "inline-block", "width": "37.5%",
                        "float": "right", "padding": "0.25rem"},
                 ),
    ],
)

time_bin_type = dbc.Switch(
    id="time-bin-toggle",
    label="Toggle month-to-month view",
    value=False,
    label_class_name="body",
)

daily_overlay_switch = dbc.Switch(
    id="daily-data-overlay",
    label="Overlay scatter plot of individual run data",
    value=False,
    label_class_name="body",
)

# monthly_graph_options = dbc.Collapse(
#     [
#         dbc.Card([
#             dbc.CardBody(
#                 [
#                     html.H6("Monthly view plot options",
#                             style={"font-size": "0.90rem"}),
#                 ],
#             )
#         ],)
#     ],
#     id="toggle-daily-overlay",
#     is_open=False,
# )

graph_options_container = html.Div(
    children=[
        html.H6("Time-series plot options"),
        y_options_container,
        html.Div([
            time_bin_type,
            daily_overlay_switch,
            # monthly_graph_options,
        ], style={"padding": "0.25rem"}),
    ],
    style={"padding": "0.25rem"}
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


habits_card = dbc.Card(
    children=[
        dbc.CardHeader(html.H6("",
                               id="running-habits-title")),
        dbc.CardBody(
            [
                running_habit_plots,
            ],
        ),
    ]
)

week_subplot_container = html.Div(
    [week_ts_subplot],
    style={"padding": "0.25rem", "padding-top": "1rem"}
)

month_subplot_container = html.Div(
    [],
    style={"padding": "0.25rem", "padding-top": "0.75rem"}
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
module_c = dbc.Col(
    children=[
        html.Div(
            [year_slider_vert],
            style={"padding": "0.25rem"},
        )
    ],
    width={"size": 1},
)

# Row 2, right col
module_d = dbc.Col(
    children=[
        habits_card,
    ],
    width={"size": 11},
)

# --- ROWS --- #

# Row 1
row1 = dbc.Row(
    children=[
        module_a,
        module_b,
    ],
    class_name="g-6",
)

# Row 2
row2 = dbc.Row(
    children=[
        module_c,
        module_d,
    ],
    class_name="gy-6",
)

# Row 3 = Trends
row3 = dbc.Row(
    children=[
    ],
    style={"background": "#eee"},
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
