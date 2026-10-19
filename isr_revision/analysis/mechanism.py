"""Mechanism evidence: what rule do holders follow when they allocate?

Conditional logit of who gets a task slot, estimated separately where authority is
binding and active (holder in office) and, as a placebo, where allocation is random.
usage: python analysis/mechanism.py DATA_DIR      (needs allocations.csv)
"""
import sys, numpy as np, pandas as pd
from statsmodels.discrete.conditional_models import ConditionalLogit

A = pd.read_csv(f"{sys.argv[1]}/allocations.csv")
A["is_holder"] = (A.agent_id == A.holder_id).astype(int)
A["grp"] = A.world_id * 100000 + A.day * 10 + A.slot
X = ["cum_tasks_before", "energy_before", "is_holder", "gifted_holder_before"]
LABEL = {"cum_tasks_before": "rotation (neg = favours those with fewer tasks)",
         "energy_before": "need (neg = favours low-energy agents)",
         "is_holder": "self-allocation by holder",
         "gifted_holder_before": "reciprocity (pos = favours past givers to holder)"}

def run(df, name):
    m = ConditionalLogit(df.received, df[X], groups=df.grp).fit(disp=0)
    out = pd.DataFrame({"coef": m.params, "se": m.bse, "z": m.params / m.bse})
    out.index = [f"{c}: {LABEL[c]}" for c in out.index]
    print(f"\n== {name} (n slots {df.grp.nunique()}) ==\n{out.round(3).to_string()}")
    return m

# binding authority, office filled: the mechanism of interest
run(A[A.binding_active == 1], "Binding authority, office filled")
# placebo: allocation is a lottery, every coefficient should be ~0
run(A[A.binding_active == 0], "Placebo: advisory or vacant (random draw)")
# does the rule differ when office carries rents?
if "rent" in A:
    for r, d in A[A.binding_active == 1].groupby("rent"):
        run(d, f"Binding, rent={r}")
