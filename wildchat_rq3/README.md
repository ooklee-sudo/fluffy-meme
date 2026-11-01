# RQ3 snapshot design (WildChat-1M, English, 478,498 convs)
Run: `extract.py <shard.parquet> <out.parquet>` per shard, concat to all.parquet, then `design.py`.
Detector patterns are a reconstruction (original v1/v2 code not in this repo). Cutoffs assumed: 3.5-turbo & gpt-4-0314 = 2021-09, gpt-4-1106 = 2023-04, gpt-4-0125 = 2023-12.
Outputs only per-conversation binary features; no text stored. See results.txt.
