"""Table 2 and the execution-test accuracies (Section 4.1), computed from stored files validity_check.json and results_tests_v2.json."""
import json, statistics as st, collections
res = json.load(open("validity_check.json"))
print("%-9s %4s %8s %9s %10s" % ("model", "n", "R1", "R2", "mean len"))
for m in ("gpt-3.5", "gpt-4o", "gpt-4"):
    s = [r for r in res if r["model"] == m]
    print("%-9s %4d %7.1f%% %8.1f%% %10.0f" % (m, len(s), 100 * st.mean(r["r1"] for r in s), 100 * st.mean(r["r2"] for r in s), st.mean(r["len"] for r in s)))
q30 = {r["qid"] for r in res if r["model"] == "gpt-4"}
print("same %d questions for all three models:" % len(q30))
for m in ("gpt-3.5", "gpt-4o", "gpt-4"):
    s = [r for r in res if r["model"] == m and r["qid"] in q30]
    print("  %-9s R1 %.1f%%  R2 %.1f%%" % (m, 100 * st.mean(r["r1"] for r in s), 100 * st.mean(r["r2"] for r in s)))
t = json.load(open("results_tests_v2.json"))
print("\nexecution-based tests (%d questions with validated tests):" % len({x["qid"] for x in t}))
for m in ("gpt-3.5", "gpt-4", "gpt-4o", "llama-3.1-8b"):
    s = [x["exec_correct"] for x in t if x["model"] == m]; print("  %-13s %d/%d = %.2f" % (m, sum(s), len(s), sum(s) / len(s)))
