"""Prospective high-frequency panel of provider-level LLM prices and availability from OpenRouter's public API.

Run once per day (cron, GitHub Action, or any scheduler).  Each run appends one snapshot per (model, provider endpoint) to
snapshots.csv: price per million input/output tokens, quantization, status, uptime over the last 5 minutes, 30 minutes and
1 day, and latency and throughput when OpenRouter reports them (empty in our test).  Repricing frequency can then be measured directly (days between
price changes), and uptime and latency are capacity-stress proxies.

python collect_openrouter.py [--models meta-llama/llama-3.3-70b-instruct,deepseek/deepseek-r1,...]
No API key is needed for these endpoints.  Be polite: one request per model per run, with a pause.
"""
import argparse, csv, datetime as dt, json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "snapshots.csv")
DEFAULT = ["meta-llama/llama-3.3-70b-instruct", "meta-llama/llama-3.1-70b-instruct", "meta-llama/llama-3.1-8b-instruct",
           "deepseek/deepseek-chat", "deepseek/deepseek-r1", "deepseek/deepseek-chat-v3.1", "deepseek/deepseek-v3.2",
           "qwen/qwen-2.5-72b-instruct", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
FIELDS = ["date", "ts_utc", "model_id", "provider", "tag", "quantization", "prompt_per_m", "completion_per_m", "status",
          "uptime_5m", "uptime_30m", "uptime_1d", "latency_30m", "throughput_30m"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-panel/0.1"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())


def per_m(x):
    return None if x in (None, "") else round(float(x) * 1e6, 6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(DEFAULT))
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    new = not os.path.exists(OUT)
    n = 0
    with open(OUT, "a", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        for m in a.models.split(","):
            try:
                d = get(f"https://openrouter.ai/api/v1/models/{m}/endpoints")["data"]
            except Exception as e:
                print("skip", m, e)
                continue
            for e in d.get("endpoints", []):
                pr = e.get("pricing", {})
                w.writerow(dict(date=now.strftime("%Y-%m-%d"), ts_utc=now.isoformat(timespec="seconds"), model_id=m,
                                provider=e.get("provider_name"), tag=e.get("tag"), quantization=e.get("quantization"),
                                prompt_per_m=per_m(pr.get("prompt")), completion_per_m=per_m(pr.get("completion")), status=e.get("status"),
                                uptime_5m=e.get("uptime_last_5m"), uptime_30m=e.get("uptime_last_30m"), uptime_1d=e.get("uptime_last_1d"),
                                latency_30m=e.get("latency_last_30m"), throughput_30m=e.get("throughput_last_30m")))
                n += 1
            time.sleep(1.0)
    print("appended", n, "rows ->", OUT)


if __name__ == "__main__":
    main()
