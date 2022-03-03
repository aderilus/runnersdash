""" healthdatabase.py: Custom context manager for creating and
                       accessing databases with SQLite3.
"""

__version__ = '1.0'

import apsw
import numpy as np


class HealthDatabase(object):

    def __init__(self, file_name, verbose=True):
        self.verbose = verbose

        # SQL connection
        self.db_file = file_name
        self.conn = None
        self.cursor = None

    def __enter__(self):

        # Create SQL connection
        self.conn = apsw.Connection(self.db_file)
        self.cursor = self.conn.cursor()

        return self

    def __exit__(self, exception_type, exception_val, traceback):
        # Close connection
        try:
            self.cursor.close()
            self.conn.close()
        except AttributeError:
            print("Not closeable.")
            return True

    def get_cursor(self):
        return self.cursor

    def get_connection(self):
        return self.conn

    def create_table(self, table_name, col_names):
        """ Creates a table in the database.

        Args:
            tablename (str): Name for the table.
            colnames (list): List of column names for the table.
        """
        # Create table
        query = "CREATE TABLE {tablename}({cols})".format(tablename=table_name, cols=col_names)

        self.cursor.execute(query)

    def create_tables_from_column(self, table_name, col_name, prefixes=[]):
        """ Creates tables derived from an existing table based on grouping
            similar values of a given column of the source table.

        Input:
            table_name (str): Name of source table.
            col_name (str): Column name to base grouping on

        Optional:
            remove_prefix (list): List of prefixes to strip the table values of
            Example: The values under column 'workoutActivityType' include
                     'HKWorkoutActivityTypeBarre' and
                     'HKWorkoutActivityTypeRunning'. If we are creating
                     sub-tables based on this column and if
                     remove_prefix = 'HKWorkoutActivityType', the newly
                     created tables will be named 'Barre' and 'Running' instead.

        """
        created_tables = []

        get_distinct_vals = "SELECT DISTINCT {x} FROM {tablename}".format(x=col_name,
                                                                          tablename=table_name)

        get_distinct_res = self.cursor.execute(get_distinct_vals).fetchall()

        subtable_names = np.array(get_distinct_res).flatten()

        for i in subtable_names:

            # Remove prefixes from identifier
            new_table_tag = i
            if len(prefixes) > 0:
                for p in prefixes:
                    new_table_tag = i.removeprefix(p)
                    if new_table_tag != i:
                        break

            create_query = "CREATE TABLE {new_table} AS SELECT * FROM {source_table} WHERE {col} = '{col_val}'".format(new_table=new_table_tag, source_table=table_name, col=col_name, col_val=i)

            self.cursor.execute(create_query)

            # Append table name to list
            created_tables.append(new_table_tag)

        return created_tables

    def populate_table(self, table_name, entries, placeholder_vals):
        """
        Args:
            table_name (str):
            entries (list, or list-like):
            placeholder_vals (str):

        """
        insert_query = "INSERT into {tablename} values({vals})".format(tablename=table_name, vals=placeholder_vals)

        self.cursor.executemany(insert_query, entries)

    def get_table_count(self, table_name):
        """ Get the number of rows of a table.
        """
        query = "SELECT COUNT(*) FROM {tb}".format(tb=table_name)

        self.cursor.execute(query)

        count = self.cursor.fetchone()

        return count[0]
