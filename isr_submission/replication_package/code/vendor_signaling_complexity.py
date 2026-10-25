"""Outcome-based pricing under private reach, with task complexity.

Extends vendor_signaling.py: a share `lam` of the firms have hard tasks where the AI's reach is scaled by
`delta` < 1 (reach ratio A_theta * delta).  Firms know their own task type but not the vendor type; the vendor
cannot condition the contract on task type.  Human technology is the same in both segments (isolates the AI gradient).

Run: python3 vendor_signaling_complexity.py
"""
import os
import numpy as np
import vendor_model as VM

a, b, B, c0 = VM.a, VM.b, VM.B, VM.c0
kv = float(os.environ.get("KV", VM.kv))
h, FG, W = VM.h, VM.FGRID, VM.W
AL, AH, q = 0.60, 1.00, 0.5
Abar = q * AH + (1 - q) * AL
S_H = FG * a * h(a * b * FG / 1.0)
rs = np.linspace(0.02, 3.0, 300)
ps = np.linspace(kv + 0.01, 3.0, 300)


def outcome_seg(r, A_true, Ab, g):
    eff = FG - r
    ok = eff > 0
    kap = np.where(ok, Ab * g * a * B * b * np.maximum(eff, 1e-9) / c0, 0.0)
    S_L = np.where(ok, np.maximum(eff, 0) * Ab * g * a * h(kap), 0.0)
    adopt = ok & (S_L >= S_H) & (kap > 1)
    T = np.where(kap > 1, np.log(np.maximum(kap, 1e-12)) / (B * b), 0.0)
    found = A_true * g * a * (1 - 1.0 / np.maximum(kap, 1.0))
    return float((adopt * (r * found - kv * T) * W).sum()), float((adopt * W).sum())


def usage_seg(p, Ab, g):
    cL = c0 + p
    adopt = FG * (Ab * g * a) * h(Ab * g * a * B * b * FG / cL) > S_H + 1e-9      # strict: ties at zero are not adoption
    T = VM.Tstar(Ab * g * a, B * b, cL, FG)
    return float((adopt * (p - kv) * T * W).sum()), float((adopt * W).sum())


def market(lam, delta):
    """Return a function (r, A_true, Ab) -> (profit, share_easy, share_hard) for the mixed population."""
    def f(r, A_true, Ab):
        pe, se = outcome_seg(r, A_true, Ab, 1.0)
        ph, sh = outcome_seg(r, A_true, Ab, delta)
        return (1 - lam) * pe + lam * ph, se, sh
    return f


def analyse(lam, delta, verbose=True):
    m = market(lam, delta)
    P = {(t, x): np.array([m(r, t, x)[0] for r in rs]) for t in (AL, AH) for x in (AL, AH, Abar)}
    iL, iH = P[(AL, AL)].argmax(), P[(AH, AH)].argmax()
    feas = (P[(AL, AH)] <= P[(AL, AL)][iL] + 1e-12) & (P[(AH, AH)] >= P[(AH, AL)][iL] - 1e-12)
    out = dict(lam=lam, delta=delta, rH_fi=rs[iH], piH_fi=P[(AH, AH)][iH], piL_fi=P[(AL, AL)][iL])
    if feas.any():
        j = np.where(feas, P[(AH, AH)], -np.inf).argmax()
        out.update(sep=True, rH_sep=rs[j], piH_sep=P[(AH, AH)][j],
                   sh_easy=m(rs[j], AH, AH)[1], sh_hard=m(rs[j], AH, AH)[2])
    else:
        out.update(sep=False, rH_sep=np.nan, piH_sep=np.nan, sh_easy=np.nan, sh_hard=np.nan)
    pool = q * P[(AH, Abar)] + (1 - q) * P[(AL, Abar)]; ip = pool.argmax()
    out.update(pool_r=rs[ip], pool_exp=pool[ip], sh_easy_pool=m(rs[ip], AH, Abar)[1], sh_hard_pool=m(rs[ip], AH, Abar)[2])
    pu = np.array([(1 - lam) * usage_seg(p, Abar, 1.0)[0] + lam * usage_seg(p, Abar, delta)[0] for p in ps]); iu = pu.argmax()
    out.update(use_p=ps[iu], use_profit=pu[iu], sh_easy_use=usage_seg(ps[iu], Abar, 1.0)[1], sh_hard_use=usage_seg(ps[iu], Abar, delta)[1])
    out["exp_sep"] = q * out["piH_sep"] + (1 - q) * P[(AL, AL)][iL] if out["sep"] else np.nan
    return out


def show(rows, title):
    print(f"\n{title}")
    print(" lam delta | r_H*  r_H^sep | piH fi->sep | adopt share easy/hard: H-sep | out-pool | usage-pool | exp.profit sep / pool-out / pool-use")
    for o in rows:
        sep = f"{o['rH_sep']:.2f}   | {o['piH_fi']:.2f}->{o['piH_sep']:.2f}" if o["sep"] else "none   | " + f"{o['piH_fi']:.2f}->  --  "
        s1 = f"{o['sh_easy']:.2f}/{o['sh_hard']:.2f}" if o["sep"] else "  --    "
        print(f" {o['lam']:.2f} {o['delta']:.1f}  | {o['rH_fi']:.2f}  {sep} | {s1:9s} | {o['sh_easy_pool']:.2f}/{o['sh_hard_pool']:.2f} | "
              f"{o['sh_easy_use']:.2f}/{o['sh_hard_use']:.2f} | {o['exp_sep']:.3f} / {o['pool_exp']:.3f} / {o['use_profit']:.3f}")


if __name__ == "__main__":
    print(f"types A_L={AL}, A_H={AH}, q={q}; vendor compute cost k={kv}")
    show([analyse(l, 0.6) for l in (0.0, 0.25, 0.5, 0.75)], "share of hard tasks lam (reach scaled by delta=0.6 on hard tasks)")
    show([analyse(0.5, d) for d in (1.0, 0.8, 0.6, 0.4)], "complexity penalty delta at lam=0.5")
