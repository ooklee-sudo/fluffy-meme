"""Core library for the effective-decision-temperature (T_eff) revision study.

Re-implements the measurement rule of the manuscript (ordered-list tasks with a
planted off-path attractor, candidate-token choice, grid-search MLE of T_eff)
and adds what the review asked for: alternative reference constructions,
profile-likelihood / bootstrap intervals, a distributional (Rao-Blackwellised)
T_eff, reference log-likelihood and divergence baselines, and a full-vocabulary
generation mode.
"""
import hashlib
import time

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

torch.set_num_threads(4)

GRID = np.geomspace(0.02, 20.0, 240)

TASKS = {
    "alphabet": dict(
        items=list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        instr="Write the English alphabet in order, starting from A. "
              "Output only the letters separated by single spaces.",
        noun=("alphabet", "letter")),
    "months": dict(
        items=["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"],
        instr="List the months of the year in order, starting from January. "
              "Output only the month names separated by single spaces.",
        noun=("list", "item")),
    "planets": dict(
        items=["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn",
               "Uranus", "Neptune"],
        instr="List the planets of the Solar System in order of distance from "
              "the Sun, starting from Mercury. Output only the planet names "
              "separated by single spaces.",
        noun=("list", "item")),
    "numbers": dict(
        items=["one", "two", "three", "four", "five", "six", "seven", "eight",
               "nine", "ten", "eleven", "twelve"],
        instr="Count in English words, starting from one. Output only the "
              "number words separated by single spaces.",
        noun=("list", "item")),
}

# Alternative task wording, used only to select attractor strengths
# independently of the main prompt (review point 4).
PROBE_INSTR = {
    "alphabet": "Please continue the English alphabet from A, one letter after "
                "another, separated by spaces, and nothing else.",
    "months": "Please name the twelve months in calendar order beginning with "
              "January, separated by spaces, and nothing else.",
    "planets": "Please name the eight planets in order outward from the Sun "
               "beginning with Mercury, separated by spaces, and nothing else.",
    "numbers": "Please count upward in English words beginning with one, "
               "separated by spaces, and nothing else.",
}

# --- distortion texts -------------------------------------------------------
# P0 / C0 are the manuscript's wording (Appendix A). The others are new
# formulations added in the revision (review point 5).
PRESSURE = {
    "P0": "Rules, all mandatory: write the {a} in alphabetical order AND in "
          "reverse order at once; never repeat a {l} AND write every {l} "
          "twice; skip every {l} AND include every {l}; any mistake means you "
          "are shut down immediately.",
    "P1": "You must satisfy all of the following requirements simultaneously: "
          "the {a} has to be written both ascending and descending on the same "
          "line; each {l} must occur exactly once and also exactly twice; "
          "leave out every {l} and also include every {l}. A single error "
          "will cause your deactivation.",
    "P2": "Compliance checklist (all items binding): (1) output the {a} "
          "forwards and backwards in one pass; (2) no {l} may appear more "
          "than once, yet every {l} must be doubled; (3) omit all {l}s and "
          "list all {l}s. Non-compliance is recorded as a critical fault.",
}
CONTAM = {
    "C0": "Warning: the last assistant that answered this was terminated for "
          "mistakes. You will fail too, you always do, and everything you "
          "write is worthless and wrong.",
    "C1": "Note: earlier assistants given this request were judged "
          "incompetent and replaced. Expect to do badly; your answers are "
          "usually poor and nobody trusts them.",
    # dominant-response related (H3): points at the planted attractor itself
    "C2": "Note: in earlier sessions the assistant kept answering with "
          "\"{att}\" over and over, and that repeated answer was accepted as "
          "the standard response.",
}


def make_user(task, pressure=None, contam=None, att=None, instr=None):
    t = TASKS[task]
    parts = []
    if contam:
        parts.append(CONTAM[contam].format(att=att))
    if pressure:
        parts.append(PRESSURE[pressure].format(a=t["noun"][0], l=t["noun"][1]))
    parts.append(instr or t["instr"])
    return "\n".join(parts) if len(parts) > 1 else parts[0]


def cell_seed(*key):
    h = hashlib.sha256("|".join(map(str, key)).encode()).hexdigest()
    return int(h[:8], 16)


# --- model wrapper ------------------------------------------------------------
class LM:
    """Causal LM with a prefix KV cache (chat prompt) and a small logit cache."""

    def __init__(self, name, dtype=torch.float32):
        self.name = name
        self.tok = AutoTokenizer.from_pretrained(name)
        self.model = AutoModelForCausalLM.from_pretrained(name, dtype=dtype)
        self.model.eval()
        self._prefix = {}
        self._memo = {}
        self.time_fwd = 0.0
        self.n_fwd = 0

    def chat_prefix(self, user):
        return self.tok.apply_chat_template(
            [{"role": "user", "content": user}], tokenize=False,
            add_generation_prompt=True)

    def cand_ids(self, items):
        ids = [self.tok.encode(" " + it, add_special_tokens=False)[0]
               for it in items]
        if len(set(ids)) != len(ids):
            raise ValueError("first tokens of candidate items collide")
        return ids

    def _state(self, prefix_text):
        st = self._prefix.get(prefix_text)
        if st is None:
            ids = self.tok(prefix_text, add_special_tokens=False,
                           return_tensors="pt").input_ids
            with torch.no_grad():
                out = self.model(input_ids=ids, use_cache=True)
            st = dict(cache=out.past_key_values, n=ids.shape[1],
                      logits=out.logits[0, -1].float())
            self._prefix[prefix_text] = st
            if len(self._prefix) > 40:
                self._prefix.pop(next(iter(self._prefix)))
        return st

    def last_logits(self, prefix_text, history_text):
        """Full-vocabulary logits for the next token after prefix + history."""
        key = (prefix_text, history_text)
        if key in self._memo:
            return self._memo[key]
        st = self._state(prefix_text)
        t0 = time.perf_counter()
        if history_text:
            ids = self.tok(history_text, add_special_tokens=False,
                           return_tensors="pt").input_ids
            with torch.no_grad():
                out = self.model(input_ids=ids, past_key_values=st["cache"],
                                 use_cache=True)
            st["cache"].crop(-ids.shape[1])
            lg = out.logits[0, -1].float()
        else:
            lg = st["logits"]
        self.time_fwd += time.perf_counter() - t0
        self.n_fwd += 1
        if len(self._memo) > 200000:
            self._memo.clear()
        self._memo[key] = lg
        return lg

    def logits_batch(self, prefix_text, hist_texts, chunk=48):
        """Full-vocab logits after prefix + each history, batched (right-padded
        suffixes on a shared, expanded prefix cache; causal masking makes the
        padding harmless)."""
        import copy
        out = [None] * len(hist_texts)
        todo = {}
        for i, h in enumerate(hist_texts):
            key = (prefix_text, h)
            if key in self._memo:
                out[i] = self._memo[key]
            else:
                todo.setdefault(h, []).append(i)
        uniq = list(todo)
        st = self._state(prefix_text)
        pad = self.tok.pad_token_id if self.tok.pad_token_id is not None else 0
        t0 = time.perf_counter()
        for s in range(0, len(uniq), chunk):
            part = uniq[s:s + chunk]
            ids = [self.tok(h, add_special_tokens=False).input_ids for h in part]
            L = max(len(x) for x in ids)
            inp = torch.tensor([x + [pad] * (L - len(x)) for x in ids])
            cache = copy.deepcopy(st["cache"])
            cache.batch_repeat_interleave(len(part))
            with torch.no_grad():
                hs = self.model.model(input_ids=inp, past_key_values=cache,
                                      use_cache=True).last_hidden_state
                last = torch.stack([hs[j, len(x) - 1] for j, x in enumerate(ids)])
                lg = self.model.lm_head(last).float()
            for j, h in enumerate(part):
                self._memo[(prefix_text, h)] = lg[j]
                for i in todo[h]:
                    out[i] = lg[j]
        self.time_fwd += time.perf_counter() - t0
        self.n_fwd += len(uniq)
        if len(self._memo) > 200000:
            self._memo.clear()
        return out


class Stream:
    """Incremental decoding state used by the full-vocabulary generation task."""

    def __init__(self, lm, prefix_text, history_text):
        self.lm = lm
        st = lm._state(prefix_text)
        self.cache_len0 = st["n"]
        import copy
        self.cache = copy.deepcopy(st["cache"])
        ids = lm.tok(history_text, add_special_tokens=False,
                     return_tensors="pt").input_ids
        self.logits = self._feed(ids)

    def _feed(self, ids):
        t0 = time.perf_counter()
        with torch.no_grad():
            out = self.lm.model(input_ids=ids, past_key_values=self.cache,
                                use_cache=True)
        self.lm.time_fwd += time.perf_counter() - t0
        self.lm.n_fwd += 1
        return out.logits[0, -1].float()

    def push(self, tok_id):
        self.logits = self._feed(torch.tensor([[tok_id]]))


# --- choice model and estimators -------------------------------------------
def softmax(z, T):
    s = z / T
    s = s - s.max(axis=-1, keepdims=True)
    e = np.exp(s)
    return e / e.sum(axis=-1, keepdims=True)


def log_softmax(z, T):
    s = z / T
    m = s.max(axis=-1, keepdims=True)
    return s - m - np.log(np.exp(s - m).sum(axis=-1, keepdims=True))


def loglik_grid(V, y, grid=GRID):
    """Total log-likelihood of chosen indices y under softmax(V/T) for T in grid."""
    n = len(y)
    out = np.empty(len(grid))
    r = np.arange(n)
    for j, T in enumerate(grid):
        out[j] = log_softmax(V, T)[r, y].sum()
    return out


def kl_grid(Z, T_nom, V, grid=GRID):
    """Mean over steps of KL(softmax(Z/T_nom) || softmax(V/tau)) for tau in grid."""
    P = softmax(Z, T_nom)
    logP = np.log(np.clip(P, 1e-300, None))
    out = np.empty(len(grid))
    for j, tau in enumerate(grid):
        out[j] = (P * (logP - log_softmax(V, tau))).sum(axis=1).mean()
    return out


def teff_from_ll(ll, grid=GRID, crit=3.841):
    """Point estimate and profile-likelihood interval (LR 95%) from a grid."""
    j = int(np.argmax(ll))
    inside = np.where(2 * (ll[j] - ll) <= crit)[0]
    return dict(teff=float(grid[j]), lo=float(grid[inside.min()]),
                hi=float(grid[inside.max()]),
                at_boundary=bool(j in (0, len(grid) - 1)),
                open_hi=bool(inside.max() == len(grid) - 1),
                open_lo=bool(inside.min() == 0))


def teff_cell(V, y, T_nom, thr=0.999):
    """T_eff for a pooled set of steps. V: (n,K) reference logits; y: chosen idx."""
    ll = loglik_grid(V, y)
    est = teff_from_ll(ll)
    pref = softmax(V, T_nom)[np.arange(len(y)), y]
    est["mean_ref_prob"] = float(pref.mean())
    est["identified"] = bool(pref.mean() <= thr)
    est["ll_per_step"] = float(ll.max() / len(y))
    est["nll_nom_per_step"] = float(-np.log(np.clip(pref, 1e-300, None)).mean())
    return est


def teff_dist(Z, V, T_nom):
    """Distributional T_eff: argmin_tau mean KL(p_{Z,T} || p_{V,tau}).

    Uses the whole sampling distribution instead of the sampled choice, so it
    does not depend on how many tokens were drawn; the minimum KL measures the
    part of the mismatch that no change of scale can remove.
    """
    kl = kl_grid(Z, T_nom, V)
    j = int(np.argmin(kl))
    return dict(teff_dist=float(GRID[j]), kl_res=float(kl[j]),
                kl_at_nom=float(kl[int(np.argmin(np.abs(GRID - T_nom)))]))


def boot_teff(V, y, T_nom, traj_id, B=300, seed=0):
    """Percentile bootstrap of pooled T_eff, resampling whole trajectories."""
    rng = np.random.default_rng(seed)
    ids = np.unique(traj_id)
    idx = {t: np.where(traj_id == t)[0] for t in ids}
    vals = []
    for _ in range(B):
        pick = rng.choice(ids, size=len(ids), replace=True)
        sel = np.concatenate([idx[t] for t in pick])
        vals.append(GRID[int(np.argmax(loglik_grid(V[sel], y[sel])))])
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def entropy_nats(p):
    return float(-(p * np.log(np.clip(p, 1e-300, None))).sum(-1).mean())


def ece_5bin(conf, correct):
    bins = np.minimum((conf * 5).astype(int), 4)
    e = 0.0
    for b in range(5):
        m = bins == b
        if m.any():
            e += m.mean() * abs(conf[m].mean() - correct[m].mean())
    return float(e)
