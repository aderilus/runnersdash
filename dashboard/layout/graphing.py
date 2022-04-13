""" Encapsulates some common routines in building grpahs.
"""
import plotly.graph_objects as go
from dashboard.assets.custom_themes import custom_theme1


def simple_time_series(plotly_fig, xcol, ycol, xlabel, ylabel,
                       plot_type='Bar', row_idx=None, col_idx=None,
                       width_px=None, height_px=None, marker_dict=None,
                       lineshape='linear', bar_text_template='%{y.:3s}'):
    """
    Args:
        xcol (pd.Series)
        ycol (pd.Series)
        xlabel (str)
        ylabel (str)

    Kwargs:
        plot_type (str): Takes in 'Bar' or 'Scatter' (not case-sensitive).
        row_idx (int): Defines row position of plot within a subplot.
        col_idx (int): Defines column position of plot within a subplot.
        width_px (int): Width of the plot in px. Default is None (auto).
        height_px (int): Height of the plot in px. Default is None.
        marker_dict (dict): Dictionary of parameters to pass into the
                            'marker' parameter of graph_objects.Bar
                            constructor. Default is None.
        lineshape (str): Passed into 'line_shape' parameter for
                         graph_objects.Scatter constructor. Default is
                         'linear'.
        bar_text_template (str): Passed into 'texttemplate' parameter for
                                 graph_objects.Bar constructor. Default
                                 is '{y:.3f}'.

    Returns:
        plotly.graph_objects figure of plot_type Bar or Scatter.
    """
    fig = plotly_fig

    if plot_type.lower() == 'bar':
        graph_obj = go.Bar(
            x=xcol,
            y=ycol,
            name=ylabel,
            texttemplate=bar_text_template,
            marker=marker_dict,
        )

    elif plot_type.lower() == 'scatter':
        graph_obj = go.Scatter(
            x=xcol,
            y=ycol,
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
        template=custom_theme1,
        xaxis=dict(
            title=xlabel,
        ),
        yaxis=dict(
            title=ylabel,
        )
    )

    if width_px:
        fig.update_layout(width=width_px)
    if height_px:
        fig.update_layout(height=height_px)

    return fig
