""" extractapplehealth.py: Extracts Apple Health data from
                           `export.xml` exported from the Health app,
                           into a database.

Output(s):
    1. A database (.db) file under subdirectory `data/` containing
       all health data organized into tables, grouped by their
       identifier. The file name will include the date corresponding
       to the given export date in the specific `export.xml` file
       it was extracted from.
    2. A list (.csv) of the tables in the .db file, along with the
       correspondinng number of entries and elapsed time. This is
       stored in the `reports/` subdirectory.

Note: Last tested on Mar. 2022 Apple Health data.
"""

__version__ = '1.2'

import sys
import os
import csv
import time
import numpy as np
import xml.etree.ElementTree as ET

import healthdatabase as hd

from itertools import islice
from datetime import datetime

CREATE_SUBTABLES_FOR = ['Record', 'Workout']
PREFIX_TO_STRIP = dict(zip(CREATE_SUBTABLES_FOR, [['HKQuantityTypeIdentifier', 'HKDataType', 'HKCategoryTypeIdentifier'],
                                                  ['HKWorkoutActivityType']]))
TYPE_COL = dict(zip(CREATE_SUBTABLES_FOR, ['type', 'workoutActivityType']))

ELEMENTS_TO_EXCLUDE = ['HeartRateVariabilityMetadataList', 'HealthData', 'MetadataEntry']
VERBOSE = True


class AppleHealthExtraction(object):

    def __init__(self, input_path, verbose=VERBOSE, exclude=ELEMENTS_TO_EXCLUDE):

        self.verbose = verbose
        self.exclude = exclude
        self.num_nodes_by_elem = {}
        self.time_per_elem = {}
        self.tablelist = []
        self.program_start_time = time.time()
        self.program_end_time = 0
        self.total_elapsed_time = 0

        self.export_path = os.path.abspath(input_path)

        if self.verbose:
            print("\nReading from: " + self.export_path)

        # Open and parse file
        with open(self.export_path, 'r') as f:
            self.data = ET.parse(f)

        # Get root of ElementTree object
        self.root = self.data.getroot()

        # Get export date value
        self.exportdate = self.root.find('ExportDate').attrib['value']
        self.exportdatetime = datetime.strptime(self.exportdate, "%Y-%m-%d %H:%M:%S %z")
        self.datestring = self.exportdatetime.strftime("%Y%m%d")

        # Database file name
        dbpath = os.path.join(os.getcwd(), "data/")
        if not os.path.exists(dbpath):
            os.makedirs(dbpath)
        self.db_name = os.path.join(dbpath, self.datestring + '_applehealth.db')

    def get_unique_tags(self):
        """ Helper function for extract_data() and get_toplevel_tags().
        Returns a list of the tags of nodes to extract.
        """
        # Get tags of all nodes
        self.listoftags = [child.tag for child in self.root.iter()]
        self.uniquetags = set(self.listoftags)  # Set of unique tags
        # Remove certain data types from extraction list
        self.uniquetags = list(self.uniquetags - set(ELEMENTS_TO_EXCLUDE))

        return self.uniquetags

    def get_toplevel_tags(self):
        """ Get tags associated with nodes that are direct children of 
        the ElementTree root.
        """
        unique = self.get_unique_tags()
        top_level_nodes = []

        for i in unique: 
            if self.root.find(f'./{i}') is not None:
                top_level_nodes.append(i)
        
        return top_level_nodes

    def extract_to_table(self, tag):
        """ Helper function for extract_data().

        Forms a table out of the attributes of nodes with tag = 'tag'
        within the ElementTree object.

        Example tags found in raw Apple Health export:
            ['Record', 'Workout', 'Me', 'ActivitySummary', 'WorkoutRoute']

        The resulting table is stored under a database .db file, the name of
        which is specified by `self.db_name`.

        Note: If tag is 'Record' or 'Workout' (see global variable
        `CREATE_SUBTABLES_FOR`), this function will create tables based on
        values of a certain column (`TYPE_COL`) of the parent table.

            Example: Under table 'Workout', there is a column labeled
                     'workoutActivityType' with an example value of
                     'HKWorkoutActivityTypeRunning'. The table 'Running'
                     will then be created from rows in 'Record' with
                     'workoutActivityType' = 'HKWorkoutActivityTypeRunning'.
        """
        # Start Timer
        start_time = time.time()

        # Extract column names
        try:
            columns = list(self.root.find(tag).attrib.keys())
        except AttributeError:
            for item in islice(self.root.iter(tag), 0, 1):
                columns = list(item.attrib.keys())

        placeholder_cols = ",".join(columns)
        placeholder_rows = ", ".join([":{0}".format(key) for key in columns])

        # List of nodes' attributes where child.tag = tag
        element_nodes = [child.attrib for child in self.root.iter(tag)]

        # Open database connection
        with hd.HealthDatabase(self.db_name) as db:
            # Create table
            db.create_table(table_name=tag, col_names=placeholder_cols)

            self.tablelist.append(tag)
            if self.verbose:
                print("Extracting {name}......".format(name=tag), end=' ', flush=True)

            # Feed entries into created table
            db.populate_table(table_name=tag, entries=element_nodes, placeholder_vals=placeholder_rows)

            # Get number of entries for this element/tag
            self.num_nodes_by_elem[tag] = db.get_table_count(tag)

            # If element is of type ('tag') 'Record' or 'Workout',
            # create subtables derived from that original table.
            if tag in CREATE_SUBTABLES_FOR:
                new_tables = db.create_tables_from_column(table_name=tag,
                                                          col_name=TYPE_COL[tag],
                                                          prefixes=PREFIX_TO_STRIP[tag])

                # Append newly created tables to table list
                self.tablelist += new_tables

                for tb in new_tables:
                    self.num_nodes_by_elem[tb] = db.get_table_count(table_name=tb)
                    self.time_per_elem[tb] = -9999.99

        # End Timer
        end_time = time.time()
        self.time_per_elem[tag] = end_time - start_time

        if self.verbose:
            print("Elapsed time was %.5g seconds" % self.time_per_elem[tag], flush=True)

    def extract_data(self):
        """ Extracts to various tables information from nodes of the
        ElementTree with matching tags specified by `get_unique_tags` function.

        The resulting tables are stored under a database .db file, the name of
        which is specified by the class variable `self.db_name`.
        """
        # Get list of elements
        elements_to_extract = self.get_unique_tags()

        for elem in elements_to_extract:
            self.extract_to_table(elem)

        # Timer stats
        self.program_end_time = time.time()
        self.total_elapsed_time = self.program_end_time - self.program_start_time

    def print_results(self):
        """ Reports extraction results such as:
            - Total time elapsed (s) extracting a specific tag
            - Number of entries inside a table
            - File name of resulting database.

        Writes report to a CSV file under subdirectory 'reports/'.
        """
        print("\nTotal time elapsed: {ttime} seconds\n".format(ttime=self.total_elapsed_time))
        print("There are {n} tables inside {database}".format(n=len(self.tablelist), database=self.db_name))

        for tag, count in self.num_nodes_by_elem.items():
            print("There are {m} entries for table {tablename}".format(m=count, tablename=tag), flush=True)

        # Write to file
        reportpath = os.path.join(os.getcwd(), "reports/")
        if not os.path.exists(reportpath):
            os.makedirs(reportpath)
        report_name = os.path.join(reportpath, self.datestring + '_report.csv')
        with open(report_name, 'w') as report:
            print("\nWriting to file {name}...... ".format(name=report_name), flush=True)
            writer = csv.writer(report, delimiter=",")
            writer.writerow(['Table name', 'Num. entries', 'Elapsed time (s)'])
            writer.writerows([[t, self.num_nodes_by_elem[t], self.time_per_elem[t]] for t in self.tablelist])


if __name__ == '__main__':

    if len(sys.argv) not in [1, 2]:
        print("USAGE: python extractapplehealth.py /path/to/export.xml[OPTIONAL] \n \
            If secondary argument isn't passed in, searches for export.xml in 'apple_health_export' sub-directory of current working directory.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) == 1:
        xml_path = os.path.join(os.getcwd(), "apple_health_export", "export.xml")
    else:
        xml_path = sys.argv[1]

    tree = AppleHealthExtraction(xml_path)
    tree.extract_data()
    tree.print_results()
