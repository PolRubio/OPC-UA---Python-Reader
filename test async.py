import asyncio, argparse, traceback
from asyncua import Client

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

def main(args):
    opcua_client = OPCUAClient(args.server, args.port, args.username, args.password)

    async def run():
        explorer = NodeExplorer(opcua_client.client)
        
        try:
            await opcua_client.connect()
        except Exception as e:
            print(f"Error connecting to server: {e}")
            if args.verbose: print(traceback.format_exc())
            return

        try:
            root_node = opcua_client.client.get_root_node()
            await explorer.explore_nodes(root_node)
            if args.verbose: 
                explorer.print_leaf_nodes()
                explorer.print_summary()

            leaf_nodes = explorer.get_leaf_nodes()              
        except Exception as e:
            print(f"Error exploring nodes: {e}")
            if args.verbose: print(traceback.format_exc())
            return

        for node in leaf_nodes:
            try:
                value = await node.read_value()
                print(f"{node} = {value}")
            except Exception as e:
                if args.verbose:
                    print(f"Error reading node ({node}): {e}")
                    print(traceback.format_exc())

        print()

        try:
            await opcua_client.disconnect()
        except Exception as e:
            print(f"Error disconnecting from server: {e}")
            if args.verbose: print(traceback.format_exc())
            return

    asyncio.run(run())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Explore OPC UA server nodes.')
    parser.add_argument('-s', '--server', dest='server', required=True, help='OPC UA server IP address')
    parser.add_argument('-p', '--port', dest='port', default=16664, help='OPC UA server port')
    parser.add_argument('-u', '--username', dest='username', help='OPC UA server username')
    parser.add_argument('-w', '--password', dest='password', help='OPC UA server password')
    parser.add_argument('-t', '--time', dest='time', default=1, help='Time between reads in seconds')
    parser.add_argument('-r', '--read', dest='read', default=10, help='Number of reads, 0 for infinite')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.username is None and args.password is not None or args.username is not None and args.password is None:
        print("Username and password must be provided together.")
        exit()

    main(args)
