""" Defines main navigation components.
"""

import dash_bootstrap_components as dbc

navbuttons = dbc.ButtonGroup(
    children=[
        dbc.Button("Main view",
                   color="secondary",
                   outline=True),
        dbc.Button("Middle",
                   color="secondary",
                   outline=True),
        dbc.Button("Right",
                   color="secondary",
                   outline=True)
    ],
    id="navbuttons",
)

navcontainer = dbc.Container(
    children=[
        dbc.Row(
            [
                dbc.Col(),
                dbc.Col(navbuttons, 
                        width="auto"),
                dbc.Col(),
            ],
            style={"margin": "1rem"}
        )
    ],
)
