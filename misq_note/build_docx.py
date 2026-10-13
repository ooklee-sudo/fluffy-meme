import json
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

R = json.load(open("results.json"))
FL, AL, AQ = R["full_linear"], R["active_linear"], R["active_quad"]
doc = Document()
sec = doc.sections[0]
for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, m, Inches(1))
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(12)
st.element.rPr.rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia", "Times New Roman")
st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE; st.paragraph_format.space_after = Pt(0)
for n, sz in (("Heading 1", 12), ("Heading 2", 12)):
    h = doc.styles[n]; h.font.name = "Times New Roman"; h.font.size = Pt(sz); h.font.bold = True
    h.font.italic = (n == "Heading 2"); h.font.color.rgb = None
    h.paragraph_format.space_before = Pt(12); h.paragraph_format.space_after = Pt(0); h.paragraph_format.keep_with_next = True

def P(text="", bold=False, italic=False, align=None, indent=True, single=False):
    p = doc.add_paragraph()
    if indent and not align: p.paragraph_format.first_line_indent = Inches(0.5)
    if align: p.alignment = align
    if single: p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    r = p.add_run(text); r.bold = bold; r.italic = italic
    return p
H1 = lambda t: doc.add_heading(t, 1)
H2 = lambda t: doc.add_heading(t, 2)

def table(rows, widths=None, note=None):
    t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.text = ""; pr = c.paragraphs[0]
            pr.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            if j: pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = pr.add_run(v); r.font.size = Pt(10); r.bold = (i == 0)
    if note: P(note, italic=True, indent=False, single=True).runs[0].font.size = Pt(10)

f = lambda x, d=3: f"{x:,.{d}f}"
P("Overdispersion in Consumer-Generated Content Volume: Why Count Models Matter and Where LLM-Derived Covariates Fit",
  bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
P("Research Note", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)

H1("Abstract")
P(f"Consumer-generated content (CGC) volume is routinely analyzed with ordinary least squares or Poisson regression, "
  f"although such series are discrete, non-negative, and typically far more variable than a Poisson process allows. "
  f"Using {R['n_reviews']:,} Amazon product reviews (February 2009–March 2019) aggregated to a calendar-complete series of "
  f"{R['n_months']} months, we show that monthly review volume has a variance-to-mean ratio of about {R['var_mean']:,.0f} and that a "
  f"negative binomial specification fits dramatically better than a Poisson specification (ΔAIC > 60,000). We also show that "
  f"conclusions about the time trend are fragile when a log-linear trend is imposed on a boom-and-bust series: on the full series the "
  f"negative binomial slope is more than three times the Poisson slope, and on the dense-collection window the Poisson slope is significant while the negative binomial slope is not. Under a quadratic trend on the "
  f"active window, the dispersion parameter falls from {AL['alpha']:.2f} to {AQ['alpha']:.2f}, indicating that much "
  f"apparent overdispersion reflects misspecified mean dynamics. We outline how large language model (LLM)-derived "
  f"attribute and sentiment measures could enter the mean equation, but we do not implement an LLM pipeline here; this "
  f"note is a methodological caution and roadmap, not an empirical test of LLM-based measurement. We provide code to reproduce all results.",
  indent=False, single=True)
P("Keywords: consumer-generated content, online reviews, count data, negative binomial regression, overdispersion, large language models",
  indent=False, single=True)

H1("Introduction")
P("Online reviews are a primary source of market intelligence and a common object of information systems research "
  "(Chevalier and Mayzlin 2006; Duan et al. 2008; Godes and Mayzlin 2004). Many studies analyze review volume—the number of reviews "
  "posted per product or per period—as a dependent variable or as a mediator of sales. Volume is a count, and counts of "
  "this kind are generally overdispersed relative to the Poisson benchmark, which favors negative binomial or related "
  "mixed-Poisson models (Cameron and Trivedi 2013; Hilbe 2011; Lawless 1987). Yet the diagnostics that establish "
  "whether a count model is adequate are seldom reported, and the practical consequences of getting them wrong are rarely shown.")
P("This note makes three contributions. First, using a public review corpus, we document the magnitude of overdispersion in monthly review "
  "volume and the resulting gap between Poisson and negative binomial fit. Second, we show that two routine practices—ignoring dispersion when testing a trend and imposing a log-linear trend on a rise-and-fall series—"
  "can inflate or reverse substantive conclusions about trend, and we identify a likely data-collection artifact that is easily mistaken for demand dynamics. Third, we "
  "describe how LLM-derived text measures (Berger et al. 2020; Brown et al. 2020) could be added to the same count framework, and what "
  "validation that would require. The first two contributions are empirical and are supported by the analysis below; the third is "
  "a research agenda and is not tested here.")

H1("Data")
P(f"We use the Datafiniti Amazon product consumer reviews data, originally released by Datafiniti in May 2019 and redistributed on Zenodo "
  f"under a CC BY 4.0 license (Rajan 2026). The file contains {R['n_reviews']:,} reviews dated February 2009 to March 2019 for "
  f"{R['brand']['Amazon']['products'] + R['brand']['AmazonBasics']['products']} products. Reviews are not confined to the AmazonBasics line: "
  f"{R['brand']['Amazon']['n']:,} reviews ({R['brand']['Amazon']['n'] / R['n_reviews']:.0%}) belong to {R['brand']['Amazon']['products']} products "
  f"listed under the brand \"Amazon\" (including Fire tablets and other Amazon devices), and {R['brand']['AmazonBasics']['n']:,} reviews "
  f"({R['brand']['AmazonBasics']['n'] / R['n_reviews']:.0%}) to {R['brand']['AmazonBasics']['products']} AmazonBasics products. "
  f"We therefore treat the data as a pooled sample of Amazon-owned products rather than a single brand.")
P(f"Review dates were converted to year–month. Timestamps in the file use more than one ISO 8601 layout; default format inference either fails or, if errors are coerced, "
  f"silently discards 62 records, so we parse each record under the full ISO 8601 specification. We construct a calendar-complete "
  f"series of {R['n_months']} months, of which {R['n_zero_months']} contain no reviews and {R['n_nonempty']} contain at least one. "
  f"We retain the empty months, because a count model estimated only on non-empty months conditions on positive counts. "
  f"We also report results for the window in which collection is dense (June 2014–March 2019, 58 months, {sum(v for k, v in R['by_year'].items() if int(k) >= 2014) - 0:,} reviews counting all of 2014 onward)."
  .replace(f"{sum(v for k, v in R['by_year'].items() if int(k) >= 2014) - 0:,} reviews counting all of 2014 onward", "28,296 reviews"))
P("Review volume in this file is a measure of reviews that were collected, not necessarily of reviews written. Almost all reviews are "
  "dated 2015–2017, and counts fall to single digits from June 2018, although the file was assembled in 2019. This pattern is "
  "consistent with a crawl whose coverage changed over time. We return to this point in the Discussion.", indent=True)

H1("Method")
P("Let Y_t be the number of reviews dated in month t. The Poisson model specifies Y_t ~ Poisson(μ_t) with log μ_t = β_0 + β_1 t. The negative binomial (NB2) "
  "model specifies Var(Y_t) = μ_t + α μ_t², with α > 0 the dispersion parameter, and the same mean function. The Poisson model is the "
  "α = 0 special case, so we test it by a likelihood-ratio statistic whose null distribution is a 50:50 mixture of χ²(0) and χ²(1) because α lies on the boundary "
  "(Cameron and Trivedi 2013). We also report the Pearson dispersion statistic of the Poisson fit and compare models by AIC. "
  "Because the series rises and then falls, we add a quadratic term (log μ_t = β_0 + β_1 t + β_2 t²) as a robustness specification "
  "estimated on the active window. All models are estimated by maximum likelihood (code provided), with t measured in years and centered.")

H1("Results")
P(f"Overdispersion. The variance-to-mean ratio of monthly volume is {R['var_mean']:,.0f} on the full series and {R['var_mean_active']:,.0f} on the active window. "
  f"Under the linear-trend Poisson model the Pearson dispersion statistic is {FL['pearson_disp']:,.0f}, far above the value of 1 implied by the model. "
  f"The NB model fits far better (full series: AIC {FL['nb_aic']:,.0f} versus {FL['pois_aic']:,.0f}; likelihood-ratio statistic {FL['lr']:,.0f}, p < 0.001), "
  f"with α̂ = {FL['alpha']:.2f}. The Poisson assumption is clearly untenable.")
P(f"Trend. Table 1 reports the estimates. On the calendar-complete series the Poisson slope is {f(FL['pois_b_month'])} per month, whereas the NB slope is {f(FL['nb_b_month'])} per month "
  f"(SE {f(FL['nb_se_month'])}, p < 0.001). The NB slope is therefore about {FL['nb_b_month'] / FL['pois_b_month']:.1f} times larger than the Poisson slope; "
  f"allowing for overdispersion does not shrink the trend here. A plausible reason is that the NB likelihood down-weights the very large counts of 2016–2017 relative to the Poisson likelihood, so the "
  f"many near-zero early months have more influence on the slope. Neither log-linear fit describes a series that peaks in {R['peak_month'][:4]} and decays "
  f"(Figure 1); a single slope is not a meaningful summary of it.")
P(f"On the active window, the NB log-linear slope is statistically indistinguishable from zero ({f(AL['nb_b_month'])} per month, p = {AL['nb_p'][1]:.2f}) while the Poisson slope is "
  f"{f(AL['pois_b_month'])}, significant only because its standard errors ignore overdispersion. Adding a quadratic term reduces AIC from {AL['nb_aic']:,.0f} to {AQ['nb_aic']:,.0f} and "
  f"lowers the dispersion parameter from {AL['alpha']:.2f} to {AQ['alpha']:.2f}; the quadratic coefficient is strongly negative ({f(AQ['nb_b'][2])}, p < 0.001), "
  f"implying a peak in late 2016. Remaining overdispersion is concentrated in a few months: volume reached {R['peak']:,} in January 2017, "
  f"far above the fitted curve (Figure 1).")
table([["", "Poisson", "Negative binomial", "Poisson", "Negative binomial"],
       ["Window", "Full (122 mo.)", "Full (122 mo.)", "Active (58 mo.)", "Active (58 mo.)"],
       ["Trend, log-linear (per month)", f(FL["pois_b_month"]), f(FL["nb_b_month"]), f(AL["pois_b_month"]), f(AL["nb_b_month"])],
       ["  Standard error", "—", f(FL["nb_se_month"]), "—", f(AL["nb_se_month"])],
       ["Dispersion α", "—", f(FL["alpha"], 2), "—", f(AL["alpha"], 2)],
       ["AIC", f"{FL['pois_aic']:,.0f}", f"{FL['nb_aic']:,.0f}", f"{AL['pois_aic']:,.0f}", f"{AL['nb_aic']:,.0f}"],
       ["Quadratic NB: α / AIC", "", "", "", f"{AQ['alpha']:.2f} / {AQ['nb_aic']:,.0f}"]],
      note="Table 1. Poisson and negative binomial trend models for monthly review volume. Poisson standard errors are omitted because they assume equidispersion and are misleading here.")
doc.add_picture("figure1.png", width=Inches(6.0)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
P("Figure 1. Monthly review volume (n = 28,332) and negative binomial fit with a quadratic trend on the active window.", italic=True, indent=False, single=True)
P("Text covariates. As a descriptive check on the usefulness of text-derived covariates, we computed dictionary-based rates of positive and negative terms per 1,000 words by month "
  "(word lists in analysis.py; months with at least one review in the active window). Their correlations with monthly volume are weak (positive-term rate r = 0.23; negative-term rate r = 0.09), and an NB model with both rates and a quadratic trend "
  "did not converge to a stable solution, so we report no coefficients. We read this as evidence that dictionary measures add little here, not as evidence about LLM measures.")

H1("Discussion")
H2("Implications for research")
P("First, overdispersion testing should be reported, not assumed. In this corpus the Poisson model is rejected by every criterion, and its reported significance "
  "is an artifact of ignoring dispersion. Second, the NB correction does not by itself make a trend estimate interpretable. A log-linear trend imposed on a boom-and-bust series yields a statistically significant but substantively "
  "meaningless slope, and the size of the estimated dispersion depends heavily on how well the mean is specified (α̂ falls from 2.45 to 0.42 once curvature is allowed). "
  "Researchers should therefore model the mean dynamics, or use product fixed effects and release-time controls in panel data, before interpreting α. "
  "Third, sample construction choices—dropping empty months, silent timestamp parsing failures, and pooling distinct brands—change results in ways that are rarely documented.")
H2("A roadmap for LLM-derived covariates")
P("LLMs can extract attribute-level mentions (for example, battery life, price, durability), sentiment, and causal claims from review text at a scale that dictionaries cannot match (Brown et al. 2020; Berger et al. 2020). "
  "Aggregating such measures to the period of the count series yields covariates that can enter the NB mean equation. We did not implement this step. Doing so credibly requires "
  "(i) a fixed, versioned model and prompt, (ii) validation against human-coded samples with reported agreement, (iii) sensitivity of the downstream count-model coefficients to measurement error in the LLM outputs, and "
  "(iv) a design in which the text covariates are not mechanically related to volume. Without these, the incremental value of LLM features remains an open empirical question.")
H2("Limitations")
P("The data come from one retailer, are pooled across Amazon-owned products, and, most importantly, appear to reflect a time-varying crawl. The collapse in counts after 2017 "
  "is unlikely to reflect a real decline in reviewing, so the 'trend' we estimate describes the collected sample and not consumer behavior. The note is also limited to aggregate monthly series; "
  "a product-level panel with product and calendar-time effects would be needed to identify drivers of review volume. Finally, the LLM component is prospective only.")

H1("Conclusion")
P("Review volume is an overdispersed count series for which Poisson models are inadequate. Negative binomial models are the appropriate starting point, but our results show that "
  "their value depends on a correctly specified mean function and a carefully constructed sample. We encourage future work to report dispersion diagnostics, "
  "document sample construction (including empty periods and data-collection coverage), and test LLM-derived measures against human-coded benchmarks before drawing substantive conclusions.")

H1("Data and Code Availability")
P("The data are available at https://doi.org/10.5281/zenodo.18758751. The script analysis.py reproduces every number and Figure 1.", indent=False)

H1("References")
refs = [
 "Berger, J., Humphreys, A., Ludwig, S., Moe, W. W., Netzer, O., and Schweidel, D. A. 2020. “Uniting the Tribes: Using Text for Marketing Insight,” Journal of Marketing (84:1), pp. 1–25.",
 "Brown, T. B., et al. 2020. “Language Models Are Few-Shot Learners,” in Advances in Neural Information Processing Systems (33), pp. 1877–1901.",
 "Cameron, A. C., and Trivedi, P. K. 2013. Regression Analysis of Count Data (2nd ed.), Cambridge, UK: Cambridge University Press.",
 "Chevalier, J. A., and Mayzlin, D. 2006. “The Effect of Word of Mouth on Sales: Online Book Reviews,” Journal of Marketing Research (43:3), pp. 345–354.",
 "Duan, W., Gu, B., and Whinston, A. B. 2008. “Do Online Reviews Matter? An Empirical Investigation of Panel Data,” Decision Support Systems (45:4), pp. 1007–1016.",
 "Godes, D., and Mayzlin, D. 2004. “Using Online Conversations to Study Word-of-Mouth Communication,” Marketing Science (23:4), pp. 545–560.",
 "Hilbe, J. M. 2011. Negative Binomial Regression (2nd ed.), Cambridge, UK: Cambridge University Press.",
 "Lawless, J. F. 1987. “Negative Binomial and Mixed Poisson Regression,” Canadian Journal of Statistics (15:3), pp. 209–225.",
 "Rajan G, S. 2026. “Datafiniti Amazon Product Consumer Reviews Dataset (May 2019)” [Data set], Zenodo, https://doi.org/10.5281/zenodo.18758751 (original data released by Datafiniti, 2019).",
]
for r in refs:
    p = P(r, indent=False); p.paragraph_format.left_indent = Inches(0.5); p.paragraph_format.first_line_indent = Inches(-0.5)

# footer page numbers
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run()
for typ, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if typ: e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), typ)
    else: e = OxmlElement("w:instrText"); e.text = txt
    r._r.append(e)
doc.save("MISQ_Research_Note_CGC_Count_Models_revised.docx")
