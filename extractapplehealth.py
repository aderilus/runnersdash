""" extractapplehealth.py: Extracts Apple Health data from
                           `export.xml` exported from the Health app, 
                           into a database.
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

        # SQL database file name
        self.db_name = os.path.join(os.getcwd(), "data/", self.datestring + '_applehealth.db')

    def get_elements(self):

        self.listoftags = [child.tag for child in self.root.iter()]  # Get tags of all nodes
        self.uniquetags = np.unique(np.array(self.listoftags))  # List of unique tags
        # Remove certain data types from extraction list
        self.uniquetags = np.setdiff1d(self.uniquetags, np.array(self.exclude))

        return self.uniquetags

    def extract_data(self):
        """
        """
        # Get list of elements
        elements_to_extract = self.get_elements()

        for elem in elements_to_extract:
            self.extract_to_table(elem)

        # Timer stats
        self.program_end_time = time.time()
        self.total_elapsed_time = self.program_end_time - self.program_start_time

    def extract_to_table(self, tag):
        """
        """
        # Timer
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

            self.tablelist.append(tag)  # Append to table list
            if self.verbose:
                print("Extracting {name}......".format(name=tag), end=' ', flush=True)

            # Feed entries into created table
            db.populate_table(table_name=tag, entries=element_nodes, placeholder_vals=placeholder_rows)

            # Get number of entries for this element/tag
            self.num_nodes_by_elem[tag] = db.get_table_count(tag)

            # If element is of type ('tag') 'Record' or 'Workout'
            if tag in CREATE_SUBTABLES_FOR:
                new_tables = db.create_tables_from_column(table_name=tag,
                                                          col_name=TYPE_COL[tag],
                                                          prefixes=PREFIX_TO_STRIP[tag])

                self.tablelist += new_tables  # Append newly created tables to table list

                for tb in new_tables:
                    self.num_nodes_by_elem[tb] = db.get_table_count(table_name=tb)
                    self.time_per_elem[tb] = -9999.99

        end_time = time.time()
        self.time_per_elem[tag] = end_time - start_time

        if self.verbose:
            print("Elapsed time was %.5g seconds" % self.time_per_elem[tag], flush=True)

    def print_results(self):
        print("\nTotal time elapsed: {ttime}".format(ttime=self.total_elapsed_time))
        print("There are {n} tables inside {database}".format(n=len(self.tablelist), database=self.db_name))

        for tag, count in self.num_nodes_by_elem.items():
            print("There are {m} entries for table {tablename}".format(m=count, tablename=tag), flush=True)

        # Write to file
        report_name = os.path.join(os.getcwd(), "reports", self.datestring + '_report.csv')
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
