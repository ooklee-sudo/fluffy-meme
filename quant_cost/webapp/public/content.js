// All participant-facing text and design numbers for Study 2 (final values; see quant_cost/study2_survey_english.md).
// Numbers: B, E, L in thousands of dollars per year; accuracy in %; cost per 1,000,000 correct answers in dollars.
var CONTENT = {
  consentHTML:
    "<h2>About this study</h2>" +
    "<p>You are invited to take part in a research study on how professionals make decisions about adopting artificial intelligence (AI) tools in their organizations. The survey takes about 22 minutes. You will read a short news item and four brief business scenarios, and you will be asked what you would choose in each one. All scenarios and figures are hypothetical.</p>" +
    "<p>Taking part is voluntary. You may stop at any time without penalty by returning the study on Prolific. Your responses are anonymous and will be used for research purposes only. We will not ask for your name or the name of your employer.</p>" +
    "<p>This study has been approved by the Institutional Review Board of Hanyang University (approval no. HY-IRB-2026-11-033). If you have any questions about the study, you can contact the researcher at ooklee@hanyang.ac.kr.</p>",
  consentLabel: "I have read the information above and agree to take part.",
  screenoutMessage: "Thank you for your time. Based on your answers, you are not eligible for this study.",
  declineMessage: "Thank you for your time. You have chosen not to take part, so the survey ends here. You can return the study on Prolific.",

  eligibility: [
    { id: "S1", text: "Which of the following best describes your main job function?", options: [
      "IT, software, or technical operations", "Data, analytics, or AI/machine learning",
      "Information security, privacy, or compliance", "Procurement, purchasing, or vendor management",
      "Finance or business planning", "General management (for example, owner, CEO, or head of a business unit)",
      "Other", "I am not currently employed"] },
    { id: "S2", text: "Which of the following best describes your current level?", options: [
      "Individual contributor", "Team leader", "Manager", "Director", "Executive (VP or above)", "Owner or founder"] },
    { id: "S3", text: "When your organization decides which technology or vendors to adopt, what is your role?", options: [
      "I make the final decision.", "I do not make the final decision, but my recommendation usually determines it.",
      "I am a member of the group that makes the decision.", "I provide input only.", "I am not involved."] },
    { id: "S4", text: "What is the largest annual technology or software budget that you can approve on your own?", options: [
      "None", "Less than USD 10,000", "USD 10,000 to 100,000", "USD 100,001 to 1,000,000", "More than USD 1,000,000"] },
    { id: "S5", text: "How many people does your organization employ?", options: [
      "Fewer than 10", "10 to 49", "50 to 249", "250 to 999", "1,000 or more"] },
    { id: "S6", text: "In the past two years, how have you been involved in decisions about adopting AI or large language model (LLM) services, such as APIs or cloud tools?", options: [
      "Not involved", "I took part in discussions", "I evaluated candidate options", "I took part directly in the decision"] },
    { id: "S7", text: "How familiar are you with the difference between cloud services and servers that an organization runs itself (on-premises)?", options: [
      "1 = Not at all familiar", "2", "3", "4", "5 = Extremely familiar"] },
    { id: "S8", text: "What is your organization's policy on sending sensitive data, such as customers' personal information, to external AI services (for example, cloud AI APIs)?", options: [
      "It is prohibited entirely.", "It is allowed only with case-by-case approval.",
      "It is allowed under general guidelines, with no approval needed.", "There is no formal policy; teams decide.", "I am not sure."] }
  ],

  introHTML:
    "<p>In the next part of the survey, you will take the role of a decision-maker at a mid-sized company of about 500 employees. The company handles large volumes of text documents that contain personal information. In each scenario, you will choose between two ways of running an AI system for the coming year:</p>" +
    "<ul><li>a <b>cloud AI service (cloud API)</b> provided by an outside vendor, or</li>" +
    "<li>a <b>local small AI model (local model)</b> that runs on your company's own servers.</li></ul>" +
    "<p>Please decide as a risk-neutral manager. Assume that your company cares only about its expected total cost over the coming year, and that it is neither more nor less cautious than that.</p>" +
    "<p>All amounts are in US dollars per year. All figures in this survey are hypothetical.</p>",

  news: {
    incident:
      "<p>Please read the following news item.</p><div class='news'><h3>Customer records exposed through an AI vendor</h3>" +
      "<p>Last year, a mid-sized insurance company found that its customers' names, phone numbers, and claim details had been exposed after a security failure at its external AI vendor. The company had to notify thousands of customers and faced an official investigation. Calls to its customer service line stayed far above normal levels for months afterward.</p>" +
      "<p><i>(This news item is fictional and was written for this study.)</i></p></div>",
    control:
      "<p>Please read the following news item.</p><div class='news'><h3>Companies weigh their options for running AI</h3>" +
      "<p>Mid-sized companies are increasingly deciding whether to run AI models in the cloud or on their own servers. Industry analysts describe the choice as a balance between cost, accuracy, and the in-house capacity needed to operate the systems, and note that each company's answer depends on its own circumstances.</p>" +
      "<p><i>(This news item is fictional and was written for this study.)</i></p></div>"
  },

  generalProbability: "Thinking about companies in general, what is the probability that a mid-sized company's personal data will be exposed through an external AI vendor at some point in the next 12 months? Enter a number from 0 to 100 (%).",

  // Scenario design: cases, cells, Latin square
  cases: {
    A: { title: "Sorting customer inquiries", task: "sort incoming customer inquiries into topic categories",
         data: "The inquiries contain customers' names and contact details.",
         B: 80, E: 144, L: 1600, accL: 94, accA: 99, costL: "2.39", costA: "29.52" },
    B: { title: "Extracting fields from HR records", task: "pull key fields out of HR records",
         data: "The records contain employees' personal information.",
         B: 60, E: 108, L: 1200, accL: 99, accA: 100, costL: "33.27", costA: "73.09" },
    C: { title: "Extracting key terms from contracts", task: "extract key terms from contracts",
         data: "The contracts contain the names and contact details of the people and companies involved.",
         B: 100, E: 180, L: 2000, accL: 99, accA: 100, costL: "33.27", costA: "73.09" },
    D: { title: "Triaging insurance claims", task: "sort incoming insurance claims into priority categories",
         data: "The claims contain policyholders' personal and claim information.",
         B: 120, E: 216, L: 2400, accL: 94, accA: 99, costL: "2.39", costA: "29.52" }
  },
  // lam: stated yearly exposure probability (%); perf 1 = accuracy only, 2 = accuracy + cost per correct answer
  cells: [
    { id: "C1", lam: 2, perf: 1 }, { id: "C2", lam: 2, perf: 2 },
    { id: "C3", lam: 6, perf: 1 }, { id: "C4", lam: 6, perf: 2 }
  ],
  latin: { V1: "ABCD", V2: "BCDA", V3: "CDAB", V4: "DABC" },

  q: {
    q1: "In this scenario, what is the yearly chance that personal data is exposed through the cloud vendor?",
    q1opts: [2, 6, 10, 20],
    q2: "Which option would you choose for the coming year?",
    q2opts: ["The local model", "The cloud API"],
    q3: "How much would you be willing to pay per year to eliminate the exposure risk of the cloud API altogether, that is, to be certain that no personal data is exposed through a vendor?",
    q3hint: "Enter an amount in thousands of dollars, between 0 and {smax}. For example, 120 means $120,000 per year.",
    q4: "In your own judgment, what is the chance per year that personal data is exposed through the cloud vendor in this scenario? Enter a number from 0 to 100 (%).",
    q5: "How large is the local model's quality disadvantage compared with the cloud API in this scenario?",
    q5opts: ["1 = Not large at all", "2", "3", "4", "5", "6", "7 = Extremely large"]
  },

  a1: { text: "To show that you are reading carefully, please select \"Somewhat agree\" for this item.",
        options: ["Strongly disagree", "Disagree", "Somewhat disagree", "Neither agree nor disagree", "Somewhat agree", "Agree", "Strongly agree"], correct: 5 },
  a2: { text: "For this question, please select the second option from the left.",
        options: ["Never", "Rarely", "Sometimes", "Often", "Always"], correct: 2 },

  numeracy: [
    { id: "N1", text: "A product costs $200 and is discounted by 25%. What is the new price? (Enter a number.)", correct: 150 },
    { id: "N2", text: "A project has a 20% chance of success. Out of 500 similar projects, about how many would you expect to succeed? (Enter a number.)", correct: 100 },
    { id: "N3", text: "A company's costs rise from $80 to $100. By what percentage have they risen? (Enter a number.)", correct: 25 }
  ],
  experience: [
    { id: "E1", text: "How familiar are you with large language models (LLMs)?", options: ["1 = Not at all familiar", "2", "3", "4", "5 = Extremely familiar"] },
    { id: "E2", text: "How often do you use LLM-based tools at work?", options: ["Never", "Rarely", "Monthly", "Weekly", "Daily"] },
    { id: "E3", text: "Has your organization ever built or run its own AI model on its own servers?", options: ["Yes", "No", "Not sure"] }
  ],
  privacyConcern: {
    id: "PC", text: "How much do you agree with each statement?",
    rows: ["I am concerned about the security of personal data held by outside vendors.",
           "Keeping data inside the company is worth some extra cost.",
           "A data breach at a vendor is a serious business risk.",
           "My organization takes data-handling rules very seriously."],
    cols: ["Strongly disagree", "Disagree", "Somewhat disagree", "Neither agree nor disagree", "Somewhat agree", "Agree", "Strongly agree"]
  },
  risk: { id: "R1", text: "In general, how willing are you to take risks when making business decisions?",
          options: ["0 = Not at all willing", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10 = Very willing"] },
  discretion: { id: "P2", text: "Within your organization's current policy, how much discretion do you (or your team) have in choosing between a local model and a cloud AI service for a use case like those in this survey?",
                options: ["1 = No discretion at all", "2", "3", "4", "5", "6", "7 = Full discretion"] },
  ranking: { id: "P3", text: "Which factors matter most when your organization decides how to source AI for sensitive data? Select your top three and rank them.",
             factors: ["Running cost", "Accuracy and quality of the AI", "Security and privacy policy",
                       "Regulatory and legal compliance", "Dependence on an outside vendor", "In-house expertise needed to operate the system"] },
  industry: [
    { id: "I1", text: "Which of the following best describes your organization's industry?", options: [
      "Semiconductors or electronics hardware", "Software or IT services", "Finance or insurance", "Healthcare or pharmaceuticals",
      "Defense, aerospace, or government", "Manufacturing (other)", "Retail or consumer goods", "Telecommunications or media",
      "Energy or utilities", "Other"] },
    { id: "I2", text: "How valuable are trade secrets and intellectual property (for example, designs, source code, or research data) to your organization's competitive position?",
      options: ["1 = Not at all valuable", "2", "3", "4", "5", "6", "7 = Extremely valuable"] },
    { id: "I3", text: "Does your organization handle classified, export-controlled, or similarly regulated information?", options: ["Yes", "No", "Not sure"] }
  ],
  c1Intro: "Before we finish, please confirm your current main job function and level.",
  demographics: [
    { id: "AGE", text: "What is your age? (optional)", options: ["18 to 24", "25 to 34", "35 to 44", "45 to 54", "55 or older", "Prefer not to say"] },
    { id: "GENDER", text: "What is your gender? (optional)", options: ["Woman", "Man", "Another gender", "Prefer not to say"] },
    { id: "EDU", text: "What is your highest level of education? (optional)", options: ["High school", "Bachelor's degree", "Master's degree", "Doctorate", "Other"] },
    { id: "EXP", text: "How many years of work experience do you have? (optional)", options: ["Less than 3", "3 to 5", "6 to 10", "11 to 20", "More than 20"] }
  ],
  debriefHTML:
    "<h2>Debrief</h2><p>Thank you for taking part. We would like to be open about what this study involved.</p><ul>" +
    "<li>Everything in this survey was fictional: the companies, the figures, the risk team's exposure estimates, and the loss amounts.</li>" +
    "<li>The news item you read, whether it described a data exposure or companies comparing their AI options, was written for this study. Participants were given different news items on purpose. The exposure probabilities shown in the scenarios were the same kind of estimate for everyone.</li>" +
    "<li>The study looks at how professionals weigh risk and performance information when choosing between cloud and local AI. Your answers do not reflect any real decision at your employer, and nothing here is advice on a real purchase.</li></ul>" +
    "<p>If you have any questions, please contact ooklee@hanyang.ac.kr. This study was approved by the Institutional Review Board of Hanyang University (HY-IRB-2026-11-033).</p>"
};
