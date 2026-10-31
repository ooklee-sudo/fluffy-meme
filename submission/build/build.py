"""Split the exported paper into anonymized manuscript + online appendix (markdown)."""
import re
src = open("paper_source.md", encoding="utf-8").read()
src = src.replace("&#91;", "[")
lines = src.split("\n")
assert lines[2].startswith("Oct 30, 2026"), lines[2]
del lines[2]  # byline (author identity) removed for blind review
s = "\n".join(lines)

# LaTeX code blocks -> display math
s = re.sub(r"```latex\n(.*?)\n```", lambda m: "$$\n" + m.group(1).strip() + "\n$$", s, flags=re.S)

# Figures
figs = [
 ("Figure1_AIO_event_study.png", "Figure 1. Effect of the AI Overviews launch on Wikipedia pageviews, August 2024 cohort",
  "Effect on pageviews in percent (log points × 100) by months since launch, relative to not-yet-treated editions; month −1 is the reference. Bars are 95% bootstrap intervals (499 draws, resampling editions)."),
 ("Figure2_search_vs_meta.png", "Figure 2. Year-over-year revenue growth of Google Search & other and of Meta, 2019Q4–2026Q3",
  "Growth = 100 × log difference over four quarters. Shaded area: Apple's App Tracking Transparency shock to Meta. Placebo breaks before ChatGPT fit as well (Table 7)."),
 ("Figure3_clicks_cpc.png", "Figure 3. Paid-click and cost-per-click growth, Google Search & other, 2023–2026",
  "Year-over-year change in percent for the first three quarters of each year (Q4 is not reported separately)."),
 ("Figure4_bing_share.png", "Figure 4. Bing's share of search referrals, January 2019–August 2026",
  "Worldwide desktop trend in percentage points per month: +0.10 before Bing Chat, +0.26 after, +0.02 after AI Overviews, −0.16 after AI Mode."),
 ("Figure5_trust_shock.png", "Figure 5. English Wikipedia desktop views relative to 10 large editions around the AI Overviews errors of May 2024",
  "Year-over-year growth of English minus 10 large editions, percentage points, 7-day centered average. Horizontal lines are period means."),
]
pat = re.compile(r"\[embedded content: (.*?)\\\]")
found = pat.findall(s); assert len(found) == 5, found
it = iter(figs)
def rep(m):
    f, cap, note = next(it)
    return f"{cap}.\n\n![](../figures/{f}){{width=6.3in}}\n\n*Note.* {note} *Source.* {m.group(1)}."
s = pat.sub(rep, s)

s = s.replace("All proofs are in the Appendix.", "All proofs are in Online Appendix A.")
s = s.replace("Replication files (price data, scraped SEC revenue series, and estimation code) are available from the authors.",
              "Replication files (data, data-collection scripts, and estimation code) are provided in the replication package described in Online Appendix B.")
assert "Online Appendix A" in s and "Online Appendix B" in s

main, appx = s.split("## Appendix: Proofs")
main = main.replace("**Funding and conflicts of interest.** \\[Author to complete.\\]\n", "")
main = main.replace("## Statements", "## Disclosures")
open("manuscript.md", "w", encoding="utf-8").write(main.rstrip() + "\n")

title = lines[0].lstrip("# ").strip()
oa = f"""# Online Appendix

**{title}**

## Appendix A. Proofs
{appx.strip()}

## Appendix B. Data and Replication Package

All analyses use publicly available data. The replication package (replication_package.zip) contains the data-collection scripts, the analysis scripts that produce each table and figure, the numerical examples for Propositions 8–10, small hand-coded datasets (event dates, rollout dates by edition and country, launch dates and revenue for 17 search engines), and the processed data for the trust-shock analysis. Its README maps every script to the corresponding table or figure and lists data sources, access dates, run order, and software requirements.

Raw data that third parties do not permit us to redistribute (for example, Google Trends extracts and Wikimedia hourly dump files) are re-downloaded by the collection scripts. Google Trends is rate-limited and returns sampled indices, so re-downloaded series can differ slightly from ours.

**Data sources.** Wikimedia hourly projectviews dumps (dumps.wikimedia.org); Google Trends (via pytrends); Eurostat datasets isoc_ai_iaiu and isoc_ci_ifp_fu; World Bank World Development Indicators (NY.GDP.PCAP.CD, IT.NET.USER.ZS, SP.POP.TOTL); StatCounter Global Stats; Alphabet, Meta, and Microsoft filings on SEC EDGAR (Forms 8-K, 10-Q, XBRL); daily stock prices for the event study; and launch dates from company announcements, archived help pages, and trade press as cited in the text. All sources were accessed in October 2026.

**Figure data.** The values plotted in Figures 1–5 are provided in figures/figure_data/ together with the plotting script (make_figures.py).
"""
open("online_appendix.md", "w", encoding="utf-8").write(oa)
print(len(main.split()), "words main;", len(oa.split()), "words appendix")
