import re
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ------------------------------------------------------------------ references (Vancouver)
REFS = {
 'gama': "Gama J, Žliobaitė I, Bifet A, Pechenizkiy M, Bouchachia A. A survey on concept drift adaptation. ACM Comput Surv. 2014;46(4):Article 44.",
 'duncan': "Duncan AJ. The economic design of X̄ charts used to maintain current control of a process. J Am Stat Assoc. 1956;51(274):228–42.",
 'khomh': "Khomh F, Dhaliwal T, Zou Y, Adams B. Do faster releases improve software quality? An empirical case study of Mozilla Firefox. In: Proceedings of the 9th IEEE Working Conference on Mining Software Repositories (MSR). 2012. p. 179–88.",
 'sculley': "Sculley D, Holt G, Golovin D, Davydov E, Phillips T, Ebner D, et al. Hidden technical debt in machine learning systems. In: Advances in Neural Information Processing Systems 28. 2015.",
 'amershi': "Amershi S, Begel A, Bird C, DeLine R, Gall H, Kamar E, et al. Software engineering for machine learning: a case study. In: Proceedings of the 41st International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP). 2019. p. 291–300.",
 'jiang': "Jiang W, Synovic N, Hyatt M, Schorlemmer TR, Sethi R, Lu YH, et al. An empirical study of pre-trained model reuse in the Hugging Face deep learning model registry. In: Proceedings of the 45th IEEE/ACM International Conference on Software Engineering (ICSE). 2023.",
 'lazaridou': "Lazaridou A, Kuncoro A, Gribovskaya E, Agrawal D, Liska A, Terzi T, et al. Mind the gap: assessing temporal generalization in neural language models. In: Advances in Neural Information Processing Systems 34. 2021.",
 'luu': "Luu K, Khashabi D, Gururangan S, Mandyam K, Smith NA. Time waits for no one! Analysis and challenges of temporal misalignment. In: Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics (NAACL). 2022.",
 'chen': "Chen L, Zaharia M, Zou J. How is ChatGPT's behavior changing over time? Harv Data Sci Rev. 2024;6(2).",
 'rust': "Rust J. Optimal replacement of GMC bus engines: an empirical model of Harold Zurcher. Econometrica. 1987;55(5):999–1033.",
 'hotz': "Hotz VJ, Miller RA. Conditional choice probabilities and the estimation of dynamic models. Rev Econ Stud. 1993;60(3):497–529.",
 'aguirre': "Aguirregabiria V, Mira P. Dynamic discrete choice structural models: a survey. J Econom. 2010;156(1):38–67.",
 'zhao': "Zhao W, Ren X, Hessel J, Cardie C, Choi Y, Deng Y. WildChat: 1M ChatGPT interaction logs in the wild. In: International Conference on Learning Representations (ICLR). 2024.",
 'dl': "DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials. 1986;7(3):177–88.",
 'cohen': "Cohen J. A coefficient of agreement for nominal scales. Educ Psychol Meas. 1960;20(1):37–46.",
 'landis': "Landis JR, Koch GG. The measurement of observer agreement for categorical data. Biometrics. 1977;33(1):159–74.",
}
order=[]
def cite_sub(text):
    def rep(m):
        keys=m.group(1).split(',')
        nums=[]
        for k in keys:
            k=k.strip().lstrip('@')
            if k not in order: order.append(k)
            nums.append(order.index(k)+1)
        nums=sorted(set(nums))
        # compress ranges
        out=[];i=0
        while i<len(nums):
            j=i
            while j+1<len(nums) and nums[j+1]==nums[j]+1: j+=1
            out.append(str(nums[i]) if j==i else (f"{nums[i]},{nums[j]}" if j==i+1 else f"{nums[i]}–{nums[j]}"))
            i=j+1
        return "["+",".join(out)+"]"
    return re.sub(r"\[@([a-z,@\s]+)\]",rep,text)

# ------------------------------------------------------------------ docx helpers
d=Document()
sec=d.sections[0]
sec.left_margin=sec.right_margin=sec.top_margin=sec.bottom_margin=Inches(1)
st=d.styles['Normal']; st.font.name='Times New Roman'; st.font.size=Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
pf=st.paragraph_format; pf.line_spacing_rule=WD_LINE_SPACING.DOUBLE; pf.space_after=Pt(0)
# line numbering (continuous) as PLOS ONE requests
ln=OxmlElement('w:lnNumType'); ln.set(qn('w:countBy'),'1'); ln.set(qn('w:restart'),'continuous'); sec._sectPr.append(ln)
# page numbers
fp=sec.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=fp.add_run()
for t,txt in (('begin',None),('instr',' PAGE '),('end',None)):
    if t=='instr':
        e=OxmlElement('w:instrText'); e.set(qn('xml:space'),'preserve'); e.text=txt
    else:
        e=OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),t)
    r._r.append(e)

def runs(p,text,size=None,bold=False):
    # markup: **bold**, *italic*, _{sub}, ^{sup}
    text=cite_sub(text)
    for tok in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|_\{[^}]*\}|\^\{[^}]*\})",text):
        if not tok: continue
        it=False; b=bold
        if re.fullmatch(r'\*\*[^*]+\*\*',tok): r=p.add_run(tok[2:-2]); b=True
        elif re.fullmatch(r'\*[^*]+\*',tok): r=p.add_run(tok[1:-1]); it=True
        elif re.fullmatch(r'[_^]\{[^}]*\}',tok):
            inner=tok[2:-1]
            if len(inner)>2 and inner.startswith('*') and inner.endswith('*'): inner=inner[1:-1]; it=True
            r=p.add_run(inner)
            if tok[0]=='_': r.font.subscript=True
            else: r.font.superscript=True
        else: r=p.add_run(tok)
        r.bold=b or None
        if it: r.italic=True
        if size: r.font.size=Pt(size)
def P(text,indent=True,align=None):
    p=d.add_paragraph(); 
    if indent: p.paragraph_format.first_line_indent=Inches(0.5)
    if align=='center': p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    runs(p,text); return p
def H1(t): 
    p=d.add_paragraph(); runs(p,t,size=14,bold=True); p.paragraph_format.keep_with_next=True
def H2(t):
    p=d.add_paragraph(); runs(p,t,bold=True); p.paragraph_format.keep_with_next=True
def H3(t):
    p=d.add_paragraph(); r=p.add_run(t); r.italic=True; p.paragraph_format.keep_with_next=True
def B(items,numbered=False):
    for i,t in enumerate(items,1):
        p=d.add_paragraph(); p.paragraph_format.left_indent=Inches(0.5); p.paragraph_format.first_line_indent=Inches(-0.25)
        runs(p,(f"{i}. " if numbered else "• ")+t)
def table(cap,header,rows,widths=None,note=None):
    p=d.add_paragraph(); p.paragraph_format.keep_with_next=True; p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
    r=p.add_run(cap.split('.')[0]+'.'); r.bold=True; runs(p,cap[len(cap.split('.')[0])+1:])
    t=d.add_table(rows=1,cols=len(header)); t.style='Table Grid'
    for i,h in enumerate(header):
        c=t.rows[0].cells[i]; c.text=''; pp=c.paragraphs[0]; pp.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE; runs(pp,h,size=10,bold=True)
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):
            cells[i].text=''; pp=cells[i].paragraphs[0]; pp.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE; runs(pp,str(v),size=10)
    if widths is None: widths=[2.4]+[(6.5-2.4)/(len(header)-1)]*(len(header)-1)
    t.autofit=False
    for row in t.rows:
        for i,w in enumerate(widths): row.cells[i].width=Inches(w)
    if note:
        p=d.add_paragraph(); p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE; runs(p,note,size=10)
    d.add_paragraph().paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE

# ------------------------------------------------------------------ front matter
p=d.add_paragraph(); runs(p,"Does Release Timing in the LLM Software Ecosystem Respond to Accumulating Degradation? An Empirical Study of Open-Source Repositories and Public Chat Logs",size=16,bold=True)
p=d.add_paragraph(); runs(p,"Short title: Release timing and degradation in the LLM software ecosystem")
p=d.add_paragraph(); runs(p,"Ook Lee^{1*}",bold=True)
p=d.add_paragraph(); runs(p,"^{1} Department of Information System, Hanyang University, Seoul, Republic of Korea")
p=d.add_paragraph(); runs(p,"* Corresponding author")
p=d.add_paragraph(); runs(p,"E-mail: ooklee@hanyang.ac.kr")
d.add_page_break()

H1("Abstract")
P("Software built around large language models (LLMs) is widely expected to degrade as the world drifts away from a model's training data, and practitioners are advised to refresh such systems on a schedule that balances the cost of renewal against the cost of degradation. I ask whether the public record of the LLM software ecosystem matches this expectation. I state a small replacement model in which errors accumulate with drift and a refresh resets them at a fixed cost, derive three testable implications, and show by simulation that the model's parameters can be recovered. I then test the implications with weekly bug-report counts and release dates for 19 widely used open-source repositories (4,071 repository-weeks; 1,521 releases) and with 478,498 English conversations from the WildChat corpus. None of the three implications is supported. Once total issue volume is controlled, bug reports do not rise with the time since the last release (pooled slope −0.0005 per week; 95% CI −0.010 to 0.009); the probability of a release does not rise with that time either; and a measure of prompt drift does not predict user corrections once repeated automated templates are removed. An uncorrected drift measure appeared to predict corrections (*p* = 0.009) only because a single template had come to dominate the data. A same-week contrast of model snapshots with different training cutoffs points the other way, but it cannot separate the cutoff from the model generation. The correction tests are weak: a pattern-based detector finds only a small share of corrections, and two labelers disagreed about what counts as one. I list what a valid test of AI-system depreciation would require and release a replication package.",indent=False)
p=d.add_paragraph(); runs(p,"*Keywords:* software maintenance, large language models, concept drift, release engineering, mining software repositories, negative results")

# ------------------------------------------------------------------ Introduction
H1("Introduction")
P("Anyone who has kept a language-model application running in production has been told that it will age. The underlying model is frozen at a training cutoff, users go on asking about events that came afterward, and the share of requests that go badly is expected to creep upward until someone retrains, fine-tunes or swaps the model. The same expectation runs through practitioner advice on monitoring and through the research literature on concept drift [@gama], and it shapes decisions. If degradation accumulates, a team should refresh before it becomes costly, and the right interval depends on how quickly the system degrades and how much a refresh costs.")
P("This paper asks a plain empirical question about that belief. If degradation accumulates and teams respond to it, what should the public record show, and do we see it? Two signatures follow from the replacement logic that maintenance research has long borrowed from reliability engineering [@duncan]. The rate of reported problems should rise with the time since the last refresh, and the chance that a refresh happens in a given week should rise with that same elapsed time, because the longer a system has aged, the more likely it is that renewal is worth its cost. A third signature concerns the cause. Where the drift between users' requests and a model's training window can be measured, more drift should go with worse outcomes.")
P("I test all three. For the first two I use the issue trackers and release histories of 19 open-source projects that sit between users and models, such as inference engines, training libraries and client software development kits (SDKs). For the third I use a public corpus of real conversations with ChatGPT-family models. The paper makes four contributions.")
B(["A small, explicit model of refresh timing that yields testable implications and whose parameters can be recovered in simulation. I use it as a benchmark for what the data would have to look like.",
   "Evidence from 19 repositories and 478,498 conversations that the signatures of accumulating degradation are absent.",
   "A methodological caution. A plausible drift measure produced a statistically significant association with user corrections until I removed repeated automated templates. I show how the contamination arises and how to detect it.",
   "A replication package with the collection, measurement, simulation and analysis code and the weekly aggregates."],numbered=True)
P("I should say at the outset what the study does not show. The data cannot tell us whether commercial operators refresh in response to degradation, and a null result in open-source repositories does not imply that degradation is absent in production. What the study does show is that these public sources are poor instruments for the question, and the Discussion sets out what a valid test would need.")
H3("Research questions")
B(["**RQ1.** Does the weekly rate of bug reports in LLM-ecosystem repositories increase with the time since the last release?",
   "**RQ2.** Does the probability of a release increase with the time since the last release?",
   "**RQ3.** Does measured prompt-distribution drift in a public chat corpus predict higher rates of user corrections?"])

H2("Background and related work")
P("*Release engineering and software quality.* Rapid-release practice has been studied extensively. Khomh and colleagues, for example, compared Firefox versions built on shorter and on traditional release cycles and found that the shorter cycles did not produce significantly more post-release bugs, although crashes appeared earlier in execution and bugs were fixed faster [@khomh]. Two points from this literature matter here. Release cadence is often a fixed organizational choice, and a release is itself an event that can introduce defects. A project that ships on a schedule leaves little room for the timing of a release to respond to the state of the system, a point I return to when interpreting RQ2.")
P("*Machine-learning systems and technical debt.* Studies of industrial practice describe machine-learning work as data-centric and as carrying maintenance burdens that traditional software does not have [@sculley,@amershi]. Software engineers have also begun to study the ecosystems that form around pre-trained models, for example how practitioners decide to reuse models from the Hugging Face registry [@jiang]. The present setting overlaps with this work but isolates one mechanism, the loss of fit between a frozen model and a moving environment.")
P("*Drift and temporal degradation.* The concept-drift literature documents declining predictive performance when the data distribution shifts [@gama]. For language models, performance is worse on text from after the training period [@lazaridou,@luu], and the behavior of hosted GPT-3.5 and GPT-4 services was found to change substantially between March and June 2023 [@chen]. These studies measure how performance changes. They do not study how, or whether, maintainers respond to it.")
P("*Replacement and maintenance optimization.* The operations literature on optimal replacement derives threshold policies in which an asset is renewed once a deterioration index passes a critical level [@duncan]. Rust turned the replacement problem into an econometric one by adding unobserved payoff shocks, so that observed replacement timing could be used to estimate the cost of renewal [@rust]; later work on conditional choice probabilities and on the properties of such estimators supplies the surrounding toolkit [@hotz,@aguirre]. The model below is a deliberately small member of this family. I use it as a source of testable implications and not as an estimator.")

# ------------------------------------------------------------------ Methods
H1("Materials and methods")
H2("A model of refresh timing")
P("Time is discrete and measured in weeks. A maintainer operates one deployed system. Let *x*_{*t*} denote the drift accumulated since the system was last refreshed, where a refresh stands for any renewal action (retraining, fine-tuning or upgrading the underlying model). Each week the drift advances, and the maintainer chooses either to keep the system or to refresh it. Errors arrive as a Poisson process with rate *λ*_{0} + *γx*_{*t*}, where *γ* > 0 is the marginal effect of drift on the error rate. Each error costs the maintainer an amount *c*, and a refresh costs *RC* and resets the drift to zero. Payoffs include an unobserved shock with a Type I extreme-value distribution, so the probability of a refresh in state *x* is logistic in the difference between the value of refreshing and the value of keeping.")
P("The Bellman operator for this problem is a contraction, so the value function exists and is unique. By induction on value iteration, the value of keeping the system is non-increasing in *x*, while the value of refreshing does not depend on *x*; the refresh probability is therefore non-decreasing in drift. I also computed, over a wide range of parameter values, that the optimal drift threshold increases with the refresh cost and with the speed of drift and decreases with the discount factor (S1 Appendix). These comparative statics are numerical regularities and not proved results.")
P("Three implications can be tested with public data. **H1 (error signature):** the expected error count increases with the time since the last refresh, that is, *γ* > 0. **H2 (timing signature):** the refresh hazard is non-decreasing in the time since the last refresh. **H3 (drift signature):** where drift can be measured directly, higher drift predicts a higher error rate. RQ1 to RQ3 test H1 to H3, respectively.")
P("I do not estimate the cost of a refresh from the repository data, for three reasons. First, *RC* is identified only through the response of refresh timing to the state of the system. That response has two parts: errors must rise with the time since the last refresh (H1), and refreshes must become more likely as that time grows (H2). If either fails, as it does in these data (see Results), no cost of refreshing can rationalize the observed timing, and a number returned by the estimator would reflect the functional form and not the behavior of maintainers. Second, even in the idealized benchmark described below the estimator is imprecise for panels of the length available here. Third, a release is only a proxy for a refresh in these repositories, so an estimate would describe the cost of releasing and not of retraining. The model therefore serves to derive H1 to H3 and to size the tests. The estimation code is included in the replication package for readers who have data in which refresh dates are known.")
H2("Simulation benchmark")
P("To check that the tests would detect the signatures if they were present, I simulated the model with *γ* = 0.5, *RC* = 40, *λ*_{0} = 5, Poisson(1) drift increments and a discount factor of 0.95. The optimal policy refreshes at a drift of 14, where the expected error rate is 12.0, or 2.4 times the baseline. I ran 100 replications of 3,000 weeks and estimated *γ* and *RC* with a two-step estimator and, separately, jointly from choice data alone. To see how precision depends on sample length, I repeated the joint estimation with 100, 250, 500 and 1,000 weeks.")

H2("Repository data (RQ1 and RQ2)")
P("*Selection.* I looked for open-source projects in the LLM ecosystem whose releases are made by people and are neither absent nor automated. The selection had three steps, and all three are reported. First, I tried six prominent candidates. Qwen2.5 (no GitHub releases in 140 weeks) and DeepSeek-V3 (one release in 94 weeks) publish model weights elsewhere, and llama.cpp publishes automated builds (185 releases in 188 weeks) that carry no timing decision. vLLM, Hugging Face Transformers and Ollama were retained. Second, so as not to rely on three projects, I fixed a list of 17 further repositories before collecting any data on them: inference and training frameworks, client SDKs, agent frameworks and evaluation tools in the LLM ecosystem, chosen from general knowledge of the field without looking at their issue or release histories. Third, I applied an eligibility rule that was also fixed in advance, namely at least 10 releases and at least 80 weeks of data. One of the 20 collected repositories (mlc-llm, with no releases) was ineligible, which leaves 19 (Table 1). This is a convenience sample of prominent projects and not a random sample of the ecosystem, and nearly all of the projects are software and tooling rather than model-retraining pipelines. In what follows, a release is therefore a proxy for a refresh.")
P("*Collection.* Using the GitHub REST API I collected every issue created since 1 January 2023 (excluding pull requests) and every non-draft, non-prerelease release. Issues were aggregated by ISO week. A bug report is an issue with a label containing “bug” or a title matching a fixed keyword list (bug, error, crash, fail, wrong, incorrect, regression, broken, exception). The age of a repository-week is the number of weeks since the last release.")
repo_rows=[
("anthropics/anthropic-sdk-python",194,123,"1","−0.016 (0.079)","−0.229 (0.093)"),
("Dao-AILab/flash-attention",203,49,"2","−0.007 (0.016)","−0.294 (0.063)"),
("EleutherAI/lm-evaluation-harness",268,19,"10","0.002 (0.019)","0.117 (0.160)"),
("ggml-org/whisper.cpp",200,33,"4","0.013 (0.016)","−0.105 (0.069)"),
("huggingface/transformers",414,186,"2","−0.016 (0.033)","−0.066 (0.063)"),
("huggingface/accelerate",293,60,"4","−0.033 (0.031)","0.045 (0.077)"),
("huggingface/diffusers",222,61,"2.5","−0.001 (0.014)","−0.024 (0.057)"),
("huggingface/peft",194,30,"7","0.004 (0.017)","0.115 (0.073)"),
("huggingface/text-generation-inference",167,58,"2","−0.049 (0.036)","−0.153 (0.094)"),
("huggingface/trl",197,79,"2","−0.043 (0.037)","0.038 (0.130)"),
("lm-sys/FastChat",185,14,"3","0.003 (0.046)","−0.403 (1.014)"),
("microsoft/autogen",187,59,"1","−0.040 (0.037)","−0.482 (0.168)"),
("microsoft/semantic-kernel",189,121,"1","0.003 (0.150)","−0.522 (0.111)"),
("NVIDIA/TensorRT-LLM",157,23,"6","0.018 (0.016)","0.172 (0.144)"),
("ollama/ollama",173,146,"1","0.076 (0.034)","0.116 (0.541)"),
("openai/openai-python",299,181,"1","−0.027 (0.043)","−0.343 (0.049)"),
("run-llama/llama_index",198,153,"1","−0.031 (0.032)","−0.564 (0.098)"),
("sgl-project/sglang",145,50,"2","0.002 (0.013)","0.172 (0.089)"),
("vllm-project/vllm",186,76,"2","−0.004 (0.012)","0.122 (0.268)")]
table("Table 1. Eligible repositories and repository-level slopes. The 19 repositories contribute 4,071 repository-weeks and 1,521 releases. Slopes are described under Statistical analysis.",
      ["Repository","Weeks","Releases","Median cycle (weeks)","Bug log-rate slope (SE)","Release-hazard logit slope (SE)"],repo_rows)

H2("Chat corpus (RQ3)")
P("I used WildChat-1M [@zhao], a public corpus of conversations with OpenAI chat models collected between April 2023 and April 2024. I kept the English conversations (478,498 across 57 ISO weeks). The corpus contains six model snapshots: gpt-3.5-turbo-0301, -0613 and -0125, gpt-4-0314, gpt-4-1106-preview and gpt-4-0125-preview. For the main drift tests I used the conversations with models whose training cutoff is reported as about September 2021, namely the three gpt-3.5-turbo snapshots and gpt-4-0314 (381,201 conversations, of which 121,648 have at least two user turns). Only aggregate counts and binary features were stored, and no conversation text was kept.")
P("*Outcomes.* The main outcome is a user correction, defined as a later user turn whose opening words match a fixed pattern of correction or negative feedback (for example “no”, “that's wrong”, “that doesn't work”, “try again”, “you misunderstood”). Among multi-turn conversations, 3.2% contain at least one such turn, and 1.25% of later user turns are corrections. A second detector (v2) adds cues anywhere in the first 200 characters, such as “I meant”, pasted error output and “still not working”. The validation described below shows that the recall of both detectors is low. As an outcome that does not rely on pattern matching, I also counted re-asks, meaning consecutive user turns whose word sets overlap (Jaccard similarity of at least 0.6, with at least four words each).")
P("*Drift.* I used two measures. The weekly measure is the Jensen–Shannon divergence between the distribution of first-prompt words in a given week and in a reference window (the first four eligible weeks), computed over the 5,000 most frequent reference words. The conversation-level measure flags prompts that mention a year after the cutoff (2022 to 2024) or a product launched after it.")

H2("Statistical analysis")
P("*RQ1 and RQ2.* For RQ1 I fitted Poisson regressions of weekly bug counts on the weeks since release, with an offset equal to the log of total weekly issues and a linear time trend. For RQ2 I fitted logistic regressions of a release in a given week on the weeks since release, with age capped at eight weeks. Repository-level standard errors come from a cluster bootstrap that resamples whole release cycles while keeping each observation's calendar time, and the repository-level slopes were pooled with a random-effects model [@dl]. I report 95% intervals for the pooled estimates, together with robustness checks that drop the repositories with a median cycle of one week, condition on surviving the first week after a release (RQ2), and drop the issue-volume offset (RQ1).")
P("*RQ3, weekly and conversation level.* I regressed the weekly correction rate on the drift measure by weighted least squares with autocorrelation-robust standard errors, first with a time trend and then with controls for task mix (code share, log prompt length, mean number of turns and the share of jailbreak-style prompts). The weekly analyses use weeks with at least 500 conversations from the model family and at least 20,000 conversations in total. At the conversation level I fitted logistic regressions of any correction on the drift flags, with week fixed effects and standard errors clustered by week. Repeated automated templates were handled by keeping at most five conversations per week with the same first 80 characters.")
P("*RQ3, snapshot contrast.* A weekly drift series trends with calendar time, so the two cannot be separated. WildChat, however, served models with different training cutoffs in the same weeks, which allows a contrast that holds the week fixed. I used the 38 weeks in which both a GPT-3.5 and a GPT-4 snapshot were served (100,362 multi-turn conversations after template de-duplication). I took the cutoffs reported by the provider: September 2021 for all GPT-3.5 snapshots and for gpt-4-0314, April 2023 for gpt-4-1106-preview and December 2023 for gpt-4-0125-preview. In the first period (April to June 2023) both families share one cutoff, so it serves as the baseline. I estimated linear probability models of any correction on indicators for the three GPT-4 snapshots, with week fixed effects, controls for code content, first-prompt length and number of turns, and standard errors clustered by week. The contrast of interest is the difference between each later GPT-4 snapshot and gpt-4-0314, relative to GPT-3.5 in the same week; H3 predicts a negative sign, because a fresher cutoff should mean fewer corrections. As a placebo I compared GPT-3.5 snapshots, which share one cutoff, with each other.")

H2("Validation of the correction detector")
P("I validated the detectors in three stages. In the first stage I drew a stratified random sample of 400 later user turns from four WildChat shards: 150 flagged by the first detector (stratum A; 1,164 such turns in the sampled shards), 150 unflagged turns containing a weak cue such as “error”, “wrong”, “I meant”, “doesn't” or “again” (B; 5,419), and 100 unflagged turns without a cue (C; 98,958). The sample was shuffled and shown without its stratum, together with the end of the preceding assistant message. A turn was labeled positive if it reported that the assistant's previous output was wrong, had failed or was not what the user wanted (an explicit rejection, an “I meant” clarification, a factual correction, an error message from running the output, or a complaint). It was labeled negative if it was a new request, a refinement, a continuation, or an answer to a question the assistant had asked, and unclear cases were marked ambiguous. These labels were produced by a single AI annotator (Claude) using a codebook fixed beforehand, not by humans.")
P("Because the first detector (v1) turned out to have low recall, I built a second one (v2) from the codebook categories and evaluated both on a fresh sample that had not been used in its design: 350 turns from four other shards (150 flagged by v2, 100 unflagged with a weak cue and 100 unflagged without one; stratum sizes 5,513, 5,193 and 116,835), labeled by the same procedure. In the third stage I labeled a random subsample of 100 of these 350 turns myself, using the same codebook and without access to the AI labels or the detector flags.")
P("Precision is the positive rate among flagged turns. Recall is the share of all estimated positives in the population that lie in the flagged stratum, with strata weighted by their population sizes. Intervals are bootstrap percentile intervals, and ambiguous cases are counted as half-positive; the extreme treatments are given in the text. Agreement between labelers is summarized with Cohen's kappa [@cohen] and read with the conventional benchmarks [@landis].")

H2("Data and code availability, and use of AI tools")
P("The study uses public repository metadata and the public WildChat corpus, which is distributed with hashed identifiers. Only aggregate counts and binary features were stored, and no conversation text is kept or published. All data and code needed to reproduce the results are provided in the replication package (S2 File), which is deposited at [repository DOI to be inserted].")
P("An AI assistant (Claude, Anthropic) was used to write and run analysis code, to draft and edit parts of the text, and as one of the two labelers in the validation of the detector described above; its labels were compared with mine, and the differences are reported in the Results. I reviewed all outputs and take responsibility for the content.")

# ------------------------------------------------------------------ Results
H1("Results")
H2("Simulation benchmark")
P("In the benchmark, the two-step estimator recovered *γ* (mean 0.499, SD 0.011) and *RC* (mean 39.9, SD 1.0) from 3,000 weeks of data, and estimating *γ* and *RC* jointly from choice data alone gave an *RC* with mean 40.1 and SD 3.0. Precision falls with sample length. The SD of the estimated *RC* is 6.7 at 100 weeks, 4.8 at 250 weeks, 2.8 at 500 weeks and 2.1 at 1,000 weeks. The repositories studied here have between 145 and 414 weekly observations, so a cost estimate would be imprecise even under ideal conditions. The tests below can therefore detect the signatures if they are present, but a cost estimate from these data would not be informative.")

H2("RQ1: bug reports do not increase with the age of a release")
P("Pooling the 19 repository-level slopes with a random-effects model, the log-rate slope of bug reports on weeks since release is −0.0005 per week (95% CI −0.010 to 0.009), with no detectable heterogeneity across repositories (*τ*^{2} = 0). The estimate is precise enough to rule out, for instance, a 1% weekly increase in the bug rate. Eight of the 19 repository-level slopes are positive and 11 are negative (Table 1). This is not what H1 predicts.")
P("Raw bug counts do fall with age. Without the offset for total issue volume the pooled slope is −0.023 (95% CI −0.047 to 0.001), and in an early look at the Transformers repository, bug counts fell from 8.9 per week in the first week after a release to 2.2 after five weeks. Once the total number of issues filed is accounted for, however, the decline disappears. The early surge therefore appears to be a general burst of issue-filing right after a release, driven by attention, announcements and defects together, and not a change in the share of reports that concern bugs. Issue counts alone cannot separate these explanations.")

H2("RQ2: release probability does not rise with age")
P("The pooled release-hazard logit slope is −0.125 per week of age (95% CI −0.228 to −0.022; *τ*^{2} = 0.036), so a release is less likely, not more likely, in a given week when more weeks have passed since the last one. Eight of the 19 repository-level slopes are positive. The negative pooled estimate comes mostly from repositories that release weekly and publish hot-fixes soon after a release. Excluding the six repositories with a median cycle of one week gives −0.016 (95% CI −0.101 to 0.069), and conditioning on surviving the first week (ages of two weeks or more) gives −0.059 (95% CI −0.146 to 0.029). I therefore find no support for a hazard that rises with age, which H2 requires. The evidence fits releasing that follows a schedule or reacts to hot-fixes, and cadence-driven releasing leaves little scope for timing to respond to the state of the system.")

H2("RQ3: drift does not predict corrections once templates are removed")
P("*The raw drift measure.* With the raw measure, the weekly correction rate for the gpt-3.5 family is positively associated with drift once a time trend is included (slope 0.032, SE 0.012, *p* = 0.009; 51 weeks). The association weakens when task-mix controls are added (0.021, *p* = 0.19), and drift is nearly collinear with time (correlation 0.93). Inspecting the underlying features shows why. The share of weekly conversations mentioning a product from a short list of post-cutoff image and language tools rose from under 1% to 81% over the sample, because a single automated prompt template, a prompt-generation script, came to dominate the traffic. The drift measure was tracking the arrival of that template.")
P("*After removing repeated templates.* When at most five conversations per week with the same first 80 characters are kept, weekly drift ranges from 0.044 to 0.158 and its correlation with time falls to 0.60. The estimated slopes are 0.018 (*p* = 0.25) without further controls, 0.019 (*p* = 0.35) with a time trend and 0.029 (*p* = 0.32) with task-mix controls, and none is distinguishable from zero. At the conversation level, with week fixed effects, mentioning a post-cutoff year is not associated with a correction in the gpt-3.5 family (odds ratio 0.92, 95% CI 0.77 to 1.09; *n* = 110,319) or for gpt-4-0314 (1.51, 0.86 to 2.63; *n* = 11,329). The product-mention flag gives 1.45 (0.80 to 2.63) and 1.29 (0.59 to 2.80), with intervals that include one. The weekly analysis for gpt-4-0314 rests on only eight weeks that meet the size threshold and is not informative. I find no support for H3.")
P("*A second detector and a pattern-free outcome.* Replacing the outcome with the higher-recall v2 detector leaves the gpt-3.5 conclusions unchanged. The weekly drift slopes are 0.015 (*p* = 0.51), 0.021 (*p* = 0.47) and −0.023 (*p* = 0.78) across the three specifications, and the conversation-level odds ratio for a post-cutoff year is 0.93 (95% CI 0.80 to 1.08; *n* = 110,319). For gpt-4-0314, v2 gives an odds ratio of 0.57 (0.44 to 0.73), an unexpected negative association that appears neither with v1 nor in the gpt-3.5 models. Because v2 flags pasted error output, this may reflect differences in task mix, such as the share of code-related turns, and not correction behavior, and I do not interpret it. Using re-asks as an outcome, 22% of multi-turn conversations contain one. I have not validated this proxy, and I expect it to be contaminated by batch workflows in which users submit the same instruction repeatedly with different content. The weekly gpt-3.5 slopes are 0.004 (*p* = 0.97), 0.043 (*p* = 0.63) and 0.367 (*p* = 0.24) across the three specifications, and the conversation-level odds ratio for a post-cutoff year is 0.87 (95% CI 0.79 to 0.97), so conversations that mention later years contain somewhat fewer re-asks, the opposite of H3. The weekly gpt-4 regressions, with eight observations and up to five regressors, are not interpretable.")
P("*What the design could detect.* With standard errors of 0.020 (v1) and 0.028 (v2) in the specification with a time trend, a weekly slope would have to exceed about 0.057 (v1) or 0.079 (v2) to be detected with 80% power at the 5% level. Across the observed range of the drift measure, these thresholds correspond to increases of about 52% (v1) and 23% (v2) in the observed correction rate. The study can therefore exclude large effects only, and only for the share of corrections that the detectors capture.")

H2("RQ3: contrast between model snapshots")
P("Within the same week, a GPT-4 snapshot with a later training cutoff did not show fewer corrections than GPT-3.5, as H3 would predict. The raw v1 correction rates were 3.8% for gpt-3.5-turbo-0301, 2.5% for -0613 and 3.7% for -0125, and 2.5% for gpt-4-0314, 3.6% for gpt-4-1106-preview and 3.7% for gpt-4-0125-preview. Relative to GPT-3.5 in the same week, gpt-4-1106-preview (cutoff 19 months later than that of GPT-3.5) had a higher correction rate than gpt-4-0314 did, by 1.31 percentage points with the v1 detector (SE 0.30, *p* < 0.001), and gpt-4-0125-preview (27 months later) differed from gpt-4-0314 by 0.65 points (SE 0.39, *p* = 0.095; Table 2). The estimated change per month of cutoff advantage is +0.043 points (95% CI 0.016 to 0.070). With the v2 detector the corresponding differences are +1.24 points (SE 0.56, *p* = 0.028) and +0.54 points (SE 0.80, *p* = 0.50), and +0.039 points per month (95% CI −0.010 to 0.089). For both detectors the sign is opposite to H3, so the contrast does not support the hypothesis.")
table("Table 2. Same-week contrast of model snapshots and same-cutoff placebo. Entries are differences in the probability of any correction, in percentage points, from linear probability models with week fixed effects and standard errors clustered by week. Contrast rows give the difference between the GPT-4 snapshot and gpt-4-0314, each relative to GPT-3.5 in the same week. H3 predicts a negative sign.",
  ["Contrast","Cutoff difference (months)","v1: estimate (SE), *p*","v2: estimate (SE), *p*"],
  [("gpt-4-1106-preview minus gpt-4-0314","19","+1.31 (0.30), <0.001","+1.24 (0.56), 0.028"),
   ("gpt-4-0125-preview minus gpt-4-0314","27","+0.65 (0.39), 0.095","+0.54 (0.80), 0.498"),
   ("Per month of cutoff advantage","–","+0.043 [0.016, 0.070], 0.002","+0.039 [−0.010, 0.089], 0.121"),
   ("Placebo: gpt-3.5-turbo-0613 minus -0301","0","−0.36 [−0.77, 0.05], 0.088","−0.77 [−1.42, −0.11], 0.021"),
   ("Placebo: gpt-3.5-turbo-0125 minus -0301","0","−0.20 [−0.75, 0.35], 0.478","−1.00 [−2.06, 0.06], 0.063")],
  note="Placebo rows are not adjusted for week effects, because the GPT-3.5 snapshots were served together in only two weeks; they are therefore confounded with calendar time. Brackets give 95% confidence intervals.")
P("The comparison does not, however, amount to evidence of an opposite effect. GPT-3.5 snapshots share a single cutoff, yet their correction rates differ (Table 2). For v1 the differences are small and mostly not significant, but for v2 they are −0.77 and −1.00 points, of about the same size as the snapshot contrast. Differences of this size therefore arise between snapshots without any change of cutoff. In addition, the contrast removes the problem of calendar time but not that of model generation: gpt-4-0314, gpt-4-1106-preview and gpt-4-0125-preview differ in capability and response style as well as in cutoff, and gpt-4-0314 had an unusually low correction rate. With only three GPT-4 snapshots and three periods, a cutoff effect cannot be separated from a generation effect. I conclude that the snapshot design finds no sign of the effect that H3 predicts, and that it cannot rule out small effects of either sign.")

H2("Validation of the correction detector")
P("*First sample (AI labels).* Of the 150 flagged turns, 119 were labeled positive and 5 ambiguous, which gives a precision of 0.81 (90% interval 0.76 to 0.86; 0.79 to 0.83 under the two extreme treatments of ambiguous cases). Recall is low. Of the 150 unflagged turns with a weak cue, 44 were positive, as were 3 of the 100 unflagged turns without a cue, so the detector captures an estimated 14% of corrections (90% interval 10% to 25%; 13% to 17% across treatments), for an F1 of about 0.24. Roughly a quarter of the corrections fall in the weak-cue stratum and 60% in the no-cue stratum. The most common misses are error messages and stack traces pasted back after running generated code, statements of the form “I meant …”, and corrections that do not begin with a negation.")
P("*Second detector (fresh sample, AI labels).* On the fresh sample, v1 had a precision of 0.80 (90% interval 0.71 to 0.89) and a recall of 0.09 (0.06 to 0.14), consistent with the first sample. The v2 detector had a precision of 0.73 (0.68 to 0.79) and a recall of 0.27 (0.20 to 0.39), for an F1 of 0.39 (0.31 to 0.51) against 0.17 (0.12 to 0.24) for v1. The recall of v2 ranges from 0.24 to 0.30 across the ambiguity treatments. About 65% of the estimated corrections are in the no-cue stratum, which a pattern-based detector cannot reach.")
P("*Human labels.* On the 100-turn subsample I marked 55 turns as corrections, 34 as non-corrections and 11 as unclear; the AI annotator marked 41, 53 and 6 on the same turns. On the 83 turns that both of us considered clear, agreement was 65% and Cohen's kappa was 0.34, which is conventionally read as fair. The disagreement is one-sided. Of the 29 discordant turns, 24 were corrections for me and not for the AI annotator, and 5 the other way. The 24 are mostly requests to rewrite, revise or redo an earlier output, resubmissions of a task template, and follow-up questions that challenge an earlier answer. I appear to have applied a broader criterion, any turn asking for a different output, than the codebook, which treated refinements as non-corrections. The differences were not adjudicated.")
P("Because my labels are more inclusive, they imply lower recall. Weighting the subsample back to the population, v1 has a precision of 0.90 (90% interval 0.77 to 1.00) and a recall of 0.05 (0.03 to 0.09), and v2 has a precision of 0.79 (0.69 to 0.89) and a recall of 0.12 (0.08 to 0.18), again counting ambiguous cases as half-positive. These intervals are wide because the subsample is small. Across labelers and detectors, recall falls between about 5% and 30%, which I regard as low under any reasonable criterion, while the precision of flagged turns is acceptable. That two labelers working from the same codebook disagreed this much shows that a “user correction” is not a self-evident construct.")
P("*Implications for RQ3.* If the misses of the detectors were unrelated to drift, the correction rate analyzed here would be a noisy and attenuated measure of the true rate. This would bias a drift coefficient toward zero and widen its interval, so the null result for H3 is weaker evidence than it would be with an accurate outcome. The misses may also be related to task mix, since code-related turns are the main source of missed positives, in which case the bias could go either way.")

# ------------------------------------------------------------------ Discussion
H1("Discussion")
P("None of the three signatures of accumulating degradation appears in these data, and I am careful not to read this as evidence that LLM-based systems do not degrade. The repositories examined are developer tools whose releases follow engineering cadence, feature work and defect fixes, so their release timing is not the decision that the model describes. The chat corpus records users of a hosted service, and it is the operator, not the users, who decides when the underlying model changes. What the results do show is that open-source release data and public chat logs are poor instruments for studying maintenance timing under drift, and that apparent effects in such data can be artifacts.")
P("The data available fall short of four requirements, and together these describe what a future study needs. First, the state variable must be measured directly and must vary independently of calendar time, because with a single trending series drift and time cannot be separated. The snapshot contrast meets this requirement only in part: it breaks the link between drift and calendar time, but at the price of confounding drift with model generation. A study that could hold the model fixed and vary only the training cutoff, for example with fine-tuned variants of one base model, would avoid this. Second, the outcome must measure model errors and not user attention or traffic mix; bug counts and pattern-based correction detectors both fail here. Third, the refresh decision must be made by an identifiable maintainer who faces the cost of acting, and the dates of refreshes must be known and not inferred from release tags. Fourth, the panel must be long enough to estimate a cost, and the simulation suggests that fewer than about 250 weekly observations per unit leave the cost imprecise.")
P("The most transferable finding may be a methodological one. A reasonable-looking drift measure and a conventional regression produced a significant result that vanished when a single automated template was removed. Anyone computing distributional drift on public chat logs should check for repeated templates, report how much of the measured drift is attributable to the most frequent prompts, and test whether the results survive de-duplication.")
P("The results offer limited practical guidance, and I would not read them as advice to stop refreshing. They suggest that a team should be wary of importing scheduling rules from monitoring dashboards without evidence from its own error data, since in the public data the time since the last release is not a useful predictor of problems. They also point to a cost that standard replacement models leave out. The burst of issue-filing after a release suggests that a refresh comes with its own regression and support burden, which a team should count when it decides how often to refresh.")
H2("Limitations")
P("*Construct validity.* Bug reports measure what users choose to report, which depends on popularity and on attention around a release, and the offset and trend controls address this only in part. The bug definition combines labels and keywords and may misclassify issues; I did not validate a sample of bug labels, and doing so is the first extension I would make. The correction measure is a pattern on the opening words of a user turn. The validation found a precision of about 0.8 and a recall between 0.05 and 0.3 depending on the detector and the labeler, and the human validation rests on one labeler and 100 turns. Agreement between the human and AI labelers was only fair (kappa 0.34), and v2 was designed after the AI annotator had seen examples from the first sample, although it was evaluated on a fresh one. The weekly drift measure captures change in the word distribution and is affected by task mix and by automated traffic. De-duplication handles the dominant template found, but not necessarily every one.")
P("*Internal validity.* Because drift, calendar time and model-version changes move together, associations are hard to attribute; I report the collinearity and show results with and without a trend. The cutoff dates are those reported by the provider and are approximate. The snapshot contrast rests on three GPT-4 snapshots and one baseline period, so the per-month estimate relies on three points, and the placebo shows that differences of about one percentage point arise between snapshots with the same cutoff.")
P("*External validity.* Twenty repositories chosen under explicit criteria are not a sample of the ecosystem, and they are software and tooling and not model-retraining pipelines. One chat corpus from a single service and period is not a sample of deployments either. The results should not be generalized to commercial operators or to other model families.")
P("*Conclusion validity and reproducibility.* Several tests have wide intervals, and the absence of a significant result is not evidence of absence. I therefore say that the evidence does not support the hypotheses, give interval estimates, and avoid claiming that the effects are zero. Collection depends on the state of the GitHub API at the time of collection, since issues can be edited or deleted afterward, and for this reason the replication package includes the weekly aggregates used.")

H1("Conclusions")
P("I asked whether the public record of the LLM software ecosystem shows the signatures of a system that degrades as drift accumulates and is refreshed in response. In 19 repositories and nearly half a million public conversations it does not. Bug reports do not increase with the age of a release once total issue volume is controlled, release probability does not rise with age, and a de-duplicated measure of drift does not predict user corrections. A contrast between model snapshots points the other way, but it cannot be separated from differences between model generations. The more useful results may be the list of requirements for a valid test and the demonstration that a single automated template can manufacture a drift effect. I hope that the replication package helps others who have better-instrumented data, such as operators' own error logs and refresh histories, to run the test that these public sources cannot support.")

H1("Supporting information")
p=d.add_paragraph(); runs(p,"**S1 Appendix. Numerical comparative statics.** Optimal drift threshold for the simulated model as a function of the refresh cost, the speed of drift and the discount factor.")
p=d.add_paragraph(); runs(p,"**S2 File. Replication package.** Collection, measurement, simulation and analysis code; weekly aggregates for the 19 repositories; per-conversation binary features; labeling codebook and labels without conversation text.")

H1("Acknowledgments")
P("[Add acknowledgments, or delete this section.]",indent=False)

H1("References")
# resolve citations first so numbering is final
refs_start=len(d.paragraphs)
for i,k in enumerate(order,1):
    p=d.add_paragraph(); p.paragraph_format.left_indent=Inches(0.4); p.paragraph_format.first_line_indent=Inches(-0.4)
    p.add_run(f"{i}. {REFS[k]}")
missing=[k for k in REFS if k not in order]
print("uncited references:",missing)

# ------------------------------------------------------------------ S1 appendix
d.add_page_break()
H1("S1 Appendix. Numerical comparative statics")
P("Optimal drift threshold (number of drift units at which the policy refreshes), computed by value iteration in the simulated model (*γ* = 0.5, *λ*_{0} = 5; other parameters as in the benchmark unless varied). These are numerical regularities, not proved results.",indent=False)
table("Table A. Refresh cost",["Refresh cost *RC*","10","20","40","80","160"],[("Optimal drift threshold","7","10","14","21","32")])
table("Table B. Drift speed",["Drift speed *μ*","0.5","1.0","1.5","2.0"],[("Optimal drift threshold","11","14","17","19")])
table("Table C. Discount factor",["Discount factor *β*","0.90","0.95","0.99"],[("Optimal drift threshold","16","14","13")])
d.save('/home/user/fluffy-meme/submission_plos/PLOS_ONE_Manuscript.docx')
print("refs:",len(order))
