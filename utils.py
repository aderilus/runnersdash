""" Used by both preparedatasets.py and Dash app files.
"""

from numpy import sort

# --- Constants --- #
DAYS_OF_WK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
ABBREV_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr',
                 'May', 'Jun', 'Jul', 'Aug',
                 'Sep', 'Oct', 'Nov', 'Dec']


def get_year_extrema(df, year_column):
    """ Returns the years of the oldest and newest entry of the
        given DataFrame.
    """

    unique_years = df[year_column].unique()
    sorted_years = sort(unique_years)

    oldest = sorted_years[0]
    newest = sorted_years[-1]

    return oldest, newest
