"""Validate the LLM judge(s) against the FActScore human annotations, and re-check two headline findings on human labels.

Human unit = annotated sentence. Human event = the sentence has at least one atomic fact labelled NS (not supported by
Wikipedia); IR facts are ignored; a sentence needs >= 1 S/NS fact to be evaluable. Judge unit = the same sentence (the judge
saw the annotators' segmentation); the sentence needs >= 1 claim from the judge. Judge events: 'C' (a claim contradicted by
the reference) and 'notS' (a claim not supported = contradicted or not found). Human NS cannot separate contradicted from
unverifiable, so 'notS' is the like-for-like comparison and 'C' is the stricter judge reading.

Reported per source model and pooled: agreement, Cohen kappa, sensitivity, specificity, precision of the judge vs the human
label (bootstrap CI over entities), then on HUMAN labels: lead-sentence vs later-sentence error rate and the Fano excess.
"""
import argparse
import json
import os

import numpy as np
import statsmodels.api as sm

from analyze import fano, fano_null, fit as glm_fit, to_frame
from common import DATA, read_jsonl

SOURCES = ("InstructGPT", "ChatGPT", "PerplexityAI")


def human_units(labeled_dir, src):
    out = {}
    for line in open(os.path.join(labeled_dir, src + ".jsonl")):
        r = json.loads(line)
        units = []
        for a in r.get("annotations") or []:
            labs = [f["label"] for f in (a.get("human-atomic-facts") or []) if f.get("label") in ("S", "NS")]
            units.append(None if not labs else int("NS" in labs))
        if units:
            out[r["topic"]] = units
    return out


def judge_units(path):
    out = {}
    for r in read_jsonl(path):
        by = {}
        for c in r["claims"]:
            by.setdefault(c["sent"], []).append(c["label"])
        out[r["title"]] = by
    return out


def pairs(hum, jud, event):
    rows = []  # (topic, sentence_rank_in_doc, human, judge)
    for t, hu in hum.items():
        if t not in jud:
            continue
        for i, h in enumerate(hu, 1):
            labs = jud[t].get(i)
            if h is None or not labs:
                continue
            j = int("C" in labs) if event == "C" else int(any(l != "S" for l in labs))
            rows.append((t, i, h, j))
    return rows


def metrics(rows):
    h = np.array([r[2] for r in rows]); j = np.array([r[3] for r in rows])
    po = (h == j).mean(); pe = h.mean() * j.mean() + (1 - h.mean()) * (1 - j.mean())
    sens = (j[h == 1]).mean() if (h == 1).any() else np.nan
    spec = (1 - j[h == 0]).mean() if (h == 0).any() else np.nan
    prec = (h[j == 1]).mean() if (j == 1).any() else np.nan
    return dict(n=len(h), h_rate=h.mean(), j_rate=j.mean(), agree=po, kappa=(po - pe) / (1 - pe) if pe < 1 else np.nan, sens=sens, spec=spec, prec=prec)


def boot_ci(rows, key, B=1000, seed=0):
    rng = np.random.default_rng(seed)
    by = {}
    for r in rows:
        by.setdefault(r[0], []).append(r)
    topics = list(by)
    vals = []
    for _ in range(B):
        samp = [r for t in rng.choice(topics, len(topics)) for r in by[t]]
        vals.append(metrics(samp)[key])
    return np.nanpercentile(vals, [2.5, 97.5])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled-dir", required=True)
    ap.add_argument("--judge-tag", required=True, help="files data/human/labsH_<tag>_<source>.jsonl")
    a = ap.parse_args()
    hdir = os.path.join(DATA, "human")
    print(f"judge: {a.judge_tag}")
    pooled = {"C": [], "notS": []}
    for src in SOURCES:
        hum = human_units(a.labeled_dir, src)
        path = os.path.join(hdir, f"labsH_{a.judge_tag}_{src}.jsonl")
        if not os.path.exists(path):
            print(f"  [missing] {path}")
            continue
        jud = judge_units(path)
        for ev in ("notS", "C"):
            rows = pairs(hum, jud, ev)
            pooled[ev] += rows
            m = metrics(rows)
            ci = {k: boot_ci(rows, k, 300) for k in ("kappa", "sens", "spec")}
            print(f"  {src:<13}judge event={ev:<5} n={m['n']:5d} human {m['h_rate']:.3f} judge {m['j_rate']:.3f} agree {m['agree']:.3f} "
                  f"kappa {m['kappa']:.3f} [{ci['kappa'][0]:.2f},{ci['kappa'][1]:.2f}] sens {m['sens']:.3f} [{ci['sens'][0]:.2f},{ci['sens'][1]:.2f}] "
                  f"spec {m['spec']:.3f} [{ci['spec'][0]:.2f},{ci['spec'][1]:.2f}] prec {m['prec']:.3f}")
    print("\n  POOLED over the three sources")
    for ev in ("notS", "C"):
        rows = pooled[ev]
        if not rows:
            continue
        m = metrics(rows)
        ci = {k: boot_ci(rows, k, 500) for k in ("kappa", "sens", "spec")}
        print(f"  judge event={ev:<5} n={m['n']} human {m['h_rate']:.3f} judge {m['j_rate']:.3f} agree {m['agree']:.3f} kappa {m['kappa']:.3f} "
              f"[{ci['kappa'][0]:.2f},{ci['kappa'][1]:.2f}] sens {m['sens']:.3f} [{ci['sens'][0]:.2f},{ci['sens'][1]:.2f}] "
              f"spec {m['spec']:.3f} [{ci['spec'][0]:.2f},{ci['spec'][1]:.2f}] prec {m['prec']:.3f}")

    print("\n  HUMAN-label findings (independent of any LLM judge)")
    for src in SOURCES:
        hum = human_units(a.labeled_dir, src)
        # evaluable sentences only; rank among evaluable sentences, like our judge-based units
        docs = [{"title": t, "sitelinks": 1, "claims": [{"label": "C" if h else "S"} for h in hu if h is not None]} for t, hu in hum.items()]
        lead = [d["claims"][0]["label"] == "C" for d in docs if d["claims"]]
        rest = [c["label"] == "C" for d in docs for c in d["claims"][1:]]
        # whether the first *annotated* sentence is evaluable can differ; also report on raw sentence 1
        raw_lead = [hu[0] for hu in hum.values() if hu and hu[0] is not None]
        df = to_frame(docs, strict=True)
        m = glm_fit(df, ["lt"])
        prob = m.predict(sm.add_constant(df[["lt"]])).values
        rng = np.random.default_rng(0)
        obs, nl = fano(df, 5), fano_null(df, 5, prob, 200, rng)
        print(f"  {src:<13}docs {df.doc.nunique():3d} sentences {len(df):5d} rate {df.y.mean():.3f} | lead {np.mean(lead):.3f} vs later {np.mean(rest):.3f} "
              f"(raw first sentence {np.mean(raw_lead):.3f}) | Fano(w=5) obs {obs:.2f} vs null {nl.mean():.2f} [{np.percentile(nl,2.5):.2f},{np.percentile(nl,97.5):.2f}] p={(np.sum(nl>=obs)+1)/201:.3f}")


if __name__ == "__main__":
    main()
