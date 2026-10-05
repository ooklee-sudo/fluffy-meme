"""Compact view of <out>/tofu_analysis.json:  python summarize.py out_llm/tofu_analysis.json"""
import json, sys
o = json.load(open(sys.argv[1])); n = o["n"]
print(f"n={n}   v(N) = {o['v(N)']}")
print("seed-noise sd (mask, auth, gen):", o["seed_noise_sd(auth,gen)"])
print(f"median |LOO| auth = {o['median_|LOO|(auth)']}   median |phi| auth = {o['median_|phi|(auth)']}")
print("phi(v) auth:", o["phi_v"]["auth"]); print("LOO(v) auth:", o["loo_v"]["auth"])
print(f"\n{'steps':>5} {'eps0':>7} {'rho0':>7} {'kappa0':>7} {'biasL1':>7} {'spear(v,vh)':>12} {'orderL1':>8} {'spear(seq,set)':>14}")
for r in o["by_strength"]:
    print(f"{r['steps']:>5} {r['eps0']['total']:>7} {r['rho0']:>7} {r['kappa0']:>7} {r['bias_L1(auth)']:>7} "
          f"{str(r['spearman(phi_v, phi_vhat)']):>12} {r['order_dependence_L1(auth)']:>8} {str(r['spearman(phi_seq, phi_vhat_setfn)']):>14}")
a = o["relearn_attack_auth@T=empty"]
print("\nrelearning attack: auth utility at T=empty after k relearn steps", a["relearn_k=[0,5,20,60]"], "| retrain baseline", a["retrain_baseline"])
for k in ("P1", "P3", "P3_phi_v_vs_k", "reps"):
    if k in o: print(k, o[k])
