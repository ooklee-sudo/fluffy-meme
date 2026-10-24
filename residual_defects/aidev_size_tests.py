"""Build PR-level size and test-code features from AIDev pr_commit_details (streamed, `patch` column skipped).

Rows are (commit, file); additions are gross churn summed over commits, so a file edited in several commits is
counted several times. Unique files are counted separately.
Test path rule: a directory named test/tests/__tests__/spec/specs/e2e/cypress, or a file named test_*, *_test.*,
*.test.*, *.spec.*, *Test(s).java|kt|cs, *_spec.rb.
"""
import pathlib
import re

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem

HERE = pathlib.Path(__file__).parent
OUT = HERE / "data" / "aidev" / "pr_size_tests.parquet"
TEST_DIR = re.compile(r"(^|/)(tests?|__tests__|specs?|e2e|cypress|__mocks__)(/|$)", re.I)
TEST_FILE = re.compile(r"(^|/)(test_[^/]*|[^/]*_tests?\.[^/]*|[^/]*\.(test|spec)\.[^/]*|[^/]*Tests?\.(java|kt|cs|swift)|[^/]*_spec\.rb)$", re.I)


def is_test(path):
    return bool(TEST_DIR.search(path) or TEST_FILE.search(path))


def main():
    fs = HfFileSystem()
    parts, pair_pr, pair_hash, pair_test = [], [], [], []
    with fs.open("datasets/hao-li/AIDev@v5/pr_commit_details.parquet", "rb") as f:
        pf = pq.ParquetFile(f)
        for i in range(pf.metadata.num_row_groups):
            df = pf.read_row_group(i, columns=["pr_id", "filename", "additions", "deletions"]).to_pandas()
            df = df.dropna(subset=["filename"])
            fn = df.filename.values
            uniq = pd.unique(fn)
            test_map = dict(zip(uniq, (is_test(p) for p in uniq)))
            df["is_test"] = [test_map[p] for p in fn]
            df["add_"] = df.additions.fillna(0)
            df["del_"] = df.deletions.fillna(0)
            df["test_add"] = np.where(df.is_test, df["add_"], 0.0)
            parts.append(df.groupby("pr_id").agg(file_rows=("filename", "size"), gross_add=("add_", "sum"),
                                                gross_del=("del_", "sum"), test_add=("test_add", "sum")))
            pair_pr.append(df.pr_id.values)
            pair_hash.append(pd.util.hash_array(fn))
            pair_test.append(df.is_test.values)
            if i % 10 == 0:
                print("row group", i, "/", pf.metadata.num_row_groups, flush=True)
    agg = pd.concat(parts).groupby(level=0).sum()
    pairs = pd.DataFrame({"pr_id": np.concatenate(pair_pr), "h": np.concatenate(pair_hash),
                          "t": np.concatenate(pair_test)}).drop_duplicates(["pr_id", "h"])
    u = pairs.groupby("pr_id").agg(n_files=("h", "size"), n_test_files=("t", "sum"))
    out = agg.join(u).reset_index().rename(columns={"pr_id": "id"})
    out["test_share"] = np.where(out.gross_add > 0, out.test_add / out.gross_add, np.nan)
    out["any_test"] = (out.n_test_files > 0).astype(float)
    out.to_parquet(OUT)
    print(len(out), "PRs with file details")
    print(out.describe().T[["mean", "50%"]].round(3).to_string())


if __name__ == "__main__":
    main()
