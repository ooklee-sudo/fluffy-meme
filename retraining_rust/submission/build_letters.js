// Builds Title_page.docx and Cover_letter.docx (A4, Times New Roman 12).
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle } = require("docx");
const FONT = "Times New Roman";
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: 24, ...o });
const para = (children, o = {}) => new Paragraph({ children: Array.isArray(children) ? children : [run(children)], spacing: { after: 160, line: 276 }, ...o });
const heading = (t) => new Paragraph({ children: [run(t, { bold: true })], spacing: { before: 280, after: 120 }, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "999999", space: 2 } }, keepNext: true });
const ph = (t) => run(t, { highlight: "yellow" });   // placeholder to be completed by the authors
const TITLE = "Does Release Timing in the LLM Software Ecosystem Respond to Accumulating Degradation? An Empirical Study of Open-Source Repositories and Public Chat Logs";
const ABSTRACT = fs.readFileSync("manuscript_blind.md", "utf8").split("## Abstract")[1].split("**Keywords:**")[0].trim()
  .replace(/\$-/g, "−").replace(/\$/g, "").replace(/\*/g, "");
const KEYWORDS = "software maintenance, large language models, concept drift, release engineering, mining software repositories, negative results";
const doc = (children) => new Document({ styles: { default: { document: { run: { font: FONT, size: 24 } } } },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children }] });

// ---------------- Title page ----------------
const title = [
  new Paragraph({ children: [run("Title page", { italics: true, color: "666666" })], spacing: { after: 240 } }),
  new Paragraph({ children: [run(TITLE, { bold: true, size: 32 })], alignment: AlignmentType.CENTER, spacing: { after: 360, line: 300 } }),
  heading("Authors and affiliations"),
  para([run("1. "), ph("[First author name]"), run(", "), ph("[Department, Institution, City, Country]"), run(", ORCID: "), ph("[0000-0000-0000-0000]")]),
  para([run("2. "), ph("[Second author name, if any]"), run(", "), ph("[Department, Institution, City, Country]"), run(", ORCID: "), ph("[ORCID]")]),
  heading("Corresponding author"),
  para([ph("[Name]"), run(", "), ph("[e-mail address]"), run(", "), ph("[postal address / telephone]")]),
  heading("Abstract"),
  para(ABSTRACT, { alignment: AlignmentType.JUSTIFIED }),
  para([run("Keywords: ", { bold: true }), run(KEYWORDS)]),
  heading("Manuscript details"),
  para("Article type: Original research. Word count: about 5,000 words in the main text (excluding abstract, tables and references); abstract 245 words. The manuscript file is anonymized for review and does not contain author information."),
  heading("Declarations"),
  para([run("Funding. ", { bold: true }), ph("[State the funding sources, or: “The authors received no specific funding for this work.”]")]),
  para([run("Competing interests. ", { bold: true }), ph("[State any competing interests, or: “The authors have no competing interests to declare that are relevant to the content of this article.”]")]),
  para([run("Ethics approval and data protection. ", { bold: true }), run("The study uses public repository metadata and the public WildChat corpus, which is distributed with hashed identifiers. We store only aggregate counts and binary features and neither store nor publish conversation text. "), ph("[Confirm with the institutional review board whether a formal review or an exemption statement is required.]")]),
  para([run("Data availability. ", { bold: true }), run("The replication package (collection, measurement and analysis scripts; weekly aggregates; simulation code; labeling codebook and labels, without conversation text) is available at https://github.com/ooklee-sudo/fluffy-meme, directory retraining_rust. "), ph("[Before submission, deposit a release in a permanent archive such as Zenodo and cite its DOI here. For double-anonymous review, provide an anonymized link in the manuscript instead.]"), run(" Raw GitHub data can be re-collected with the supplied scripts, and WildChat-1M is available from its publisher.")]),
  para([run("Author contributions. ", { bold: true }), ph("[Describe each author’s contribution, for example conceptualization, data collection, analysis, labeling and writing.]")]),
  para([run("Use of AI tools. ", { bold: true }), run("An AI assistant (Claude, Anthropic) was used to write and run analysis code, to draft and edit the manuscript text, and as an annotator in the validation of the correction detector (Section 4.4 of the manuscript). Its labels were compared with those of a human author, and the differences are reported in Section 5.4. The authors reviewed the outputs and take responsibility for the content. "), ph("[Check the journal’s current policy on disclosing AI use and adapt this statement accordingly.]")]),
  para([run("Acknowledgments. ", { bold: true }), ph("[Optional.]")]),
];
// ---------------- Cover letter ----------------
const L = (t, o = {}) => para(t, { alignment: AlignmentType.JUSTIFIED, ...o });
const cover = [
  para([ph("[Author name]")], { spacing: { after: 0 } }), para([ph("[Department, Institution]")], { spacing: { after: 0 } }), para([ph("[Address]")], { spacing: { after: 0 } }), para([ph("[e-mail]")], { spacing: { after: 240 } }),
  para("October 12, 2026", { spacing: { after: 240 } }),
  para("The Editors", { spacing: { after: 0 } }), para("Empirical Software Engineering", { spacing: { after: 240 } }),
  para([run("Re: Submission of an original research article", { bold: true })]),
  para("Dear Editors,"),
  L("We are pleased to submit our manuscript, “" + TITLE + ",” for consideration as an original research article in Empirical Software Engineering."),
  L("Software built around large language models is widely said to age: the model is frozen at a training cutoff, the world moves on, and practitioners are told to refresh such systems on a schedule. We ask a simple empirical question about that belief. If degradation accumulates and maintainers respond to it, what should the public record show, and do we see it? We state a small replacement model, derive three testable implications (errors rise with the time since the last refresh, the chance of a refresh rises with the same elapsed time, and measured drift predicts worse outcomes), and test them using the weekly issue and release histories of 19 widely used open-source repositories (4,071 repository-weeks; 1,521 releases) and 478,498 English conversations from the public WildChat corpus."),
  L("None of the three implications is supported. Once total issue volume is controlled, bug reports do not rise with the age of a release (pooled slope −0.0005 per week; 95% CI −0.010 to 0.009), the probability of a release does not rise with age, and a measure of prompt drift does not predict user corrections after repeated automated templates are removed. We report these as negative results, and we are careful about what they can and cannot show. The repositories are software and tooling and not model-retraining pipelines, and our pattern-based detector of user corrections captures only a small share of them."),
  L("We believe the paper will interest readers of Empirical Software Engineering for three reasons. First, it reports a fully specified negative result, with eligibility rules fixed before data collection, a complete account of how repositories were selected and excluded, random-effects pooling, robustness checks, and an explicit analysis of what effect sizes the design could detect. Second, it documents a measurement problem that others working with public chat logs are likely to meet: a drift measure that appeared to predict user corrections (p = 0.009) did so only because a single automated prompt template had come to dominate the data. Third, it validates the outcome measure openly. A human author and an AI annotator labeled the same sample of user turns and agreed only moderately (kappa = 0.34), which shows that “user correction” is not a self-evident construct. We release the full replication package, including collection and analysis code, weekly aggregates, and the labeling codebook."),
  L("We confirm that the manuscript is original, has not been published, and is not under consideration for publication elsewhere. ", { spacing: { after: 0 } }),
  para([ph("[Confirm before sending: that all authors have approved the submission, and that there are no competing interests.]")]),
  L("The study uses only public data. An AI assistant was used for coding, drafting, and as an annotator in the validation step, as disclosed in the manuscript and on the title page. The authors reviewed all outputs and take full responsibility for the content."),
  para([run("Suggested reviewers (optional): ", { bold: true }), ph("[Names, affiliations, e-mail addresses]")]),
  para([run("Reviewers to exclude (optional): ", { bold: true }), ph("[Names, if any]")]),
  L("Thank you for considering our work. We look forward to your response."),
  para("Sincerely,", { spacing: { after: 360 } }),
  para([ph("[Author name(s)]")], { spacing: { after: 0 } }), para([ph("[Affiliation]")]),
];
Promise.all([Packer.toBuffer(doc(title)), Packer.toBuffer(doc(cover))]).then(([a, b]) => {
  fs.writeFileSync("Title_page.docx", a); fs.writeFileSync("Cover_letter.docx", b); console.log("written");
});
