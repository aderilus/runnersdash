""" Callbacks for month view
"""

import math
from dash.dependencies import Input, Output
from dashboard.index import app
from utils import (COLMAPPER,
                   format_pace, get_unit_from_string)
from dashboard.layout.monthstats import build_monthly_timeseries, get_monthly_stats


@app.callback(
    [Output("month-stat-distance", "children"),
     Output("month-stat-duration", "children"),
     Output("month-stat-pace", "children"),
     Output("month-stat-rhr", "children")
     ],
    [Input("home-year-picker", "value"),
     Input("home-month-picker", "value")]
)
def update_monthly_stats(in_year, in_month):

    total_distance = get_monthly_stats(COLMAPPER['distance'],
                                       in_month, in_year)
    total_duration = get_monthly_stats(COLMAPPER['duration'],
                                       in_month, in_year)
    avg_pace = get_monthly_stats(COLMAPPER['avg pace'],
                                 in_month, in_year)
    avg_rhr = get_monthly_stats(COLMAPPER['avg rhr'],
                                in_month, in_year)

    if not math.isnan(avg_pace):
        pace_min, pace_sec = format_pace(avg_pace)
        msg_pace = '{:0>2d}\' {:0>2.0f}\"'.format(pace_min, pace_sec)
    else:
        msg_pace = "0\' 00\""

    msg_distance = '{:.2f} {unit}'.format(total_distance,
                                          unit=get_unit_from_string(COLMAPPER['distance']))
    msg_duration = '{:.2f} {unit}'.format(total_duration,
                                          unit=get_unit_from_string(COLMAPPER['duration']))
    msg_rhr = '{:.0f} {unit}'.format(avg_rhr, unit=get_unit_from_string(COLMAPPER['avg rhr']))

    return msg_distance, msg_duration, msg_pace, msg_rhr


@app.callback(
    Output("month-time-series", "figure"),
    [Input("home-month-picker", "value"),
     Input("home-year-picker", "value"),
     Input("time-series-y1", "value"),
     Input("time-series-y2", "value")
     ]
)
def update_month_timeseries(in_month, in_year, y1, y2=None):
    fig = build_monthly_timeseries(in_month, in_year, y1, y2)

    if y2 is not None:
        fig.update_yaxes(
            secondary_y=True,
            title_text=y2,
        )

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )

    return fig
