"""Stackelberg-style evasion model calibrated on the measured white-box attack.
A machine-using author chooses evasion effort e in [0,1] at cost (kappa/2) e^2 and wins B if the paper is not detected, loses P if it is:
   u(e) = B(1-d(e)) - P d(e) - (kappa/2) e^2     =>   maximise  -(B+P) d(e) - (kappa/2) e^2.
With m = (B+P)/kappa, the author minimises m*d(e) + e^2/2.  d(e) = detection rate (share of machine papers flagged at 5% FPR) at effort e,
interpolated from the attack experiment (mixture of generators).  Linear case d(e) = d0 (1-e): e* = min(1, m*d0), d(e*) = d0 (1 - m*d0)."""
import json, numpy as np
r = json.load(open("results_attack.json"))
E = np.array([0, .25, .5, .75, 1.0]); d_mix = np.mean([[r[g][str(e)][1] for e in E] for g in r], axis=0)
rob = np.array([0.34, 0.33, 0.33, 0.33, 0.33])         # detector on the two hard-to-edit events (attack_robust.txt, mixture det@5%FPR)
grid = np.linspace(0, 1, 1001)
def eq(d, m):
    dd = np.interp(grid, E, d); k = int(np.argmin(m * dd + grid ** 2 / 2)); return grid[k], dd[k]
print("measured detection (mixture, share flagged at 5% FPR) vs evasion effort e:", dict(zip(E.tolist(), np.round(d_mix, 2).tolist())))
print("\nEquilibrium evasion e* and detection d(e*) as the stakes-to-evasion-cost ratio m = (B+P)/kappa rises")
print(f"{'m':>6s} | {'full screen: e*':>16s} {'d(e*)':>7s} | {'hard-to-edit only: e*':>22s} {'d(e*)':>7s} | better design")
rows = []
for m in (0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8):
    e1, d1 = eq(d_mix, m); e2, d2 = eq(rob, m)
    rows.append((m, e1, d1, e2, d2)); print(f"{m:6.2f} | {e1:16.2f} {d1:7.2f} | {e2:22.2f} {d2:7.2f} | {'full' if d1 >= d2 else 'hard-to-edit'}")
cross = next((m for m in np.linspace(0.01, 8, 800) if eq(d_mix, m)[1] < eq(rob, m)[1]), None)
print(f"\nhard-to-edit design overtakes the full screen at m ~ {cross:.2f}")
print("\nlinear case: d(e*) = d0 (1 - m d0) is maximised at d0 = 1/(2m); e.g. m=1 -> d0*=0.50, d(e*)=0.25 ; m=2 -> d0*=0.25, d(e*)=0.125")
json.dump(dict(E=E.tolist(), d_mix=d_mix.tolist(), eq=rows, cross=cross), open("results_strategic.json", "w"))
