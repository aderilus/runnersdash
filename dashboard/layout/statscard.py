""" Objects and function definitions for stat summaries across
various time periods (week, month, year).

The template for stats summaries.
    | Tot. Distance | Tot. Duration | Avg. Pace |  (CardBody)
    ---------------------------------------------
    | Avg. Distance |    Avg. VO2   | Avg. RHR  |  (CardFooter)
"""

import dash_bootstrap_components as dbc
from dash import html
from collections import OrderedDict
from utils import (get_latest_weekly_agg,
                   get_latest_monthly_agg,
                   format_pace,
                   colmapper)

weekly_data = get_latest_weekly_agg()
monthly_data = get_latest_monthly_agg()


def get_stat_over(time_period, metric, on_date):
    """
    Args:
        time_period (str): Defines which dataset to read. Takes in:
                           ['week', 'month', 'year'].
        metric (str): Column name of the metric. If metric = None,
                      returns a Series of the selected date with
                      all the columns.
        on_date (datetime.datetime): Date associated with the data to read.

    Returns:
        Object or float or string of the DataFrame column's contents.
        If metric = None, returns a Series.
    """
    if time_period == 'week':
        data = weekly_data
        dfiltered = data[data.index == on_date]
    elif time_period in ['year', 'month']:
        data = monthly_data
        dfiltered = data[data.index.year == on_date.year]

        if time_period == 'month':
            dfiltered = dfiltered[dfiltered.index.month == on_date.month]
    else:
        raise ValueError("'time_period' parameter only takes in ['week', 'month', 'year']")

    try:
        if metric:
            return dfiltered[metric].iloc[0]
        return dfiltered.iloc[0]
    except IndexError:  # If dfiltered is empty
        return "No data"


def get_list_of_stats(time_period_type, selected_time):
    """
    """
    time_period_type = time_period_type.lower()

    data_on_date = get_stat_over(time_period_type, metric=None,
                                 on_date=selected_time)
    column_list = data_on_date.index.tolist()
    stats = OrderedDict()
    # This is the same order as the Output list
    data_to_get = [('Total Distance', 'sum'),
                   ('Total Duration', 'sum'),
                   ('Avg Pace', 'mean'),
                   ('Total Distance', 'mean'),
                   ('Avg VO2', 'mean'),
                   ('Avg Resting Heart Rate', 'mean'),
                   ]

    for i, j in data_to_get:
        try:
            key = i + '_' + j
            col_name_level0 = colmapper(i, column_list)
            stat = data_on_date[col_name_level0][j]

            if i == "Avg Pace":
                if stat:
                    pacemin, pacesec = format_pace(stat)
                else:
                    pacemin, pacesec = (None, None)
                stat_msg = '{:0>2d}\'{:0>2.0f}\"'.format(pacemin, pacesec)
            elif i == "Avg Resting Heart Rate":
                stat_msg = '{:.0f}'.format(stat)
            else:
                stat_msg = '{:.2f}'.format(stat)
            stats[key] = stat_msg
        except TypeError:  # If type(data_on_date) is NoneType
            stats[key] = "No data"

    return list(stats.values())


# --- dbc.CardGroup components ---#
week_stats_title = html.H6(["Select week on the plot"],
                           id="week-stats-title",
                           style={"padding-bottom": "0.25rem"})

weekly_cols = weekly_data.columns.tolist()
week_stats_cardgroup = dbc.CardGroup(
    [
        dbc.Card(
            [
                dbc.CardBody([
                    html.P(colmapper('Total Distance', weekly_cols)),
                    html.H4(children=[], id="week-stat-distance")
                ],
                ),
                dbc.CardFooter([
                    html.P("Avg Distance"),
                    html.H4(children=[], id="week-stat-avgdistance")
                ],
                )
            ],
        ),

        dbc.Card(
            [
                dbc.CardBody([
                    html.P(colmapper('Total Duration', weekly_cols)),
                    html.H4(children=[], id="week-stat-duration")
                ],
                ),
                dbc.CardFooter([
                    html.P(colmapper('Avg VO2', weekly_cols)),
                    html.H4(children=[], id="week-stat-avgvo2")
                ],
                )
            ]
        ),

        dbc.Card(
            [
                dbc.CardBody([
                    html.P(colmapper('Avg Pace', weekly_cols)),
                    html.H4(children=[], id="week-stat-avgpace")
                ],
                ),
                dbc.CardFooter([
                    html.P(colmapper('Avg Resting Heart Rate', weekly_cols)),
                    html.H4(children=[], id="week-stat-avgrhr")
                ],
                )
            ]
        ),
    ], id="week-stats-cardgroup"
)

week_stats_container = html.Div(
    [
        week_stats_title,
        week_stats_cardgroup
    ],
    style={"padding-top": "1rem"}
)


month_stats_title = html.H6(["Select month on the plot"],
                            id="month-stats-title",
                            style={"padding-bottom": "0.25rem",
                                   "padding-top": "1rem"})

monthly_cols = monthly_data.columns.tolist()
month_stats_cardgroup = dbc.CardGroup(
    [
        dbc.Card(
            [
                dbc.CardBody([
                    html.P(colmapper('Total Distance', monthly_cols)),
                    html.H4(children=[], id="month-stat-distance")
                ],
                ),
                dbc.CardFooter([
                    html.P("Avg Distance"),
                    html.H4(children=[], id="month-stat-avgdistance")
                ],
                )
            ]
        ),

        dbc.Card(
            [
                dbc.CardBody([
                    html.P(colmapper('Total Duration', monthly_cols)),
                    html.H4(children=[], id="month-stat-duration")
                ],
                ),
                dbc.CardFooter([
                    html.P(colmapper('Avg VO2', monthly_cols)),
                    html.H4(children=[], id="month-stat-avgvo2")
                ],
                )
            ]
        ),

        dbc.Card(
            [
                dbc.CardBody([
                    html.P(colmapper('Avg Pace', monthly_cols)),
                    html.H4(children=[], id="month-stat-avgpace")
                ],
                ),
                dbc.CardFooter([
                    html.P(colmapper('Avg Resting Heart Rate', monthly_cols)),
                    html.H4(children=[], id="month-stat-avgrhr")
                ],
                )
            ]
        ),
    ]
)

month_stats_container = html.Div(
    [
        month_stats_title,
        month_stats_cardgroup
    ],
    style={"padding-top": "0.50rem"}
)

year_stats_cardgroup = dbc.CardGroup([], id="year-stats-cardgroup")
