"""Recompute the derived figures in Tables 1-2 and the text. Usage: python reproduce.py"""
import csv, pathlib
d = pathlib.Path(__file__).parent
t1 = {int(r["year"]): r for r in csv.DictReader(open(d / "data_table1.csv"))}
f = lambda r, k: float(r[k]) if r[k] else None
cpi = {y: f(r, "cpi_2024_100") for y, r in t1.items()}
real = lambda v, y: v * 100 / cpi[y]
sal = {y: f(r, "prof_salary_private_krw_mn") for y, r in t1.items() if r["prof_salary_private_krw_mn"]}
rd = {y: f(r, "business_rd_krw_tn") for y, r in t1.items()}
print("year  salary_idx  rd_idx  (2013=100, 2024 prices)")
for y in sorted(t1):
    si = real(sal[y], y) / real(sal[2013], 2013) * 100 if y in sal else float("nan")
    ri = real(rd[y], y) / real(rd[2013], 2013) * 100
    print(y, f"{si:7.1f} {ri:7.1f}")
r19, r24 = real(sal[2019], 2019), real(sal[2024], 2024)
print(f"real salary 2019-24: {r24/r19-1:+.1%} total, {(r24/r19)**(1/5)-1:+.2%}/yr")
print(f"nominal salary 2019-24: {sal[2024]/sal[2019]-1:+.2%}")
print(f"professor nominal CAGR 2013-24: {(sal[2024]/sal[2013])**(1/11)-1:.2%}")
print(f"R&D real CAGR 2013-24: {(real(rd[2024],2024)/real(rd[2013],2013))**(1/11)-1:.2%}")
t2 = {int(r["year"]): r for r in csv.DictReader(open(d / "data_table2.csv"))}
emp = lambda y: f(t2[y], "employee_large_firm_krw_mn")
ex = lambda y: f(t2[y], "unreg_exec_large_firm_krw_mn")
print(f"employee nominal CAGR 2012-25: {(emp(2025)/emp(2012))**(1/13)-1:.2%}")
for y, p in ((2012, sal[2013]), (2019, sal[2019]), (2024, sal[2024])):
    print(f"professor/employee {y}: {p/emp(y):.3f}")
print(f"exec/prof 2019: {ex(2019)/sal[2019]:.2f}; Samsung 2024 (671): {671/sal[2024]:.2f}; exec/emp 2020: {ex(2020)/emp(2020):.2f}")
