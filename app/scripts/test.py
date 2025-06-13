import pyarrow as pa
import pyarrow.compute as pc
import pandas as pd

# Example: Column of string IDs
string_ids = ["36108871", "36108871","36108871"]

# Convert to int64 if it's just numeric strings
int_ids = [int(s) for s in string_ids]

# Then build a column (optional: convert to Arrow)
arrow_array = pa.array(int_ids, type=pa.uint32())
print(arrow_array)