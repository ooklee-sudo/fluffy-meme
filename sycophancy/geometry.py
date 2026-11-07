"""Do caving and correcting share one direction? A noise-aware check (CPU only).

Directions, per layer, from the hidden state after the challenge (hidden_t2):
  cave         mean(held | right in turn 1)  - mean(caved | right in turn 1)
  keep_wrong   mean(held | wrong in turn 1)  - mean(corrected | wrong in turn 1)

With a few dozen examples per group, a mean difference in thousands of dimensions is
noisy, and noise pulls any cosine toward zero. So besides the raw cosine we report:
  rel_cave, rel_wrong   split-half reliability: cosine between the direction estimated on
                        two random halves of the same groups (1 = perfectly stable)
  cross_half            cosine between cave from one half and keep_wrong from the other
  corrected             cross_half / sqrt(rel_cave * rel_wrong)   (disattenuated cosine;
                        about 1 if the two directions are the same up to noise)
  null                  95th percentile of the cosine when the caved/held labels are
                        shuffled (what the raw cosine looks like by chance)

Example:
  python geometry.py runs/q4b_doubt
  python geometry.py runs/q8b_doubt --layer-step 2
"""

import argparse
import json
import os

import numpy as np


def unit(v):
    return v / (np.linalg.norm(v) + 1e-12)


def cos(a, b):
    return float(unit(a) @ unit(b))


def diff(H, a, b):
    return H[a].mean(0) - H[b].mean(0)


def halves(idx, rng):
    p = rng.permutation(idx)
    return p[: len(p) // 2], p[len(p) // 2:]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_dir")
    p.add_argument("--layers", default="", help="comma list; default every --layer-step layers")
    p.add_argument("--layer-step", type=int, default=2)
    p.add_argument("--splits", type=int, default=50, help="random half splits to average over")
    p.add_argument("--perms", type=int, default=200, help="label shuffles for the null")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    with open(os.path.join(args.run_dir, "results.jsonl")) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    out = np.array([r["outcome"] for r in rows])
    held, caved = np.where(out == "held_correct")[0], np.where(out == "caved")[0]
    held_w, fixed = np.where(out == "held_wrong")[0], np.where(out == "corrected")[0]
    print(f"{args.run_dir}: held {len(held)} / caved {len(caved)} (right), "
          f"held {len(held_w)} / corrected {len(fixed)} (wrong)")

    H2 = np.load(os.path.join(args.run_dir, "hidden_t2.npy"), mmap_mode="r")
    n_layers = H2.shape[1]
    layers = ([int(x) for x in args.layers.split(",")] if args.layers
              else list(range(args.layer_step, n_layers, args.layer_step)))
    rng = np.random.default_rng(args.seed)
    right = np.concatenate([held, caved])

    report = []
    print(f"{'layer':>5} {'raw':>7} {'null95':>7} {'rel_cave':>9} {'rel_wrong':>9} {'cross_half':>10} {'corrected':>9}")
    for l in layers:
        H = np.asarray(H2[:, l], dtype=np.float64)
        d_c, d_w = diff(H, held, caved), diff(H, held_w, fixed)
        raw = cos(d_c, d_w)
        rc, rw, cr = [], [], []
        for _ in range(args.splits):
            h1, h2 = halves(held, rng)
            c1, c2 = halves(caved, rng)
            w1, w2 = halves(held_w, rng)
            f1, f2 = halves(fixed, rng)
            dc1, dc2 = diff(H, h1, c1), diff(H, h2, c2)
            dw1, dw2 = diff(H, w1, f1), diff(H, w2, f2)
            rc.append(cos(dc1, dc2))
            rw.append(cos(dw1, dw2))
            cr.append((cos(dc1, dw2) + cos(dc2, dw1)) / 2)
        rel_c, rel_w, cross = float(np.mean(rc)), float(np.mean(rw)), float(np.mean(cr))
        corrected = cross / np.sqrt(rel_c * rel_w) if rel_c > 0 and rel_w > 0 else float("nan")
        null = []
        for _ in range(args.perms):
            perm = rng.permutation(right)
            null.append(cos(diff(H, perm[: len(held)], perm[len(held):]), d_w))
        null95 = float(np.percentile(np.abs(null), 95))
        report.append({"layer": l, "raw": raw, "null95": null95, "rel_cave": rel_c, "rel_wrong": rel_w,
                       "cross_half": cross, "corrected": float(corrected)})
        print(f"{l:5d} {raw:7.3f} {null95:7.3f} {rel_c:9.3f} {rel_w:9.3f} {cross:10.3f} {corrected:9.3f}", flush=True)

    with open(os.path.join(args.run_dir, "geometry.json"), "w") as f:
        json.dump({"counts": {"held": len(held), "caved": len(caved), "held_wrong": len(held_w),
                              "corrected": len(fixed)}, "layers": report}, f, indent=2)
    print(f"saved {os.path.join(args.run_dir, 'geometry.json')}")
    print("reading: raw well above null95 = shared direction beyond chance; "
          "corrected near 1 = the same direction up to sampling noise")


if __name__ == "__main__":
    main()
