import asyncio
import argparse
import traceback
import signal
import time
import csv
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

class CSVHandler:
    def __init__(self, filename, leaf_nodes):
        if filename is None:
            filename = f"opcua_{args.server}_{args.port}_{time.strftime('%Y%m%d', time.localtime())}.csv"
        self.filename = filename
        self.leaf_nodes = leaf_nodes
        self.last_nodes = {node: None for node in leaf_nodes}

    def write_row(self, row):
        with open(self.filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(row)
            csvfile.flush()

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
            self.csv_handler = CSVHandler(self.args.file, leaf_nodes)
        except Exception as e:
            print(f"Error exploring nodes: {e}")
            if self.args.verbose: print(traceback.format_exc())
            return

        reads_remaining = int(self.args.reads)

        try:
            signal.signal(signal.SIGINT, on_sigint)

            with alive_bar(reads_remaining, title='Diferent Nodes' if not self.args.all else 'Reading Nodes', calibrate=1000) as bar:
                self.csv_handler.write_row(["Timestamp"] + leaf_node_names)
                while reads_remaining != 0:
                    diferent_node = False
                    row = [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())]

                    for node in leaf_nodes:
                        try:
                            value = await node.read_value()
                            if self.csv_handler.last_nodes[node] != value:
                                self.csv_handler.last_nodes[node] = value
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
                        self.csv_handler.write_row(row)
                        bar()
                        if self.args.verbose: print()

                    await asyncio.sleep(float(args.time))

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
    parser = argparse.ArgumentParser(description='Explore OPC UA server nodes.')
    parser.add_argument('-s', '--server', dest='server', required=True, help='OPC UA server IP address')
    parser.add_argument('-p', '--port', dest='port', default=16664, help='OPC UA server port')
    parser.add_argument('-u', '--username', dest='username', help='OPC UA server username')
    parser.add_argument('-w', '--password', dest='password', help='OPC UA server password')
    parser.add_argument('-t', '--time', dest='time', default=1, help='Time between reads in seconds')
    parser.add_argument('-r', '--reads', dest='reads', default=10, help='Number of reads, -1 for infinite')
    parser.add_argument('-f', '--file', dest='file', help='Output file name')
    parser.add_argument('-a', '--all', dest='all', action='store_true', help='Save all nodes, not just when they change')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.username is None and args.password is not None or args.username is not None and args.password is None:
        print("Username and password must be provided together.")
        exit()

    main(args)
