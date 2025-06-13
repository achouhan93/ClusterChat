
import pyarrow as pa # Import pyarrow for memory_map
import pyarrow.ipc as ipc # Import pyarrow.ipc for Arrow IPC format
import sys
import os

# Define the input file path
# filename = 'cosmograph-points-batch-1.arrow'
# script_dir = os.path.dirname(os.path.abspath(__file__))
# input_file = os.path.join(script_dir, f'../static/data/{filename}')
# input_file = os.path.normpath(input_file)


input_file="cosmograph-points-1M.arrow"

# Check if the file exists
if not os.path.exists(input_file):
    print(f"Error: The file '{input_file}' was not found.", file=sys.stderr)
    print("Please ensure 'create_arrow_file.py' has been run successfully.", file=sys.stderr)
    sys.exit(1)

try:
    # Read the Arrow IPC file into a PyArrow Table
    # Using memory_map and open_file to read the IPC file
    with pa.memory_map(input_file, 'rb') as source:
        reader = ipc.open_file(source)
        table = reader.read_all()

    print(f"Successfully read '{input_file}'.")
    print("\n--- Table Schema ---")
    print(table.schema)

    print("\n--- Table Data (as Python dictionary) ---")
    # Convert the table to a Python dictionary for easy printing
    print(table.to_pydict())

    print("\n--- Table Data (as Pandas DataFrame - if pandas is installed) ---")
    # You can also convert to a Pandas DataFrame for a tabular view,
    # if pandas is installed. This is often more human-readable.
    try:
        import pandas as pd
        df = table.to_pandas()
        print(df.to_string(index=False)) # Use to_string to avoid truncation
    except ImportError:
        print("Pandas not installed. Install with 'pip install pandas' for tabular view.")

except Exception as e:
    print(f"An error occurred while reading the Arrow file: {e}", file=sys.stderr)
    sys.exit(1)

