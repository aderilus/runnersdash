from dash import Dash
import dash_bootstrap_components as dbc


app = Dash(__name__,
           title="Runner's Dash",
           external_stylesheets=[dbc.themes.ZEPHYR])
