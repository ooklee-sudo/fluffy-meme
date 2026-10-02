"""List the model ids a provider offers, so that the exact name can be copied into run_small.bat.
usage: python list_models.py openai|gemini|openrouter [filter words ...]
Keys are read from environment variables: OPENAI_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY (OpenRouter lists models without a key and shows prices).
Example: python list_models.py openrouter 8b instruct
"""
import json, os, sys, urllib.request

PROV = {"openai": ("https://api.openai.com/v1/models", "OPENAI_API_KEY"),
        "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/models", "GEMINI_API_KEY"),
        "openrouter": ("https://openrouter.ai/api/v1/models", "OPENROUTER_API_KEY")}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in PROV:
        sys.exit(__doc__)
    url, keyvar = PROV[sys.argv[1]]; words = [w.lower() for w in sys.argv[2:]]
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + os.environ.get(keyvar, "")})
    data = json.load(urllib.request.urlopen(req, timeout=60))["data"]
    rows = []
    for m in data:
        mid = m.get("id", "")
        if all(w in mid.lower() for w in words):
            p = m.get("pricing") or {}
            price = f"  in ${float(p['prompt']) * 1e6:.2f} / out ${float(p['completion']) * 1e6:.2f} per 1M tokens" if p.get("prompt") not in (None, "") and p.get("completion") not in (None, "") else ""
            rows.append(mid + price)
    print(f"{len(rows)} models" + (f" matching {words}" if words else ""))
    print("\n".join(sorted(rows)[:200]))

if __name__ == "__main__":
    main()
