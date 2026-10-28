---
title: "Acquired, Not Yet Assimilated? Complementary Assets and the Limits of Occupation-Level Evidence on Generative Visual AI"
---

## Abstract

Statistics showing that firms have adopted generative visual AI are often read as evidence that creative work is being displaced. We argue that this reading is premature. Extending information systems research on assimilation, we develop a task-level model in which a firm hands a visual task to a generator only when the share of acceptable output exceeds a threshold set by generation, review, and human production costs. Complementary assets such as expertise, review routines, and compliance procedures enter through review cost alone. Because a generator costs almost nothing to acquire, acquisition can climb without the investment that assimilation requires, and the gap between the two widens. Eurostat data show that 9.6 percent of EU firms use AI that generates pictures, video, or audio, and that firms that considered but did not adopt AI cite missing expertise (70 percent) and legal uncertainty (54 percent) far more often than lack of usefulness (18 percent). European and Canadian job-advert data show no detectable labor-market response, yet we show that these designs could not detect even complete assimilation at the substitution rates observed on freelance platforms. A null result is therefore uninformative. We derive a detectability bound that can accompany any exposure estimate and specify the firm-level data needed to separate the competing accounts.

**Keywords:** generative AI; assimilation gap; complementary assets; review costs; post-adoption; online job adverts; minimum detectable effect; creative work

## 1 Introduction

Tools that turn text into images (widely available since 2022) and into video (since 2024) have made a first draft of visual content almost free. Official statistics already record their spread. In 2025, roughly one in ten European enterprises with ten or more employees reported using AI that generates pictures, video, or audio, and more than one in three did so in publishing, film, and broadcasting (Eurostat, 2026). The natural reading is that the people who used to produce such content are being redeployed, and a growing body of exposure-based labor-market research looks for that redeployment in hiring data.

Information systems (IS) research gives reason for caution. Implementation research has long treated adoption as one stage in a sequence that runs through adaptation, acceptance, routinization, and infusion (Cooper & Zmud, 1990; Jasperson et al., 2005). Organizations can acquire an innovation well before they deploy it, so diffusion statistics overstate use. Fichman and Kemerer (1999) called this wedge an assimilation gap and found it widest where knowledge barriers were high. Studies of enterprise systems later showed that what follows acquisition depends on organizational conditions, such as the participation of top management, rather than on the technology alone (Liang et al., 2007). The IT business value literature makes a parallel point: returns depend on complementary organizational investments (Aral & Weill, 2007; Brynjolfsson & Hitt, 2000; Melville et al., 2004). Macroeconomics points the same way. General-purpose technologies take effect only after complementary investments, labor markets adjust through attrition and reallocation rather than immediate job loss, and technology often accelerates structural change that was already under way (Acemoglu & Restrepo, 2018; Brynjolfsson et al., 2021; David, 1990). For generative visual AI, then, the question is not only whether it substitutes for creative labor. It is also whether reported use reflects assimilation into tasks at all, and whether the evidence researchers currently rely on could tell the difference.

We take up this question in three steps. First, we develop a task-level theory in which a firm reassigns a visual task to a generator only when the acceptance rate of its output exceeds a threshold set by generation cost, review cost, and the cost of human production. Complementary assets enter through review cost: the expertise to specify and check output, the capacity to run review as a routine, and the procedures that keep copyright and personal-data exposure manageable. We embed review in a task-based model of labor demand that separates displacement, reinstatement, and scale effects (Acemoglu & Restrepo, 2018, 2019), treat review as a bottleneck task (Baumol, 1967), and let employers adjust through attrition. The theory implies that when review cost alone exceeds the cost of human production, no improvement in the model can trigger assimilation, and that because acquiring a generator costs almost nothing, acquisition can grow without the complements that assimilation requires. Second, we ask what aggregate public data can reveal about this gap. We derive a detectability bound that compares the hiring response implied by complete assimilation with the minimum detectable effect of standard exposure designs. Third, we assemble the descriptive evidence that exists on the acquisition margin and on the barriers that firms report.

The results are partly substantive and partly cautionary. Acquisition of generative visual AI is substantial and rising, so the absence of a hiring response cannot be explained by an absence of acquisition. Firms that considered AI and did not adopt it cite missing expertise, legal uncertainty, and data-protection concerns far more often than a tool that is not useful, which is what a complementary-asset account predicts and a capability-failure account does not. The hiring data, however, cannot currently distinguish an assimilation gap from complete assimilation. At observed acquisition rates and at the substitution effects estimated on freelance platforms (Demirci et al., 2025), complete assimilation would reduce adverts in the most exposed occupation by roughly 2 to 17 percent, while the European design cannot detect a reduction smaller than about 24 percent. The exposure gradients the designs do report are small and imprecise, about 1 to 2 percent fewer adverts per standard deviation of exposure in 2023 and 2024, and the European gradient was already moving in the same direction before generative tools were released.

We are explicit about what the paper does not claim. We do not observe assimilation inside firms, and we do not treat small or fragile hiring responses as evidence of a gap. Our point is that such responses could not, at present, have revealed either a gap or its absence. Four accounts remain in contention: a capability failure, in which the tool does not meet task requirements; complete assimilation with net substitution; assimilation in which scale effects offset substitution; and an assimilation gap held open by missing complements. The barrier evidence weighs against the first at the acquisition margin. Separating the other three requires firm-level data that link use, complementary assets, task reassignment, and hiring, and we specify what such data would have to show.

The paper contributes to IS research in three ways.

*First, a theoretical contribution.* We extend assimilation theory to generative AI by locating complementary assets in a single, observable cost term, review cost, and by showing why the near-zero acquisition cost of generative tools should widen the gap between acquisition and assimilation. The enterprise systems on which assimilation theory was built were costly to acquire, which meant that acquisition itself partly selected firms that had already built complements. A visual generator can be acquired with almost no complementary investment. Better models raise the acceptance rate of output, but they cannot supply the expertise, review capacity, or compliance procedures needed to cross the acceptance threshold. Reported use is therefore a weaker signal of task reassignment for generative tools than it was for earlier information technologies. Platform studies observe substitution because the buyer of a freelance task can switch tools without first building a review routine; standing occupations inside firms face that friction.

*Second, a methodological contribution.* We provide a detectability bound that changes how the large and growing literature on AI exposure and hiring should be read. At current acquisition rates and at the substitution effects estimated on platforms, where assimilation is comparatively frictionless, complete assimilation of visual tasks would lower adverts in the most exposed occupations by roughly 2 to 17 percent. Standard European and Canadian occupation-level designs cannot detect effects of that size. The small gradients they do report are no larger than the pre-2022 trend and are therefore uninformative about assimilation. The bound is simple enough to be reported next to any exposure coefficient, and doing so guards against both false alarms and false reassurance.

*Third, a research-design contribution.* We turn the assimilation-gap hypothesis into a set of falsifiable predictions that can be tested once firm-level data link reported use, the stock of complementary assets, task reassignment, and hiring. Among acquiring firms, reassignment should rise with expertise, review capacity, and compliance procedures, and hiring for visual occupations should fall only among firms that have both acquired the tool and built those assets. These predictions separate an assimilation gap from capability failure, from complete assimilation with net substitution, and from assimilation with offsetting scale effects, accounts that occupation-level data cannot currently tell apart.

The paper proceeds as follows. Section 2 reviews the literature. Section 3 develops the theory, Section 4 derives the detectability bound, and Section 5 describes the data. Sections 6 to 8 present the evidence on acquisition and barriers, apply the bound to hiring data, and ask when occupation-level data could become informative. Section 9 sets out a firm-level design, and Sections 10 and 11 discuss implications and conclude.

## 2 Related Literature

### 2.1 From Adoption to Assimilation

IT implementation is a staged process in which adoption is followed by adaptation, acceptance, routinization, and infusion, and the factors that explain early stages differ from those that explain later ones (Cooper & Zmud, 1990). Complex technologies spread slowly not because firms lack information about them but because they lack the know-how to use them, and mediating institutions emerge to lower that knowledge barrier (Attewell, 1992). The distinction becomes a measurement problem: cumulative acquisition of software-process innovations ran well ahead of cumulative deployment, and the resulting assimilation gap was largest for innovations with high knowledge barriers (Fichman & Kemerer, 1999). Post-adoption usage and value vary widely across adopters of e-business, again pointing to organizational rather than technological determinants (Zhu & Kraemer, 2005). The post-adoption literature has since described, in detail, how users continue to explore, extend, and often under-use the features of technologies they have formally adopted (Jasperson et al., 2005), and how organizational mechanisms such as top-management participation carry an enterprise system from implementation into use (Liang et al., 2007). We build on this tradition but apply it to an outcome that it has rarely examined: whether assimilation of a production technology reaches the occupation that used to perform the task.

### 2.2 Complementary Assets

A second tradition holds that the value of information technology depends on complementary investments in skills, processes, and organizational design (Aral & Weill, 2007; Brynjolfsson & Hitt, 2000; Melville et al., 2004). General-purpose technologies display long lags for the same reason (Bresnahan & Trajtenberg, 1995; David, 1990), and the lag can be formalized as a productivity J-curve in which intangible complements are built before measured gains appear (Brynjolfsson et al., 2021). When prediction becomes cheap, the value of human judgment rises (Agrawal et al., 2018). We draw on these ideas to make the complements concrete for generative visual AI and to locate them in a single cost term. Expertise, review capacity, and compliance procedures are not supplied by a better model. A better model can raise the share of acceptable output, but it does not create the person who can judge that output, the time in which to judge it, or the policy that says whether it may be used.

### 2.3 Generative AI, Work, and Information Systems Research

A large literature maps AI capabilities onto occupational tasks (Eloundou et al., 2023; Felten et al., 2021; Webb, 2020). Exposure measures describe where a technology could matter, not where it has been acquired or assimilated. Task-based models separate the displacement, reinstatement, and productivity effects of automation (Acemoglu & Restrepo, 2018, 2019), and models of unbalanced growth show that tasks which cannot be automated become bottlenecks (Aghion et al., 2019; Baumol, 1967); we use both ideas in Section 3. Establishments exposed to AI change their hiring, but little aggregate effect is detectable at the occupation or industry level (Acemoglu et al., 2022). Evidence from online labor markets is sharper. Freelancers exposed to ChatGPT and image generators lost employment and earnings (Hui et al., 2024), and image-creation posts fell by about 17 percent after image generators were released, relative to manual-intensive jobs (Demirci et al., 2025). On creator platforms, generative tools raise output for some artists and reallocate demand across creator types (Kim et al., 2026; Zhou & Lee, 2024), and inside firms they raise individual productivity on suitable tasks (Brynjolfsson et al., 2025). These settings share a feature that our theory makes explicit: the buyer of a freelance task, or a worker inside a studied team, can switch to the tool without the firm first building a review routine or a compliance policy. We use the platform estimates as a reference for how large substitution can be once assimilation has occurred, not as a test of our account.

Within IS, work on AI has mostly examined what happens inside organizations that already use it. Experimental evidence suggests that people are poorly calibrated about their own capabilities when deciding whether to delegate to an AI system (Fügener et al., 2022), which implies that judging machine output is not costless even for competent workers; this is the mechanism that our review-cost term abstracts. Editorial work has framed AI as something that must be managed as a continually moving technological frontier (Berente et al., 2021), as a component of human–AI hybrids that reshape digital labor platforms (Rai et al., 2019), and, in the case of generative models, as a double-edged tool for knowledge work (Susarla et al., 2023). Studies of this kind take use as given. Labor economics, by contrast, takes the occupation as the unit and asks whether exposure predicts hiring, but seldom asks whether exposed employers have changed how work is done. What is missing is an account of the step in between, from acquiring a generator to reassigning a task to it, and of what that step implies for the evidence that occupation-level studies can supply.

Two strands of work are close to our empirical approach. Tambe and Hitt (2012) showed that IT labor data can sharpen measurement of IT's contribution to firm output. We use the same kind of data, online job adverts, for a narrower purpose: to ask what such data can and cannot reveal about assimilation. Babina et al. (2024) build firm-level indicators of AI investment from workforce data and find that AI-investing firms grow faster, mainly through product innovation. That is precisely the sort of firm-level linkage that the design in Section 9 requires for generative visual AI.

## 3 Theory

### 3.1 Acquisition and Assimilation

A firm produces visual tasks such as images, layouts, and short videos. *Acquisition* is the event that the firm has a visual generator available and reports using it. *Assimilation* of a task is the event that the task is produced by the generator rather than by the occupation that used to produce it. Acquisition is necessary for assimilation but not sufficient. A marketing team may try an image generator while the tasks that define a graphic-design role stay with that role. Survey indicators of use therefore measure something closer to acquisition than to assimilation.

Generative tools differ from the technologies studied in earlier assimilation research in one respect that matters for the theory. Acquiring a relational database or a CASE tool required licences, installation, and training, so acquisition itself was costly and partly selected firms that had already built complements. Acquiring a visual generator often requires a subscription or nothing at all. Acquisition decisions are then nearly independent of the complements, and acquisition statistics can rise without any corresponding change in the capacity to assimilate.

### 3.2 The Acceptance Threshold

Producing a visual asset with human labor costs $\theta$. Producing it with the generator costs $c$ for generation and $r$ for human review. With probability $a$ the output is accepted; with probability $1-a$ it is rejected and a human produces the asset at cost $\theta$. Expected cost with the generator is $c + r + (1-a)\theta$, so the firm assimilates the task when

$$a > a^{*} = \frac{c + r}{\theta}. \qquad (1)$$

The acceptance rate $a = a(q, m)$ rises with model quality $m$ and falls with the task's quality requirement $q$, so assimilation is more likely for routine and internal visuals than for brand-defining, technically exact, or legally sensitive work. The review cost $r = r(q; K)$ also rises with $q$ but falls with the firm's stock of complementary assets $K = (K^{E}, K^{R}, K^{C})$. Expertise $K^{E}$ lowers the cost of specifying a task and recognizing a failed draft. Review capacity $K^{R}$ lowers the cost of running that check as a routine rather than as an exception. Compliance procedures $K^{C}$ lower the cost of deciding whether an output may be used given copyright and personal-data exposure. Two implications follow directly from equation (1).

**Implication 1 (complements are necessary).** *If $c + r(q; K) \geq \theta$, then $a^{*} \geq 1$ and the task is not assimilated for any model quality $m$. Model improvements cannot substitute for missing complements; they matter only once complements have brought $a^{*}$ below one.*

**Implication 2 (cheap acquisition widens the gap).** Because acquisition requires little investment, the share of firms that acquire the tool can grow independently of $K$. If $K$ accumulates more slowly than acquisition, the share of acquiring firms that satisfy equation (1) for a given task falls even as acquisition rises, and the gap between acquisition and assimilation widens before it narrows.

### 3.3 From Tasks to Occupational Demand

Let $A^{u}$ be the share of employers that report use and $A^{a} \leq A^{u}$ the share that have assimilated the visual-production tasks of occupation $j$. Let $s_j$ be the share of the occupation's work that consists of such tasks, and let $\beta$ be the log change in demand for the occupation's visual-production work at an assimilating employer. To a first approximation, the aggregate log change in demand is

$$\Delta \ln N_j \approx s_j \cdot A^{a} \cdot \beta \;\geq\; s_j \cdot A^{u} \cdot \beta \quad \text{for } \beta < 0. \qquad (2)$$

The parameter $\beta$ combines substitution, which is negative, with a scale effect, which is positive when cheaper content raises the volume of visual work and the demand for direction and selection. Equation (2) makes clear why a small aggregate response is ambiguous. It can arise because $A^{a}$ is small relative to $A^{u}$, which is the assimilation gap, or because $\beta$ is close to zero, which is assimilation with offsetting scale effects. It can also arise simply because $s_j \cdot A^{u} \cdot \beta$ is small even when $A^{a} = A^{u}$. Section 4 shows that this last possibility is the binding one in current data.

### 3.4 Review as a Bottleneck Task

Equation (1) says when a firm assimilates a task. To see what assimilation does to labor demand, let a unit of the visual asset require $h$ hours of human production, so that $\theta = wh$, and let review require $u$ hours, so that $r = wu$. Write $\rho = r/\theta$ for review cost relative to human production and $\gamma = c/\theta$ for generation cost relative to human production, so that $a^{*} = \gamma + \rho$. With the generator, a unit of output needs review labor and, with probability $1-a$, human production labor, so labor per unit falls from $h$ to $u + (1-a)h$, a ratio of $1 - a + \rho$, while cost per unit falls by the ratio $\kappa = \gamma + \rho + 1 - a$. The ratio $\kappa$ is below one exactly when $a > a^{*}$. Review labor is paid the same wage as production labor; relaxing this changes $\rho$ but not the argument.

**Proposition 1 (review floor).** *Labor per unit of output at an assimilating firm cannot fall below the review share $\rho$, however high the acceptance rate $a$. If review hours do not fall with model quality, improvements in the generator reduce labor per unit only down to this floor, and when $\rho$ is large relative to $a$ the labor saved is small even though the task has been assimilated.*

The floor is a bottleneck: when a task that can be automated is complementary to one that cannot, the task that cannot be automated becomes the binding constraint, and its share of the remaining labor rises as the generator improves (Aghion et al., 2019; Baumol, 1967). Because $\rho$ depends on the complements $K$ through review cost, the same complements that govern assimilation also govern how much labor assimilation can save. The condition that review hours do not fall with model quality is an assumption, not a result. It is plausible where review means judging brand fit, legal exposure, or factual accuracy, and less so where a better model simply produces fewer visible defects; we return to it in Section 10.4.

### 3.5 Displacement, Reinstatement, and Scale

Equation (2) leaves $\beta$ unspecified. Let $\varepsilon$ be the price elasticity of demand for the occupation's visual output, so that output rises by $\kappa^{-\varepsilon}$ when cost per unit falls by the ratio $\kappa$. The net effect on demand for the occupation's work at an assimilating employer is

$$\beta = \ln(1 - a + \rho) - \varepsilon \ln \kappa. \qquad (3)$$

The first term combines displacement, because the generator takes over a share $a$ of human production, with reinstatement, because review and direction create labor $\rho$ that did not exist before; these are the displacement and reinstatement effects of the task-based framework (Acemoglu & Restrepo, 2018, 2019). The second term is the productivity or scale effect, which is positive because cheaper output raises the quantity demanded and with it the demand for review and direction. The values $\beta = -0.19$ and $\beta = -0.5$ used below are therefore reduced-form: each bundles $a$, $\rho$, $\gamma$, and $\varepsilon$. For example, with $a = 0.8$, $\rho = 0.3$, and $\gamma = 0.05$, labor per unit falls to one half and cost per unit to 0.55 of its earlier level, and $\beta$ is $-0.39$ if $\varepsilon = 0.5$, $-0.10$ if $\varepsilon = 1$, and $+0.02$ if $\varepsilon = 1.2$.

**Proposition 2 (scale offset).** *The net effect $\beta$ is negative if and only if $\varepsilon < \varepsilon^{*} = \ln(1 - a + \rho)/\ln \kappa$, and $\varepsilon^{*} > 1$ whenever $\gamma > 0$. As generation cost falls toward zero, $\varepsilon^{*}$ approaches one: complete assimilation reduces demand for the occupation if demand for visual output is inelastic and can raise it only if demand is elastic.*

### 3.6 Adjustment Through Attrition

Job adverts measure hiring, and hiring is how most employers reduce a workforce without layoffs. Let $L(t)$ be an employer's employment in the occupation, $\delta$ the separation rate, and $H(t)$ hires, so that $L(t+1) = (1 - \delta)L(t) + H(t)$. Suppose assimilation lowers target employment to $L^{*} = (1 - f)L_0$ and the employer closes a fraction $\lambda \leq \delta$ of the remaining gap each period by adjusting hiring:

$$H(t) = \delta L(t) + \lambda\,(L^{*} - L(t)). \qquad (4)$$

**Proposition 3 (attrition lag).** *Under equation (4), (i) hiring in the first period falls by the fraction $(\lambda/\delta)f \leq f$ and converges to a fall of $f$, so the decline in adverts never exceeds the decline in target employment, and equation (5) below, which gives the coefficient implied by $f$, is an upper bound for adverts as well as for employment; (ii) employment closes only a fraction $1 - (1-\lambda)^{T}$ of the gap after $T$ periods. With $\lambda = 0.10$, for example, 19 percent of the gap is closed after two years and 41 percent after five.*

Two consequences follow. Employment series, such as those in Section 7.3, can show no contraction for years after assimilation has begun, so adverts are the earlier signal, though not a larger one. And a decline that began before the technology, because of structural change in the industries that employ the occupation, enters as a lower target employment at an earlier date and follows the same dynamics. A pre-existing trend in adverts and a target cut caused by the technology cannot be told apart without firm-level data that observe use of the tool.

### 3.7 Competing Accounts

Table 1 sets out four accounts and what each predicts for four observables. Only the first three columns are observed in this paper. The fourth, the firm-level link between use and hiring, is what discriminates among the last three accounts.

**Table 1. Competing accounts and their observable implications**

| Account | Acquisition ($A^{u}$) | Barriers cited by non-adopters | Occupation-level hiring | Firm-level link (not observed here) |
|:--|:--|:--|:--|:--|
| Capability failure | Low | "Not useful" dominant | No change | Users do not reassign tasks |
| Complete assimilation, net substitution | Substantial | Any | $\Delta \ln N \approx s \cdot A^{u} \cdot \beta$, $\beta < 0$ | Users cut visual hiring relative to non-users |
| Assimilation, offsetting scale | Substantial | Any | $\Delta \ln N \approx 0$ | Users reassign tasks; hiring unchanged; postings shift toward direction and review |
| Assimilation gap | Substantial | Complements (expertise, legal, privacy) dominant | $\Delta \ln N \approx s \cdot A^{u} \cdot \beta$, small | Few users reassign tasks; reassignment rises with $K$ |

*Notes.* $A^{u}$: share of firms reporting use. $A^{a}$: share that have assimilated the occupation's visual tasks. $K$: complementary assets. The occupation-level column discriminates among accounts only when $s \cdot A^{u} \cdot \beta$ exceeds the minimum detectable effect of the design (Section 4).

From the table we derive two hypotheses that can be examined with current data and one that cannot. **H1 (complements, not capability):** among firms that considered AI and did not adopt it, complementary-asset barriers are cited substantially more often than lack of usefulness. **H2 (detectability):** at current acquisition rates and at platform-sized substitution effects, the occupation-level hiring response implied by complete assimilation lies below the minimum detectable effect of exposure-based designs. **H3 (firm-level, for future data):** among acquiring firms, task reassignment increases with $K$, and hiring for visual occupations falls only among firms that have reassigned tasks.

## 4 What Occupation-Level Data Can Identify

Exposure-based hiring designs regress the change in log adverts for occupation $j$ on standardized exposure. Suppose the most exposed occupation lies $k$ standard deviations above the mean and that its work is almost entirely visual production ($s_j \approx 1$). If exposure is approximately proportional to $s_j$, complete assimilation implies a coefficient per standard deviation of approximately

$$\gamma^{*} \approx A^{u} \cdot \beta / k. \qquad (5)$$

The design can detect $\gamma^{*}$ only if its magnitude exceeds the minimum detectable effect (MDE), which for a two-sided 5 percent test at 80 percent power is approximately 2.8 times the standard error of the coefficient. This gives a classification rule, stated before we apply it, so that neither a small nor a large observed coefficient is read as support for the gap.

(i) If $|\gamma^{*}|$ is below the MDE, the design is uninformative about assimilation, whatever the estimated coefficient. A null result does not support the gap, and a negative result is not evidence of substitution. (ii) If $|\gamma^{*}|$ exceeds the MDE and the estimate is significantly smaller in magnitude than $\gamma^{*}$, the data reject complete assimilation with net substitution but do not distinguish the gap from offsetting scale effects. (iii) If the estimate is significantly larger in magnitude than the largest plausible $\gamma^{**}$, which we take to be the coefficient implied by $\beta = -0.5$ at the acquisition rate of the highest-acquisition sector, or if the gradient is already present before the technology was available, the decline is attributed to other causes and counts as evidence for none of the accounts.

The reference value of $\beta$ comes from the platform literature. A 17 percent fall in image-creation posts (Demirci et al., 2025) corresponds to $\beta \approx -0.19$. Because standing occupations may adjust differently, we also consider $\beta = -0.5$ (a 39 percent fall among assimilating employers) as an aggressive case. Appendix B gives the derivation, including the effect of measurement error in exposure.

## 5 Data

### 5.1 Acquisition and Barriers

We use Eurostat's survey on ICT usage in enterprises (Eurostat, 2026), which covers firms with ten or more employees in the EU27. The 2025 wave asks whether enterprises use AI that generates pictures, video, or sound. This is the closest public measure of acquisition of generative visual AI and is available only for 2025. Text generation, asked in 2021, 2023, 2024, and 2025, and image recognition provide the time path of neighboring AI uses. The survey asks enterprises that considered AI but did not adopt it why they did not, offering lack of expertise, unclear legal consequences, data protection and privacy, costs, data availability or quality, incompatibility with existing systems, ethical considerations, and the view that AI is not useful. These items correspond to the complementary assets, with two limits that bound every inference below: they refer to AI in general rather than to visual generators, and they are asked only of firms that considered AI. They describe the acquisition margin, not the assimilation margin among users.

### 5.2 Hiring Series

Because the acquisition measure covers EU firms, the hiring series is Eurostat's experimental online job advertisements by ISCO-08 three-digit occupation, 2019 to 2024 (Eurostat, 2026), with 2022 as the base year (604 country-occupation cells, 96 occupations, 16 countries, after a floor of 1,000 base-year adverts). Its population matches the acquisition data, but it offers only two post-2022 years. The Canadian series is the Job Vacancy and Wage Survey by NOC 2021 unit group, 2015 to 2026 (Statistics Canada, 2026), restricted to 308 unit groups with at least 1,000 vacancies in the base window; the quarter 2020Q2 was not collected, so 2020 and 2021 cannot be used. European Labour Force Survey employment by industry and US sector postings from Indeed Hiring Lab (2026) are used descriptively.

### 5.3 Exposure and Its Measurement

Occupational exposure to visual content creation is the mean, over O\*NET task statements (National Center for O\*NET Development, 2026), of a language-model score on a 0 to 2 rubric divided by two. It is mapped to European occupations through ISCO-08 (three-digit prefix of the ESCO crosswalk) and to Canadian occupations through NOC main-duty statements. The primary measure uses a narrow rubric that scores production or editing of visual content (Appendix A).

The construct is hard to code reliably, and we report the evidence in full. On 199 human-validated tasks, design-weighted Cohen's $\kappa$ between two human coders is 0.18, and the narrow score's weighted $\kappa$ with the two coders is 0.11 and 0.04. A broad rubric that scores work with visual materials agrees better with the coders (weighted $\kappa$ 0.31 to 0.41), but it was written after one coder's pattern on a first half-sample had been seen, so we report it only as exploratory. A rule-based score correlates 0.78 to 0.88 with the narrow score and serves as a robustness check.

These agreement statistics need careful reading, for three reasons. First, chance-corrected coefficients are depressed when one category dominates, and the great majority of O\*NET task statements describe no visual production at all; low $\kappa$ at the task level can therefore coexist with high raw agreement. Future validation work should report prevalence, raw agreement, and a prevalence-robust statistic alongside $\kappa$. Second, the exposure measure that enters the regressions is an occupation-level mean over roughly twenty task statements, and averaging raises reliability when task-level errors are independent. By the Spearman–Brown relation, a task-level reliability between 0.04 and 0.18 implies an occupation-level reliability of roughly 0.45 to 0.81 for twenty tasks. This is an indicative range, not an estimate: it assumes independent errors, and systematic bias in the language-model score, for example a tendency to treat all design-related occupations alike, does not average out. Third, and most important for our argument, classical measurement error attenuates the coefficient per standard deviation of exposure by the square root of the reliability (Appendix B). Complete assimilation would therefore produce a *smaller* coefficient than the one in equation (5), while the minimum detectable effect is unchanged. Noise in the exposure measure makes the detectability result stronger, not weaker. What it weakens is the substantive reading of any observed gradient, which is why we classify gradients by the bound before interpreting them and make no claim that the gradients are effects of visual generation. We do not correct the coefficients for attenuation.

## 6 The Acquisition Margin

### 6.1 Acquisition Is Substantial and Rising

In 2025, 9.6 percent of EU27 enterprises with ten or more employees used AI that generates pictures, video, or audio, close to the 8.8 percent that used text generation (Table 2). The share rises to 27.9 percent among firms with 250 or more employees, 35.5 percent in information and communication, and 36.2 percent in publishing, film, television, and music. Text-generation use rose from 1.3 percent in 2021 to 2.1 percent in 2023, 5.4 percent in 2024, and 8.8 percent in 2025, while use of at least one AI technology rose from 7.7 to 20.0 percent. Image recognition grew only from 2.1 to 3.8 percent. Acquisition of generative tools is therefore early but accelerating, and it is concentrated where visual production is most common.

**Table 2. Acquisition of generative AI, EU27, 2025 (percent of enterprises with 10 or more employees)**

| Group | Picture, video, or audio | Text generation |
|:--|--:|--:|
| All enterprises (10+) | 9.6 | 8.8 |
| 10–49 employees | 8.1 | 7.0 |
| 50–249 employees | 14.4 | 14.8 |
| 250 or more employees | 27.9 | 31.7 |
| Information and communication (J) | 35.5 | 42.2 |
| Publishing, film, TV, music (J58–J60) | 36.2 | 34.0 |
| Professional, scientific, technical (M) | 18.7 | 17.7 |
| Construction (F) | 4.5 | 3.2 |
| Transportation and storage (H) | 4.0 | 3.9 |

*Source.* Eurostat survey on ICT usage in enterprises, indicators E_AI_TPVSG and E_AI_TNLG. The visual-generation indicator exists only for 2025 and is interpreted as acquisition ($A^{u}$), not assimilation.

### 6.2 Reported Barriers Are Complements, Not Capability

Among enterprises that considered AI and did not adopt it, 70.3 percent cite lack of relevant expertise, 53.6 percent unclear legal consequences, and 52.7 percent data protection and privacy (Table 3). Costs are cited by 38.4 percent and the view that AI is not useful by 17.8 percent. The pattern is similar across size classes. This is consistent with H1: firms that stopped short of acquisition describe the obstacle as a missing asset rather than as a tool that fails the task.

**Table 3. Reasons for not using AI among enterprises that considered it, EU27, 2025**

| Reason | Percent | Interpretation in the model |
|:--|--:|:--|
| Lack of relevant expertise | 70.3 | Expertise ($K^{E}$) |
| Unclear legal consequences | 53.6 | Compliance procedures ($K^{C}$) |
| Data protection and privacy | 52.7 | Compliance procedures ($K^{C}$) |
| Costs seem too high | 38.4 | Fixed cost of complements or of the tool |
| Ethical considerations | 24.6 | Institutional complement |
| AI is not useful for the enterprise | 17.8 | Capability failure |

*Source.* Eurostat 2025. Multiple answers allowed. Items refer to AI in general and are asked only of enterprises that considered AI.

Three limits govern how far this evidence reaches. First, the items refer to AI in general, so the share citing legal uncertainty may partly reflect text or decision tools. Second, firms that never considered AI are excluded, and they may include many for which the tool is genuinely not useful; the 17.8 percent figure is therefore a lower bound on capability-based non-adoption in the population. Third, the evidence concerns non-adopters and cannot show that the same barriers block assimilation among adopters, which is what H3 would test.

Cross-country patterns are descriptive. Across 23 countries, acquisition of visual generation is negatively correlated with the share of considerers citing costs ($r = -0.76$), weakly with unclear legal consequences ($r = -0.24$) and data protection ($r = -0.02$), and positively with missing expertise ($r = 0.46$), which would be expected if countries with more acquisition also have more considerers who have encountered the knowledge barrier. With 23 observations these correlations do not show that differences in legal concern explain differences in acquisition. Sector exposure to visual content creation correlates with visual-generation acquisition at 0.84, but also with text-generation acquisition at 0.83 and image recognition at 0.81, and in country-sector cells with country fixed effects a standard deviation of exposure is associated with higher acquisition of every AI type (permutation $p$-values 0.003 to 0.006). Exposure therefore identifies digitally intensive sectors rather than a specific propensity to acquire visual generators, which is a further reason not to read exposure gradients in hiring as effects of visual generation.

## 7 Occupation-Level Hiring Through the Bound

### 7.1 Exposure Gradients

For each country-occupation cell in 16 European countries we regress the change in log online adverts relative to 2022 on standardized visual-creation exposure and standardized language-model exposure, with country-year fixed effects and standard errors clustered by ISCO occupation (Table 4). A standard deviation of exposure is associated with 1.6 percent fewer adverts in 2023 (standard error 0.6, randomization $p = 0.016$) and 1.2 percent fewer in 2024 (standard error 1.7, $p = 0.19$). Without the language-model control the estimates are $-3.7$ and $-5.9$ percent, because exposure to visual content creation and exposure to language models are positively correlated across occupations (0.27).

**Table 4. Europe: change in log adverts per standard deviation of visual-creation exposure, relative to 2022**

| | 2019 | 2020 | 2021 | 2023 | 2024 |
|:--|--:|--:|--:|--:|--:|
| Preferred (country-year FE, language-model control) | +0.024 (0.014) | +0.008 (0.013) | +0.011 (n.r.) | −0.016 (0.006) | −0.012 (0.017) |
| No language-model control | +0.008 (0.013) | −0.002 (0.013) | n.r. | −0.037 (n.r.) | −0.059 (n.r.) |
| Deviation from linear pre-trend (preferred) | — | — | — | −0.009 (0.007) | +0.002 (0.023) |
| Randomization $p$ (preferred) | — | — | — | 0.016 | 0.19 |
| Minimum detectable effect (preferred) | 0.038 | 0.037 | n.r. | 0.016 | 0.048 |

*Notes.* 604 country-occupation cells (96 occupations, 16 countries); country-year fixed effects; standard errors clustered by ISCO three-digit occupation in parentheses. The deviation row estimates a linear trend in the exposure gradient on 2019–2021 (−0.0072 per year, standard error 0.0047) and reports the deviation of 2023 and 2024 from its extrapolation. Minimum detectable effect = 2.8 × standard error of the preferred specification (two-sided 5 percent test, 80 percent power). n.r. = not reported; — = not applicable.

The coefficients before 2022 are positive (+0.024, +0.008, and +0.011 for 2019, 2020, and 2021). Because the outcome is the change in adverts relative to 2022, a positive coefficient means that exposed occupations had more adverts in those years than in 2022, that is, they were already declining relative to others before generative tools were released. The trend is weak ($-0.007$ per year, standard error 0.005), but it runs in the same direction as the post-2022 coefficients: relative to it, the 2023 and 2024 coefficients are $-0.009$ (standard error 0.007) and $+0.002$ (0.023). The series has only two post-2022 years. In Canada, within NOC two-digit groups, the coefficient is $-2.2$ percent in the first post-2022 year (standard error 0.9, randomization $p = 0.10$) and indistinguishable from zero afterward ($-0.9$, $+1.6$, and $+1.1$ percent in 2024, 2025, and 2026, with standard errors of 2.5, 2.7, and 3.0), in a market where total vacancies fell 47 percent.

### 7.2 Applying the Bound

In the European exposure distribution the most exposed occupations are creative and performing artists (ISCO 265, 6.2 standard deviations above the mean) and architects, planners, surveyors, and designers (ISCO 216, which includes graphic designers, 5.7 standard deviations). We set $k = 5.7$, the value more favorable to detection. Table 5 reports the coefficient per standard deviation that complete assimilation would produce under equation (5) for a range of acquisition rates and substitution effects, alongside the minimum detectable effect and the observed coefficients.

**Table 5. Coefficient per standard deviation implied by complete assimilation ($A^{a} = A^{u}$), Europe, $k = 5.7$**

*Panel A. Implied coefficients*

| Acquisition rate $A^{u}$ | $\beta = -0.19$ (platform) | $\beta = -0.50$ (aggressive) | Implied log change, most exposed occupation ($\beta = -0.50$) |
|:--|--:|--:|--:|
| 9.6% (EU, all firms) | −0.003 | −0.008 | −0.048 |
| 36.2% (publishing, film, broadcasting) | −0.012 | −0.032 | −0.181 |
| 2.1% (text generation 2023, proxy for early acquisition) | −0.001 | −0.002 | −0.010 |

*Panel B. Observed coefficients and detectability*

| Year | Observed, preferred (SE) | Observed, no language-model control | Minimum detectable effect | MDE $\times k$ (log change) | Observed $\times k$, preferred |
|:--|--:|--:|--:|--:|--:|
| 2023 | −0.016 (0.006) | −0.037 | 0.016 | 0.09 | −0.09 |
| 2024 | −0.012 (0.017) | −0.059 | 0.048 | 0.27 | −0.07 |

*Notes.* $\gamma^{*} = A^{u} \cdot \beta / k$. The upper bound $A^{a} = A^{u}$ maximizes the implied response; any assimilation gap makes it smaller. Acquisition rates: Eurostat 2025 (all enterprises; publishing, film, television, and music) and Eurostat 2023 text generation as a proxy for early acquisition. The final column of Panel A multiplies by $k$; the last two columns of Panel B convert coefficients to the scale of the most exposed occupation. The no-language-control estimate multiplied by $k$ is $-0.34$ for 2024.

Two results follow. First, every complete-assimilation scenario for 2024 implies a coefficient below the minimum detectable effect of 0.048. The largest, $-0.032$, requires a 39 percent fall among assimilating employers in a sector where 36 percent have acquired the tool, and assimilation by all of them. Under rule (i), the 2024 European estimate is uninformative about whether acquisition has been assimilated, and its small and imprecise coefficient supports neither the gap nor substitution. The preferred estimate of $-0.012$ equals what the platform effect would produce if every employer in a high-acquisition sector had assimilated, but it lies 0.7 standard errors from zero. The estimate without the language control ($-0.059$) is larger than any scenario, but it is not significantly larger than $\gamma^{**}$ ($-0.032$; $z = 1.3$) and, as the difference between the specifications shows, partly reflects exposure to language models.

Second, the 2023 estimate has more power (minimum detectable effect 0.016). Text-generation acquisition stood at 2.1 percent in 2023. If acquisition of visual generators was similarly low, complete assimilation with $\beta = -0.5$ implies a coefficient of about $-0.002$, and the observed $-0.016$ differs from it significantly ($z = 2.6$); if acquisition had already reached its 2025 level, the implied coefficient would be $-0.008$ and the difference would not be significant ($z \approx 1.3$). Either way, the 2023 gradient is of the size predicted by the trend that preceded the technology, since relative to that trend it is $-0.009$ (standard error 0.007). Under rule (iii), the gradient is better attributed to other causes than to generative visual AI.

The Canadian series has standard errors of 0.025 to 0.030 per standard deviation after 2023, so its minimum detectable effect is about 0.07 to 0.08 per standard deviation. For the most exposed unit group, 9.0 standard deviations above the mean, this corresponds to a log change of about 0.6 to 0.8. The Canadian series is therefore uninformative about assimilation at any plausible acquisition rate, and its first-year coefficient, which does not persist, leads to the same classification.

### 7.3 Employment Where Acquisition Is Highest

European Labour Force Survey employment in video and film production, advertising, and other professional activities including design and photography rose between 2019–2021 and 2023–2025 by 0.13, 0.11, and 0.15 log points, against a median of 0.04 across 88 industries; creative industries gained 0.09 log points relative to other industries (randomization $p = 0.20$). US sector postings in arts, media, and marketing fell relative to other sectors, but so did software and data postings, and the same sectors were not stable before the base period. The finest public occupation-by-industry cross-tabulation (one-digit occupations by industry section) shows professionals' employment growing by 0.26 log points in information and communication, 0.17 in professional and technical activities, and 0.14 in arts and entertainment, against a median of 0.19 across 19 sections; these groups are dominated by occupations other than visual production, and two-digit occupation data (cultural professionals, +0.09) are too coarse to isolate designers or artists. Neither series isolates visual generation, and both are consistent with every account in Table 1 other than large and rapid net substitution.

### 7.4 Acquisition Interaction in Europe

A European dose-response test interacts occupational exposure with country-level acquisition of picture, video, or audio generation (Eurostat, 2026), which is available for 12 of the 16 countries. Complete assimilation predicts a steeper exposure gradient where acquisition is higher, whereas the gap and offsetting-scale accounts predict no such interaction. The interaction coefficient per standard deviation of acquisition (5.1 percentage points) is $-0.008$ (standard error 0.008) in 2023 and $+0.003$ (0.016) in 2024; permutation $p$-values across countries are 0.46 and 0.85. In 2021, before the base year, it is $+0.008$ (0.007). Complete assimilation with $\beta = -0.5$ predicts an interaction of only about $-0.004$ ($-0.5 \times 0.051 / 5.7$), far smaller than the standard errors, so the test cannot discriminate among the accounts. We report it because it is the only test here that uses variation in acquisition directly. It becomes informative only with more countries, more post-2022 years, and acquisition measured before the outcome. The detectability result does not depend on it, because that result depends only on acquisition rates, reference effect sizes, and standard errors.

### 7.5 Sector-Level Acquisition and Employment

Firm-level links between use and hiring are not public, so we use sectors as the nearest proxy. In 260 country-sector cells (30 countries, 9 NACE sections), sectors with higher acquisition of picture, video, or audio generation in 2025 had higher employment growth between 2019–2021 and 2023–2025: 0.051 log points per standard deviation of acquisition (10.6 percentage points), with country fixed effects (standard error 0.010). The same relationship holds before the technology: for 2016–2018 to 2019–2021 the coefficient is 0.049 (0.008), and the difference between the two periods is 0.002 (0.012). Acquisition is not a separate signal here, because it correlates 0.92 with acquisition of text generation and 0.95 with use of any AI across cells; adding the text-generation control leaves a post-minus-pre difference of 0.041 (0.020), which is imprecise because of this collinearity. In the United States, the sector share of businesses reporting AI use in the Business Trends and Outlook Survey (U.S. Census Bureau, 2026) correlates 0.59 across 20 sectors with the sector's reported employee-change index (descriptive only). Complete assimilation with $\beta = -0.5$ would imply a coefficient of about $-0.053$ times $s$, the share of sector employment in visual-production occupations, per standard deviation of acquisition. Because $s$ is well below one, the implied effect is far smaller than the standard errors. Sector-level data therefore show that acquisition marks growing, digitally intensive sectors, not that it displaces labor, and they cannot reveal the assimilation margin; this is the limit that firm-level data would remove.

## 8 When Will Occupation-Level Data Become Informative?

Equation (5) also tells us when the European design would gain the power to detect complete assimilation. Holding the 2024 standard error fixed, detection for an occupation at $k = 5.7$ requires $|A^{a} \cdot \beta| \geq 0.27$. With $\beta = -0.19$ this cannot occur even at full assimilation. With $\beta = -0.5$ it requires $A^{a} \geq 0.54$; with $\beta = -0.8$ (a 55 percent fall among assimilators), $A^{a} \geq 0.34$. Table 6 reports the first year in which acquisition would reach these shares if its log-odds rose at the 2023–2025 pace of text-generation AI (about 0.75 per year) or at two-thirds or one-third of that pace. Because $A^{a} \leq A^{u}$, these are the earliest possible detection dates; any persistent assimilation gap pushes them later. The standard error will change as post-2022 years accumulate, so the dates are conditional on the precision of the current design.

**Table 6. Earliest year in which complete assimilation would become detectable, European design**

| $\beta$ among assimilators | Required $A^{a}$ | Fast (all / media) | Medium (all / media) | Slow (all / media) |
|:--|--:|:--|:--|:--|
| −0.19 (−17%) | above 100% | never | never | never |
| −0.50 (−39%) | 54% | 2029 / 2026 | 2030 / 2027 | 2035 / 2028 |
| −0.80 (−55%) | 34% | 2028 / 2025 | 2029 / 2025 | 2032 / 2025 |

*Notes.* Paths start in 2025 at 9.6 percent (all firms) or 36.2 percent (publishing, film, and broadcasting) with log-odds slopes of 0.75 (fast), 0.50 (medium), and 0.25 (slow) per year. Detection threshold: $2.8 \times 0.017 \times 5.7 \approx 0.27$. Each entry is the first year in which the required share is reached. Dates assume $A^{a} = A^{u}$ and are lower bounds; entries that fall close to a threshold can shift by a year with the rounding of the standard error.

The table is not a forecast of displacement. Its purpose is to show that, for substitution effects of the size observed on platforms, aggregate occupational data will remain uninformative for the foreseeable future, and that even large effects require assimilation to reach most employers before they can be seen. The media entries for $\beta = -0.8$ are already within reach in 2025, because that sector's acquisition rate exceeds the required share. They show that only very large effects concentrated in high-acquisition sectors could already be detectable, and even these assume that every acquiring employer has assimilated the tool. Questions about generative-AI assimilation in standing occupations will have to be answered with firm-level data.

## 9 A Firm-Level Design That Would Discriminate

The accounts in Table 1 differ in what they predict for firms that report use. A design that discriminates among them needs four linked measures at the firm level: reported use of visual generators, the stock of complementary assets, task reassignment for visual production, and hiring for visual occupations. Several data sources could provide them. Eurostat ICT-usage microdata can be linked to employer-employee registers in some member states through national statistical offices. Online job advertisements that carry employer identifiers can record both hiring for visual occupations and requests for generative-AI skills, in the spirit of the firm-level AI indicators built from workforce data by Babina et al. (2024). And a purpose-built survey of acquiring firms can measure the three assets and the share of visual tasks reassigned.

The predictions are specific. Under the assimilation gap, task reassignment among users is low on average and rises with expertise, review capacity, and compliance procedures, and hiring for visual occupations falls, if at all, only among users with high asset stocks. Under complete assimilation with net substitution, users cut visual hiring relative to non-users regardless of asset stocks. Under offsetting scale effects, users reassign tasks but their visual hiring does not fall, and their job adverts shift toward direction, selection, and review. Under capability failure, users do not reassign tasks even when assets are present. Each prediction can be falsified by a single well-measured comparison, and the asset measures make the test one of mechanism rather than of association between use and hiring.

## 10 Discussion

### 10.1 Contributions to Information Systems Research

Assimilation research was built on technologies whose acquisition was costly. Generative AI reverses that condition. When acquisition is nearly free, the decision to acquire carries little information about the decision to reorganize work, and the gap between the two can widen as adoption statistics rise. The complementary-asset account developed here gives that gap a precise location: review cost, which depends on expertise, review capacity, and compliance procedures rather than on the model. This adds a mechanism to IT-complementarity research for a class of technologies in which the bottleneck is judging output rather than producing it. Unlike earlier enterprise systems, model quality alone cannot substitute for the missing complements; improvements in the generator matter only after those complements have brought review cost below the cost of human production. The account also connects two literatures that rarely meet. IS studies of AI inside adopting organizations (for example, Fügener et al., 2022) take use as given, and labor-market studies of exposure take the occupation as given. Placing the assimilation step between them clarifies what each can and cannot say.

The paper also offers a methodological caution for a fast-growing literature. Exposure-based hiring designs are widely used to study generative AI, and their estimates are often read as early effects of the technology. The detectability bound shows that, for standing occupations and at current acquisition rates, these designs cannot detect plausible assimilation effects of the size observed on platforms, and that the gradients they do detect can be no larger than a trend that preceded the technology. A null or small coefficient in these designs is therefore uninformative about assimilation. The bound is simple enough to be reported alongside any such estimate, and doing so would prevent both false alarms and false reassurance. In this sense, the contribution is not a claim that generative visual AI has no labor-market effects, but a demonstration that occupation-level evidence of the kind currently available cannot yet reveal those effects.

A related reading is that falling demand for visual-production occupations reflects structural change in industries, such as shifts in how marketing and media content is produced and bought, and that generative AI accelerates change already under way rather than starting it. Our evidence is compatible with this reading. The European gradient was already moving in the same direction before 2022 ($-0.007$ per year, not statistically significant), and the estimates depend on the language-exposure control. In the model, acceleration enters through the acceptance threshold: the technology lowers the cost of review and generation for tasks in industries that were already reducing their demand for them, so assimilation is most likely where structural pressure exists. Country-year fixed effects absorb economy-wide shocks but not industry-specific restructuring, and the industry employment series in Section 7.3 show no contraction in the creative industries. Public data cannot show what happened to visual-production occupations within those industries, so the within-industry reading is a hypothesis rather than a finding. Separating acceleration from an independent effect of the technology requires firm-level data that observe an employer's industry, its use of the tool, and its hiring together.

### 10.2 A Macroeconomic Reading

The results fit a standard macroeconomic account of technology shocks. General-purpose technologies take effect only after complementary investments in organization and skills, so adoption can run ahead of measured effects (Bresnahan & Trajtenberg, 1995; Brynjolfsson et al., 2021; David, 1990). The task-based framework (Acemoglu & Restrepo, 2018, 2019) splits the labor-market effect of a technology into displacement, reinstatement, and productivity components, and equation (3) shows that the net effect on an occupation depends on how much review labor remains and on how elastic demand for visual output is. Because review is a bottleneck task (Baumol, 1967), better generation alone does not remove the labor that review requires, and the complements that govern assimilation also govern how much labor assimilation saves. If generative AI is a general-purpose technology (Eloundou et al., 2023), the experience of earlier general-purpose technologies suggests that its labor-market effects appear after complementary investments accumulate. Our results are consistent with this reading but do not test it.

Two features of labor adjustment shape what the data can show. Employers reduce workforces mainly through attrition, so hiring falls first and employment follows at the pace of separations (Proposition 3). Employment series can therefore show no contraction for years after assimilation begins, and an observed fall does not by itself identify the technology. Technology also often accelerates change already under way, such as the movement of labor out of industries in structural decline, which enters the model as an earlier and lower target employment. The usual macroeconomic expectation is that technology shocks appear as reallocation across tasks, occupations, and industries before they appear in aggregate employment. We study occupations and sectors, not aggregates, and say nothing about unemployment or aggregate productivity.

On timing, the evidence supports neither a prediction that effects will take decades nor the view that the future cannot be known. Table 6 gives earliest detection dates that range from 2025, for very large effects in high-acquisition sectors, to 2035, for a 39 percent fall under slow diffusion in the average firm, and never, in this design, for platform-sized effects. What the data cannot say is whether assimilation is occurring now. Answering that requires firm-level data that link use, complementary assets, task reassignment, and hiring.

### 10.3 Implications

For researchers, the implication is to report the acquisition rate and the reference effect size that an exposure estimate would require, and to treat estimates that exceed that requirement, or that predate the technology, as evidence about something else. For managers, the barrier evidence suggests that the constraints on using generative visual tools are organizational: review capacity and policies for copyright and personal data are complements to the tool, and waiting for better models will not build them. For statistical agencies and policymakers, a rising use indicator should not be read as rising task reassignment, and a small hiring response should not be read as evidence that the response will remain small. Adding questions on task reassignment and on review and compliance practices to enterprise surveys would make the gap directly measurable.

### 10.4 Limitations

We do not observe assimilation. The barrier items refer to AI in general and to firms that considered it, so they speak to the acquisition margin only. The hiring series are experimental, measure adverts or vacancies rather than employment, and would miss substitution through hours, outsourcing, or freelancing. Exposure is measured with low task-level agreement, and although we argue that this strengthens the detectability result, it limits what can be said about the gradients themselves; a categorical treatment defined by occupation codes (for example, graphic designers, visual artists, and photographers) would avoid model-based scoring and is a natural next step that we leave to future work. Acquisition rates are sector averages and do not identify the employers of particular occupations. We study occupations and sectors, not aggregate employment or productivity, and the macroeconomic reading in Section 10.2 interprets the results through the model rather than testing it. The review floor in Proposition 1 rests on the assumption that review hours do not fall with model quality; where better models reduce visible defects, review may become cheaper and the threshold in equation (1) may fall without any change in complements, which would weaken Implication 1 for those tasks. The detectability bound rests on a linear mapping from exposure to the visual share of work and on reference effect sizes from platforms, and both could be refined; however, plausible changes alter the numbers in Tables 5 and 6 without changing the conclusion that current designs lack the power to detect complete assimilation at platform-sized effects.

## 11 Conclusion

Generative visual AI has been widely acquired: about one in ten European firms used it in 2025, and about one in three in publishing, film, and broadcasting. Firms that considered AI and did not adopt it point to missing expertise, legal uncertainty, and data protection rather than to a tool that is not useful. The theory developed here explains why such complements govern assimilation and why near-free acquisition can let adoption statistics run ahead of any change in work. In macroeconomic terms, general-purpose technologies, task-based labor demand, bottleneck tasks, and attrition-based adjustment together imply that effects reach hiring and employment with a lag and unevenly across occupations. The empirical lesson is equally important. So far, occupation-level hiring data show no detectable labor-market effect of generative visual AI: the exposure gradients are small, imprecise, and no larger than the trend that preceded the technology. That is not evidence of no effect, because these designs could not have detected complete assimilation at platform-sized effects and cannot tell whether acquisition has been assimilated. Answering the question requires linking firms' use, their complementary assets, and their hiring, and this paper specifies what that evidence would have to show.

## Data, Code, and Use of Generative AI

All data are public (Eurostat, Statistics Canada, U.S. Census Bureau, O\*NET, Indeed Hiring Lab). Code, prompts, task scores, and human coding files required to reproduce the tables are available in an anonymized replication repository. **[CONFIRM before submission: keep this sentence only if the repository exists; otherwise describe what is actually available.]** Large language models were used as measurement instruments to code task statements. A generative AI assistant was used to help write analysis code and to draft and edit the manuscript. The authors reviewed all results, text, and code and take responsibility for the content.

## Appendix A. Rubrics

**Visual content creation (primary).** Score 2 if producing or editing visual content is central to the task; 1 if visual content is a partial or supporting product; 0 otherwise. Reading, inspecting, writing, and audio production do not count. Technical drawings count only when the task is about producing them as drawings or graphics.

**Broad visual materials (exploratory).** Score 2 if producing, designing, or editing visual or aesthetic output is the core of the task; 1 if the task works with visual materials without that core; 0 otherwise. Tasks are not scored merely because the worker must see to do them. This rubric was written after inspecting one coder's scores on a first half-sample and is reported only as exploratory.

## Appendix B. Derivation of the Detectability Bound

Let exposure $e_j$ be proportional to the visual share of work, $e_j = \lambda s_j$, and let standardized exposure be $z_j = (e_j - \bar{e})/\sigma_e$. If the most exposed occupation has $s_j \approx 1$ and $z_j = k$, and if exposure near the mean is small relative to its maximum, then $s_j \approx z_j/k$ over the relevant range. Substituting into equation (2) with $A^{a} = A^{u}$ gives $\Delta \ln N_j \approx (A^{u}\beta/k)\cdot z_j$, so the regression coefficient on $z_j$ under complete assimilation is $\gamma^{*} = A^{u}\beta/k$. The minimum detectable effect for a two-sided test of size 0.05 with power 0.8 is $(1.96 + 0.84)\cdot SE \approx 2.8\,SE$. Detection for the most exposed occupation requires $|A^{a}\beta| \geq 2.8\,SE\cdot k$. With $SE = 0.017$ (Europe, 2024) and $k = 5.7$ the threshold is 0.27. If mean exposure is not small relative to its maximum, $k$ overstates the effective spread and the implied $\gamma^{*}$ is somewhat larger, but for the values in Table 5 to cross the detection threshold the effective $k^{*}$ would need to fall below about 4 under the most aggressive scenario.

*Measurement error in exposure.* Suppose observed exposure is $\tilde{e}_j = e_j + u_j$, with $u_j$ independent of $e_j$ and of the outcome, and let $R = \mathrm{var}(e)/\mathrm{var}(\tilde{e})$ denote its reliability. The slope per unit of observed exposure is $R$ times the slope per unit of true exposure. Because $\sigma_{\tilde{e}} = \sigma_e/\sqrt{R}$, the coefficient per standard deviation of observed exposure is $\sqrt{R}\,\gamma^{*}$. Complete assimilation therefore implies a coefficient of magnitude $\sqrt{R}\,|\gamma^{*}|$, while the minimum detectable effect, a function of the standard error, is not reduced. With $R = 0.5$, for example, the largest scenario in Table 5 falls from $-0.032$ to about $-0.023$, further below the 2024 threshold of 0.048. Noise of this classical kind strengthens the conclusion that the design cannot detect complete assimilation. It does not license any substantive reading of the observed gradients, and if the error in the language-model score is correlated with exposure to language models, the direction of the bias is ambiguous.

*Occupation-level reliability.* If the exposure of an occupation is the mean of $n$ task-level scores with independent errors and task-level reliability $\rho$, the reliability of the mean is $n\rho/(1 + (n-1)\rho)$. For $n = 20$ and $\rho$ between 0.04 and 0.18 this is roughly 0.45 to 0.81. The relation is indicative only, since it assumes independent errors.

## Appendix C. Derivations for Section 3

*Labor and cost ratios.* Human production of a unit takes $h$ hours. With the generator, a unit requires $u$ hours of review and, with probability $1-a$, $h$ hours of human production, so expected labor per unit is $u + (1-a)h = h(\rho + 1 - a)$ with $\rho = u/h = r/\theta$ at equal wages. Expected cost per unit is $c + r + (1-a)\theta = \theta\kappa$. Output scales by $\kappa^{-\varepsilon}$ under constant elasticity $\varepsilon$, so labor demand scales by $(1 - a + \rho)\kappa^{-\varepsilon}$, which gives equation (3) after taking logarithms.

*Proposition 2.* $\beta < 0$ if and only if $\ln(1 - a + \rho) < \varepsilon \ln\kappa$. When $\gamma > 0$ and $a > a^{*}$, $1 - a + \rho < \kappa < 1$, so both logarithms are negative and $|\ln(1 - a + \rho)| > |\ln\kappa|$. Dividing by $\ln\kappa$ reverses the inequality: $\beta < 0$ if and only if $\varepsilon < \varepsilon^{*} = \ln(1 - a + \rho)/\ln\kappa$, and $\varepsilon^{*} > 1$. As $\gamma \to 0$, $\kappa \to 1 - a + \rho$ and $\varepsilon^{*} \to 1$.

*Proposition 3.* Substituting equation (4) into the employment equation gives $L(t+1) - L^{*} = (1 - \lambda)(L(t) - L^{*})$, so $L(t) - L^{*} = (1-\lambda)^{t}(L_0 - L^{*})$ and the share of the gap closed after $T$ periods is $1 - (1-\lambda)^{T}$. Hires in the first period are $H(0) = \delta L_0 - \lambda f L_0$, so $H(0)/(\delta L_0) = 1 - (\lambda/\delta)f$. As $t \to \infty$, $L(t) \to L^{*}$ and $H(t) \to \delta L^{*}$, so $H(t)/(\delta L_0) \to 1 - f$. Hires are non-negative in every period when $\lambda \leq \delta$, because $\lambda f \leq \delta$ for $f \leq 1$. The upper bound in part (i) holds when hiring is adjusted smoothly as in equation (4); a temporary hiring freeze could produce a larger transitory fall in adverts.

## References

Acemoglu, D., Autor, D., Hazell, J., & Restrepo, P. (2022). Artificial intelligence and jobs: Evidence from online vacancies. *Journal of Labor Economics, 40*(S1), S293–S340.

Acemoglu, D., & Restrepo, P. (2018). The race between man and machine: Implications of technology for growth, factor shares, and employment. *American Economic Review, 108*(6), 1488–1542.

Acemoglu, D., & Restrepo, P. (2019). Automation and new tasks: How technology displaces and reinstates labor. *Journal of Economic Perspectives, 33*(2), 3–30.

Aghion, P., Jones, B. F., & Jones, C. I. (2019). Artificial intelligence and economic growth. In A. Agrawal, J. Gans, & A. Goldfarb (Eds.), *The economics of artificial intelligence: An agenda*. University of Chicago Press.

Agrawal, A., Gans, J., & Goldfarb, A. (2018). *Prediction machines: The simple economics of artificial intelligence*. Harvard Business Review Press.

Aral, S., & Weill, P. (2007). IT assets, organizational capabilities, and firm performance: How resource allocations and organizational differences explain performance variation. *Organization Science, 18*(5), 763–780.

Attewell, P. (1992). Technology diffusion and organizational learning: The case of business computing. *Organization Science, 3*(1), 1–19.

Babina, T., Fedyk, A., He, A., & Hodson, J. (2024). Artificial intelligence, firm growth, and product innovation. *Journal of Financial Economics, 151*, 103745.

Baumol, W. J. (1967). Macroeconomics of unbalanced growth: The anatomy of urban crisis. *American Economic Review, 57*(3), 415–426.

Berente, N., Gu, B., Recker, J., & Santhanam, R. (2021). Managing artificial intelligence. *MIS Quarterly, 45*(3), 1433–1450.

Bresnahan, T. F., & Trajtenberg, M. (1995). General purpose technologies: "Engines of growth"? *Journal of Econometrics, 65*(1), 83–108.

Brynjolfsson, E., & Hitt, L. M. (2000). Beyond computation: Information technology, organizational transformation and business performance. *Journal of Economic Perspectives, 14*(4), 23–48.

Brynjolfsson, E., Li, D., & Raymond, L. (2025). Generative AI at work. *The Quarterly Journal of Economics, 140*(2), 889–942.

Brynjolfsson, E., Rock, D., & Syverson, C. (2021). The productivity J-curve: How intangibles complement general purpose technologies. *American Economic Journal: Macroeconomics, 13*(1), 333–372.

Cooper, R. B., & Zmud, R. W. (1990). Information technology implementation research: A technological diffusion approach. *Management Science, 36*(2), 123–139.

David, P. A. (1990). The dynamo and the computer: An historical perspective on the modern productivity paradox. *American Economic Review, 80*(2), 355–361.

Demirci, O., Hannane, J., & Zhu, X. (2025). Who is AI replacing? The impact of generative AI on online freelancing platforms. *Management Science, 71*(10), 8097–8108.

Eloundou, T., Manning, S., Mishkin, P., & Rock, D. (2023). *GPTs are GPTs: An early look at the labor market impact potential of large language models* (arXiv:2303.10130). arXiv.

Eurostat. (2026). *ICT usage in enterprises; online job advertisements by occupation (experimental); Labour force survey* [Data sets]. Retrieved October 4, 2026, from the Eurostat dissemination database.

Felten, E., Raj, M., & Seamans, R. (2021). Occupational, industry, and geographic exposure to artificial intelligence. *Strategic Management Journal, 42*(12), 2195–2217.

Fichman, R. G., & Kemerer, C. F. (1999). The illusory diffusion of innovation: An examination of assimilation gaps. *Information Systems Research, 10*(3), 255–275.

Fügener, A., Grahl, J., Gupta, A., & Ketter, W. (2022). Cognitive challenges in human–artificial intelligence collaboration: Investigating the path toward productive delegation. *Information Systems Research, 33*(2), 678–696.

Hui, X., Reshef, O., & Zhou, L. (2024). The short-term effects of generative artificial intelligence on employment: Evidence from an online labor market. *Organization Science, 35*(6), 1977–1989.

Indeed Hiring Lab. (2026). *Job postings index, by sector, United States* [Data set]. Retrieved October 4, 2026. Creative Commons Attribution 4.0.

Jasperson, J. S., Carter, P. E., & Zmud, R. W. (2005). A comprehensive conceptualization of post-adoptive behaviors associated with information technology enabled work systems. *MIS Quarterly, 29*(3), 525–557.

Kim, S., Jin, G. Z., & Lee, E. (2026). *Does generative AI crowd out human creators? Evidence from Pixiv* (NBER Working Paper No. 34733). National Bureau of Economic Research.

Liang, H., Saraf, N., Hu, Q., & Xue, Y. (2007). Assimilation of enterprise systems: The effect of institutional pressures and the mediating role of top management. *MIS Quarterly, 31*(1), 59–87.

Melville, N., Kraemer, K., & Gurbaxani, V. (2004). Information technology and organizational performance: An integrative model of IT business value. *MIS Quarterly, 28*(2), 283–322.

National Center for O\*NET Development. (2026). *O\*NET database* (Version 29.1) [Data set]; ESCO crosswalk. Retrieved October 4, 2026. Creative Commons Attribution 4.0.

Rai, A., Constantinides, P., & Sarker, S. (2019). Next-generation digital platforms: Toward human–AI hybrids. *MIS Quarterly, 43*(1), iii–ix.

Statistics Canada. (2026). *Job vacancies by occupation* (Table 14-10-0444; NOC 2021) [Data set]. Retrieved October 4, 2026. Statistics Canada Open Licence.

Susarla, A., Gopal, R., Thatcher, J. B., & Sarker, S. (2023). The Janus effect of generative AI: Charting the path for responsible conduct of scholarly activities in information systems. *Information Systems Research, 34*(2), 399–408.

Tambe, P., & Hitt, L. M. (2012). The productivity of information technology investments: New evidence from IT labor data. *Information Systems Research, 23*(3-part-1), 599–617.

U.S. Census Bureau. (2026). *Business Trends and Outlook Survey (BTOS), sector estimates* [Data set]. Retrieved October 4, 2026.

Webb, M. (2020). *The impact of artificial intelligence on the labor market* [Working paper]. SSRN. https://ssrn.com/abstract=3482150

Zhou, E., & Lee, D. (2024). Generative artificial intelligence, human creativity, and art. *PNAS Nexus, 3*(3), Article pgae052.

Zhu, K., & Kraemer, K. L. (2005). Post-adoption variations in usage and value of e-business by organizations: Cross-country evidence from the retail industry. *Information Systems Research, 16*(1), 61–84.
