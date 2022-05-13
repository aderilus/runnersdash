""" Used by both preparedatasets.py and Dash app files.
"""

import pandas as pd
import re
import settings
from pathlib import Path
from numpy import sort
from calendar import monthrange, monthcalendar, week
from datetime import datetime, timedelta, date

# --- Constants --- #
DAYS_OF_WK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
DAY_MAP = dict(zip(range(1, 8), DAYS_OF_WK))  # Use date.isoweekday()
MONTHS = ['January', 'February', 'March', 'April', 'May',
          'June', 'July', 'August', 'September', 'October',
          'November', 'December']
ABBREV_MONTHS = [i[:3] for i in MONTHS]
MONTHS_MAP = dict(zip(range(1, 13), MONTHS))


def get_project_root(test=False):
    root = Path(__file__).parent
    if test:
        print('Project root: ', root)
    return root


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
        files. Returns the date as a string formatted as "YYYYmmdd".
    """
    path_to_search = get_project_root().joinpath('data')
    csvlist = list(sorted(path_to_search.glob('*.csv')))

    if len(csvlist) == 0:
        raise OSError("No CSV files found in {0}".format(str(path_to_search)))

    latestcsvpath = str(csvlist[-1])
    export_date = extract_export_date(latestcsvpath)

    return export_date


def get_unit_from_string(input):
    """ Returns the unit (as a string) from a string formatted as
    "Measured values (unit)".
    """
    isolate1 = input.split('(')[-1]
    return isolate1.split(')')[0]


def format_pace(pace):
    """ Converts pace as a decimal to minutes and seconds.
    """
    pace_str = str(pace)
    pace_split = pace_str.split('.')
    pace_minutes = int(pace_split[0])
    pace_decimal = ".{0}".format(pace_split[1])
    pace_seconds = float(pace_decimal) * 60

    return pace_minutes, pace_seconds


def get_weeks_of_month(in_month, in_year):
    """ Gives the dates of the first day of each week of the month, year.
    Args:
        in_month (int): Month formatted as an int.
        in_year (int): Year.

    Returns:
        A list of the start dates, as a datetime object, of each
        week, given the month and year.

        Example: The first day of the week of March 2022 is not
                 March 1 but February 28. The first element of the output
                 would be datetime.date(2022, 2, 28).
    """
    month_cal = monthcalendar(in_year, in_month)
    week_start_dates = []

    for wk in month_cal:
        if wk[0] == 0:
            # If the first day of the month is not the 1st of the month
            # but one of the last days of the previous month
            if in_month == 1:
                prev_year = in_year - 1
                prev_month = 12
            else:
                prev_year = in_year
                prev_month = in_month - 1

            n_zero = wk.count(0)
            last_date = monthrange(prev_year, prev_month)[1]
            prev_month_last_day = date(prev_year, prev_month, last_date)
            first_day_current_month = prev_month_last_day - timedelta(days=n_zero - 1)

            week_start_dates.append(first_day_current_month)

        else:
            week_start_dates.append(date(in_year, in_month, wk[0]))

    return week_start_dates


# --- GET DATA --- #
def get_column_extremas(df, column_name, column_name_level1=None):
    """ Returns the mininum and maximum of a column in a given
        DataFrame.

    Args:
        df (pd.DataFrame): The dataset to work with.
        column_name (str): The name of the column to get the extrema of.

    Kwargs:
        column_name_level1 (str or None): If DataFrame has MultiIndex columns,
            this is the level 1 label.

    Returns: A tuple of two values: (min, max).
    """
    if column_name == 'index':
        sorted_index = df.index.sort_values()
        return (sorted_index[0], sorted_index[-1])

    if column_name_level1:  # If DataFrame has MultiIndex columns
        filtered_df = df[df[column_name][column_name_level1].notnull()]
        unique_values = filtered_df[column_name][column_name_level1].unique()
    else:
        filtered_df = df[df[column_name].notnull()]  # Filter out NaN rows
        unique_values = filtered_df[column_name].unique()

    sorted_values = sort(unique_values)

    minimum = sorted_values[0]
    maximum = sorted_values[-1]

    return (minimum, maximum)


def colmapper(substr, column_list):
    """ Given a substring, finds its first instance within the
    column list (case-sensitive).

    Example:
        Let `w` be the weekly aggregate DataFrame columns (MultiIndex),
        containing 4 instances of 'Total Distance (km)'.

        colmapper("Total Distance", w) -> 'Total Distance (km)'
        colmapper("total distance", w) -> ValueError

    Args:
        substr (str): Substring (case-sensitive) to find within column list.
        column_list (list): DataFrame list of columns. Can be single or
            MultiIndex.

    Returns:
        A string matching an element within column_list.
    """

    # If column_list is MultiIndex, flatten to the first level
    if type(column_list[0]) == tuple:
        cols = [c[0] for c in column_list]
    else:
        cols = column_list

    pattern = re.compile(fr".*{substr}.*")
    matches = list(filter(pattern.match, cols))

    if not matches:
        raise ValueError(f"No matches found for {substr}.")

    return matches[0]


# --- LOAD DATA ROUTINES --- #
def get_csv_file_path(file_type, verbose=False):
    """ Given a file type, returns the path to its latest version.
    Args:
        file_type (str): Specifies which CSV file to return. Takes in
                         specific strings: ['dailyagg', 'weeklyagg',
                         'monthlyagg', 'running-resampled', 'running-log'].
    Kwargs:
        verbose (bool): If True, will print the file path.

    Returns:
        Path to file as a pathlib.PosixPath object.
    """
    valid_types = ['dailyagg',
                   'weeklyagg',
                   'monthlyagg',
                   'running-resampled',
                   'running-log'
                   ]
    if file_type not in valid_types:
        raise ValueError(f"Must pass in one of the following as parameter: {valid_types}")

    export_date = get_latest_exportdate()
    file_suffix = settings.AGG_D_SUFFIX

    if file_type == 'weeklyagg':
        file_suffix = settings.AGG_W_SUFFIX
    elif file_type == 'monthlyagg':
        file_suffix = settings.AGG_M_SUFFIX
    elif file_type == 'running-resampled':
        file_suffix = f'Running_{settings.RESAMPLE_D_SUFFIX}'
    elif file_type == 'running-log':
        file_suffix = 'Running'

    file_name = "{0}_{1}.csv".format(export_date, file_suffix)
    file_path = get_project_root().joinpath(settings.PD_OUTPUT_SUBDIR, file_name)

    if verbose:
        print("Reading from... {0}".format(file_path))

    return file_path


def get_latest_daily_agg(verbose=False):
    """ Reads in the file "{date}_dailyAggregate.csv" and returns it
        as a DataFrame.
    """
    data_path = get_csv_file_path('dailyagg', verbose)
    data = pd.read_csv(data_path,
                       index_col='Date',
                       parse_dates=True,
                       infer_datetime_format=True)

    return data


def get_latest_weekly_agg(verbose=False):
    """ Reads in the file "{date}_weeklyAggregate.csv" and returns it
        as a DataFrame.
    """
    data_path = get_csv_file_path('weeklyagg', verbose)
    data = pd.read_csv(data_path,
                       header=[0, 1],
                       parse_dates=True,
                       index_col=0,
                       infer_datetime_format=True)

    # Rename any Unnamed column level 1's
    renamed_columns = [(x[0], '') if x[1].startswith("Unnamed:") else x for x in data.columns.tolist()]
    data.columns = pd.MultiIndex.from_tuples(renamed_columns)

    return data


def get_latest_monthly_agg(verbose=False):
    """ Reads in the file "{date}_monthlyAggregate.csv" and returns it
        as a DataFrame.
    """
    data_path = get_csv_file_path('monthlyagg', verbose)
    data = pd.read_csv(data_path,
                       header=[0, 1],
                       parse_dates=True,
                       index_col=0,
                       infer_datetime_format=True)

    return data


def get_resampled_runs(verbose=False):
    """ Returns the latest version of "{date}_Running_resampledDaily.csv" as
        a DataFrame.
    """
    dtype_map = {'Calendar Week': int,
                 }
    data_path = get_csv_file_path('running-resampled', verbose)
    data = pd.read_csv(data_path,
                       index_col='Date',
                       parse_dates=True,
                       dtype=dtype_map)
    data['startDate'] = pd.to_datetime(data['startDate'],
                                       format="%Y-%m-%d %H:%M:%S%z")

    return data


def get_running_logs(verbose=False):
    """ Returns the latest version of "{date}_Running.csv" as a DataFrame.
    """
    dtype_map = {'sourceName': str}
    data_path = get_csv_file_path('running-log', verbose)
    data = pd.read_csv(data_path,
                       index_col=0,
                       parse_dates=['startDate', 'endDate'],
                       dtype=dtype_map)
    data['startDate'] = pd.to_datetime(data['startDate'],
                                       format="%Y-%m-%d %H:%M:%S%z")
    return data
