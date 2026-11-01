# Concatenate per-shard feature files (f*.parquet from extract.py) into all.parquet. Usage: build_all.py DATA_DIR
import sys, glob, pandas as pd
d=sys.argv[1]; pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(d+'/f*.parquet'))],ignore_index=True).to_parquet(d+'/all.parquet')
