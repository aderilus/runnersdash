""" Used by both preparedatasets.py and Dash app files.
"""

from pathlib import Path
from numpy import sort

# --- Constants --- #
DAYS_OF_WK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
ABBREV_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr',
                 'May', 'Jun', 'Jul', 'Aug',
                 'Sep', 'Oct', 'Nov', 'Dec']


def extract_export_date(db_path):
    """ Returns export date of the database file as a string formatted
        as "YYYYmmdd".
    """
    split_db_path = db_path.split('/')
    if len(split_db_path) > 1:
        export_date = split_db_path[-1].split('_')[0]
    else:
        export_date = split_db_path[0].split('_')[0]

    return export_date


def get_latest_exportdate():
    """ Searches 'data/' folder for the date of most recent csv
        files.
    """
    csvlist = list(sorted(Path('data/').glob('*.csv')))
    latestcsvpath = str(csvlist[-1])
    export_date = extract_export_date(latestcsvpath)

    return export_date


def get_year_extrema(df, year_column):
    """ Returns the years of the oldest and newest entry of the
        given DataFrame.
    """

    unique_years = df[year_column].unique()
    sorted_years = sort(unique_years)

    oldest = sorted_years[0]
    newest = sorted_years[-1]

    return oldest, newest
