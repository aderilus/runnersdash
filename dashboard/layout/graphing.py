""" Encapsulates some common routines in building grpahs.
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dashboard.assets.custom_themes import timeseriesplate


def simple_time_series(plotly_fig, dataframe, xcol, ycol, xlabel, ylabel,
                       plot_type='Bar', row_idx=None, col_idx=None,
                       width_px=None, height_px=None, marker_dict=None,
                       lineshape='linear', truncate_bar_text=False):
    """
    Args:
        dataframe (pd.DataFrame)
        xcol (str)
        ycol (str)

    Returns:
        plotly.graph_objects figure.
    """
    textplate = '%{y:.3f}'
    if truncate_bar_text:
        textplate = '%{y:.2s}'

    fig = plotly_fig

    if plot_type in ['bar', 'Bar']:
        graph_obj = go.Bar(
            x=dataframe[xcol],
            y=dataframe[ycol],
            name=ylabel,
            texttemplate=textplate,
            marker=marker_dict,
        )

    elif plot_type in ['scatter', 'Scatter']:
        graph_obj = go.Scatter(
            x=dataframe[xcol],
            y=dataframe[ycol],
            name=ylabel,
            line_shape=lineshape,
            mode='lines+markers',
            cliponaxis=True,
        )

    fig.add_trace(
        graph_obj,
        row=row_idx,
        col=col_idx
    )

    fig.update_layout(
        template=timeseriesplate,
        xaxis=dict(
            title=xlabel,
        ),
        yaxis=dict(
            title=ycol,
        )
    )

    if width_px:
        fig.update_layout(width=width_px)
    if height_px:
        fig.update_layout(height=height_px)

    return fig
