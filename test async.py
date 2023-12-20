import asyncio, argparse, traceback
from asyncua import Client

class NodeExplorer:
    def __init__(self, client):
        self.client = client
        self.leaf_nodes = []

    async def explore_nodes(self, node, indent=""):
        try:
            browse_name = await node.read_browse_name()
            children = await node.get_children()

            if children == []: # and node.read_browse_name():
                self.leaf_nodes.append(node)
                return

            for child in children:
                await self.explore_nodes(child, indent + "---")

        except Exception as e:
            print(f"{indent}Error exploring node: {e}")
            print(traceback.format_exc())

    def print_summary(self):
        print(f"Number of children: {len(self.leaf_nodes)}\n")

    def print_leaf_nodes(self):
        for node in self.leaf_nodes:
            print(node)

class OPCUAClient:
    def __init__(self, server_ip, server_port, username=None, password=None):
        if username is None and password is None:
            self.client = Client(url=f"opc.tcp://{server_ip}:{server_port}")
        else:
            self.client = Client(url=f"opc.tcp://{username}:{password}@{server_ip}:{server_port}")

    async def connect(self):
        try:
            await self.client.connect()
            print("Connected to server!\n")
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return False
        return True

    async def disconnect(self):
        await self.client.disconnect()
        print("Disconnected from server!\n")

def main(args):
    opcua_client = OPCUAClient(args.server, args.port, args.username, args.password)

    async def run():
        explorer = NodeExplorer(opcua_client.client)

        if await opcua_client.connect():
            try:
                root_node = opcua_client.client.get_root_node()
                await explorer.explore_nodes(root_node)
                if args.verbose: explorer.print_leaf_nodes()
                explorer.print_summary()
            except Exception as e:
                print(f"Error reading variable value: {e}")
                print(traceback.format_exc())
            finally:
                await opcua_client.disconnect()

    asyncio.run(run())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Explore OPC UA server nodes.')
    parser.add_argument('-s', '--server', dest='server', required=True, help='OPC UA server IP address')
    parser.add_argument('-p', '--port', dest='port', default=16664, help='OPC UA server port')
    parser.add_argument('-u', '--username', dest='username', help='OPC UA server username')
    parser.add_argument('-w', '--password', dest='password', help='OPC UA server password')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.username is None and args.password is not None or args.username is not None and args.password is None:
        print("Username and password must be provided together.")
        exit()

    main(args)
