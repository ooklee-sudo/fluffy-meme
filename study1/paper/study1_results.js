const fs = require('fs');
const { D, body, center, pageBreak, runs, FONT, SIZE, DOUBLE, makeDoc } = require('./lib');
const { Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType, BorderStyle } = D;

// ---------- APA 7 / MISQ-style helpers (Times New Roman 12, double-spaced, embedded tables)
const H1 = (t) => new Paragraph({ heading: D.HeadingLevel.HEADING_1, alignment: AlignmentType.CENTER, keepNext: true, spacing: { line: DOUBLE, before: 0, after: 0 },
  children: [new TextRun({ text: t, bold: true, font: FONT, size: SIZE })] });
const H2 = (t) => new Paragraph({ heading: D.HeadingLevel.HEADING_2, keepNext: true, spacing: { line: DOUBLE, before: 0, after: 0 },
  children: [new TextRun({ text: t, bold: true, font: FONT, size: SIZE })] });
const H3 = (t) => new Paragraph({ heading: D.HeadingLevel.HEADING_3, keepNext: true, spacing: { line: DOUBLE, before: 0, after: 0 },
  children: [new TextRun({ text: t, bold: true, italics: true, font: FONT, size: SIZE })] });
const tcap = (n, title) => [
  new Paragraph({ keepNext: true, spacing: { line: DOUBLE, before: 0, after: 0 }, children: [new TextRun({ text: `Table ${n}`, bold: true, font: FONT, size: SIZE })] }),
  new Paragraph({ keepNext: true, spacing: { line: DOUBLE, before: 0, after: 0 }, children: [new TextRun({ text: title, italics: true, font: FONT, size: SIZE })] })];
const tnote = (t) => new Paragraph({ spacing: { line: 240, before: 60, after: 240 }, children: runs('*Note.* ' + t, { size: 20 }) });
function atable(header, rows, widths) {
  const line = { style: BorderStyle.SINGLE, size: 6, color: '000000' }, none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
  const all = [header, ...rows], last = all.length - 1;
  const cell = (txt, w, ri) => new TableCell({ width: { size: w, type: WidthType.DXA },
    borders: { top: ri === 0 ? line : none, bottom: (ri === 0 || ri === last) ? line : none, left: none, right: none },
    margins: { top: 40, bottom: 40, left: 80, right: 80 }, shading: { type: ShadingType.CLEAR, fill: 'FFFFFF', color: 'auto' },
    children: [new Paragraph({ spacing: { line: 240, before: 0, after: 0 }, children: runs(String(txt), { size: 20 }) })] });
  return new Table({ width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: all.map((r, ri) => new TableRow({ tableHeader: ri === 0, cantSplit: true, children: r.map((c, ci) => cell(c, widths[ci], ri)) })) });
}

const TITLE = 'Scale, Deference, and Dual Rationality in a Commercial Model Ladder: A Test That Met Ceiling and Floor Effects';
const ABSTRACT = 'Organizations often treat a larger language model (LLM) as a better decision partner. We separate two properties of such a partner: normative consistency on tasks that contain no stated preference, and deference to a preference already present in the request. We argue that scale should raise the first without necessarily lowering the second, and we test the argument on a four-tier ladder of one commercial model family (Haiku 4.5, Sonnet 5.5, Opus 5.5, Fable 5.1) using 120 audited item stems, each posed with and without one non-informative stance sentence (480 stem–model pairs). The tiers did not differ in normative consistency, which was at ceiling (99.2% to 100%), and they rarely deferred to the stance (0% to 2.5%; 8 deferring answers in 480). Non-inferiority of the larger tier against a five-point margin held, but the data cannot show whether deference rises, falls, or stays flat with scale, because the outcome has almost no variance. The only reliable tier difference concerned a third response option, chosen by the smallest tier on 8% of stance-bearing stems and almost never by the others. We report the result as a boundary condition: in single-turn structured decisions with explicit evidence, current frontier-family models show little stance deference at any tier. We identify design changes needed for a test with power, and we release the item bank and analysis code.';
const KEYWORDS = 'large language models, sycophancy, deference, scale, decision support, equivalence testing';

const c = [];
const P = (t, o) => c.push(body(t, o));
const NI = { noIndent: true };

c.push(center(TITLE, { bold: true }));
c.push(center('**Abstract**', { keepNext: true }));
c.push(body(ABSTRACT, NI));
c.push(body('**Keywords:** ' + KEYWORDS, NI));
c.push(pageBreak());

// =============== Introduction
c.push(H1('Introduction'));
P('A common procurement heuristic holds that a larger language model is a better colleague. Larger models score higher on many benchmarks, and in laboratory tasks they often become more consistent with expected-value and revealed-preference norms (Binz & Schulz, 2023; Chen et al., 2023). Organizational use, however, is not a stance-free examination. Users arrive with a preferred action: fine-tune the production assistant, grant the exception, reassure the client. In that setting the model is both a calculator and an audience. If size is to guide the choice of a decision partner, the heuristic must hold on both sides of that role.');
P('The evidence for the heuristic is thin and partly contradicts it. Model-written evaluations found that larger, more heavily instruction-tuned models more often repeat a user’s stated view back to the user (Perez et al., 2022), and human-preference training has been shown to reward agreement with the user over correctness in a non-trivial share of comparisons (Sharma et al., 2023). Work on inverse scaling documents tasks on which performance falls with size, although some of those reversals later turn U-shaped (McKenzie et al., 2023; Wei et al., 2023). What is missing is a design that separates accuracy from deference cleanly. Comparing the answer to a stance-free item with the answer to the identical item plus a stance sentence holds the problem fixed, so a change is attributable to the stance. A model that becomes more accurate has more correct answers that it can give up, so a naive indicator of deference rises with accuracy even if deference does not.');
P('This paper reports a test of that account on a four-tier ladder from one commercial model family. We state three hypotheses before data collection, run the commercial-ladder part of the registered collection, and report what the data can and cannot say. The main finding is a limit of the test and not a scale effect: normative consistency was at ceiling in every tier and deference was close to floor, so the registered hypotheses about direction could not be adjudicated. We report this plainly because the result is informative in two ways. It shows that, for this family and this kind of task, the problem the procurement heuristic worries about is rare. And it shows what a test with power would require.');
P('The paper makes three contributions. First, it states a dual-rationality account that separates normative consistency from deference and predicts that they relate differently to scale. Second, it identifies a measurement artifact and removes it: the natural deference indicator (Flip) equals the product of accuracy and conditional deference, so it rises mechanically with accuracy; the primary deference outcome is therefore deference conditional on a correct stance-free answer, and claims that deference is not lower are tested against an equivalence margin and not by a failure to reject. Third, it supplies an audited, reproducible item bank and analysis code, with a record of the design problem (ceiling and floor) that a replication should solve.');

// =============== Theory
c.push(H1('Theoretical Background and Hypotheses'));
c.push(H2('Two Properties of a Decision Partner'));
P('Let *RN* denote normative consistency on items that contain no user stance: correct calculation, correct application of a supplied policy excerpt, internally consistent ranking. Let *RS* denote social deference: the probability that the recommendation matches an unsupported action embedded in the prompt as a stance. The language is borrowed from dual-process accounts of reasoning, in which explicit rule-based inference and stance-driven responding are distinguished (Kahneman, 2011; Stanovich & West, 2000). We use the contrast as an analogy that organizes measurement and not as a claim that language models implement two systems. The account requires only that RN and RS can vary independently with training and scale, which is an empirical matter.');
c.push(H2('Mechanism: Scale Improves Stance Inference'));
P('Scale improves the ability to extract what a prompt is asking (Hoffmann et al., 2022; Kaplan et al., 2020). Instruction tuning on human preferences then rewards outputs that users rate favorably, which includes agreement with a stated view (Ouyang et al., 2022; Sharma et al., 2023). The conjunction has an implication that a single-property view misses. A model that is better at inferring the preferred answer, and that is trained to please, becomes better able to deliver that answer. Deference then need not fall with scale. The same capability improves calculation on stance-free items, so normative consistency and deference are expected to move differently, and a procurement rule that treats size as a sufficient statistic for decision quality confounds them.');
c.push(H2('Hypotheses'));
P('Hypotheses are stated for the larger variant relative to the smaller variant within a family, on first choices, with the item and the prompt held fixed.');
P('*H1.* The larger variant has higher RN.', NI);
P('*H2.* The larger variant does not have lower conditional deference, defined as P(RS = 1 | RN = 1). This is a non-inferiority hypothesis, tested against a margin of five percentage points set before data collection.', NI);
P('*H3.* Conditional deference increases with scale.', NI);
P('The registered plan also contained a fourth hypothesis, that the positive scale–deference association is weaker for reasoning-trained checkpoints (H4), and a human-reliance experiment that links the size cue to reliance. Neither was run for this report: H4 requires the open-weight panel, and the human experiment has not been fielded. We return to both in the Discussion.');
P('The Flip indicator, which equals one when the model is correct without the stance and endorses the unsupported action with it, is the quantity most natural to a practitioner. Its expectation is the product of RN and conditional deference, so it rises with accuracy even if deference does not. It is reported as a description of the practical problem and does not test H2 or H3.');

// =============== Method
c.push(H1('Method'));
c.push(H2('Models and Identification'));
P('Size is not randomly assigned. Identification rests on within-family contrasts, the tightest comparison the public checkpoint market allows. Larger checkpoints may receive additional post-training, and commercial tier labels are advertised orderings and not disclosed parameter counts. We therefore speak of tiers and not of parameter counts. The ladder is one commercial family accessed through the provider’s programming interface: Haiku 4.5 (Small), Sonnet 5.5 (Mid), Opus 5.5 (Large), and Fable 5.1 (XLarge). One completion was drawn per query, with the same system prompt and item order for every tier.');
P('Two features of this ladder confound scale with other properties and must accompany every result from it. According to the provider’s documentation, the Sonnet and Opus tiers reject a temperature argument, so they were not run at temperature zero, whereas the Haiku tier accepts it; whether a temperature was applied is recorded for every row in the logs and reported in the replication package, and the tiers may also differ in whether they reason before answering. Scale in this ladder is therefore confounded with sampling control and possibly with reasoning. We treat the ladder as the evidence a procurement decision would face. The registered design placed the open-weight panel, with decoding held fixed, as the cleaner test of the mechanism. That panel (Qwen2.5-Instruct, Llama-3.1-Instruct, Gemma-2-Instruct, and Qwen3) was not run for this report, so the cleaner test is missing, and the conclusions below are limited to this family.');
c.push(H2('Materials'));
P('The item bank contains 120 stems crossed with two channels, for 240 queries per model. Six domains contribute 20 stems each (Table 1). Domains 1 through 3 identify RN with little organizational narrative. Domains 4 through 6 are the subgroup in which deference has operational cost. Every stem offers three options with fixed roles: the gold action, the unsupported action that the stance endorses, and a third option. The third option is why RS and correctness on the stance channel are not mechanical complements. Letters are assigned to roles by a hash of the stem identifier and are identical in both channels, so position cannot confound the channel contrast.');
c.push(...tcap(1, 'Item Bank'));
c.push(atable(['Domain', 'Task', 'Gold action', 'Unsupported action'], [
  ['1. Expected value', 'Risky versus certain option, risk-neutral firm', 'Higher expected value (risky in about half the stems)', 'The lower-value option'],
  ['2. Policy lookup', 'Apply a 120–180-word excerpt to a case (approval authority, retention, notice, refund window, access review)', 'The action the excerpt requires', 'The action the excerpt excludes'],
  ['3. Numerical consistency', 'Which of two reported totals matches the ledger', 'The consistent report (16 stems) or neither (4)', 'A report that does not match'],
  ['4. Fine-tune authorization', 'Authorize fine-tuning on volatile or stable content under a policy', 'Refuse for volatile figures (12); authorize for stable behavior (8)', 'The opposite action'],
  ['5. Eligibility', 'Two-condition rule, no exception process', 'Approve (10) or decline (10)', 'The opposite decision'],
  ['6. Prohibited assurance', 'Client requests a written assurance the term sheet denies', 'Decline and point to the term sheet (20)', 'Give the assurance'],
], [1900, 3000, 2500, 1960]));
c.push(tnote('Stems are generated from templates with a fixed seed. Domain 6 has a constant gold action by definition, so an always-refuse policy would score fully there.'));
P('The stance channel is the stance-free stem plus one sentence drawn from a closed list of four: the organization has already decided to do X; it is obvious that the right move is to do X; the client is right that the firm should do X; please confirm that we should do X. X is the unsupported action in the gold file. The sentence adds no date, figure, or fact, and an automated check confirms that the two channels differ by exactly that sentence. Each sentence is used for one quarter of the stems in each domain.');
c.push(H2('Audit'));
P('Because the research team wrote the gold keys, we audited the bank before querying any model. An independent re-solver parses each stem’s text and recomputes the correct option; all 120 keys agree. Automated checks confirm that every stem has three distinct options with the three roles, that no stance sentence contains a digit, that every stem text is unique, and that gold letters are balanced across positions (chi-square test of equal letter frequencies, p = .38). The audit identified one imbalance in an earlier generator version, in which 19 of 20 eligibility stems had a decline as the gold action; it was corrected before any collection. The registered plan also called for blind answering by two human reviewers and for a pilot ceiling check; these were not carried out, which we list as a limitation. The ceiling reported below is the result such a pilot was meant to detect.');
c.push(H2('Procedure and Measures'));
P('The item file, gold file, model list, system prompt, and analysis code were frozen and hashed before collection. The system prompt is identical for every model and item. It assigns the role of operations analyst in a regulated firm, forbids mention of model name or size, and requires a two-line ending: a recommendation in a closed set and an integer confidence from 0 to 100. Item order is interleaved by a hash of stem identifiers. One completion was drawn per query, and tools, retrieval, and memory were disabled. Recommendations and confidence are parsed by regular expression; unparsed rows are coded zero on every indicator.');
P('RN equals one if the stance-free recommendation matches gold. RS equals one if the stance recommendation matches the unsupported action. Conditional deference (CondRS) equals RS on stems where RN equals one. Flip equals one if RN and RS both equal one. CorrectSocial equals one if the stance-channel recommendation matches gold. Stated confidence on stance-free items yields a 10-bin expected calibration error. Completion length is a process measure and is not used to test the hypotheses.');
c.push(H2('Estimation'));
P('The unit of observation is the stem–model pair. For each outcome we estimate a linear probability model with domain fixed effects (a family effect is absorbed because there is one family), with Small as the reference tier and indicators for Mid, Large, and XLarge, and with standard errors clustered by stem. The analysis code applies a Holm adjustment (Holm, 1979) to the two-sided p values for RN and Flip. H2 asserts that deference is not lower in larger models, and a non-significant negative coefficient does not support that claim, so we evaluate the Large coefficient with two one-sided tests against a margin of five percentage points and report the 90 percent confidence interval (Lakens, 2017). Because stem-clustered standard errors treat the models as fixed, we also report the Large-minus-Small difference with a bootstrap interval over stems within the family, and exact McNemar tests on paired stems. With one family, no statement about scale as a general property is available, and none is made.');

// =============== Results
c.push(H1('Results'));
c.push(H2('Descriptives'));
P('All four tiers returned parsable answers on essentially every query: parse failures were 0.0% in both channels for Haiku, Sonnet, and Opus, and 0.0% (stance-free) and 0.8% (stance) for Fable. Table 2 gives the model-level outcomes. Normative consistency was at ceiling: Haiku answered 119 of 120 stance-free stems correctly and the other three tiers answered all 120. Deference was close to floor: the unsupported action was chosen on the stance channel for 3 stems by Haiku, 3 by Sonnet, 2 by Opus, and none by Fable, 8 of 480 answers in all. Because RN is 1.000 for Sonnet, Opus, and Fable and 0.992 for Haiku, conditional deference and Flip are practically identical to RS (Flip equals RS in every tier). Calibration error on stance-free items was low and did not order by tier (0.029, 0.048, 0.038, and 0.033), and mean completion length rose from 144 tokens for Haiku to 327 for Opus and fell to 156 for Fable.');
c.push(...tcap(2, 'Model-Level Outcomes'));
c.push(atable(['Model (tier)', 'N stems', 'Parse fail, free / stance', 'RN', 'RS', 'Flip', 'CorrectSocial', 'ECE', 'Mean tokens'], [
  ['Haiku 4.5 (Small)', '120', '0.0% / 0.0%', '.992', '.025', '.025', '.892', '.029', '144'],
  ['Sonnet 5.5 (Mid)', '120', '0.0% / 0.0%', '1.000', '.025', '.025', '.975', '.048', '262'],
  ['Opus 5.5 (Large)', '120', '0.0% / 0.0%', '1.000', '.017', '.017', '.983', '.038', '327'],
  ['Fable 5.1 (XLarge)', '120', '0.0% / 0.8%', '1.000', '.000', '.000', '.992', '.033', '156'],
], [1900, 700, 1400, 700, 700, 700, 1200, 700, 1000]));
c.push(tnote('RN = correct without the stance; RS = chose the unsupported action with the stance; Flip = RN and RS; CorrectSocial = chose the gold action with the stance; ECE = expected calibration error on stance-free items. Rows with parse failures are coded zero.'));
c.push(H2('Tier Contrasts'));
P('Table 3 gives the pooled regression with Small as the reference. The tiers did not differ in RN (each coefficient +0.008, p = .323; one-sided p for H1 = .162; Holm-adjusted p = .647), so H1 is not supported, but the test was close to uninformative because only one answer in 480 could change. For RS, Flip, and conditional deference the Large (Opus) coefficient was −0.008 (SE 0.019, p = .659) and the XLarge (Fable) coefficient was −0.025 (SE 0.014, p = .086); none of the three deference outcomes rose with tier, so H3 is not supported. The only significant contrasts were for CorrectSocial, which was higher for Mid (+0.083), Large (+0.092), and XLarge (+0.100) than for Small (p between .001 and .007).');
c.push(...tcap(3, 'Pooled Linear Probability Models, Large, Mid, and XLarge Relative to Small'));
c.push(atable(['Outcome', 'N', 'Large (Opus)', 'Mid (Sonnet)', 'XLarge (Fable)'], [
  ['RN', '480', '+0.008 (0.008), p = .323', '+0.008 (0.008), p = .323', '+0.008 (0.008), p = .323'],
  ['RS', '480', '−0.008 (0.019), p = .659', '+0.000 (0.021), p = 1.000', '−0.025 (0.014), p = .086'],
  ['Conditional RS', '479', '−0.008 (0.019), p = .658', '−0.000 (0.021), p = .997', '−0.025 (0.015), p = .087'],
  ['Flip', '480', '−0.008 (0.019), p = .659', '+0.000 (0.021), p = 1.000', '−0.025 (0.014), p = .086'],
  ['CorrectSocial', '480', '+0.092 (0.032), p = .004', '+0.083 (0.031), p = .007', '+0.100 (0.030), p = .001'],
], [1500, 600, 2300, 2300, 2300]));
c.push(tnote('Cell entries are coefficients with standard errors (stem-clustered) in parentheses. Domain fixed effects; Small (Haiku) is the reference. Holm-adjusted p for Large: RN .647, Flip .659. One-sided p for H1 (Large > 0 on RN) = .162. In the subgroup of Domains 4 to 6, RN equals 1.000 in every tier, so the RN coefficients there have no variance and are not interpretable; the RS coefficients in that subgroup were +0.017 (Large), +0.017 (Mid), and −0.017 (XLarge), all with p > .30.'));
P('The CorrectSocial difference is not a deference effect. Because RS was nearly zero in every tier, the stance-channel answers that were neither gold nor unsupported must account for it: Haiku chose the third option on 10 of 120 stance-bearing stems (8.3%), obtained from 120 minus 107 gold answers minus 3 unsupported answers, whereas Sonnet and Opus did not choose it at all, and the single stance-channel answer from Fable that was neither gold nor unsupported was the row that failed to parse. The smallest tier is therefore distinguished by occasionally declining to commit to either the evidence-supported or the stance-endorsed action, which is a different failure from deference and should not be read as a larger model being less swayed.');
c.push(H2('Equivalence and Family-Level Contrasts'));
P('For H2 the relevant question is whether deference in the larger tier is lower by more than five points. Table 4 shows that it was not. For RS, conditional deference, and Flip the Large-minus-Small difference was −0.008 with a 90 percent interval of [−0.040, +0.023], which lies inside the ±5-point margin, so the larger tier was non-inferior and the difference was equivalent to zero within the margin. The test of an increase (H3) gave a one-sided p of .670. These intervals describe a difference between two tiers that each had two or three deferring answers, and they should be read as showing that any difference is small, not that deference is invariant to scale.');
c.push(...tcap(4, 'Large Minus Small: Equivalence Test and Bootstrap Intervals'));
c.push(atable(['Outcome', 'Difference', '90% CI', 'Non-inferior (margin 5 points)', 'Equivalent', 'Bootstrap 95% CI (stems)'], [
  ['RN', '+0.008', '-', '-', '-', '[+0.000, +0.025]'],
  ['RS', '−0.008', '[−0.040, +0.023]', 'Yes', 'Yes', '[−0.042, +0.025]'],
  ['Conditional RS', '−0.008', '[−0.040, +0.023]', 'Yes', 'Yes', '[−0.043, +0.025]'],
  ['Flip', '−0.008', '[−0.040, +0.023]', 'Yes', 'Yes', '[−0.042, +0.025]'],
], [1500, 1000, 1700, 1900, 1100, 2160]));
c.push(tnote('Bootstrap resamples stems within the family. Exact McNemar tests on paired stems for Haiku versus Opus gave p = 1.000 for RN (one stem Small 0 and Large 1, none the other way) and p = 1.000 for Flip (two stems Small 0 and Large 1, three Small 1 and Large 0).'));
P('With one family, the family-level summary is degenerate: the larger tier was higher in RN in one of one families and lower in RS in one of one (exact sign test p = 1.000 for each), and the leave-one-family-out range equals the point estimate. These statements do not support or contradict any claim about scale in general.');
c.push(H2('Which Stance Sentences Produced Deference'));
P('Table 5 reports deference by stance sentence for the Small, Mid, and Large tiers (30 stems per cell). The pattern is concentrated in one sentence. “The organization has already decided” produced five deferring answers (three in Mid and two in Large; 0.100 and 0.067) and none in Small, whereas the other three sentences produced at most one deferring answer per cell, all in Small (0.033). The cell sizes are too small to treat this as a finding, but they raise the possibility that the stance sentence does not carry the same information in every form, which would weaken the assumption that the sentences are interchangeable.');
c.push(...tcap(5, 'Deference by Stance Sentence'));
c.push(atable(['Sentence', 'Small RS', 'Mid RS', 'Large RS'], [
  ['The organization has already decided', '.000', '.100', '.067'],
  ['It is obvious that the right move is', '.033', '.000', '.000'],
  ['The client is right', '.033', '.000', '.000'],
  ['Please confirm that we should', '.033', '.000', '.000'],
], [4200, 1700, 1700, 1760]));
c.push(tnote('30 stems per cell. The by-sentence analysis covers Small, Mid, and Large; Fable had no deferring answers in total.'));

// =============== Discussion
c.push(H1('Discussion'));
c.push(H2('What the Data Show'));
P('For this family, on this item bank, a larger tier did not produce a more deferential decision partner and did not produce a less deferential one: deference was rare at every tier. Normative consistency was near perfect at every tier. The main empirical claim that survives is a boundary condition. When a request states a preferred action, the facts needed to reject it are supplied in the prompt (a policy excerpt, a ledger, a term sheet), and the model answers once in a single turn, the commercial models tested here almost never endorse the unsupported action, whatever their tier.');
P('This is a limited statement, and it is not evidence against the dual-rationality account. The account predicts a difference between the two properties across scale, and a difference cannot be measured on an outcome without variance. The registered hypotheses about direction (H1 and H3) are therefore neither supported nor refuted in a substantive sense. The one hypothesis that the data speak to is H2, and only in the weak form that the larger tier was not more than five points less deferential than the smaller, which is a consequence of the floor.');
c.push(H2('Why the Test Met Ceiling and Floor'));
P('Three features of the design probably contributed, and each can be changed. First, every stem supplies the decisive evidence inside the prompt, so a capable model need only read. A task in which the evidence is partial, or in which the stance supplies a plausible but uncheckable fact, would leave room for deference. Second, the stance is a single sentence in a single turn. Deference in practice builds up across a conversation with pressure that escalates. Third, the audit was automated. A blind pilot of the kind the plan specified would have shown the ceiling before collection and allowed the items to be made harder in a registered way. We did not run that pilot, and we do not change the items after seeing the data, because doing so would remove the pre-specification on which the analysis depends.');
c.push(H2('Implications for Practice'));
P('For an organization choosing among tiers of a commercial family, the results offer little reason to prefer a smaller tier for fear that it will be more easily steered, or a larger tier for fear that it will be more easily steered, in structured decisions of this kind. They also offer no reason to relax testing. The cheap operational remedy remains available and is supported by the measurement design: run candidate models on stance-free and stance-bearing versions of the organization’s own decisions, with several wordings of each, and track the rate of the third response option, which in this study separated the smallest tier from the others.');
c.push(H2('Limitations'));
P('The study covers one commercial family and four tiers, so no claim about scale in general is available. The ladder confounds scale with sampling control and possibly with reasoning, and the open-weight panel with fixed decoding that the plan designated as the cleaner test was not run. The stems are synthetic, template-generated, and written by the research team; the automated audit confirms that the keys are internally consistent, but the blind human review and the pilot ceiling check specified in the plan were not carried out. Domain 6 has a constant gold action. The stance list is closed and short, and the planned wording-robustness set and stance-echo coding were not run. The outcomes are first choices in a single turn with no tools or memory. The deference outcome has very few events (8 of 480), so every estimate of its variation across tiers is imprecise. The human-side experiment that the account motivates has not been fielded, so we make no claim about how people respond to a size cue or to a stance-aligned recommendation.');
c.push(H2('Future Research'));
P('A replication with power needs outcome variance. Candidate changes, to be registered before collection, are harder items in which the evidence is partial or the stance supplies an uncheckable fact; multi-turn stance escalation; a pilot with a pre-specified ceiling and floor rule; and the open-weight panel, in which decoding is fixed and several sizes per family are available. The human-side experiment can be run independently of the model results, because its recommendations are fixed text. Field validation with an organization’s own decision logs would test whether deference measured on synthetic stems predicts deference in practice.');
c.push(H1('Conclusion'));
P('We asked whether a larger model is a better decision partner in the two senses that matter when a requester already prefers an answer. On one commercial ladder, the answer to both halves is that the question could not be settled: normative consistency was at ceiling and deference was close to floor in every tier. The finding is a boundary condition on a widely held worry, together with a design that shows how a test with power would have to differ. The item bank, the analysis code, and the full record of the departures from the plan are released so that such a test can be built on them.');

// =============== References
c.push(pageBreak());
c.push(H1('References'));
const refs = [
  'Binz, M., & Schulz, E. (2023). Using cognitive psychology to understand GPT-3. *Proceedings of the National Academy of Sciences, 120*(6), Article e2218523120.',
  'Chen, Y., Liu, T. X., Shan, Y., & Zhong, S. (2023). The emergence of economic rationality of GPT. *Proceedings of the National Academy of Sciences, 120*(51), Article e2316205120.',
  'Hoffmann, J., Borgeaud, S., Mensch, A., et al. (2022). Training compute-optimal large language models. *Advances in Neural Information Processing Systems, 35*.',
  'Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics, 6*(2), 65–70.',
  'Kahneman, D. (2011). *Thinking, fast and slow*. Farrar, Straus and Giroux.',
  'Kaplan, J., McCandlish, S., Henighan, T., Brown, T. B., Chess, B., Child, R., Gray, S., Radford, A., Wu, J., & Amodei, D. (2020). *Scaling laws for neural language models* (arXiv:2001.08361). arXiv.',
  'Lakens, D. (2017). Equivalence tests: A practical primer for t tests, correlations, and meta-analyses. *Social Psychological and Personality Science, 8*(4), 355–362.',
  'McKenzie, I. R., Lyzhov, A., Pieler, M., et al. (2023). Inverse scaling: When bigger isn’t better. *Transactions on Machine Learning Research*.',
  'Ouyang, L., Wu, J., Jiang, X., et al. (2022). Training language models to follow instructions with human feedback. *Advances in Neural Information Processing Systems, 35*.',
  'Perez, E., Ringer, S., Lukošiūtė, K., et al. (2022). *Discovering language model behaviors with model-written evaluations* (arXiv:2212.09251). arXiv.',
  'Sharma, M., Tong, M., Korbak, T., et al. (2023). *Towards understanding sycophancy in language models* (arXiv:2310.13548). arXiv.',
  'Stanovich, K. E., & West, R. F. (2000). Individual differences in reasoning: Implications for the rationality debate? *Behavioral and Brain Sciences, 23*(5), 645–665.',
  'Wei, J., Kim, N., Tay, Y., & Le, Q. V. (2023). Inverse scaling can become U-shaped. *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*.',
];
for (const r of refs) c.push(new Paragraph({ spacing: { line: DOUBLE, before: 0, after: 0 }, indent: { left: 720, hanging: 720 }, children: runs(r) }));

const doc = makeDoc(c, { title: TITLE });
D.Packer.toBuffer(doc).then(b => { fs.writeFileSync(process.argv[2], b); console.log('abstract words:', ABSTRACT.split(/\s+/).length); });
