# OPC UA PYTHON READER

This Python script allows you to explore OPC UA server nodes and read their values. It connects to an OPC UA server, explores the server's nodes, and records the values in a CSV file.

## Features

- Explore OPC UA server nodes and display a summary.
- Read values from OPC UA leaf nodes.
- Save node values to a CSV file.
- Graceful handling of interruptions (CTRL+C).
- Option to save all nodes or only when values change.

## Prerequisites

- Python 3.6 or later
- Install required packages using the following command:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python opcua_node_explorer.py -s <server_ip> -p <server_port> [-u <username> -w <password>] -t <time_between_reads> -r <number_of_reads> -f <output_file_name> [-a] [-v]
```

- `-s`, `--server`: OPC UA server IP address (required).
- `-p`, `--port`: OPC UA server port (default: 16664).
- `-u`, `--username`: OPC UA server username.
- `-w`, `--password`: OPC UA server password.
- `-t`, `--time`: Time between reads in seconds (default: 1).
- `-r`, `--reads`: Number of reads, -1 for infinite (default: 10).
- `-f`, `--file`: Output file name for saving CSV data.
- `-a`, `--all`: Save all nodes, not just when they change.
- `-v`, `--verbose`: Verbose output.

## Example

```bash
python opcua_node_explorer.py -s 127.0.0.1 -p 4840 -u user -w password -t 2 -r 5 -f opcua_data.csv -v
```

This command connects to the OPC UA server at `127.0.0.1:4840` with the provided username and password, reads values every 2 seconds, performs 5 reads, and saves the data to the `opcua_data.csv` file with verbose output.

Feel free to modify the script to suit your specific requirements.
