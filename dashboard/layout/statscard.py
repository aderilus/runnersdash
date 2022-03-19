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
from datetime import datetime
from utils import (get_latest_weekly_agg,
                   get_latest_monthly_agg,
                   format_pace,
                   COLMAPPER)


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
        data = get_latest_weekly_agg()
        dfiltered = data[data[time_period.capitalize()] == on_date]
    elif time_period in ['year', 'month']:
        data = get_latest_monthly_agg()
        dfiltered = data[data['Year'] == on_date.year]

        if time_period == 'month':
            dfiltered = dfiltered[dfiltered['Month'] == on_date.month]
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
    stats = OrderedDict()
    # This is the same order as the Output list
    data_to_get = ['distance', 'duration', 'avg pace',
                   'avg distance', 'avg vo2', 'avg rhr']

    for d in data_to_get:
        try:
            stat = data_on_date[COLMAPPER[d]]

            if d == "avg pace":
                if stat:
                    pacemin, pacesec = format_pace(stat)
                else:
                    pacemin, pacesec = (None, None)
                stat_msg = '{:0>2d}\'{:0>2.0f}\"'.format(pacemin, pacesec)
            else:
                stat_msg = '{:.2f}'.format(stat)

            stats[d] = stat_msg
        except TypeError:  # If type(data_on_date) is NoneType
            stats[d] = "No data"

    return list(stats.values())


# --- dbc.CardGroup components ---#
week_stats_title = html.H6(["Select week on the plot"],
                           id="week-stats-title",
                           style={"padding-bottom": "0.25rem"})

week_stats_cardgroup = dbc.CardGroup(
    [
        dbc.Card(
            [
                dbc.CardBody([
                    html.P(COLMAPPER['distance']),
                    html.H4(children=[], id="week-stat-distance")
                ],
                ),
                dbc.CardFooter([
                    html.P(COLMAPPER['avg distance']),
                    html.H4(children=[], id="week-stat-avgdistance")
                ],
                )
            ],
        ),

        dbc.Card(
            [
                dbc.CardBody([
                    html.P(COLMAPPER['duration']),
                    html.H4(children=[], id="week-stat-duration")
                ],
                ),
                dbc.CardFooter([
                    html.P(COLMAPPER['avg vo2']),
                    html.H4(children=[], id="week-stat-avgvo2")
                ],
                )
            ]
        ),

        dbc.Card(
            [
                dbc.CardBody([
                    html.P(COLMAPPER['avg pace']),
                    html.H4(children=[], id="week-stat-avgpace")
                ],
                ),
                dbc.CardFooter([
                    html.P(COLMAPPER['avg rhr']),
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
    style={"padding-top": "0.25rem"}
)


month_stats_title = html.H6(["Select month on the plot"],
                            id="month-stats-title",
                            style={"padding-bottom": "0.25rem",
                                   "padding-top": "0.75rem"})

month_stats_cardgroup = dbc.CardGroup(
    [
        dbc.Card(
            [
                dbc.CardBody([
                    html.P(COLMAPPER['distance']),
                    html.H4(children=[], id="month-stat-distance")
                ],
                ),
                dbc.CardFooter([
                    html.P(COLMAPPER['avg distance']),
                    html.H4(children=[], id="month-stat-avgdistance")
                ],
                )
            ]
        ),

        dbc.Card(
            [
                dbc.CardBody([
                    html.P(COLMAPPER['duration']),
                    html.H4(children=[], id="month-stat-duration")
                ],
                ),
                dbc.CardFooter([
                    html.P(COLMAPPER['avg vo2']),
                    html.H4(children=[], id="month-stat-avgvo2")
                ],
                )
            ]
        ),

        dbc.Card(
            [
                dbc.CardBody([
                    html.P(COLMAPPER['avg pace']),
                    html.H4(children=[], id="month-stat-avgpace")
                ],
                ),
                dbc.CardFooter([
                    html.P(COLMAPPER['avg rhr']),
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
