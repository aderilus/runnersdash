from dash import Input, Output, callback
from dashboard.index import app
from dashboard.pages import home

path_prefix = ''


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'))
def display_page(pathname):
    if pathname in [f"{path_prefix}/home", "/"]:
        return home.layout
    else:
        return '404'


@app.callback(
    Output('home-link', 'active'),
    Input('url', 'pathname'),
)
def set_home_page_active(pathname):
    return pathname == f"{path_prefix}/home"
