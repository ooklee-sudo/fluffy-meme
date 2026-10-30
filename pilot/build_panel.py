"""Weekly new-question counts per tag (top-50 tags used in questions_v2) from the HF Stack Overflow dump (to 2023-06-14)."""
import duckdb, json, csv
tags = list(dict.fromkeys(q["tag"] for q in json.load(open("questions_v2.json"))))
con = duckdb.connect(); con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("CREATE TABLE tl(tag VARCHAR)"); con.executemany("INSERT INTO tl VALUES (?)", [(t,) for t in tags])
con.execute("CREATE TABLE wk(week DATE, tag VARCHAR, n INTEGER)")
con.execute("CREATE TABLE tot(week DATE, n INTEGER)")
for i in range(58):
    u = f"https://huggingface.co/datasets/mikex86/stackoverflow-posts/resolve/main/stackoverflow-posts-{i:05d}-of-00058.parquet"
    con.execute(f"""CREATE OR REPLACE TEMP TABLE q AS SELECT date_trunc('week', CAST(CreationDate AS TIMESTAMP))::DATE AS week, Tags
        FROM read_parquet('{u}') WHERE PostTypeId=1 AND CreationDate >= '2019-01-01'""")
    con.execute("INSERT INTO tot SELECT week, count(*) FROM q GROUP BY week")
    con.execute("INSERT INTO wk SELECT week, t AS tag, count(*) FROM (SELECT week, unnest(Tags) AS t FROM q) JOIN tl ON t = tl.tag GROUP BY week, t")
    print(i, con.execute("SELECT count(*) FROM q").fetchone()[0], flush=True)
con.execute("COPY (SELECT week, tag, sum(n) AS n FROM wk GROUP BY week, tag ORDER BY tag, week) TO 'panel_tag_week.csv' (HEADER)")
con.execute("COPY (SELECT week, sum(n) AS n FROM tot GROUP BY week ORDER BY week) TO 'panel_total_week.csv' (HEADER)")
print(con.execute("SELECT min(week), max(week), count(DISTINCT tag), count(*) FROM (SELECT week, tag FROM wk GROUP BY week, tag)").fetchone())
