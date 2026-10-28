"""Turn SWE-agent trajectories into step-level event sequences.
Event (agent-side tool error) at step t if the observation after the agent's t-th action shows interface misuse:
 edit rejected for syntax errors, command not found, missing file/directory, usage error, interface 'Error:' line, timeout.
A separate mark records Python tracebacks (often intended, e.g. reproducing the bug).
python3 -I extract_events.py out.parquet shard1.parquet [shard2 ...]"""
import sys, re
import pyarrow.parquet as pq, pandas as pd
ERR = re.compile(r"(Your proposed edit has introduced new syntax error|command not found|No such file or directory|Directory .* not found|File .* not found|"
                 r"^Usage: |^usage: |^Error: |Invalid line|EXECUTION TIMED OUT|is not a valid|Unrecognized arguments|unexpected EOF)", re.M)
TB = re.compile(r"Traceback \(most recent call last\)")
rows = []
for path in sys.argv[2:]:
    t = pq.read_table(path, columns=["instance_id", "model_name", "target", "exit_status", "trajectory"]).to_pandas()
    for k, r in t.iterrows():
        msgs = list(r.trajectory); step = 0; ev, tb, ed = [], [], []
        for i, m in enumerate(msgs):
            if m["role"] == "ai" and i + 1 < len(msgs) and msgs[i + 1]["role"] == "user":
                obs = msgs[i + 1]["text"] or ""
                viewer = obs.lstrip().startswith("[File:") and "Your proposed edit" not in obs   # file contents shown by the viewer, not an error
                ev.append(int(bool(ERR.search(obs)) and not viewer)); ed.append(int("Your proposed edit has introduced new syntax error" in obs)); tb.append(int(bool(TB.search(obs)))); step += 1
        rows.append(dict(traj=f"{path.split('/')[-1]}:{k}", instance_id=r.instance_id, model=r.model_name, resolved=bool(r.target),
                         exit=r.exit_status, n_steps=step, errors=ev, tracebacks=tb, edit_errors=ed))
df = pd.DataFrame(rows); df.to_parquet(sys.argv[1])
print(len(df), "trajectories;", df.model.value_counts().to_dict())
print("steps median", df.n_steps.median(), "error share", sum(map(sum, df.errors)) / max(1, df.n_steps.sum()))
