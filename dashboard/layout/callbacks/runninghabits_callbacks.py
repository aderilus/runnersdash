"""
"""
from dash.dependencies import Input, Output
from dashboard.index import app
from dashboard.layout.runninghabits import build_habit_plots


@app.callback(
    [Output("running-habits-plots", "figure"),
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

    fig = build_habit_plots(yr)

    return fig, container_title
