# OPC UA PYTHON READER

This Python script allows you to explore OPC UA server nodes and log their data to either a CSV file or a SQL Server database. It uses the `asyncua` library for OPC UA communication and provides options for flexible configuration.

## Prerequisites

- Python 3.6 or above
- Install required packages using the following command:
  ```bash
  pip install -r requirements.txt
  ```

## Usage

### Basic Usage

To explore OPC UA server nodes and log data, run the script with the required arguments:

```bash
python script_name.py -s <server_ip> -p <server_port> [-u <username> -w <password>] -t <time_between_reads> -r <number_of_reads> --save-to-sql [--db-ip <db_ip> --db-name <db_name> --db-username <db_username> --db-password <db_password> --sql-driver <sql_driver> --table-name <table_name>] --save-to-csv --file-name <file_name> [-a] [-v]
```

### Options

- `-s`, `--server`: OPC UA server IP address.
- `-p`, `--port`: OPC UA server port (default: 4840).
- `-u`, `--username`: OPC UA server username.
- `-w`, `--password`: OPC UA server password.
- `-t`, `--time`: Time between reads in seconds (default: 1).
- `-r`, `--reads`: Number of reads, -1 for infinite (default: 10).
- `--save-to-sql`: Save data to SQL Server.
- `--db-ip`: Database IP address.
- `--db-name`: Database name.
- `--db-username`: Database username.
- `--db-password`: Database password.
- `--sql-driver`: SQL Server driver.
- `--table-name`: Name of the table to save data.
- `--no-save-to-csv`: Do not save data to a CSV file.
- `-f`, `--file-name`: Output file name for saving CSV data.
- `-a`, `--all`: Save all nodes, not just when they change.
- `-v`, `--verbose`: Verbose output.

### Example

Explore OPC UA server nodes, save data to a CSV file, and log data to a SQL Server database:

```bash
python script_name.py -s 192.168.0.1 -p 4840 -u user -w password -t 2 -r 50 --save-to-sql --db-ip 192.168.0.2 --db-name MyDatabase --db-username db_user --db-password db_password --sql-driver ODBC --table-name MyTable --save-to-csv -f output.csv -a -v
```

## Notes

- Ensure that the required libraries are installed using the provided `pip install` command.
- The script supports both CSV and SQL Server logging. You can choose one or both options based on your requirements.
- Use the `-a` option to save data for all nodes, not just when they change.
- The script is designed to be flexible and provides options for customization and debugging.

Feel free to modify the script and adapt it to your specific use case. For additional information on OPC UA and its Python implementation, refer to the [asyncua documentation](https://github.com/FreeOpcUa/python-opcua) and [pyodbc documentation](https://github.com/mkleehammer/pyodbc).