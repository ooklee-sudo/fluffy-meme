"""Transformer decoder for the rotated surface code vs. MWPM / belief-matching.

Data are generated on the fly with Stim (circuit-level noise), so there is no
dataset to download.  Each detector is one token: its Fourier-encoded (x,y,t)
coordinates plus a learned embedding of its 0/1 outcome.  Position encoding is
coordinate based, so a model trained at one code distance can be evaluated at
another (--eval-d).

Noise mismatch (the setting where a data-driven decoder should win)
  --p            true physical noise rate of the data
  --meas-mult    true reset/measurement error = p * meas_mult
  --data-mult    true data-qubit depolarization = p * data_mult
  --assume-p     uniform noise rate that the MWPM / belief-matching *graph* assumes
                 (default: --p).  With meas_mult/data_mult != 1 or assume_p != p
                 the matching graphs are misspecified; the "oracle" baselines use
                 the true noise model.  --eval-p changes only the TRUE p (drift)
                 while the assumed graph stays fixed.

Modes
  plain    the network predicts the logical flip directly.
  --hybrid MWPM's (assumed-graph) prediction m and weight w are fed to the
           network and it predicts whether MWPM is WRONG (target = obs XOR m);
           final prediction = m XOR flip, so it starts at MWPM quality.

Other
  --baselines-only  no network: MWPM/BM with assumed / calibrated (MWPMc, BMc) / oracle (*) graphs
  --calib-shots N  unlabeled shots for the DEM calibration (default 200000)
  --bm        also evaluate belief-matching baselines (slower)
  --init PATH start from saved weights and keep training (fine-tune after drift)
  --load PATH load weights, skip training, evaluate only
  --ckpt PATH save weights (every 20% and at the end)

Examples
  python qec_decoder.py --smoke --hybrid --bm
  python qec_decoder.py --d 5 --p 0.005 --hybrid --meas-mult 3 --bm --device cuda
  python qec_decoder.py --d 5 --p 0.005 --hybrid --assume-p 0.002 --eval-p 0.002 0.005 0.008 --bm
"""
import argparse
import json
import math
import os
import time

import numpy as np
import pymatching
import stim
import torch
import torch.nn as nn
import torch.nn.functional as F


# ----------------------------------------------------------------- data
def make_circuit(d, rounds, p_gate, p_data, p_reset, p_meas):
    return stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=d,
        rounds=rounds,
        after_clifford_depolarization=p_gate,
        before_round_data_depolarization=p_data,
        after_reset_flip_probability=p_reset,
        before_measure_flip_probability=p_meas,
    )


def noise_params(p, meas_mult=1.0, data_mult=1.0):
    return dict(p_gate=p, p_data=min(p * data_mult, 0.5),
                p_reset=min(p * meas_mult, 0.5), p_meas=min(p * meas_mult, 0.5))


def detector_coords(circ):
    c = circ.get_detector_coordinates()
    return np.array([c[i] for i in range(circ.num_detectors)], dtype=np.float32)  # x, y, t


class Sampler:
    """Samples from the TRUE noise.  Baseline decoders (MWPM / belief-matching) can use
      assumed   graph of uniform noise assume_p            (what a deployed decoder believes)
      oracle    graph of the true noise                    (upper reference, unknowable)
      calib     assumed graph re-weighted from syndrome statistics of `calib_shots`
                unlabeled shots of the true noise          (no oracle knowledge)"""

    def __init__(self, d, rounds, p, meas_mult=1.0, data_mult=1.0, assume_p=None, calib_shots=0):
        self.d, self.rounds, self.p = d, rounds, p
        self.meas_mult, self.data_mult = meas_mult, data_mult
        self.assume_p = p if assume_p is None else assume_p
        self.calib_shots = calib_shots
        self.circ = make_circuit(d, rounds, **noise_params(p, meas_mult, data_mult))
        self.sampler = self.circ.compile_detector_sampler()
        self.coords = detector_coords(self.circ)
        self.mismatch = not (meas_mult == 1.0 and data_mult == 1.0 and self.assume_p == p)
        self.circ_assumed = (make_circuit(d, rounds, **noise_params(self.assume_p))
                             if self.mismatch else self.circ)
        self.calibrated = self.mismatch and calib_shots > 0
        self._cache = {}

    # -- detector error models for the three decoder variants
    def _dem(self, which):
        if which == "oracle":
            return self.circ.detector_error_model(decompose_errors=True)
        if which == "assumed":
            return self.circ_assumed.detector_error_model(decompose_errors=True)
        if ("dem", "calib") not in self._cache:
            self._cache[("dem", "calib")] = self._calibrated_dem()
        return self._cache[("dem", "calib")]

    def _calibrated_dem(self):
        """Estimate every graph-edge probability from detector-pair statistics
        (p_ij = 1/2 - 1/2 sqrt(1 - 4 cov_ij / (1 - 2<x_i> - 2<x_j> + 4<x_i x_j>))),
        then rescale each error mechanism of the assumed DEM by the (geometric mean of
        the) ratio new/old edge probability of its components."""
        dem0 = self._dem("assumed")
        edges = pymatching.Matching.from_detector_error_model(dem0).edges()
        det, _ = self.sampler.sample(self.calib_shots, separate_observables=True)
        x = det.astype(np.float32)
        mean = x.mean(0).astype(np.float64)
        second = (x.T @ x).astype(np.float64) / len(x)
        lo, hi = 1e-6, 0.5 - 1e-6
        new, prod = {}, np.ones(len(mean))
        for u, v, attr in edges:
            if v is None:
                continue
            cuv = second[u, v]
            den = 1 - 2 * mean[u] - 2 * mean[v] + 4 * cuv
            arg = 1 - 4 * (cuv - mean[u] * mean[v]) / den
            pij = float(np.clip(0.5 - 0.5 * math.sqrt(max(arg, 0.0)), lo, hi))
            new[tuple(sorted((u, v)))] = pij
            prod[u] *= 1 - 2 * pij
            prod[v] *= 1 - 2 * pij
        ratio = {}
        for u, v, attr in edges:
            if v is None:
                pn = float(np.clip(0.5 * (1 - (1 - 2 * mean[u]) / prod[u]), lo, hi))
                key = (u,)
            else:
                key = tuple(sorted((u, v)))
                pn = new[key]
            ratio[key] = pn / attr["error_probability"]
        lines = [f"detector D{i}" for i in range(self.circ.num_detectors)]
        for ins in dem0.flattened():
            if ins.type != "error":
                continue
            p = ins.args_copy()[0]
            targets = ins.targets_copy()
            comps = [[]]
            for t in targets:
                if t.is_separator():
                    comps.append([])
                else:
                    comps[-1].append(t)
            rs = []
            for c in comps:
                dets = tuple(sorted(t.val for t in c if t.is_relative_detector_id()))
                if dets:
                    rs.append(ratio.get(dets, 1.0))
            r = float(np.exp(np.mean(np.log(np.maximum(rs, 1e-9))))) if rs else 1.0
            pn = min(max(p * r, 1e-9), 0.499)
            lines.append(f"error({pn}) " + " ".join(str(t) for t in targets))
        return stim.DetectorErrorModel("\n".join(lines))

    def _matching(self, which):
        if ("mw", which) not in self._cache:
            self._cache[("mw", which)] = pymatching.Matching.from_detector_error_model(self._dem(which))
        return self._cache[("mw", which)]

    def sample(self, n):
        det, obs = self.sampler.sample(n, separate_observables=True)
        return det, obs[:, 0]

    def mwpm(self, det, which="assumed"):
        """MWPM prediction (bool) and matching weight (float32) per shot."""
        pred, w = self._matching(which).decode_batch(det, return_weights=True)
        return pred[:, 0].astype(bool), np.asarray(w, dtype=np.float32)

    def belief_matching(self, det, which="assumed"):
        from beliefmatching import BeliefMatching
        if ("bm", which) not in self._cache:
            self._cache[("bm", which)] = BeliefMatching(self._dem(which), max_bp_iters=20)
        return self._cache[("bm", which)].decode_batch(det)[:, 0].astype(bool)


# ---------------------------------------------------------------- model
class FourierPos(nn.Module):
    def __init__(self, dim, n_freq=8):
        super().__init__()
        self.register_buffer("freqs", (2.0 ** torch.arange(n_freq)) * math.pi / 16.0)
        self.proj = nn.Linear(3 * n_freq * 2, dim)

    def forward(self, xyz):  # (N, 3)
        a = xyz[..., None] * self.freqs  # (N, 3, F)
        f = torch.cat([a.sin(), a.cos()], dim=-1).flatten(-2)
        return self.proj(f)


class Decoder(nn.Module):
    def __init__(self, dim=128, layers=4, heads=4, hybrid=False):
        super().__init__()
        self.hybrid = hybrid
        self.amp = False
        self.pos = FourierPos(dim)
        self.val = nn.Embedding(2, dim)
        self.cls = nn.Parameter(torch.zeros(1, 1, dim))
        if hybrid:
            self.m_emb = nn.Embedding(2, dim)
            self.w_proj = nn.Linear(1, dim)
        layer = nn.TransformerEncoderLayer(
            dim, heads, dim * 4, dropout=0.0, batch_first=True, norm_first=True
        )
        self.enc = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.head = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, 1))

    def forward(self, det, coords, m=None, w=None):
        # det: (B, N) bool, coords: (N, 3), m: (B,) bool, w: (B,) float
        x = self.val(det.long()) + self.pos(coords)[None]
        cls = self.cls.expand(len(x), -1, -1)
        if self.hybrid:
            cls = cls + self.m_emb(m.long())[:, None] + self.w_proj(torch.log1p(w)[:, None])[:, None]
        x = torch.cat([cls, x], dim=1)
        return self.head(self.enc(x)[:, 0]).squeeze(-1).float()


def run_batch(model, smp, n, coords, device):
    """Sample n shots; return (logits, obs, mwpm_pred, det), numpy bool except logits."""
    det, obs = smp.sample(n)
    m, w = (smp.mwpm(det) if model.hybrid else (None, None))
    t = lambda a: torch.tensor(a, device=device)
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=model.amp):
        logits = model(t(det), coords, t(m) if m is not None else None,
                       t(w) if w is not None else None)
    return logits, obs, m, det


# ------------------------------------------------------------ train/eval
@torch.no_grad()
def evaluate(model, smp, n, device, bs=1024, with_bm=False):
    """Logical error rates of the network (if model is not None) and the baselines."""
    hybrid = model is not None and model.hybrid
    if model is not None:
        model.eval()
        coords = torch.tensor(smp.coords, device=device)
    c = dict(nn=0, mw=0, mw_or=0, mw_ca=0, bm=0, bm_or=0, bm_ca=0, flip=0, fixed=0, broken=0)
    done = 0
    while done < n:
        b = min(bs, n - done)
        if model is not None:
            logits, obs, m, det = run_batch(model, smp, b, coords, device)
            flip = (logits > 0).cpu().numpy()
            pred = (flip ^ m) if hybrid else flip
            c["nn"] += int((pred != obs).sum())
            if hybrid:
                c["flip"] += int(flip.sum())
                c["fixed"] += int((flip & (m != obs)).sum())
                c["broken"] += int((flip & (m == obs)).sum())
        else:
            det, obs = smp.sample(b)
            m = None
        mw = m if m is not None else smp.mwpm(det)[0]
        c["mw"] += int((mw != obs).sum())
        if smp.mismatch:
            c["mw_or"] += int((smp.mwpm(det, "oracle")[0] != obs).sum())
        if smp.calibrated:
            c["mw_ca"] += int((smp.mwpm(det, "calib")[0] != obs).sum())
        if with_bm:
            c["bm"] += int((smp.belief_matching(det) != obs).sum())
            if smp.mismatch:
                c["bm_or"] += int((smp.belief_matching(det, "oracle") != obs).sum())
            if smp.calibrated:
                c["bm_ca"] += int((smp.belief_matching(det, "calib") != obs).sum())
        done += b
    out = {"d": smp.d, "rounds": smp.rounds, "p": smp.p, "assume_p": smp.assume_p,
           "meas_mult": smp.meas_mult, "data_mult": smp.data_mult, "shots": n,
           "ler_mwpm": c["mw"] / n}
    if model is not None:
        out["ler_nn"] = c["nn"] / n
    if smp.mismatch:
        out["ler_mwpm_oracle"] = c["mw_or"] / n
    if smp.calibrated:
        out["ler_mwpm_calib"] = c["mw_ca"] / n
        out["calib_shots"] = smp.calib_shots
    if with_bm:
        out["ler_bm"] = c["bm"] / n
        if smp.mismatch:
            out["ler_bm_oracle"] = c["bm_or"] / n
        if smp.calibrated:
            out["ler_bm_calib"] = c["bm_ca"] / n
    if hybrid:
        out.update(override_rate=c["flip"] / n, n_fixed=c["fixed"], n_broken=c["broken"])
    return out


def fmt(r):
    parts = []
    if "ler_nn" in r:
        parts.append(f"NN {r['ler_nn']:.4f}")
    parts.append(f"MWPM {r['ler_mwpm']:.4f}")
    for k, name in (("ler_mwpm_calib", "MWPMc"), ("ler_mwpm_oracle", "MWPM*"), ("ler_bm", "BM"),
                    ("ler_bm_calib", "BMc"), ("ler_bm_oracle", "BM*")):
        if k in r:
            parts.append(f"{name} {r[k]:.4f}")
    s = "  ".join(parts)
    if "override_rate" in r:
        s += f"  | override {r['override_rate']:.4f} (fixed {r['n_fixed']}, broken {r['n_broken']})"
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, default=3, help="training code distance")
    ap.add_argument("--rounds", type=int, default=None, help="default: d")
    ap.add_argument("--p", type=float, default=0.005, help="true physical noise rate")
    ap.add_argument("--meas-mult", type=float, default=1.0)
    ap.add_argument("--data-mult", type=float, default=1.0)
    ap.add_argument("--assume-p", type=float, default=None,
                    help="noise rate assumed by the matching graph (default: --p)")
    ap.add_argument("--calib-shots", type=int, default=200000,
                    help="unlabeled shots used to re-estimate the DEM weights (mismatch only)")
    ap.add_argument("--baselines-only", action="store_true",
                    help="no network: evaluate MWPM/BM baselines (assumed/calibrated/oracle)")
    ap.add_argument("--eval-d", type=int, nargs="*", default=None)
    ap.add_argument("--eval-p", type=float, nargs="*", default=None,
                    help="extra TRUE noise levels to evaluate at (drift); assumed graph stays fixed")
    ap.add_argument("--hybrid", action="store_true", help="learn a correction on top of MWPM")
    ap.add_argument("--bm", action="store_true", help="also evaluate belief-matching baselines")
    ap.add_argument("--large", action="store_true",
                    help="preset: dim 256, 6 layers, 8 heads, bs 512, 60000 steps, lr 2e-4")
    ap.add_argument("--no-amp", action="store_true", help="disable bf16 autocast on cuda")
    ap.add_argument("--steps", type=int, default=5000)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--dim", type=int, default=128)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--heads", type=int, default=4)
    ap.add_argument("--eval-n", type=int, default=20000)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--ckpt", default=None, help="save weights (every 20%% and at the end)")
    ap.add_argument("--load", default=None, help="load weights, skip training (evaluate only)")
    ap.add_argument("--init", default=None, help="start from weights and keep training")
    ap.add_argument("--smoke", action="store_true", help="tiny CPU run")
    a = ap.parse_args()
    if a.large:
        a.dim, a.layers, a.heads, a.bs, a.steps, a.lr = 256, 6, 8, 512, 60000, 2e-4
    if a.smoke:
        a.steps, a.bs, a.dim, a.layers, a.eval_n, a.device = 300, 128, 64, 2, 4000, "cpu"
        a.p = 0.01
    if a.out is None and not a.baselines_only:
        tag = ("_hybrid" if a.hybrid else "") + ("_smoke" if a.smoke else "")
        a.out = f"results/qec_decoder{tag}.json"
    rounds = a.rounds or a.d
    assume_p = a.assume_p if a.assume_p is not None else a.p

    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    if a.device == "cuda":
        torch.set_float32_matmul_precision("high")
    mk = lambda d, r, p: Sampler(d, r, p, a.meas_mult, a.data_mult, assume_p, a.calib_shots)
    if a.baselines_only:
        results = []
        for d in (a.eval_d or [a.d]):
            for p in [a.p] + (a.eval_p or []):
                r = evaluate(None, mk(d, d if d != a.d else rounds, p), a.eval_n, a.device,
                             with_bm=a.bm)
                results.append(r)
                print(f"d={d} p={p}: " + fmt(r), flush=True)
        a.out = a.out or "results/qec_baselines.json"
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump({"args": vars(a), "results": results}, open(a.out, "w"), indent=2)
        print("saved", a.out)
        return
    train = mk(a.d, rounds, a.p)
    model = Decoder(a.dim, a.layers, a.heads, a.hybrid).to(a.device)
    model.amp = a.device == "cuda" and not a.no_amp and torch.cuda.is_bf16_supported()
    n_params = sum(p.numel() for p in model.parameters())
    print(f"d={a.d} rounds={rounds} p={a.p} meas_mult={a.meas_mult} data_mult={a.data_mult} "
          f"assume_p={assume_p} mismatch={train.mismatch} detectors={train.circ.num_detectors} "
          f"params={n_params/1e6:.2f}M hybrid={a.hybrid} amp={model.amp} device={a.device}")

    coords = torch.tensor(train.coords, device=a.device)
    history = []
    t0 = time.time()
    if a.load or a.init:
        model.load_state_dict(torch.load(a.load or a.init, map_location=a.device))
        print("loaded", a.load or a.init)
    if a.load:
        a.steps = 0
    else:
        opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=a.steps, pct_start=0.05)
    for step in range(1, a.steps + 1):
        model.train()
        logits, obs, m, _ = run_batch(model, train, a.bs, coords, a.device)
        target = (obs ^ m) if model.hybrid else obs  # hybrid: "is MWPM wrong?"
        loss = F.binary_cross_entropy_with_logits(
            logits, torch.tensor(target, device=a.device, dtype=torch.float32))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % max(1, a.steps // 10) == 0:
            msg = f"step {step}/{a.steps} loss {loss.item():.4f} ({time.time()-t0:.0f}s)"
            if step % max(1, a.steps // 5) == 0 and step < a.steps:  # quick progress check
                r = evaluate(model, train, 4000, a.device)
                history.append({"step": step, **r})
                msg += " | quick eval " + fmt(r)
            print(msg, flush=True)
            if a.ckpt and step % max(1, a.steps // 5) == 0:
                torch.save(model.state_dict(), a.ckpt)

    if a.ckpt and not a.load:
        torch.save(model.state_dict(), a.ckpt)
    results = []
    for d in (a.eval_d or [a.d]):
        for p in [a.p] + (a.eval_p or []):
            r = evaluate(model, mk(d, d if d != a.d else rounds, p), a.eval_n, a.device,
                         with_bm=a.bm)
            results.append(r)
            print(f"eval d={d} p={p}: " + fmt(r), flush=True)

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        json.dump({"args": vars(a), "params": n_params, "train_seconds": time.time() - t0,
                   "history": history, "results": results}, f, indent=2)
    print("saved", a.out)


if __name__ == "__main__":
    main()
