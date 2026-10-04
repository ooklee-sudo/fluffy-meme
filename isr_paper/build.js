const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,WidthType,ShadingType,AlignmentType,HeadingLevel,BorderStyle,Footer,PageNumber,LineRuleType}=require('docx');
const F='Times New Roman';
const DBL={line:480,lineRule:LineRuleType.AUTO};
const SGL={line:240,lineRule:LineRuleType.AUTO};
// inline markup: *italic*  **bold**
function runs(t,o={}){const out=[];const re=/(\*\*[^*]+\*\*|\*[^*]+\*)/g;let last=0,m;
 while((m=re.exec(t))){if(m.index>last)out.push(new TextRun({text:t.slice(last,m.index),font:F,size:o.size||24,...o}));
  const s=m[0];if(s.startsWith('**'))out.push(new TextRun({text:s.slice(2,-2),bold:true,font:F,size:o.size||24,...o}));
  else out.push(new TextRun({text:s.slice(1,-1),italics:true,font:F,size:o.size||24,...o}));last=m.index+s.length;}
 if(last<t.length)out.push(new TextRun({text:t.slice(last),font:F,size:o.size||24,...o}));return out;}
const P=(t)=>new Paragraph({children:runs(t),spacing:{...DBL,after:0},indent:{firstLine:720},alignment:AlignmentType.LEFT});
const H1=(t)=>new Paragraph({heading:HeadingLevel.HEADING_1,children:[new TextRun({text:t,bold:true,font:F,size:24,allCaps:true})],spacing:{before:360,after:120,...SGL},keepNext:true});
const H2=(t)=>new Paragraph({heading:HeadingLevel.HEADING_2,children:[new TextRun({text:t,bold:true,font:F,size:24})],spacing:{before:240,after:120,...SGL},keepNext:true});
const H3=(t)=>new Paragraph({heading:HeadingLevel.HEADING_3,children:[new TextRun({text:t,bold:true,italics:true,font:F,size:24})],spacing:{before:200,after:100,...SGL},keepNext:true});
const EQ=(t,n)=>new Paragraph({children:[new TextRun({text:t,italics:true,font:F,size:24}),new TextRun({text:'\t('+n+')',font:F,size:24})],tabStops:[{type:'right',position:9360}],spacing:{before:120,after:120,...SGL},alignment:AlignmentType.CENTER});
const CAP=(t)=>new Paragraph({children:runs(t,{size:22}),spacing:{before:240,after:80,...SGL},keepNext:true,alignment:AlignmentType.CENTER});
const NOTE=(t)=>new Paragraph({children:runs(t,{size:20}),spacing:{before:60,after:200,...SGL}});
const C=(t)=>new Paragraph({children:[new TextRun({text:'',font:F})],spacing:SGL});
const bd={style:BorderStyle.SINGLE,size:4,color:'000000'},nb={style:BorderStyle.NONE,size:0,color:'FFFFFF'};
function TBL(widths,rows,hdr=true){const tot=widths.reduce((a,b)=>a+b,0);
 return new Table({width:{size:tot,type:WidthType.DXA},columnWidths:widths,rows:rows.map((r,i)=>new TableRow({tableHeader:i===0&&hdr,cantSplit:true,children:r.map((c,j)=>new TableCell({width:{size:widths[j],type:WidthType.DXA},
  borders:{top:i===0?bd:nb,bottom:(i===0||i===rows.length-1)?bd:nb,left:nb,right:nb},margins:{top:50,bottom:50,left:90,right:90},
  shading:i===0?{fill:'EDEDED',type:ShadingType.CLEAR,color:'auto'}:undefined,
  children:[new Paragraph({children:runs(c,{size:20,bold:i===0}),spacing:SGL})]}))}))});}
const REF=(t)=>new Paragraph({children:runs(t),spacing:{...SGL,after:120},indent:{left:720,hanging:720}});
const TODO='[TO BE COMPLETED AFTER ESTIMATION]';

const body=[];
const add=(...x)=>body.push(...x);

// Title page
add(new Paragraph({children:[new TextRun({text:'Beyond Exposure: Fixed Costs, Foundation Models, and the Diffusion of AI Vision',bold:true,font:F,size:32})],alignment:AlignmentType.CENTER,spacing:{before:1200,after:240,...SGL}}),
 new Paragraph({children:[new TextRun({text:'Evidence from Online Job Postings',italics:true,font:F,size:26})],alignment:AlignmentType.CENTER,spacing:{after:480,...SGL}}),
 new Paragraph({children:[new TextRun({text:'Manuscript prepared for submission to Information Systems Research',font:F,size:22})],alignment:AlignmentType.CENTER,spacing:{after:120,...SGL}}),
 new Paragraph({children:[new TextRun({text:'[Author names and affiliations removed for double-blind review]',font:F,size:22})],alignment:AlignmentType.CENTER,spacing:{after:480,...SGL}}),
 new Paragraph({children:[new TextRun({text:'Status of this draft. ',bold:true,font:F,size:22}),new TextRun({text:'This draft implements the full manuscript structure, theory, hypotheses, measurement and identification strategy of the research proposal. The Lightcast data have not yet been extracted and no model has been estimated. Section 6 therefore contains pre-specified tables with placeholders and no numerical results; no empirical finding is asserted anywhere in this draft. Bibliographic details marked † must be verified before submission.',font:F,size:22})],spacing:{...SGL},shading:{fill:'F5F5F5',type:ShadingType.CLEAR,color:'auto'}}),
 new Paragraph({children:[],pageBreakBefore:true}));

// Abstract
add(new Paragraph({children:[new TextRun({text:'Abstract',bold:true,font:F,size:24})],alignment:AlignmentType.CENTER,spacing:{after:120,...SGL}}),
 new Paragraph({children:runs('Whether AI vision displaces workers depends less on what the technology can see than on whether automating a visual task covers a largely fixed cost. We develop a break-even model of automation in which a firm adopts computer vision only when its volume of visual tasks exceeds a threshold, and derive four testable predictions: adoption reduces demand for vision-intensive occupations, more so in firms with large visual task volumes; general-purpose vision foundation models lower the break-even scale and extend adoption to smaller firms; and adoption raises demand for complementary judgment, monitoring, and integration skills. We design a test using Lightcast online job postings for the United States, 2015–2025, measuring adoption from firms’ computer-vision skill requirements and occupational visual intensity from O*NET task statements, and using staggered difference-in-differences and an event study around foundation-model releases, while separating vision effects from concurrent large language model effects. The paper moves research on AI and work from technical exposure to the economics of adoption.'),spacing:{...SGL,after:200},alignment:AlignmentType.JUSTIFIED}),
 new Paragraph({children:[new TextRun({text:'Keywords: ',bold:true,font:F,size:24}),new TextRun({text:'AI adoption; computer vision; foundation models; automation; fixed costs; online job postings; technology diffusion; complementary assets; difference-in-differences',font:F,size:24})],spacing:{...SGL,after:120}}),
 new Paragraph({children:[new TextRun({text:'History: ',bold:true,font:F,size:24}),new TextRun({text:'[to be completed by the journal].',font:F,size:24})],spacing:SGL}),
 new Paragraph({children:[],pageBreakBefore:true}));

// 1 Intro
add(H1('1. Introduction'),
P('Debates about artificial intelligence (AI) and work have been organized around exposure: the degree to which the capabilities of a technology overlap with the tasks that make up an occupation (Webb 2020; Felten et al. 2021; Eloundou et al. 2023). Exposure is a statement about technical feasibility. It does not say whether a firm finds it profitable to act on that feasibility. A task can be fully within reach of a machine and still be performed by a person because building, integrating, and maintaining the machine costs more than the labor it replaces.'),
P('This distinction is sharpest for computer vision, where costs are concrete and largely fixed. Svanberg et al. (2024)† simulate the cost of deploying computer vision systems and estimate that only about 23% of the wages attached to vision-dependent tasks would be attractive to automate at current costs, because development, integration, and maintenance costs do not scale with usage. That figure is the output of a cost model. It has not been tested against how firms actually behave, and the model itself implies a sharp, observable pattern: automation should occur where the volume of a visual task is large relative to a break-even threshold, and nowhere else.'),
P('Large pretrained vision and vision-language models, which we call vision foundation models, should move this threshold. By reducing the task-specific data and development effort required, and by spreading fixed costs across many customers through application programming interfaces (APIs), they lower the fixed cost of adopting vision for any single firm. If that is right, adoption should extend to smaller firms whose visual workloads were previously too small to justify a bespoke system. This is a diffusion claim as much as a labor claim, and it speaks directly to how platform-like layers of AI infrastructure reshape who can use AI.'),
P('We therefore ask three questions. **RQ1:** How does AI vision adoption change a firm’s demand for vision-intensive occupations and complementary skills? **RQ2:** Are these effects concentrated in firms with large pre-existing volumes of visual tasks? **RQ3:** Did the arrival of vision foundation models shift adoption toward smaller firms, consistent with a falling break-even scale?'),
P('To answer them, we use Lightcast (formerly Burning Glass Technologies) online job postings for the United States from 2015 to 2025. Postings let us observe, at the firm-quarter level, both what a firm hires for and which technical skills it requires. We infer adoption of computer vision from the skills a firm begins to demand, measure the visual intensity of occupations by classifying O*NET task statements according to their dependence on visual perception, and estimate (i) staggered difference-in-differences effects of adoption on demand for vision-intensive occupations and complementary skills, (ii) heterogeneity of these effects by pre-period task scale, and (iii) an event study around the release of general-purpose vision foundation models, estimated separately by firm size. Because vision foundation models diffused alongside large language models (LLMs), all specifications control for occupational exposure to LLMs.'),
P('The paper contributes to information systems (IS) research in three ways. First, it moves the literature on AI and work from exposure to adoption economics, providing evidence on a fixed-cost mechanism that cost simulations have proposed but not tested. Second, it contributes to research on IT business value and complementary assets by identifying which skills rise in demand alongside vision adoption. Third, it studies how foundation models, as a platform-like layer of AI infrastructure, change the diffusion of AI capabilities across firms of different sizes, connecting to IS work on digital platforms and technology diffusion.'),
P('The remainder of the paper is organized as follows. Section 2 reviews related literature. Section 3 presents the model and hypotheses. Section 4 describes the data and measures. Section 5 sets out the empirical strategy and threats to identification. Section 6 reports the pre-specified analyses. Section 7 discusses contributions, implications, and limitations.'));

// 2 Lit
add(H1('2. Related Literature'),
H2('2.1 AI Exposure and Labor Demand'),
P('A large literature measures how closely AI capabilities map onto occupational tasks. Webb (2020)† links patent text to task descriptions, Felten et al. (2021) link AI application progress to workplace abilities and build occupation-, industry-, and geography-level exposure indices, and Eloundou et al. (2023) assess the exposure of occupations to LLMs. Acemoglu et al. (2022) move from exposure to behavior, using online vacancies to show that establishments with greater AI-exposed task content reduce hiring for non-AI positions. We build on this vacancy-based approach but ask a different question. Exposure indices rank occupations by feasibility; we ask when feasibility is converted into adoption, and we exploit variation in firm scale that the exposure literature does not use.'),
H2('2.2 Economics of Automation and Prediction'),
P('Agrawal et al. (2018) frame AI as a fall in the cost of prediction, which raises the value of complements such as judgment and action. This framing motivates our complementarity hypothesis. The cost-effectiveness approach of Svanberg et al. (2024)† adds that the cost of AI is not only the marginal cost of a prediction but also a fixed cost of building and maintaining a system. Our contribution is to test this logic with observed adoption rather than simulated cost.'),
H2('2.3 IT Business Value, Complementary Assets, and Diffusion'),
P('IS research has long argued that the value of IT depends on complementary organizational assets and skills, and that diffusion is shaped by adoption costs and firm characteristics. Foundation models resemble a platform layer whose fixed development cost is borne by a provider and shared across adopters through APIs. This suggests that platform-mediated cost sharing can change who adopts, not only how much adopters gain. [Positioning against recent ISR, MIS Quarterly, and Management Science work on AI adoption and labor is to be completed in the final manuscript; the underlying proposal did not yet include this review and we do not cite specific papers here.]'));

// 3 Theory
add(H1('3. Theory and Hypotheses'),
H2('3.1 A Break-Even Model of Vision Automation'),
P('Consider a visual task performed *q* times per year at labor cost *θ* per unit. An AI system has fixed cost *F*, annualized using the capital recovery factor *φ(r, T)* for discount rate *r* and system lifetime *T*, plus an annual maintenance rate *m*. It also has an inference cost *c* per unit. Conditional on meeting the task’s accuracy requirement, the firm automates when its task volume exceeds the break-even volume:'),
EQ('q* = F [ φ(r, T) + m ] / ( θ − c )',1),
P('Equation (1) has two implications that exposure measures cannot capture. First, even technically feasible automation is not adopted when *q* < *q**, so adoption is concentrated among firms with large visual workloads. Second, *q** is proportional to the fixed cost *F*. Vision foundation models reduce task-specific data and development costs and are shared across many customers, so they lower *F* and therefore *q**. They may, however, raise the per-unit inference cost *c*, which works in the opposite direction by raising *q**. The net effect on the threshold is thus an empirical matter, and our hypothesis is that the fixed-cost effect dominates in practice.'),
H2('3.2 Hypotheses'),
P('Adopting firms substitute AI for labor in tasks above the threshold, which yields H1. Because the saving from automation scales with *q*, and only firms with *q* well above *q** gain enough to adopt at scale, displacement should be larger where visual task volume is high (H2). A fall in *q** brings smaller firms across the threshold (H3). Finally, cheaper visual prediction raises the value of complements in the sense of Agrawal et al. (2018) (H4).'),
CAP('**Table 1.** Hypotheses and observable predictions'),
TBL([900,4000,4460],[
 ['','Hypothesis','Prediction in posting data'],
 ['H1','Vision adoption displaces demand for vision-intensive tasks within the adopting firm.','Postings in high-visual-intensity occupations fall after adoption.'],
 ['H2','Displacement is larger where visual task volume is high (q well above q*).','Effect increases with pre-period scale of vision-intensive postings.'],
 ['H3','Foundation models lower the break-even scale of adoption.','After the shock, adoption rises most among smaller firms with high visual exposure.'],
 ['H4','Cheaper visual prediction raises demand for complements: judgment, monitoring, and integration.','Share of postings requiring these skills rises in adopting firms.']]),
C());

// 4 Data
add(H1('4. Data and Measures'),
H2('4.1 Lightcast Job Postings'),
P('The primary source is Lightcast U.S. online job postings, which record employer, occupation (SOC/O*NET), industry, location, posting date, required skills, and, where available, posted wages. The sample covers 2015–2025 at the firm-quarter level. To obtain stable firm-level measures we restrict to employers with at least 50 postings per year in the pre-period (2015–2018), and we match a subsample to Compustat for employment and financial controls.'),
H2('4.2 Key Measures'),
P('Table 2 summarizes the construction of the main variables. *Vision adoption* is the first quarter in which postings requiring computer-vision skills (for example, computer vision, machine vision, image processing, object detection, image segmentation, OpenCV) exceed a threshold share of the firm’s postings; we vary the threshold in robustness checks, and exact skill names will be verified against the current Lightcast Open Skills taxonomy. *Visual task intensity* is the share of an occupation’s O*NET task statements that depend on visual perception or inspection, classified using an LLM-assisted protocol validated against human coders on a random sample. *Firm visual exposure* aggregates occupational visual intensity using pre-period posting weights, and *firm language exposure* does the same for occupational LLM exposure from Eloundou et al. (2023). Firm-level exposures are fixed in the pre-period so that they are not themselves affected by adoption.'),
CAP('**Table 2.** Variable construction'),
TBL([1700,5560,2100],[
 ['Construct','Operationalization','Source'],
 ['Vision adoption','Firm posts jobs requiring computer-vision skills. Adoption date = first quarter in which such postings exceed a threshold share; thresholds varied in robustness checks.','Lightcast skills taxonomy (names to be verified)'],
 ['Visual task intensity','Share of each occupation’s O*NET task statements that depend on visual perception or inspection; LLM-assisted classification validated against human coders on a random sample.','O*NET task statements'],
 ['Firm visual exposure (VisExp)','Posting-weighted average of occupational visual intensity in the pre-period (2015–2018).','Lightcast + O*NET'],
 ['Firm language exposure (LangExp)','Posting-weighted average of occupational exposure to large language models.','Eloundou et al. (2023)'],
 ['Task scale','Pre-period count of postings in vision-intensive occupations; Compustat employment for the matched subsample.','Lightcast, Compustat'],
 ['Outcomes','Log postings and posting share in high-visual-intensity occupations; share of postings requiring judgment, monitoring, or systems-integration skills; posted wages.','Lightcast']]),
C());

// 5 Methods
add(H1('5. Empirical Strategy'),
H2('5.1 Effects of Adoption (H1, H2, H4)'),
P('Adoption timing varies across firms, so we estimate a staggered difference-in-differences design. Because two-way fixed-effects estimates are biased under heterogeneous treatment timing, we use the Callaway and Sant’Anna (2021) estimator with not-yet-treated firms as controls. The dynamic specification is:'),
EQ('Y_ft = α_f + λ_jt + Σ_k β_k · 1[t − E_f = k] + X′_ft γ + ε_ft',2),
P('where *Y_ft* is an outcome for firm *f* in quarter *t*, *E_f* is the adoption quarter, *α_f* are firm fixed effects, and *λ_jt* are industry-by-quarter fixed effects. H1 predicts negative post-adoption coefficients *β_k* for postings in high-visual-intensity occupations, and H4 predicts positive coefficients for the share of postings requiring judgment, monitoring, or integration skills. For H2 we estimate group-time effects separately by terciles of pre-period task scale and test whether effects increase with scale.'),
H2('5.2 Foundation Models and the Break-Even Scale (H3)'),
P('Adoption is itself endogenous, so for H3 we exploit the release of general-purpose vision foundation models as a common shock whose bite varies with firms’ pre-period visual exposure. Our primary shock date is 2023Q2, when promptable segmentation and vision-language models became broadly available; we use the 2021 release of contrastive image-text models as an alternative date. The event-study specification, estimated separately by firm size class, is:'),
EQ('Adopt_ft = α_f + λ_jt + Σ_k δ_k (VisExp_f × 1[t = k]) + Σ_k ψ_k (LangExp_f × 1[t = k]) + ε_ft',3),
P('H3 predicts that post-shock coefficients *δ_k* are positive and larger for smaller firms. Pre-shock coefficients provide a test of parallel trends. Interacting *LangExp_f* with time absorbs the concurrent language-model shock.'),
H2('5.3 Identification Threats and Robustness'),
P('**Concurrent LLM shock.** Vision foundation models diffused alongside LLMs. Beyond the language-exposure control, we compare occupations with similar language exposure but different visual intensity.'),
P('**Postings measure intent, not use.** Hiring vision talent may lag or lead deployment, and firms may buy vision systems from vendors without hiring. We validate the adoption measure against vision-related patents and, where available, public disclosures. Vendor-based adoption is not observed in postings and biases estimates toward zero.'),
P('**Coverage bias.** Online postings over-represent professional occupations. We reweight to occupational employment shares from the BLS Occupational Employment and Wage Statistics (OES) and report results by industry.'),
P('**Selection into adoption.** We use pre-trend tests, matching on pre-period characteristics, and HonestDiD sensitivity bounds (Rambachan and Roth 2023).'),
P('**Measurement of visual intensity.** We report inter-rater agreement for the task classification and show robustness to alternative exposure measures (for example, Webb 2020; Felten et al. 2021).'));

// 6 Results
add(H1('6. Pre-Specified Analyses and Results'),
P('No estimation has been conducted. This section fixes the tables and figures that will report the tests of H1–H4 and states in advance how each hypothesis will be judged, so that the analysis is committed to before outcomes are seen. All cells are placeholders.'),
H2('6.1 Descriptive Statistics and Measurement Validation'),
P('We will report sample construction (employers, postings, firm-quarters), the distribution of adoption quarters, and summary statistics for visual intensity, *VisExp*, and *LangExp*. Validation will include inter-rater agreement between the LLM-assisted and human classifications of O*NET tasks, and the correlation of the adoption measure with vision-related patenting.'),
CAP('**Table 3.** Summary statistics '+TODO),
TBL([3360,1500,1500,1500,1500],[
 ['Variable','Mean','SD','P25','P75'],
 ['Log postings, high-visual-intensity occupations','—','—','—','—'],
 ['Share of postings requiring judgment/monitoring/integration skills','—','—','—','—'],
 ['Firm visual exposure (VisExp)','—','—','—','—'],
 ['Firm language exposure (LangExp)','—','—','—','—'],
 ['Pre-period task scale','—','—','—','—']]),
C(),
H2('6.2 Effects of Adoption on Vision-Intensive Demand and Complements (H1, H2, H4)'),
P('We will estimate equation (2) with the Callaway and Sant’Anna (2021) estimator and report the aggregate average treatment effect on the treated and event-time coefficients. H1 is supported if post-adoption effects on postings in high-visual-intensity occupations are negative and statistically distinguishable from zero with flat pre-trends. H2 is supported if effects are monotonically larger in magnitude across terciles of task scale and a test of equality across terciles rejects. H4 is supported if the share of postings requiring judgment, monitoring, or integration skills rises after adoption.'),
CAP('**Table 4.** Staggered difference-in-differences estimates of adoption '+TODO),
TBL([3360,1500,1500,1500,1500],[
 ['Outcome','ATT (all)','Low scale','Mid scale','High scale'],
 ['Log postings, high-visual-intensity occupations (H1, H2)','—','—','—','—'],
 ['Posting share, high-visual-intensity occupations (H1, H2)','—','—','—','—'],
 ['Share requiring judgment skills (H4)','—','—','—','—'],
 ['Share requiring monitoring skills (H4)','—','—','—','—'],
 ['Share requiring systems-integration skills (H4)','—','—','—','—'],
 ['Posted wages (where available)','—','—','—','—']]),
NOTE('*Note.* Cells to be populated with point estimates and clustered standard errors. Controls: firm and industry-by-quarter fixed effects; not-yet-treated comparison group.'),
H2('6.3 Foundation Models and the Break-Even Scale (H3)'),
P('We will estimate equation (3) separately by firm size class and plot *δ_k* with confidence intervals. H3 is supported if pre-shock coefficients are statistically indistinguishable from zero and post-shock coefficients are positive and larger for smaller size classes, both for the 2023Q2 date and for the 2021 alternative date.'),
CAP('**Table 5.** Event-study estimates around foundation-model release '+TODO),
TBL([3360,1500,1500,1500,1500],[
 ['Firm size class','Pre-shock joint test (p)','Mean post δ (2023Q2)','Mean post δ (2021 alt.)','N firms'],
 ['Small','—','—','—','—'],
 ['Medium','—','—','—','—'],
 ['Large','—','—','—','—']]),
C(),
H2('6.4 Robustness'),
P('We will report: alternative adoption thresholds and skill lists; HonestDiD bounds on post-treatment effects; matched-sample estimates; BLS OES reweighting; results by industry; comparison of occupations with similar language exposure but different visual intensity; and alternative exposure measures (Webb 2020; Felten et al. 2021). Support for a hypothesis will require that the sign of the main estimate survive the HonestDiD bounds at a stated degree of parallel-trend violation.'));

// 7 Discussion
add(H1('7. Discussion'),
H2('7.1 Contributions'),
P('The study is designed to make three contributions. By testing a break-even prediction with observed adoption, it shifts evidence on AI and work from what the technology can do to what firms find worthwhile to automate. By tracing which skills rise alongside vision adoption, it informs the IT business value literature on the complementary assets through which AI creates value. By comparing adoption before and after foundation models across firm sizes, it provides evidence on how a platform-like AI layer redistributes access to AI capabilities. Which of these contributions is realized depends on the estimates, and the discussion will be written accordingly once results are available.'),
H2('7.2 Implications'),
P('If H3 holds, policy and managerial attention to AI and work should shift from whether a technology can perform a task to who bears its fixed cost and how that cost is shared; displacement risk would then rise for smaller employers as platforms lower the threshold. If H2 holds but H3 does not, labor effects of vision remain concentrated in large, high-volume employers regardless of model availability. If H4 holds, managers should expect adoption to shift hiring toward judgment, monitoring, and integration skills.'),
H2('7.3 Limitations'),
P('Postings measure hiring intent rather than deployment, and vendor-supplied systems are invisible to our adoption measure, which biases estimates toward zero. Postings over-represent professional occupations despite reweighting. The adoption event is a choice, so staggered difference-in-differences identifies causal effects only under parallel-trend assumptions that we probe but cannot prove; the foundation-model shock is common to all firms and relies on cross-sectional variation in exposure. The LLM-assisted classification of visual intensity depends on prompt and model choices, which we address through validation and alternative measures. Finally, the break-even model is a stylized single-task model, and multi-task bundling of automation costs is left for future work.'),
H1('8. Conclusion'),
P('Exposure shows what AI could do; fixed costs determine what firms do. By modeling vision automation as a break-even problem and testing it in firm-level hiring data around the arrival of vision foundation models, this paper aims to show whether the diffusion of AI vision is governed by scale economics, and whether platform-like AI infrastructure lowers the scale at which adoption pays.'));

// refs
add(new Paragraph({children:[],pageBreakBefore:true}),H1('References'),
REF('Acemoglu, D., Autor, D., Hazell, J., and Restrepo, P. 2022. Artificial intelligence and jobs: Evidence from online vacancies. *Journal of Labor Economics* 40(S1):S293–S340.†'),
REF('Agrawal, A., Gans, J., and Goldfarb, A. 2018. *Prediction Machines: The Simple Economics of Artificial Intelligence*. Boston: Harvard Business Review Press.†'),
REF('Callaway, B., and Sant’Anna, P. H. C. 2021. Difference-in-differences with multiple time periods. *Journal of Econometrics* 225(2):200–230.†'),
REF('Eloundou, T., Manning, S., Mishkin, P., and Rock, D. 2023. GPTs are GPTs: An early look at the labor market impact potential of large language models. arXiv:2303.10130.†'),
REF('Felten, E., Raj, M., and Seamans, R. 2021. Occupational, industry, and geographic exposure to artificial intelligence. *Strategic Management Journal* 42(12):2195–2217.†'),
REF('Rambachan, A., and Roth, J. 2023. A more credible approach to parallel trends. *Review of Economic Studies* 90(5):2555–2591.†'),
REF('Svanberg, M., Li, W., Fleming, M., Goehring, B., and Thompson, N. 2024. Beyond AI exposure: Which tasks are cost-effective to automate with computer vision? MIT FutureTech working paper, SSRN.'),
REF('Webb, M. 2020. The impact of artificial intelligence on the labor market. Working paper, Stanford University.†'),
new Paragraph({children:runs('† Details taken from the research proposal without independent verification; to be checked before submission. Lightcast skill names must be checked against the current Lightcast Open Skills taxonomy.',{size:20}),spacing:{...SGL,before:200}}));

const doc=new Document({
 styles:{default:{document:{run:{font:F,size:24}}},paragraphStyles:[
  {id:'Heading1',name:'Heading 1',basedOn:'Normal',next:'Normal',quickFormat:true,run:{size:24,bold:true,font:F},paragraph:{outlineLevel:0}},
  {id:'Heading2',name:'Heading 2',basedOn:'Normal',next:'Normal',quickFormat:true,run:{size:24,bold:true,font:F},paragraph:{outlineLevel:1}},
  {id:'Heading3',name:'Heading 3',basedOn:'Normal',next:'Normal',quickFormat:true,run:{size:24,bold:true,italics:true,font:F},paragraph:{outlineLevel:2}}]},
 sections:[{properties:{page:{size:{width:12240,height:15840},margin:{top:1440,bottom:1440,left:1440,right:1440}}},
  footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({children:[PageNumber.CURRENT],font:F,size:20})]})]})},
  children:body}]});
Packer.toBuffer(doc).then(b=>fs.writeFileSync('ISR_Paper_AI_Vision_Fixed_Costs.docx',b));
