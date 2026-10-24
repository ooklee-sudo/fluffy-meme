"""Zero-inflation check on saved replication data: python tools/zinb_check.py out_rep/replication_data.csv [...]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

import models

for p in sys.argv[1:]:
    z = models.zero_inflation_check(pd.read_csv(p))
    print(p, {k: (round(v, 3) if isinstance(v, float) and abs(v) > 1e-3 else v) for k, v in z.items()})
