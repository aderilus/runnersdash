""" Callback(s) for heatmap(s).
"""

from dashboard.index import app
from dashboard.layout.activityheatmap import build_heatmap
from dash.dependencies import Input, Output
from utils import ABBREV_MONTHS


@app.callback(
    Output("monthbyday-heatmap", "figure"),
    [Input("heatmap-year", "value"),
     Input("heatmap-zaxis", "value")]
)
def update_monthbyday_heatmap(input_year, z):

    x = 'Month'
    y = 'Day'
    mapid = 'monthly-heatmap'

    fig = build_heatmap(input_year, x_col='Month', y_col='Day',
                        z_col=z, hmap_id=mapid)
    fig.update_layout(
        width=350,
        height=650,
        margin=dict(l=5, r=5, b=5, t=20),
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=ABBREV_MONTHS,
        ),
    )

    return fig
