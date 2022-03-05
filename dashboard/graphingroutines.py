""" graphingroutines.py: Graph-making routines for the dashboard.
"""

from dash import dash_table as dt
from dash.dash_table.Format import Format, Scheme
from dash import dcc
from plotly.subplots import make_subplots

import plotly.graph_objects as go


# --- RUNNING LOG --- #
def generate_running_log(dataframe):
    """ Generate and format a DataTable to display DataFrame.

    Args:
        dataframe (pd.DataFrame)

    Returns:
        A dash_table.DataTable object.
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


# --- GRAPHS AND CHARTS --- #
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

    Returns:

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

    Returns: A dcc.Graph
    """

    fig = distancegraph(df[distance_col], df[ycol2], xcol=df[datecol],
                        xStart=dateStart, xEnd=dateEnd)

    return dcc.Graph(figure=fig, id=dcc_id)
