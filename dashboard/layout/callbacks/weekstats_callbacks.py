""" Callbacks for week view section under /home
"""

from datetime import datetime, date, timedelta
from calendar import monthcalendar, monthrange
from dash.dependencies import Input, Output
from dashboard.index import app
from dashboard.layout.weekstats import build_weekly_timeseries, get_weekly_stat
from dashboard.layout.header import max_year
from utils import (MONTHS_MAP, COLMAPPER,
                   get_unit_from_string,
                   format_pace, get_weeks_of_month,
                   get_latest_weekly_agg)


# @app.callback(
#     Output("home-week-picker", "options"),
#     [Input("home-month-picker", "value"),
#      Input("home-year-picker", "value")],
# )
# def update_week_picker(input_month, input_year):  # NOT USING ANYMORE?
#     week_start_dates = get_weeks_of_month(input_month, input_year)

#     return [{"label": i.strftime("%Y-%m-%d"), "value": i} for i in week_start_dates]


@app.callback(
    [Output("week-info", "children")],
    [Input("month-time-series", "clickData")]
)
def update_week_info(click_data):

    if click_data is None:
        return ["Week of"]

    selected_date = click_data['points'][0]['x']
    date_split = selected_date.split('-')
    yr = date_split[0]
    mon = MONTHS_MAP[int(date_split[1])]
    day = date_split[2]

    return ["Week of {0} {1}, {2}".format(mon, day, yr)]


@app.callback(
    [Output("week-stat-distance", "children"),
     Output("week-stat-duration", "children"),
     Output("week-stat-pace", "children")],
    # [Input("home-week-picker", "value")]
    [Input("month-time-series", "clickData")]
)
def update_weekly_stats(click_data):

    if click_data is None:
        return ("", "", "")
    else:
        clicked_data_dump = click_data['points'][0]
        selected_week = clicked_data_dump['x']

    try:
        week_as_datetime = datetime.strptime(selected_week, '%Y-%m-%d')
    except ValueError:
        week_as_datetime = datetime.strptime(selected_week, '%Y-%m-%dT%H:%M:%S')

    total_distance = get_weekly_stat(COLMAPPER['distance'], week_as_datetime)
    total_duration = get_weekly_stat(COLMAPPER['duration'], week_as_datetime)
    avg_pace = get_weekly_stat(COLMAPPER['avg_pace'], week_as_datetime)

    pacemin, pacesec = format_pace(avg_pace)

    msg_distance = '{:.2f} {unit}'.format(total_distance,
                                          unit=get_unit_from_string(COLMAPPER['distance']))
    msg_duration = '{:.2f} {unit}'.format(total_duration,
                                          unit=get_unit_from_string(COLMAPPER['duration']))
    msg_pace = '{:0>2d}\' {:0>2.0f}\"'.format(pacemin, pacesec)

    return msg_distance, msg_duration, msg_pace


@app.callback(
    Output("week-time-series", "figure"),
    # [Input("home-week-picker", "value")]
    [Input("month-time-series", "clickData"),
     Input("time-series-y1", "value"),
     Input("time-series-y2", "value")],
)
# def update_week_timeseries(picked_date, y1=None, y2=None):
def update_week_timeseries(click_data, y1, y2=None):

    try:
        click_data_dump = click_data['points'][0]
        picked_date = click_data_dump['x']
    except TypeError:  # click_data returns NoneType if user hasn't interacted yet
        wkly_data = get_latest_weekly_agg()
        picked_date = (wkly_data.iloc[-1])['Week'].strftime('%Y-%m-%d')

    try:
        date_as_datetime = datetime.strptime(picked_date, "%Y-%m-%d")
    except ValueError:
        date_as_datetime = datetime.strptime(picked_date, "%Y-%m-%dT%H:%M:%S")

    fig = build_weekly_timeseries(date_as_datetime, y1col=y1, y2col=y2)

    # update y-axis label and ticks
    fig.update_yaxes(
        title_text=y1,
        secondary_y=False,
    )

    if y2 is not None:
        fig.update_yaxes(
            title_text="Avg." + y2,
            secondary_y=True,
        )

    # update legend
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
    )

    return fig
