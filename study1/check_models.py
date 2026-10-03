"""Check that every OpenRouter model id in a models file is currently listed, and print price per million tokens. No key needed (public list).
usage: python check_models.py models_hard.json"""
import json, sys, urllib.request
path = sys.argv[1] if len(sys.argv) > 1 else "models_hard.json"
want = [m for m in json.load(open(path, encoding="utf-8"))["models"] if m.get("base_url", "").startswith("https://openrouter.ai")]
lst = {m["id"]: m for m in json.load(urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=60))["data"]}
bad = 0
for m in want:
    r = lst.get(m["model"])
    if r is None: bad += 1; print(f"MISSING  {m['key']:15s} {m['model']}"); continue
    p = r.get("pricing", {}); print(f"ok       {m['key']:15s} {m['model']:42s} in {float(p.get('prompt', 0)) * 1e6:5.2f} out {float(p.get('completion', 0)) * 1e6:5.2f} USD/M")
print("missing:", bad); sys.exit(1 if bad else 0)
