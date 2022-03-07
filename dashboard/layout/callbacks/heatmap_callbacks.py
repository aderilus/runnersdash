""" Callbacks for heatmaps.
"""
from dashboard.index import app
from dashboard.layout.activityheatmap import build_heatmap
from dash.dependencies import Input, Output
from utils import DAYS_OF_WK, ABBREV_MONTHS


@app.callback(
    Output("monthbyday-heatmap", "figure"),
    Input("heatmap-year", "value"),
    Input("heatmap-zaxis", "value")
)
def update_monthbyday_heatmap(input_year, z):

    # if heatmap_type == 'By Month':
    x = 'Month'
    y = 'Day'
    mapid = 'monthly-heatmap'

    # figure layout parameters
    w = 400
    h = 700

    # else:
    #     x = 'Calendar Week'
    #     y = 'Day of Week'
    #     mapid = 'weekly-heatmap'

    #     w = 700
    #     h = 400

    fig = build_heatmap(input_year, x_col='Month', y_col='Day',
                        z_col=z, hmap_id=mapid)
    fig.update_layout(
        width=w,
        height=h,
    )

    # Format axes tick labels
    # if heatmap_type == 'By Month':
    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=ABBREV_MONTHS,
        )
    )
    # else:
    #     fig.update_layout(
    #         yaxis={
    #             'categoryarray': DAYS_OF_WK
    #         }
    #     )

    return fig
