"""Calibration of H, v, k from public sources and sensitivity of the main conclusions.
Sources (accessed 2026-10-25): BLS OOH software developers (May 2025): median $64.44/h wage ($134,040/yr in Quick Facts; $135,980 May 2025 in Pay section);
BLS ECEC (private industry, June 2022): benefits = 29.5% of total compensation => loaded multiplier 1/(1-0.295) = 1.418;
SWE-bench Verified annotated time-to-fix (Epoch AI / OpenAI annotation): <15 min 39%, 15 min-1 h 52%, 1-4 h 8%, >4 h 3 issues (METR: estimates likely optimistic);
OpenRouter public price list (per million tokens) for k; published agent cost per task in SWE-bench submission READMEs ($0.60 Bracket, $0.64 Moatless Claude-4-Sonnet, $0.84 Cortexa)."""
import numpy as np
out = []; P = out.append
wage = 64.44; mult = 1/(1-0.295); loaded = wage*mult
P(f"Loaded hourly cost of a software developer: ${wage:.2f}/h x {mult:.3f} = ${loaded:.0f}/h")
shares = [(.39, 10/60), (.52, .5), (.08, 2.0), (.006, 6.0)]            # (share, representative hours; bucket midpoints)
mean_h = sum(s*h for s, h in shares)/sum(s for s, h in shares)
P(f"SWE-bench Verified expected hands-on time (annotated, familiar engineer): {mean_h:.2f} h => H = ${mean_h*loaded:.0f}; unfamiliar-engineer multiplier 2x-4x => H = ${2*mean_h*loaded:.0f}-${4*mean_h*loaded:.0f}")
P(f"Bucket values: <15min => ${10/60*loaded:.0f}; 15-60min => ${0.5*loaded:.0f}; 1-4h => ${2*loaded:.0f}-${4*loaded:.0f}")
# k from token usage x OpenRouter prices
def k_attempt(pt, ct, pin, pout): return (pt*pin + ct*pout)/1e6
prices = {"Gemma-3-4B (small)": (.04, .05), "Qwen3-Coder-30B-A3B": (.07, .28), "Qwen3-Coder": (.30, 1.0), "Claude Sonnet 5.5": (2., 10.), "o4-mini (reasoning)": (1.1, 4.4)}
tok = {"function-level, non-reasoning (RepairBench: ~1,700 in / ~800 out)": (1700, 800), "function-level, reasoning (RepairBench o4-mini: ~1,400 in / ~10,400 out)": (1420, 10408)}
P("\nPer-attempt vendor cost k for function-level repair (price list x observed tokens):")
for tname, (pt, ct) in tok.items():
    P(f"  {tname}")
    for m, (pi, po) in prices.items():
        P(f"     {m:24s} k = ${k_attempt(pt, ct, pi, po):.5f}")
P("Repository-level agentic repair: published cost per task $0.60-$0.84 (one trajectory or one multi-sample pipeline)")
P("Verification cost v per attempt: automated tests only (CI run) ~ $0.01-$0.50; with 2-10 min of manual triage ~ $3-$15 (at $91/h)")
np.save("calibration_loaded.npy", np.array([loaded, mean_h]))
open("results_calibration.txt", "w").write("\n".join(out)); print("\n".join(out))
