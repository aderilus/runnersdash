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
import logging

import healthdatabase as hd

from itertools import islice
from datetime import datetime
from sqlalchemy import create_engine, func

CURRENT_TIME = datetime.now().strftime("%Y%m%d_%H%M%S")
CREATE_SUBTABLES_FOR = ['Record', 'Workout']
PREFIX_TO_STRIP = dict(zip(CREATE_SUBTABLES_FOR, [['HKQuantityTypeIdentifier', 'HKDataType', 'HKCategoryTypeIdentifier'],
                                                  ['HKWorkoutActivityType']]))
TYPE_COL = dict(zip(CREATE_SUBTABLES_FOR, ['type', 'workoutActivityType']))

VERBOSE = True


def func_timer(func):
    def function_wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        run_time = end - start

        # Print and log output
        msg = "Elapsed time was {:.5f} seconds".format(run_time)
        logging.info(msg)
        if VERBOSE:
            print(msg, flush=True)
    return function_wrapper


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
        self.tosql_time_per_elem = {}
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

        # Log configs
        log_path = os.path.join(os.getcwd(), 'logs/')
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        log_suffix = 'db_' + self.datestring + '_run' + CURRENT_TIME + '.log'
        self.log_file_name = os.path.join(log_path, log_suffix)
        logging.basicConfig(filename=self.log_file_name, encoding='utf-8', level=logging.INFO)

        # Log associated output file
        logging.info("export.xml export date: {}".format(self.exportdate))

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
        # Update node count for Workout node child
        self.num_nodes_by_elem[workoutchild.tag] += 1

    @func_timer
    def extract_workout_elems(self, workout_tag="Workout"):
        """ Extracts all elements with tag = 'Workout' from the tree.
        For each Workout type (indicated by attribute 'workoutActivityType'),
        creates a table of the 'Workout' elements of the same type.
        Also creates two other tables: 'WorkoutEvent' and 'WorkoutRoute'.
        """
        # initialize node count for tables 'WorkoutEvent' and 'WorkoutRoute'
        self.num_nodes_by_elem['WorkoutEvent'] = 0
        self.num_nodes_by_elem['WorkoutRoute'] = 0

        for i, node in enumerate(self.root.findall(f'./{workout_tag}'), start=1):

            for p in PREFIX_TO_STRIP[workout_tag]:
                tblname = node.attrib[TYPE_COL[workout_tag]].removeprefix(p)
            if tblname not in self.all_tables.keys():
                self.all_tables[tblname] = pd.DataFrame()
                self.num_nodes_by_elem[tblname] = 0

            self.all_tables[tblname] = pd.concat([self.all_tables[tblname],
                                                  pd.DataFrame([node.attrib])], ignore_index=True)
            idx = len(self.all_tables[tblname]) - 1
            self.num_nodes_by_elem[tblname] += 1

            workout_route_queue = []

            for child in self.get_subtree(node):

                if child.tag == workout_tag:
                    pass
                elif child.tag == "MetadataEntry":
                    if self.check_if_workout_route(child):
                        workout_route_queue.append(child)
                    else:
                        self.all_tables[tblname].loc[idx, child.attrib['key']] = child.attrib['value']
                elif child.tag == "FileReference":
                    workout_route_queue.append(child)
                elif child.tag in ["WorkoutEvent", "WorkoutRoute"]:
                    self.all_tables[tblname].loc[idx, child.tag] = True
                    self.add_workout_property(child, tblname, idx)

                    if child.tag == "WorkoutRoute":
                        # get_subtree has traversed through the children of
                        # this current WorkoutRoute node.
                        while workout_route_queue:
                            route_child = workout_route_queue[0]

                            if route_child.tag == "FileReference":
                                colname = 'FilePath'
                                value_key = 'path'
                            else:  # tag is 'MetadataEntry'
                                colname = route_child.attrib['key']
                                value_key = 'value'

                            # Update WorkoutRoute node with child data
                            route_idx = len(self.all_tables[child.tag]) - 1
                            route_val = route_child.attrib[value_key]
                            self.all_tables[child.tag].loc[route_idx, colname] = route_val

                            # Update workout_route_queue
                            workout_route_queue.pop(0)
                else:
                    errmsg = "Have not implemented support for child node of {0} with tag '{1}'. \
                            Add the tag {0} to 'exclude' parameter of AppleHealthExtraction constructor."
                    raise ValueError(errmsg.format("Workout", child.tag))

    @func_timer
    def extract_record_elements(self, record_tag="Record"):
        """
        """
        for i, node in enumerate(self.root.findall(f"./{record_tag}")):
            for p in PREFIX_TO_STRIP[record_tag]:
                tblname = node.attrib[TYPE_COL[record_tag]].removeprefix(p)
            if tblname not in self.all_tables.keys():
                self.all_tables[tblname] = pd.DataFrame()
                self.num_nodes_by_elem[tblname] = 0

            self.num_nodes_by_elem[tblname] += 1  # Update node count

        return

    @func_timer
    def extract_childless_elem_to_table(self, tag, rootnode=None, table_name=""):
        """ Extracts attributes of (childless) Elements with tag = 'tag' to a
        table in all_tables[tag].
        """
        if not rootnode:
            rootnode = self.root

        if not table_name:
            table_name = tag

        if table_name not in self.all_tables.keys():
            self.all_tables[table_name] = pd.DataFrame()

        for i, node in enumerate(rootnode.findall(f"./{tag}"), start=1):

            current_node = pd.DataFrame([node.attrib])
            temp_ref = self.all_tables[table_name]
            self.all_tables[table_name] = pd.concat([temp_ref, current_node],
                                                    ignore_index=True)

        # Update node count
        self.num_nodes_by_elem[table_name] = i

    @func_timer
    def extract_tag_from_tree(self, tag):
        """ Extract all (top-level) nodes with tag 'tag' from the tree.
        Creates a DataFrame and stores it in all_tables dictionary with
        key = 'tag'.
        """

        if tag not in self.get_top_level_tags():
            raise ValueError(f"{tag} is not a top-level node.")

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
                    #     self.all_tables[bpm_node.tag].loc[bpm_idx,
                    #                               f"{child.tag} index"] = idx
                    pass
                elif child.tag == tag:
                    pass
                else:
                    errmsg = "Have not implemented support for child node of {0} with tag '{1}'. \
                            Add the tag {0} to 'exclude' parameter of AppleHealthExtraction constructor."
                    raise ValueError(errmsg.format(tag, child.tag))

        self.num_nodes_by_elem[tag] = i

    @func_timer
    def dataframe_to_sql(self, df, table_name, ifexists='fail'):
        """ Feeds entries from DataFrame to a new or existing table
        in a database with name '{table_name}'.

        Args:
            df (pd.DataFrame): DataFrame to feed into SQL table.
            table_name (str): Name of the table to be created.
        """
        if self.verbose:
            print("Writing to database {0}......".format(table_name), end=' ', flush=True)

        with self.engine.begin() as conn:
            df.to_sql(table_name, con=conn, if_exists=ifexists)

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
            msg = "Extracting {0}......".format(elem)
            logging.info(msg)
            if self.verbose:
                print(msg, end=' ', flush=True)

            if elem == "Workout":
                self.extract_workout_elems()
            elif elem == "Record":
                pass
            elif elem == "Correlation":
                pass
            elif elem == "Audiogram":
                pass
            else:
                self.extract_childless_elem_to_table(elem)

        # for tname, table in self.all_tables.items():
        #     self.dataframe_to_sql(table, tname, ifexists='replace')

        # Timer stats
        self.program_end_time = time.time()
        self.total_elapsed_time = self.program_end_time - self.program_start_time

        # Log results
        self.log_results()

    def log_results(self):
        """ Reports extraction results in a log file and in the terminal
        output such as:
            - Total time elapsed (s) extracting a specific tag
            - Number of entries inside a table
            - File name of resulting database.
        """
        time_elapsed_msg = "Total time elapsed: {0} seconds\n".format(self.total_elapsed_time)
        num_tables_msg = "There are {0} tables inside {1}".format(len(self.all_tables.keys()), self.db_name)

        # Log
        logging.info(time_elapsed_msg)
        logging.info(num_tables_msg)

        # Print
        if self.verbose:
            print('\n' + time_elapsed_msg)
            print(num_tables_msg)

        for tag, count in self.num_nodes_by_elem.items():
            num_entries_msg = "There are {0} entries for table {1}".format(count, tag)
            logging.info(num_entries_msg)

            if self.verbose:
                print(num_entries_msg, flush=True)


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
