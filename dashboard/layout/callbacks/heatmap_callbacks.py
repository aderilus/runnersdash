""" Callbacks for heatmaps.
"""
from dashboard.index import app
from dashboard.layout.activityheatmap import build_heatmap
from dash.dependencies import Input, Output
from preparedatasets import DAYS_OF_WK


MONTH_LIST = ['Jan', 'Feb', 'Mar', 'Apr',
              'May', 'Jun', 'Jul', 'Aug',
              'Sep', 'Oct', 'Nov', 'Dec']


@app.callback(
    Output("activity-heatmap", "figure"),
    Input("heatmap-year", "value"),
    Input("heatmap-type", "value"),
    Input("heatmap-zaxis", "value")
)
def update_heatmap(input_year, heatmap_type, z):

    if heatmap_type == 'By Month':
        x = 'Month'
        y = 'Day'
        mapid = 'monthly-heatmap'

        # Layout parameters
        w = 400
        h = 700

    else:
        x = 'Calendar Week'
        y = 'Day of Week'
        mapid = 'weekly-heatmap'

        w = 700
        h = 400

    fig = build_heatmap(input_year, x, y, z, mapid)
    fig.update_layout(
        width=w,
        height=h,
    )

    # Format axes tick labels
    if heatmap_type == 'By Month':
        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(1, 13)),
                ticktext=MONTH_LIST,
            )
        )
    else:
        fig.update_layout(
            yaxis={
                'categoryarray': DAYS_OF_WK
            }
        )

    return fig
