"""
preparedatasets.py: Imports and formats SQL tables as DataFrames for
                    visualization and analysis.
                    Outputs, stored in 'data' sub-directory:
                        1. "[date]_dailyaggregate.csv"
                        2. "[date]_weeklyaggregate.csv"
                        3. "[date]_monthlyaggregate.csv"
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
"""

__version__ = '1.4'

import os
import sys
import pandas as pd
import healthdatabase as hd
import math
from utils import (DAYS_OF_WK, 
                   extract_export_date,
                   get_unit_from_string)
from pathlib import Path

TB_OF_INTEREST = ['Running', 'VO2Max', 'BodyMass', 'MenstrualFlow',
                  'RestingHeartRate']


# --- HELPER FUNCTIONS --- #
def write_to_csv(dataframe, filename, verbose):
    dataframe.to_csv(filename)
    if verbose:
        print('Wrote full DataFrame to {n}'.format(n=filename))


def get_run_type(x):
    """
    Args:
        x (float): Duration of run in minutes.

    Returns:
        String indicating the type of run based on duration.
            'Mini': x < 15 min
            'Short': 15 <= x < 30
            'Recovery': 30 <= x < 60
            'Long': x >= 60
    """
    if math.isnan(x) or x <= 0:
        return None

    if x < 30:
        if x < 15:
            return 'Mini'
        return 'Short'
    else:
        if x >= 60:
            return 'Long'
        return 'Recovery'


def find_substr_in_list(txt, listobj, verbose):
    """ Returns string in listobj if txt matches all or part of the string.

    Args:
        txt (str): Substring to find a match.
        listobj (list): List of strings.

    Returns:
        None.
    """
    for i in listobj:
        if txt in i:
            return i

    if verbose:
        msg = "\nCould not find any matches for {elem} in {list}"
        print(msg.format(elem=txt, list=listobj))

    return None


def join_two_tables(df_left, df_right, join_left, join_right):
    """ Merge two tables, taking the union of both tables.

    Args:
        df_left (pd.DataFrame):
        df_right (pd.DataFrame):
        join_left (str):
        join_right (str):

    Returns:
        resultant (pd.DataFrame): Joined resultant table.
    """
    # Format date columns as type datetime
    df_left[join_left] = pd.to_datetime(df_left[join_left], format='%Y-%m-%d')
    df_right[join_right] = pd.to_datetime(df_right[join_right], format='%Y-%m-%d')

    resultant = df_left.merge(df_right, how='outer',
                              left_on=join_left, right_on=join_right)

    # Combine both date columns into one column
    combined_column = join_left + '_prime'
    resultant[combined_column] = resultant[join_left].combine_first(resultant[join_right])
    resultant.drop([join_left, join_right], axis=1, inplace=True)
    resultant.rename({combined_column: join_left}, axis=1, inplace=True)
    resultant[join_left] = pd.to_datetime(resultant[join_left], format='%Y-%m-%d')

    # Sort by new Date column
    resultant.sort_values(join_left, axis=0, inplace=True, ignore_index=True)

    return resultant


def get_aggregation_method(list_of_cols):
    """ Return aggregation method depending on the column title.
        The appearance of keywords like "Total" and "Avg" within the column
        name indicates 'sum' and 'mean' aggregation methods respectively.

        Date columns indicated by "Day", "Week", "Month", etc. within the
        name are skipped.
    """
    agg = {}

    for col in list_of_cols:
        if 'total' in col.lower():
            agg[col] = 'sum'
        elif 'starttime' in col.lower():
            agg[col] = 'first'
        elif 'endtime' in col.lower():
            agg[col] = 'last'
        elif col in ['Date', 'Week', 'Month', 'Year', 'Run Type']:
            pass
        else:  # VO2Max, BodyMass, Menstrual Flow
            agg[col] = 'mean'

    return agg


def group_by_date(dataframe, aggregation_method, datetimecol):
    """ Group rows by common date. Helper function for get_daily_aggregate.

    Args:
        dataframe (pd.DataFrame): DataFrame to group.
        aggregation_method (dict): Dictionary with the given DataFrame columns
                                   as keys, with its aggregation method.
            Example: agg_method = {'duration (min)': 'sum',
                                   'totalDistance (km)': 'sum',
                                   'totalEnergyBurned (Cal)': 'sum',
                                   'startDate': 'first', 'endDate': 'last'}
        datetimecol (str): Name of the column containing datetime values.

    Returns:
        aggregated (pd.DataFrame): Resulting DataFrame grouped by the date.
    """

    aggregated = dataframe.groupby(dataframe[datetimecol].dt.date).agg(aggregation_method).reset_index()

    return aggregated


class DatasetPrep(object):

    def __init__(self, database_path, tables=TB_OF_INTEREST, verbose=True,
                 testing=False):

        self.verbose = verbose
        self.testing = testing

        self.dbPath = str(database_path)
        self.exportDate = extract_export_date(self.dbPath)
        self.tableNames = tables

        self.extracted_data = {}
        self.formatted_data = {}

        # Outputs of processing routines
        self.aggregate_outputs = {}
        self.resample_outputs = {}

        # Use in rename_column_with_unit
        self.colname_prefix = {'Running': ['Total Duration', 'Total Distance',
                                           'Total Energy Burned From Run'],
                               'VO2Max': ['VO2Max'],
                               'BodyMass': ['BodyMass'],
                               'MenstrualFlow': ['MenstrualFlow'],
                               'RestingHeartRate': ['Avg. Resting HR']}

        self.columnmapper = {'Running': dict(zip(['duration', 'totalDistance',
                                                  'totalEnergyBurned'], self.colname_prefix['Running'])),
                             'VO2Max': dict(zip(['value'], self.colname_prefix['VO2Max'])),
                             'BodyMass': dict(zip(['value'], self.colname_prefix['BodyMass'])),
                             'MenstrualFlow': dict(zip(['value'], self.colname_prefix['MenstrualFlow'])),
                             'RestingHeartRate': dict(zip(['value'], self.colname_prefix['RestingHeartRate']))
                             }

        self.daily_colnames = {}

    # --- ACCESSOR METHODS ---- #
    def get_export_date(self):
        return self.exportDate

    def get_original_data(self):
        return self.extracted_data

    def get_formatted_data(self):
        return self.formatted_data

    def get_all_aggregates(self):
        """ Returns aggregated DataFrames within a dictionary keyed by their
            aggregation type ('daily', 'weekly', or 'monthly').
        """
        return self.aggregate_outputs

    def get_all_resamples(self):
        """ Returns resampled DataFrames within a dictionary keyed by the
            database table name.
        """
        return self.resample_outputs
    # --- END ACCESSORS --- #

    # --- EXTRACT & LOAD --- #
    def extract_to_dataframes(self, database_file, tables_to_get):
        """ Given the path to a database and a list of the table names to
            import, outputs a dictionary of the corresponding DataFrames.
            Helper function for load_database().
        """

        dflist = []

        #  Create sqlite3 Connection and read given tables
        with hd.HealthDatabase(database_file) as db:
            conn = db.get_connection()
            cursor = db.get_cursor()

            for tb in tables_to_get:
                query = "SELECT * FROM {table}".format(table=tb)
                dflist.append(pd.read_sql_query(query, conn))

        return dict(zip(tables_to_get, dflist))

    def load_database(self):
        """ Reads and formats database file.
        """

        imported = self.extract_to_dataframes(self.dbPath, self.tableNames)
        formatted = self.format_dataframes(imported)

        self.extracted_data = imported
        self.formatted_data = formatted
    # --- END EXTRACT & LOAD --- #

    # --- FORMAT TABLES --- #
    def rename_column_with_unit(self, dframe, tablename, column_mapper):
        """ Helper function for format_dataframes().
            Concatenates the unit onto each column name in value_cols.

        Examples:
            tablename = 'Running': 'totalDistance' renamed to 'totalDistance (km)'
            tablename = 'VO2Max': 'value' --> 'VO2Max ([unit])'
            tablename = 'BodyMass': 'value' --> 'Weight (lb)'
            tablename = 'RestingHeartRate': 'value' --> 'Avg. Resting HR (bpm)'

        Args:
            dframe (pd.DataFrame): DataFrame with columns to rename.
            tablename (str): Name of the table as appears in the database file.
            column_mapper (dict):

        Returns:
            None. Modifies given DataFrame in place.
        """

        custom_unit = {'Running': False,
                       'VO2Max': False,
                       'BodyMass': False,
                       'MenstrualFlow': 'num',
                       'RestingHeartRate': 'bpm'}

        for value_col, new_col_name in column_mapper[tablename].items():

            if value_col == 'value':
                unit_col = 'unit'
            else:  # CASE: tablename = 'Running'
                unit_col = value_col + 'Unit'

            # Get root and unit of column
            root = new_col_name

            if custom_unit[tablename]:
                get_unit = custom_unit[tablename]
            else:
                get_unit = dframe[unit_col].iloc[0]

            new_name = root + ' (%s)' % get_unit

            # Rename
            dframe.rename(mapper={value_col: new_name}, axis=1, inplace=True)

            # Drop unit cols
            dframe.drop(unit_col, axis=1, inplace=True)

    def format_dataframes(self, df_dict):
        """ Formats the given DataFrames stored inside a dictionary.

        Note: As of Dec. 2021 data, some entries under the 'value' column of
        table 'MenstrualFlow' have a typo: 'HKCategoryValueMensturalFlowNone'
        instead of 'HKCategoryValueMenstrualFlowNone'.

        Args:
            df_dict (dict): Dictionary of DataFrames.

        Returns:
            None. Modifies the DataFrames in place.
        """

        updated = {}
        col_names = {}

        menstrualvaluemap = {'None': 0, 'Light': 1, 'Medium': 2, 'Heavy': 3}

        for table_name, table in df_dict.items():

            updated[table_name] = table.copy()
            newtable = updated[table_name]

            if table_name == "MenstrualFlow":
                # Strip prefix from 'value' column. See Note above.
                newtable['value'] = table['value'].apply(lambda x: x.removeprefix("HKCategoryValueMenstrualFlow").removeprefix("HKCategoryValueMensturalFlow"))

                # Drop rows where 'MenstrualFlow' value is 'Unspecified'
                newtable.drop(newtable.index[newtable['value'] == "Unspecified"], inplace=True)

                # Map string values to numeric values
                newtable['value'] = newtable['value'].map(menstrualvaluemap)

            else:
                # Format these columns as numeric types
                numeric_cols = list(self.columnmapper[table_name].keys())
                newtable[numeric_cols] = newtable[numeric_cols].apply(pd.to_numeric)

            # Format column 'startDate' as datetime.datetime and create a new
            # 'Date' column for each table
            if table_name == "RestingHeartRate":
                newtable['endDate'] = pd.to_datetime(table['endDate'], format='%Y-%m-%d %H:%M:%S %z')
                newtable['Date'] = pd.to_datetime(newtable['endDate'].dt.date)
            else:
                newtable['startDate'] = pd.to_datetime(table['startDate'], format='%Y-%m-%d %H:%M:%S %z')
                newtable['Date'] = pd.to_datetime(newtable['startDate'].dt.date)

            # Drop these shared columns
            cols_to_drop = ['sourceName', 'sourceVersion', 'creationDate']
            if table_name == "Running":
                cols_to_drop.append('workoutActivityType')
            else:
                cols_to_drop.extend(['type', 'startDate', 'endDate'])

            newtable.drop(cols_to_drop, axis=1, inplace=True)

            # Rename 'value' columns, concatenating the unit to the column name
            self.rename_column_with_unit(newtable, table_name, column_mapper=self.columnmapper)

            # Rename 'startDate' and 'endDate' columns for 'Running'
            if table_name == "Running":
                newtable.rename({'startDate': 'runStartTime', 'endDate': 'runEndTime'},
                                axis=1, inplace=True)

            # Store column names
            new_cols = list(newtable.columns)
            new_cols.remove('Date')
            col_names[table_name] = new_cols

        # Update self.daily_colnames
        self.daily_colnames = col_names

        return updated
    # --- END FORMAT --- #

    # --- JOIN METHOD(S) --- #
    def join_all_tables(self, dfdict):
        """ Merge all tables.
        """

        joined = join_two_tables(dfdict[self.tableNames[0]],
                                 dfdict[self.tableNames[1]], 'Date', 'Date')

        for name in self.tableNames[2:]:
            joined = join_two_tables(joined, dfdict[name], 'Date', 'Date')

        return joined
    # --- END JOIN --- #

    def add_more_runstats(self, dataframe):
        """ Adds additional running stats to given dataframe, including
            average pace and run type.
        """

        cols = list(dataframe.columns)

        matches_duration = [find_substr_in_list("Avg. Duration", cols, self.testing),
                            find_substr_in_list("Total Duration", cols, self.testing)]
        matches_distance = [find_substr_in_list("Avg. Distance", cols, self.testing),
                            find_substr_in_list("Total Distance", cols, self.testing)]

        avg_duration_colname = next(item for item in matches_duration if item is not None)
        avg_distance_colname = next(item for item in matches_distance if item is not None)

        duration_unit = get_unit_from_string(avg_duration_colname)
        distance_unit = get_unit_from_string(avg_distance_colname)

        avg_pace_colname = "Avg. Pace ({unit})".format(unit=duration_unit + '/' + distance_unit)
        run_type_colname = "Run Type"

        dataframe[avg_pace_colname] = dataframe[avg_duration_colname] / dataframe[avg_distance_colname]
        dataframe[run_type_colname] = dataframe[avg_duration_colname].map(get_run_type)

    # --- AGGREGATE BY DATE --- #
    def aggregate_daily(self, df_dict, export_date):
        """ Group DataFrame rows by date. Each row will have a distinct date.
            Aggregation method for each column is defined by method
            get_aggregation_method().

        Args:
            db_path (str): File path of Apple Health database (.db) file.
            export_date (str): Date formatted as "YYYYmmdd", used for naming
                               resulting CSV file.

        Returns:
            full_aggregate (pd.DataFrame):
        """

        aggregated = {}

        for name, table in df_dict.items():
            agg_method = get_aggregation_method(self.daily_colnames[name])
            aggregated[name] = group_by_date(table, agg_method, datetimecol='Date')

        if self.testing:
            for key, table in aggregated.items():
                csv_name = "{date}_{name}_daily.csv".format(date=export_date, name=key)
                csv_path = os.path.join(os.getcwd(), "testing", csv_name)
                write_to_csv(table, csv_path, self.verbose)

        full_aggregate = self.join_all_tables(aggregated)

        self.add_more_runstats(full_aggregate)

        # Write to CSV
        csvname = "{date}_dailyaggregate.csv".format(date=export_date)
        csvpath = os.path.join(os.getcwd(), "data/", csvname)
        write_to_csv(full_aggregate, csvpath, self.verbose)

        # Set class variable
        self.aggregate_outputs['daily'] = full_aggregate

    def aggregate_weekly_monthly(self, dailyagg, exportdate):
        """
        Args:
            dailyagg (pd.DataFrame): Dataset grouped by day.
                                    Output of get_daily_aggregate().
            exportdate (str): Date formatted as a "YYYYmmdd" string.

        Returns:
            Tuple of 2 DataFrames, representing weekly and monthly
            aggregates respectively.
        """

        cols_to_drop = ['runStartTime', 'runEndTime']
        weeklyagg = dailyagg.drop(cols_to_drop, axis=1)
        monthlyagg = dailyagg.drop(cols_to_drop, axis=1)

        weeklyagg['Date'] = pd.to_datetime(weeklyagg['Date'], format="%Y-%m-%d")
        weeklyagg['Week'] = weeklyagg['Date'] - pd.to_timedelta(6, unit='d')

        monthlyagg['Date'] = pd.to_datetime(monthlyagg['Date'], format="%Y-%m-%d")
        monthlyagg['Year'] = monthlyagg['Date'].dt.year
        monthlyagg['Month'] = monthlyagg['Date'].dt.month

        cols_to_add = ['Avg. Duration', 'Avg. Distance', 'Avg. Energy Burned From Run']
        matching_cols = []

        for i in range(len(cols_to_add)):
            col = cols_to_add[i]
            matches = [j for j in list(dailyagg.columns) if col.split('Avg. ')[-1] in j]

            if len(matches) != 1:
                msg = 'None or more than 1 match for {cur}: {matchvals}'
                print(msg.format(cur=col, matchvals=matches), sys.stderr)
                sys.exit(1)
            else:
                match = matches[0]
                matching_cols.append(match)
                matching_unit = get_unit_from_string(match)
                cols_to_add[i] = "{root} ({unit})".format(root=col, unit=matching_unit)

                if self.testing:
                    print(cols_to_add[i] + ' is matched with ', match, end='\n')

        newcolmapper = dict(zip(cols_to_add, matching_cols))

        for newcol, currentcol in newcolmapper.items():
            weeklyagg[newcol] = dailyagg[currentcol]
            monthlyagg[newcol] = dailyagg[currentcol]

        weeklyaggmethod = get_aggregation_method(list(weeklyagg.columns))
        monthlyaggmethod = get_aggregation_method(list(monthlyagg.columns))

        if self.testing:
            print("\nWeekly agg method: ", weeklyaggmethod)
            print("\nMonthly agg method: ", monthlyaggmethod, '\n')

        weeklyagg = weeklyagg.groupby(pd.Grouper(key='Week', freq='W-MON')).agg(weeklyaggmethod).reset_index()
        monthlyagg = monthlyagg.groupby(['Year', 'Month']).agg(monthlyaggmethod).reset_index()

        self.add_more_runstats(weeklyagg)
        self.add_more_runstats(monthlyagg)

        # Write to CSV
        csvpath = os.path.join(os.getcwd(), "data/")
        namebase = "{date}_{type}aggregate.csv"
        weeklyname = os.path.join(csvpath, namebase.format(date=exportdate, type="weekly"))
        monthlyname = os.path.join(csvpath, namebase.format(date=exportdate, type="monthly"))
        write_to_csv(weeklyagg, weeklyname, self.verbose)
        write_to_csv(monthlyagg, monthlyname, self.verbose)

        self.aggregate_outputs['weekly'] = weeklyagg
        self.aggregate_outputs['monthly'] = monthlyagg

    def run_all_aggregates(self):
        """ Wrapper for all aggregation routines.
        """
        # Aggregate by day
        self.aggregate_daily(self.formatted_data, self.exportDate)
        daily_aggregate = self.aggregate_outputs['daily']

        # Aggregate by week and month
        self.aggregate_weekly_monthly(daily_aggregate, self.exportDate)

    def resample_table(self, tablename, on='Date', write_to_file=True):
        """ Resample a table by day. Fills missing values with NaN.

        Note for ver. 1.4:
            For now, its main use is to prepare a running heatmap. Only
            implemented for and tested on tablename = 'Running'.

        Args:
            tablename (str): Name of the table to resample.

        Kwargs:
            on (str): The column name containing datetime values.
                      Default is 'Date'.
            write_to_file (bool): Toggle writing resulting resampled data to
                                  CSV in data sub-directory.

        Returns:
            None
        """

        data = self.formatted_data[tablename]
        data[on] = pd.to_datetime(data[on], format="%Y-%m-%d")

        # Group by day to remove extraneous date values
        aggmethod = get_aggregation_method(list(data.columns))
        daily_data = group_by_date(data, aggmethod, datetimecol=on)

        # Resample
        df = daily_data.set_index(on)
        df.index = pd.to_datetime(df.index)
        df = df.resample("D").asfreq()

        # Adds average pace and additional running stats
        if tablename == 'Running':
            self.add_more_runstats(df)

        # Adds Year, Month, Day column
        df['Year'] = df.index.year
        df['Month'] = df.index.month
        df['Day'] = df.index.day

        # Adds 'Day of Week' column
        num_to_day = dict(zip(range(7), DAYS_OF_WK))
        df['Day of Week'] = df.index.dayofweek
        df['Day of Week'] = df['Day of Week'].map(num_to_day)

        # Adds 'Calendar Week' column
        df['Calendar Week'] = df.index.isocalendar().week

        if write_to_file:
            namebase = "{date}_{name}_resampledDaily.csv"
            file_name = namebase.format(date=self.exportDate, name=tablename)
            csvpath = os.path.join(os.getcwd(), "data", file_name)
            write_to_csv(df, csvpath, self.verbose)

        self.resample_outputs[tablename] = df
    # --- END AGGREGATE --- #


# --- RUN PROCESSING ROUTINES --- #
def get_processed_data(database_path, tbls_to_agg, tbls_to_resample,
                       return_outputs=False, verbose=True, write_to_csv=True):
    """ Runs all processing routines on given database file.

    Args:
        database_path (str or PosixPath): Path of database file to read.
        tbls_to_agg (list): List of names of the table(s) to run aggregation
                            routines on.
        tbls_to_resample (list): List of names of the table(s) from database
                                to run resample_table() on.
    Kwargs:
        return_outputs (bool): Toggle whether to return the output
                               DataFrames. Default False.
        verbose (bool): Toggle print functions.
        resample_var (str or list): Name of the table(s) from database to run
                            resampling function get_resampled_data() on.
        write_csv (bool): Toggle to write output DataFrames to CSV. Default
                          is True.

    Returns:
        If return_outputs = True, returns a tuple of the export date formatted
        as a string "YYYYmmdd" and two dictionaries ("YYYYmmdd", dict1, dict2).
        `dict1` holds aggregated DataFrames keyed by their aggregation method
        (['daily', 'weekly', 'monthly']). `dict2` holds resampled DataFrames
        keyed by the name of the resampled table as it appears in the
        {YYYYmmdd}_applehealth.db file.

        Example: get_processed_data(...) --> ({'daily': pd.DataFrame,
                                               'weekly': pd.DataFrame,
                                               'monthly': pd.DataFrame
                                                },
                                              {'Running': pd.DataFrame})
    """

    hdata = DatasetPrep(database_path, tbls_to_agg, verbose, testing=False)
    hdata.load_database()
    hdata.run_all_aggregates()  # Run aggregating routines

    # Run resampling routine
    for i in tbls_to_resample:
        hdata.resample_table(i, on='Date', write_to_file=write_to_csv)

    if return_outputs:
        return (hdata.get_export_date(),
                hdata.get_all_aggregates(),
                hdata.get_all_resamples())


# --- IF RUNNING PREPAREDATASETS FROM ANOTHER PY FILE --- #
def load_processed_data(agg_tables=TB_OF_INTEREST, resample_tables=['Running'],
                        verbose=False):
    """ Gets list of available db files inside 'data/' subdirectory
        and runs all data processing routines.

        Use this if trying to run processing routines from another
        file.

    Kwargs:
        agg_tables (list): List of table names to aggregate by day, week,
                           and month.
        resample_tables (list): List of table names to resample by day.
        verbose (bool): Toggle print functions.

    Returns:
        A tuple of the export date formatted as a string "YYYYmmdd" and two
        dictionaries ("YYYYmmdd", dict1, dict2). `dict1` holds aggregated
        DataFrames keyed by their aggregation method (['daily', 'weekly',
        'monthly']). `dict2` holds resampled DataFrames keyed by the name of
        the resampled table as it appears in the {YYYYmmdd}_applehealth.db
        file.
    """

    db_list = list(sorted(Path('data/').glob('*applehealth.db')))
    most_recent_ver = db_list[-1]

    if verbose:
        print('Available db files:\n')
        for i in db_list:
            print(i)
        print('Reading from... {0}'.format(most_recent_ver))

    return get_processed_data(most_recent_ver, tbls_to_agg=agg_tables,
                              tbls_to_resample=resample_tables,
                              return_outputs=True)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print("USAGE: $ python preparedatasets.py path/to/applehealthdatabase.db",
              file=sys.stderr)
        sys.exit(1)

    dbpath = sys.argv[1]
    get_processed_data(dbpath, tbls_to_agg=TB_OF_INTEREST,
                       tbls_to_resample=['Running'], verbose=True,
                       write_to_csv=True)
