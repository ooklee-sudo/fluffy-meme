"""Trace-driven capacity sizing for batched serving (Section 5.4 / Table 1, Table B4).

Each engine holds at most M requests in its batch; every request in service progresses at speed
rho(n) = (1+b)/(1+b*n) (b = beta/alpha) in units of 'isolated service time per unit time'.
A request with work w (isolated service times) finishes when the engine's virtual clock advanced by w.
Excess requests wait FCFS per engine.  Routing: 'random' or 'jsq' (join-the-shortest-queue, "balanced").
Delays are in units of the mean isolated service time of the workload.
"""
import argparse, heapq, collections
import numpy as np


def simulate(arr, work, c, M, b, routing='random', seed=0):
    """arr: sorted arrival times; work: isolated service times. Returns (wait, sojourn) arrays."""
    rng = np.random.default_rng(seed)
    n_req = len(arr)
    rho = lambda n: (1 + b) / (1 + b * n)
    v = np.zeros(c); tl = np.zeros(c); nb = np.zeros(c, int)                # virtual clock, last update, batch size
    fin = [[] for _ in range(c)]                                              # heaps of (finish_virtual, req)
    q = [collections.deque() for _ in range(c)]
    ver = np.zeros(c, int); ev = []                                           # global completion events
    start = np.full(n_req, np.nan); done = np.full(n_req, np.nan)

    def advance(e, t):
        if nb[e] > 0: v[e] += (t - tl[e]) * rho(nb[e])
        tl[e] = t

    def schedule(e):
        ver[e] += 1
        if nb[e] > 0:
            heapq.heappush(ev, (tl[e] + (fin[e][0][0] - v[e]) / rho(nb[e]), e, ver[e]))

    def admit(e, i, t):
        heapq.heappush(fin[e], (v[e] + work[i], i)); nb[e] += 1; start[i] = t

    def complete_until(t_lim):
        while ev and ev[0][0] <= t_lim:
            t, e, vv = heapq.heappop(ev)
            if vv != ver[e]: continue
            advance(e, t)
            _, i = heapq.heappop(fin[e]); nb[e] -= 1; done[i] = t
            while q[e] and nb[e] < M: admit(e, q[e].popleft(), t)
            schedule(e)

    for i in range(n_req):
        t = arr[i]; complete_until(t)
        if routing == 'random': e = int(rng.integers(c))
        else: e = int(np.argmin(nb + np.fromiter((len(x) for x in q), int, c)))
        advance(e, t)
        if nb[e] < M: admit(e, i, t)
        else: q[e].append(i)
        schedule(e)
    complete_until(np.inf)
    return start - arr, done - arr


def size_capacity(arr, work, M, b, target, routing='random', c_max=512, seed=0):
    """Smallest #engines whose tail probability meets `target = (metric, thresh, prob)`.
    metric 'wait' -> P(wait > thresh) <= prob; 'sojourn' -> P(sojourn > thresh) <= prob."""
    metric, thresh, prob = target
    lo, hi = 1, 1
    ok = lambda c: np.mean((lambda w, s: (w if metric == 'wait' else s))(*simulate(arr, work, c, M, b, routing, seed)) > thresh) <= prob
    while hi < c_max and not ok(hi): lo, hi = hi, hi * 2
    if not ok(hi): return None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid): hi = mid
        else: lo = mid
    return hi


# ----- arrival models --------------------------------------------------------------
def poisson_same_rate(arr, rng):
    n = len(arr); T = arr[-1] - arr[0]
    return np.sort(arr[0] + rng.uniform(0, T, n))


def block_bootstrap(arr, work, block, rng):
    """Resample blocks of consecutive interarrivals (with their work) to preserve burst structure."""
    ia = np.diff(arr, prepend=arr[0]); n = len(arr); nblocks = int(np.ceil(n / block))
    starts = rng.integers(0, n - block, nblocks)
    idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
    return np.cumsum(ia[idx]), work[idx]


def load_trace(path, alpha_ms, beta_ms, prefill_ms_per_tok, prompt_col='ContextTokens', gen_col='GeneratedTokens',
               ts_col='TIMESTAMP', max_rows=None):
    """Azure format. Work in isolated service times: (G*(alpha+beta) + P*prefill)/mean."""
    import pandas as pd
    df = pd.read_csv(path, nrows=max_rows)
    t = pd.to_datetime(df[ts_col]); arr = (t - t.iloc[0]).dt.total_seconds().to_numpy()
    iso_ms = df[gen_col].to_numpy() * (alpha_ms + beta_ms) + df[prompt_col].to_numpy() * prefill_ms_per_tok
    mean_s = iso_ms.mean() / 1000.0
    return arr / mean_s, iso_ms / iso_ms.mean(), mean_s      # time in mean-isolated-service-time units


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trace', required=True); ap.add_argument('--alpha-ms', type=float, required=True)
    ap.add_argument('--beta-ms', type=float, required=True); ap.add_argument('--prefill-ms', type=float, required=True)
    ap.add_argument('--M', type=int, required=True); ap.add_argument('--max-rows', type=int, default=None)
    ap.add_argument('--sojourn-mult', type=float, required=True, help='k in P(sojourn > k isolated service times) <= 5%%')
    ap.add_argument('--routing', default='random', choices=['random', 'jsq'])
    ap.add_argument('--block', type=int, default=200); ap.add_argument('--reps', type=int, default=5)
    a = ap.parse_args()
    b = a.beta_ms / a.alpha_ms
    arr, work, mean_s = load_trace(a.trace, a.alpha_ms, a.beta_ms, a.prefill_ms, max_rows=a.max_rows)
    print(f'mean isolated service time = {mean_s:.3f}s, n = {len(arr)}')
    tgt = ('sojourn', a.sojourn_mult, 0.05)
    rng = np.random.default_rng(1)
    out = {'real trace replay': size_capacity(arr, work, a.M, b, tgt, a.routing)}
    ps = [size_capacity(poisson_same_rate(arr, rng), work, a.M, b, tgt, a.routing, seed=s) for s in range(a.reps)]
    out['poisson (median)'] = int(np.median([x for x in ps if x]))
    bs = []
    for s in range(a.reps):
        ar2, w2 = block_bootstrap(arr, work, a.block, rng)
        bs.append(size_capacity(ar2, w2, a.M, b, tgt, a.routing, seed=s))
    out['block bootstrap (median)'] = int(np.median([x for x in bs if x]))
    for k, v in out.items(): print(f'{k:28s} {v}')
    print(f"Poisson understates bootstrap by {1 - out['poisson (median)'] / out['block bootstrap (median)']:.1%}")


if __name__ == '__main__':
    main()
