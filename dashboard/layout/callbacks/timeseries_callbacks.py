""" Callback definitions associated with time-series plots (timeseriesplots.py
and timeseriessubplots.py).
"""
from dash.dependencies import Input, Output, State
from plotly.io import write_image
from dashboard.index import app
from pathlib import Path
from dashboard.layout.timeseriesplots import (build_agg_binned_across_year,
                                              )
from dashboard.layout.timeseriessubplots import build_week_ts_subplot


@app.callback(
    Output("main-timeseries-title", "children"),
    [Input("year-slider", "value"),
     Input("time-bin-toggle", "value")]
)
def update_main_time_series_title(in_year, monthly_toggled):
    if monthly_toggled:
        return f"Monthly running data across {in_year}"
    return f"Weekly running data across {in_year}"


@app.callback(
    Output("weekly-time-series", "figure"),
    [Input("year-slider", "value"),
     Input("time-series-y1", "value"),
     Input("time-series-y2", "value"),
     Input("time-series-y3", "value"),
     Input("time-bin-toggle", "value"),
     Input("daily-data-overlay", "value"),
     Input("time-series-line-shape", "value")
     ],
)
def update_weekly_time_series(in_year, y1, y2, y3, monthly_toggled,
                              daily_overlay, line_shape):
    y_splits = [y.split('_') for y in [y1, y2, y3]]
    y_cols = [(i, j) if j != ' ' else (i, None) for i, j in y_splits]

    bin_type = 'm' if monthly_toggled else 'w'
    fig = build_agg_binned_across_year(in_year, freq=bin_type,
                                       ycol=y_cols[0][0], ycol_sub=y_cols[0][1],
                                       y2col=y_cols[1][0], y2col_sub=y_cols[1][1],
                                       y3col=y_cols[2][0], y3col_sub=y_cols[2][1],
                                       line_type=line_shape,
                                       show_daily_scatter=daily_overlay
                                       )
    return fig


@app.callback(
    Output("weekly-download-msg", "children"),
    [Input("svg-download-weekly", "n_clicks"),
     Input("png-download-weekly", "n_clicks")],
    [State("weekly-time-series", "figure")],
    prevent_initial_call=True
)
def download_weekly_time_series(svg_nclick, png_nclick, fig):
    write_to_img = False
    msg = ""
    file_path = ""
    nclick = 0

    if png_nclick is not None:
        file_format = 'png'
        write_to_img = True
        nclick += png_nclick
    elif svg_nclick > 0:
        file_format = 'svg'
        write_to_img = True
        nclick += svg_nclick

    if write_to_img:
        file_name = f'weekly_timeseries_{nclick}.{file_format}'
        file_path = Path(Path.cwd(), 'screenshots', file_name)
        write_image(fig, file_path, file_format, width=600, height=700)
        msg = f"Saved as file {file_name} in /screenshots/"

    return msg


# --- MAIN TIME SERIES SUBPLOTS --- #
# Find associated functions and objects at timeseriessubplots.py

@app.callback(
    Output("week-ts-subplot", "figure"),
    [Input("weekly-time-series", "clickData")],
    prevent_initial_callback=True
)
def update_week_ts_subplot(click_data):

    if click_data is None:
        selected_date = 'most recent'
    else:
        clicked_data_dump = click_data['points'][0]
        # type(click_data_dump) is str
        selected_date = clicked_data_dump['x']

    fig = build_week_ts_subplot(selected_date, ycol_pattern='Total Distance')

    return fig
