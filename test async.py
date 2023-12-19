import asyncio
from asyncua import Client, ua

async def explore_nodes(node, indent=""):
    try:
        browse_name = await node.read_browse_name()
        children = await node.get_children()
        
        if children == []:
            # print(f"{indent}Children ID: {node.nodeid}, Children Browse Name: {browse_name.Name}")
            print(f"{indent}{browse_name.Name}")
            return

        # print(f"{indent}Node ID: {node.nodeid}, Node Browse Name: {browse_name.Name}")
        print(f"{indent}{browse_name.Name}:")

        for child in children:
            # await explore_nodes(child, indent + "  ")
            await explore_nodes(child, indent + "---")

    except Exception as e:
        print(f"{indent}Error exploring node: {e}")

async def main():
    # OPC UA server information
    server_ip = "192.168.100.186"
    server_port = "16664"
    username = "opc"
    password = "ulmaopc"

    # Create a client and connect to the server
    try:
        print("\nConnecting to server...")
        client = Client(url=f"opc.tcp://{username}:{password}@{server_ip}:{server_port}")
        print("Client: ", client)
        await client.connect()
        print("Connected to server!\n")
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return

    try:
        print("Exploring nodes...")
        root_node = client.get_root_node()
        await explore_nodes(root_node)

    except Exception as e:
        print(f"Error reading variable value: {e}")
    finally:
        # Disconnect from the server
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
