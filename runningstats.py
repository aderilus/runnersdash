""" runningstats.py: Takes in CSV file of health data
            (the output of preparedatasets.py) and builds
            a Dash app of visualizations.

Created 09 Dec. 2021
Modified 02 Mar. 2022

ver. 1.2 (02 Mar. 2022):
- Implemented linting to clean up code.
- In future versions, the routines in this file will be
  distributed between:
    - app.py
    - callbacks.py
    - index.py
    - layout.py
    - py files inside apps/

Known issue(s):
- Takes in a CSV file that's an output of preparedatasets.py,
  but which file does it need? The daily aggregate? Weekly?
  Monthly?
- Is get_weekly_data() method still necessary?


"""

__version__ = '1.2'

import os
import sys
import webbrowser
import dash
import preparedatasets
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

from dash import dash_table as dt
from dash.dash_table.Format import Format, Scheme, Trim
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
from threading import Timer

from datetime import datetime, date


# ========== LOAD CSV ========== #
def preprocess_data(csvfile):
    """ Read in a CSV to a DataFrame and format the latter.
    """
    # Read CSV file
    data = pd.read_csv(csvfile, index_col=0)

    # Format as type datetime
    data["Date"] = pd.to_datetime(data["Date"], format="%Y-%m-%d")
    data["runStartTime"] = pd.to_datetime(data["runStartTime"], yearfirst=True,
                                          format="%Y-%m-%d %H:%M:%S%z")
    data["runEndTime"] = pd.to_datetime(data["runEndTime"], yearfirst=True,
                                        format="%Y-%m-%d %H:%M:%S %z")

    # Drop rows where date precedes 12/2020
    data.drop(data[pd.DatetimeIndex(data["Date"]).year < 2020].index,
              inplace=True)
    data.drop(data[(pd.DatetimeIndex(data["Date"]).year == 2020) & (pd.DatetimeIndex(data["Date"]).month < 12)].index,
              inplace=True)
    data.reset_index(inplace=True, drop=True)

    # Sort by 'Date', descending
    data.sort_values(by=['Date'], inplace=True, ascending=False)

    # Insert Date column at position 0
    data.insert(0, 'Date_temp', data["Date"])
    data.drop('Date', axis=1, inplace=True)
    data.rename(columns={'Date_temp': 'Date'}, inplace=True)

    # Format date columns
    for col in ["runStartTime", "runEndTime"]:
        data[col] = pd.DatetimeIndex(data[col]).strftime("%Y-%m-%d %H:%M:%S")

    data["Date"] = data["Date"].dt.date

    return data


def get_numeric_colnames(dataframe):
    """Get column names where dtype is numeric
    """
    numeric_cols = dataframe.dtypes.index[dataframe.dtypes == 'float64'].tolist()
    return numeric_cols


def get_weekly_data(df, col, agg_method, datecol="Date"):
    """ Aggregates Pandas Series by week according to aggregation method.

    Args:
        df (pd.DataFrame):
        col (str):
        datecol (str):
        agg_method (str): 'sum' or 'avg'
    """
    agg = df.copy()
    agg[datecol] = agg[datecol] - pd.to_timedelta(7, unit='d')
    if agg_method == "sum":
        return agg.groupby(pd.Grouper(key=datecol, freq='W-MON'))[col].sum().reset_index()
    if agg_method == "avg":
        return agg.groupby(pd.Grouper(key=datecol, freq='W-Mon'))[col].mean().reset_index()


# Build layout of Dash
def generate_running_log(dataframe):
    """ Generate and format a DataTable to display DataFrame.
    """
    cols = []

    for i in dataframe.columns:
        if dataframe.dtypes.loc[i] == 'float64':
            cols.append(dict(id=i, name=i, type='numeric',
                        format=Format(precision=4, scheme=Scheme.decimal)))
        else:
            cols.append(dict(id=i, name=i))

    return dt.DataTable(
        id='tbl', data=dataframe.to_dict('records'),
        columns=cols,
        style_cell={'textAlign': 'left',
                    'font-family': 'sans-serif',
                    'font-size': '12px',
                    'minWidth': '30px',
                    'width': '100px',
                    'maxWidth': '100px',
                    'whiteSpace': 'normal'
                    },
        css=[{
            'selector': '.dash-spreadsheet td div',
            'rule': '''
                line-height: 15px;
                max-height: 30px; min-height: 3px; height: 30px;
                display: block;
                overflow-y: hidden;
            '''
        }],
        style_header={'fontWeight': 'bold', 'font-size': '11px'},
        style_cell_conditional=[
            {'if': {'column_id': 'duration (min)'}, 'width': '10%'},
            {'if': {'column_id': 'totalDistance (km)'}, 'width': '10%'},
            {'if': {'column_id': 'runStartTime'}, 'width': '10%'},
            {'if': {'column_id': 'runEndTime'}, 'width': '10%'},
            {'if': {'column_id': 'menstrualFlow (None)'}, 'width': '10%'},
            {'if': {'column_id': 'Date'}, 'width': '10%'},
        ]
    )


def distancegraph(distancecol, ycol2, xcol, xStart, xEnd):
    """ Generate a line and bar graph against time within a given date range.

    Args:
        distancecol (pd.Series): Series to graph in the y-axis (ascending=False)
        ycol2 (pd.Series): Secondary series to graph in the secondary y-axis (ascending=False)
        timecol (pd.Series): Column of dates to graph in the x-axis (ascending=False)
        dateStart (str or datetime): datetime date. If string, formatted as "YYYY-MM-dd"
                                     indicating the start of the date range.
        dateEnd (str or datetime): datetime date. If string, formatted as "YYYY-MM-dd"
                                   indicating the end of the date range.

    Output:
        graph (dcc.Graph)
    """
    # if type(dateStart) == 'str':
    #     dateStart = datetime.strptime(dateStart, "%Y-%m-%d")
    #     dateEnd = datetime.strptime(dateEnd, "%Y-%m-%d")

    # startIndex = pd.Index(timecol).get_loc(dateStart)
    # endIndex = pd.Index(timecol).get_loc(dateEnd)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Bar(x=xcol, y=distancecol, name=distancecol.name),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=xcol, y=ycol2, name=ycol2.name, mode='lines+markers',
                   connectgaps=True),
        secondary_y=True
    )

    # Set xy-axis title
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="{n}".format(n=distancecol.name),
                     secondary_y=False)
    fig.update_yaxes(title_text="{n}".format(n=ycol2.name), secondary_y=True)

    return fig


def generate_distancegraph(df, distance_col, ycol2, dcc_id, datecol="Date",
                           dateStart="", dateEnd=""):
    """
    Args:
        df (pd.DataFrame):
        distance_col (str):
        ycol2 (str):
        dateStart (str): String formatted as "YYYY-mm-dd"
        dateEnd (str): String formatted as "YYYY-mm-dd"
    Kwargs:
        datecol (str): Name of the DataFrame's date column.
    """

    fig = distancegraph(df[distance_col], df[ycol2], xcol=df[datecol],
                        xStart=dateStart, xEnd=dateEnd)

    return dcc.Graph(figure=fig, id=dcc_id)


# Open browser automatically
def open_dash_link():
    webbrowser.open_new('http://127.0.0.1:8050/')


# Run Dash server
def generate_dash_server(toggle_debug=False):
    Timer(1, open_dash_link).start()
    app.run_server(debug=toggle_debug)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print("USAGE: python runningstats.py /path/to/csv", file=sys.stderr)
        sys.exit(1)

    CSV_FILE = sys.argv[1]

    # If csv_file can't be found, run processdatabase and create file
    if not os.path.isfile(CSV_FILE):
        db_path = "{dt}_applehealth.db".format(dt=sys.argv[1])
        s = preparedatasets.DatasetPrep(db_path, verbose=True, testing=False)
        s.load_database()
        s.get_all_aggregates()
        s.get_resampled_data('Running', on='Date', write_to_file=True)

    dataframe = preprocess_data(CSV_FILE)
    numeric_cols = get_numeric_colnames(dataframe)

    # # Create instance of a Dash class
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])

    # Define Dash layout
    app.layout = html.Div(
        children=[
            html.H1(children="Running stats", style={"padding": '10px'},
                    className="header-title"),
            html.P(
                children="blah blah blah blah blahdity view running trends and\
                          health metrics",
                style={"paddingLeft": '10px'},
            ),

            dbc.Row(
                children=[
                    html.H2(children="  Time Series Graphs",
                            style={"padding-left": '10spx'}),
                ],
                style={"padding": '10px'},
            ),

            dbc.Row(  # row 1: time seres
                children=[
                    dbc.Row([
                        dbc.Col(
                            children=[
                                dcc.Dropdown(
                                    id='distance-graph-y1',
                                    options=[{'label': i, 'value': i} for i in numeric_cols],
                                    value=numeric_cols[1]
                                ),

                                dcc.RadioItems(
                                    id='distance-graph-y1-type',
                                    options=[{'label': ' ' + i, 'value': i} for i in ['bar', 'scatter', 'line']],
                                    value='bar',
                                    labelStyle={'display': 'inline-block',
                                                'padding': '5px'},
                                ),
                            ]),

                        dbc.Col(
                            children=[
                                dcc.Dropdown(
                                    id='distance-graph-y2',
                                    options=[{'label': i, 'value': i} for i in numeric_cols],
                                    value=numeric_cols[3]
                                ),

                                dcc.RadioItems(
                                    id='distance-graph-y2-mode',
                                    options=[{'label': ' ' + i, 'value': i} for i in ['lines', 'markers', 'lines+markers']],
                                    value='lines+markers',
                                    labelStyle={'display': 'inline-block',
                                                'padding': '5px'}
                                ),
                            ]),
                    ]),

                    dbc.Row(
                        children=[
                            # generate_distancegraph(dataframe,
                            #                        "totalDistance (km)",
                            #                        "VO2Max (mL/min·kg)",
                            #                        dcc_id='distance-graph'),
                            dcc.Graph(id='distance-graph')
                        ]
                    ),
                ]),  # end row 1

            # dbc.Row([
            #      # col 1: Weekly view
            #     dbc.Col(
            #         children=[
            #             html.H2(children="Weekly"),
            #         ]
            #     ), # end col 1

            #     # col 2: Weekly view
            #     dbc.Col(
            #         children=[
            #             html.H2(children="Monthly"),
            #         ]
            #     )
            # ]), # end row 2

            dbc.Row(dbc.Col(
                children=[
                    html.H2(children="Running Log", style={"padding": '5px'}),
                    generate_running_log(dataframe),  # Table
                ]
            ), style={"padding": '20px'})  # end row 3

        ])

    @app.callback(
        output=Output('distance-graph', 'figure'),
        inputs=[Input('distance-graph-y1', 'value'),
                Input('distance-graph-y2', 'value'),
                Input('distance-graph-y1-type', 'value'),
                Input('distance-graph-y2-mode', 'value')]
    )
    def update_graph(y1_colname, y2_colname, y1_type, y2_mode):

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add traces
        if y1_type == 'bar':
            fig.add_trace(
                go.Bar(x=dataframe["Date"], y=dataframe[y1_colname],
                       name=y1_colname),
                secondary_y=False,
            )
        else:
            if y1_type == 'line':
                y1_mode = 'lines+markers'
            else:
                y1_mode = 'markers'

            fig.add_trace(
                go.Scatter(x=dataframe["Date"], y=dataframe[y1_colname],
                           name=y1_colname, mode=y1_mode, connectgaps=True),
                secondary_y=False,
            )

        fig.add_trace(
            go.Scatter(x=dataframe["Date"], y=dataframe[y2_colname],
                       name=y2_colname, mode=y2_mode, connectgaps=True),
            secondary_y=True
        )

        # Set xy-axis title
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="{n}".format(n=y1_colname),
                         secondary_y=False)
        fig.update_yaxes(title_text="{n}".format(n=y2_colname),
                         secondary_y=True)

        return fig

    generate_dash_server(True)
