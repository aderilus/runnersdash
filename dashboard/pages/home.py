""" Home page layout definitions.

TODO:
    - Store YEAR_RANGE and similar data such as min_year and
      max_year in browser session to pass data across files.
"""

import dash_bootstrap_components as dbc
from utils import COLMAPPER, MONTHS_MAP, get_latest_weekly_agg
from dash import html, dcc
from dashboard.layout.header import navbar, min_year, max_year
from dashboard.layout.weekstats import (week_stat_container,
                                        week_time_series)
from dashboard.layout.monthstats import (month_stat_container,
                                         month_time_series)
from dashboard.layout.yearstats import year_time_series

# --- LOAD DATA --- #
weeklyagg = get_latest_weekly_agg()
YEAR_RANGE = list(range(min_year, max_year + 1))
row12_leftcol_size = 7
row12_rightcol_size = "auto"

# --- INTERACTIVE ELEMENTS --- #
year_picker = dcc.Dropdown(
    options=[
        {"label": str(i), "value": i} for i in YEAR_RANGE
    ],
    value=YEAR_RANGE[-1],
    clearable=False,
    id="home-year-picker",
)

month_picker = dcc.Dropdown(
    options=[
        {"label": mstring, "value": mnum} for mnum, mstring in MONTHS_MAP.items()
    ],
    value=weeklyagg['Week'].iloc[-1].month,
    clearable=False,
    id="home-month-picker",
)

# week_picker = dcc.Dropdown(
#     value=weeklyagg['Week'].iloc[-1],
#     placeholder=weeklyagg['Week'].iloc[-1].strftime('%Y-%m-%d'),
#     clearable=False,
#     id="home-week-picker",
# )

y1_options = [COLMAPPER['distance'], COLMAPPER['duration']]
y1_picker = dcc.Dropdown(
    options=[
        {"label": i.split('(')[0], "value": i} for i in y1_options
    ],
    value=y1_options[0],
    placeholder=y1_options[0].split('(')[0],
    clearable=False,
    id='time-series-y1',
)

y2_options = [COLMAPPER['avg rhr'], COLMAPPER['avg vo2'], COLMAPPER['weight']]
y2_picker = dcc.Dropdown(
    options=[
        {"label": i.split('(')[0], "value": i} for i in y2_options
    ],
    value=y2_options[0],
    placeholder="y2",
    id='time-series-y2',
)

# --- CARDS --- #
week_card = dbc.Card(
    children=[
        dbc.CardHeader(
            [
                html.Div(html.H6(["Week view"], id="week-info"),),
            ]
        ),
        dbc.CardBody(
            [
                week_stat_container,
                week_time_series
            ],
        ),
    ],
)

month_card = dbc.Card(
    children=[
        dbc.CardHeader([month_stat_container]),
        dbc.CardBody(
            [
                month_time_series
            ],
        ),
    ],
)

year_card = dbc.Card(
    children=[
        dbc.CardHeader(html.H6("Year view")),
        dbc.CardBody(
            [
                year_time_series
            ],
        ),
    ]
)


# --- COLUMNS --- #

# Row 2, right col
week_col = dbc.Col(
    children=[
        week_card,
    ],
    width={"size": row12_rightcol_size, "order": "last"},
)


# Row 2, left col
month_col = dbc.Col(
    children=[
        month_card
    ],
    width={"size": row12_leftcol_size, "order": "first"},
)

# Row 3, left col
year_col = dbc.Col(
    children=[

    ],
)


# --- ROWS --- #

row1 = dbc.Row(
    children=[
        dbc.Col(
            [
                html.Div(
                    [
                        html.P("Choose month", className="lead",
                               style={"padding-bottom": "0rem"})
                    ],
                    style={"width": "40%", "float": "left",
                           "display": "inline-block"},
                ),
                html.Div(
                    [year_picker],
                    style={"width": "20%", "float": "right",
                           "display": "inline-block"}
                ),
                html.Div(
                    [month_picker],
                    style={"width": "25%", "float": "right",
                           "padding-right": "1rem",
                           "display": "inline-block"}
                ),
            ],
            width={"size": row12_leftcol_size, "offset": 0},
            style={"padding-top": "0.5rem"}
        ),

        dbc.Col(
            [
                html.Div(
                    [y2_picker],
                    style={"display": "inline-block",
                           "float": "right", "padding-right": "1.75rem",
                           "width": "35%"}
                ),
                html.Div(
                    [y1_picker],
                    style={"display": "inline-block", "width": "35%",
                           "float": "right", "padding-right": "1rem"}
                ),
            ],
            width={"size": 12 - row12_leftcol_size},
            style={"padding-top": "0rem"}
        ),
    ],
    class_name="g-6 sticky-top",
    align="center",
    style={'background-color': '#fff',
           'opacity': '0.85'}
)

# Row 1 = 2-column Week and Month view
row2 = dbc.Row(
    children=[
        month_col,
        week_col,
    ],
    class_name="g-6",
)

# Row 2 = Year view, 1-column
row3 = dbc.Row(
    children=[
        dbc.Col([year_card], class_name="g-6")
    ],
    class_name="gy-6",
)

# Row 3 = Trends
row4 = dbc.Row(
    children=[
        dbc.Col([], class_name="g-6")
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
                row2,
                html.Br(),
                row3,
                html.Br(),
                row4
            ],
        ),
    ],
)
