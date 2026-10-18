"""Offline tests for rewrite_corpus.py using a fake API (no network, no key)."""
import json, os, tempfile
import rewrite_corpus as rc

prices = lambda: {m: (1e-6, 4e-6) for m in rc.MODELS}  # $1/M in, $4/M out
d = tempfile.mkdtemp()
src, out = os.path.join(d, "in.jsonl"), os.path.join(d, "out.jsonl")
with open(src, "w") as f:
    for i in range(30):
        f.write(json.dumps({"id": f"c{i}", "text": "word " * 400}) + "\n")

def fake(model, prompt, max_tokens, key):
    return {"model": model + "-served", "choices": [{"message": {"content": "rewritten"}}],
            "usage": {"prompt_tokens": 500, "completion_tokens": 500, "cost": 0.0025}}

os.environ["OPENROUTER_API_KEY"] = "test"
base = ["--input", src, "--out", out, "--n-cheap", "4", "--n-top", "2", "--workers", "4"]

rc.main(base + ["--dry-run"], call=fake, price_fn=prices)
assert not os.path.exists(out)

rc.main(base, call=fake, price_fn=prices)
recs = [json.loads(l) for l in open(out)]
n_expected = 3 * (5 * 4 + 2 * 2)            # 3 prompts x (5 cheap x 4 + 2 top x 2)
assert len(recs) == n_expected, len(recs)
assert os.path.exists(out + ".manifest.json")

rc.main(base, call=fake, price_fn=prices)    # resume: nothing new
assert len(open(out).readlines()) == n_expected

out2 = os.path.join(d, "out2.jsonl")        # budget cap stops the run
rc.main(["--input", src, "--out", out2, "--n-cheap", "4", "--n-top", "2", "--budget", "0.05",
         "--workers", "1"], call=fake, price_fn=prices)
spent = sum(json.loads(l)["cost_usd"] for l in open(out2))
assert spent <= 0.05, spent
print("OK; records:", n_expected, "| capped run spent:", round(spent, 4))
