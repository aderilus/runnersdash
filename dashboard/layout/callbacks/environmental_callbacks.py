from dash.dependencies import Input, Output
from dashboard.index import app
from dashboard.layout.environmentalfactors import (build_weather_factors_plot,
                                                   )


@app.callback(
    Output("weather-factors-plot", "figure"),
    Input("weather-factors-y", "value")
)
def update_weather_factors(y_col):
    return build_weather_factors_plot(y_col)
