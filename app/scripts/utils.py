import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.feather as feather
import pyarrow.ipc as ipc 
from pathlib import Path

import os


def combineFiles(path):

    arrow_dir = Path(path)  # relative path
    files = sorted(arrow_dir.glob('cosmograph-points-batch*'))

    output_path = Path(f'{path}/cosmograph-points-combined.arrow')

    with output_path.open('wb') as out_f:
        writer = None
        for file_path in files:
            with file_path.open('rb') as in_f:
                try:
                    reader = ipc.RecordBatchStreamReader(in_f)
                except pa.lib.ArrowInvalid:
                    print(f"Skipping invalid or incompatible file: {file_path}")
                    continue

                if writer is None:
                    writer = ipc.RecordBatchStreamWriter(out_f, reader.schema)

                for batch in reader:
                    writer.write_batch(batch)

        if writer:
            writer.close()

def updateCols(filename):
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, f'../static/data/{filename}')
    data_path = os.path.normpath(data_path)

       # Try opening as a stream
    with pa.memory_map(data_path, 'r') as source:
        reader = ipc.open_stream(source)
        table = reader.read_all()

    # Convert 'date' column from string to timestamp
    
    

    date_index = table.schema.get_field_index("date")
    cluster_id_index = table.schema.get_field_index("cluster_id")
    title_index = table.schema.get_field_index("title")
    id_index = table.schema.get_field_index("id")
    
    # parsed_cluster_ids = pc.dictionary_encode(table.column(cluster_id_index))
    parsed_cluster_ids = pc.cast(table["cluster_id"],pa.uint32())
    parsed_ids = pc.cast(table["id"], pa.uint32())
    parsed_dates = pc.strptime(table["date"], format="%Y-%m-%d", unit="s")

    table = table.set_column(date_index, "date", parsed_dates)
    table = table.set_column(cluster_id_index, "cluster_id", parsed_cluster_ids)
    table = table.set_column(id_index, "id", parsed_ids)
    table = table.remove_column(title_index)

    output_path = os.path.join(script_dir, '../static/data', 'updated-' + filename)
    output_path = os.path.normpath(output_path)

    with pa.OSFile(output_path, 'wb') as sink:
        with ipc.new_file(sink, table.schema) as writer:
            writer.write(table)

    print(f"✅ Updated file saved to: {output_path}")
    print(table.schema)

def splitTable(filename):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, f'../static/data/{filename}')
    data_path = os.path.normpath(data_path)

       # Try opening as a stream
    with pa.memory_map(data_path, 'r') as source:
        reader = ipc.open_file(source)
        table = reader.read_all()

    num_rows = table.num_rows
    midpoint = num_rows // 2

    # Split the table
    table1 = table.slice(0, midpoint)
    table2 = table.slice(midpoint)


    output_path1 = os.path.join(script_dir, '../static/data', 'updated-1' + filename)
    output_path1 = os.path.normpath(output_path1)

    output_path2 = os.path.join(script_dir, '../static/data', 'updated-2' + filename)
    output_path2 = os.path.normpath(output_path2)

    with pa.OSFile(output_path1, "wb") as sink1:
        with ipc.new_file(sink1, table1.schema) as writer:
            writer.write(table1)

    with pa.OSFile(output_path2, "wb") as sink2:
        with ipc.new_file(sink2, table2.schema) as writer:
            writer.write(table2)

if __name__ == "__main__":
    # combineFiles('../static/data')
    updateCols('cosmograph-points-combined.arrow')
    splitTable('updated-cosmograph-points-combined.arrow')

