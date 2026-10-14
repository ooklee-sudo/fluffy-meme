"""Rebuild chains/MCD.json from McDonald's earnings 8-K exhibits (EDGAR CIK 63908); text pulled by /tmp script, parsed here from parsed.json."""
import json,sys
rows=json.load(open(sys.argv[1]))
lab={"2023-03-31":"Q1 2023","2023-06-30":"Q2 2023","2023-09-30":"Q3 2023","2023-12-31":"Q4 2023","2024-03-31":"Q1 2024","2024-06-30":"Q2 2024","2024-09-30":"Q3 2024","2024-12-31":"Q4 2024","2025-03-31":"Q1 2025","2025-06-30":"Q2 2025","2025-09-30":"Q3 2025","2025-12-31":"Q4 2025","2026-03-31":"Q1 2026","2026-06-30":"Q2 2026","2022-12-31":"Q4 2022"}
import datetime
out=[]
for x,row,qe,sent in rows:
    qe=datetime.datetime.strptime(qe,"%B %d, %Y").strftime("%Y-%m-%d")
    cur=row.split()[1]; neg=row.split()[1].startswith('(')
    v=float(cur.strip('()'))*(-1 if neg else 1)
    out.append(dict(quarter_label=lab[qe],fiscal_quarter_end=qe,comps_pct=v,metric_name="Comparable sales, U.S.",quote=row+" ... "+(sent or "").lstrip("• "),filing_date=x['filing_date'],source_url=x['url'],note="Table row 'COMPARABLE SALES' in Exhibit 99.1: current-quarter then prior-year-quarter value; prior-year column matches the previous year's release."))
json.dump(out,open('chains/MCD.json','w'),indent=1)
print([(r['quarter_label'],r['comps_pct']) for r in out])
