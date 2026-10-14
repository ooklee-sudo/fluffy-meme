"""Load chain comps keyed by CALENDAR quarter (plan: fiscal quarter mapped to the calendar quarter containing most of its weeks = quarter of the midpoint, fiscal_quarter_end - 45 days). Replaces the earlier label-based keying, which misaligned Starbucks and Jack in the Box by one quarter."""
import json,glob,pandas as pd
def load():
    D={}
    for f in sorted(glob.glob('chains/*.json')):
        t=f.split('/')[1][:-5]; d={}
        for r in json.load(open(f)):
            if r['comps_pct'] is None: continue
            mid=pd.Timestamp(r['fiscal_quarter_end'])-pd.Timedelta(days=45); q=f"Q{mid.quarter} {mid.year}"
            d[q]=r['comps_pct']
        D[t]=d
    return D
