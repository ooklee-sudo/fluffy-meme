const fs = require('fs');
const { d, P, H1, H2, run } = require('./lib');
const { Document, Packer, Paragraph, AlignmentType, Footer, PageNumber, TextRun } = d;
const { intro, related, model, thinning, cascade, typed } = require('./theory');
const { method } = require('./method');
const { results } = require('./results');
const { discussion, conclusion, references } = require('./tail');

const title = 'Operational Readiness for LLM Hallucinations: A Counting-Process Capacity Model and Measured Evidence on Guardrail Cascades';
const S = require('../runs/summary.json');
const R3 = ['qwen05', 'smol360', 'qwen15'];
const rg = (a, d = 0) => { const lo = Math.min(...a).toFixed(d), hi = Math.max(...a).toFixed(d); return lo === hi ? lo : `${lo}-${hi}`; };
const cfgk = (r, c) => S[r].sla500.configs.find(x => x.config === c);
const red = R3.map(r => 100 * (1 - cfgk(r, 'L2').k_star / cfgk(r, 'none').k_star));
const fb = R3.map(r => 100 * S[r].false_block_share_of_good.L2);
const dsr = R3.map(r => S[r].dependence_stats.ratio_no_routing.point), dsrr = R3.map(r => S[r].dependence_stats.ratio_with_routing.point);
const none3 = R3.map(r => 100 * S[r].burst.poisson_checks.none.p_exceed_k_star_observed), none44 = R3.map(r => 100 * S[r].burst044.poisson_checks.none.p_exceed_k_star_observed);
const best = R3.flatMap(r => [100 * S[r].burst.poisson_checks['L1+L2'].p_exceed_k_star_observed, 100 * S[r].burst044.poisson_checks['L1+L2'].p_exceed_k_star_observed]);
const TC = S.failure.typed_capacity, tcr = TC.scenarios.map(x => 100 * (x.all_classes.k_typed / x.all_classes.k_naive_poisson - 1));
const T3 = S.triage, ccv = [T3.software_company.arrivals.detrended.implied_daily_rate_cv, T3.italian_helpdesk.arrivals.detrended.implied_daily_rate_cv, T3.servicenow.arrivals.detrended.implied_daily_rate_cv];
const caus = [T3.software_company.arrivals.causal.poisson_plan_exceeded, T3.italian_helpdesk.arrivals.causal.poisson_plan_exceeded].map(x => 100 * x);
const abstract = [
  H1('Abstract'),
  P(`Organisations that deploy large language models (LLMs) must decide how much human triage capacity to hold in reserve and how many automated guardrail layers to place in front of the model. Two simple heuristics, provisioning at the mean incident load and crediting each guardrail layer with its stand-alone effectiveness as if layers failed independently, are easy to apply but can be improved on. We describe the capacity requirement as a quantile of the daily count of human-handled incidents and replace a single Poisson description of all failures by typed classes: hallucinations as thinned, over-dispersed streams; provider incidents as seasonal, level-adjusted processes with at most weak self-excitation; serving failures as heavy-tailed episodes; and heavy-tailed human service. We show analytically that over-dispersion inflates required capacity, that positive association between layers makes the independence formula a lower bound on residual risk, and that, because capacity is integer-valued, cost is not unimodal in the number of layers. We evaluate the pipeline on the outputs of three small open LLMs that answered the same 300 SQuAD 2.0 questions (900 answers) through three executed guardrail layers with measured latency and failures; user arrivals are simulated and informed by public traces of an LLM service, of LLM providers' incidents and of company ticket systems, none of which is a hallucination log. A single task-specific verifier, adopted after an NLI classifier proved uninformative and evaluated on the same questions, reduced required capacity by ${rg(red)}% but blocked ${rg(fb)}% of correct answers; a routed judge added a modest, model-dependent gain at about triple the latency. The share of hallucinations passing a two-layer cascade was ${rg(dsr, 1)} times the independence prediction without routing and ${rg(dsrr, 1)} times with routing, with wide intervals. With mild burstiness (daily-rate CV 0.3-0.44) a Poisson-sized capacity plan was exceeded on ${rg([...none3, ...none44])}% of days without guardrails and ${rg(best)}% with the best cascade, against a target of 5%; in public ticket streams the net-of-trend daily-rate CV was ${rg(ccv, 2)} and a causal Poisson plan was exceeded on about ${rg(caus)}% of work days, whereas over-dispersion changed the 95% capacity by at most one or two units for low-rate streams (provider incidents, dated court cases). In an illustrative organisation, a typed superposition required ${rg(tcr)}% more daily capacity than a single Poisson on the total, with the gap driven by the assumed dispersion of the hallucination class and by how strongly over-dispersed the serving class is taken to be. Hallucination arrivals are simulated and, to our knowledge, no operator log of hallucinations is public; the models are small and the task is extractive question answering, so the numbers do not transfer to production, whereas the method and its diagnostics do.`),
  new Paragraph({ children: [run('Keywords: ', { bold: true }), run('LLM operations, hallucination, guardrails, capacity planning, Poisson process, over-dispersion, design science')], spacing: { after: 200 } }),
];
const frontNote = new Paragraph({ children: [run('Working draft. Code, data pointers and analysis scripts: hallucination_poisson/ in the accompanying repository.', { italics: true, size: 18 })], spacing: { after: 160 } });

const doc = new Document({
  creator: 'Author', title,
  styles: { default: { document: { run: { font: 'Times New Roman', size: 22 } } } },
  numbering: { config: [{ reference: 'bul', levels: [{ level: 0, format: d.LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: 'Times New Roman', size: 18 })] })] }) },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [run(title, { bold: true, size: 30 })] }),
      frontNote, ...abstract, ...intro, ...related, ...model, ...thinning, ...cascade, ...typed, ...method, ...results, ...discussion, ...conclusion, ...references,
    ],
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync('../runs/LLM_Hallucination_Poisson_Framework_Revised.docx', b); console.log('written', b.length); });
