from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

d = Document()
sec = d.sections[0]; sec.left_margin = sec.right_margin = Inches(1); sec.top_margin = sec.bottom_margin = Inches(1)
st = d.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.space_after = Pt(6); st.paragraph_format.line_spacing = 1.15

def P(text, bold=False, italic=False, align=None, size=None, after=None):
    p = d.add_paragraph(); parts = text.split("**")
    for i, t in enumerate(parts):
        r = p.add_run(t); r.bold = bold or (i % 2 == 1); r.italic = italic
        if size: r.font.size = Pt(size)
    if align == "c": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if after is not None: p.paragraph_format.space_after = Pt(after)
    return p

def H(t):
    p = d.add_paragraph(); r = p.add_run(t.upper()); r.bold = True; r.font.size = Pt(11)
    p.paragraph_format.space_before = Pt(10); p.paragraph_format.keep_with_next = True

def H2(t):
    p = d.add_paragraph(); r = p.add_run(t); r.bold = True; r.italic = True
    p.paragraph_format.space_before = Pt(4); p.paragraph_format.keep_with_next = True

def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), color); tcPr.append(s)

def T(caption, header, rows, note=None, widths=None):
    p = d.add_paragraph(); r = p.add_run(caption); r.bold = True; r.font.size = Pt(10); p.paragraph_format.keep_with_next = True
    t = d.add_table(rows=1, cols=len(header)); t.style = "Table Grid"
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""; rr = c.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(9); shade(c, "E7E6E6")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; rr = cells[i].paragraphs[0].add_run(v); rr.font.size = Pt(9)
    for row in t.rows:
        for c in row.cells:
            for pp in c.paragraphs: pp.paragraph_format.space_after = Pt(1); pp.paragraph_format.line_spacing = 1.0
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths): row.cells[i].width = Inches(w)
    if note: P(note, size=9, after=8)
    else: d.add_paragraph().paragraph_format.space_after = Pt(2)

P("Managing Enterprise LLM Maintenance Uncertainties: A Real Options Framework for Cloud API Lifecycles", bold=True, align="c", size=15, after=4)
P("Cloud language-model versions are retired about every year, and replacements are repriced. A real options view and a simulation built from public records show when flexibility in the architecture pays, and when it does not.", italic=True, align="c", after=4)
P("Ook Lee, Hanyang University, Seoul, Korea", align="c", after=10)

P("**Abstract**—Cloud large language model (LLM) application programming interfaces (APIs) shorten the planning horizon of enterprise IT: model versions are retired about a year after release, and successors are repriced. Public records show a median lifetime of 13.8 months for retired Gemini API models (n = 9) and a median notice of 183 days for OpenAI retirements (n = 96). We treat maintenance as real options: choosing among vendors at retirement, and switching early. A 36-month simulation of an enterprise chatbot, with inputs taken from these records, shows that a flexible architecture lowers discounted lifecycle cost by 24% when successor prices are unchanged and by 3% to 77% when they change, depending on how closely vendors' prices move together. We report the break-even flexibility premium for each case. A volatility-based switching threshold did not beat a simple net-present-value rule.", size=10)
P("**Keywords**—large language models, real options, IT governance, vendor lock-in, API deprecation, total cost of ownership", size=10, after=10)

H("Introduction")
P("An enterprise that builds a service on a cloud LLM rents a component that its vendor can withdraw. Vendors publish retirement schedules, name replacements, and sometimes change prices on the same page. For a chief information officer (CIO) the consequence is a recurring cost: each retirement forces a migration of prompts, evaluation sets, integrations, and sometimes fine-tuned assets. Whether to prepare for this cost by building a vendor-neutral layer, and when to move early rather than on the retirement date, are investment questions under uncertainty.")
P("Real options analysis was developed for such questions.¹⁻³ It values the right, but not the obligation, to act later, and it has been applied to information technology (IT) investments.⁴ This article applies the idea to a setting that is new in one respect: the underlying uncertainty is public. Vendors post their deprecation histories, so some inputs to the analysis can be measured instead of guessed. We use that data in three steps. We describe how long models live and how much notice customers receive. We define three options that map onto decisions a CIO can take. We then simulate a 36-month chatbot lifecycle and report where flexibility pays.")
P("Two cautions shape the presentation. First, some inputs cannot be taken from public data, notably migration effort and the way competing vendors' prices move together. We therefore report break-even values rather than a single saving. Second, one result is negative: a switching threshold derived from option theory did not improve on a simple net-present-value (NPV) rule. We report it because it limits what the framework can claim.")

H("What public records show")
P("Table 1 lists the inputs taken from open sources, retrieved on 2 October 2026. Google lists release and shutdown dates for each Gemini API model;⁵ OpenAI lists the announcement date and shutdown date of each deprecation.⁶ Median wages come from the US Bureau of Labor Statistics.⁷")
T("Table 1. Inputs taken from public records.", ["Input", "Value", "Source"], [
  ["Version lifetime, release to retirement", "Median 13.8 months, range 5.7–21.2 (9 retired Gemini API models)", "Google deprecations page"],
  ["Notice before retirement", "Median 183 days; quartiles 97 and 184; 3 of 96 under 90 days (OpenAI)", "OpenAI deprecations page"],
  ["Price ratio of successor generation to predecessor (blended 5:1 input:output list price)", "4.4, 4.1, 0.45 (Flash tier); 1.3, 3.1, 1.5 (Flash-Lite tier)", "Google pricing page; 2.0 prices from third-party aggregators"],
  ["Migration effort in two industry reports", "First migration of a production search application took “a couple of months end-to-end”; a structured regression testbed reduced it to “a couple of weeks” (one case)⁹. Deprecation and migration cycle of “roughly every 12 months” in a question-answering system with 5.3M interactions per month in six regions¹⁰", "Tripathi et al.; Casey et al. (arXiv)"],
  ["Labor cost", "USD 91.5 per hour: median developer pay USD 135,980 (May 2025) times 1.4 for overhead (the factor is an assumption)", "BLS"],
], note="Notice periods are from OpenAI because Google's table gives no announcement dates. Records were extracted with an automated page reader and should be re-verified against the live pages.", widths=[2.0, 3.0, 1.5])
P("Three patterns matter. Lifetimes are short: the median retired model lived about 14 months, and the shortest, two Gemini live-audio models, lived 5.7 and 8.0 months. Notice is usually generous: the median is about six months and only 3 of 96 OpenAI records give less than 90 days. And replacements are not price-neutral. In the Gemini records, the named replacement of Gemini 2.0 Flash is priced at about 8.3 times its predecessor on a blended list price, and that of 2.0 Flash-Lite at about 4.1 times. Google also announced that Gemini 3.6 to 3.8 Flash list prices would rise on 1 January 2027, so prices can change within a version. These price ratios mix price and capability changes, so they are not like-for-like quotes, and we treat them as an upper bound on price risk. Behavior can also shift between versions of the same model,⁸ which adds testing effort to every migration.")
P("Two industry reports give a first check on our effort assumptions. One describes a search application built on GPT-4-32k, which OpenAI deprecated on 6 June 2024 with shutdown a year later, and whose successor GPT-4.5-preview was deprecated on 14 April 2025 with shutdown on 14 July 2025, a window of three months;⁹ its first migration took a couple of months and a structured testbed later cut this to a couple of weeks. The other reports a deprecation and migration cycle of roughly 12 months in a commercial question-answering system and builds a statistical method to limit the cost of evaluating replacements.¹⁰ Both match the order of magnitude of our assumptions: migrations about once a year, effort of weeks rather than days, and a large reduction in effort once an evaluation harness exists (our base case halves the effort; the sensitivity analysis goes down to 0.3 of it). They are single cases that report elapsed time, not person-weeks, so they support the direction of the assumptions, not their values.")

H("Three options")
P("We map maintenance decisions onto options a CIO can recognize.")
P("**Option to choose at retirement.** When a model is retired the firm may move to the vendor's successor or to another vendor or tier. The option exists only if the system can be pointed elsewhere at reasonable cost, which requires a model-abstraction layer and an evaluation harness that decide whether a candidate is good enough.")
P("**Option to switch early.** Between retirements a cheaper or better alternative may appear. Switching costs effort, so the firm waits until the present value of savings is high enough. Option theory gives a threshold: with a price gap that follows a random walk with volatility σ and a discount rate r, the firm should switch when the savings are θ times the switching cost, where θ = β/(β−1) and β is the positive root of ½σ²β(β−1) − r = 0 (a zero-drift form of the McDonald–Siegel result³). At 10% monthly volatility and a 10% annual discount rate, θ is 2.1.")
P("**Option to defer the flexibility investment.** The firm pays a premium up front (the abstraction layer and the harness) and in return lowers the effort of each later migration and gains the first two options. The premium is the price of the options, so the first question for a CIO is the premium at which flexibility stops paying.")

H("Simulation design")
P("We simulate a chatbot for 36 months and compare four strategies on common random draws, with 20,000 lifecycles per scenario. In each lifecycle the first retirement date is drawn from the Gemini lifetimes (scaled by a random model age at adoption), later retirements follow the same draw, notice is drawn from the OpenAI records, and the price ratio at each retirement is drawn from the six observed generation ratios.")
P("The **rigid** strategy is hard-wired and migrates when forced, to the vendor's successor. The **flex** strategy pays a premium of 6 person-weeks, cuts migration effort to half, and at each retirement takes the cheaper of the successor and an alternative vendor. **Flex + NPV** adds early switching whenever the present value of savings exceeds the switching cost. **Flex + threshold** switches early only when savings exceed θ times the switching cost. The alternative vendor's price ratio equals the successor's with probability c (the correlation parameter, base 0.5) and is otherwise an independent draw.")
P("Cost is the present value over 36 months at 10% per year of token spend, migration labor, the premium, an emergency surcharge of 50% when notice is shorter than the time needed (two calendar days per working day of effort), and USD 2,000 per day of outage. It is a variable lifecycle cost; fixed operating costs of the chatbot are excluded. Migration effort is triangular with a minimum of 2, mode of 4 and maximum of 10 person-weeks. Effort, premium, outage cost, and the correlation c are assumptions, not public data, and we vary them. The base token volume is 1 billion tokens per month, which costs about USD 1,250 per month at a Flash-class list price. Code, data, and all outputs are in the project repository.")

H("Results")
H2("Savings depend on how vendors' prices move together")
T("Table 2. Saving relative to the rigid strategy, in percent of its discounted cost (20,000 lifecycles; 95% interval for the base case in brackets).", ["Scenario", "Flex", "Flex + NPV", "Flex + threshold"], [
  ["Base (1B tokens/month, c = 0.5)", "54.1 [49.9, 58.3]", "65.2", "62.9"],
  ["Successor price unchanged", "23.7 [23.2, 24.2]", "24.0", "23.8"],
  ["Alternative price perfectly correlated (c = 1)", "3.3 [3.3, 3.4]", "32.4", "27.9"],
  ["Alternative price independent (c = 0)", "77.4", "80.2", "79.4"],
], widths=[3.0, 1.2, 1.2, 1.2])
P("Table 2 shows the central finding. When the successor is priced like its predecessor, a flexible architecture saves about 24% of variable lifecycle cost, entirely through lower migration effort net of the premium. When retirements come with price increases, as in the Gemini records, the saving depends on whether another vendor can be had at a different price. If vendors' prices rise together there is nothing to choose between and the saving falls to 3%; if they move independently the saving reaches 77%. The data used here cannot tell which case holds, so a CIO should estimate it first.")
H2("Break-even premium")
P("Because the flexible strategy's cost is linear in the premium, the break-even premium is the average cost difference between the rigid and the flexible strategy before the premium, expressed in person-weeks. Table 3 gives it for halved migration effort.")
T("Table 3. Break-even flexibility premium in person-weeks (halved migration effort, no early switching; 95% interval in brackets). The assumed premium in Table 2 is 6 person-weeks.", ["Condition", "Break-even premium"], [
  ["Successor price unchanged (effort 2–4–10 weeks)", "14.8 [14.5, 15.1]"],
  ["Successor price unchanged (effort 4–8–20 weeks)", "73.0 [71.5, 74.5]"],
  ["Prices change, alternative perfectly correlated", "14.5 [14.2, 14.8]"],
  ["Prices change, c = 0.5, 100M tokens/month", "27.1 [25.6, 28.6]"],
  ["Prices change, c = 0.5, 1B tokens/month", "140.3 [125.8, 154.9]"],
  ["Prices change, c = 0, 1B tokens/month", "198.4 [181.2, 215.7]"],
], widths=[4.5, 2.0])
P("Even where flexibility yields no price advantage, the break-even premium is about 15 person-weeks against a base premium of 6, because the simulated firm migrates 4.4 times in three years on average. The break-even grows with token volume and with the independence of vendors' prices, because the choice option then has more to save; at one billion tokens per month it exceeds one hundred person-weeks. These larger values rest on the empirical price ratios, which include capability changes, and should be read as an upper range. The low end, 15 weeks, uses no price shock at all. A firm whose premium for an abstraction layer and evaluation harness is below that low end can therefore justify it on migration effort alone, if retirement frequency is as high as in the public records.")
H2("The threshold rule did not beat the NPV rule")
P("A switching trigger derived from option theory was no better than a plain NPV check. Table 4 compares the two rules in the base case at several price-gap volatilities. The threshold rule had higher cost in all five rows, and the difference was statistically distinguishable from zero in four.")
T("Table 4. Present-value cost of switching rules (USD) and number of early switches per lifecycle (8,000 lifecycles). Difference = NPV rule cost minus threshold cost; a negative value means the NPV rule is cheaper.", ["Monthly price-gap volatility (θ)", "NPV rule", "Threshold rule", "Difference [95% interval]", "Switches NPV / threshold"], [
  ["0.05 (1.5)", "379,401", "390,898", "−11,498 [−29,711, 6,715]", "1.0 / 0.7"],
  ["0.10 (2.1)", "327,059", "352,640", "−25,581 [−40,154, −11,009]", "1.7 / 0.8"],
  ["0.20 (4.2)", "251,262", "309,605", "−58,343 [−68,680, −48,005]", "2.5 / 0.7"],
  ["0.36 (9.7)", "187,709", "291,481", "−103,772 [−111,715, −95,829]", "2.7 / 0.4"],
  ["0.10, successor price unchanged", "102,484", "102,703", "−219 [−240, −199]", "0.3 / 0.0"],
], widths=[1.8, 0.9, 1.0, 1.9, 1.0])
P("The reason lies in the price process. In our model the gap between the cheapest alternative and the current model has no drift, and it resets to zero after each switch, so favorable gaps keep recurring and a firm that switches often benefits. The threshold rule waits for larger savings and therefore switches less. Real markets include frictions that this process omits: alternatives differ in quality, so a lower price may not be a like-for-like gain, and re-evaluating a candidate costs effort. Until the price process is calibrated on like-for-like quotes, we do not claim that the threshold improves timing. We keep it in the framework as a hypothesis and recommend a plain NPV check with an explicit switching cost in practice.")

H("Guidelines for CIOs")
P("**Plan for a replacement every year.** The median retired model lived under 14 months.")
P("**Treat short notice as the exception, not the rule.** Notice was about six months in the median OpenAI case, so the cost of rigidity is mostly effort and price exposure, not outages. Keep a runbook for the 3 of 96 cases with under 90 days.")
P("**Compute the break-even premium before building an abstraction layer.** Multiply the expected number of migrations by the effort a vendor-neutral layer would save, and compare it with the cost of building and maintaining the layer and the evaluation harness. In our simulation the break-even is about 15 person-weeks under the least favorable price assumption, with migration effort halved and a base effort of 2 to 10 person-weeks.")
P("**Track your own tier's list price and at least one alternative's.** How closely they move together decides the value of the vendor choice, and it is the largest source of uncertainty in the results.")
P("**Use a plain NPV check for early switching.** Include the switching cost and the testing effort, and leave out volatility-based thresholds until they are calibrated.")

H("Limitations")
P("The public record is small: nine retired Gemini models, 96 OpenAI retirements, and six price ratios. Google provides no announcement dates, so notice is taken from another vendor. Migration effort, the premium, outage cost, token volume, and price correlation are assumptions that we vary rather than measure, and the savings are conditional on them. Only variable costs are counted. The simulation does not model quality differences between models, contract terms, or regulatory constraints on moving data between vendors. The two industry reports we cite describe single migrations in qualitative terms and give no person-weeks, so a field study of actual migrations, even a single firm's, would replace the largest assumptions. Records and prices were extracted automatically and should be verified before the numbers are quoted.")

H("Conclusion")
P("Public deprecation records make the rhythm of LLM maintenance measurable: about one retirement a year, usually with months of notice, often with a higher price for the replacement. A real options view turns that rhythm into three decisions: the premium for flexibility, the choice at retirement, and the timing of early moves. In simulation, flexibility pays on migration effort alone when the premium is below about 15 person-weeks, and pays more when vendors' prices move independently. The theoretical timing threshold did not beat a plain NPV rule, which marks where the framework needs better price data before it can claim more.")

H("References")
refs = [
 "L. Trigeorgis, Real Options: Managerial Flexibility and Strategy in Resource Allocation, MIT Press, 1996.",
 "A. K. Dixit and R. S. Pindyck, Investment under Uncertainty, Princeton Univ. Press, 1994.",
 "R. McDonald and D. Siegel, “The value of waiting to invest,” Quart. J. Econ., vol. 101, no. 4, pp. 707–727, 1986.",
 "M. Benaroch, “Managing information technology investment risk: A real options perspective,” J. Manage. Inf. Syst., vol. 19, no. 2, pp. 43–84, 2002.",
 "Google, “Gemini API deprecations,” ai.google.dev/gemini-api/docs/deprecations (accessed Oct. 2, 2026).",
 "OpenAI, “Deprecations,” developers.openai.com/api/docs/deprecations (accessed Oct. 2, 2026).",
 "U.S. Bureau of Labor Statistics, “Software developers, quality assurance analysts, and testers,” Occupational Outlook Handbook, bls.gov/ooh (accessed Oct. 2, 2026).",
 "L. Chen, M. Zaharia, and J. Zou, “How is ChatGPT’s behavior changing over time?” arXiv:2307.09009, 2023.",
 "S. Tripathi, P. Nema, A. Halder, S. Qiao, and A. Jindal, “Prompt migration: Stabilizing GenAI applications with evolving large language models,” arXiv:2507.05573, 2025.",
 "E. Casey, D. Roberts, D. Sim, and I. Beaver, “When your LLM reaches end-of-life: A framework for confident model migration in production systems,” arXiv:2604.27082, 2026.",
]
for i, r in enumerate(refs, 1):
    p = P(f"[{i}] {r}", size=9, after=2); p.paragraph_format.left_indent = Inches(0.3); p.paragraph_format.first_line_indent = Inches(-0.3)
P("")
P("**Ook Lee** is a professor at Hanyang University, Seoul. Contact: ooklee@hanyang.ac.kr.", size=9)
d.save("IEEE_Computer_manuscript.docx")
