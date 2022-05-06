"""
"""
from dash.dependencies import Input, Output
from dashboard.index import app
from dashboard.layout.runninghabits import (build_dow_histogram,
                                            build_tod_histogram,
                                            build_runmetric_histogram,
                                            )


@app.callback(
    [Output("running-habits-dow", "figure"),
     Output("running-habits-tod", "figure"),
     Output("running-habits-rundist", "figure"),
     Output("running-habits-title", "children")],
    [Input("year-slider-vertical", "value")]
)
def update_running_habits(input_year):

    if input_year == 2023:  # TODO CHANGE THIS
        yr = "all"
        container_title = "Your running habits across all years"
    else:
        yr = input_year
        container_title = f"Your running habits across {yr}"

    outputs = (build_dow_histogram(yr),
               build_tod_histogram(yr),
               build_runmetric_histogram(yr),
               container_title)

    return outputs
