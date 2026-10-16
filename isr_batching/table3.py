"""Table 3: loss of the best flat price versus the best phase-dependent plan as a function of switching speed
(exact Markov chain, Section 4.3).  Phases come from the two-state MMPP fitted to the 2023 code trace.

Demand convention (same as Section 6.2): unpriced demand of phase k is Lam_k = ratio * capacity * rate_k / mean(rate),
capacity = c servers (dedicated) or mubar of the engine (batched).  Loss is reported as a percentage of the welfare of the
best phase-dependent plan.  The dwell times of the MMPP are scaled by f; the mean burst length in service times is
f / (r12 * svc) with r12 the exit rate of the burst phase.

  python table3.py --dedicated --c 7 --N 200
  python table3.py --M 1024 --b 0.00883 --N 2000
"""
import argparse, json, time
import numpy as np
from multiprocessing import Pool
from exact_chain import Chain

# two-state MMPP fitted to the Azure 2023 code trace (capacity_sim.py, fit_mmpp2): rates per second
L1, L2, R12, R21, SVC = 36.7671, 1.6695, 0.133, 0.0035, 1.86   # SVC: mean isolated service time of the dedicated benchmark (s)
BASE_BURST = 1.0 / R12 / SVC                                   # mean burst length in service times (4.04)


def setup(a):
    rate = np.array([L1, L2]) * SVC                            # offered load of each phase in isolated-service units
    pi = np.array([R21, R12]) / (R12 + R21)
    G0 = np.array([[-R12 * SVC, R12 * SVC], [R21 * SVC, -R21 * SVC]])
    if a['dedicated']: M, b, cap = a['c'], 0.0, float(a['c'])
    else:
        M, b = a['M'], a['b']; cap = M * (1 + b) / (1 + b * M)
    Lam = a['ratio'] * cap * rate / (pi * rate).sum()
    return M, b, cap, G0, Lam, pi, rate


def one(job):
    a, f = job
    M, b, cap, G0, Lam, pi, rate = setup(a)
    t0 = time.time()
    ch = Chain(M, b, a['N'], G0, 1.0 / f, a['V'], Lam)
    st = [np.minimum([x * cap, y * cap], Lam) for x, y in ((0.5, 0.1), (0.9, 0.05), (0.7, 0.3), (0.3, 0.02))]
    Wpd, lpd = ch.best_phase_dependent(st)
    Wf, pf, lf = ch.best_flat(np.linspace(0, a['pmax'], a['np']), st[0])
    return dict(f=f, burst=f * BASE_BURST, Wpd=Wpd, Wflat=Wf, loss=Wpd - Wf, rel=100 * (Wpd - Wf) / Wpd,
                p_flat=float(pf), lam_pd=lpd.tolist(), lam_flat=lf.tolist(), seconds=time.time() - t0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dedicated', action='store_true'); ap.add_argument('--c', type=int, default=7)
    ap.add_argument('--M', type=int, default=1024); ap.add_argument('--b', type=float, default=0.00883)
    ap.add_argument('--N', type=int, required=True); ap.add_argument('--V', type=float, default=20.0)
    ap.add_argument('--ratio', type=float, default=1.4)
    ap.add_argument('--pmax', type=float, default=18.0); ap.add_argument('--np', type=int, default=37)
    ap.add_argument('--scales', default='0.005,0.02,0.1,0.5,1,2,5,50', help='dwell-time scale factors f (burst length = f*4.04 service times)')
    ap.add_argument('--procs', type=int, default=4); ap.add_argument('--json', default=None)
    a = vars(ap.parse_args())
    fs = [float(x) for x in a['scales'].split(',')]
    M, b, cap, G0, Lam, pi, rate = setup(a)
    print(f"{'dedicated' if a['dedicated'] else 'batched'} M={M} b={b} capacity={cap:.2f} N={a['N']} V={a['V']} Lam={np.round(Lam,1)} pi={np.round(pi,4)}", flush=True)
    with Pool(a['procs']) as pool:
        res = pool.map(one, [(a, f) for f in fs])
    for r in res:
        print(f"burst {r['burst']:7.2f} service times (f={r['f']:g}):  loss {r['rel']:6.2f}% of W_pd  (abs {r['loss']:.4g})  flat price {r['p_flat']:.2f}  [{r['seconds']:.0f}s]")
    b_ = np.array([r['burst'] for r in res]); l = np.array([r['loss'] for r in res])
    sl = np.diff(np.log(l)) / np.diff(np.log(b_))
    print('local log-log slope of the absolute loss between successive burst lengths:', np.round(sl, 2))
    if a['json']: json.dump(dict(args=a, results=res), open(a['json'], 'w'), indent=1)


if __name__ == '__main__':
    main()
