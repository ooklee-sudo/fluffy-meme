"""Parse the pasted analysis outputs (*.txt) into CSV tables used by the manuscript builder."""
import re, pandas as pd
CI = re.compile(r'(-?[\d.]+) \[(-?[\d.]+),(-?[\d.]+)\](\*?)')


def dist(fn, out):
    rows = []
    for line in open(fn):
        if not line.strip():
            continue
        t = line.split()
        model, anchor, cond, n = t[:4]
        rest = t[4:]
        fail = float(rest[1] if "." not in rest[0] else rest[0])  # optional "seeds" column
        cs = CI.findall(line); assert len(cs) == 4, line
        r = dict(model=model, anchor=anchor == "True", cond=cond, n=int(n), parse_fail=fail)
        for k, c in zip(["mean", "var_mean", "zero", "alpha"], cs):
            r[k] = float(c[0]); r[k + "_lo"] = float(c[1]); r[k + "_hi"] = float(c[2]); r[k + "_excl"] = c[3] == "*"
        rows.append(r)
    df = pd.DataFrame(rows); df.to_csv(out, index=False); return df


def hill_table():
    cell = re.compile(r'(inf \(ctrl rate 0\)|-?[\d.]+ \[-?[\d.]+,-?[\d.]+\]\*?)')
    rows = []
    for line in open("hillstrom_table.txt"):
        p = line.split()
        model, anchor, method, outcome, fail, ctrl, men, women = p[:8]
        cs = cell.findall(" ".join(p[8:])); assert len(cs) == 2, line
        def rr(c):
            if c.startswith("inf"):
                return (float("inf"), None, None, False)
            m = re.match(r'(-?[\d.]+) \[(-?[\d.]+),(-?[\d.]+)\](\*?)', c)
            return (float(m[1]), float(m[2]), float(m[3]), m[4] == "*")
        a, b = rr(cs[0]), rr(cs[1])
        rows.append(dict(model=model, anchor=anchor == "True", method=method, outcome=outcome, fail=float(fail), ctrl=float(ctrl),
                         men=float(men), women=float(women), RR_men=a[0], RR_men_lo=a[1], RR_men_hi=a[2], RR_men_excl=a[3],
                         RR_women=b[0], RR_women_lo=b[1], RR_women_hi=b[2], RR_women_excl=b[3]))
    d = pd.DataFrame(rows); d["RD_men"] = d.men - d.ctrl; d["RD_women"] = d.women - d.ctrl
    d.to_csv("hillstrom_table.csv", index=False); return d


def hill_rd():
    rows = []
    c3 = re.compile(r'([+-][\d.]+) \[([+-][\d.]+),([+-][\d.]+)\](\*?)')
    for line in open("hillstrom_rd.txt"):
        p = line.split(None, 4); model, anchor, method, outcome = p[:4]
        cs = c3.findall(p[4]); assert len(cs) == 3, line
        r = dict(model=model, anchor=anchor == "True", method=method, outcome=outcome)
        for k, c in zip(["RD_men", "RD_women", "gap"], cs):
            r[k] = float(c[0]); r[k + "_lo"] = float(c[1]); r[k + "_hi"] = float(c[2]); r[k + "_star"] = c[3] == "*"
        r["men_over_real"] = float(p[4].split()[-1]); rows.append(r)
    d = pd.DataFrame(rows); d.to_csv("hillstrom_rd_parsed.csv", index=False); return d


def rho():
    c = re.compile(r'([+-][\d.]+) \[([+-][\d.]+),([+-][\d.]+)\]')
    rows = []
    for line in open("demo_rho.txt"):
        t = line.split(); model, anchor, cond = t[:3]
        cs = c.findall(line)
        first_nan = t[3] == "NaN"
        r = dict(model=model, anchor=anchor == "True", cond=cond, rho=None, rho_lo=None, rho_hi=None, lam=None, lam_lo=None, lam_hi=None)
        if first_nan:
            pass
        else:
            r.update(rho=float(cs[0][0]), rho_lo=float(cs[0][1]), rho_hi=float(cs[0][2]))
            if len(cs) > 1:
                r.update(lam=float(cs[1][0]), lam_lo=float(cs[1][1]), lam_hi=float(cs[1][2]))
        rows.append(r)
    d = pd.DataFrame(rows); d.to_csv("demo_rho.csv", index=False); return d


if __name__ == "__main__":
    for fn, out in (("retail_ci.txt", "retail_ci.csv"), ("grocery_ci.txt", "grocery_ci.csv"), ("demo_ci.txt", "demo_ci.csv")):
        print(fn, len(dist(fn, out)))
    print("hillstrom_table", len(hill_table()), "hillstrom_rd", len(hill_rd()), "rho", len(rho()))
