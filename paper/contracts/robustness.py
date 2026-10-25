import numpy as np
from contracts import Mkt, solve
rng = np.random.default_rng(7)
out = []; P = out.append
# (1) random parameter sweep
rows = []
for _ in range(300):
    a = rng.uniform(.05, .6); b = np.exp(rng.uniform(np.log(.1), np.log(4))); H = np.exp(rng.uniform(np.log(30), np.log(500)))
    v = H*np.exp(rng.uniform(np.log(.001), np.log(.03))); k = v*np.exp(rng.uniform(np.log(.1), np.log(3)))
    m = Mkt(a, b, H, v, k, J=3000); fb, bw, bf, ef = solve(m, grid=400)
    if fb['surplus'] <= 1e-6: continue
    rows.append(dict(a=a, b=b, ratio=H/v, W_pa=bw['welfare']/fb['surplus'], W_sf=bf['welfare']/fb['surplus'], V_pa=bw['vend'], V_sf=bf['vend'],
                     F_pa=m.H-bw['firm'], F_sf=m.H-bf['firm'], N_fb=fb['N'], N_pa=bw['N'], N_sf=bf['N'], vshare_eff=ef['vend']/fb['surplus'], k_over_kv=k/(k+v)))
R = rows; n = len(R)
f = lambda key: np.array([r[key] for r in R])
P(f"Random sweep: {n} parameter draws (a~U(.05,.6), b log-U(.1,4), H log-U(30,500), v/H log-U(.001,.03), k/v log-U(.1,3))")
P(f"Vendor profit: success-fee >= per-attempt in {np.mean(f('V_sf') >= f('V_pa')-1e-9)*100:.0f}% of draws")
P(f"Firm saving:   success-fee >= per-attempt in {np.mean(f('F_sf') >= f('F_pa')-1e-9)*100:.0f}% of draws")
P(f"Welfare/FB:    per-attempt median {np.median(f('W_pa')):.2f} [IQR {np.percentile(f('W_pa'),25):.2f}-{np.percentile(f('W_pa'),75):.2f}];  success-fee median {np.median(f('W_sf')):.2f} [IQR {np.percentile(f('W_sf'),25):.2f}-{np.percentile(f('W_sf'),75):.2f}]")
P(f"Success-fee welfare > per-attempt welfare in {np.mean(f('W_sf') >= f('W_pa')-1e-9)*100:.0f}% of draws")
P(f"Median attempts: first-best {np.median(f('N_fb')):.0f}, per-attempt monopoly {np.median(f('N_pa')):.0f}, success-fee monopoly {np.median(f('N_sf')):.0f}")
P(f"Efficient-fee vendor share of surplus equals k/(k+v): max abs diff {np.max(np.abs(f('vshare_eff')-f('k_over_kv'))):.3f}")
# (2) quality-misperception regret: firm believes a_believed, true a_true (b fixed). Cap chosen from belief; contract terms fixed at belief-based monopoly price.
P("")
P("Regret from over-estimating vendor quality (H=100, v=1, k=0.2, b=0.39): firm saving vs human-only when it sets N from believed 'a' but true 'a' is lower")
P("a_true   contract         saving(correct belief a=0.25 vs true)   saving(believed a=0.25)   loss")
b, H, v, k = .39, 100., 1., .2
belief = Mkt(.25, b, H, v, k); fb_, bw_, bf_, ef_ = solve(belief, grid=800)
w0, f0 = bw_['w'], ef_['f']
for at in [.25, .15, .10, .05]:
    true = Mkt(at, b, H, v, k)
    # fee levels fixed by contract: per-attempt at w=k+0.5 (cost-plus) ; success fee at efficient f
    w_cp = 2.0
    for name, fn, term in [("per-attempt w=2.0", true.per_attempt, w_cp), ("success fee f=Hk/(k+v)", true.success_fee, f0)]:
        # firm sets N from believed a under the same terms
        Nb = belief.Nstar(H/(term+v)) if "per-attempt" in name else belief.Nstar((H-term)/v)
        if "per-attempt" in name: c = term+v; cost_b = c*true.att(Nb) + H*(1-true.P(Nb)); Nt = true.Nstar(H/c); cost_t = c*true.att(Nt)+H*(1-true.P(Nt))
        else: cost_b = v*true.att(Nb) + term*true.P(Nb) + H*(1-true.P(Nb)); Nt = true.Nstar((H-term)/v); cost_t = v*true.att(Nt)+term*true.P(Nt)+H*(1-true.P(Nt))
        P(f"{at:5.2f}    {name:22s} {H-cost_t:8.2f}   {H-cost_b:8.2f}   {cost_b-cost_t:7.2f}   (N_believed={Nb}, N_true={Nt})")
open("results_robustness.txt", "w").write("\n".join(out)); print("\n".join(out))
