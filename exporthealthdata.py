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
