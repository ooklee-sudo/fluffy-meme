"""Generate Qualtrics import assets for Study 2 from one source of truth.

  python quant_cost/qualtrics/build_assets.py

Writes into quant_cost/qualtrics/:
  loop_merge_V1.tsv ... V4.tsv   rows = scenario cells C1..C4 (Latin square version), columns = Loop & Merge fields 1..13
  scenario_body.html             participant-facing scenario text with ${lm://Field/n} pipes
  import_questions.txt           static questions in Qualtrics "Advanced Format" (consent, eligibility, covariates, ...)
  field_map.md                   which Loop & Merge column is which field

Numbers are the final design values (advisor-approved) and measured performance (study2_survey_english.md).
These files are UNTESTED inside Qualtrics (no Qualtrics access where they were generated): import into a test survey first.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

CASES = {
    "A": dict(title="Sorting customer inquiries", task="sort incoming customer inquiries into topic categories",
              data="The inquiries contain customers' names and contact details.",
              B=80, E=144, L=1600, accL=94, accA=99, costL="2.39", costA="29.52"),
    "B": dict(title="Extracting fields from HR records", task="pull key fields out of HR records",
              data="The records contain employees' personal information.",
              B=60, E=108, L=1200, accL=99, accA=100, costL="33.27", costA="73.09"),
    "C": dict(title="Extracting key terms from contracts", task="extract key terms from contracts",
              data="The contracts contain the names and contact details of the people and companies involved.",
              B=100, E=180, L=2000, accL=99, accA=100, costL="33.27", costA="73.09"),
    "D": dict(title="Triaging insurance claims", task="sort incoming insurance claims into priority categories",
              data="The claims contain policyholders' personal and claim information.",
              B=120, E=216, L=2400, accL=94, accA=99, costL="2.39", costA="29.52"),
}
# cell -> (exposure probability in %, performance format: 1 = accuracy only, 2 = accuracy + cost per correct answer)
CELLS = {"C1": (2, 1), "C2": (2, 2), "C3": (6, 1), "C4": (6, 2)}
# Latin square: version -> case in cells C1..C4
LATIN = {"V1": "ABCD", "V2": "BCDA", "V3": "CDAB", "V4": "DABC"}

FIELDS = ["cell", "case", "title", "task", "data", "B", "E", "L", "lam", "accL", "accA", "costrow", "smax"]


def costrow(c):
    return ("<tr><td>Cost per 1,000,000 correct answers (local model: including hardware and electricity)</td>"
            f"<td>${c['costL']}</td><td>${c['costA']}</td></tr>")


def rows_for(version):
    out = []
    for cell, case in zip(CELLS, LATIN[version]):
        lam, perf = CELLS[cell]
        c = CASES[case]
        out.append([cell, case, c["title"], c["task"], c["data"], c["B"], c["E"], c["L"], lam, c["accL"], c["accA"],
                    costrow(c) if perf == 2 else "", c["L"] // 4])
    return out


def write_tsv():
    for v in LATIN:
        with open(os.path.join(HERE, f"loop_merge_{v}.tsv"), "w", encoding="utf-8", newline="") as f:
            for r in rows_for(v):
                assert all("\t" not in str(x) and "\n" not in str(x) for x in r)
                f.write("\t".join(str(x) for x in r) + "\n")


SCENARIO_HTML = """<p><b>Scenario ${lm://CurrentLoopNumber} of 4: ${lm://Field/3}</b></p>
<p>Your company wants to use AI to ${lm://Field/4}. ${lm://Field/5} For the coming year, you must choose between the two options described below.</p>
<p><b>Key figures</b> (per year, in thousands of dollars)</p>
<ul>
<li><b>Running cost.</b> The local model is cheaper to run than the cloud API by <b>$${lm://Field/6}k</b> per year.</li>
<li><b>Errors.</b> The local model is somewhat less accurate than the cloud API. Its additional errors cost the company <b>$${lm://Field/7}k</b> per year.</li>
<li><b>Data exposure with the cloud API.</b> Your company's risk team estimates that there is a <b>${lm://Field/9}% chance per year</b> that personal data is exposed through the vendor. The estimate is based on industry-wide data covering all reported incidents. If an exposure happens, it would cost the company <b>$${lm://Field/8}k</b> (fines, notification costs, and lost business).</li>
<li><b>Data exposure with the local model.</b> All data stay in-house, so there is no exposure risk from a vendor.</li>
</ul>
<p>The cost figures above already take into account the performance difference shown below.</p>
<table border="1" cellpadding="6" style="border-collapse:collapse">
<tr><th></th><th>Local model</th><th>Cloud API</th></tr>
<tr><td>Accuracy</td><td>${lm://Field/10}%</td><td>${lm://Field/11}%</td></tr>
${lm://Field/12}
</table>
"""

FIELD_MAP = """# Loop & Merge field map (Study 2)

Qualtrics refers to loop columns by number: `${lm://Field/n}`. Paste each `loop_merge_V*.tsv` into the **Static Loop & Merge** table of its block (4 rows = cells C1 to C4, 13 columns).

| Field | Content | Used in |
| --- | --- | --- |
| 1 | cell (C1 to C4) | analysis: identifies the condition |
| 2 | case code (A to D) | analysis |
| 3 | scenario title | heading |
| 4 | task description | first paragraph |
| 5 | data sentence | first paragraph |
| 6 | B, running cost saving (thousand dollars) | key figures |
| 7 | E, cost of extra errors (thousand dollars) | key figures |
| 8 | L, loss if exposure occurs (thousand dollars) | key figures; WTP range |
| 9 | exposure probability (%): 2 or 6 | key figures |
| 10 | accuracy, local model (%) | performance table |
| 11 | accuracy, cloud API (%) | performance table |
| 12 | cost-per-correct row (HTML), empty for the accuracy-only cells | performance table |
| 13 | upper limit of the WTP question (L/4, thousand dollars) | Q3 prompt |

Cell definitions: C1 = 2%, accuracy only; C2 = 2%, accuracy + cost; C3 = 6%, accuracy only; C4 = 6%, accuracy + cost.
Responses are exported with the loop row number as a column prefix (`1_Q2`, `2_Q2`, ...), so the row number identifies the cell regardless of presentation order.
"""

# ---------------------------------------------------------------- static questions (Advanced Format)
TXT = r"""[[AdvancedFormat]]

[[Block:Consent]]

[[Question:DB]]
<b>About this study</b><br><br>
You are invited to take part in a research study on how professionals make decisions about adopting artificial intelligence (AI) tools in their organizations. The survey takes about 19 minutes. You will read a short news item and four brief business scenarios, and you will be asked what you would choose in each one. All scenarios and figures are hypothetical.<br><br>
Taking part is voluntary. You may stop at any time without penalty by returning the study on Prolific. Your responses are anonymous and will be used for research purposes only. We will not ask for your name or the name of your employer.<br><br>
This study has been approved by the Institutional Review Board of Hanyang University (approval no. HY-IRB-2026-11-033). If you have any questions about the study, you can contact the researcher at ooklee@hanyang.ac.kr.

[[Question:MC]]
[[ID:consent]]
I have read the information above and agree to take part.
[[Choices]]
I agree to take part.
I do not agree.

[[Block:Eligibility]]

[[Question:MC]]
[[ID:S1]]
Which of the following best describes your main job function?
[[Choices]]
IT, software, or technical operations
Data, analytics, or AI/machine learning
Information security, privacy, or compliance
Procurement, purchasing, or vendor management
Finance or business planning
General management (for example, owner, CEO, or head of a business unit)
Other
I am not currently employed

[[Question:MC]]
[[ID:S2]]
Which of the following best describes your current level?
[[Choices]]
Individual contributor
Team leader
Manager
Director
Executive (VP or above)
Owner or founder

[[Question:MC]]
[[ID:S3]]
When your organization decides which technology or vendors to adopt, what is your role?
[[Choices]]
I make the final decision.
I do not make the final decision, but my recommendation usually determines it.
I am a member of the group that makes the decision.
I provide input only.
I am not involved.

[[Question:MC]]
[[ID:S4]]
What is the largest annual technology or software budget that you can approve on your own?
[[Choices]]
None
Less than USD 10,000
USD 10,000 to 100,000
USD 100,001 to 1,000,000
More than USD 1,000,000

[[Question:MC]]
[[ID:S5]]
How many people does your organization employ?
[[Choices]]
Fewer than 10
10 to 49
50 to 249
250 to 999
1,000 or more

[[Question:MC]]
[[ID:S6]]
In the past two years, how have you been involved in decisions about adopting AI or large language model (LLM) services, such as APIs or cloud tools?
[[Choices]]
Not involved
I took part in discussions
I evaluated candidate options
I took part directly in the decision

[[Question:MC]]
[[ID:S7]]
How familiar are you with the difference between cloud services and servers that an organization runs itself (on-premises)?
[[Choices]]
1 = Not at all familiar
2
3
4
5 = Extremely familiar

[[Question:MC]]
[[ID:S8]]
What is your organization's policy on sending sensitive data, such as customers' personal information, to external AI services (for example, cloud AI APIs)?
[[Choices]]
It is prohibited entirely.
It is allowed only with case-by-case approval.
It is allowed under general guidelines, with no approval needed.
There is no formal policy; teams decide.
I am not sure.

[[Block:Introduction]]

[[Question:DB]]
In the next part of the survey, you will take the role of a decision-maker at a mid-sized company of about 500 employees. The company handles large volumes of text documents that contain personal information. In each scenario, you will choose between two ways of running an AI system for the coming year:<br><br>
&bull; a <b>cloud AI service (cloud API)</b> provided by an outside vendor, or<br>
&bull; a <b>local small AI model (local model)</b> that runs on your company's own servers.<br><br>
Please decide as a risk-neutral manager. Assume that your company cares only about its expected total cost over the coming year, and that it is neither more nor less cautious than that.<br><br>
All amounts are in US dollars per year. All figures in this survey are hypothetical.

[[Block:News_Incident]]

[[Question:DB]]
Please read the following news item.<br><br>
<b>Customer records exposed through an AI vendor</b><br>
Last year, a mid-sized insurance company found that its customers' names, phone numbers, and claim details had been exposed after a security failure at its external AI vendor. The company had to notify thousands of customers and faced an official investigation. Calls to its customer service line stayed far above normal levels for months afterward.<br>
<i>(This news item is fictional and was written for this study.)</i>

[[Block:News_Control]]

[[Question:DB]]
Please read the following news item.<br><br>
<b>Companies weigh their options for running AI</b><br>
Mid-sized companies are increasingly deciding whether to run AI models in the cloud or on their own servers. Industry analysts describe the choice as a balance between cost, accuracy, and the in-house capacity needed to operate the systems, and note that each company's answer depends on its own circumstances.<br>
<i>(This news item is fictional and was written for this study.)</i>

[[Block:GeneralProbability]]

[[Question:TextEntry]]
[[ID:GP]]
Thinking about companies in general, what is the probability that a mid-sized company's personal data will be exposed through an external AI vendor at some point in the next 12 months? Enter a number from 0 to 100 (%).

[[Block:Scenario_TEMPLATE]]

[[Question:DB]]
[[ID:ScenarioText]]
PASTE scenario_body.html HERE (HTML view), then copy this block three times (one per Latin-square version).

[[Question:MC]]
[[ID:Q1]]
In this scenario, what is the yearly chance that personal data is exposed through the cloud vendor?
[[Choices]]
2%
6%
10%
20%

[[Question:MC]]
[[ID:Q2]]
Which option would you choose for the coming year?
[[Choices]]
The local model
The cloud API

[[Question:TextEntry]]
[[ID:Q3]]
How much would you be willing to pay per year to eliminate the exposure risk of the cloud API altogether, that is, to be certain that no personal data is exposed through a vendor?<br><br>
<i>Enter an amount in thousands of dollars, between 0 and ${lm://Field/13}. For example, 120 means $120,000 per year.</i>

[[Question:TextEntry]]
[[ID:Q4]]
In your own judgment, what is the chance per year that personal data is exposed through the cloud vendor in this scenario? Enter a number from 0 to 100 (%).

[[Question:MC]]
[[ID:Q5]]
How large is the local model's quality disadvantage compared with the cloud API in this scenario?
[[Choices]]
1 = Not large at all
2
3
4
5
6
7 = Extremely large

[[Block:AttentionCheck_A1]]

[[Question:MC]]
[[ID:A1]]
To show that you are reading carefully, please select "Somewhat agree" for this item.
[[Choices]]
Strongly disagree
Disagree
Somewhat disagree
Neither agree nor disagree
Somewhat agree
Agree
Strongly agree

[[Block:Numeracy_Experience]]

[[Question:TextEntry]]
[[ID:N1]]
A product costs $200 and is discounted by 25%. What is the new price? (Enter a number.)

[[Question:TextEntry]]
[[ID:N2]]
A project has a 20% chance of success. Out of 500 similar projects, about how many would you expect to succeed? (Enter a number.)

[[Question:TextEntry]]
[[ID:N3]]
A company's costs rise from $80 to $100. By what percentage have they risen? (Enter a number.)

[[Question:MC]]
[[ID:E1]]
How familiar are you with large language models (LLMs)?
[[Choices]]
1 = Not at all familiar
2
3
4
5 = Extremely familiar

[[Question:MC]]
[[ID:E2]]
How often do you use LLM-based tools at work?
[[Choices]]
Never
Rarely
Monthly
Weekly
Daily

[[Question:MC]]
[[ID:E3]]
Has your organization ever built or run its own AI model on its own servers?
[[Choices]]
Yes
No
Not sure

[[Block:PrivacyConcern_Risk]]

[[Question:Matrix]]
[[ID:PC]]
How much do you agree with each statement?
[[Choices]]
I am concerned about the security of personal data held by outside vendors.
Keeping data inside the company is worth some extra cost.
A data breach at a vendor is a serious business risk.
My organization takes data-handling rules very seriously.
[[Answers]]
Strongly disagree
Disagree
Somewhat disagree
Neither agree nor disagree
Somewhat agree
Agree
Strongly agree

[[Question:MC]]
[[ID:R1]]
In general, how willing are you to take risks when making business decisions?
[[Choices]]
0 = Not at all willing
1
2
3
4
5
6
7
8
9
10 = Very willing

[[Question:MC]]
[[ID:A2]]
For this question, please select the second option from the left.
[[Choices]]
Never
Rarely
Sometimes
Often
Always

[[Block:Discretion_Industry]]

[[Question:MC]]
[[ID:P2]]
Within your organization's current policy, how much discretion do you (or your team) have in choosing between a local model and a cloud AI service for a use case like those in this survey?
[[Choices]]
1 = No discretion at all
2
3
4
5
6
7 = Full discretion

[[Question:MC]]
[[ID:I1]]
Which of the following best describes your organization's industry?
[[Choices]]
Semiconductors or electronics hardware
Software or IT services
Finance or insurance
Healthcare or pharmaceuticals
Defense, aerospace, or government
Manufacturing (other)
Retail or consumer goods
Telecommunications or media
Energy or utilities
Other

[[Question:MC]]
[[ID:I2]]
How valuable are trade secrets and intellectual property (for example, designs, source code, or research data) to your organization's competitive position?
[[Choices]]
1 = Not at all valuable
2
3
4
5
6
7 = Extremely valuable

[[Question:MC]]
[[ID:I3]]
Does your organization handle classified, export-controlled, or similarly regulated information?
[[Choices]]
Yes
No
Not sure

[[Block:Demographics]]

[[Question:MC]]
[[ID:AGE]]
What is your age? (optional)
[[Choices]]
18 to 24
25 to 34
35 to 44
45 to 54
55 or older
Prefer not to say

[[Question:MC]]
[[ID:GENDER]]
What is your gender? (optional)
[[Choices]]
Woman
Man
Another gender
Prefer not to say

[[Question:MC]]
[[ID:EDU]]
What is your highest level of education? (optional)
[[Choices]]
High school
Bachelor's degree
Master's degree
Doctorate
Other

[[Question:MC]]
[[ID:EXP]]
How many years of work experience do you have? (optional)
[[Choices]]
Less than 3
3 to 5
6 to 10
11 to 20
More than 20

[[Block:Debrief]]

[[Question:DB]]
Thank you for taking part. We would like to be open about what this study involved.<br><br>
&bull; Everything in this survey was fictional: the companies, the figures, the risk team's exposure estimates, and the loss amounts.<br>
&bull; The news item you read, whether it described a data exposure or companies comparing their AI options, was written for this study. Participants were given different news items on purpose. The exposure probabilities shown in the scenarios were the same kind of estimate for everyone.<br>
&bull; The study looks at how professionals weigh risk and performance information when choosing between cloud and local AI. Your answers do not reflect any real decision at your employer, and nothing here is advice on a real purchase.<br><br>
If you have any questions, please contact ooklee@hanyang.ac.kr. This study was approved by the Institutional Review Board of Hanyang University (HY-IRB-2026-11-033).
"""


def main():
    write_tsv()
    with open(os.path.join(HERE, "scenario_body.html"), "w", encoding="utf-8") as f:
        f.write(SCENARIO_HTML)
    with open(os.path.join(HERE, "import_questions.txt"), "w", encoding="utf-8") as f:
        f.write(TXT)
    with open(os.path.join(HERE, "field_map.md"), "w", encoding="utf-8") as f:
        f.write(FIELD_MAP)
    print("wrote", ", ".join(sorted(x for x in os.listdir(HERE) if x != "build_assets.py")))


if __name__ == "__main__":
    main()
