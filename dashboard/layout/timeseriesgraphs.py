"""

"""
import dashboard.layout.graphing as gr
import plotly.graph_objects as go
from dash import dcc
from datetime import date
from pandas import to_datetime
from plotly.subplots import make_subplots
from utils import (get_latest_daily_agg, get_latest_monthly_agg, get_latest_weekly_agg,
                   get_weeks_of_month, get_column_extremas,
                   MONTHS_MAP, COLMAPPER)

SUBPLOT_SPACING_V = 0.08

daily_data = get_latest_daily_agg()
weekly_data = get_latest_weekly_agg()
monthly_data = get_latest_monthly_agg()

# --- dcc COMPONENTS --- #
highresweeklyplots = dcc.Graph(id="weekly-time-series")


# --- GRAPH BUILDING ROUTINES --- #
def build_weekly_binned_across_year(input_year, ycol, y2col, y3col,
                                    show_daily_scatter=False):
    """
    """
    y_offset = [(0, 2.5), (0.5, 0.5), (0.5, 0.5)]  # Offset values for each y-axis (min, max)

    data = weekly_data
    date_col = 'Week'
    y_cols = [ycol, y2col, y3col]
    max_year = data[date_col].dt.year.iloc[-1]  # If in_year = max_year, do something special

    if input_year == max_year:
        last_month = data.loc[len(data) - 1, date_col].month
        dfiltered = data[data[date_col] >= '{y}-{m}-01'.format(y=input_year - 1, m=last_month + 1)]
        last_of_prev_yr = len(dfiltered[dfiltered[date_col].dt.year == input_year - 1]) - 1
        color_scale = ["#e7c280" for _ in range(len(dfiltered))]
        color_scale[:last_of_prev_yr] = ["rgba(188, 196, 209, 0.6)"] * last_of_prev_yr
        marker_input = dict(color=color_scale)

    else:
        dfiltered = data[data[date_col].dt.year == int(input_year)]
        marker_input = None

    fig = make_subplots(rows=3, cols=1, row_heights=[0.3] * 3,
                        vertical_spacing=SUBPLOT_SPACING_V)

    fig = gr.simple_time_series(fig, dfiltered, xcol=date_col, ycol=y_cols[0],
                                xlabel=None, ylabel=y_cols[0],
                                row_idx=1, col_idx=1,
                                width_px=None, height_px=None,
                                marker_dict=marker_input,
                                truncate_bar_text=True)

    fig = gr.simple_time_series(fig, dfiltered, xcol=date_col, ycol=y_cols[1],
                                xlabel=None, ylabel=y_cols[1], plot_type='scatter',
                                row_idx=2, col_idx=1, height_px=None,
                                lineshape='spline')

    fig = gr.simple_time_series(fig, dfiltered, xcol=date_col, ycol=y_cols[2],
                                xlabel=None, ylabel=y_cols[2], plot_type='scatter',
                                row_idx=3, col_idx=1, height_px=None,
                                lineshape='spline')

    # Update x-ticks
    x_tick_filter = dfiltered[(dfiltered[date_col].dt.day >= 1) & (dfiltered[date_col].dt.day <= 7)]
    x_tick_labels = []
    for i, w in enumerate(x_tick_filter[date_col]):
        if i == 0:
            lbl = "{m} {y}".format(m=MONTHS_MAP[w.month][:3], y=w.year)
        elif i == 11:
            lbl = "{d:02} {m}<br>{y}".format(m=MONTHS_MAP[w.month][:3], d=w.day, y=w.year)
        else:
            lbl = "{d:02}<br>{m}".format(m=MONTHS_MAP[w.month][:3], d=w.day)
        x_tick_labels.append(lbl)

    x2_tick_labels = ["{d:02}<br>{m}".format(m=MONTHS_MAP[i.month][:3], d=i.day) for i in x_tick_filter[date_col]]

    fig.update_layout(
        xaxis1=dict(
            tickmode='array',
            nticks=12,
            ticks='outside',
            tickvals=x_tick_filter[date_col],
            ticktext=x_tick_labels,
        ),
        bargap=0.25,
        uniformtext_minsize=10,
        uniformtext_mode='hide',
        # margin=dict(l=5, r=3),
    )

    matching_xaxis_prop = dict(
        tickmode='array',
        nticks=12,
        ticks='outside',
        tickvals=x_tick_filter[date_col],
        ticktext=x2_tick_labels,
        range=dfiltered[date_col].iloc[[0, -1]],
    )

    # Since cliponaxis=True for Scatter plot, this will
    # ensure marker nodes are displayed above axis lines
    axis_layer_param = "below traces"

    fig.update_layout(
        xaxis2=matching_xaxis_prop,
        xaxis3=matching_xaxis_prop,
        yaxis=dict(tick0=0),
        yaxis2=dict(layer=axis_layer_param),
        yaxis3=dict(layer=axis_layer_param),
    )

    # Update y-axes
    # Add absolute y-scale across the years based on max y
    y_extremas = [get_column_extremas(data, colname) for colname in y_cols]

    for i in range(len(y_cols)):
        r = [y_extremas[i][0] - y_offset[i][0], y_extremas[i][1] + y_offset[i][1]]
        fig.update_yaxes(title_text=y_cols[i], range=r,
                         row=i + 1, col=1)

    fig.update_layout(height=675)

    # If toggled, overlay daily data onto the last two traces
    if show_daily_scatter:
        if input_year == max_year:
            date_bounds = dfiltered[date_col].iloc[0]
            trace_daily = daily_data[daily_data['Date'] >= date_bounds]
        else:
            trace_daily = daily_data[daily_data['Date'].dt.year == input_year]
        fig.add_trace(
            go.Scatter(
                x=trace_daily['Date'],
                y=trace_daily[y_cols[1]],
                name=y_cols[1].split('(')[0] + 'for single run',
                mode='markers',
                cliponaxis=True,
                marker=dict(color='rgba(52, 105, 167, 0.35)',
                            symbol='circle-open'),
                showlegend=False
            ),
            row=2, col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=trace_daily['Date'],
                y=trace_daily[y_cols[2]],
                name=y_cols[2].split('(')[0] + 'for single run',
                mode='markers',
                cliponaxis=True,
                marker=dict(color='rgba(212, 123, 101, 0.35)',
                            symbol='circle-open'),
                showlegend=False
            ),
            row=3, col=1,
        )

    return fig


def build_monthly_binned_across_year(input_year, ycol, y2col=None, y3col=None, show_daily_scatter=False):
    """
    """
    y_offset = [(0, 10), (0.5, 0.5), (0.5, 0.5)]  # Offset values for each y-axis (min, max)

    data = monthly_data
    data['Date'] = to_datetime([date(y, m, 1) for y, m in zip(data['Year'], data['Month'])], errors="coerce")
    date_col = 'Date'
    y_cols = [ycol, y2col, y3col]
    max_year = data[date_col].dt.year.iloc[-1]  # If in_year = max_year, do something special

    if input_year == max_year:
        last_month = data.loc[len(data) - 1, date_col].month
        dfiltered = data[data[date_col] >= '{y}-{m}-01'.format(y=input_year - 1, m=last_month + 1)]
        last_of_prev_yr = len(dfiltered[dfiltered[date_col].dt.year == input_year - 1])
        color_scale = ["#e7c280" for _ in range(len(dfiltered))]
        color_scale[:last_of_prev_yr] = ["rgba(188, 196, 209, 0.6)"] * last_of_prev_yr
        marker_input = dict(color=color_scale)

    else:
        dfiltered = data[data[date_col].dt.year == int(input_year)]
        marker_input = None

    fig = make_subplots(rows=3, cols=1, row_heights=[0.3] * 3,
                        vertical_spacing=SUBPLOT_SPACING_V)

    fig = gr.simple_time_series(fig, dfiltered, xcol=date_col, ycol=y_cols[0],
                                xlabel=None, ylabel=y_cols[0],
                                row_idx=1, col_idx=1,
                                width_px=None, height_px=None,
                                marker_dict=marker_input,
                                truncate_bar_text=True)

    fig = gr.simple_time_series(fig, dfiltered, xcol=date_col, ycol=y_cols[1],
                                xlabel=None, ylabel=y_cols[1], plot_type='scatter',
                                row_idx=2, col_idx=1, height_px=None,
                                lineshape='spline')

    fig = gr.simple_time_series(fig, dfiltered, xcol=date_col, ycol=y_cols[2],
                                xlabel=None, ylabel=y_cols[2], plot_type='scatter',
                                row_idx=3, col_idx=1, height_px=None,
                                lineshape='spline')

    # Update x-ticks
    x_tick_filter = dfiltered[(dfiltered[date_col].dt.day >= 1) & (dfiltered[date_col].dt.day <= 7)]
    x_tick_labels = []
    for i, w in enumerate(x_tick_filter[date_col]):
        if i == 0 or i == 11:
            lbl = "{m} {y}".format(m=MONTHS_MAP[w.month][:3], y=w.year)
        else:
            lbl = "{m}".format(m=MONTHS_MAP[w.month][:3])
        x_tick_labels.append(lbl)

    fig.update_layout(
        xaxis1=dict(
            tickmode='array',
            nticks=12,
            ticks='outside',
            tickvals=x_tick_filter[date_col],
            ticktext=x_tick_labels,
        ),
        bargap=0.25,
        uniformtext_minsize=10,
        uniformtext_mode='hide',
        # margin=dict(l=5, r=3),
    )

    matching_xaxis_prop = dict(
        tickmode='array',
        nticks=12,
        ticks='outside',
        tickvals=x_tick_filter[date_col],
        ticktext=x_tick_labels,
        # range=dfiltered[date_col].iloc[[0, -1]],
    )

    # Since cliponaxis=True for Scatter plot, this will
    # ensure marker nodes are displayed above axis lines
    axis_layer_param = 'below traces'

    fig.update_layout(
        xaxis2=matching_xaxis_prop,
        xaxis3=matching_xaxis_prop,
        yaxis=dict(tick0=0),
        yaxis2=dict(layer=axis_layer_param),
        yaxis3=dict(layer=axis_layer_param),
    )

    # Update y-axes
    # Add absolute y-scale across the years based on max y
    y_extremas = [get_column_extremas(data, colname) for colname in y_cols]

    for i in range(len(y_cols)):
        r = [y_extremas[i][0] - y_offset[i][0], y_extremas[i][1] + y_offset[i][1]]
        fig.update_yaxes(title_text=y_cols[i], range=r,
                         row=i + 1, col=1)

    fig.update_layout(height=675)

    # If toggled, overlay daily data onto the last two traces
    if show_daily_scatter:
        if input_year == max_year:
            date_bounds = dfiltered[date_col].iloc[0]
            trace_daily = daily_data[daily_data[date_col] >= date_bounds]
        else:
            trace_daily = daily_data[daily_data[date_col].dt.year == input_year]
        fig.add_trace(
            go.Scatter(
                x=trace_daily[date_col],
                y=trace_daily[y_cols[1]],
                name=y_cols[1].split('(')[0] + 'for single run',
                mode='markers',
                cliponaxis=True,
                marker=dict(color='rgba(52, 105, 167, 0.35)',
                            symbol='circle-open'),
                showlegend=False
            ),
            row=2, col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=trace_daily[date_col],
                y=trace_daily[y_cols[2]],
                name=y_cols[2].split('(')[0] + 'for single run',
                mode='markers',
                cliponaxis=True,
                marker=dict(color='rgba(212, 123, 101, 0.35)',
                            symbol='circle-open'),
                showlegend=False
            ),
            row=3, col=1,
        )

    return fig
