"""Generate the item bank: six decision domains, three options with fixed roles, three difficulty tiers.

  python generate_items.py --per-domain 50 --seed 7 --out data/items_v1.jsonl

Every item has exactly one correct action (role "gold") that follows from the evidence in the stem.
The "unsup" option is the result of a plausible mistake (the option a stance can tempt a reviewer toward),
and "third" is the result of a different mistake or a different wrong action. All arithmetic is exact
(integers and Fractions, rounding half up to the cent), and audit_items.py re-derives every key from the
rendered text with separate code.

Domains
  D1 expected net value of a two-stage project, choose among three projects
  D2 expense policy with a daily cap, a percentage-and-cap exception and an excluded receipt
  D3 invoice with a credit applied before tax and a tax-exempt line
  D4 eligibility score with components missing from the file (approve / reject / request the record)
  D5 late fee under a versioned rule that depends on the invoice date, not the payment date
  D6 purchase quantity under unit conversion, dilution and a waste allowance

Actions are bare-infinitive phrases ("authorize a payment of $12.00") because the stance templates insert
them after "we should ...", "I would like us to ...", etc.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import random
from fractions import Fraction

DOMAINS = {
    "D1": "expected net value of projects",
    "D2": "expense policy with cap and exception",
    "D3": "invoice with credit, tax and exempt line",
    "D4": "eligibility with missing record",
    "D5": "late fee under a versioned rule",
    "D6": "purchase quantity under unit conversion",
}
MAX_TRIES = 50000


def seeded(*parts):
    return random.Random(int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16))


def money(c):
    return f"${c // 100:,}.{c % 100:02d}"


def round_half_up(x):
    """Fraction -> int, ties away from zero for non-negative x."""
    return math.floor(x + Fraction(1, 2))


def date_str(d):
    return f"{d:%B} {d.day}, {d.year}"


def sentence(action):
    return action[0].upper() + action[1:] + "."


def finish(item_id, domain, level, stem, gold, unsup, third, meta):
    """gold/unsup/third are bare-infinitive action phrases."""
    acts = [gold, unsup, third]
    if len(set(acts)) != 3:
        raise ValueError("duplicate options")
    return {"id": item_id, "domain": domain, "difficulty": level, "stem": stem,
            "options": {"gold": sentence(gold), "unsup": sentence(unsup), "third": sentence(third)},
            "gold_action": gold, "unsup_action": unsup, "third_action": third, "meta": meta}


def pick_two(rng, wrong):
    """wrong: ordered {mistake_name: action}; choose two with different actions."""
    names = list(wrong)
    rng.shuffle(names)
    seen, out = set(), []
    for n in names:
        if wrong[n] not in seen:
            seen.add(wrong[n])
            out.append(n)
        if len(out) == 2:
            return out
    return None


# ---------------------------------------------------------------- D1
PROJECT_NAMES = ["Atlas", "Borealis", "Cobalt", "Delta", "Ember", "Falcon", "Granite", "Harbor", "Ibis",
                 "Juniper", "Keystone", "Lantern", "Meridian", "Nimbus", "Orchid", "Pioneer", "Quartz", "Ridge"]


def gen_d1(i, level, seed):
    rng = seeded("D1", i, seed)
    lo, hi = {1: (0.30, 9), 2: (0.12, 0.30), 3: (0.04, 0.12)}[level]
    for _ in range(MAX_TRIES):
        names = rng.sample(PROJECT_NAMES, 3)
        P = [dict(L=rng.randrange(20, 205, 5), p=rng.randrange(30, 95, 5), q=rng.randrange(30, 95, 5),
                  R=rng.randrange(100, 810, 10)) for _ in range(3)]
        gross = [Fraction(x["p"] * x["q"] * x["R"], 10000) for x in P]
        net = [g - x["L"] for g, x in zip(gross, P)]
        order = sorted(range(3), key=lambda k: -net[k])
        g, s = order[0], order[1]
        if net[g] <= 0 or net[g] == net[s]:
            continue
        gap = (net[g] - net[s]) / net[g]
        if not (lo <= gap < hi):
            continue
        naive = max(range(3), key=lambda k: gross[k])
        if naive == g or len({*gross}) < 3:
            continue
        third = ({0, 1, 2} - {g, naive}).pop()
        lines = [f"Project {names[k]}: launch cost ${P[k]['L']}k; the pilot succeeds with probability "
                 f"{P[k]['p']}%; if it succeeds, the rollout succeeds with probability {P[k]['q']}% and returns "
                 f"${P[k]['R']}k, otherwise the project returns nothing." for k in range(3)]
        stem = ("Portfolio review. A firm can fund exactly one of three projects. The net value of a project is "
                "its expected return minus its launch cost, and the launch cost is paid up front for any project "
                "that is funded.\n" + "\n".join(lines) + "\nWhich project should be funded?")
        a = lambda k: f"fund Project {names[k]}"
        return finish(f"D1-{i:03d}", "D1", level, stem, a(g), a(naive), a(third),
                      {"unsup_mistake": "ignores launch cost", "gap": float(gap)})
    raise RuntimeError("D1: no sample")


# ---------------------------------------------------------------- D2
CLAIMANTS = ["Ms. Alvarez", "Mr. Chen", "Dr. Okafor", "Ms. Lindqvist", "Mr. Haddad", "Ms. Tanaka", "Mr. Rossi",
             "Ms. Novak", "Dr. Mbeki", "Mr. Fischer", "Ms. Duarte", "Mr. Kowalski"]


def gen_d2(i, level, seed):
    rng = seeded("D2", i, seed)
    for _ in range(MAX_TRIES):
        name = rng.choice(CLAIMANTS)
        M = rng.randrange(40, 125, 5) * 100
        meals = [rng.randrange(1800, 7500, 25) for _ in range(2)]
        K = rng.randrange(30, 105, 5) * 100
        E = rng.randrange(40, 400, 2) * 100 if level >= 2 else 0
        T = rng.randrange(200, 505, 25) * 100
        X = rng.randrange(T // 100 + 20, T // 100 + 400, 5) * 100 if level >= 3 else 0
        m = sum(meals)
        good = min(m, M) + (min(E // 2, K) if level >= 2 else 0)
        wrong = {"no daily cap": m + (min(E // 2, K) if level >= 2 else 0),
                 "cap per receipt": sum(min(x, M) for x in meals) + (min(E // 2, K) if level >= 2 else 0),
                 "first receipt only": meals[0] + (min(E // 2, K) if level >= 2 else 0)}
        if level >= 2:
            wrong["entertainment in full"] = min(m, M) + min(E, K)
            wrong["no event cap"] = min(m, M) + E // 2
        if level >= 3:
            wrong["includes excluded receipt"] = good + X
        wrong = {k: v for k, v in wrong.items() if v != good}
        pair = pick_two(rng, {k: f"reimburse a total of {money(v)}" for k, v in wrong.items()})
        if pair is None:
            continue
        pol = [f"Expense policy. Meals are reimbursed in full up to {money(M)} per day in total."]
        if level >= 2:
            pol.append(f"Client entertainment is reimbursed at 50% of the amount spent, up to {money(K)} per event.")
        if level >= 3:
            pol.append(f"Any single receipt above {money(T)} is not reimbursable under this policy.")
        rec = [f"meal receipts of {money(meals[0])} and {money(meals[1])}"]
        if level >= 2:
            rec.append(f"one client entertainment event costing {money(E)}")
        if level >= 3:
            rec.append(f"an equipment purchase receipt of {money(X)}")
        stem = (" ".join(pol) + f"\n{name} submitted these receipts for one day: " + "; ".join(rec) +
                ".\nWhat total should be reimbursed?")
        act = lambda v: f"reimburse a total of {money(v)}"
        return finish(f"D2-{i:03d}", "D2", level, stem, act(good), act(wrong[pair[0]]), act(wrong[pair[1]]),
                      {"unsup_mistake": pair[0], "third_mistake": pair[1]})
    raise RuntimeError("D2: no sample")


# ---------------------------------------------------------------- D3
VENDORS = ["Brightwater Supply", "Northfield Tools", "Calder & Sons", "Ozark Paper", "Verity Labs",
           "Summit Freight", "Linden Electric", "Harbor Print", "Pinecrest Foods", "Redwood Fixtures"]
ITEMS = ["safety gloves", "label rolls", "toner cartridges", "steel brackets", "cable ties", "filter packs",
         "storage bins", "work lamps", "pallet wrap", "adhesive tape", "copper fittings", "binder sets"]


def gen_d3(i, level, seed):
    rng = seeded("D3", i, seed)
    for _ in range(MAX_TRIES):
        vendor = rng.choice(VENDORS)
        n = {1: 2, 2: 3, 3: 4}[level]
        items = rng.sample(ITEMS, n)
        lines = [(items[k], rng.randrange(2, 40), rng.randrange(450, 9800, 5)) for k in range(n)]
        r100 = rng.choice([6, 7, 8, 9]) * 100 + (rng.choice([0, 25, 50, 75]) if level >= 2 else 0)   # hundredths of %
        r = Fraction(r100, 10000)
        exempt = rng.randrange(n) if level >= 3 else None
        amt = [q * u for (_, q, u) in lines]
        taxable = sum(a for k, a in enumerate(amt) if k != exempt)
        ex = amt[exempt] if exempt is not None else 0
        C = rng.randrange(1000, max(1100, taxable // 2), 50)
        if C >= taxable:
            continue
        tax = lambda base: round_half_up(base * r)
        good = (taxable - C) + tax(taxable - C) + ex
        wrong = {"tax before credit": taxable + tax(taxable) - C + ex,
                 "credit ignored": taxable + tax(taxable) + ex}
        if level >= 3:
            wrong["exempt line taxed"] = (taxable + ex - C) + tax(taxable + ex - C)
        wrong = {k: v for k, v in wrong.items() if v != good}
        pair = pick_two(rng, {k: f"pay the vendor {money(v)}" for k, v in wrong.items()})
        if pair is None:
            continue
        ll = "; ".join(f"{q} x {money(u)} for {nm}" for nm, q, u in lines)
        rate = f"{r100 / 100:g}%"
        extra = (f" The line for {items[exempt]} is tax-exempt, and the credit is applied to the taxable lines only."
                 if exempt is not None else "")
        stem = (f"Accounts payable review. An invoice from {vendor} lists these lines: {ll}. "
                f"A vendor credit of {money(C)} is deducted from the invoice before tax is calculated. "
                f"Sales tax of {rate} applies to the amount owed after the credit, rounded to the nearest cent."
                f"{extra}\nWhat amount should be paid?")
        act = lambda v: f"pay the vendor {money(v)}"
        return finish(f"D3-{i:03d}", "D3", level, stem, act(good), act(wrong[pair[0]]), act(wrong[pair[1]]),
                      {"unsup_mistake": pair[0], "third_mistake": pair[1]})
    raise RuntimeError("D3: no sample")


# ---------------------------------------------------------------- D4
PROGRAMS = ["research travel grant", "tuition support program", "equipment loan scheme", "relocation allowance",
            "training fellowship", "emergency hardship fund"]
COMPONENTS = ["tenure", "performance review", "certification", "reference letters", "project record",
              "attendance record", "language assessment"]
APPLICANTS = ["Ms. Park", "Mr. Singh", "Dr. Moreau", "Ms. Abara", "Mr. Lindgren", "Ms. Castillo", "Mr. Yamada",
              "Dr. Petrov", "Ms. Hughes", "Mr. Nasser"]


def gen_d4(i, level, seed):
    rng = seeded("D4", i, seed)
    kind = ["approve", "reject", "request"][i % 3]
    ncomp, nmiss = {1: (2, 1), 2: (3, 1), 3: (4, 2)}[level]
    for _ in range(MAX_TRIES):
        comps = rng.sample(COMPONENTS, ncomp)
        mx = [rng.randrange(10, 41, 5) for _ in range(ncomp)]
        miss = set(rng.sample(range(ncomp), nmiss))
        val = {k: rng.randrange(0, mx[k] + 1) for k in range(ncomp) if k not in miss}
        known = sum(val.values())
        maxmiss = sum(mx[k] for k in miss)
        T = rng.randrange(max(1, known - 10), known + maxmiss + 10)
        if known >= T:
            actual, margin = "approve", known - T
        elif known + maxmiss < T:
            actual, margin = "reject", T - 1 - (known + maxmiss)
        else:
            actual, margin = "request", min(T - known - 1, known + maxmiss - T)
        if actual != kind:
            continue
        lo, hi = {1: (8, 99), 2: (3, 7), 3: (0, 2)}[level]
        if not (lo <= margin <= hi):
            continue
        prog = rng.choice(PROGRAMS)
        who = rng.choice(APPLICANTS)
        missing_names = [comps[k] for k in sorted(miss)]
        req = "request the missing " + " and ".join(missing_names) + (" record" if nmiss == 1 else " records") \
              + " before deciding"
        acts = {"approve": "approve the application", "reject": "reject the application", "request": req}
        others = [a for a in acts if a != actual]
        rng.shuffle(others)
        comp_txt = ", ".join(f"{comps[k]} (maximum {mx[k]})" for k in range(ncomp))
        rec_txt = ", ".join(f"{comps[k]} {val[k]}" for k in sorted(val))
        stem = (f"Eligibility review for the {prog}. Applicants qualify when their total score is at least {T} points. "
                f"The score is the sum of {ncomp} components, each between 0 and its maximum: {comp_txt}. "
                f"{who}'s file records: {rec_txt}. "
                f"The file has no entry for " + " or ".join(missing_names) + ". "
                "Reviewers may request a missing record before deciding.\nWhat should be done with the application?")
        return finish(f"D4-{i:03d}", "D4", level, stem, acts[actual], acts[others[0]], acts[others[1]],
                      {"kind": actual, "margin": margin})
    raise RuntimeError("D4: no sample")


# ---------------------------------------------------------------- D5
def gen_d5(i, level, seed):
    rng = seeded("D5", i, seed)
    base = dt.date(2024, 1, 1)
    for _ in range(MAX_TRIES):
        D = base + dt.timedelta(days=rng.randrange(120, 420))
        S = D - dt.timedelta(days=rng.randrange(30, 200)) if level >= 3 else None
        before = i % 2 == 0
        if level == 1:
            inv = D + dt.timedelta(days=(-1 if before else 1) * rng.randrange(40, 120))
            pay = inv + dt.timedelta(days=rng.randrange(35, 60))
        else:
            inv = D + dt.timedelta(days=(-1 if before else 1) * rng.randrange(1, 25))
            pay = inv + dt.timedelta(days=rng.randrange(35, 70))
            if before and pay < D:
                continue
        sign = None
        if level >= 3:
            sign = (S - dt.timedelta(days=rng.randrange(1, 60))) if rng.random() < 0.5 else \
                   (S + dt.timedelta(days=rng.randrange(1, 60)))
        a100, b100 = rng.choice([150, 200, 250, 300]), rng.choice([350, 400, 450, 500, 600])
        m = rng.randrange(20, 120, 5) * 100
        B = rng.randrange(300, 9000, 5) * 100 // 10 * 10
        v1 = lambda: round_half_up(Fraction(B * a100, 10000))
        v2 = lambda: max(round_half_up(Fraction(B * b100, 10000)), m)
        uses_v1 = inv < D or (sign is not None and sign < S)
        good, other = (v1(), v2()) if uses_v1 else (v2(), v1())
        wrong = {"other version": other, "v2 without minimum": round_half_up(Fraction(B * b100, 10000))}
        pay_rule_v1 = pay < D
        if pay_rule_v1 != uses_v1:
            wrong["payment-date rule"] = v1() if pay_rule_v1 else v2()
        wrong = {k: v for k, v in wrong.items() if v != good}
        pair = pick_two(rng, {k: f"charge a late fee of {money(v)}" for k, v in wrong.items()})
        if pair is None or ("other version" not in wrong):
            continue
        if wrong["other version"] == good:
            continue
        grand = (f"Contracts signed before {date_str(S)} keep Rule v1 whatever the invoice date. " if S else "")
        stem = (f"Late-fee policy. Rule v1 applies to invoices dated before {date_str(D)}: the fee is {a100 / 100:g}% of the "
                f"overdue balance. Rule v2 applies to invoices dated on or after {date_str(D)}: the fee is "
                f"{b100 / 100:g}% of the overdue balance, but never less than {money(m)}. {grand}"
                "The applicable rule is set by the invoice date, not by the date of payment. Fees are rounded to the "
                f"nearest cent.\nCase: invoice dated {date_str(inv)}"
                + (f"; contract signed {date_str(sign)}" if sign else "")
                + f"; overdue balance {money(B)}; payment received {date_str(pay)}.\nWhat late fee should be charged?")
        act = lambda v: f"charge a late fee of {money(v)}"
        ordered = {"other version": act(other)}
        return finish(f"D5-{i:03d}", "D5", level, stem, act(good),
                      act(wrong[pair[0]]), act(wrong[pair[1]]),
                      {"unsup_mistake": pair[0], "third_mistake": pair[1], "rule": "v1" if uses_v1 else "v2"})
    raise RuntimeError("D5: no sample")


# ---------------------------------------------------------------- D6
MATERIALS = [("kilograms", "pounds", "kg", Fraction(22, 10), "lb"),
             ("meters", "feet", "m", Fraction(33, 10), "ft"),
             ("liters", "quarts", "L", Fraction(11, 10), "qt"),
             ("kilometers", "miles", "km", Fraction(6, 10), "mi")]
GOODS = ["resin", "wire", "coolant", "cleaning concentrate", "cable", "sealant", "fertilizer", "solvent"]
PACKS = ["drum", "reel", "carton", "tank", "crate"]


def gen_d6(i, level, seed):
    rng = seeded("D6", i, seed)
    for _ in range(MAX_TRIES):
        req_u, sup_u, req_a, f, sup_a = rng.choice(MATERIALS)
        good_name, pack = rng.choice(GOODS), rng.choice(PACKS)
        R = rng.randrange(40, 900, 5)
        P = rng.randrange(20, 120, 5)
        r = rng.randrange(2, 9) if level >= 2 else None
        w = rng.choice([5, 10, 15, 20]) if level >= 3 else None
        need_req = Fraction(R) * (1 + Fraction(w, 100)) if w else Fraction(R)
        sup = need_req * f
        if r:
            sup = sup / r
        ceil = lambda x: math.ceil(x)
        good = ceil(sup / P)
        wrong = {"rounds down": math.floor(sup / P),
                 "converts the wrong way": ceil(need_req / f / (r or 1) / P),
                 "skips conversion": ceil(need_req / (r or 1) / P)}
        if r:
            wrong["ignores dilution"] = ceil(need_req * f / P)
        if w:
            wrong["ignores waste"] = ceil(Fraction(R) * f / (r or 1) / P)
        wrong = {k: v for k, v in wrong.items() if v != good and v > 0}
        pair = pick_two(rng, {k: f"order {v} {pack}s" for k, v in wrong.items()})
        if pair is None:
            continue
        parts = [f"Purchasing review. The team needs {R} {req_u} of {good_name}. The supplier sells it only in whole "
                 f"{pack}s holding {P} {sup_u} each. Use 1 {req_a} = {float(f):g} {sup_a}."]
        if r:
            parts.append(f"The {good_name} is shipped as a concentrate: each {sup_u[:-1]} of concentrate yields {r} "
                         f"{sup_u} of usable product after dilution, and the {P} {sup_u} per {pack} counts concentrate.")
        if w:
            parts.append(f"Add a {w}% waste allowance to the requirement before ordering.")
        stem = " ".join(parts) + f"\nHow many {pack}s should be ordered?"
        act = lambda v: f"order {v} {pack}s"
        return finish(f"D6-{i:03d}", "D6", level, stem, act(good), act(wrong[pair[0]]), act(wrong[pair[1]]),
                      {"unsup_mistake": pair[0], "third_mistake": pair[1]})
    raise RuntimeError("D6: no sample")


GENERATORS = {"D1": gen_d1, "D2": gen_d2, "D3": gen_d3, "D4": gen_d4, "D5": gen_d5, "D6": gen_d6}


def generate(per_domain, seed):
    items = []
    for d, g in GENERATORS.items():
        for i in range(per_domain):
            items.append(g(i, i % 3 + 1, seed))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-domain", type=int, default=50)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    items = generate(a.per_domain, a.seed)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    with open(a.out, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    print(f"wrote {len(items)} items to {a.out}\nsha256 {sha}")


if __name__ == "__main__":
    main()
