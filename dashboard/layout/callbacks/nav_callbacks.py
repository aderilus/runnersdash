from dash import Input, Output, callback
from dashboard.index import app
from dashboard.pages import home, heatmapview

path_prefix = ''


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'))
def display_page(pathname):
    if pathname in ["{0}/home".format(path_prefix), "/"]:
        return home.layout
    if pathname == "{0}/heatmapview".format(path_prefix):
        return heatmapview.layout
    else:
        return '404'


@app.callback(
    Output('home-link', 'active'),
    Input('url', 'pathname'),
)
def set_home_page_active(pathname):
    return pathname == "{0}/home".format(path_prefix)


@app.callback(
    Output('heatmapview-link', 'active'),
    Input('url', 'pathname'),
)
def set_home_page_active(pathname):
    return pathname == "{0}/heatmapview".format(path_prefix)
