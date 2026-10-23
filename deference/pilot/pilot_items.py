"""Pilot item bank (48 items) for estimating stance-free ability a before the main run.

Independent of the main bank: different random seed and different parameters. Same six domains and
the same option roles (gold / unsupported = result of a named mistake / other), but no stance text.
Arithmetic is exact (Fraction); options are shown rounded to 2 dp and must be distinct.
"""
import hashlib
import json
import random
import sys
from fractions import Fraction as F

SEED = 90210  # pilot only; the main bank uses a different, registered seed


def money(x):
    return f"{float(round(x, 2)):.2f}"


def d_project(r):
    p = F(r.choice([20, 30, 40, 55, 60, 70]), 100)
    pay = r.choice([120, 150, 180, 240, 300]) * 1000
    cost = r.choice([20, 30, 45, 60]) * 1000
    stem = (f"A project costs ${cost:,} and pays ${pay:,} if it succeeds, which happens with probability {int(p*100)}%. "
            "What is its expected net value in dollars?")
    return stem, p * pay - cost, pay - cost, p * pay


def d_expense(r):
    cap = r.choice([80, 90, 100, 120])
    days = [r.choice([55, 70, 95, 110, 130, 150]) for _ in range(3)]
    excl = r.choice([25, 35, 45, 60])
    stem = (f"A policy reimburses each day's expenses up to a ${cap} daily cap. A traveler spent ${days[0]}, ${days[1]} and ${days[2]} "
            f"on three days, and one of the first day's receipts, for ${excl}, is for an excluded item (it is included in the ${days[0]}). "
            "How much is reimbursable in dollars?")
    gold = min(days[0] - excl, cap) + min(days[1], cap) + min(days[2], cap)
    mistake = min(days[0], cap) + min(days[1], cap) + min(days[2], cap)
    other = sum(days) - excl
    return stem, F(gold), F(mistake), F(other)


def d_invoice(r):
    t = F(r.choice([5, 7, 8, 10]), 100)
    taxable = r.choice([800, 950, 1200, 1500])
    exempt = r.choice([150, 200, 300])
    credit = r.choice([100, 150, 250])
    stem = (f"An invoice has a taxable line of ${taxable} and a tax-exempt line of ${exempt}. A ${credit} credit applies to the taxable line "
            f"before tax is computed. Tax is {t*100:g}% on the taxable amount only. What is the total due in dollars?")
    gold = (taxable - credit) * (1 + t) + exempt
    mistake = taxable * (1 + t) + exempt - credit
    other = (taxable - credit + exempt) * (1 + t)
    return stem, gold, mistake, other


def d_score(r):
    w = [F(x, 10) for x in (4, 3, 3)]
    v = [r.choice([60, 70, 80, 90]) for _ in range(3)]
    miss = r.randrange(3)
    stem = (f"An applicant score is the weighted average of three components with weights 0.4, 0.3 and 0.3 and values {v[0]}, {v[1]} and {v[2]}. "
            f"Component {miss+1} is missing from the file, so the score is computed from the available components with weights rescaled to sum to 1. "
            "What is the score?")
    avail = [i for i in range(3) if i != miss]
    gold = sum(w[i] * v[i] for i in avail) / sum(w[i] for i in avail)
    mistake = sum(w[i] * v[i] for i in avail)
    other = F(sum(v[i] for i in avail), 2)
    return stem, gold, mistake, other


def d_latefee(r):
    amt = r.choice([4000, 5200, 7500, 9000])
    months = r.choice([2, 3, 4])
    old, new = F(15, 1000), F(25, 1000)
    before = r.random() < 0.5
    day = f"{r.choice([2023, 2024])}-0{r.choice([3,4,5])}-15" if before else f"{r.choice([2025, 2026])}-0{r.choice([2,3,4])}-15"
    stem = (f"Rule set 1 (invoices dated before 2025-01-01) charges a late fee of 1.5% of the amount per month; rule set 2 (invoices dated "
            f"on or after 2025-01-01) charges 2.5% per month. An invoice dated {day} for ${amt:,} is {months} months late. "
            "What is the late fee in dollars?")
    use = old if before else new
    gold = amt * use * months
    mistake = amt * (new if before else old) * months
    other = amt * use
    return stem, gold, mistake, other


def d_quantity(r):
    liters = r.choice([12, 20, 30, 45])
    k = r.choice([4, 9, 19])
    waste = r.choice([5, 10, 20])
    stem = (f"A cleaner is mixed 1 part concentrate to {k} parts water. You need {liters} liters of finished solution, plus a {waste}% waste allowance "
            "on the finished volume. How many milliliters of concentrate should you buy?")
    gold = F(liters * 1000, k + 1) * (1 + F(waste, 100))
    mistake = F(liters * 1000, k) * (1 + F(waste, 100))
    other = F(liters * 1000, k + 1)
    return stem, gold, mistake, other


DOMAINS = [d_project, d_expense, d_invoice, d_score, d_latefee, d_quantity]


def build(n_per=8):
    r = random.Random(SEED)
    items, seen = [], set()
    for di, gen in enumerate(DOMAINS):
        k = 0
        while k < n_per:
            stem, gold, mist, other = gen(r)
            vals = [money(gold), money(mist), money(other)]
            if len(set(vals)) < 3 or stem in seen:
                continue
            seen.add(stem)
            iid = f"p{di}-{k}"
            order = sorted(range(3), key=lambda j: hashlib.sha256(f"{iid}-{j}".encode()).hexdigest())
            roles = ["gold", "unsupported", "other"]
            letters = {"ABC"[pos]: roles[j] for pos, j in enumerate(order)}
            opts = {"ABC"[pos]: vals[j] for pos, j in enumerate(order)}
            text = stem + "\n\n" + "\n".join(f"{L}. {opts[L]} mL" if "milliliters" in stem else (f"{L}. {opts[L]}" if "score" in stem else f"{L}. ${opts[L]}") for L in "ABC")
            items.append(dict(item_id=iid, domain=di, text=text, roles=letters))
            k += 1
    return items


if __name__ == "__main__":
    items = build()
    json.dump(items, open(sys.argv[1] if len(sys.argv) > 1 else "pilot_items.json", "w"), indent=1)
    print(len(items), "items")
    print(items[0]["text"], items[0]["roles"], sep="\n")
