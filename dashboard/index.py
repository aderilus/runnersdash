from dash import Dash
from utils import (get_latest_daily_agg,
                   get_latest_weekly_agg,
                   get_latest_monthly_agg,
                   get_resampled_runs,
                   get_running_logs,
                   get_column_extremas)
import dash_bootstrap_components as dbc

# --- GLOBAL VARIABLES --- #
# Load datasets
daily_data = get_latest_daily_agg()
weekly_data = get_latest_weekly_agg(verbose=True)
monthly_data = get_latest_monthly_agg()
resampled_runs = get_resampled_runs()
running_log = get_running_logs()

# Get min, max years of dataset
min_date, max_date = get_column_extremas(resampled_runs, 'index')
min_year = min_date.year
max_year = max_date.year

# --- Dash instance --- #
app = Dash(__name__,
           title="Runner's Dash",
           external_stylesheets=[dbc.themes.LITERA],
           suppress_callback_exceptions=True)
