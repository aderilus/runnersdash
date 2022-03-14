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

__version__ = '2.0'

import sys
import os
import csv
import time
import pandas as pd
import xml.etree.ElementTree as ET

import healthdatabase as hd

from itertools import islice
from datetime import datetime
from sqlalchemy import create_engine

CREATE_SUBTABLES_FOR = ['Record', 'Workout']
PREFIX_TO_STRIP = dict(zip(CREATE_SUBTABLES_FOR, [['HKQuantityTypeIdentifier', 'HKDataType', 'HKCategoryTypeIdentifier'],
                                                  ['HKWorkoutActivityType']]))
TYPE_COL = dict(zip(CREATE_SUBTABLES_FOR, ['type', 'workoutActivityType']))

VERBOSE = True


class AppleHealthExtraction(object):

    def __init__(self, input_path, verbose=VERBOSE, exclude=[]):

        # --- DEPRECATED? --- #
        self.tablelist = []
        # ---

        self.verbose = verbose
        self.exclude = exclude
        self.num_nodes_by_elem = {}
        self.elements_to_extract = []
        self.all_tables = {}
        self.time_per_elem = {}
        self.program_start_time = time.time()
        self.program_end_time = 0
        self.total_elapsed_time = 0
        self.export_path = os.path.abspath(input_path)

        # Contains the DataFrames created in extract_tag_from_tree
        self.all_tables = {}

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
        self.db_name = os.path.join(dbpath, self.datestring + '_applehealth_ver2.db')

        # SQLAlchemy engine
        self.engine = create_engine(f'sqlite:////{self.db_name}')

    def get_unique_tags(self):
        """ Helper function for extract_data() and get_toplevel_tags().
        Returns a list of the tags of nodes to extract.
        """
        # Get tags of all nodes
        self.listoftags = [child.tag for child in self.root.iter()]
        self.uniquetags = set(self.listoftags)  # Set of unique tags
        # Remove certain data types from extraction list
        self.uniquetags = list(self.uniquetags - set(self.exclude))

        return self.uniquetags

    def get_top_level_tags(self):
        """ Get tags associated with nodes that are direct children of
        the ElementTree root.
        """
        unique = self.get_unique_tags()
        top_level_nodes = [i for i in unique if self.root.find(f'./{i}') is not None]

        return top_level_nodes

    def get_subtree(self, node):
        """ Depth-first tree traversal.
        Helper function for extract_tag_from_tree().
        """
        for subelem in node.findall('./'):
            yield from self.get_subtree(subelem)
        yield node

    def check_if_workout_route(self, metadata_node):
        """  Returns whether or not input MetadataEntry node is a child of
        a WorkoutRoute node. Helper function for extract_tag_from_tree().
        Assumes that node passed in has tag == "MetadataEntry".
        """
        if metadata_node.tag != "MetadataEntry":
            raise ValueError(f"Input Element must have tag = 'MetadataEntry'")

        if "HKMetadataKey" in metadata_node.attrib['key']:
            return True
        return False

    def add_workout_property(self, workoutchild, workouttype, workoutidx):
        """ Adds data from a node 'workoutchild' to a DataFrame in all_tables.
        This function adds two columns: 'workoutType' and 'workoutIndex'
        mapping to values 'workouttype' and 'workoutidx' respectively. Does not
        return anything.
        """
        df = pd.DataFrame([workoutchild.attrib])
        df.loc[0, ['workoutType', 'workoutIndex']] = [workouttype, workoutidx]

        if workoutchild.tag not in self.all_tables.keys():
            self.all_tables[workoutchild.tag] = df
        else:
            tableref = self.all_tables[workoutchild.tag]
            self.all_tables[workoutchild.tag] = pd.concat([tableref, df],
                                                          ignore_index=True)

    def extract_tag_from_tree(self, tag):
        """ Extract all (top-level) nodes with tag 'tag' from the tree.
        Creates a DataFrame and stores it in all_tables dictionary with
        key = 'tag'.
        """

        if tag not in self.get_top_level_tags():
            raise ValueError(f"{tag} is not a top-level node.")

        if self.verbose:
            print("Extracting {0}......".format(tag), end=' ', flush=True)

        # Start Timer
        start_time = time.time()

        # Iterates through top level nodes
        for i, node in enumerate(self.root.findall(f"./{tag}"), start=1):

            node_table = pd.DataFrame([node.attrib])

            if tag in ['Record', 'Workout']:
                for p in PREFIX_TO_STRIP[tag]:
                    tblname = node.attrib[TYPE_COL[tag]].removeprefix(p)
            else:
                tblname = tag

            if tblname not in self.all_tables.keys():
                self.all_tables[tblname] = pd.DataFrame()

            # Add current node attributes to DataFrame
            temp_table = self.all_tables[tblname]
            self.all_tables[tblname] = pd.concat([temp_table, node_table],
                                                 ignore_index=True)
            # Get index of current node within the DataFrame
            idx = len(self.all_tables[tblname]) - 1

            if tag == "Workout":
                workout_route_queue = []
            elif tag == "Record":
                bpm_queue = []

            if i % 1000 == 0:  # DEBUG
                print(i, tblname, self.all_tables[tblname].info(memory_usage="deep"))

            # Iterate through the children of current node
            for child in self.get_subtree(node):

                if child.tag == "MetadataEntry":
                    if tag == "Workout" and self.check_if_workout_route(child):
                        workout_route_queue.append(child)
                    else:  # Its parent is a Workout, Record, Correlation node
                        self.all_tables[tblname].loc[idx, child.attrib['key']] = child.attrib['value']
                elif child.tag == "FileReference":
                    workout_route_queue.append(child)
                elif child.tag in ["WorkoutEvent", "WorkoutRoute"]:
                    self.all_tables[tblname].loc[idx, child.tag] = True
                    self.add_workout_property(child, tblname, idx)

                    if child.tag == "WorkoutRoute":
                        # workout_route_queue will hold all children of current
                        # WorkoutRoute node
                        while len(workout_route_queue) > 0:
                            route_child = workout_route_queue[0]

                            if route_child.tag == "FileReference":
                                colname = 'Filepath'
                                value_key = 'path'
                            else:  # WorkoutRoute child node is type MetadataEntry
                                colname = route_child.attrib['key']
                                value_key = 'value'

                            # Update WorkoutRoute node with child data
                            route_idx = len(self.all_tables[child.tag]) - 1
                            route_val = route_child.attrib[value_key]
                            self.all_tables[child.tag].loc[route_idx, colname] = route_val

                            workout_route_queue.pop(0)  # Pop current child off queue

                elif child.tag == "InstantaneousBeatsPerMinute":
                    # bpm_queue.append(child)
                    pass
                elif child.tag == "HeartRateVariabilityMetadataList":
                    # # Add InstantaneousBPM in bpm_queue to the DataFrame
                    # while len(bpm_queue) > 0:
                    #     bpm_node = bpm_queue[0]
                    #     bpm_idx = len(self.all_tables[bpm_node.tag]) - 1
                    #     self.all_tables[bpm_node.tag].loc[bpm_idx, f"{child.tag} index"] = idx
                    pass
                elif child.tag == tag:
                    pass
                else:
                    errmsg = "Have not implemented support for child node of {0} with tag '{1}'. \
                            Add the tag {0} to 'exclude' parameter of AppleHealthExtract constructor."
                    raise ValueError(errmsg.format(tag, child.tag))



        # End timer
        end_time = time.time()
        self.time_per_elem[tag] = end_time - start_time

        self.num_nodes_by_elem[tag] = i

        if self.verbose:
            print("Elapsed extraction time was %.5g seconds" % self.time_per_elem[tag], flush=True)

    def dataframe_to_sql(self, df, table_name, ifexists='fail'):
        """ Feeds entries from DataFrame to a new or existing table
        in a database with name '{table_name}'.

        Args:
            df (pd.DataFrame): DataFrame to feed into SQL table.
            table_name (str): Name of the table to be created.
        """
        if self.verbose:
            print("Writing to database {0}......".format(table_name), end=' ', flush=True)

        # # Start time
        # start_time = time.time()

        with self.engine.begin() as conn:
            df.to_sql(table_name, con=conn, if_exists=ifexists)
            # # Get number of entries for this element/tag
            # self.num_nodes_by_elem[table_name] = db.get_table_count(table_name)

        # # End timer
        # end_time = time.time()
        # self.tosql_time_per_elem[table_name] = end_time - start_time

        # if self.verbose:
        #     print("Time to write to SQL table was %.5g seconds" % self.tosql_time_per_elem[table_name], flush=True)

    def extract_to_table(self, tag):
        """ DEPRECATED. Helper function for extract_data().

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
        ElementTree.

        The resulting tables are stored under a database .db file, the name of
        which is specified by the class variable `self.db_name`.
        """
        # Get list of elements
        self.elements_to_extract = list(set(self.get_top_level_tags()) - set(self.exclude))

        for elem in self.elements_to_extract:
            self.extract_tag_from_tree(elem)

        for tname, table in self.all_tables.items():
            self.dataframe_to_sql(table, tname, ifexists='replace')

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
        print("There are {n} tables inside {database}".format(n=len(self.all_tables.keys()), database=self.db_name))

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
            writer.writerows([[t, self.num_nodes_by_elem[t], self.time_per_elem[t]] for t in self.elements_to_extract])


if __name__ == '__main__':

    if len(sys.argv) not in [1, 2]:
        print("USAGE: python extractapplehealth.py /path/to/export.xml[OPTIONAL] \n \
            If secondary argument isn't passed in, searches for export.xml in 'apple_health_export' sub-directory of current working directory.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) == 1:
        xml_path = os.path.join(os.getcwd(), "apple_health_export", "export.xml")
    else:
        xml_path = sys.argv[1]

    tree = AppleHealthExtraction(xml_path, exclude=['Record', 'Correlation', 'Audiogram'])
    tree.extract_data()
    tree.print_results()
