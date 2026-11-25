"""Build the Study 1 regression table (spec A) with all coefficients.
Usage: python tables.py FRAME_CSV"""
import sys, warnings, numpy as np, pandas as pd, statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
d = pd.read_csv(sys.argv[1]); d["ct"] = d.city + "|" + d.room_type
ctl = "C(room_type)+accommodates+bedrooms+superhost+multi_listing_host+host_tenure_yrs"
def fit(f, df, logit=False):
    mod = (smf.logit if logit else smf.ols)(f, df); g = pd.factorize(df.loc[mod.data.row_labels, "neighbourhood_cleansed"])[0]
    return mod.fit(cov_type="cluster", cov_kwds={"groups": g}, disp=0)
b = d[d.is_bookable & d.ln_price.notna()]
M = {
 "(1)": fit(f"ln_price~zP+zE+zQ+{ctl}+C(neighbourhood_cleansed)", b),
 "(2)": fit(f"ln_price~zP*ln_reviews+zE*ln_reviews+zQ+{ctl}+C(neighbourhood_cleansed)", b),
 "(3)": fit(f"acc~O+zE+zQ+{ctl}+C(neighbourhood_cleansed)", d),
 "(4)": fit(f"acc_below~O+zE+zQ+{ctl}+C(neighbourhood_cleansed)", d, True),
 "(5)": fit(f"O~ln_comp_density_500m+zQ+{ctl}+C(ct)", d),
}
rows = [("zP", "zP"), ("zE", "zE"), ("zP:ln_reviews", "zP x ln(Reviews)"), ("zE:ln_reviews", "zE x ln(Reviews)"), ("O", "O"), ("zQ", "zQ"), ("ln_comp_density_500m", "ln(Competitor density)")]
def star(p): return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""
for var, lab in rows:
    cells = []
    for k, m in M.items():
        if var in m.params:
            v = np.exp(m.params[var]) if k == "(4)" else m.params[var]; se = (np.exp(m.params[var]) * m.bse[var]) if k == "(4)" else m.bse[var]
            cells.append(f"{v:.3f}{star(m.pvalues[var])} ({se:.3f})")
        else: cells.append("")
    print(f"| {lab} | " + " | ".join(cells) + " |")
print("| Observations | " + " | ".join(f"{int(m.nobs):,}" for m in M.values()) + " |")
print("| R2 / pseudo-R2 | " + " | ".join(f"{(m.prsquared if k=='(4)' else m.rsquared):.3f}" for k, m in M.items()) + " |")
# extra descriptives
m = fit("O~multi_listing_host+C(ct)", d); print("multi-listing diff O: %.3f se %.3f p=%.3g" % (m.params["multi_listing_host"], m.bse["multi_listing_host"], m.pvalues["multi_listing_host"]))
print("share O>1:", round((d.O > 1).mean(), 3), " N", len(d), "bookable", len(b))
print(d.groupby("city").size().to_dict())
print("accuracy mean/sd", round(d.acc.mean(), 3), round(d.acc.std(), 3), "share<4.8", round(d.acc_below.mean(), 3), "median reviews", d.number_of_reviews.median())
