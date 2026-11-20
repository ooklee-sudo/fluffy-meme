# Study 2 Survey: Participant-Facing Text (English)

> 구현 메모(한국어): 이 파일은 **응답자에게 보이는 영어 문안의 최종본**이다. 흐름, 무선화, 배정표, 규범 값은 `study2_survey_instrument.md`(한국어 구현 문서)를 따른다. `{중괄호}`는 설문 도구에서 값을 넣는 자리이고, `[구현]`은 응답자에게 보이지 않는 메모다. 수치는 모두 확정값(설계값은 지도교수 승인, 성능 표는 `scenario_numbers.py` 출력)이다.
> 문안을 다듬은 원칙: 짧은 문장, 한 문항에 한 가지만 묻기, 유도하는 단어 피하기, 같은 개념은 같은 단어로 쓰기("personal data", "cloud API", "local model"). 전문 용어는 처음 나올 때 풀어 쓴다.

---

## 0. Consent

**About this study**
You are invited to take part in a research study on how professionals make decisions about adopting artificial intelligence (AI) tools in their organizations. The survey takes about 22 minutes. You will read a short news item and four brief business scenarios, and you will be asked what you would choose in each one. All scenarios and figures are hypothetical.

Taking part is voluntary. You may stop at any time without penalty by returning the study on Prolific. Your responses are anonymous and will be used for research purposes only. We will not ask for your name or the name of your employer.

This study has been approved by the Institutional Review Board of Hanyang University (approval no. HY-IRB-2026-11-033). If you have any questions about the study, you can contact the researcher at ooklee@hanyang.ac.kr.

☐ I have read the information above and agree to take part.

---

## 1. Eligibility Questions

[구현] 자격 규칙은 `screening_items.md`. S8은 자격 기준이 아니며 무선 배정 전에 묻는다.

**S1. Which of the following best describes your main job function?**
○ IT, software, or technical operations
○ Data, analytics, or AI/machine learning
○ Information security, privacy, or compliance
○ Procurement, purchasing, or vendor management
○ Finance or business planning
○ General management (for example, owner, CEO, or head of a business unit)
○ Other *(not eligible)*
○ I am not currently employed *(not eligible)*

**S2. Which of the following best describes your current level?**
○ Individual contributor ○ Team leader ○ Manager ○ Director ○ Executive (VP or above) ○ Owner or founder

**S3. When your organization decides which technology or vendors to adopt, what is your role?**
○ I make the final decision.
○ I do not make the final decision, but my recommendation usually determines it.
○ I am a member of the group that makes the decision.
○ I provide input only.
○ I am not involved. *(not eligible)*

**S4. What is the largest annual technology or software budget that you can approve on your own?**
○ None ○ Less than USD 10,000 ○ USD 10,000 to 100,000 ○ USD 100,001 to 1,000,000 ○ More than USD 1,000,000

**S5. How many people does your organization employ?**
○ Fewer than 10 ○ 10 to 49 ○ 50 to 249 ○ 250 to 999 ○ 1,000 or more

**S6. In the past two years, how have you been involved in decisions about adopting AI or large language model (LLM) services, such as APIs or cloud tools?**
○ Not involved ○ I took part in discussions ○ I evaluated candidate options ○ I took part directly in the decision

**S7. How familiar are you with the difference between cloud services and servers that an organization runs itself (on-premises)?**
1 = Not at all familiar … 5 = Extremely familiar

**S8. What is your organization's policy on sending sensitive data, such as customers' personal information, to external AI services (for example, cloud AI APIs)?**
○ It is prohibited entirely.
○ It is allowed only with case-by-case approval.
○ It is allowed under general guidelines, with no approval needed.
○ There is no formal policy; teams decide.
○ I am not sure.

*Message for respondents who are not eligible:*
Thank you for your time. Based on your answers, you are not eligible for this study.

---

## 2. Introduction

In the next part of the survey, you will take the role of a decision-maker at a mid-sized company of about 500 employees. The company handles large volumes of text documents that contain personal information. In each scenario, you will choose between two ways of running an AI system for the coming year:

- a **cloud AI service (cloud API)** provided by an outside vendor, or
- a **local small AI model (local model)** that runs on your company's own servers.

Please decide as a risk-neutral manager. Assume that your company cares only about its expected total cost over the coming year, and that it is neither more nor less cautious than that.

All amounts are in US dollars per year. All figures in this survey are hypothetical.

---

## 3. News Item

[구현] 무선 배정: 아래 두 항목 중 하나만 보여 준다. 길이를 맞췄다.

### 3-A. Incident condition
Please read the following news item.

> **Customer records exposed through an AI vendor**
> Last year, a mid-sized insurance company found that its customers' names, phone numbers, and claim details had been exposed after a security failure at its external AI vendor. The company had to notify thousands of customers and faced an official investigation. Calls to its customer service line stayed far above normal levels for months afterward.
> *(This news item is fictional and was written for this study.)*

### 3-B. Control condition
Please read the following news item.

> **Companies weigh their options for running AI**
> Mid-sized companies are increasingly deciding whether to run AI models in the cloud or on their own servers. Industry analysts describe the choice as a balance between cost, accuracy, and the in-house capacity needed to operate the systems, and note that each company's answer depends on its own circumstances.
> *(This news item is fictional and was written for this study.)*

### 3-C. Everyone
**Thinking about companies in general, what is the probability that a mid-sized company's personal data will be exposed through an external AI vendor at some point in the next 12 months?**
Enter a number from 0 to 100 (%).

---

## 4. Scenarios

[구현] 시나리오 4개. 조건 배정은 라틴 방격 V1–V4(`study2_survey_instrument.md` §4-3), 제시 순서는 무선. 시나리오 2와 3 사이에 주의 점검 A1(§5).

### 4-1. Scenario text (template)

**Scenario {n} of 4: {title}**

Your company wants to use AI to {task}. {data sentence} For the coming year, you must choose between the two options described below.

**Key figures** (per year, in thousands of dollars)

- **Running cost.** The local model is cheaper to run than the cloud API by **${B}k** per year.
- **Errors.** The local model is somewhat less accurate than the cloud API. Its additional errors cost the company **${E}k** per year.
- **Data exposure with the cloud API.** Your company's risk team estimates that there is a **{λ}% chance per year** that personal data is exposed through the vendor. The estimate is based on industry-wide data covering all reported incidents. If an exposure happens, it would cost the company **${L}k** (fines, notification costs, and lost business).
- **Data exposure with the local model.** All data stay in-house, so there is no exposure risk from a vendor.

The cost figures above already take into account the performance difference shown below.

*Performance shown with accuracy only:*

| | Local model | Cloud API |
| --- | --- | --- |
| Accuracy | {acc_local}% | {acc_api}% |

*Performance shown with accuracy and cost per correct answer:*

| | Local model | Cloud API |
| --- | --- | --- |
| Accuracy | {acc_local}% | {acc_api}% |
| Cost per 1,000,000 correct answers (local model: including hardware and electricity) | ${cost_local} | ${cost_api} |

### 4-2. Case-specific text and figures (thousands of dollars per year)

| Case | Title | {task} | {data sentence} |
| --- | --- | --- | --- |
| A | Sorting customer inquiries | sort incoming customer inquiries into topic categories | The inquiries contain customers' names and contact details. |
| B | Extracting fields from HR records | pull key fields out of HR records | The records contain employees' personal information. |
| C | Extracting key terms from contracts | extract key terms from contracts | The contracts contain the names and contact details of the people and companies involved. |
| D | Triaging insurance claims | sort incoming insurance claims into priority categories | The claims contain policyholders' personal and claim information. |

| Case | B | E | L | Entry range for Q3 | Accuracy (local / API) | Cost per 1,000,000 correct answers (local / API) |
| --- | --- | --- | --- | --- | --- | --- |
| A | 80 | 144 | 1,600 | $0 to $400k | 94% / 99% | $2.39 / $29.52 |
| B | 60 | 108 | 1,200 | $0 to $300k | 99% / 100% | $33.27 / $73.09 |
| C | 100 | 180 | 2,000 | $0 to $500k | 99% / 100% | $33.27 / $73.09 |
| D | 120 | 216 | 2,400 | $0 to $600k | 94% / 99% | $2.39 / $29.52 |

The exposure probability {λ} is **2%** or **6%**, depending on the condition (`study2_survey_instrument.md` §4-1).

### 4-3. Questions after each scenario

**Q1.** In this scenario, what is the yearly chance that personal data is exposed through the cloud vendor?
○ 2% ○ 6% ○ 10% ○ 20%
[구현] 선택지 순서 무선. 정답은 그 시나리오의 λ.

**Q2.** Which option would you choose for the coming year?
○ The local model ○ The cloud API

**Q3.** How much would you be willing to pay per year to eliminate the exposure risk of the cloud API altogether, that is, to be certain that no personal data is exposed through a vendor?
*Enter an amount in thousands of dollars, between 0 and {smax}. For example, 120 means $120,000 per year.*
[구현] 숫자 입력(텍스트 입력, Number 검증, 최소 0, 초기값 없음). 안내문의 {smax}는 L/4: A 400, B 300, C 500, D 600. L/4를 넘는 입력은 분석에서 L/4로 자른다.

**Q4.** In your own judgment, what is the chance per year that personal data is exposed through the cloud vendor in this scenario?
Enter a number from 0 to 100 (%).

**Q5.** How large is the local model's quality disadvantage compared with the cloud API in this scenario?
1 = Not large at all … 7 = Extremely large

---

## 5. Additional Questions

**A1. (Attention check; place between scenarios 2 and 3.)** To show that you are reading carefully, please select "Somewhat agree" for this item.
1 = Strongly disagree, 2 = Disagree, 3 = Somewhat disagree, 4 = Neither agree nor disagree, 5 = Somewhat agree, 6 = Agree, 7 = Strongly agree

**Numeracy**
**N1.** A product costs $200 and is discounted by 25%. What is the new price? *(Enter a number.)*
**N2.** A project has a 20% chance of success. Out of 500 similar projects, about how many would you expect to succeed? *(Enter a number.)*
**N3.** A company's costs rise from $80 to $100. By what percentage have they risen? *(Enter a number.)*

**Experience with AI**
**E1.** How familiar are you with large language models (LLMs)? 1 = Not at all familiar … 5 = Extremely familiar
**E2.** How often do you use LLM-based tools at work? ○ Never ○ Rarely ○ Monthly ○ Weekly ○ Daily
**E3.** Has your organization ever built or run its own AI model on its own servers? ○ Yes ○ No ○ Not sure

**Privacy concern** (1 = Strongly disagree … 7 = Strongly agree)
**PC1.** I am concerned about the security of personal data held by outside vendors.
**PC2.** Keeping data inside the company is worth some extra cost.
**PC3.** A data breach at a vendor is a serious business risk.
**PC4.** My organization takes data-handling rules very seriously.

**Risk attitude**
**R1.** In general, how willing are you to take risks when making business decisions? 0 = Not at all willing … 10 = Very willing

**A2. (Attention check.)** For this question, please select the second option from the left.
○ Never ○ Rarely ○ Sometimes ○ Often ○ Always

**P2. Discretion.** Within your organization's current policy, how much discretion do you (or your team) have in choosing between a local model and a cloud AI service for a use case like those in this survey?
1 = No discretion at all … 7 = Full discretion

**P3. Ranking.** [구현] 선택·WTP 뒤에 묻는다. 항목 순서 무선.
Which factors matter most when your organization decides how to source AI for sensitive data? Select your **top three** and rank them (1 = most important).
○ Running cost ○ Accuracy and quality of the AI ○ Security and privacy policy ○ Regulatory and legal compliance ○ Dependence on an outside vendor ○ In-house expertise needed to operate the system

**I1. Industry.** Which of the following best describes your organization's industry?
○ Semiconductors or electronics hardware ○ Software or IT services ○ Finance or insurance ○ Healthcare or pharmaceuticals ○ Defense, aerospace, or government ○ Manufacturing (other) ○ Retail or consumer goods ○ Telecommunications or media ○ Energy or utilities ○ Other

**I2. Intellectual property.** How valuable are trade secrets and intellectual property (for example, designs, source code, or research data) to your organization's competitive position?
1 = Not at all valuable … 7 = Extremely valuable

**I3. Regulated information.** Does your organization handle classified, export-controlled, or similarly regulated information?
○ Yes ○ No ○ Not sure

---

## 6. Consistency Check and Background

**C1.** Before we finish, please confirm your current main job function and level.
- Job function: *(same options as S1)*
- Level: *(same options as S2)*
[구현] S1·S2와 불일치하면 제외(사전등록). 단 IT·데이터·보안(S1 = 1~3)은 같은 묶음으로 본다.

**About you** *(optional)*
- Age: ○ 18 to 24 ○ 25 to 34 ○ 35 to 44 ○ 45 to 54 ○ 55 or older ○ Prefer not to say
- Gender: ○ Woman ○ Man ○ Another gender ○ Prefer not to say
- Highest level of education: ○ High school ○ Bachelor's degree ○ Master's degree ○ Doctorate ○ Other
- Years of work experience: ○ Less than 3 ○ 3 to 5 ○ 6 to 10 ○ 11 to 20 ○ More than 20
- Country of residence: *(drop-down list)*

---

## 7. Debrief

Thank you for taking part. We would like to be open about what this study involved.

- Everything in this survey was fictional: the companies, the figures, the risk team's exposure estimates, and the loss amounts.
- The news item you read, whether it described a data exposure or companies comparing their AI options, was written for this study. Participants were given different news items on purpose. The exposure probabilities shown in the scenarios were the same kind of estimate for everyone.
- The study looks at how professionals weigh risk and performance information when choosing between cloud and local AI. Your answers do not reflect any real decision at your employer, and nothing here is advice on a real purchase.

If you have any questions, please contact ooklee@hanyang.ac.kr. This study was approved by the Institutional Review Board of Hanyang University (HY-IRB-2026-11-033).

Your completion code is {completion code}.
