""" extractapplehealth.py: Extracts Apple Health data from
                           `export.xml` exported from the Health app,
                           into a database.

Output(s):
    1. A database (.db) file under subdirectory `data/` containing
       all health data organized into tables, grouped by their
       identifier. The file name will include the date corresponding
       to the given export date in the specific `export.xml` file
       it was extracted from, and if passed in the, version number of
       extractapplehealth.py
    2. A log file in the logs/ subdirectory, with name formatted as
        "db_{exportdate}_run{script run date in %Y%m%d}_{%H%M%S}.log"

Things to note:
- Last tested on Mar. 2022 Apple Health data.
- This version does not extract elements with tag = "Correlation" or
tag = "Audiogram".
- This version does not extract 'InstantaneousBeatsPerMinute' elements
properly.
"""

__version__ = '2.2'

import sys
import os
import time
import pandas as pd
import xml.etree.ElementTree as ET
import logging
import sqlalchemy
import sqlite3

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.sql import text

CURRENT_TIME = datetime.now().strftime("%Y%m%d_%H%M%S")
CREATE_SUBTABLES_FOR = ['Record', 'Workout']
PREFIX_TO_STRIP = dict(zip(CREATE_SUBTABLES_FOR, [['HKQuantityTypeIdentifier',
                                                   'HKDataType', 'HKCategoryTypeIdentifier'],
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

    def __init__(self, input_path, append_to_existing_db=False,
                 exclude=[], verbose=VERBOSE, append_ver=False):

        # --- DEPRECATED? --- #
        self.tablelist = []
        # ---

        self.append_to_db = append_to_existing_db
        self.append_ver = append_ver
        self.verbose = verbose
        self.exclude = exclude
        self.num_nodes_by_elem = {}
        self.elements_to_extract = []
        self.all_tables = {}
        self.record_tables = []
        self.table_error_count = {}
        self.extract_time_per_elem = {}
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
        extension = '.db'
        if not os.path.exists(dbpath):
            os.makedirs(dbpath)
        if self.append_ver:
            dbsuffix = '_ver{0}'.format(__version__.replace('.', ''))
        else:
            dbsuffix = ''
        dbprefix = self.datestring + '_applehealth' + dbsuffix
        self.db_name = os.path.join(dbpath, dbprefix + extension)

        if not self.append_to_db:  # If file already exists, rename the new db to be created
            counter = 1
            while os.path.exists(self.db_name):
                count_fix = "_{}".format(counter)
                self.db_name = os.path.join(dbpath, dbprefix + count_fix + extension)
                counter += 1

        # SQLAlchemy engine
        self.engine = create_engine(f'sqlite:////{self.db_name}')

        # Log configs
        self.log_path = os.path.join(os.getcwd(), 'logs/')
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)
        log_suffix = 'db_' + self.datestring + '_run' + CURRENT_TIME + '.log'
        self.log_name = os.path.join(self.log_path, log_suffix)
        logging.basicConfig(filename=self.log_name, encoding='utf-8', level=logging.DEBUG)

        # Log associated output file
        logging.info(f"extractapplehealth.py ver: {__version__}")
        logging.info(f"export.xml export date: {self.exportdate}")
        logging.info(f"Writing to database file: {self.db_name}")

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
    def extract_workout_elements(self, workout_tag="Workout"):
        """ Extracts all elements with tag = 'Workout' from the tree.
        For each Workout type (indicated by attribute 'workoutActivityType'),
        creates a table of the 'Workout' elements of the same type.
        Also creates two other tables: 'WorkoutEvent' and 'WorkoutRoute'.
        """
        # initialize node count for tables 'WorkoutEvent' and 'WorkoutRoute'
        self.num_nodes_by_elem['WorkoutEvent'] = 0
        self.num_nodes_by_elem['WorkoutRoute'] = 0

        for i, node in enumerate(self.root.findall(f'./{workout_tag}'), start=1):

            start = time.time()  # Start timer

            for p in PREFIX_TO_STRIP[workout_tag]:
                tblname = node.attrib[TYPE_COL[workout_tag]].removeprefix(p)

            if tblname not in self.all_tables.keys():
                self.all_tables[tblname] = pd.DataFrame()
                self.num_nodes_by_elem[tblname] = 0  # Node counter
                self.extract_time_per_elem[tblname] = 0  # Node timer

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

                end = time.time()  # End timer
                self.extract_time_per_elem[tblname] += end - start

    @func_timer
    def extract_record_elements(self, record_tag="Record", n=5000):
        """ Extracts all elements with tag = 'Record' from the tree.
        For each Record type (indicated by attribute 'type'), creates a
        table of 'Record' elements of the same type.

        For every nth iteration, appends all existing 'Record' (sub)tables
        to their respective tables in the database.

        Also creates one other tables: 'InstantaneousBeatsPerMinute'.

        Kwargs:
            record_tag (str): The tag associated with 'Record' nodes.
                              Defaults to "Record".
            n (int): The iteration number of the loop through 'Record'
                     nodes. For every nth iteration, existing 'Record'
                     subtables will written to the SQL database file.
                     And their DataFrames will be reset as an empty
                     DataFrames.
        """
        # Queue of every table name to write to db file for every nth
        # iteration of the following loop
        table_queue = []
        # InstantaneousBeatsPerMinute is a known (grand)child of Record
        bpmname = "InstantaneousBeatsPerMinute"
        self.all_tables[bpmname] = pd.DataFrame()
        self.num_nodes_by_elem[bpmname] = 0
        self.record_tables.append(bpmname)

        for i, node in enumerate(self.root.findall(f"./{record_tag}"), start=1):
            start = time.time()  # Start timer
            nodetype = node.attrib[TYPE_COL[record_tag]]

            for p in PREFIX_TO_STRIP[record_tag]:
                nodetype = nodetype.removeprefix(p)

            if nodetype not in table_queue:
                table_queue.append(nodetype)

            # Instantiate table if it doesn't exist
            if nodetype not in self.all_tables.keys():
                self.all_tables[nodetype] = pd.DataFrame()
                self.record_tables.append(nodetype)  # Append to list of tables created under Record nodes
                self.num_nodes_by_elem[nodetype] = 0  # Node counter
                self.extract_time_per_elem[nodetype] = 0  # Node type timer

            self.all_tables[nodetype] = pd.concat([self.all_tables[nodetype],
                                                   pd.DataFrame([node.attrib])],
                                                  ignore_index=True)

            node_idx = len(self.all_tables[nodetype]) - 1
            self.num_nodes_by_elem[nodetype] += 1  # Update node count
            bpm_queue = []

            for child in node.findall('./'):

                if child.tag == "MetadataEntry":
                    self.all_tables[nodetype].loc[node_idx, child.attrib['key']] = child.attrib['value']
                elif child.tag == bpmname:
                    bpm_queue.append(child)
                    print(bpm_queue)
                else:  # child tag = HeartRateVariabilityMetadataList
                    while bpm_queue:
                        # Have to define a separate index because all_tables
                        # gets reset every nth iteration
                        index_val = self.num_nodes_by_elem[nodetype] - 1

                        bpm_table = pd.DataFrame([bpm_queue[0].attrib])
                        bpm_table.loc[0, ["Record table", "Index"]] = [nodetype, index_val]
                        # Add to all_tables table
                        self.all_tables[bpmname] = pd.concat([self.all_tables[bpmname],
                                                              bpm_table],
                                                             ignore_index=True)
                        self.num_nodes_by_elem[bpmname] += 1  # Update node count
                        bpm_queue.pop(0)  # Update queue

                    if bpmname not in table_queue:  # Append to queue
                        table_queue.append(bpmname)

            end = time.time()  # End timer
            self.extract_time_per_elem[nodetype] += end - start

            if i % n == 0:
                # Every nth iteration, write to DataFrame. This is a tremendous
                # help for performance.

                while table_queue:
                    table_name = table_queue[0]
                    # Write to SQL table
                    self.dataframe_to_sql(self.all_tables[table_name], table_name, ifexists='append')
                    # Reset DataFrames in dictionary (remove reference)
                    self.all_tables[table_name] = pd.DataFrame()
                    table_queue.pop(0)  # Reset queue

            if i % 10000 == 0:
                print(i, nodetype)

        while table_queue:  # If exit out of loop and queue is not empty
            tbl = table_queue[0]
            self.dataframe_to_sql(self.all_tables[tbl], tbl, ifexists='append')
            self.all_tables[tbl] = pd.DataFrame()
            table_queue.pop(0)

        # Check that there are no more nodes to be written to database
        for rtable in self.record_tables:
            len_table = len(self.all_tables[rtable])
            if len_table > 0:
                unresolved_tbls_msg = f"{rtable} has {len_table} entries left."
                logging.error(unresolved_tbls_msg)
                if self.verbose:
                    print(unresolved_tbls_msg, end='\n')

    @func_timer
    def extract_childless_elements(self, tag, rootnode=None, table_name=""):
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

    def add_newcols_to_table(self, df, tbl):
        """ Adds new columns from df not found in existing tbl in
        database.
        """

        with self.engine.begin() as conn:
            # Get columns from DB table
            query_cols = "SELECT name from pragma_table_info('{0}')".format(tbl)
            db_cols = conn.execute(text(query_cols)).fetchall()

            old_cols = [i[0] for i in db_cols]
            old_cols.remove('index')

            # New cols to add to table
            diff = set(df.columns.tolist()) - set(old_cols)
            new_cols = list(diff)
            assert len(new_cols) > 0, "{0}".format(new_cols)

            for col in new_cols:
                newcolmsg = "ALTER TABLE {0} ADD COLUMN {1}".format(tbl, col)
                conn.execute(text(newcolmsg))
                logging.info(f"Added new column {col} for table {tbl}")

            # Fetch DB columns again
            check_cols = [j[0] for j in conn.execute(text(query_cols)).fetchall()]
            # assert len(set(new_cols) - set(check_cols)) == 0
            for added_col in new_cols:
                assert added_col in check_cols, f"{added_col} not in table cols"

            df.to_sql(tbl, con=conn, if_exists='append')

    def dataframe_to_sql(self, df, table_name, ifexists='fail'):
        """ Feeds entries from DataFrame to a new or existing table
        in a database with name '{table_name}'.

        Args:
            df (pd.DataFrame): DataFrame to feed into SQL table.
            table_name (str): Name of the table to be created.
        """
        if self.verbose:
            msg = "Writing to database {0} entries for table {1}......"
            print(msg.format(len(df), table_name), end='\n', flush=True)

        if table_name not in self.table_error_count.keys():
            self.table_error_count[table_name] = 0
        if table_name not in self.tosql_time_per_elem.keys():
            self.tosql_time_per_elem[table_name] = 0

        start_time = time.time()
        with self.engine.begin() as conn:
            try:
                df.to_sql(table_name, con=conn, if_exists=ifexists)
            except (sqlalchemy.exc.OperationalError, sqlite3.OperationalError) as e:
                # Log error
                logging.info(f"Encountered error on {table_name}")
                logging.info(str(e))
                self.table_error_count[table_name] += 1
                self.add_newcols_to_table(df, table_name)

        end_time = time.time()
        run_time = end_time - start_time
        self.tosql_time_per_elem[table_name] += run_time

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
                self.extract_workout_elements()
            elif elem == "Record":
                self.extract_record_elements()
            elif elem == "Correlation":
                pass
            elif elem == "Audiogram":
                pass
            else:
                self.extract_childless_elements(elem)

        # Write datasets to db
        write_to_db = list(set(self.all_tables.keys()) - set(self.record_tables))
        if self.append_to_db:
            if_exists_toggle = 'append'
        else:
            if_exists_toggle = 'replace'
        for tablename in write_to_db:
            self.dataframe_to_sql(self.all_tables[tablename], tablename,
                                  ifexists=if_exists_toggle)

        # for n, t in self.all_tables.items():  # Write to CSV
        #     t.to_csv("data/{0}_{1}.csv".format(self.datestring, n))

        # Timer stats
        self.program_end_time = time.time()
        self.total_elapsed_time = self.program_end_time - self.program_start_time

        # Log and check results
        self.log_results()
        self.check_results()

    def check_results(self):
        """ Compares table counts and table names between what is stored
        in the created database and what is stored in memory. Logs
        discrepancies as errors.
        """
        print_error_msgs = []

        tables_query = "SELECT {0} FROM sqlite_master WHERE type = 'table'"
        total_count_query = text(tables_query.format("count(*)"))
        table_names_query = text(tables_query.format("name"))

        per_table_query = "SELECT count(*) FROM {0}"

        with self.engine.begin() as conn:
            db_total_tbl_count = conn.execute(total_count_query).fetchone()[0]
            db_tbl_names = conn.execute(table_names_query).fetchall()
            db_tables = [i[0] for i in db_tbl_names]

            # Compare table counts
            in_memory_tbl_count = len(self.all_tables.keys())
            if not db_total_tbl_count == in_memory_tbl_count:
                total_count_msg = "There are {0} tables inside db file but\
                                   {1} tables in self.all_tables".format(db_total_tbl_count,
                                                                         in_memory_tbl_count)
                logging.debug(total_count_msg)
                print_error_msgs.append(total_count_msg)

            # Compares list of table names
            in_memory_tables = list(self.all_tables.keys())
            list_diff = list(set(db_tables) ^ set(in_memory_tables))
            list_fail_msg = "List of table names self.all_tables.keys() and from db don't match."
            if list_diff:
                logging.debug(list_fail_msg)
                logging.debug("self.all_tables.keys(): {}".format(in_memory_tables))
                logging.debug("Tables inside db: {}".format(db_tables))
                logging.debug("List difference: {}".format(list_diff))

                print_error_msgs.append(list_fail_msg)

            for tb in db_tables:  # Compare lengths of individual tables
                nnodes_count = self.num_nodes_by_elem[tb]
                db_tbl_count = conn.execute(text(per_table_query.format(tb))).fetchone()[0]
                count_fail_msg = "Length of {t} from DB: {c1}, Length from class var: {c2}, sqlite3.OperationalError count: {c3}"

                if not db_tbl_count == nnodes_count:
                    count_msg = count_fail_msg.format(t=tb, c1=db_tbl_count,
                                                      c2=nnodes_count,
                                                      c3=self.table_error_count[tb])
                    logging.debug(count_msg)
                    print_error_msgs.append(count_msg)

        if self.verbose:  # Print found errors
            while print_error_msgs:
                print(print_error_msgs[0], end='\n')
                print_error_msgs.pop(0)
            print("See log {}".format(self.log_name))

    def log_results(self):
        """ Reports extraction results in a log file and in the terminal
        output such as:
            - Total time elapsed (s) extracting a specific tag
            - Number of entries inside a table
            - File name of resulting database.
        """
        # Total number of tables in database
        num_elems_extracted = "There are {0} types of elements extracted".format(len(self.all_tables.keys()))
        logging.info(num_elems_extracted)
        if self.verbose:
            print(num_elems_extracted, end='\n')

        # Get number of instances and total time to write to database file for
        # each Element.
        for tag, count in self.num_nodes_by_elem.items():
            if tag in self.extract_time_per_elem.keys():
                time_to_extract = self.extract_time_per_elem[tag] + self.tosql_time_per_elem[tag]
                time_str = "{:.3f}".format(time_to_extract)
                time_snippet = f"{time_str} seconds to extract and write"
            else:
                time_str = "{:.3f}".format(self.tosql_time_per_elem[tag])
                time_snippet = f"{time_str} seconds to write"

            elem_stats_msg = "Total of {0} {1} entries to table {2}"
            elem_stats = elem_stats_msg.format(time_snippet, count, tag)
            logging.info(elem_stats)

            if self.verbose:
                print(elem_stats, flush=True)

        # Total time elapsed
        elapsed_time = time.strftime('%H:%M:%S', time.gmtime(self.total_elapsed_time))
        time_elapsed_msg = "Total time elapsed: {0} hh:mm:ss\n".format(elapsed_time)
        logging.info(time_elapsed_msg)

        if self.verbose:
            print('\n' + time_elapsed_msg)


if __name__ == '__main__':

    if len(sys.argv) not in [1, 2]:
        print("USAGE: python extractapplehealth.py [OPTIONAL]/path/to/export.xml \n \
            If secondary argument isn't passed in, searches for export.xml in 'apple_health_export' sub-directory of current working directory.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) == 1:
        xml_path = os.path.join(os.getcwd(), "apple_health_export", "export.xml")
    else:
        xml_path = sys.argv[1]

    tree = AppleHealthExtraction(xml_path, append_to_existing_db=False,
                                 exclude=['Correlation', 'Audiogram'],
                                 append_ver=True)
    tree.extract_data()
