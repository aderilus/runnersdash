""" Graph building routine(s) and dcc components associated with
main page time-series graphs.
"""
import dashboard.layout.graphing as gr
import plotly.graph_objects as go
import utils
from dash import dcc
from datetime import date
from pandas import to_datetime
from plotly.subplots import make_subplots


SUBPLOT_SPACING_V = 0.07

daily_data = utils.get_latest_daily_agg()
weekly_data = utils.get_latest_weekly_agg()
monthly_data = utils.get_latest_monthly_agg()


# --- dcc COMPONENTS --- #
highresweeklyplots = dcc.Graph(id="weekly-time-series")

# Y INPUTS
cols = daily_data.columns.tolist()
y1_tuple = [('Total Distance', 'sum'),
            ('Total Duration', 'sum'),
            ('Total Energy Burned', 'mean'),
            ('Elevation Ascended', 'mean'),
            ('Menstrual Flow', ' '),
            ]

y1_options = [f"{utils.colmapper(i, cols)}_{j}" for i, j in y1_tuple]
y1_picker = dcc.Dropdown(
    options=[
        {"label": i.replace('_', ', '),
         "value": i} for i in y1_options
    ],
    value=y1_options[0],
    placeholder="Choose y-axis 1",
    clearable=False,
    id='time-series-y1',
)

combined_metrics = ['Avg Pace',
                    'Avg VO2 Max',
                    'Avg METs',
                    'Avg Resting Heart Rate',
                    'Avg Heart Rate Variability',
                    'Avg Respiratory Rate',
                    'Avg Body Mass',
                    'Avg Blood Pressure Diastolic',
                    'Avg Blood Pressure Systolic',
                    ]
agg_type = 'mean'

y2_options = [f"{utils.colmapper(i, cols)}_{agg_type}" for i in combined_metrics]
y2_picker = dcc.Dropdown(
    options=[
        {"label": i.split('_')[0].split(' (')[0],
         "value": i} for i in y2_options
    ],
    value=y2_options[0],
    placeholder="Choose y-axis 2",
    id='time-series-y2',
    clearable=False,
)

y3_options = y2_options[1:]
y3_picker = dcc.Dropdown(
    options=[
        {"label": i.split('_')[0].split(' (')[0],
         "value": i} for i in y3_options
    ],
    value=y3_options[0],
    placeholder="Choose y-axis 3",
    id='time-series-y3',
    clearable=False,
)


# --- GRAPH BUILDING ROUTINES --- #
def build_agg_binned_across_year(input_year, freq,
                                 ycol, ycol_sub,
                                 y2col, y2col_sub,
                                 y3col, y3col_sub,
                                 show_daily_scatter=False):
    """

    Args:
        input_year ():
        freq (str): Specifies aggregation frequency, takes in either 'w' or 'm'
            representing weekly and monthly binning respectively.
        ycol (str):
        ycol_sub (str):
        y2col (str):
        y2col_sub (str):
        y3col (str):
        y3col_sub (str):

    Kwargs:
        show_daily_scatter (bool): Toggle overlay daily data points over graph.
            Default False.
    """
    weekly_bin = True if freq == 'w' else False

    # Specify dataset
    if weekly_bin:
        data = weekly_data
        # Offset values for each y-axis (min, max)
        y_offset = [(0, 2.5), (0.5, 0.5), (0.5, 0.5)]
    else:  # Monthly binning
        data = monthly_data
        y_offset = [(0, 10), (0.5, 0.5), (0.5, 0.5)]
    date_col = data.index
    max_year = date_col[-1].year  # If in_year = max_year, do something special

    if input_year == max_year:
        last_month = date_col[-1].month
        dfiltered = data[date_col >= '{y}-{m}-01'.format(y=input_year - 1, m=last_month + 1)]
        last_of_prev_yr = len(dfiltered[dfiltered.index.year == input_year - 1]) - 1
        color_scale = ["#e7c280" for _ in range(len(dfiltered))]
        color_scale[:last_of_prev_yr] = ["rgba(188, 196, 209, 0.6)"] * last_of_prev_yr
        marker_input = dict(color=color_scale)

    else:
        dfiltered = data[date_col.year == int(input_year)]
        marker_input = None

    y_map = [(ycol, ycol_sub),
             (y2col, y2col_sub),
             (y3col, y3col_sub)
             ]

    y_series = [dfiltered[i] if not j else dfiltered[i][j] for i, j in y_map]

    fig = make_subplots(rows=3, cols=1, row_heights=[0.3] * 3,
                        vertical_spacing=SUBPLOT_SPACING_V,
                        shared_xaxes=True)

    bar_template = '%{y:.2s}' if weekly_bin else '%{y:.3s}'
    fig = gr.simple_time_series(fig, xcol=dfiltered.index, ycol=y_series[0],
                                xlabel=None, ylabel=ycol,
                                row_idx=1, col_idx=1,
                                width_px=None, height_px=None,
                                marker_dict=marker_input,
                                bar_text_template=bar_template)

    fig = gr.simple_time_series(fig, xcol=dfiltered.index, ycol=y_series[1],
                                xlabel=None, ylabel=y2col, plot_type='scatter',
                                row_idx=2, col_idx=1, height_px=None,
                                lineshape='spline')

    fig = gr.simple_time_series(fig, xcol=dfiltered.index, ycol=y_series[2],
                                xlabel=None, ylabel=y3col, plot_type='scatter',
                                row_idx=3, col_idx=1, height_px=None,
                                lineshape='spline')

    # Update x-ticks
    x_tick_filter = dfiltered[(dfiltered.index.day >= 1) & (dfiltered.index.day <= 7)]
    x_tick_labels = []
    for i, w in enumerate(x_tick_filter.index):
        if i == 0:
            lbl = "{m} {y}".format(m=utils.MONTHS_MAP[w.month][:3], y=w.year)
        elif i == 11:
            if weekly_bin:
                lbl = "{d:02} {m}<br>{y}".format(m=utils.MONTHS_MAP[w.month][:3], d=w.day, y=w.year)
            else:  # Monthly bin settings
                lbl = "{m} {y}".format(m=utils.MONTHS_MAP[w.month][:3], y=w.year)
        else:
            if weekly_bin:
                lbl = "{d:02}<br>{m}".format(m=utils.MONTHS_MAP[w.month][:3], d=w.day)
            else:
                lbl = "{m}".format(m=utils.MONTHS_MAP[w.month][:3])

        x_tick_labels.append(lbl)

    if weekly_bin:
        x2_tick_labels = ["{d:02}<br>{m}".format(m=utils.MONTHS_MAP[i.month][:3], d=i.day) for i in x_tick_filter.index]
    else:
        x2_tick_labels = x_tick_labels.copy()

    fig.update_layout(
        xaxis1=dict(
            tickmode='array',
            nticks=12,
            ticks='outside',
            tickvals=x_tick_filter.index,
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
        tickvals=x_tick_filter.index,
        ticktext=x2_tick_labels,
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

    # Since we set shared_xaxes = True, but we still want to show tick
    # labels for each subplot.
    fig.layout['xaxis'].showticklabels = True
    fig.layout['xaxis2'].showticklabels = True

    # Update y-axes
    # Add absolute y-scale across the years based on max y
    y_extremas = [utils.get_column_extremas(data, i, j) for i, j in y_map]

    for i in range(len(y_map)):
        r = [y_extremas[i][0] - y_offset[i][0], y_extremas[i][1] + y_offset[i][1]]
        fig.update_yaxes(title_text=y_map[i][0], range=r,
                         row=i + 1, col=1)

    fig.update_layout(
        height=675,
        hovermode="x",
    )

    # If toggled, overlay daily data onto the last two traces
    if show_daily_scatter:
        if input_year == max_year:
            date_bounds = dfiltered.index[0]
            trace_daily = daily_data[daily_data.index >= date_bounds]
        else:
            trace_daily = daily_data[daily_data.index.year == input_year]
        fig.add_trace(
            go.Scatter(
                x=trace_daily.index,
                y=trace_daily[y2col],
                name=y2col.split(' (')[0] + 'for single run',
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
                x=trace_daily.index,
                y=trace_daily[y3col],
                name=y3col.split(' (')[0] + 'for single run',
                mode='markers',
                cliponaxis=True,
                marker=dict(color='rgba(212, 123, 101, 0.35)',
                            symbol='circle-open'),
                showlegend=False
            ),
            row=3, col=1,
        )

    return fig


def build_monthly_binned_across_year(input_year, ycol, y2col=None, y3col=None,
                                     show_daily_scatter=False):
    """
    """
    y_offset = [(0, 10), (0.5, 0.5), (0.5, 0.5)]  # Offset values for each y-axis (min, max)
    data = monthly_data
    date_col = data.index
    y_cols = [ycol, y2col, y3col]
    max_year = date_col[-1].year  # If in_year = max_year, do something special

    if input_year == max_year:
        last_month = date_col[-1].month
        dfiltered = data[date_col >= '{y}-{m}-01'.format(y=input_year - 1, m=last_month + 1)]
        last_of_prev_yr = len(dfiltered[date_col.year == input_year - 1])
        color_scale = ["#e7c280" for _ in range(len(dfiltered))]
        color_scale[:last_of_prev_yr] = ["rgba(188, 196, 209, 0.6)"] * last_of_prev_yr
        marker_input = dict(color=color_scale)

    else:
        dfiltered = data[date_col.year == int(input_year)]
        marker_input = None

    fig = make_subplots(rows=3, cols=1, row_heights=[0.3] * 3,
                        vertical_spacing=SUBPLOT_SPACING_V,
                        shared_xaxes=True,
                        )

    fig = gr.simple_time_series(fig, dfiltered, xcol=date_col, ycol=y_cols[0],
                                xlabel=None, ylabel=y_cols[0],
                                row_idx=1, col_idx=1,
                                width_px=None, height_px=None,
                                marker_dict=marker_input,
                                bar_text_template='%{y:.3s}')

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
            lbl = "{m} {y}".format(m=utils.MONTHS_MAP[w.month][:3], y=w.year)
        else:
            lbl = "{m}".format(m=utils.MONTHS_MAP[w.month][:3])
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

    # Since we set shared_xaxes = True, but we still want to show tick
    # labels for each subplot.
    fig.layout['xaxis'].showticklabels = True
    fig.layout['xaxis2'].showticklabels = True

    # Update y-axes
    # Add absolute y-scale across the years based on max y
    y_extremas = [utils.get_column_extremas(data, colname) for colname in y_cols]

    for i in range(len(y_cols)):
        r = [y_extremas[i][0] - y_offset[i][0], y_extremas[i][1] + y_offset[i][1]]
        fig.update_yaxes(title_text=y_cols[i], range=r,
                         row=i + 1, col=1)

    fig.update_layout(
        height=675,
        hovermode="x",
    )

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
                name=y_cols[2].split(' (')[0] + 'for single run',
                mode='markers',
                cliponaxis=True,
                marker=dict(color='rgba(212, 123, 101, 0.35)',
                            symbol='circle-open'),
                showlegend=False
            ),
            row=3, col=1,
        )

    return fig
