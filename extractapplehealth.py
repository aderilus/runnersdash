""" extractapplehealth.py: Extracts Apple Health data from
                           `export.xml` exported from the Health app,
                           into a database.

Usage:
    $ python extractapplehealth.py OPTIONAL[-o path/to/export.xml  --append]

    If --append is passed in, script will find the latest version of a db file
    within the 'data/' subdirectory and append to the database any data with
    'startDate' >= latest export date of the db file. Default is --no-append.

Output(s):
    1. A database (.db) file under subdirectory `data/` containing
       all health data organized into tables, grouped by their
       identifier.
       if --no-append: The file name will include the date corresponding
       to the given export date in the specific `export.xml` file
       it was extracted from, and if passed in the, version number of
       extractapplehealth.py
       if --append: The file name is the latest available db file prior to
       current export.
    2. A log file in the logs/ subdirectory, with name formatted as
        "db_{exportdate}_run{script run date in %Y%m%d}_{%H%M%S}.log"

Things to note:
- Last tested on Mar. 2022 Apple Health data.
- This version does not extract elements with tag = "Correlation", "Audiogram",
  or "ClinicalRecord".
- ver 2.5
    - Added functionality to extract nodes starting from a certain date and
      append to latest available database.
"""

__version__ = '2.5'

import argparse
import os
import time
import pandas as pd
import xml.etree.ElementTree as ET
import logging
import sqlalchemy
import sqlite3

from pathlib import Path
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

    def __init__(self, input_path, append_to_existing_db, exclude=[],
                 verbose=VERBOSE, append_ver=False,
                 ):

        self.program_start_time = time.time()  # Start program timer
        self.export_path = Path(input_path)  # export.xml path
        self.append_to_existing_db = append_to_existing_db
        self.append_from = None  # Initialize append from date as None
        self.append_ver = append_ver
        self.verbose = verbose
        self.exclude = exclude

        self.num_nodes_by_elem = {}  # Node counter
        self.elements_to_extract = []  # Tag list of top level Elements to extract
        self.table_error_count = {}  # Error count for table in the database
        # Total time taken to extract info from all nodes of each Element type
        self.extract_time_per_elem = {}
        # Time taken to write to database all nodes of each Element type
        self.tosql_time_per_elem = {}
        self.program_end_time = 0
        self.total_elapsed_time = 0

        if self.verbose:
            print("\nReading from: " + str(self.export_path))

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
        dbpath = Path(Path.cwd(), "data/")
        extension = '.db'

        if self.append_to_existing_db and list(dbpath.glob(f"*{extension}")):
            # If append_from is passed in and there are db files inside
            # the 'data/' subdirectory, get the path of the latest
            # available db file in that folder
            self.db_name = list(sorted(dbpath.glob(f"*{extension}")))[-1]
            self.datestring = str(self.db_name).split('/')[-1][:8]
            write_mode = 'Appending'
        else:
            # In the case if available db files cannot be found
            self.append_to_existing_db = False
            write_mode = 'Writing'

            if not os.path.exists(dbpath):
                os.makedirs(dbpath)
            if self.append_ver:
                dbsuffix = '_ver{0}'.format(__version__)
            else:
                dbsuffix = ''
            dbprefix = self.datestring + '_applehealth' + dbsuffix
            self.db_name = os.path.join(dbpath, dbprefix + extension)

            # If file already exists, rename the new db to be created
            if os.path.exists(self.db_name):
                counter = 1
                while os.path.exists(self.db_name):
                    count_fix = "_{}".format(counter)
                    self.db_name = os.path.join(dbpath, dbprefix + count_fix + extension)
                    counter += 1

        # SQLAlchemy engine
        self.engine = create_engine(f'sqlite:////{self.db_name}')

        # If append to existing db is True, get Export Date of latest db
        if self.append_to_existing_db:
            with self.engine.begin() as conn:
                fetched = conn.execute("SELECT * FROM ExportDate").fetchall()
                exportdatestr = fetched[-1][1]
                self.append_from = datetime.strptime(exportdatestr, "%Y-%m-%d %H:%M:%S %z")

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
        logging.info(f"{write_mode} to database file: {self.db_name}")

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

    def get_nodes_after_datetime(self, date_start, full_node_list):
        """
        Args:
            date_start (datetime): Start date of date range as datetime object.
            full_node_list (list):

        Returns:
            A list of nodes with their startDate attribute >= date_start.
        """
        start_idx = -1
        cur_node = full_node_list[start_idx]
        cur_date = datetime.strptime(cur_node.attrib['startDate'], "%Y-%m-%d %H:%M:%S %z")

        while cur_date >= date_start:
            start_idx -= 1
            cur_node = full_node_list[start_idx]
            cur_date = datetime.strptime(cur_node.attrib['startDate'], "%Y-%m-%d %H:%M:%S %z")

        return full_node_list[start_idx + 1:]

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

    def get_current_table_length(self, table_name):
        with self.engine.begin() as conn:
            query = f"SELECT count(*) FROM {table_name}"
            fetched = conn.execute(query).fetchone()
            length = fetched[0]
        if type(length) == tuple:
            return length[0]
        elif type(length) == int:
            return length
        else:
            raise ValueError(f"length {length} is an unsupported type {type(length)}")

    @func_timer
    def extract_workout_elements(self, start_from="all", workout_tag="Workout",
                                 chunk_size=5000):
        """ Extracts all elements with tag = 'Workout' from the tree.
        For each Workout type (indicated by attribute 'workoutActivityType'),
        creates a table of the 'Workout' elements of the same type.
        Also creates two other tables: 'WorkoutEvent' and 'WorkoutRoute'.

        Kwargs:
            start_from (str or datetime.date): If datetime date is passed
                              in, will only extract nodes where "startDate"
                              attribute >= start_from. If "all", extracts all
                              nodes regardless of "startDate". Default is "all".
            workout_tag (str): The node tag associated with Workout nodes.
                               Default is "Workout".
            chunk_size (int): The iteration number of the loop through 'Workout'
                              nodes. For every nth iteration, existing 'Workout'
                              subtables will written to the SQL database file.
                              And their list within table_queue will be reset
                              to an empty list. Default is 5000.
        """

        # Initialize queue to dataframe_to_sql() function call
        # This dictionary is keyed by the node type tag and
        # holds a list of node.attrib, each of type dict.
        table_queue = {}

        # If self.append_to_existing_db is True, store the existing table
        # lengths keyed by table names.
        existing_table_length = {}

        # Get node list
        node_list = self.root.findall(f'./{workout_tag}')
        if start_from != "all":
            node_list = self.get_nodes_after_datetime(start_from, node_list)

        for i, node in enumerate(node_list, start=1):
            # If i a multiple of chunk_size, write every list in table_queue
            # to a DataFrame and call dataframe_to_sql()
            if i % chunk_size == 0:
                for key, node_list in table_queue.items():
                    df = pd.DataFrame(node_list)
                    self.dataframe_to_sql(df, table_name=key, ifexists='append')
                    del df
                    table_queue[key] = []  # Reset the list

            start = time.time()  # Start timer

            # Get node.attrib['type'] and remove prefix
            for p in PREFIX_TO_STRIP[workout_tag]:
                nodetype = node.attrib[TYPE_COL[workout_tag]].removeprefix(p)

            if nodetype not in table_queue.keys():
                table_queue[nodetype] = []  # Initialize list in queue
                self.num_nodes_by_elem[nodetype] = 0  # Node counter
                self.extract_time_per_elem[nodetype] = 0  # Node extraction timer

            # Append current node.attrib in its list in queue
            table_queue[nodetype].append(node.attrib)
            self.num_nodes_by_elem[nodetype] += 1
            node_index = self.num_nodes_by_elem[nodetype] - 1

            if self.append_to_existing_db:
                if nodetype not in existing_table_length.keys():
                    existing_table_length[nodetype] = self.get_current_table_length(nodetype)
                node_index += existing_table_length[nodetype]

            # Initialize queue for Workout children nodes
            workout_route_queue = []

            for child in self.get_subtree(node):

                if child.tag == workout_tag:
                    # Get subtree will also the node passed in
                    pass
                elif child.tag == "MetadataEntry":
                    if self.check_if_workout_route(child):
                        workout_route_queue.append(child)
                    else:  # It's a direct child of the current Workout node
                        new_item = {child.attrib['key']: child.attrib['value']}
                        table_queue[nodetype][-1].update(new_item)
                elif child.tag == "FileReference":
                    workout_route_queue.append(child)
                elif child.tag in ["WorkoutEvent", "WorkoutRoute"]:
                    # If not found in table_queue yet, initialize a few things
                    if child.tag not in table_queue.keys():
                        table_queue[child.tag] = []
                        self.num_nodes_by_elem[child.tag] = 0
                        self.extract_time_per_elem[child.tag] = 0

                    child_start = time.time()  # Start timer

                    # Add key,val (child.tag, True) to current node attrib
                    table_queue[nodetype][-1].update({child.tag: True})

                    # Update current child attributes with new items
                    new_items = {'workoutType': nodetype,
                                 'workoutIndex': node_index}
                    new_child_attrib = child.attrib | new_items

                    # Update table_queue and node counter
                    table_queue[child.tag].append(new_child_attrib)
                    self.num_nodes_by_elem[child.tag] += 1

                    # Because WorkoutRoute can have child nodes
                    if child.tag == "WorkoutRoute":
                        # get_subtree has (depth-first) traversed through the
                        # children of this current WorkoutRoute node.
                        while workout_route_queue:
                            route_child = workout_route_queue[0]

                            if route_child.tag == "FileReference":
                                colname = 'filePath'
                                value_key = 'path'
                            elif route_child.tag == "MetadataEntry":
                                colname = route_child.attrib['key']
                                value_key = 'value'
                            else:
                                raise ValueError(f"No support implemented for child node tag {route_child.tag} for type {nodetype}.")

                            # Update WorkoutRoute node with its child data
                            route_items = {colname: route_child.attrib[value_key]}
                            table_queue[child.tag][-1].update(route_items)

                            # Update workout_route_queue
                            workout_route_queue.pop(0)

                    self.extract_time_per_elem[child.tag] += time.time() - child_start
                else:
                    errmsg = "Have not implemented support for child node of {0} with tag '{1}'. \
                            Add the tag {0} to 'exclude' parameter of AppleHealthExtraction constructor."
                    raise ValueError(errmsg.format(workout_tag, child.tag))

                end = time.time()  # End timer
                self.extract_time_per_elem[nodetype] += end - start

        # Out of loop
        while table_queue:
            key = list(table_queue.keys())[0]
            if table_queue[key]:  # If list is not empty
                df = pd.DataFrame(table_queue[key])
                self.dataframe_to_sql(df, table_name=key, ifexists='append')
                del df
            del table_queue[key]

        # Make sure there are no more nodes to process
        assert len(table_queue) == 0

    @func_timer
    def extract_record_elements(self, start_from="all", record_tag="Record",
                                chunk_size=5000):
        """ Extracts all elements with tag = 'Record' from the tree.
        For each Record type (indicated by attribute 'type'), creates a
        table of 'Record' elements of the same type.

        For every nth iteration, appends all existing 'Record' (sub)tables
        to their respective tables in the database.

        Also creates one other table: 'InstantaneousBeatsPerMinute'.

        Kwargs:
            start_from (str or datetime.date): If datetime date is passed
                              in, will only extract nodes where "startDate"
                              attribute >= start_from. If "all", extracts all
                              nodes regardless of "startDate". Default is "all".
            record_tag (str): The tag associated with 'Record' nodes.
                              Defaults to "Record".
            chunk_size (int): The iteration number of the loop through 'Record'
                              nodes. For every nth iteration, existing 'Record'
                              subtables will written to the SQL database file.
                              And their list within table_queue will be reset
                              to an empty list. Default is 5000.
        """
        val_err_msg = "Have not implemented support for node child of type {0}"
        # Queue of every list of attributes to write to db file for every nth
        # iteration of the following loop
        table_queue = {}
        # InstantaneousBeatsPerMinute is a known (grand)child of Record
        bpm_type = "InstantaneousBeatsPerMinute"

        existing_table_length = {}

        # Get node list
        node_list = self.root.findall(f'./{record_tag}')
        if start_from != "all":
            # Have to approach this differently from Workout type nodes because
            # Record data is grouped by Record type.
            new_node_list = []
            for n in node_list:
                if datetime.strptime(n.attrib['startDate'], "%Y-%m-%d %H:%M:%S %z") >= start_from:
                    new_node_list.append(n)
            node_list = new_node_list

        for i, node in enumerate(node_list, start=1):
            # Write chunk_size entries to SQL
            if i % chunk_size == 0:
                for node_type, node_list in table_queue.items():
                    if node_list:  # If node_list is not empty
                        df = pd.DataFrame(node_list)
                        self.dataframe_to_sql(df, table_name=node_type, ifexists='append')
                        table_queue[node_type] = []
                        del df

            start = time.time()  # Timer

            # Get node.attrib type and remove prefix
            nodetype = node.attrib[TYPE_COL[record_tag]]
            for p in PREFIX_TO_STRIP[record_tag]:
                nodetype = nodetype.removeprefix(p)

            # If this is the first occurrence
            if nodetype not in table_queue.keys():
                table_queue[nodetype] = []
                self.num_nodes_by_elem[nodetype] = 0
                self.extract_time_per_elem[nodetype] = 0

            # Append current node attributes to list
            table_queue[nodetype].append(node.attrib)
            self.num_nodes_by_elem[nodetype] += 1
            node_index = self.num_nodes_by_elem[nodetype] - 1

            if self.append_to_existing_db:
                if nodetype not in existing_table_length.keys():
                    existing_table_length[nodetype] = self.get_current_table_length(nodetype)
                node_index += existing_table_length[nodetype]

            for child in self.get_subtree(node):
                if child.tag == "MetadataEntry":
                    new_item = {child.attrib['key']: child.attrib['value']}
                    table_queue[nodetype][-1].update(new_item)
                elif child.tag == bpm_type:
                    if child.tag not in table_queue.keys():
                        table_queue[child.tag] = []
                        self.num_nodes_by_elem[child.tag] = 0
                        self.extract_time_per_elem[child.tag] = 0
                    bpm_start = time.time()
                    new_items = {'recordType': nodetype,
                                 'recordIndex': node_index}
                    bpm_node_attrib = child.attrib | new_items
                    table_queue[child.tag].append(bpm_node_attrib)
                    self.num_nodes_by_elem[child.tag] += 1
                    self.extract_time_per_elem[child.tag] += time.time() - bpm_start
                elif child.tag == "HeartRateVariabilityMetadataList":
                    # HeartRateVariabilityMetadataList is just a wrapper node
                    # for child type "InstantaneousBeatsPerMinute"
                    pass
                elif child.tag == record_tag:
                    # get_subtree also returns argument node
                    pass
                else:
                    raise ValueError(val_err_msg.format(child.tag))

            self.extract_time_per_elem[nodetype] += time.time() - start

            # Write all InstantaneousBPM entries to SQL and reset table_queue
            if bpm_type in table_queue.keys() and len(table_queue[bpm_type]) >= chunk_size:
                df = pd.DataFrame(table_queue[bpm_type])
                self.dataframe_to_sql(df, table_name=bpm_type, ifexists='append')
                del df
                table_queue[bpm_type] = []

        # Out of loop
        while table_queue:
            # If exited out of loop and there's still some nodes to process
            key = list(table_queue.keys())[0]
            if table_queue[key]:
                df = pd.DataFrame(table_queue[key])
                self.dataframe_to_sql(df, table_name=key, ifexists='append')
                del df
            del table_queue[key]

        # Make sure there are no more nodes to process
        assert len(table_queue) == 0

    @func_timer
    def extract_childless_elements(self, tag, start_from="all", rootnode=None,
                                   table_name=""):
        """ Extracts attributes of (childless) Elements with tag = 'tag' to a
        table in a database with name table_name.

        Args:
            tag (str): Node tag.

        Kwargs:
            start_from (str or datetime.date): If datetime date is passed
                              in, will only extract nodes where "startDate"
                              attribute >= start_from. If "all", extracts all
                              nodes regardless of "startDate". Default is "all".
            rootnode (ElementTree.Element): Root node. If None is passed in,
                                            will default to the class root
                                            node, the root of the ElementTree.
            table_name (str): Name of the table to create in the database. If
                              an empty string is passed in (the default), the
                              table name is the tag.
        """
        if not rootnode:
            rootnode = self.root

        if not table_name:
            table_name = tag

        if table_name not in self.num_nodes_by_elem.keys():
            self.num_nodes_by_elem[table_name] = 0
            self.extract_time_per_elem[table_name] = 0

        start = time.time()  # Timer

        # Get node list
        node_list = rootnode.findall(f"./{tag}")
        if_exists = 'fail'

        # If append to latest db is True
        if start_from != "all":
            if tag == "Me":
                if_exists = 'replace'
            elif tag == "ExportDate":
                if_exists = 'append'
            elif tag == "ActivitySummary":
                if_exists = 'append'
                dcol = 'dateComponents'
                start = -1
                cur_date = datetime.strptime(node_list[-1].attrib[dcol], "%Y-%m-%d")
                while cur_date.date() >= start_from.date():
                    start -= 1
                    cur_date = datetime.strptime(node_list[start].attrib[dcol], "%Y-%m-%d")
                node_list = node_list[start + 1:]
            else:
                raise ValueError(f"Have not implemented append support for type {tag}")

        # Initialize container for node attributes
        attrib_list = []
        for i, node in enumerate(node_list, start=1):
            attrib_list.append(node.attrib)

        # Call dataframe_to_sql() and write dataframe to database
        df = pd.DataFrame(attrib_list)
        self.dataframe_to_sql(df, table_name, ifexists=if_exists)

        # Update node count and node timer
        self.num_nodes_by_elem[table_name] = i
        self.extract_time_per_elem[table_name] += time.time() - start

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
                logging.info(f"Added new column '{col}' for table {tbl}")

            # Fetch DB columns again
            check_cols = [j[0] for j in conn.execute(text(query_cols)).fetchall()]

            for added_col in new_cols:
                assert added_col in check_cols, f"{added_col} not in table cols"

            df.to_sql(tbl, con=conn, if_exists='append', method='multi')

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
                if self.append_to_existing_db and ifexists == 'append':
                    # Reindex the DataFrame according to existing table length
                    query = f"SELECT count(*) FROM {table_name}"
                    table_len = conn.execute(query).fetchone()[0]
                    df.index = df.index + table_len

                df.to_sql(table_name, con=conn, if_exists=ifexists,
                          method='multi')
            except (sqlalchemy.exc.OperationalError, sqlite3.OperationalError) as e:
                # Log error
                logging.info(f"Encountered error on {table_name}")

                # Thee following split() is to truncate the error message to
                # only the description of error. Otherwise, will also print
                # a list of the entries that it tried to pass in, which for
                # a DataFrame of 5000 would be a very long list.
                truncated_msg = str(e).split('\n')[0]
                self.table_error_count[table_name] += 1

                # If the error is that the table has no column found in df:
                if "has no column" in truncated_msg:
                    logging.info(truncated_msg)
                    self.add_newcols_to_table(df, table_name)
                elif "too many SQL variables" in truncated_msg:
                    logging.error(truncated_msg)
                    err_msg = f"Cannot insert {table_name} into database."
                    logging.error(err_msg)
                    print(err_msg, end='\n')

        self.tosql_time_per_elem[table_name] += time.time() - start_time

    def extract_data(self):
        """ Extracts to various tables information from nodes of the
        ElementTree.

        The resulting tables are stored under a database .db file, the name of
        which is specified by the class variable `self.db_name`.
        """
        # Get list of elements
        self.elements_to_extract = list(set(self.get_top_level_tags()) - set(self.exclude))

        # If appending to existing database
        from_datetime = "all" if not self.append_from else self.append_from

        for elem in self.elements_to_extract:
            msg = "Extracting {0}......".format(elem)
            logging.info(msg)
            if self.verbose:
                print(msg, end=' ', flush=True)

            if elem == "Workout":
                self.extract_workout_elements(start_from=from_datetime)
            elif elem == "Record":
                self.extract_record_elements(start_from=from_datetime)
            elif elem in ["Correlation", "Audiogram", "ClinicalRecord"]:
                pass
            else:
                self.extract_childless_elements(elem, start_from=from_datetime)

        # Timer stats
        self.program_end_time = time.time()
        self.total_elapsed_time = self.program_end_time - self.program_start_time

        # Log and check results
        self.log_results()
        if not self.append_to_existing_db:
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
            in_memory_tbl_count = len(self.num_nodes_by_elem.keys())
            if not db_total_tbl_count == in_memory_tbl_count:
                total_count_msg = "There are {0} tables inside db file but\
                                   {1} tables were created during runtime".format(db_total_tbl_count,
                                                                                  in_memory_tbl_count)
                logging.debug(total_count_msg)
                print_error_msgs.append(total_count_msg)

            # Compares list of table names
            in_memory_tables = list(self.num_nodes_by_elem.keys())
            list_diff = list(set(db_tables) ^ set(in_memory_tables))
            list_fail_msg = "List of table names self.num_nodes_by_elem.keys() and from db don't match."
            if list_diff:
                logging.debug(list_fail_msg)
                logging.debug("self.num_nodes_by_elem.keys(): {}".format(in_memory_tables))
                logging.debug("Tables inside db: {}".format(db_tables))
                logging.debug("List difference: {}".format(list_diff))

                print_error_msgs.append(list_fail_msg)

            for tb in self.num_nodes_by_elem.keys():  # Compare lengths of individual tables
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
        num_elems_extracted = f"There are {len(self.num_nodes_by_elem.keys())} types of elements extracted"
        logging.info(num_elems_extracted)
        if self.verbose:
            print("\n" + num_elems_extracted, end='\n')

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

    parser = argparse.ArgumentParser(description='Extracts data from exported Apple Health file `export.xml` and stores it in a database inside a \
                                                 folder named `data/`. If path to `export.xml` is not passed in, will search for an export.xml \
                                                 in a folder `apple_health_export/` within the current working directory.',
                                     )
    parser.add_argument('-o', '--open-file',
                        type=str, nargs='?', required=False,
                        help='the/path/to/export.xml.')
    parser.add_argument('-a', '--append',
                        type=bool, required=False, default=False,
                        action=argparse.BooleanOptionalAction,
                        help="Toggle whether to append new data to the latest db file.")
    args = vars(parser.parse_args())

    if args['open_file'] is None:
        xml_path = os.path.join(os.getcwd(), "apple_health_export", "export.xml")
    else:
        arg_path = args['open_file']
        if arg_path[0] == '/':
            xml_path = os.path.join(os.getcwd(), arg_path[1:])
        else:
            xml_path = arg_path

    tree = AppleHealthExtraction(xml_path, append_to_existing_db=args['append'],
                                 exclude=['Correlation', 'Audiogram'],
                                 append_ver=True)
    tree.extract_data()
