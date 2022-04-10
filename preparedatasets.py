"""
preparedatasets.py: Imports and formats SQL tables as DataFrames for
                    visualization and analysis.
                    Outputs, stored in 'data' sub-directory:
                        1. "[date]_dailyAggregate.csv"
                        2. "[date]_weeklyAggregate.csv"
                        3. "[date]_monthlyAggregate.csv"
                        4. "[date]_running_resampledDaily.csv"

ver 1.2:
    - Reorganizes routines into class DatasetPrep.
    - Implemented linting to clean up code

ver. 1.3:
    - Adds columns 'Day of Week' and 'Calendar Week' to
      resampled running data (see 4th listed output).

ver. 1.4:
    - Added class variables to hold processed data (`aggregate_outputs`
      and `resample_outputs`). Also added corresponding accessor methods.
    - Renamed aggregating and resampling routines and removed their return
      statements. They instead set the aforementioned class variables with
      their output.
    - Created function `load_processed_data()` to find and read the most recent
      database file, create a DatasetPrep obj and run all processing routines.
      Wrapped the processing routines in function `get_processed_data()`.
    - Can run preparedatasets from the terminal or import in a file and run
      `load_processed_data()`

ver 1.5:
    - Implemented argparse
    - Rewrote routines for loading, aggregating, and combining tables.
"""

__version__ = '1.5'

import argparse
import re
import pandas as pd
import healthdatabase as hd

from pathlib import Path
from utils import (extract_export_date,
                   get_unit_from_string)


# --- HELPER FUNCTIONS --- #
def write_to_csv(dataframe, filename, verbose):
    dataframe.to_csv(filename)
    if verbose:
        print('Wrote full DataFrame to {n}'.format(n=filename))


def find_substr_in_list(txt, listobj, verbose):
    """ Returns string in listobj if txt matches all or part of the string.

    Args:
        txt (str): Substring to find a match.
        listobj (list): List of strings.
        verbose (bool): Print output.

    Returns:
        None.
    """
    pattern = re.compile(fr".*{txt}.*")
    matching = list(filter(pattern.match, listobj))

    if verbose:
        msg = "Found {0} matches for '{1}' inside list. Matches: {2}"
        print(msg.format(len(matching), txt, matching))

    return matching


def get_daily_agg_method(list_of_cols):
    """ Return aggregation method as a dictionary depending on the column name,
        given a list of column names.
        The appearance of keywords like "Total" and "Avg" within the column
        name indicates 'sum' and 'mean' aggregation methods respectively.
    """
    agg = {}

    for c in list_of_cols:
        col = c.lower()

        if 'total' in col:
            agg[c] = 'sum'
        elif 'avg' in col or 'average' in col:
            agg[c] = 'mean'
        elif 'maximum' in col:
            agg[c] = 'max'
        elif 'minimum' in col:
            agg[c] = 'min'
        elif 'duration' in col:
            # Previous elif will catch 'Avg Duration'
            agg[c] = 'sum'
        elif 'startdate' in col:
            agg[c] = 'first'
        elif 'enddate' in col:
            agg[c] = 'last'
        elif 'menstrual cycle start' in col.replace(' ', ''):
            agg[c] = 'max'
        elif 'elevation' in col:
            agg[c] = 'sum'
        elif 'weather' in col:
            agg[c] = 'mean'
        elif 'stepcount' in col.replace(' ', ''):
            agg[c] = 'sum'
        elif col == 'Date':
            pass
        else:
            # VO2Max, BodyMass, Menstrual Flow (num), Indoor Workout
            # RestingHeartRate, HeartRateVariabilitySDNN, BloodPressure,
            agg[c] = 'mean'

    return agg


def get_weekly_agg_method(list_of_cols):
    """ Return aggregation method as a dictionary depending on the column name,
        given a list of column names.
    """
    agg = {}

    # Special cases
    workout_cases = ['Duration', 'Total Distance', 'Total Energy Burned']
    record_cases = ['Resting Heart Rate', 'VO2 Max', 'Body Mass',
                    'Heart Rate Variability SDNN', 'Blood Pressure',
                    'Blood Pressure', 'Respiratory Rate']
    special_cases = {i: ['sum', 'mean', 'min', 'max'] for i in workout_cases}
    special_cases.update({j: ['mean', 'std'] for j in record_cases})
    for s in special_cases.keys():
        pattern = re.compile(fr".*{s}.*")
        matches = list(filter(pattern.match, list_of_cols))
        for m in matches:
            agg[m] = special_cases[s]

    # Update columns to parse
    remaining_cols = list_of_cols.copy()
    for k in agg.keys():
        remaining_cols.remove(k)

    for c in remaining_cols:
        col = c.lower().replace(' ', '')

        if 'elevation' in col:
            agg[c] = ['mean', 'min', 'max']
        elif 'pace' in col:
            agg[c] = ['mean', 'min', 'max']
        elif 'menstrualcyclestart' in col:
            agg[c] = 'max'
        else:
            agg[c] = 'mean'

    return agg


def get_monthly_agg_method(list_of_cols):
    """ Return aggregation method as a dictionary depending on the column name,
        given a list of column names.
    """
    agg = {}

    for c in list_of_cols:
        col = c.lower().replace(' ', '')

        if 'totalduration' in col or 'totaldistance' in col or 'totalenergy' in col:
            agg[c] = ['sum', 'mean', 'std']
        elif 'speed' in col:
            agg[c] = 'mean'
        elif 'date' in col:
            pass
        else:
            agg[c] = ['mean', 'std']

    return agg


def extract_unit_from_column(dataframe, column_name, unitcolumn):
    """ Helper function for format_record_table and format_workout_table.
    """
    dfiltered = dataframe[(dataframe[unitcolumn] != 'None') & (dataframe[unitcolumn] is not None)]
    distinct_units = dfiltered[unitcolumn].unique()

    if len(distinct_units) != 1:
        raise ValueError(f"{column_name} has {len(distinct_units)} units: {distinct_units}")

    unit = distinct_units[0]
    return unit


def rename_from_camelcase(current_colname, flag_count=0):
    """ Helper function for format_workout_table.
    """
    noprefix = current_colname.removeprefix("HK")
    pattern = r"(\w)([A-Z])"

    if "VO2Max" in current_colname:
        pattern = r"(\w\d)([A-Z])"

    newcolname = re.sub(pattern, r"\1 \2", noprefix, count=flag_count)
    return newcolname


def get_col_dtype(column_name):
    """
    """
    col = column_name.lower().replace(' ', '')
    unit = get_unit_from_string(column_name)
    special_case = {'indoorworkout': 'float64',
                    'menstrualcyclestart': 'int64',
                    'workoutevent': bool,
                    'workoutroute': bool,
                    'wasuserentered': float}

    time_units = ['hr', 'min', 's', 'sec', 'ms', 'ns']  # float64
    distance_metric = ['m', 'km', 'cm', 'mm']  # float64
    distance_imperial = ['mi', 'miles', 'ft', 'feet']  # float 64
    distance_units = distance_metric + distance_imperial
    other_float_units = ['degF', 'degC', '%', 'lb', 'mmHg', 'Cal', 'kcal', 'num']
    int_units = ['count']  # int64

    float_types = time_units + distance_units + other_float_units
    bool_rate_type = unit.find('/') != -1
    bool_unit_float = bool_rate_type or unit in float_types or 'avg' in col
    bool_unit_int = unit in int_units

    if bool_unit_float:
        return 'float64'
    elif bool_unit_int:
        return 'int64'
    elif 'date' in col:
        return 'datetime64[ns]'
    else:
        for k, v in special_case.items():
            if k in col:
                return v
        return str  # Set as string type if all cases fail


def set_dataframe_dtypes(dataframe):
    """ Returns DataFrame with columns casted as data types determined
    by get_col_dtype() method.
    """
    search_columns = list(dataframe.columns)
    if 'startDate' in search_columns:
        search_columns.remove('startDate')
    if 'endDate' in search_columns:
        search_columns.remove('endDate')
    dtypes = {i: get_col_dtype(i) for i in search_columns}
    return dataframe.astype(dtypes)


class DatasetPrep(object):

    def __init__(self, database_path, workout_tables, record_tables,
                 verbose=True, testing=False):

        self.verbose = verbose
        self.testing = testing

        self.WORKOUT_TABLES = workout_tables
        self.RECORD_TABLES = record_tables

        if database_path[0] == '/':
            # File path is an absolute path (as string)
            self.DB_FILE = database_path
        else:
            # File path is relative
            self.DB_FILE = str(Path(Path.cwd(), database_path))

        if self.verbose:
            print(f'Reading from {self.DB_FILE}')

        self.DB_EXPORT_DATE = extract_export_date(database_path)

        # Formatting
        self.DATE_FORMAT = "%Y-%m-%d %H:%M:%S %z"

        # Containers
        self.daily_aggregates = {}
        self.weekly_aggregates = {}
        self.monthly_aggregates = {}
        self.resampled_tables = {}

    # --- ACCESSOR METHODS ---- #
    def get_export_date(self):
        return self.DB_EXPORT_DATE

    def get_aggregates_dict(self, freq):
        f = freq.lower()

        if f.startswith('d'):
            return self.daily_aggregates
        elif f.startswith('w'):
            return self.weekly_aggregates
        elif f.startswith('m'):
            return self.monthly_aggregates
        else:
            raise ValueError("Allowed inputs for freq parameter: ['d', 'daily', \
                             'w', 'weekly', 'm', 'monthly'].")
    # --- END ACCESSORS --- #

    # --- FORMATTING FUNCTIONS --- #
    def format_menstrual_flow(self, dataframe):
        """
        """
        # Remove prefix from value column
        dataframe['value'] = dataframe['value'].apply(lambda x: x.split("Flow")[-1])

        # New numerical 'value' column
        value_map = {'None': 0, 'Light': 1, 'Medium': 2, 'Heavy': 3}
        dataframe['Menstrual Flow (num)'] = dataframe['value'].map(value_map)

        # Rename columns
        dataframe.rename(columns={'value': 'Menstrual Flow',
                                  'HKMenstrualCycleStart': rename_from_camelcase('HKMenstrualCycleStart')},
                         inplace=True)

        # Set column data types
        dataframe = set_dataframe_dtypes(dataframe)

        return dataframe

    def format_record_table(self, tablename, dataframe):
        if tablename == "MenstrualFlow":
            df = self.format_menstrual_flow(dataframe)
        else:
            df = dataframe.copy()

            # -- Get distinct values in 'unit' column -- #
            metric_unit = extract_unit_from_column(df, tablename, 'unit')

            # -- Rename value column to "{table_name} ({unit})" -- #
            formatted_name = rename_from_camelcase(tablename, 3)
            df.rename(columns={'value': f'{formatted_name} ({metric_unit})'}, inplace=True)
            df.drop('unit', axis=1, inplace=True)

            # -- Set column data type -- #
            df = set_dataframe_dtypes(df)

        return df

    def format_workout_table(self, tablename, dataframe):
        """
        """
        # Format numeric columns
        numeric_cols = ['duration', 'totalDistance', 'totalEnergyBurned']
        for numcol in numeric_cols:
            if numcol in dataframe.columns:
                colunit = extract_unit_from_column(dataframe, tablename, numcol + 'Unit')
                # Change numeric col names from camel case to regular
                # capitalized case
                new_col_prefix = rename_from_camelcase(numcol).title()
                new_col_name = f"{new_col_prefix} ({colunit})"
                dataframe.rename(columns={numcol: new_col_name},
                                 inplace=True)
                # Drop redundant unit column
                dataframe.drop(numcol + "Unit", axis=1, inplace=True)

        # Format MetadataEntry columns
        hk_cols = [col for col in dataframe.columns if col.startswith("HK")]
        hk_bool_types = ['WorkoutEvent', 'WorkoutRoute']
        hk_str_to_num = ['HKAverageSpeed', 'HKMaximumSpeed',
                         'HKElevationDescended',
                         'HKElevationAscended',
                         'HKAverageMETs',
                         'HKWeatherTemperature',
                         'HKWeatherHumidity']

        # Cast bool columns
        for hcol in hk_bool_types:
            if hcol in dataframe.columns:
                dataframe[hcol] = dataframe[hcol].fillna(0)

        # For HK columns not in hk_str_to_num, rename columns
        for hcol in list(set(hk_cols) - set(hk_str_to_num)):
            if hcol in dataframe.columns:
                dataframe.rename(columns={hcol: rename_from_camelcase(hcol)}, inplace=True)

        # Separate numeric value and unit for columns hk_str_to_num
        for col in hk_str_to_num:
            if col in dataframe.columns:
                col_rename = rename_from_camelcase(col, 1)
                unit_col = col + 'Unit'
                dataframe[[col, unit_col]] = dataframe[col].str.split(' ', n=1, expand=True)

                # Set data types
                dataframe[unit_col] = dataframe[unit_col].astype(str)

                # If there is only one distinct unit, add to column name and
                # drop unit column
                distinct_units = dataframe[dataframe[unit_col] != 'None'][unit_col].unique()
                if len(distinct_units) == 1:
                    dataframe.rename(columns={col: f"{col_rename} ({distinct_units[0]})"},
                                     inplace=True)
                    dataframe.drop(unit_col, axis=1, inplace=True)
                elif len(distinct_units) > 1 and 'm' in distinct_units:
                    map_to_meter = {'cm': 10**-2, 'mm': 10**-3}
                    # Filter out where unit isn't None or 'm'
                    idx = dataframe[(dataframe[unit_col] != 'm') & (dataframe[unit_col] != 'None')].index
                    # Rename numeric column to include unit
                    new_col_name = f"{col_rename} (m)"
                    dataframe.rename(columns={col: new_col_name}, inplace=True)
                    # Set column data type
                    dataframe[new_col_name] = dataframe[new_col_name].astype(get_col_dtype(new_col_name))
                    # Convert to meters
                    dataframe.loc[idx, new_col_name] = dataframe.loc[idx].apply(lambda x: x[new_col_name] * map_to_meter[x[unit_col]],
                                                                                axis=1)
                    # Drop unit column
                    dataframe.drop(unit_col, axis=1, inplace=True)
                else:  # Keep unit col and numeric col as is
                    pass

        # Set column data types
        dataframe = set_dataframe_dtypes(dataframe)

        return dataframe

    # --- EXTRACT & LOAD FUNCTIONS ---#
    def extract_to_dataframe(self, table_name):
        """ Returns the table in the database contained as a DataFrame,
        keeping only the relevant columns.
        """
        date_col_map = {'startDate': self.DATE_FORMAT}

        # Create sqlite3 connection and get the given table as is
        with hd.HealthDatabase(self.DB_FILE) as db:
            conn = db.get_connection()

            if table_name in self.RECORD_TABLES:
                read_cols = ['[index]', 'value', 'unit', 'startDate']
                if table_name == "MenstrualFlow":
                    read_cols.remove('unit')
                    read_cols.append('HKMenstrualCycleStart')
                cols_to_get = ", ".join(read_cols)
            elif table_name in self.WORKOUT_TABLES:
                cols_to_get = "*"
                date_col_map.update({'endDate': self.DATE_FORMAT})
            else:
                raise ValueError(f"extract_to_dataframe: Have not yet implemented support for {table_name}")

            # Query database
            query = f"SELECT {cols_to_get} FROM {table_name}"
            df = pd.read_sql_query(query, conn,
                                   index_col='index',
                                   parse_dates=date_col_map)

            # Drop unnecessary columns for type = 'Workout'
            if table_name in self.WORKOUT_TABLES:
                cols_to_drop = ['workoutActivityType', 'device', 'HKTimeZone',
                                'sourceVersion', 'creationDate']
                df.drop(columns=cols_to_drop, inplace=True)

        return df

    def load_table(self, table_name):
        """ Returns a DataFrame of the formatted table from the database given
        its table name.
        """
        # Extract table as DataFrame
        df = self.extract_to_dataframe(table_name)

        # Format tables
        if table_name in self.RECORD_TABLES:
            table = self.format_record_table(table_name, df)
        elif table_name in self.WORKOUT_TABLES:
            table = self.format_workout_table(table_name, df)
        else:
            raise ValueError(f"No support for loading {table_name}.")

        return table

    # --- AGGREGATING FUNCTIONS --- #
    def add_to_aggregate(self, aggregated_table):
        """ Adds the following columns to aggregated_table:
            1. 'Date': Date formatted 'YYYY-mm-dd'
            2. 'Avg Pace (unit)': Pace computed as total duration divided
                by total distance.
        Helper function for aggregate_daily().
        """
        cols = aggregated_table.columns

        # Add a Date column from startDate
        aggregated_table['Date'] = aggregated_table['startDate'].dt.date

        # If there exists a duration and distance column add avg pace column
        durations_filter = find_substr_in_list('Duration', cols, verbose=self.testing)
        distances_filter = find_substr_in_list('Total Distance', cols, verbose=self.testing)

        if durations_filter and distances_filter:
            duration_col = durations_filter[0]
            distance_col = distances_filter[0]

            duration_unit = get_unit_from_string(duration_col)
            distance_unit = get_unit_from_string(distance_col)
            pace_unit = f'{duration_unit}/{distance_unit}'

            pace_col_name = f'Avg Pace ({pace_unit})'
            aggregated_table[pace_col_name] = aggregated_table[duration_col] / aggregated_table[distance_col]

        new_columns = list(aggregated_table.columns)
        new_columns.remove('Date')

        # Set column data types
        resultant = set_dataframe_dtypes(aggregated_table)

        return resultant[['Date'] + new_columns]

    def rename_by_agg(self, dataframe, aggregation_map):
        new_column_names = {}

        for col in dataframe.columns:
            if type(col) == str:
                if aggregation_map[col] == 'sum' and 'total' not in col.lower():
                    new_col_name = 'Total ' + col
                elif aggregation_map[col] == 'mean' and 'avg' not in col.lower():
                    if 'Average' in col:
                        new_col_name = col.replace('Average', 'Avg')
                    else:
                        new_col_name = 'Avg ' + col
                elif aggregation_map[col] == 'max' and 'maximum' not in col.lower():
                    if 'Maximum' in col:
                        new_col_name = col.replace('Maximum', 'Max')
                    elif 'menstrualcyclestart' not in col.lower().replace(' ', ''):
                        new_col_name = 'Max ' + col
                    else:
                        new_col_name = col
                elif aggregation_map[col] == 'min' and 'minimum' not in col.lower():
                    if 'Maximum' in col:
                        new_col_name = col.replace('Minimum', 'Min')
                    else:
                        new_col_name = 'Min ' + col
                else:
                    new_col_name = col

                new_column_names[col] = new_col_name

        return dataframe.rename(columns=new_column_names)

    def aggregate_daily(self, tablename, date_column):
        """ Given the table name and the name of column of dates to group by,
        returns a daily aggregate of the table as a DataFrame.
        """
        data = self.load_table(tablename)

        # Drop certain columns for certain tables
        if tablename in self.WORKOUT_TABLES:
            cols_to_drop = ['sourceName', 'Was User Entered',
                            'WorkoutEvent', 'WorkoutRoute']
        elif tablename == 'MenstrualFlow':
            cols_to_drop = ['Menstrual Flow']
        else:
            cols_to_drop = []

        for drop_col in cols_to_drop:
            if drop_col in data.columns:
                data.drop(columns=drop_col, inplace=True)

        # Load aggregation methods for each column
        column_agg_methods = get_daily_agg_method(list(data.columns))

        # Aggregate by date_column
        aggregated_data = data.groupby(data[date_column].dt.date,
                                       as_index=False).agg(column_agg_methods)

        # Rename columns to prefix 'Avg' or 'Total' according to aggregation
        # method
        aggregated_data = self.rename_by_agg(aggregated_data, column_agg_methods)

        # Add new columns
        resultant = self.add_to_aggregate(aggregated_table=aggregated_data)

        # Store
        self.daily_aggregates[tablename] = resultant

        return resultant

    def aggregate_weekly(self, table_name):
        """ Returns the DataFrame aggregated by week, on its date_column.
        """
        date_column = 'Date'
        if table_name in self.daily_aggregates.keys():
            daily = self.daily_aggregates[table_name]
        else:
            daily = self.aggregate_daily(table_name, 'startDate')

        # Drop columns
        if table_name in self.WORKOUT_TABLES:
            cols_to_drop = ['startDate', 'endDate']

            # Find and drop indoor workout column, if found
            pattern = re.compile(".*Indoor Workout.*")
            matches = list(filter(pattern.match, daily.columns))
            if len(matches) == 1:
                cols_to_drop.append(matches[0])
        elif table_name in self.RECORD_TABLES:
            cols_to_drop = 'startDate'

        daily.drop(columns=cols_to_drop, inplace=True)

        # Load aggregation methods
        agg_methods = get_weekly_agg_method(list(daily.columns))

        # Aggregate
        grouper = pd.Grouper(key=date_column, freq='W-MON',
                             closed='left', label='left')
        weekly_aggregated = daily.groupby(grouper).agg(agg_methods)

        # Drop redundant date column
        weekly_aggregated.drop(columns='Date', inplace=True)

        # Rename columns according to agg method
        weekly_aggregated = self.rename_by_agg(weekly_aggregated, agg_methods)

        # Store
        self.weekly_aggregates[table_name] = weekly_aggregated

        return weekly_aggregated

    def aggregate_monthly(self, table_name):
        date_column = 'Date'

        if table_name in self.daily_aggregates.keys():
            daily = self.daily_aggregates[table_name]
        else:
            daily = self.aggregate_daily(table_name, 'startDate')

        # Load aggregation methods
        agg_methods = get_monthly_agg_method(list(daily.columns))

        # Aggregate
        grouper = pd.Grouper(key=date_column, freq='MS')
        monthly_aggregated = daily.groupby(grouper).agg(agg_methods)

        return monthly_aggregated

    def aggregate_table(self, tablename, freq, return_table=True):
        """ Aggregate table according to 'freq'. If return_table is
        True, will return the aggregated table as a DataFrame.

        Args:
            tablename (str): Name of the table.
            freq (str): Determines the frequency of aggregation. Takes in
                        'daily' or 'd', 'weekly' or 'w', and 'monthly' or 'm'.
        Kwargs:
            return_table (bool): Default True. Returns the aggregated table
                                 as the output.
        """
        if freq.startswith('d'):
            agg = self.aggregate_daily(tablename, 'startDate')
            # Store
            self.daily_aggregates[tablename] = agg
        elif freq.startswith('w'):
            agg = self.aggregate_weekly(tablename)
            self.weekly_aggregates[tablename] = agg
        elif freq.startswith('m'):
            agg = self.aggregate_monthly(tablename)
            self.monthly_aggregates[tablename] = agg
        else:
            raise ValueError("Accepts 'daily' or 'd', 'weekly' or 'w', 'monthly' or 'm'.")

        if return_table:
            return agg

    # -- COMBINE AGGREGATES -- #
    def prep_to_join(self, frame):
        """ Prepare given DataFrame to join with other DataFrames. Helper
        function for join_aggregates.
        """
        # Turn to MultiIndex
        if frame.columns.nlevels == 1:
            frame.columns = pd.MultiIndex.from_product([frame.columns, ['']])
        # Set 'Date' column as index
        if frame.index.name != 'Date':
            frame.set_index('Date', inplace=True)
        # Drop startDate
        if 'startDate' in frame.columns:
            frame.drop(columns=['startDate'], inplace=True, level=0)

        return frame

    def join_aggregates(self, freq, table_list):
        """
        Args:
            freq (str): Accepts 'daily' or 'd', 'weekly' or 'w', and
                        'monthly' or 'm'. Designates the type of
                        aggregation.
            table_list (list): List of names of tables whose aggregates are to
                               be joined.
        Returns:
            A DataFrame containing aggregates of all the table names
            passed into RECORD_TABLES.
        """
        f = freq.lower()

        if f.startswith('d'):
            container = self.daily_aggregates
        elif f.startswith('w'):
            container = self.weekly_aggregates
        elif f.startswith('m'):
            container = self.monthly_aggregates
        else:
            raise ValueError("Accepts 'daily' or 'd', 'weekly' or 'w', \
                             'monthly' or 'm'.")

        for t in table_list:
            if t not in container.keys():
                self.aggregate_table(t, f[0], False)

        # Queue to join all record table aggregates
        queue = table_list.copy()
        combined = container[queue[0]].copy()
        combined = self.prep_to_join(combined)
        queue.pop(0)
        while queue:
            df_right = self.prep_to_join(container[queue[0]].copy())
            combined = combined.join(df_right, how='outer')
            queue.pop(0)

        return combined

    def combine_health_aggs(self, freq):
        return self.join_aggregates(freq, self.RECORD_TABLES)

    def combine_workout_aggs(self, freq):
        return self.join_aggregates(freq, self.WORKOUT_TABLES)

    def combine_aggregates(self, freq, workouts, records):
        """
        Args:
            freq (str):
            workouts (list, or str): Accepts either a list of workout table
                names or 'all' to indicate everything in WORKOUT_TABLES class
                variable.
            records (list, or str): Accepts either a list of record table
                names or 'all' to indicate everything in RECORD_TABLES class
                variable.

        Returns:
            A DataFrame combining all the aggregates of tables listed within
            workouts and records parameters.
        """
        if records == 'all':
            health_agg = self.combine_health_aggs(freq)
        else:
            health_agg = self.join_aggregates(freq, records)

        if workouts == 'all':
            workout_agg = self.combine_workout_aggs(freq)
        else:
            workout_agg = self.join_aggregates(freq, workouts)

        combined = workout_agg.join(health_agg, how='outer')

        return combined

    def get_resampled_workout(self, workout_name):
        """
        """
        if workout_name not in self.daily_aggregates.keys():
            daily = self.daily_aggregates(workout_name, 'startDate')
        else:
            daily = self.daily_aggregates[workout_name]

        # Set index as the 'Date' column
        resampled = daily.set_index('Date')
        resampled = resampled.resample("D").asfreq()

        # Add 'Calendar Week' column
        resampled['Calendar Week'] = resampled.index.isocalendar().week

        # Store
        self.resampled_tables[workout_name] = resampled

        return resampled


if __name__ == '__main__':

    write_csv = True

    # Default tables
    workout_tables = ['Running']
    record_tables = ['MenstrualFlow', 'RestingHeartRate', 'VO2Max', 'BodyMass',
                     'HeartRateVariabilitySDNN', 'HeartRate', 'StepCount',
                     'RespiratoryRate', 'BloodPressureDiastolic',
                     'BloodPressureSystolic'
                     ]

    parser = argparse.ArgumentParser(description=""
                                     )
    parser.add_argument('-o', '--open-db',
                        type=str, nargs='?', required=True,
                        help='The path to health database file \
                             `*_applehealth.db`')
    parser.add_argument('-w', '--workouts',
                        default=workout_tables,
                        type=str, nargs='+', required=False)
    parser.add_argument('-r', '--records',
                        default=record_tables,
                        type=str, nargs='+', required=False)

    args = vars(parser.parse_args())

    dbpath = args['open_db']

    data = DatasetPrep(dbpath, workout_tables=args['workouts'],
                       record_tables=args['records'],
                       verbose=True, testing=True)
    file_date = data.get_export_date()
    file_path = 'data/'

    # Do not include 'HeartRate' in aggregates.
    records_to_aggregate = args['records'].copy()
    if 'HeartRate' in args['records']:
        records_to_aggregate.remove('HeartRate')

    # Get combined aggregates and write to csv
    combined_daily = data.combine_aggregates('d', workouts=['Running'],
                                             records=records_to_aggregate)
    combined_weekly = data.combine_aggregates('w', workouts=['Running'],
                                              records=records_to_aggregate)
    combined_monthly = data.combine_aggregates('m', workouts=['Running'],
                                               records=records_to_aggregate)

    # Daily resampled runs
    resampled_runs = data.get_resampled_workout('Running')

    if write_to_csv:
        file_prefix = f"{file_path}{file_date}_"
        write_to_csv(combined_daily, f"{file_prefix}dailyAggregate.csv", verbose=True)
        write_to_csv(combined_weekly, f"{file_prefix}weeklyAggregate.csv", verbose=True)
        write_to_csv(combined_monthly, f"{file_prefix}monthlyAggregate.csv", verbose=True)
        write_to_csv(resampled_runs, f"{file_prefix}running_resampledDaily.csv", verbose=True)
