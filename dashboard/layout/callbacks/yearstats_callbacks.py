from dash.dependencies import Input, Output
from dashboard.index import app
from dashboard.layout.yearstats import build_yearview_timeseries


@app.callback(
    Output("year-time-series", "figure"),
    [Input("home-year-picker", "value"),
     Input("time-series-y1", "value"),
     Input("time-series-y2", "value")]
)
def update_year_timeseries(in_year, y1, y2=None):
    fig = build_yearview_timeseries(in_year, y1, y2)

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
