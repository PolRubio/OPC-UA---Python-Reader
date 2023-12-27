import asyncio
import argparse
import traceback
import signal
import time
import csv
import pyodbc
from asyncua import Client
from alive_progress import alive_bar

class NodeExplorer:
    def __init__(self, client):
        self.client = client
        self.leaf_nodes = []

    async def explore_nodes(self, node):
        browse_name = await node.read_browse_name()
        namespace_index = node.nodeid.NamespaceIndex
        children = await node.get_children()

        if children == [] and namespace_index == 1:
            self.leaf_nodes.append(node)
            return

        for child in children:
            await self.explore_nodes(child)

    def print_summary(self):
        print(f"Number of children: {len(self.leaf_nodes)}\n")

    def print_leaf_nodes(self):
        for node in self.leaf_nodes:
            print(node)

    def get_leaf_nodes(self):
        return self.leaf_nodes

    async def get_leaf_node_names(self):
        leaf_nodes_names = []
        for node in self.leaf_nodes:
            browse_name = await node.read_browse_name()
            leaf_nodes_names.append(browse_name.Name)
        return leaf_nodes_names

class OPCUAClient:
    def __init__(self, server_ip, server_port, username=None, password=None):
        if username is None and password is None:
            self.client = Client(url=f"opc.tcp://{server_ip}:{server_port}")
        else:
            self.client = Client(url=f"opc.tcp://{username}:{password}@{server_ip}:{server_port}")

    async def connect(self):
        await self.client.connect()
        print("Connected to server!\n")

    async def disconnect(self):
        await self.client.disconnect()
        print("Disconnected from server!\n")

class DataHandler:
    def __init__(self, args, leaf_nodes, leaf_nodes_names):
        self.args = args
        self.leaf_nodes = leaf_nodes
        self.last_nodes = {node: None for node in leaf_nodes}
        self.leaf_nodes_names = leaf_nodes_names

        if self.args.save_to_csv and self.args.file_name is None:
            self.file_name = f"{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}.csv"
        else:
            self.file_name = self.args.file_name

        if self.args.save_to_sql:
            connection_string = f"DRIVER={self.args.sql_driver};SERVER={self.args.db_ip};DATABASE={self.args.db_name};UID={self.args.db_username};PWD={self.args.db_password}"
            self.connection = pyodbc.connect(connection_string)
            self.cursor = self.connection.cursor()

    def is_table_created(self):
        self.cursor.execute(f"SELECT name FROM sys.tables WHERE name='{self.args.table_name}'")
        return self.cursor.fetchone() is not None

    def create_table(self, types):
        if self.args.verbose: print(f"CREATE TABLE {self.args.table_name} (Timestamp DATETIME, "
                                + ', '.join([f"{node.replace(r'.', r'_')} {types[node.replace(r'.', r'_')]}" for node in self.leaf_nodes_names]) + ")")
        self.cursor.execute(f"CREATE TABLE {self.args.table_name} (Timestamp DATETIME, "
                                + ', '.join([f"{node.replace(r'.', r'_')} {types[node.replace(r'.', r'_')]}" for node in self.leaf_nodes_names]) + ")")
        self.connection.commit()
        print(f"Created table {self.args.table_name} in database {self.args.db_name}!\n")

    def write_header(self, header):
        if self.args.save_to_csv:
            with open(self.file_name, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(header)
                csvfile.flush()
    
    def write_row(self, row):
        if self.args.save_to_csv:
            with open(self.file_name, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(row)
                csvfile.flush()

        if self.args.save_to_sql:
            placeholders = ', '.join(['?' for _ in row])
            insert_query = f"INSERT INTO {self.args.table_name} VALUES ({placeholders})"
            if self.args.verbose: 
                print(insert_query)
                print(row)
            self.cursor.execute(insert_query, row)
            self.connection.commit()

def on_sigint(signum, frame):
    print("\nReceived SIGINT (CTRL+C). Exiting gracefully.")
    raise KeyboardInterrupt

class DataExplorer:
    def __init__(self, opcua_client, explorer, args):
        self.opcua_client = opcua_client
        self.explorer = explorer
        self.args = args

    async def run(self):
        try:
            await self.opcua_client.connect()
        except Exception as e:
            print(f"Error connecting to server: {e}")
            if self.args.verbose: print(traceback.format_exc())
            return

        try:
            root_node = self.opcua_client.client.get_root_node()
            await self.explorer.explore_nodes(root_node)
            if self.args.verbose:
                self.explorer.print_summary()
                self.explorer.print_leaf_nodes()

            leaf_nodes = self.explorer.get_leaf_nodes()
            leaf_node_names = await self.explorer.get_leaf_node_names()
        except Exception as e:
            print(f"Error exploring nodes: {e}")
            if self.args.verbose: print(traceback.format_exc())
            return

        reads_remaining = int(self.args.reads)

        try:
            self.data_handler = DataHandler(self.args, leaf_nodes, leaf_node_names)
        except Exception as e:
            print(f"Error creating data handler: {e}")
            if self.args.verbose: print(traceback.format_exc())
            return

        try:
            signal.signal(signal.SIGINT, on_sigint)

            with alive_bar(reads_remaining, title='Diferent Nodes' if not self.args.all else 'Reading Nodes', calibrate=1000) as bar:
                self.data_handler.write_header(["Timestamp"] + leaf_node_names)
                while reads_remaining != 0:
                    diferent_node = False
                    row = [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())]

                    for node in leaf_nodes:
                        try:
                            value = await node.read_value()
                            if self.data_handler.last_nodes[node] != value:
                                self.data_handler.last_nodes[node] = value
                                diferent_node = True
                                if self.args.verbose: print(f"{node} = {value}")
                            
                            row.append(value)
                        except Exception as e:
                            row.append("Error")
                            if self.args.verbose:
                                print(f"Error reading node ({node}): {e}")
                                print(traceback.format_exc())

                    if reads_remaining > 0:
                        reads_remaining -= 1

                    if diferent_node or self.args.all:

                        if self.args.save_to_sql :
                            if self.args.verbose: print(f"Is table {self.args.table_name} created in database {self.args.db_name}? {self.data_handler.is_table_created()}")
                            if not self.data_handler.is_table_created():
                                types = {"TIMESTAMP": "DATETIME"}
                                tmp_row = row[1:]
                                for i in range(len(leaf_node_names)):
                                    try:
                                        float(tmp_row[i])
                                        types[leaf_node_names[i].replace(r'.', r'_')] = "FLOAT"
                                    except:
                                        types[leaf_node_names[i].replace(r'.', r'_')] = "VARCHAR(255)"

                                if self.args.verbose:
                                    print(types)
                                    print()
                                self.data_handler.create_table(types)

                        self.data_handler.write_row(row)
                        bar()
                        if self.args.verbose: print()

                    await asyncio.sleep(float(self.args.time))

        except KeyboardInterrupt:
            pass
        finally:
            print("\nExiting...")
            try:
                await self.opcua_client.disconnect()
            except Exception as e:
                print(f"Error disconnecting from server: {e}")
                if self.args.verbose: print(traceback.format_exc())
                return

def main(args):
    opcua_client = OPCUAClient(args.server, args.port, args.username, args.password)
    explorer = NodeExplorer(opcua_client.client)
    data_explorer = DataExplorer(opcua_client, explorer, args)

    try:
        asyncio.run(data_explorer.run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error running async loop: {e}")
        if args.verbose: print(traceback.format_exc())
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Explore OPC UA server nodes and save data.')

    # OPC UA server options
    parser.add_argument('-s', '--server', dest='server', required=True, help='OPC UA server IP address')
    parser.add_argument('-p', '--port', dest='port', default=16664, help='OPC UA server port')
    parser.add_argument('-u', '--username', dest='username', help='OPC UA server username')
    parser.add_argument('-w', '--password', dest='password', help='OPC UA server password')

    # Time and reads options
    parser.add_argument('-t', '--time', dest='time', default=1, help='Time between reads in seconds')
    parser.add_argument('-r', '--reads', dest='reads', default=10, help='Number of reads, -1 for infinite')

    # SQL Server options
    parser.add_argument('--save-to-sql', dest='save_to_sql', action='store_true', help='Save data to SQL Server')
    parser.add_argument('--db-ip', dest='db_ip', help='Database IP address')
    parser.add_argument('--db-name', dest='db_name', help='Database name')
    parser.add_argument('--db-username', dest='db_username', help='Database username')
    parser.add_argument('--db-password', dest='db_password', help='Database password')
    parser.add_argument('--sql-driver', dest='sql_driver', help='SQL Server driver')
    parser.add_argument('--table-name', dest='table_name', help='Name of the table to save data')

    # CSV options
    parser.add_argument('--no-save-to-csv', dest='save_to_csv', action='store_false', help='Do not save data to a CSV file')
    parser.add_argument('-f', '--file-name', dest='file_name', help='Output file name for saving CSV data')

    # Optional flags for debugging
    parser.add_argument('-a', '--all', dest='all', action='store_true', help='Save all nodes, not just when they change')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.save_to_sql and (not args.db_ip or not args.db_name or not args.db_username or not args.db_password or not args.table_name):
        print("For SQL Server, please provide database IP, name, username, password, and table name.")
        exit()
    
    if args.save_to_sql and args.sql_driver.lower() != 'sql server':
        print("Only SQL Server is supported at the moment.")
        exit()

    if args.username is None and args.password is not None or args.username is not None and args.password is None:
        print("Username and password must be provided together.")
        exit()

    main(args)
