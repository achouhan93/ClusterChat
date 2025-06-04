import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.feather as feather
import pyarrow.ipc as ipc 

import os

def updateDate(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, f'../static/data/{filename}')
    data_path = os.path.normpath(data_path)

       # Try opening as a stream
    with pa.memory_map(data_path, 'r') as source:
        reader = ipc.open_stream(source)
        table = reader.read_all()

    # Convert 'date' column from string to timestamp
    date_index = table.schema.get_field_index("date")
    parsed_dates = pc.strptime(table["date"], format="%Y-%m-%d", unit="s")
    table = table.set_column(date_index, "date", parsed_dates)

    # Save the updated file
    updated_path = os.path.join(script_dir, 'updated-' + filename)
    with pa.OSFile(updated_path, 'wb') as sink:
        with ipc.new_file(sink, table.schema) as writer:
            writer.write(table)

    print(f"✅ Updated file saved to: {updated_path}")

if __name__ == "__main__":
    updateDate('cosmograph-points-1M.arrow')