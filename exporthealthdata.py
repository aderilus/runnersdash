""" exporthealthdata.py: Wrapper function for extraction and processing
routines in preparation for visualization through Plotly Dash.

USAGE:
    $ python exporthealthdata.py [-o --open-file </path/to/export.xml>]
                                 [-a --append] [-v --version]
                                 [-w --workouts] [-r --records]

    OPTIONAL ARGUMENTS:

    -o --open-export </path/to/export.xml> : Determine export.xml file to read.

    -a --append (bool) : If passed in, script will find the latest version of a
        db file within the 'data/' subdirectory and append to the database any
        data with 'startDate' >= latest export date of the .db file.
        For use if you have previous exports already stored in a database and
        just need to add new data entries since your last export.
        Default is --no-append.

    -v --version (bool) : If true, the version number of extractapplehealth.py
        is appended to the name of the resulting database .db file.
        Default is --no-version.

    -w --workouts <list of Workout names> : List (space-separated) of table
        names (as it appears) in the database file of type Workout to process.

        Default: Running

        Example Workout tables:
            - Running                           - Other
            - Barre                             - Skiing
            - FunctionalStrengthTraining        - Walking

    -r --records <list of Record names> : List (space-separated) of table names
        of type Record to process.

        Default: MenstrualFlow RestingHeartRate VO2Max BodyMass
                 HeartRateVariabilitySDNN StepCount
                 RespiratoryRate BloodPressureDiastolic
                 BloodPressureSystolic

        Example Record tables:
            - HeartRateVariabilitySDNN
            - VO2Max
            - StepCount


COMPONENTS:

1) [extractapplehealth.py] Extracts and stores (as a database) Apple Health
XML data.

    Output(s):
        1. A database (.db) file under subdirectory `data/` containing
        all health data organized into tables, grouped by their
        identifier.

        Naming scheme: `YYYYmmdd_applehealth.db`

        if --no-append: The file name will include the date corresponding
        to the given export date in the specific `export.xml` file
        it was extracted from, and if passed in the, version number of
        extractapplehealth.py

        if --append: The file name is the latest available db file prior to
        current export.

        2. A log file in the logs/ subdirectory, with name formatted as
            "db_{1}_run{2}_{3}.log",
            where:
                {1} is the export date of the Apple Health export as "YYYYmmdd"
                {2} is the script run date as "YYYYmmdd"
                {3} is the script run date (time) as "HHMMSS".

2) [preparedatasets.py] Collects certain health and fitness metrics from the
database of Health data (output of `extractapplehealth.py`) and runs data
processing routines, the results of which are in the form of a set of CSV files
output by the script:

    Output(s):
        1. "{date}_dailyAggregate.csv" - aggregated daily
        2. "{date}_weeklyAggregate.csv" - aggregated weekly
        3. "{date}_monthlyAggregate.csv" - aggregated monthly
        4. "{date}_Running_resampledDaily.csv" - running data resampled daily
        5. "{date}_Running.csv" - entries to table 'Running' as is, no
                                  aggregation or resampling.

        where 'date' is the export date of the corresponding database formatted
        as 'YYYYmmdd'.
"""

import argparse
import os
from etl import setup
from etl import extractapplehealth as eah
from etl import preparedatasets as pds


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='',
                                     )

    # Optional argument(s)
    parser.add_argument('-o', '--open-file', **setup.eah_open_file_args)
    parser.add_argument('-a', '--append', **setup.eah_append_kwargs)
    parser.add_argument('-v', '--version', **setup.eah_append_ver_kwargs)
    parser.add_argument('-w', '--workouts', **setup.pd_workout_kwargs)
    parser.add_argument('-r', '--records', **setup.pd_record_kwargs)

    args = vars(parser.parse_args())

    if args['open_file'] is None:
        xml_path = os.path.join(os.getcwd(), "apple_health_export", "export.xml")
    else:
        xml_path = args['open_file']
        if xml_path[0] == '~':
            xml_path = os.path.join(os.getcwd(), xml_path[1:])

    tree = eah.AppleHealthExtraction(xml_path, append_to_existing_db=args['append'],
                                     exclude=setup.eah_tables_to_exclude,
                                     append_ver=args['version'])
    tree.extract_data()

    # Prepare dataset
    db_path = tree.db_name  # Database file path

    data = pds.DatasetPrep(db_path, workout_tables=args['workouts'],
                           record_tables=args['records'],
                           verbose=True, testing=False)

    # Do not include 'HeartRate' in aggregates.
    records_to_agg = args['records'].copy()
    if 'HeartRate' in args['records']:
        records_to_agg.remove('HeartRate')

    # Get combined aggregates and write to csv
    combined_daily = data.combine_aggregates('d', workout_tables=setup.workout_tables,
                                             record_tables=records_to_agg,
                                             write_to_file=True,
                                             )
    combined_weekly = data.combine_aggregates('w', workout_tables=setup.workout_tables,
                                              record_tables=records_to_agg,
                                              write_to_file=True,
                                              )
    combined_monthly = data.combine_aggregates('m', workout_tables=setup.workout_tables,
                                               record_tables=records_to_agg,
                                               write_to_file=True,
                                               )

    # Daily resampled runs
    resampled_runs = data.get_resampled_workout('Running', write_to_file=True)

    # All runs
    all_runs = data.load_table('Running', write_to_file=True)
