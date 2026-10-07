"""Which features survive the white-box edit? Detectors built only on the two events the attacker does NOT edit (passives, nominalizations)
versus only on the five edited events, at no attack (e=0) and full attack (e=1)."""
import json, numpy as np
import attack_eval as A
import features as F
idx = lambda names: [F.NAMES.index(n) for n in names]
def sel(names):
    ii = idx(names)
    return lambda f: np.concatenate([f["rate"][ii], f["a"][ii], f["b"][ii]])
SETS = {"hard-to-edit events only (passive, nominal)": sel(["passive", "nominal"]),
        "edited events only (5)": sel(["parentheses", "brackets", "semicolons", "quotes", "markers"]),
        "all seven events (reference)": A.FAM["NEW: rates+(a,b)"]}
out = {}
print(f"{'feature set':46s}{'target':8s}  e=0 AUC / det@5%FPR    e=1 AUC / det@5%FPR")
for name, fam in SETS.items():
    rows = {g: A.evaluate(g, (0.0, 1.0), fam) for g in ("gpt4o", "claude", "llama")}
    for g, r in rows.items(): print(f"{name:46s}{g:8s}  {r[0.0][0]:.3f} / {r[0.0][1]:.2f}           {r[1.0][0]:.3f} / {r[1.0][1]:.2f}")
    mix = {e: (np.mean([rows[g][e][0] for g in rows]), np.mean([rows[g][e][1] for g in rows])) for e in (0.0, 1.0)}
    print(f"{name:46s}{'mixture':8s}  {mix[0.0][0]:.3f} / {mix[0.0][1]:.2f}           {mix[1.0][0]:.3f} / {mix[1.0][1]:.2f}\n", flush=True)
