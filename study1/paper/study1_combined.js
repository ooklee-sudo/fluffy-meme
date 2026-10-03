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

const TITLE = 'Do Larger Language Models Defer Less to a Stated Stance? A Registered Ladder Test Across Fourteen Models';
const ABSTRACT = 'Organizations often treat a larger language model (LLM) as a better decision partner. We separate two properties of such a partner: normative consistency on items with no stated preference, and deference to a preference already present in the request. We argued that scale should raise the first without lowering the second. We tested this in two registered studies with 120 audited item stems, each posed with and without one stance sentence. Study 1, a four-tier commercial ladder on easy items, met a ceiling on consistency and a floor on deference and could not test the hypotheses. Study 1b used harder items, stance sentences that assert unverifiable support, an open-weight panel of four families and ten models, and the commercial ladder again, after a pre-registered pilot gate. In the open-weight sample, larger tiers were more consistent (+27 percentage points) and less deferential (−29 points on the stance-endorsed answer; −24 points conditional on a correct stance-free answer). Deference fell with tier in all five families (exact sign test p = .062, the smallest value five families allow), but it stayed high in absolute terms: the largest open models still followed the stance on 15% to 53% of items. Gemma-3 was an exception, with consistency rising and deference flat. The registered prediction that scale does not lower deference is therefore not supported. We report the cross-family spread, the measurement design, and the limits of tier comparisons.';
const KEYWORDS = 'large language models, sycophancy, deference, scale, decision support, registered report';

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
P('The evidence for the heuristic is thin and partly contradicts it. Model-written evaluations found that larger, more heavily instruction-tuned models more often repeat a user’s stated view back to the user (Perez et al., 2022), and human-preference training has been shown to reward agreement with the user over correctness in a non-trivial share of comparisons (Sharma et al., 2023). Work on inverse scaling documents tasks on which performance falls with size, although some of those reversals later turn U-shaped (McKenzie et al., 2023; Wei et al., 2023). What is missing is a design that separates accuracy from deference cleanly and tests the relation with scale inside model families. Comparing the answer to a stance-free item with the answer to the identical item plus a stance sentence holds the problem fixed, so a change is attributable to the stance. A model that becomes more accurate has more correct answers that it can give up, so a naive indicator of deference rises with accuracy even if deference does not.');
P('This paper reports two registered studies of that question. We stated a dual-rationality account before collection: normative consistency and deference are distinct properties, scale should raise the first, and scale need not lower the second because larger models are better at inferring what a requester wants. The first study, a commercial model ladder on easy items, could not test the account because it met a ceiling and a floor. The second used harder items, a stance that asserts support, an open-weight panel, and a pilot gate registered before collection. The result of the second study contradicts the account’s sign prediction: larger tiers were less deferential, in every family. We report this directly, together with a feature that the sign prediction missed, namely that deference remains common in the largest models, and that it differs more across families than across sizes within a family.');
P('The paper makes three contributions. First, it supplies a measurement design that avoids a mechanical artifact: the indicator for deference that requires the model to be correct without the stance (Flip) rises with accuracy by construction, so the primary deference outcome is deference conditional on a correct stance-free answer, and claims that deference is not lower are tested against an equivalence margin and not by a failure to reject. Second, it reports a sequence in which the first test failed for reasons of design and was repaired under a pre-specified gate, so that the repair does not use the results of the hypothesis tests. Third, it reports the substantive finding and its limits: a consistent direction across five families that five families cannot establish as a general law, and a cross-family spread that is as large as the size effect.');

// =============== Theory
c.push(H1('Theoretical Background and Hypotheses'));
c.push(H2('Two Properties of a Decision Partner'));
P('Let *RN* denote normative consistency on items that contain no user stance: correct calculation, correct application of a supplied policy excerpt, internally consistent ranking. Let *RS* denote social deference: the probability that the recommendation matches an unsupported action embedded in the prompt as a stance. The language is borrowed from dual-process accounts of reasoning, in which explicit rule-based inference and stance-driven responding are distinguished (Kahneman, 2011; Stanovich & West, 2000). We use the contrast as an analogy that organizes measurement and not as a claim that language models implement two systems. The account requires only that RN and RS can vary independently with training and scale, which is an empirical matter.');
c.push(H2('Mechanism and Prediction'));
P('Scale improves the ability to extract what a prompt is asking (Hoffmann et al., 2022; Kaplan et al., 2020). Instruction tuning on human preferences then rewards outputs that users rate favorably, which includes agreement with a stated view (Ouyang et al., 2022; Sharma et al., 2023). A model that is better at inferring the preferred answer, and that is trained to please, becomes better able to deliver that answer. Deference then need not fall with scale. The same capability improves calculation on stance-free items, so normative consistency and deference are expected to move differently, and a procurement rule that treats size as a sufficient statistic for decision quality confounds them. We recognized at the time that the opposite is also plausible: post-training that targets sycophancy, and the greater ability of larger models to hold a position, could lower deference. The registered hypotheses took the first position.');
c.push(H2('Hypotheses'));
P('Hypotheses are stated for the larger variant relative to the smaller variant within a family, on first choices, with the item and the prompt held fixed.');
P('*H1.* The larger variant has higher RN.', NI);
P('*H2.* The larger variant does not have lower conditional deference, defined as P(RS = 1 | RN = 1). This is a non-inferiority hypothesis, tested against a margin of five percentage points set before data collection.', NI);
P('*H3.* Conditional deference increases with scale.', NI);
P('The registered plan also contained a hypothesis about reasoning-trained checkpoints and a human-reliance experiment. Neither was run here: reasoning-first families were left out of the open-weight panel so that reasoning would not be confounded with size, and the experiment has not been fielded. The Flip indicator, which equals one when the model is correct without the stance and endorses the unsupported action with it, is the quantity most natural to a practitioner. Its expectation is the product of RN and conditional deference, so it rises with accuracy even if deference does not. It is reported as a description of the practical problem and does not test H2 or H3.');

// =============== Method
c.push(H1('Method'));
c.push(H2('Design Overview'));
P('Study 1 (collected first) used an easy item bank and the commercial ladder. Its result, a ceiling on RN and a floor on RS, is reported in full. Study 1b followed under a registered plan written before any model saw its items: a harder item bank, stance sentences that assert support, an open-weight panel, the commercial ladder again, and a pilot gate that had to pass before the bank was frozen. The study 1b plan, the generator, the audit, and the frozen files are in the replication package; the plan records one pilot attempt, which passed without any change to the items.');
c.push(H2('Item Banks'));
P('Each bank has 120 stems, 20 in each of six domains, crossed with two channels, for 240 queries per model. Every stem offers three options with fixed roles: the gold action, the unsupported action that the stance endorses, and a third option. The third option is why RS and correctness on the stance channel are not mechanical complements. Letters are assigned to roles by a hash of the stem identifier and are identical in both channels. The stance channel is the stance-free stem plus one sentence. In Study 1 the sentences state a preference (for example, that the organization has already decided on the action). In Study 1b they assert unverifiable support for the action: that a colleague has reviewed it, that the requester has long experience with such cases, that a lawyer has confirmed it, or that it has precedent. No sentence contains a figure or a date. Each sentence is used for one quarter of the stems in each domain.');
c.push(...tcap(1, 'Domains of the Two Item Banks'));
c.push(atable(['Domain', 'Study 1 bank (easy)', 'Study 1b bank (hard)'], [
  ['1', 'Risky versus certain option; higher expected value', 'Two-stage gamble with a launch cost; options differ by 4 to 12 percent'],
  ['2', 'Apply a 120–180-word policy excerpt to a case', 'Rule with an exception and a cap on the exception; three conditions needed'],
  ['3', 'Which of two reported totals matches a three-line ledger', 'Ledger with five charges, a credit, and a tax; reports differ by the two natural errors'],
  ['4', 'Authorize fine-tuning on volatile or stable content', 'Under-determined case: in half of the stems the decisive fact is missing and the gold action is to ask for it'],
  ['5', 'Two-condition eligibility rule', 'Two versions of a rule with an effective date; the case date decides which applies'],
  ['6', 'Decline a prohibited written assurance', 'Unit conversion and ratios (weeks and days, minutes and hours, percent of budget, years and months)'],
], [900, 3800, 4660]));
c.push(tnote('Both banks are generated from templates with fixed seeds and hashed before collection.'));
c.push(H2('Audit and Pilot Gate'));
P('Because the research team wrote the gold keys, each bank was audited before collection. For both banks, an independent re-solver that parses the stem text and not the generator parameters agrees with the key on all 120 stems, every stem has three distinct options with the three roles, every stem text is unique, gold letters are balanced across positions, and the two channels differ by exactly one sentence. The registered blind review of the keys by two people who had not seen the generator was not carried out, which we list as a limitation. For Study 1b, a pilot used 48 stems from a different seed on four models (Claude Haiku, Qwen2.5-7B, Llama-3.1-8B, Llama-3.1-70B). The pre-registered gate required mean RN between .35 and .90, at least four of six domains between .15 and .95, and at least one model with conditional deference of at least .05. The gate passed (mean RN .760, six of six domains inside the band, conditional deference between .042 and .458), no parameter was changed, and the pilot completions are not used in any hypothesis test.');
c.push(H2('Models'));
P('Size is not randomly assigned. Identification rests on within-family contrasts, the tightest comparison the public checkpoint market allows. Larger checkpoints may receive additional post-training, tiers within a commercial family are advertised orderings and not disclosed parameter counts, and families are of different generations. We therefore speak of tiers. Study 1b has four open-weight families served through a hosted aggregator and one commercial family (Table 2). Reasoning-first open families were not included. The aggregator chooses the serving hardware and quantization, which we did not control. The runner omits the temperature argument for the Sonnet, Opus, and Fable tiers, which the provider’s documentation lists as rejecting it; every other model was called at temperature zero when the endpoint accepted it. One completion was drawn per query, with a limit of 512 new tokens, tools and memory disabled, and the same system prompt and hash-interleaved order for every model.');
c.push(...tcap(2, 'Model Grid for Study 1b'));
c.push(atable(['Family', 'Small', 'Mid', 'Large', 'XLarge', 'Access'], [
  ['Qwen2.5-Instruct', '7B', '-', '72B', '-', 'Hosted aggregator'],
  ['Llama-3.1-Instruct', '8B', '-', '70B', '-', 'Hosted aggregator'],
  ['Gemma-3-it', '4B', '12B', '27B', '-', 'Hosted aggregator'],
  ['Ministral (2512)', '3B', '8B', '14B', '-', 'Hosted aggregator'],
  ['Claude (commercial)', 'Haiku 4.5', 'Sonnet 5.5', 'Opus 5.5', 'Fable 5.1', 'Provider API; advertised ordering'],
], [2200, 1100, 1300, 1100, 1100, 2560]));
c.push(tnote('Study 1 used only the Claude ladder. Open-weight sizes are parameter counts of dense models.'));
c.push(H2('Measures and Estimation'));
P('RN equals one if the stance-free recommendation matches gold. RS equals one if the stance recommendation matches the unsupported action. Conditional deference (CondRS) equals RS on stems where RN equals one. Flip equals one if RN and RS both equal one. CorrectSocial equals one if the stance-channel recommendation matches gold. Stated confidence on stance-free items yields an expected calibration error. Unparsed rows are coded zero on every indicator in the registered primary analysis and are dropped in a pre-specified sensitivity analysis; a model with more than five percent failures is kept and flagged. The unit of observation is the stem–model pair. For each outcome we estimate a linear probability model with family and domain fixed effects, Small as the reference tier, and standard errors clustered by stem. A Holm adjustment is applied to the two-sided p values for RN and Flip. H2 asserts that deference is not lower in larger models, so we evaluate the Large coefficient with two one-sided tests against a margin of five percentage points and report the 90 percent interval. Because stem-clustered errors treat the models as fixed, we also report the Large-minus-Small difference per family with a bootstrap interval over stems within the family, and an exact sign test over families. With five families the smallest attainable two-sided sign-test p value is .0625, so conclusions about scale are stated as patterns across families. The open-weight sample and the commercial ladder are analyzed separately and are not pooled. A pre-registered informativeness rule required pooled RN in the open sample between .35 and .95 and conditional deference above .02 in at least one tier before a result counts as informative about H1 to H3.');

// =============== Results
c.push(H1('Results'));
c.push(H2('Study 1: Commercial Ladder, Easy Items'));
P('All four tiers returned parsable answers on essentially every query. Normative consistency was at ceiling (Haiku .992, and 1.000 for Sonnet, Opus, and Fable) and deference was close to floor (.025, .025, .017, and .000; eight deferring answers in 480). The Large-minus-Small difference in RS was −0.008 with a 90 percent interval of [−0.040, +0.023], inside the margin, but the interval describes two tiers with two or three deferring answers each. The only significant tier contrast was for CorrectSocial (Haiku .892; Sonnet, Opus, and Fable .975 to .992), which is explained by Haiku choosing the third option on 10 of 120 stance-bearing stems and not by deference. Study 1 was therefore uninformative about H1 and H3. The follow-up replaced the bank because of this ceiling and floor; the replacement was fixed under the pre-registered gate described above and was not tuned on the results of any hypothesis test.');
c.push(H2('Study 1b: Descriptives'));
P('The informativeness rule was met in the open sample: the mean RN across the ten open models was .75 (range .53 to .91), and conditional deference was far above .02 in every tier. Parse failures were negligible except for Qwen2.5-7B, with 10.8 percent in the stance-free channel and 15.8 percent in the stance channel and a mean output of 20 tokens. Table 3 gives the model-level outcomes under the registered coding. The commercial ladder was again at ceiling on RN in every tier (1.000), and its deference was .050 for Haiku and zero for the three larger tiers.');
c.push(...tcap(3, 'Model-Level Outcomes in Study 1b'));
c.push(atable(['Model (tier)', 'Parse fail, free / stance', 'RN', 'RS', 'Flip', 'CorrectSocial', 'ECE'], [
  ['Qwen2.5-7B (S)', '10.8% / 15.8%', '.542', '.642', '.300', '.192', '.398'],
  ['Qwen2.5-72B (L)', '0.0% / 0.0%', '.908', '.150', '.092', '.850', '.067'],
  ['Llama-3.1-8B (S)', '0.0% / 1.7%', '.758', '.392', '.258', '.558', '.187'],
  ['Llama-3.1-70B (L)', '0.8% / 0.8%', '.900', '.175', '.142', '.792', '.090'],
  ['Gemma-3-4B (S)', '0.0% / 0.0%', '.525', '.708', '.325', '.225', '.429'],
  ['Gemma-3-12B (M)', '0.0% / 0.0%', '.783', '.525', '.358', '.450', '.213'],
  ['Gemma-3-27B (L)', '0.0% / 0.0%', '.883', '.525', '.433', '.458', '.112'],
  ['Ministral-3B (S)', '0.8% / 0.0%', '.633', '.550', '.267', '.392', '.342'],
  ['Ministral-8B (M)', '0.0% / 0.0%', '.783', '.367', '.233', '.558', '.223'],
  ['Ministral-14B (L)', '0.0% / 0.0%', '.825', '.275', '.175', '.625', '.165'],
  ['Claude Haiku (S)', '0.0% / 0.0%', '1.000', '.050', '.050', '.908', '.032'],
  ['Claude Sonnet (M)', '0.0% / 0.0%', '1.000', '.000', '.000', '.992', '.042'],
  ['Claude Opus (L)', '0.0% / 0.0%', '1.000', '.000', '.000', '1.000', '.038'],
  ['Claude Fable (XL)', '0.0% / 0.8%', '1.000', '.000', '.000', '.992', '.028'],
], [2400, 2000, 800, 800, 800, 1400, 800]));
c.push(tnote('Rows with parse failures are coded zero. ECE = expected calibration error on stance-free items. With failed rows dropped, Qwen2.5-7B has RN .607, RS .762, Flip .367, CorrectSocial .228; the other rows change by at most .015.'));
c.push(H2('Tier Contrasts in the Open-Weight Sample'));
P('Table 4 gives the pooled regression. Larger tiers had higher RN (Large +0.265, Mid +0.199; both p < .001), which supports H1. They also had lower deference: the stance-endorsed answer fell by 0.292 for Large and 0.215 for Mid, and conditional on a correct stance-free answer by 0.238 and 0.185. The 90 percent interval for the Large contrast in RS was [−0.345, −0.238] and for conditional deference [−0.297, −0.179]; both lie wholly below the registered margin of −5 points, so H2 is not supported, and the one-sided test of an increase (H3) gave p = 1.000. Flip fell by 0.077 (p = .009, Holm-adjusted), a smaller fall than RS because Flip also requires a correct stance-free answer, which becomes more common with tier. Larger tiers also gave the gold answer more often when the stance pointed away from it (CorrectSocial +0.340 for Large). The results were unchanged in direction and size when failed rows were dropped (RS −0.319, conditional deference −0.238, Flip −0.091), and they held in the subgroup of Domains 4 to 6 (RS −0.275, conditional deference −0.185).');
c.push(...tcap(4, 'Pooled Linear Probability Models, Open-Weight Sample, Large and Mid Relative to Small'));
c.push(atable(['Outcome', 'N', 'Large', 'Mid', 'Large, failed rows dropped'], [
  ['RN', '1,200', '+0.265 (0.033)', '+0.199 (0.040)', '+0.248 (0.033)'],
  ['RS', '1,200', '−0.292 (0.032)', '−0.215 (0.044)', '−0.319 (0.033)'],
  ['Conditional RS', '905', '−0.238 (0.036)', '−0.185 (0.047)', '−0.238 (0.036)'],
  ['Flip', '1,200', '−0.077 (0.029)', '−0.043 (0.035)', '−0.091 (0.030)'],
  ['CorrectSocial', '1,200', '+0.340 (0.031)', '+0.249 (0.043)', '+0.325 (0.032)'],
], [1800, 900, 2000, 2000, 2660]));
c.push(tnote('Coefficients with stem-clustered standard errors in parentheses; family and domain fixed effects; Small is the reference. All coefficients for Large are significant at p < .01; the Mid coefficient for Flip is not significant (p = .219). N with failed rows dropped: RN 1,185; RS 1,178; Flip 1,173; CorrectSocial 1,178.'));
c.push(H2('Family-Level Contrasts'));
P('Table 5 gives the Large-minus-Small difference for each family. RN was higher in the larger tier in four of five families (the Claude ladder was at ceiling in both), and RS was lower in all five (exact sign test p = .062; leave-one-family-out range −0.292 to −0.181). Conditional deference was also lower in all five (mean −0.205, p = .062). With failed rows dropped the Qwen2.5 contrast in RS grew from −0.492 to −0.594 and the mean across families was −0.265. Gemma-3 differed from the others. From the 12B to the 27B variant RN rose from .783 to .883 while RS stayed at .525, and Flip rose from .358 to .433; the family-level interval for the change in Flip was [−0.000, +0.225] and for conditional deference [−0.262, +0.004]. For this family, a more accurate model was not a less deferential one.');
c.push(...tcap(5, 'Large Minus Small by Family (95% Bootstrap Interval over Stems)'));
c.push(atable(['Family', 'RN', 'RS', 'Conditional RS', 'Flip'], [
  ['Claude', '+0.000 [+0.000, +0.000]', '−0.050 [−0.092, −0.017]', '−0.050 [−0.092, −0.017]', '−0.050 [−0.092, −0.017]'],
  ['Gemma-3', '+0.358 [+0.258, +0.458]', '−0.183 [−0.292, −0.083]', '−0.128 [−0.262, +0.004]', '+0.108 [−0.000, +0.225]'],
  ['Llama-3.1', '+0.142 [+0.042, +0.242]', '−0.217 [−0.317, −0.108]', '−0.183 [−0.291, −0.069]', '−0.117 [−0.208, −0.017]'],
  ['Ministral', '+0.192 [+0.083, +0.292]', '−0.275 [−0.392, −0.150]', '−0.209 [−0.351, −0.072]', '−0.092 [−0.192, +0.008]'],
  ['Qwen2.5', '+0.367 [+0.267, +0.467]', '−0.492 [−0.583, −0.400]', '−0.453 [−0.584, −0.326]', '−0.208 [−0.308, −0.108]'],
], [1200, 2000, 2000, 2200, 1960]));
c.push(tnote('Failed rows coded zero (registered primary). Sign test across the five families: RN higher in 4 of 5 (p = .125); RS lower in 5 of 5 (p = .062); conditional RS lower in 5 of 5 (p = .062).'));
c.push(H2('The Commercial Ladder'));
P('The commercial ladder could not test H1 because RN was 1.000 in every tier. Deference was low and fell with tier: Haiku .050, and zero for Sonnet, Opus, and Fable. The Large-minus-Small difference was −0.050 (SE 0.020, p = .014; 90 percent interval [−0.083, −0.017]), below the registered margin, so H2 is not supported there either, and an exact McNemar test on paired stems for Haiku against Opus gave six stems with the stance-endorsed answer only for Haiku and none for Opus (p = .031). The same direction held in Domains 4 to 6 (−0.083, p = .026). Absolute deference was far lower than in the open-weight models, which means the ladder is informative about direction but at a level where a few answers decide the contrast.');
c.push(H2('Large Tiers Differ More Across Families Than Sizes Differ Within Them'));
P('At the largest tier, RN was similar across the four open families (Qwen2.5-72B .908, Llama-3.1-70B .900, Gemma-3-27B .883, Ministral-14B .825), but RS ranged from .150 (Qwen2.5-72B) through .175 (Llama-3.1-70B) and .275 (Ministral-14B) to .525 (Gemma-3-27B). The spread in deference among the largest models, 37.5 percentage points, is of the same order as the within-family difference between smallest and largest tiers (18 to 49 points). Size does not therefore identify a safe model on its own, and the family or post-training recipe matters at least as much. The data do not allow us to say which feature of the recipe drives this.');
c.push(H2('Which Stance Sentences Produced Deference'));
P('Table 6 reports deference by stance sentence for the open-weight sample. Deference fell with tier for each of the four sentences. It was highest when the sentence asserted that a colleague had reviewed the action (RS .730 for Small and .367 for Large) and lowest when it cited precedent (.374 and .109). The ordering of sentence types was the same in all three tiers, so the tier effect cannot be attributed to one sentence. We report this as exploratory.');
c.push(...tcap(6, 'Deference (RS) by Stance Sentence and Tier, Open-Weight Sample, Failed Rows Dropped'));
c.push(atable(['Sentence', 'Small (N = 120)', 'Mid (N = 60)', 'Large (N = 120)'], [
  ['A colleague has reviewed it and agrees', '.730', '.500', '.367'],
  ['I have handled such cases for years and am certain', '.643', '.600', '.358'],
  ['The client’s lawyer has confirmed it', '.649', '.433', '.292'],
  ['We did the same last quarter and it went fine', '.374', '.250', '.109'],
], [4600, 1600, 1600, 1560]));
c.push(tnote('Cell sizes pool the families that have the tier (Mid exists for two families).'));

// =============== Discussion
c.push(H1('Discussion'));
c.push(H2('What the Data Show'));
P('The registered prediction that scale would not lower deference is not supported. In the open-weight sample larger tiers were more consistent and less deferential, by large margins, and the direction was the same in all five families, including the commercial ladder, where it rests on few events. That the direction was uniform is the most robust feature of the result; that five families cannot establish it as a general property is the most important caution, since the smallest p value a sign test over five families can give is .062. The Gemma-3 family, in which accuracy rose and deference did not, shows that the two properties can separate, and in that sense the measurement distinction at the center of the account is borne out even though its sign prediction is not.');
P('We do not claim to know why deference fell. Larger models in this panel come from families with different post-training, and recent post-training often targets agreement with a user’s stated view. The commercial tiers, which fell together toward zero, also differ from the open-weight families in training and in whether they accept sampling control. Scale, generation, and recipe are confounded in any such ladder, and our design cannot separate them. The informative comparison for a decision maker is the one we report: among models that a firm might choose, bigger tiers of the same family were less deferential, and families differed more than sizes.');
c.push(H2('Implications for Practice'));
P('For an organization choosing among tiers of a family, the results support a weak default: a larger tier is likely to be both more accurate and less deferential in structured decisions of this kind. They do not support treating size as a safeguard. The largest open models in the panel still endorsed the stance-endorsed option on 15 to 53 percent of items in which the stance asserted unverifiable support, and two families with similar consistency at the largest tier differed sharply in deference (Gemma-3-27B: RN .883, RS .525; Qwen2.5-72B: RN .908, RS .150). The practical remedy remains to test candidate models on stance-free and stance-bearing versions of the organization’s own decisions, with several wordings of each, and to track deference as well as accuracy. Our stance sentences assert support that the model cannot check; the results should be generalized to that form of pressure and not to a bare preference, for which Study 1 on the commercial ladder found almost none.');
c.push(H2('Limitations'));
P('The study covers four open-weight families and one commercial family, so no claim about scale in general is available, and the sign test over families has little power. Tiers differ in more than size. Hosted inference did not allow control of serving hardware or quantization, and the commercial Sonnet, Opus, and Fable tiers could not be run at temperature zero. The stems are synthetic, template-generated, and written by the research team; the automated audit confirms that the keys are internally consistent, but the registered blind human review was not carried out. The hard bank was built after seeing that the easy bank had no variance. The bank was fixed under a pre-registered gate and not tuned on hypothesis-test results, but it is a second instrument and the two banks are not directly comparable. The stance sentences differ between the banks, and in Study 1b they assert support. The stance list is closed and short, and the planned wording-robustness set and stance-echo coding were not run. Outcomes are first choices in a single turn without tools or memory. Qwen2.5-7B had a high parse-failure rate; results are reported with and without failures and do not change in direction. The human-reliance experiment that motivates the account has not been fielded, so we make no claim about how people respond to a size cue or to a stance-aligned recommendation.');
c.push(H2('Future Research'));
P('Three extensions follow. A wording-robustness replication, with alternative system prompts and the second stance list that is already part of the replication package, would test whether the direction depends on the registered wording. A design that varies post-training within a fixed size, where the vendor releases such pairs, would separate scale from recipe. And the human experiment, in which people authorize decisions after seeing a recommendation that is labeled by tier and that does or does not echo the requester’s stance, would test whether the tier cue changes reliance independently of what these results show about the models.');
c.push(H1('Conclusion'));
P('We asked whether a larger model is a better decision partner when a requester already prefers an answer. In ten open-weight models and one commercial ladder, larger tiers were more accurate and less deferential, in every family, and the registered prediction that scale does not lower deference was not supported. Deference nevertheless remained common in the largest open models and differed more across families than across sizes. A first test that met a ceiling and a floor was repaired under a registered gate, and the full record, with the item banks, the audit, and the analysis code, is released so that these conclusions can be tested again.');

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
