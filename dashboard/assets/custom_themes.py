""" Defines templates for graph object figures.

See: https://plotly.com/python/templates/#specifying-themes-in-graph-object-figures
"""

import plotly.graph_objects as go

grid_color = '#ebf0ee'
axis_label_color = '#69737d'  # '#7b899f'
axis_line_color = '#8b9ab2'
zeroline_color = '#626e7f'
colorway1 = ['#84c0a9', '#3469a7', '#d47b65', '#817cc0', '#e7c280']
colorway2 = ['#3469a7', '#e78767', '#a1c497', '#e7c280']
toggle_colorway = colorway1

# https://plotly.com/python-api-reference/generated/plotly.graph_objects.layout.html?highlight=plotly%20graph_objects%20layout%20template#plotly.graph_objects.layout.Template
timeseriesplate = go.layout.Template(
    layout={
        # https://plotly.com/python-api-reference/generated/plotly.graph_objects.Layout.html#plotly.graph_objects.Layout
        'coloraxis': {
            'colorbar': {
                'outlinewidth': 0,
                'tickcolor': '#ffffff',
                'ticklen': 6,
                'ticks': 'inside',
            },
        },
        'colorway': toggle_colorway,
        'font': {'color': axis_label_color,
                 'family': 'Helvetica Neue, Helvetica, Arial, Sans-serif',
                 },
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'left',
            'x': 0,
        },
        'margin': dict(l=35, r=10, t=40, b=30),
        # https://plotly.com/python/reference/layout/xaxis/#layout-xaxis
        'xaxis': {
            'automargin': True,
            'showgrid': True,
            'color': axis_label_color,
            'gridcolor': grid_color,
            'showline': True,
            'linecolor': axis_line_color,
            'zeroline': False,
            'zerolinecolor': zeroline_color,
            'zerolinewidth': 1,
            'ticks': '',
            'tickmode': 'array',
        },
        # https://plotly.com/python/reference/layout/yaxis/#layout-yaxis
        'yaxis': {
            'automargin': True,
            'color': axis_label_color,
            'showgrid': True,
            'gridcolor': grid_color,
            'showline': True,
            'linecolor': grid_color,
            'zeroline': False,
            'zerolinecolor': zeroline_color,
            'zerolinewidth': 1,
            'ticks': '',
            'title': {'font': {'size': 12},
                      'standoff': 5},
        }
    }
)

timeseriesplate.data.bar = [
    go.Bar(textfont={'family': 'Arial, Helvetica Neue, Helvetica, Sans-serif',
                     'size': 13,
                     },
           showlegend=True,
           insidetextfont={'family': 'Arial, Helvetica Neue, Helvetica, Sans-serif',
                           'size': 13,
                           'color': "#ffffff",
                           },
           outsidetextfont={'family': 'Arial, Helvetica Neue, Helvetica, Sans-serif',
                            'size': 13,
                            'color': axis_label_color,
                            },
           textposition='outside',
           ),
]

timeseriesplate.data.scatter = [
    go.Scatter(
        connectgaps=True,
        textfont={'family': 'Arial, Helvetica Neue, Helvetica, Sans-serif',
                  'size': 13,
                  },
    )
]
