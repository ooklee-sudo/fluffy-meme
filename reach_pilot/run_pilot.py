"""Batch runner: N Django instances x R repetitions x models -> pilot_results.csv (resumable).

python3 run_pilot.py --models anthropic/claude-haiku-5.5 --n 5 --reps 3 [--ids id1,id2]
Then:  python3 analyze_pilot.py pilot_results.csv
"""
import argparse, csv, json, os, sys, traceback
import swt_pilot as S

ap = argparse.ArgumentParser()
ap.add_argument("--models", default="anthropic/claude-haiku-5.5")
ap.add_argument("--n", type=int, default=3); ap.add_argument("--reps", type=int, default=2)
ap.add_argument("--ids", default=""); ap.add_argument("--out", default="pilot_results.csv")
ap.add_argument("--workdir", default=os.path.join(S.HERE, "work"))
a = ap.parse_args()
os.makedirs(a.workdir, exist_ok=True)
df = S.load(a.workdir)
dj = df[df.repo == "django/django"].sort_values("instance_id")
ids = a.ids.split(",") if a.ids else list(dj.instance_id.iloc[:: max(1, len(dj) // a.n)][: a.n])
done = set()
if os.path.exists(a.out):
    done = {(r["instance_id"], r["model"], int(r["rep"])) for r in csv.DictReader(open(a.out))}
new = not os.path.exists(a.out)
cols = ["instance_id", "model", "rep", "detected", "reason", "n_tests", "n_before_fail", "cost_usd", "seconds"]
with open(a.out, "a", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); new and w.writeheader()
    for iid in ids:
        row = next(df[df.instance_id == iid].itertuples())
        for model in a.models.split(","):
            for rep in range(a.reps):
                if (iid, model, rep) in done:
                    continue
                try:
                    r = S.run_instance(row, model, a.workdir, rep)
                except Exception as e:                      # environment failures are data too
                    r = dict(instance_id=iid, model=model, rep=rep, detected=False, reason="harness_error: " + str(e)[:100])
                r["cost_usd"] = (r.get("cost_tokens") or {}).get("cost")
                w.writerow({k: r.get(k) for k in cols}); f.flush()
                print(iid, model, rep, r["detected"], r["reason"], flush=True)
