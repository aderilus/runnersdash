from dash import html

header = html.Div(
    id="header",
    className="dashheader",
    children=[
        html.H5("Runner's Dash"),
        html.H6("View running statistics and other health metrics, \
                from imported Apple Health data.")
    ])
