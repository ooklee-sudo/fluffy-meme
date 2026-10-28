"""Figure and short report for the fault-injection experiment (reads inject_results.json)."""
import json
from pathlib import Path
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Pt, Inches
from docx.oxml.ns import qn

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "inject_results.json"))
LAB = {"llama8b": "Llama-3.1-8B", "llama70b": "Llama-3.1-70B", "deepseek": "DeepSeek-V3.1"}
MODELS = [m for m in LAB if m in R]

# figure: lag coefficients (exogenous 503, exogenous blame, endogenous) and success by arm
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
ax = axes[0]; off = {"inj": -0.25, "blm": 0.0, "err": 0.25}
col = {"inj": "#2a6f97", "blm": "#e07a5f", "err": "#6c757d"}
name = {"inj": "injected 503", "blm": "injected 'not found'", "err": "agent's own error"}
for mi, m in enumerate(MODELS):
    lg = R[m]["lag_logit"]
    if "error" in lg: continue
    for v in ("inj", "blm", "err"):
        for l in (1, 2, 3):
            b, se = lg[f"{v}{l}"]["b"], lg[f"{v}{l}"]["se"]
            if se > 5: continue  # not identified (too few events)
            x = mi * 4 + l + off[v]
            ax.errorbar(x, b, yerr=1.96 * se, fmt="o", ms=3, color=col[v], label=name[v] if (mi == 0 and l == 1) else None)
ax.axhline(0, color="k", lw=0.6)
ax.set_xticks([mi * 4 + 2 for mi in range(len(MODELS))]); ax.set_xticklabels([LAB[m] for m in MODELS], fontsize=8)
ax.set_ylabel("Log-odds of a later agent error"); ax.set_title("a  Effect of an error 1, 2, 3 calls earlier (left to right)", loc="left", fontsize=9)
ax.legend(fontsize=7, frameon=False)
ax = axes[1]; arms = ["control", "single", "blame", "multi"]; acol = ["#6c757d", "#2a6f97", "#e07a5f", "#8e5ea2"]
for mi, m in enumerate(MODELS):
    for ai, a in enumerate(arms):
        s = R[m]["success"].get(a)
        if not s: continue
        x = mi * 5 + ai
        ax.bar(x, s["rate"], color=acol[ai], label=a if mi == 0 else None)
        ax.errorbar(x, s["rate"], yerr=[[s["rate"] - s["ci"][0]], [s["ci"][1] - s["rate"]]], color="k", lw=0.7, capsize=2)
ax.set_xticks([mi * 5 + 1.5 for mi in range(len(MODELS))]); ax.set_xticklabels([LAB[m] for m in MODELS], fontsize=8)
ax.set_ylabel("Task success (database check)"); ax.set_title("b  Task success by arm", loc="left", fontsize=9)
ax.legend(fontsize=7, frameon=False, ncol=2)
fig.tight_layout(); fig.savefig(HERE / "fig_inject.png", dpi=200)

d = Document(); st = d.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Malgun Gothic")
def P(t, b=False, i=False, size=None):
    p = d.add_paragraph(); r = p.add_run(t); r.bold = b; r.italic = i
    if size: r.font.size = Pt(size)
def TABLE(head, rows):
    t = d.add_table(rows=1, cols=len(head)); t.style = "Light Grid Accent 1"
    for i, h in enumerate(head): t.rows[0].cells[i].text = h
    for row in rows:
        cs = t.add_row().cells
        for i, v in enumerate(row): cs[i].text = str(v)
    d.add_paragraph()
f = lambda x: f"{x:.3f}"
ci = lambda c: f"[{c[0]:.3f}, {c[1]:.3f}]"
P("Fault-injection experiment on τ²-bench: do errors cause errors?", b=True, size=14)
d.add_heading("Design", level=1)
P("Agents: " + ", ".join(LAB[m] for m in MODELS) + ". User simulator: GPT-4.1-mini. Tasks: τ²-bench airline (50) and retail (114). "
  "Arms: control (no injection; a virtual injection call j is drawn), single (the j-th tool call, j ∈ {1, 2, 3}, is not executed and "
  "returns 'service temporarily unavailable (503)'), blame (same, but the error reads like the agent's own mistake, "
  "\"<argument> '<value>' not found\"), multi (from the second call, each call is replaced by the 503 error with probability 0.25, at "
  "most three). Three repetitions per task and arm for the Llama models, two for DeepSeek (upstream rate limits). Temperature 0.5 for "
  "agent and user. Injected calls change nothing in the database and are replayed unchanged in evaluation. An agent error is a tool "
  "call the real environment rejects. Success is the τ²-bench database check.")
d.add_heading("Results", level=1)
rows = []
for m in MODELS:
    s = R[m]["success"]
    rows.append([LAB[m], R[m]["n_runs"], f(s["control"]["rate"]),
                 *(f"{s[a + '_minus_control']['diff']:+.3f} {ci(s[a + '_minus_control']['ci'])}" if a + "_minus_control" in s else "—" for a in ("single", "blame", "multi"))])
TABLE(["Agent", "Runs", "Success (control)", "Δ single", "Δ blame", "Δ multi"], rows)
rows = []
for m in MODELS:
    w = R[m]["window"]
    for a in ("single", "blame"):
        if f"{a}_post" not in w: continue
        rows.append([LAB[m], a, f(w[f"{a}_post"]["control"]), f(w[f"{a}_post"]["treated"]),
                     f"{w[f'{a}_post']['diff']:+.3f} {ci(w[f'{a}_post']['ci'])}", f"{w[f'{a}_pre']['diff']:+.3f} {ci(w[f'{a}_pre']['ci'])}"])
TABLE(["Agent", "Arm", "Error rate after j (control)", "Error rate after j (injected)", "Difference [95% CI]", "Pre-j balance"], rows)
P("Agent-error rate in the five tool calls after the injection point; control runs use the virtual point. Task-clustered bootstrap.", i=True, size=9)
rows = []
for m in MODELS:
    lg = R[m]["lag_logit"]
    if "error" in lg: continue
    g = lambda k: f"{lg[k]['b']:+.2f} ({lg[k]['se']:.2f})" if lg[k]["se"] < 5 else "n.i."
    rows.append([LAB[m], g("inj1"), g("blm1"), g("err1"), g("err2"), f"{R[m]['lag_logit_n']['base_rate']:.3f}"])
TABLE(["Agent", "Injected 503, lag 1", "Injected 'not found', lag 1", "Own error, lag 1", "Own error, lag 2", "Base error rate"], rows)
P("Logit of an agent error on lagged injected and own errors, with task fixed effects and log call position (coefficient, SE). "
  "Injected errors are randomised, so their coefficients are causal; own-error coefficients mix contagion with within-run "
  "persistence of difficulty. n.i.: not identified (too few agent errors).", i=True, size=9)
d.add_picture(str(HERE / "fig_inject.png"), width=Inches(6.3))
d.add_heading("What the experiment shows", level=1)
for t in [
    "System-style failures do not cause agent errors. After an injected 503, the next-call error log-odds fall in every model "
    "(lag-1 coefficients −0.34 to −0.46): agents retry, and the retry usually succeeds.",
    "Errors that look like the agent's own mistake cause a short burst. The lag-1 effect is +0.42 (SE 0.12) for Llama-8B and +0.90 "
    "(SE 0.20) for DeepSeek-V3.1, and it is gone by lag 2–3. Llama-70B shows no burst (−0.56). In Hawkes terms the jump α is "
    "positive for some models but the decay is fast (δ near 0), so the implied branching ratio is small.",
    "Own-error lags are much larger than the causal injected-error lags (lag 1: +0.66, +0.19, +0.59). Most observed clustering "
    "therefore reflects persistence within a run (hard tasks, bad states) rather than errors causing errors; this agrees with the "
    "heterogeneity-adjusted estimates from the SWE-agent data.",
    "The main cost of an error is task failure, not more errors. One injected error lowers DeepSeek-V3.1's success from 0.68 to "
    "0.48 (−0.20, CI −0.26 to −0.14) although it makes almost no further errors; repeated 503s lower Llama-70B's success by 0.09. "
    "Llama-8B succeeds rarely in any arm (0.18), so there is little to lose.",
    "For the theory: the contagion channel (Propositions 2 and 4) is weak and short-lived, so recency-weighted monitoring adds little "
    "over a rule on the last call or the error rate (Proposition 5). Assumption A3 (completion independent of errors) is violated: "
    "errors lower the completion probability. The model should let q fall with errors, which makes early hand-off after an error "
    "valuable even without contagion.",
    "Limits: one benchmark family (customer service), one user simulator, injected errors of two kinds only, temperature 0.5. "
    "Malformed tool arguments from Llama-8B were parsed leniently (first JSON object), so its runs continue where τ²-bench would stop.",
]: d.add_paragraph(t, style="List Bullet")
d.add_heading("한국어 요약", level=1)
for t in [
    "시스템 오류(503)는 에이전트의 다음 오류를 늘리지 않는다. 오히려 줄어든다(재시도 후 성공).",
    "에이전트 자신의 실수처럼 보이는 오류는 8B와 DeepSeek에서 바로 다음 호출의 오류를 늘리지만(로그오즈 +0.42, +0.90), 2–3단계 뒤면 사라진다. 70B는 영향 없음. 전염은 있으나 짧고 약하다.",
    "관찰되는 오류 군집(자기 오류 시차 계수)은 인과 효과보다 훨씬 크다. 군집의 대부분은 전염이 아니라 어려운 과제·나쁜 상태의 지속이다.",
    "오류의 진짜 비용은 '오류 연쇄'가 아니라 '과제 실패'다. DeepSeek은 오류 한 번에 성공률이 0.68에서 0.48로 떨어진다.",
    "이론 수정 방향: 오류가 완료확률 q를 낮추는 경로를 모형에 넣어야 한다(가정 A3 완화). 모니터링 규칙은 최근 가중보다 '직전 호출 실패/오류율' 규칙이면 충분하다.",
]: d.add_paragraph(t, style="List Bullet")
d.save(HERE / "Inject_Results.docx"); print("saved")
