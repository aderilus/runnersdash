from dash.dependencies import Input, Output, State
from plotly.io import write_image
from dashboard.index import app
from pathlib import Path
from dashboard.layout.timeseriesgraphs import (build_weekly_binned_across_year,
                                               build_monthly_binned_across_year
                                               )


@app.callback(
    Output("main-timeseries-title", "children"),
    [Input("year-slider", "value"),
     Input("time-bin-toggle", "value")]
)
def update_main_time_series_title(in_year, monthly_toggled):
    if monthly_toggled:
        return f"Monthly running data across {in_year}"
    return f"Weekly running data across {in_year}"


# @app.callback(
#     Output("toggle-daily-overlay", "is_open"),
#     [Input("time-bin-toggle", "value")],
#     [State("toggle-daily-overlay", "is_open")]
# )
# def toggle_daily_overlay(monthly_toggled, is_open):
#     if not monthly_toggled:
#         return False
#     return not is_open


@app.callback(
    Output("weekly-time-series", "figure"),
    [Input("year-slider", "value"),
     Input("time-series-y1", "value"),
     Input("time-series-y2", "value"),
     Input("time-series-y3", "value"),
     Input("time-bin-toggle", "value"),
     Input("daily-data-overlay", "value"),
     ],
)
def update_weekly_time_series(in_year, y1, y2, y3, monthly_toggled,
                              daily_overlay):
    if monthly_toggled:
        fig = build_monthly_binned_across_year(in_year, y1, y2, y3, daily_overlay)
    else:
        fig = build_weekly_binned_across_year(in_year, y1, y2, y3, daily_overlay)
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
