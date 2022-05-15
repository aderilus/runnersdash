from pathlib import Path
import sys
import argparse

# Default tables to prepare
workout_tables = ['Running']
record_tables = ['MenstrualFlow', 'RestingHeartRate', 'VO2Max', 'BodyMass',
                 'HeartRateVariabilitySDNN', 'StepCount',
                 'RespiratoryRate', 'BloodPressureDiastolic',
                 'BloodPressureSystolic'
                 ]

# Append parent and grandparent directory
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))
sys.path.append(str(parent_dir.parent))

# -- extractapplehealth argparse -- #
eah_open_file_args = dict(type=str, nargs='?', required=False,
                          help='the/path/to/export.xml.')
eah_append_kwargs = dict(type=bool, required=False, default=False,
                         action=argparse.BooleanOptionalAction,
                         help="Toggle whether to append new data to the latest db file.")
eah_append_ver_kwargs = dict(type=bool, required=False, default=False,
                             action=argparse.BooleanOptionalAction,
                             help="Toggle whether to append script version number to database file name.")

# Argument parser
eah_parser = argparse.ArgumentParser(description='Extracts data from exported Apple Health file `export.xml` and stores it in a database inside a \
                                                folder named `data/`. If path to `export.xml` is not passed in, will search for an export.xml \
                                                in a folder `apple_health_export/` within the current working directory.',
                                     )

eah_parser.add_argument('-o', '--open-export', **eah_open_file_args)
eah_parser.add_argument('-a', '--append', **eah_append_kwargs)
eah_parser.add_argument('-v', '--version', **eah_append_ver_kwargs)

# -- extractapplehealth object instance settings -- #
eah_tables_to_exclude = ['Correlation', 'Audiogram']


# -- preparedatasets argparse -- #
pd_open_db_kwargs = dict(type=str, nargs='?', required=True,
                         help='The path to health database file \
                              `*_applehealth.db`')

pd_workout_kwargs = dict(default=workout_tables,
                         type=str, nargs='+', required=False)
pd_record_kwargs = dict(default=record_tables,
                        type=str, nargs='+', required=False)

pd_parser = argparse.ArgumentParser(description=""
                                    )

pd_parser.add_argument('-o', '--open-db', **pd_open_db_kwargs)
pd_parser.add_argument('-w', '--workouts', **pd_workout_kwargs)
pd_parser.add_argument('-r', '--records', **pd_record_kwargs)
