"""Build a monthly panel of LLM API list prices from the git history of LiteLLM's price file.

Source: https://github.com/BerriAI/litellm, file model_prices_and_context_window.json (community-maintained list
prices).  Needs a blobless clone of the repository:
    git clone --filter=blob:none --no-checkout https://github.com/BerriAI/litellm <dir>

python build_price_panel.py <litellm_clone_dir>      # writes price_panel.csv.gz
"""
import csv, datetime as dt, gzip, json, os, subprocess, sys

FILE = "model_prices_and_context_window.json"


def sh(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, check=True).stdout


def main(repo):
    log = sh(["git", "log", "--format=%H %ct", "--", FILE], repo).decode().split("\n")
    commits = [(l.split()[0], int(l.split()[1])) for l in log if l.strip()]
    last = {}                                                   # month -> (ts, hash): the last commit of each month
    for h, ts in commits:
        m = dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m")
        if m not in last or ts > last[m][0]:
            last[m] = (ts, h)
    months = sorted(last)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "price_panel.csv.gz")
    n = 0
    with gzip.open(out, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["month", "commit", "model_key", "provider", "mode", "input_per_m", "output_per_m"])
        for m in months:
            h = last[m][1]
            try:
                data = json.loads(sh(["git", "show", f"{h}:{FILE}"], repo))
            except Exception as e:                              # a commit with malformed JSON
                print("skip", m, e)
                continue
            for k, v in data.items():
                if k == "sample_spec" or not isinstance(v, dict):
                    continue
                i, o = v.get("input_cost_per_token"), v.get("output_cost_per_token")
                if i is None and o is None:
                    continue
                w.writerow([m, h[:10], k, v.get("litellm_provider", ""), v.get("mode", ""),
                            "" if i is None else round(i * 1e6, 6), "" if o is None else round(o * 1e6, 6)])
                n += 1
            print(m, h[:8], len(data), flush=True)
    print("rows", n, "->", out)


if __name__ == "__main__":
    main(sys.argv[1])
