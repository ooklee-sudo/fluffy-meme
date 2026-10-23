"""Recompute every derived figure quoted in the manuscript from data/*.csv.

Usage: python reproduce.py
Real value in year t = nominal * CPI_2024 / CPI_t; indices use 2013 = 100.
"""
import csv
from pathlib import Path

D = Path(__file__).parent / "data"


def load(name):
    with open(D / name, newline="") as f:
        return {int(r["year"]): {k: (float(v) if v else None) for k, v in r.items() if k != "year" and k != "source"}
                for r in csv.DictReader(f)}


def cagr(a, b, years):
    return (b / a) ** (1 / years) - 1


t1, t2 = load("table1_academic_pay_rd.csv"), load("table2_pay_comparison.csv")


def real(series, key):
    return {y: r[key] * 100 / r["cpi_2024_100"] for y, r in t1.items() if r[key] is not None}


sal, rd = real(t1, "professor_salary_nominal_krw_million"), real(t1, "business_rd_nominal_krw_trillion")
print("Table 1 indices (2013 = 100): year, real salary, real R&D")
for y in sorted(t1):
    s = f"{sal[y] / sal[2013] * 100:6.1f}" if y in sal else "    --"
    print(f"  {y}  {s}  {rd[y] / rd[2013] * 100:6.1f}")
print(f"Real salary change 2019-2024: {sal[2024] / sal[2019] - 1:+.1%} ({cagr(sal[2019], sal[2024], 5):+.1%}/yr)")
print(f"Real R&D 2013-2024: {rd[2024] / rd[2013] - 1:+.1%} ({cagr(rd[2013], rd[2024], 11):+.1%}/yr)")
print(f"Nominal professor pay 2013-2024: {cagr(84.79, 101.39, 11):+.1%}/yr; 2019-2024: {101.39 / 100.62 - 1:+.1%} total")
print(f"Nominal large-firm employee pay 2012-2025: {cagr(59.8, 102.8, 13):+.1%}/yr")
for y, p, e in [(2013, 84.79, 59.8), (2019, 100.62, 78.8), (2024, 101.39, 95.1)]:
    print(f"Professor / employee pay {y}: {p / e:.2f}")
print(f"Exec / professor 2019: {342.7 / 100.62:.1f}x; Samsung exec / professor 2024: {671 / 101.39:.1f}x; exec / employee 2020: {358.9 / 81.2:.1f}x")
