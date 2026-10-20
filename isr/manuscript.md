---
title: "Who Profits from Large Language Models? An Appropriability Theory of Value Capture along the AI Value Chain"
---

**Abstract**

Adopters of large language models (LLMs) report substantial productivity gains, yet profit is hard to locate at either end of the value chain. Developers post operating losses that exceed their revenue, and the margins of adopting firms show little systematic response. We argue that this pattern follows from appropriability and need not be read as a measurement failure. Drawing on competitive-equilibrium reasoning, vertical-differentiation models, and the profiting-from-innovation framework, we model three positions in the LLM value chain: the frontier developer, the API adopter, and the complement builder. We show that an API adopter earns no economic profit from the model itself, that the developer's rent is proportional to its quality lead and disappears as rivals catch up, and that complement builders earn rents only from co-specialized organizational capital. The central result is that this rent lasts only until rivals imitate the capital or until the developer itself productizes the use, so that an adopter's profitable window depends on its supplier as well as on its competitors. As illustration, we then relate measurable counterparts of the theory to public leaderboard, endpoint-price, and SEC filing data. A lab's flagship price is positively associated with its quality lead, and firms that launch a dated first-party AI product show a higher operating margin afterward. These patterns are consistent with the theory, but the samples are small, and the data cannot establish that the margin increment decays or separate it from alternative explanations. The evidence is illustrative and does not test the theory.

**Key words:** large language models; generative AI; IT business value; appropriability; quasi-rents; complementarities; organizational capital; general-purpose technology

# 1. Introduction

Within three years of the public release of the first widely used chat-based large language model, LLMs had been built into office software, customer service, software development, and search. Controlled studies had documented productivity gains of 14 to 55 percent on affected tasks (Brynjolfsson et al. 2025, Noy and Zhang 2023, Peng et al. 2023, Dell'Acqua et al. 2023), while the firms that develop the models were reporting operating losses on a scale with few precedents in the history of technology. Practitioners often describe this as a puzzle: the technology evidently works, nearly everyone is buying it, and nobody can find the profit.

Information systems researchers will recognize the puzzle. It is the profitability half of the IT productivity paradox (Brynjolfsson 1993, Hitt and Brynjolfsson 1996), and it has reappeared in much the same form with each general-purpose technology since the mainframe. In this paper we argue that the puzzle has a stable answer that follows from standard economics, and that LLMs offer an unusually clean setting in which to state the answer and examine it. The answer is that value from a general-purpose technology is captured only where it is appropriable, and that appropriability is a property of the relationship between the technology and firm-specific complements, not of the technology alone. An LLM accessed through a public API is available to every firm in an industry on identical terms. Under competition, no firm then earns an economic profit from using it, because each firm's gain is bid away in price and passes to consumers. Profit arises at two other points in the chain. It arises with the frontier developer, in proportion to the developer's quality lead over the best alternative and for as long as the lead lasts. It also arises with adopters that combine the model with organizational capital that rivals lack and cannot quickly build, again for as long as imitation takes.

Each of these claims is familiar in isolation. Hitt and Brynjolfsson (1996) showed that IT can raise productivity and consumer surplus while leaving profitability unchanged. The resource-based view of IT holds that only imperfectly imitable IT-enabled capabilities confer sustained advantage (Mata et al. 1995, Bharadwaj 2000, Piccoli and Ives 2005). Teece (1986) identified appropriability regimes and co-specialized complementary assets as the determinants of who profits from an innovation. Models of vertical differentiation, vertical chains, and platforms with complementors (e.g., Mussa and Rosen 1978, Spengler 1950, Rochet and Tirole 2003) already tell us that surplus in a layered market is shared according to quality differences and competitive conditions at each layer. We do not claim a new theorem about any of these mechanisms, and we use them as the benchmark for what follows.

What this benchmark leaves out is a feature of the LLM value chain that sets it apart from most earlier technologies. In the standard account, an adopter's complement rent is threatened by one force, imitation by rival adopters, which takes time because organizational capital is slow to build. For LLMs there is a second force. The supplier of the input can itself move into the adopter's layer. The developer sells the model on posted terms to the adopter and to the adopter's competitors, sees how it is used through the interface, and is able to productize a successful use and sell it to everyone. Research on platform owners entering complementors' markets suggests that this kind of entry is both common and consequential (Gawer and Henderson 2007, Zhu and Liu 2018). Its implication for rent has not been put into the appropriability framework. If the use is productized, the adopter's co-specialized capital becomes a commodity before rivals could have copied it, and the window in which the rent is earned shortens.

The central result of the paper, Proposition 5, formalizes this. When a vendor productizes an adopter's use at rate $\eta$, independent of imitation by rivals, the adopter's expected complement rent falls strictly in $\eta$, so that the rent depends on two clocks and not one. Taken with the benchmark results, this gives a fuller account of where profit appears. API adopters earn nothing from the model itself (Proposition 1). Complement builders earn a rent for as long as both rival imitation and vendor productization are held off (Propositions 2 and 5). The developer earns a rent in proportion to its quality lead, until rivals close it (Proposition 3). The remainder passes to consumers (Proposition 4). The result is deliberately simple, and it takes the rate $\eta$ as given. Section 4.5 then lets the developer choose $\eta$ and shows how contract terms that limit its use of adopters' data change that choice and, through it, the adopter's incentive to invest. How far an adopter can lower $\eta$ through other means, such as the choice of what to build, we leave to future work.

We make three contributions. First, Proposition 5 adds vendor encroachment to the appropriability account of IT value and shows that, for a technology whose supplier can enter the adopter's layer, the adopter's profitable window depends on the supplier's behavior as well as on rivals'. Propositions 6 and 7 extend the result by endogenizing $\eta$, and they turn contractual choices about data use, fine-tuning ownership, and deployment into strategic decisions of the kind that Section 7.2 discusses. Second, we place that result in an integrated benchmark across the developer, the adopter, and the consumer, with appropriability defined ex ante as expected imitation lag and cost, which yields testable constructs (quality lead, imitation lag, and organizational capital) that can be measured from public sources. Third, we provide illustrative evidence on these constructs from leaderboard, endpoint-price, and regulatory filing data. The evidence does not bear on Proposition 5 itself and is limited, and we state what it cannot show. For practice, the theory replaces the question that dominates managerial discussion of AI, namely how much to invest, with the question it identifies as decisive: what does the firm own that the model cannot supply, and how long will it take competitors, and the model's own supplier, to own it as well?

The paper proceeds as follows. Section 2 reviews the relevant literatures and the public financial record of frontier developers. Section 3 defines the constructs. Section 4 presents the model and states the propositions, with proofs in Appendix A. Section 5 maps the model to data and states its empirical implications, and Section 6 presents illustrative evidence. Section 7 discusses implications, boundary conditions, and limitations, and Section 8 concludes.

# 2. Theoretical Background

## 2.1 The profitability paradox

The IT productivity paradox contains two questions that the literature has not always kept apart. The first is Solow's (1987) original observation about aggregate productivity, which has a largely settled explanation in mismeasurement and in the lagged accumulation of expensed intangible complements (Griliches 1994, Brynjolfsson and Hitt 2003, Brynjolfsson et al. 2021). The second concerns profitability. Even where IT demonstrably raises productivity, it is weakly related to firm profit. Hitt and Brynjolfsson (1996) separated productivity, profitability, and consumer surplus, and found that IT raised the first and the third but left the second unchanged, which they attributed to competition passing IT gains through to consumers. Later work on IT business value has mostly treated the weak profit link as a measurement problem to be solved with better data. We take the other route and treat it as a prediction to be derived. The profitability component is also the one that LLMs reproduce.

## 2.2 Complementarity and the resource-based view of IT

The resource-based view holds that sustained advantage requires resources that are valuable, rare, imperfectly imitable, and non-substitutable (Barney 1991, Peteraf 1993). Applied to IT, the argument is that technology itself rarely confers advantage because it can be purchased, while IT-enabled capabilities embedded in organizational routines can (Clemons and Row 1991, Mata et al. 1995, Bharadwaj 2000, Piccoli and Ives 2005). The economic foundation is complementarity (Milgrom and Roberts 1990). Bresnahan et al. (2002) documented complementarity among IT, workplace reorganization, and skills, and Brynjolfsson et al. (2002) estimated that the market value of IT-intensive firms reflects organizational capital worth roughly ten times the hardware. Imperfect imitability has identifiable sources: organizational capital accumulates through path-dependent processes subject to time-compression diseconomies (Dierickx and Cool 1989), and causal ambiguity protects it from copying (Lippman and Rumelt 1982). A well-known weakness of this literature is tautology, since any advantage that persists can be redescribed as inimitable after the fact. We address this in Section 3 by defining appropriability ex ante.

## 2.3 Schumpeterian rents and appropriability

Under competitive equilibrium with free entry, price equals minimum average cost and economic profit is zero. Schumpeter (1934, 1942) located profit in innovation: the innovator earns a temporary rent equal to the gap between price and its own cost until imitation closes the gap. Marshall (1890) called such returns quasi-rents. Teece (1986) specified who captures them. Innovators profit when the appropriability regime is tight or when they control co-specialized complementary assets. Nordhaus (2004) estimated that innovators in the United States capture roughly two percent of the social value of their innovations. For a general-purpose technology (Bresnahan and Trajtenberg 1995) the framework applies twice, once to the developer, whose innovation is the technology, and once to each adopter, whose innovation is a co-specialized use of it.

## 2.4 Vertical chains, platforms, and complementors

The question of who captures surplus in a layered market has been studied extensively outside IS, and our setting borrows from that work in three ways. First, vertical differentiation models show that a quality leader can price above its rival only by the amount buyers value the quality difference, so that its margin is proportional to the lead and falls to zero when the lead does (Mussa and Rosen 1978, Shaked and Sutton 1982). Our developer rent in Proposition 3 is an application of this logic, with the lead measured on public leaderboards. Second, the literature on vertical chains, beginning with Spengler (1950), analyzes how margins are divided among successive layers. Our division-of-surplus result (Proposition 4) is a decomposition of this kind. It is accounting in nature, and its content comes from how each term moves with the lead, the imitation lag, and downstream competition. Third, work on platforms and complementors shows that platform owners can enter complementors' markets and that entry shortens the complementors' profitable window (Gawer and Henderson 2007, Zhu and Liu 2018, Rochet and Tirole 2003). We use this in Proposition 5, where a developer's productization of a use reduces the expected rent of the complement builder that created it.

Against this background, the contribution of the present paper is not a new result about any single layer. It is the combination of these layers, with ex ante defined appropriability at each, applied to a technology for which the key state variables are observable and for which the empirical record is now long enough to look at.

## 2.5 Evidence on large language models

LLM evidence to date has concentrated at the task level and at the developer level, with little at the level of firm profit. Field and laboratory studies report large productivity effects: Brynjolfsson et al. (2025) find a 14 percent increase in issues resolved per hour among customer-support agents; Noy and Zhang (2023) report a 40 percent reduction in time spent on professional writing tasks; Peng et al. (2023) report 55 percent faster task completion among programmers; and Dell'Acqua et al. (2023) find gains of 25 to 40 percent on consulting tasks that lie within the model's capability frontier. Eloundou et al. (2024) estimate that a majority of occupations have at least some tasks exposed to LLMs. Agrawal et al. (2018, 2022) frame AI as lowering the cost of prediction, so that value accrues to owners of complements, and Bommasani et al. (2021) characterize foundation models as a shared substrate. At the level of the adopting organization the evidence is thinner and less favorable. Linking Danish adoption surveys to administrative records, Humlum and Vestergaard (2025) estimate precise null effects of AI chatbots on earnings and recorded hours two years after adoption, even where employers invested heavily in adoption.

## 2.6 The public record on frontier developers

Three regularities were visible before systematic study. Frontier quality is matched by rivals within months. The inference price of a given capability has fallen by more than an order of magnitude per year. And frontier developers report losses while raising capital at valuations that presuppose future profit. Table 1 collects the audited and company-disclosed figures that are available for 2024 to 2026.

Revenue is large and growing. OpenAI's 2025 operating loss of \$20.9 billion on \$13.1 billion of revenue was driven by \$19.2 billion of research and development. Payments to Microsoft alone, \$17.2 billion, equal about half of its \$34 billion of total costs and expenses. The price of reaching a fixed benchmark score has fallen by roughly 5 to 10 times per year for models on the price-performance frontier (Cottier et al. 2025, Gundlach et al. 2026). The decline is steepest in the highest performance bin, about 31 times per year against 1.7 times in the lowest, while the cost of running the current best model has risen by 3 to 18 times per year (Gundlach et al. 2026). OpenAI's gross margin nonetheless rose from 28 to 43 percent between 2024 and 2025, so over that interval serving cost fell faster than price.

**Table 1. Frontier-developer financials, 2024 to 2026 (USD billions unless noted)**

| Firm / metric | 2024 | 2025 | 2026 (latest) |
|:---|---:|---:|---:|
| OpenAI revenue | 3.70 | 13.07 | ≈40 run-rate (Aug.) |
| OpenAI cost of revenue | 2.65 | 7.50 | n/a |
| OpenAI gross margin | 28.4% | 42.6% | n/a |
| OpenAI research and development | 7.81 | 19.18 | n/a |
| OpenAI sales and marketing | 1.11 | 5.73 | n/a |
| OpenAI general and administrative | 0.91 | 1.57 | n/a |
| OpenAI operating result | −8.78 | −20.92 | n/a |
| OpenAI payments to Microsoft | n/a | 17.2 | n/a |
| Anthropic annualized run-rate | ≈1 (Dec.) | ≈9 (Dec.) | 47 (May) |

*Notes.* OpenAI figures for 2024 and 2025 are taken from audited financial statements reported by Zitron (2026) and line items as presented by MLQ (2026). The 2025 net loss of \$38.5 billion includes a \$41.55 billion non-cash charge related to the for-profit conversion, which is excluded here. Other sources place 2025 gross margin at 33 percent (Sacra 2026), which suggests definitional differences in cost of revenue. The 2026 OpenAI figure and all Anthropic figures are unaudited annualized run-rates (latest month × 12) from company disclosures and press reports (Sacra 2026, SaaStr 2026). Anthropic books cloud-reseller revenue gross, so its run-rates are not comparable with OpenAI's booked revenue. The table is illustrative and does not enter any regression.

These figures are too coarse to test the theory, and they should not be read as doing so. Run-rate is not profit, and a hyperscaler's AI profit is not a developer's rent. Their role in this paper is to motivate the developer half of the theory and to fix orders of magnitude. The formal tests appear in Section 6.

# 3. Constructs

## 3.1 Three positions in the LLM value chain

The theory distinguishes three positions, each defined by the actor's relationship to the model.

The *frontier developer* trains and serves a model whose measured quality exceeds that of the best alternative. Its rent depends on the size and duration of its quality lead.

The *API adopter* accesses a model through a public interface at a posted price, on the same terms as every competitor, and deploys it without firm-specific complementary investment beyond routine integration. For this adopter the model is a commodity input.

The *complement builder* combines a model with organizational capital that competitors do not possess: proprietary data, proprietary workflows, distribution, and evaluation and governance capabilities. Its rent depends on how long competitors need to accumulate equivalent capital.

The positions form a lifecycle. A frontier model becomes a commodity when competitors match its quality, and a proprietary use becomes a commodity when vendors productize it or when the underlying organizational capital diffuses. A single legal entity may occupy more than one position. Microsoft, for example, holds an equity claim on future model leads, supplies the compute that sits outside the three-way split in Section 4, and sells a bundled product (Copilot) that is a complement-builder's offering. Consolidated operating income is therefore not developer rent.

## 3.2 Appropriability defined ex ante

We define the appropriability of an investment as the expected duration and cost of imitation by a competitor, assessed at the time of investment. Defining the construct before outcomes are observed is what makes the theory falsifiable. A complement builder that invests in proprietary data and workflow integration and then fails to earn a rent is evidence against the theory. It cannot be rescued by reclassifying the investment as a commodity after the fact.

## 3.3 Adopter-side rents are rents to organizational capital

A purchased input cannot earn its purchaser a rent, because any firm can purchase it. What earns a rent is the firm-specific asset that raises the model's marginal product above what competitors can achieve with the same model. The LLM case sharpens this point, since the model's own contribution is nearly identical across adopters: the same weights, the same API, and the same price.

# 4. Model and Propositions

## 4.1 Environment

Consider a downstream industry with a continuum of firms indexed by $j$, producing a homogeneous good sold at price $p$. Firm $j$'s output is

$$Y_j = A\,F\big(K_j,\,N_j,\,L_j,\,\varphi(L_j,O_j)\big), \tag{1}$$

where $K$ and $N$ are capital and labor, $L$ is LLM usage purchased at a posted price $p_L$, $O$ is firm-specific organizational capital that is co-specialized with the model, and $A$ is a common technology parameter. The function $F$ is increasing, concave, and homogeneous of degree one. The function $\varphi$ captures complementarity: $\varphi(L,0)=0$, and $\varphi$ is supermodular, so that the marginal product of $L$ rises with $O$ and vice versa. The third argument of $F$ is the model's commodity contribution, available to any firm that buys $L$. The fourth is the contribution that arises only in combination with $O$.

Organizational capital is built at a convex cost $g(O)$ subject to time-compression diseconomies. A competitor can replicate it only after a lag $\tau_O>0$ and at a cost $g^m(O)\ge g(O)$. Free entry drives $p$ to the minimum average cost of the marginal firm, and firms discount at rate $\rho$.

Upstream, models are vertically differentiated by quality $\theta$. The frontier developer holds a lead $\Delta\theta(t)=\theta_{\text{lead}}(t)-\theta_{\text{second}}(t)$ over the best alternative. Inference is supplied at a marginal cost $m$ common to developers with comparable infrastructure. A frontier model costs $F_T$ to train and requires developer organizational capital $O_{\text{dev}}$, built at cost $g(O_{\text{dev}})$. A competitor closes the quality gap only after a lag $\tau_{\text{dev}}$ and at cost $g^m(O_{\text{dev}})\ge g(O_{\text{dev}})$. Compute is bought from its owners at market prices and is a factor payment, not a component of developer rent.

Table 2 lists the notation.

**Table 2. Notation**

| Symbol | Meaning |
|:---|:---|
| $p$, $p_L$ | Product price; posted price of LLM usage |
| $L_j$, $O_j$ | LLM usage and co-specialized organizational capital of firm $j$ |
| $\varphi(L,O)$ | Complementarity term, with $\varphi(L,0)=0$ |
| $g(O)$, $g^m(O)$ | Cost of building $O$; cost to a rival of replicating $O$ |
| $\tau_O$, $\tau_{\text{dev}}$ | Imitation lag for adopter capital; catch-up lag for developer quality |
| $\Delta\theta(t)$ | Developer's quality lead over the best alternative |
| $m$, $\kappa$ | Marginal cost of inference; price premium per unit of lead |
| $q(t)$ | Inference demand served by the developer |
| $F_T$, $O_{\text{dev}}$ | Training cost per frontier model; developer organizational capital |
| $\rho$ | Discount rate |
| $\eta$ | Rate at which a vendor productizes a complement builder's use (Propositions 5 to 7) |
| $\mu$, $r$ | Rate at which rivals imitate $O_j$ (Section 4.5); $r=\rho+\mu$ |
| $s$, $K(s)$ | Contractual protection against productization; developer's cost curvature, increasing in $s$ |
| $R$, $\phi$ | Rent flow $(p-c_j)q_j$; share of its present value the developer gains by productizing |

## 4.2 Propositions

We state the propositions once here. Proofs are in Appendix A.

**Proposition 1 (Adopter zero profit).** In a competitive industry with $O_j=0$ for all $j$, the economic profit attributable to LLM usage is zero for every adopter. An improvement in the model or a fall in $p_L$ lowers the product price by the full reduction in minimum average cost, so the productivity gain accrues entirely to consumers.

**Corollary 1 (Compulsory adoption).** A firm that sets $L_j$ below the equilibrium level has an average cost above $p$ and earns negative profit. Adoption is necessary for non-negative profit, but it is not sufficient for positive profit.

**Proposition 2 (Complement rent).** An adopter with $O_j>0$ earns the economic profit

$$\Pi_j=\int_0^{\tau_O}(p-c_j)\,q_j\,e^{-\rho t}\,dt-g(O_j), \tag{2}$$

where $c_j<p$ is its unit cost given $\varphi(L_j,O_j)>0$ and $q_j$ is its output. The profit is increasing in $\tau_O$ and in $g^m(O_j)-g(O_j)$, decreasing in $g(O_j)$, and zero for any level of spending on $L_j$ if $O_j=0$. The rent flow vanishes at $t=\tau_O$.

**Corollary 2 (Conversion).** At $\tau_O$ the co-specialized use is available to all firms at a common effective cost and meets the definition of a commodity input. Every complement rent is therefore transient, and sustained adopter-side profit requires a sequence of complementary investments.

**Proposition 3 (Developer rent).** The frontier developer earns the economic profit

$$\Pi_{\text{dev}}=\int_0^{\tau_{\text{dev}}}\kappa\,\Delta\theta(t)\,q(t)\,e^{-\rho t}\,dt-F_T-g(O_{\text{dev}}), \tag{3}$$

where $\kappa>0$ converts a unit of quality lead into a price premium over $m$. The profit is positive if and only if the discounted value of the lead exceeds training and organizational cost. It is increasing in $\Delta\theta$, in $\tau_{\text{dev}}$, and in $g^m(O_{\text{dev}})-g(O_{\text{dev}})$, and the premium converges to zero as $\Delta\theta(t)\to 0$.

**Corollary 3 (Release sequence).** Sustained developer profit over a horizon longer than one catch-up lag requires successive frontier releases at intervals no longer than $\tau_{\text{dev}}$, so that a new lead opens before the previous one closes. A developer that stops advancing the frontier reverts to pricing at $m$.

**Corollary 4 (Measured losses).** Reported developer profit understates economic profit by the unamortized balance of outlays whose benefits outlast the accounting period. That balance is small for model-specific training, whose economic life is bounded by $\tau_{\text{dev}}$, and large only for durable components of $O_{\text{dev}}$ such as compute contracts, infrastructure, talent, and distribution. Reported losses therefore overstate economic losses by at most the durable share of development spending.

**Proposition 4 (Division of surplus).** Let $S$ be the surplus created per period by the LLM in the downstream industry, net of payments for compute. Then

$$S=S_{\text{dev}}+S_{\text{comp}}+\Delta CS,\qquad S_{\text{dev}}=\kappa\Delta\theta\,q,\quad S_{\text{comp}}=\lambda(p-\bar c)\bar q, \tag{4}$$

where $S_{\text{dev}}$ is the developer's rent, $S_{\text{comp}}$ is the aggregate rent of complement builders, $\Delta CS$ is the consumers' gain, $\lambda$ is the fraction of adopters currently inside an imitation lag, and $(p-\bar c)\bar q$ is their average rent. API adopters as a class receive nothing. The developer's share is increasing in $\Delta\theta$, the complement builders' share is increasing in $\tau_O$ and $\lambda$, and the consumers' share is the residual, which approaches $S$ as downstream competition intensifies.

**Proposition 5 (Encroachment).** Suppose that, independently of imitation, a vendor productizes a complement builder's use at a constant rate $\eta\ge 0$, after which the use is a commodity. Holding $q_j$ and $c_j$ fixed, the expected complement rent is

$$E[\Pi_j]=(p-c_j)q_j\frac{1-e^{-(\rho+\eta)\tau_O}}{\rho+\eta}-g(O_j), \tag{5}$$

which is strictly decreasing in $\eta$.

## 4.3 Comparative statics

Five predictions follow, and they are the ones the empirical work in Sections 5 and 6 can address.

1. Realized developer prices for inference rise with $\Delta\theta$ and fall toward serving cost as $\Delta\theta\to 0$ (Proposition 3).
2. Developer rent is shortened by open-weight releases, compressed release intervals, and falling serving cost (Proposition 3 and Corollary 3).
3. Adopter-side profit is predicted by a dated first-party product, which proxies $O>0$, and not by pooled exposure to LLMs (Propositions 1 and 2).
4. Industries with shorter $\tau_O$, or with more vendor encroachment, show weaker associations between AI use and profit (Propositions 2 and 5).
5. As downstream competition intensifies, the AI–profit association weakens while the AI–productivity association is unaffected (Propositions 1 and 4).

Predictions 4 and 5 are not tested here. Proposition 5 is also untested, but it bears directly on the LLM setting and on managerial choices about data-use terms and fine-tuning ownership, which we take up in Section 7.

## 4.4 What is specific to LLMs

A fair question is whether anything in the model is specific to LLMs, or whether the same propositions would describe any layered technology market. The structure is general. What is specific is the combination of values and measurement conditions that LLMs bring to it. Marginal inference cost $m$ is low relative to the cost of producing a frontier model $F_T$, so that profit depends almost entirely on the premium $\kappa\Delta\theta$. The catch-up lag $\tau_{\text{dev}}$ is short, on the order of three to four months for open-weight models relative to the closed frontier (Emberson 2025, Epoch AI 2026), which places the developer close to the zero-rent corner of Proposition 3. The same model serves both the complement builder and its competitors on posted terms, which is what makes the adopter's position commodity-like in the first place. And developers can and do move into the complement layer, which is the situation Proposition 5 describes. In this sense the theory is less a new mechanism than a calibration of known mechanisms to a market in which the state variables can be observed. We return to the limits of this claim in Section 7.3.

## 4.5 Endogenous encroachment and contract protection

Proposition 5 treats the productization rate $\eta$ as given. Here we let the developer choose it and ask how contract terms affect the choice. The analysis is a reduced-form extension. It adds the minimum structure needed to endogenize $\eta$, and it should be read as a first formalization and not as a full model of vendor behavior.

*Setup.* Let $R=(p-c_j)q_j$ be the adopter's rent flow. For tractability, we replace the deterministic imitation lag $\tau_O$ by an exponential one: rivals imitate $O_j$ at rate $\mu$, so that the mean lag is $1/\mu$. Write $r=\rho+\mu$. The adopter's expected rent from Proposition 5 then becomes $R/(r+\eta)-g(O_j)$, with the same comparative statics. A contract specifies protection $s\in[0,1)$, which limits the developer's use of the adopter's data, fine-tuning, or deployment information. The developer exerts effort $e$ at cost $(k/2)e^2$, but only the fraction $1-s$ of that effort converts into productization, so that $\eta=(1-s)e$. The cost of achieving a rate $\eta$ is therefore $(K/2)\eta^2$ with $K(s)=k/(1-s)^2$, which increases in $s$. When it productizes the use, the developer gains the present value $G=\phi R/r$, where $\phi\in(0,1]$ is the share of the rent's present value $R/r$ that it captures, and the rest passes to consumers. The developer chooses $\eta$ to maximize

$$J(\eta)=\frac{G\eta-K\eta^2/2}{r+\eta}, \tag{6}$$

the expected present value of its gain net of effort cost, which accrues until productization or imitation ends the opportunity.

**Proposition 6 (Equilibrium productization).** The developer's problem has a unique interior solution,

$$\eta^*=-r+\sqrt{r^2+2Gr/K}. \tag{7}$$

The rate $\eta^*$ is increasing in $G$ (and so in $R$ and $\phi$) and decreasing in $K$ (and so in $s$). For a given $G$, it is increasing in $r$: the faster rivals are expected to imitate, the faster the developer productizes.

**Proposition 7 (Contract protection and complement investment).** The adopter's expected rent $R/(r+\eta^*(s))-g(O_j)$ is increasing in $s$. Consequently, the set of organizational-capital investments that satisfy $R/(r+\eta^*)\ge g(O_j)$ expands as $s$ rises, and some investments that would not be made without protection are made with it.

Proposition 6 says that imitation by rivals and encroachment by the vendor are strategic complements. A shorter expected imitation lag makes the developer move sooner, so that the two threats to the adopter's rent compound. Proposition 7 is the hold-up logic of Klein et al. (1978) and Grossman and Hart (1986) applied to the LLM supply relationship. An adopter that fears productization under-invests in the co-specialized capital that generates its rent, and contract terms that raise the developer's cost of encroaching restore some of that investment.

Whether such protection is actually written is a separate question. The adopter's willingness to pay for a move from $s_0$ to $s_1$ is $R/(r+\eta_1^*)-R/(r+\eta_0^*)$. The developer's loss is $K_1\eta_1^*-K_0\eta_0^*$, because its value at the optimum is $J^*=G-K\eta^*$. A contract can be agreed only if the first exceeds the second. Table 4 gives a numerical illustration. Protection clears for uses with small rents and fails for uses with large rents, because the developer's gain from productizing grows with the rent. The pattern depends on the parameters and is not general, since in a simulation with randomly drawn parameters the willingness to pay fell short of the developer's loss in about five percent of the draws. We therefore offer it as an illustration and not as a proposition. If it held more generally, it would imply that the uses most worth protecting are the ones least likely to be protected.

**Table 4. Willingness to pay for protection versus the developer's loss (illustration; $r=0.3$, $\phi=0.8$, $k=1$, $s$ raised from 0 to 0.5)**

| $R$ | $\eta^*$ ($s=0$) | $\eta^*$ ($s=0.5$) | Willingness to pay | Developer's loss | Contract agreed |
|---:|---:|---:|---:|---:|:---|
| 0.5 | 0.643 | 0.239 | 0.398 | 0.311 | Yes |
| 1 | 1.000 | 0.400 | 0.659 | 0.600 | Yes |
| 2 | 1.514 | 0.643 | 1.017 | 1.060 | No |
| 4 | 2.248 | 1.000 | 1.507 | 1.752 | No |
| 8 | 3.290 | 1.514 | 2.182 | 2.765 | No |

The extension has clear limits. The rate $\eta$ is constant and chosen by a single developer. We do not model competition among vendors for the same use, the adopter's responses (concealing the use, moving to another vendor), or bargaining over the contract. The functional form $K(s)=k/(1-s)^2$ is a convenience, and the share $\phi$ is a reduced-form parameter that does not model how the developer earns from a productized offering. Contract terms are not publicly observed, so the propositions cannot be examined with the data in Section 6.

# 5. Empirical Counterparts and Implications

## 5.1 Mapping model objects to data

We assign each model object an empirical counterpart in public data. The mapping is interpretive. We do not recover structural parameters, and Table 1 figures are not regression inputs.

**Table 3. Model objects and empirical counterparts**

| Model object | Empirical counterpart | Source |
|:---|:---|:---|
| $\Delta\theta$ | Gap between the top-ranked and second-ranked lab on the Arena overall leaderboard | Chiang et al. (2024) |
| $\kappa\Delta\theta$ | Provider-mean blended flagship inference price, not a GAAP margin | OpenRouter (2026) |
| $\tau_{\text{dev}}$ | Time from a frontier release to the first competitor release matching its score | Arena series |
| $\varphi(L,O)$ with $O_j>0$ | Dated general-availability (GA) year of a first-party AI product | Hand-coded from public product dates |
| $O_j=0$ | Pooled API use or mention without a coded GA year | SEC filings |
| Adopter profit | Operating margin | SEC EDGAR XBRL company facts |
| Compute payments | Factor payment outside the three-way split | Table 1 (illustrative) |

## 5.2 Empirical implications

The comparative statics in Section 4.3 yield five testable implications, stated below as hypotheses. We state all five to show how the theory would be tested, but the public data available to us bear on only some of them. H3 and H4 are examined in Section 6, together with a lab-month association that is related to H1a and H1b but does not test them. H1a, H1b, and H2 are stated for future work.

*Implications examined in Section 6*

**H3.** Firms that ship a dated first-party AI product earn a higher operating margin after the GA year than before, relative to firms with no such product. Treatment is the calendar year of GA (for example, Copilot for Microsoft 365 in 2023, Firefly in 2023, Now Assist in 2023, Cortex in 2023, AIP in 2023, watsonx in 2023, Charlotte AI in 2023, Gemini for Workspace in 2024, Agentforce in 2024, Bits AI in 2024, and analogues), not a time-invariant bundle indicator.

**H4.** The within-firm margin increment after GA declines as event time lengthens. Disconfirmation is a flat or rising post-GA path, or a difference between the first post-GA year and the last post-GA bin that cannot be distinguished from zero.

*Implications stated for future work*

**H1a.** Within a given flagship model, realized inference price rises with the model's own quality lead and falls when a competitor closes it. The dependent variable is the OpenRouter provider-mean blended rate across endpoints for that model, which is a realized multi-provider price and not a single list card. Where endpoints are unpublished, the change-point list price is used as a fallback. Disconfirmation is the absence of a within-model price response to changes in the model's own lead.

**H1b.** Across releases, a model's launch price is increasing in its quality lead at launch. Because proprietary list prices rarely change after launch (Gundlach et al. 2026), the premium in Proposition 3 may attach mainly at release and decay as cheaper successors arrive, not through repricing. H1b captures this channel. Disconfirmation is the absence of any relationship between launch price and lead at launch.

**H2.** Among adopters, pooled exposure to LLMs, meaning use or mention without a dated first-party GA, does not predict economic profit. Disconfirmation is a time-invariant exposure indicator that predicts operating margin in the pooled cross-section.

# 6. Illustrative Evidence

This section relates the constructs of Section 5 to public data. It is not a test of the theory: the samples are small, the proxies are coarse, and several hypotheses are not tested. Its purpose is to show that the constructs can be measured and to indicate whether the data are consistent with the predictions.

The developer panel combines Arena overall leaderboard snapshots (Chiang et al. 2024) with OpenRouter endpoint prices (OpenRouter 2026). It contains 171 lab-months with a price, of which 102 have at least one live endpoint and 69 use the list-price fallback. The adopter panel is drawn from SEC EDGAR XBRL company facts (SEC 2026) and covers 81 firms and 520 firm-years, with staggered GA-year treatment for 21 firms. GA years are coded by hand from public product dates.

On the developer side, we regress log realized price on the lab's lead with lab fixed effects and a trend, clustering by lab. On the adopter side, we regress operating margin on a post-GA indicator with firm and year fixed effects, clustering by firm.

## 6.1 Developer side (H1)

*Lab-month association.* Regressing log realized flagship price on the lab's lead with lab fixed effects and a trend gives a coefficient of 0.0099 on the 171 lab-months with list fallback and 0.0068 on the 102 months with at least one live endpoint. Conventional clustered p-values are below 0.001 and 0.017, respectively. With few lab clusters these p-values likely overstate precision (Cameron et al. 2008), and we regard the estimates as suggestive. A first-difference cut on an older list-price snapshot series ($N=1{,}190$) gives a coefficient of 0.0049 (p = 0.081). We read it as directional only and do not use it for H1a or H1b.

*What the lab-month estimates do not show.* They are identified mainly by new releases and so do not isolate the premium on a given model. They should be read as associations between a lab's lead and its flagship price, and not as tests of H1a or H1b. Those tests require a model-month panel and a release-level panel of launch prices, which we do not estimate here.

## 6.2 Adopter side (H2 to H4)

*H2.* We do not report a test of H2 here.

*H3.* The two-way fixed-effects baseline gives a post-GA margin increment of 5.3 percentage points ($\beta=0.053$, $p=0.007$; $N=520$ firm-years, 21 treated firms). Because the treated firms are large software incumbents and treatment is staggered, this estimate may be biased and may reflect non-AI margin trends, so we do not read it as a stand-alone test of H3. An increment carried by the operating-expense ratio, or concentrated among the largest firms, would point to cost reduction or market power and not to a complement rent.

*H4.* In the baseline event study, with $t=-1$ omitted, the coefficient at $t=-2$ is −1.2 percentage points ($p=0.64$), at the GA year +4.4 ($p=0.037$), at $t+1$ +6.1 ($p=0.021$), at $t+2$ +5.3 ($p=0.16$), and at $t+3$ +2.4 ($p=0.59$). The pre-period coefficient is small and not distinguishable from zero. The point estimates peak at $t+1$ and fall afterward, which is the direction the theory predicts. However, the $t+2$ and $t+3$ estimates are imprecise and rest on fewer treated firms, and we do not test the equality of the $t+1$ coefficient and the last post-GA bin. The data are therefore inconclusive on H4, and we do not claim that the margin increment decays. A time-invariant bundle-by-post-2023 difference-in-differences gives a similar coefficient and is retained as a robustness check.

## 6.3 What is and is not identified

Six restrictions bind. First, the realized price is the mean of provider cards on OpenRouter, not a billed invoice and not a GAAP inference margin. Second, endpoint coverage is incomplete (102 of 171 priced months). Third, GA years are coded from public product dates, and they do not measure token spend or retrieval intensity. Fourth, Table 1 figures are illustrative and are not regression inputs. Fifth, two-way fixed-effects estimates under staggered timing can be biased when effects differ across cohorts (Goodman-Bacon 2021), and they rest on parallel trends, which we do not test beyond the pre-GA coefficients in the event study. Sixth, operating margin is an accounting measure and not the economic profit of Proposition 2, and the timing of GA marks the launch of a product, not the start of organizational-capital accumulation.

# 7. Discussion

## 7.1 Contributions

The paper extends IT business value theory (Melville et al. 2004) from the adopting firm to the vertical structure of a general-purpose technology. Modeling the developer, the adopter, and the consumer in one framework lets us say why developer losses, adopter productivity gains, and weak adopter profit effects are observed together. The same account separates the profitability paradox from the productivity paradox and derives the former from the zero-profit condition applied to an input with a common market price. We also provide an ex ante definition of appropriability that applies to developers and adopters alike, which speaks to the tautology charge against resource-based IT research, and we show how a model can be a source of rent at one date and a marginal-cost input at another.

We should be clear about what is not new. The mechanisms in each layer are established in industrial organization and strategy (Section 2.4). What the paper adds is their combination under a single appropriability definition and the specification of measurable counterparts for a technology in which those counterparts are observable.

## 7.2 Implications for practice

For adopters, the central question is not how much to spend on AI but what the firm owns that the model cannot supply, and how long competitors will take to own it too. The theory also says that spending on the model itself is not a source of advantage, since any rival can buy the same model. For developers, the next model is the source of value, not the current one. When leads last only a few months, much of the reported loss is economic (Corollary 4). The valuations of frontier labs are best read as prices for an option on a sequence of future leads and not as capitalized current earnings. For the relationship between the two sides, Propositions 5 to 7 imply that contractual terms covering data use, fine-tuning ownership, and on-premise deployment are strategic decisions, because they affect the rate at which a vendor can productize an adopter's use and so the adopter's incentive to invest in the capital that generates its rent. The illustration in Table 4 suggests that such terms may be hardest to obtain for the most valuable uses, which is a reason for adopters to negotiate them before a use proves valuable and not after.

## 7.3 Boundary conditions and limitations

The theory assumes competitive downstream product markets. Where adopters hold market power, pass-through is incomplete, and commodity LLM use can raise profit. Evidence that IT intensity accompanies rising industry concentration suggests that this case is empirically relevant (Autor et al. 2020, Bessen 2020), and it is also an alternative reading of the margin increment in H3. The theory further assumes that the developer's lead closes. Economies of scale in compute and data flywheels could prevent closure and shift surplus durably toward the developer, and sustained margins without a quality lead, that is, disconfirmation of H1, would indicate that this case dominates.

The model abstracts from uncertainty in training outcomes, from strategic interaction among developers (the lead and the catch-up lag are treated as exogenous), and from purchasable organizational capital. Making the lead endogenous to a training race is the most natural extension, and it is where we would expect a more specifically LLM-based theory to develop. The empirical proxies are imperfect, and misclassification biases the estimated difference between commodity and complementary use toward zero. The adopter sample is small and made up of large software incumbents, so the results should not be generalized to adopters in other industries. Finally, the evidence is observational and cross-sectional in time, over a period in which the technology and its business models are still changing. H1a, H1b, and H2 are not tested here, and the evidence on H4 is inconclusive. The tests reported are best viewed as a first look at the constructs, and they are not a confirmation of the theory.

# 8. Conclusion

LLMs create value, and the theory developed here says where it goes. Adopters that use a model available to every competitor on the same terms pass their gain to consumers. The frontier developer captures a share in proportion to its quality lead, and only until a competitor closes it. Adopters that combine the model with organizational capital that rivals cannot quickly build earn a rent in proportion to how long the building takes, and that rent shrinks if a vendor productizes the use. The remainder goes to consumers, and statistics that pool all three positions report an average close to zero.

The public record makes the developer half of this account visible. Frontier labs combine large booked revenue with large operating losses and pay complement owners for compute. The price of matched capability falls several-fold each year, while the cost of frontier capability rises. Investors nonetheless value the same firms as if a release sequence will continue. These three facts are consistent with a single explanation: competition over a general-purpose input whose quality lead is short and must be bought again with each release. The profitability puzzle that accompanies every general-purpose technology is, on this account, what competition over a common input looks like from the inside.

# Appendix A. Proofs

**Proof of Proposition 1.** With $O_j=0$, $\varphi=0$ and $L$ enters only through the third argument of $F$. Firm $j$'s first-order condition for $L_j$ is

$$pA\frac{\partial F}{\partial L_j}=p_L. \tag{A1}$$

Since $p_L$ and $F$ are common to all firms, every firm chooses the same $L$ per unit of scale, and the marginal revenue product of LLM usage equals its price. By Euler's theorem under constant returns, factor payments exhaust revenue. The payment to $L$ is $p_L L_j$ and contributes nothing to residual profit. Now let the model improve or its price fall, lowering minimum average cost from $c_0$ to $c_1<c_0$. With free entry, price falls from $p_0=c_0$ to $p_1=c_1$, and firm profit is zero before and after. Consumer surplus rises by

$$\Delta CS=\int_{p_1}^{p_0}D(p)\,dp>0, \tag{A2}$$

where $D$ is market demand. The productivity gain is real and appears in industry output and measured total factor productivity, and it accrues entirely to consumers. $\blacksquare$

**Proof of Corollary 1.** If $L_j$ is set below the level that satisfies (A1), the firm's average cost exceeds the minimum average cost of firms that do satisfy it. Since $p$ equals that minimum, firm $j$ earns $p-c_j<0$ per unit. $\blacksquare$

**Proof of Proposition 2.** With $O_j>0$, supermodularity of $\varphi$ lowers firm $j$'s average cost to $c_j<p$, where $p$ is set by the mass of firms with $O=0$. Firm $j$ earns $(p-c_j)$ on $q_j$ units until $\tau_O$, when imitators replicate $O_j$, enter at cost $c_j$, and drive price to $c_j$. Discounting gives the integral in (2). Differentiating (2) with respect to $\tau_O$ gives $(p-c_j)q_je^{-\rho\tau_O}>0$. A larger imitation-cost premium $g^m(O_j)-g(O_j)$ delays imitator entry and so lengthens $\tau_O$. The profit decreases in $g(O_j)$ by construction. If $O_j=0$, then $\varphi=0$ and $c_j$ equals the common cost, so $p-c_j=0$ for any $L_j$ satisfying (A1). Expenditure on $L$ therefore cannot generate a rent without $O$. $\blacksquare$

**Proof of Corollary 2.** At $\tau_O$ imitators hold equivalent $O$, so the cost $c_j$ is available to all, the price falls to $c_j$, and $p-c_j=0$. A rent in later periods requires a new $O'$ with its own lag. $\blacksquare$

**Proof of Proposition 3.** Under Bertrand competition in a vertically differentiated market, the leader prices so that buyers are indifferent between the leader at quality $\theta_{\text{lead}}$ and the runner-up at $\theta_{\text{second}}$ priced at $m$. The leader's margin per unit is therefore proportional to $\Delta\theta(t)$, with $\kappa$ given by buyers' marginal valuation of quality. Before catch-up the leader is the unique supplier at $\theta_{\text{lead}}$ and earns the premium on every unit. At $\tau_{\text{dev}}$ a competitor reaches $\theta_{\text{lead}}$, the premium is competed to zero, and inference is priced at $m$. Differentiating (3) with respect to $\tau_{\text{dev}}$ gives $\kappa\Delta\theta(\tau_{\text{dev}})q(\tau_{\text{dev}})e^{-\rho\tau_{\text{dev}}}>0$. A larger imitation-cost premium $g^m(O_{\text{dev}})-g(O_{\text{dev}})$ delays the competitor's entry and raises $\Pi_{\text{dev}}$. Convergence of the premium follows from the entry condition. $\blacksquare$

**Proof of Corollary 3.** After $\tau_{\text{dev}}$ the premium is zero. A positive flow from $\tau_{\text{dev}}$ onward therefore requires a new lead $\Delta\theta'>0$ to exist, which in turn requires a new release. If the new lead opens after the old one has closed, there is an interval of zero premium. Continuity of the premium stream requires the intervals between releases to be no longer than $\tau_{\text{dev}}$. $\blacksquare$

**Proof of Corollary 4.** An outlay with economic life $T$ enters economic profit as an amortization charge spread over $T$, and enters reported profit in full when incurred. In any period the difference between the two equals the unamortized balance of outlays still inside their lives. For model-specific training the relevant life is the rent window, $T\le\tau_{\text{dev}}$. As $\tau_{\text{dev}}$ shrinks toward one accounting period, the unamortized balance goes to zero and the amortization charge converges to the expensed amount. Only outlays whose life exceeds the period create a gap between reported and economic profit. Because that gap understates profit, reported losses overstate economic losses by the unamortized balance. $\blacksquare$

**Proof of Proposition 4.** Proposition 1 gives API adopters zero. Proposition 3 gives the developer $\kappa\Delta\theta q$, the portion of adopters' cost saving extracted through $p_L$ above $m$. Proposition 2 gives each complement builder $(p-c_j)q_j$ during its lag, and aggregating over the fraction $\lambda$ inside a lag gives the second term. The remainder of the cost saving is passed through in price under free entry and appears as $\Delta CS$. Payments for compute are made at market prices to owners outside the three positions and are netted from $S$ before the split. Equation (4) is therefore an accounting identity once $\Delta CS$ is defined as the residual. Its content lies in the comparative statics: the first term moves with $\Delta\theta$, the second with $\tau_O$ and $\lambda$, and the third absorbs the remainder. $\blacksquare$

**Proof of Proposition 5.** Let productization arrive at rate $\eta$ independently of imitation. The rent flow $(p-c_j)q_j$ continues at time $t<\tau_O$ only if productization has not yet occurred, which has probability $e^{-\eta t}$. The expected discounted rent is therefore

$$\int_0^{\tau_O}(p-c_j)\,q_j\,e^{-\eta t}e^{-\rho t}\,dt=(p-c_j)q_j\frac{1-e^{-(\rho+\eta)\tau_O}}{\rho+\eta}.$$

Subtracting $g(O_j)$ gives (5). The derivative of the integral with respect to $\eta$ equals $-\int_0^{\tau_O}t\,(p-c_j)q_je^{-(\rho+\eta)t}\,dt<0$. $\blacksquare$

**Proof of Proposition 6.** Write $N(\eta)=G\eta-K\eta^2/2$, so that $J=N/(r+\eta)$. The first-order condition $N'(\eta)(r+\eta)=N(\eta)$ reads $(G-K\eta)(r+\eta)=G\eta-K\eta^2/2$, which simplifies to $\eta^2+2r\eta-2Gr/K=0$. This quadratic has exactly one positive root, given by (7). Since $J(0)=0$, $J'(0)=G/r>0$, and $J\to-\infty$ as $\eta\to\infty$, that root is the global maximum on $\eta\ge 0$. Equation (7) shows directly that $\eta^*$ increases in $G$ and decreases in $K$, and $K(s)=k/(1-s)^2$ increases in $s$. For $r$, differentiate (7) with $G$ and $K$ fixed: $\partial\eta^*/\partial r=-1+(r+G/K)/\sqrt{r^2+2Gr/K}$. Because $(r+G/K)^2=r^2+2Gr/K+G^2/K^2>r^2+2Gr/K$, the derivative is positive. Finally, the first-order condition implies $J^*=N'(\eta^*)=G-K\eta^*$, which is used in the text. $\blacksquare$

**Proof of Proposition 7.** By Proposition 6, $\eta^*(s)$ is decreasing in $s$, and $R/(r+\eta)$ is decreasing in $\eta$, so $R/(r+\eta^*(s))$ is increasing in $s$. The investment condition compares this present value with $g(O_j)$, so the set of $O_j$ for which it holds is larger at higher $s$. For any $O_j$ with $R/(r+\eta^*(0))<g(O_j)\le R/(r+\eta^*(s))$, the investment is made only with protection. $\blacksquare$

# References

Agrawal, A., Gans, J., and Goldfarb, A. 2018. *Prediction Machines*. Boston: Harvard Business Review Press.

Agrawal, A., Gans, J., and Goldfarb, A. 2022. *Power and Prediction*. Boston: Harvard Business Review Press.

Autor, D., Dorn, D., Katz, L. F., Patterson, C., and Van Reenen, J. 2020. The fall of the labor share and the rise of superstar firms. *Quarterly Journal of Economics* 135(2):645–709.

Barney, J. 1991. Firm resources and sustained competitive advantage. *Journal of Management* 17(1):99–120.

Bessen, J. 2020. Industry concentration and information technology. *Journal of Law and Economics* 63(3):531–555.

Bharadwaj, A. S. 2000. A resource-based perspective on information technology capability and firm performance. *MIS Quarterly* 24(1):169–196.

Bommasani, R., et al. 2021. On the opportunities and risks of foundation models. Preprint, arXiv:2108.07258.

Bresnahan, T. F., Brynjolfsson, E., and Hitt, L. M. 2002. Information technology, workplace organization, and the demand for skilled labor. *Quarterly Journal of Economics* 117(1):339–376.

Bresnahan, T. F., and Trajtenberg, M. 1995. General purpose technologies: "Engines of growth"? *Journal of Econometrics* 65(1):83–108.

Brynjolfsson, E. 1993. The productivity paradox of information technology. *Communications of the ACM* 36(12):66–77.

Brynjolfsson, E., and Hitt, L. M. 2003. Computing productivity: Firm-level evidence. *Review of Economics and Statistics* 85(4):793–808.

Brynjolfsson, E., Hitt, L. M., and Yang, S. 2002. Intangible assets: Computers and organizational capital. *Brookings Papers on Economic Activity* 2002(1):137–198.

Brynjolfsson, E., Li, D., and Raymond, L. 2025. Generative AI at work. *Quarterly Journal of Economics* 140(2):889–942.

Brynjolfsson, E., Rock, D., and Syverson, C. 2021. The productivity J-curve: How intangibles complement general purpose technologies. *American Economic Journal: Macroeconomics* 13(1):333–372.

Cameron, A. C., Gelbach, J. B., and Miller, D. L. 2008. Bootstrap-based improvements for inference with clustered errors. *Review of Economics and Statistics* 90(3):414–427.

Chiang, W.-L., Zheng, L., Sheng, Y., Angelopoulos, A. N., Li, T., Li, D., Zhang, H., Zhu, B., Jordan, M., Gonzalez, J. E., and Stoica, I. 2024. Chatbot Arena: An open platform for evaluating LLMs by human preference. *Proceedings of the 41st International Conference on Machine Learning*, PMLR 235:8359–8388.

Clemons, E. K., and Row, M. C. 1991. Sustaining IT advantage: The role of structural differences. *MIS Quarterly* 15(3):275–292.

Cottier, B., Snodin, B., Owen, D., and Adamczewski, T. 2025. LLM inference prices have fallen rapidly but unequally across tasks. Epoch AI Data Insights, March. https://epoch.ai/data-insights/llm-inference-price-trends.

Dell'Acqua, F., et al. 2023. Navigating the jagged technological frontier: Field experimental evidence of the effects of AI on knowledge worker productivity and quality. Harvard Business School Working Paper 24-013.

Dierickx, I., and Cool, K. 1989. Asset stock accumulation and sustainability of competitive advantage. *Management Science* 35(12):1504–1511.

Eloundou, T., Manning, S., Mishkin, P., and Rock, D. 2024. GPTs are GPTs: Labor market impact potential of LLMs. *Science* 384(6702):1306–1308.

Emberson, L. 2025. Open-weight models lag state-of-the-art by around 3 months on average. Epoch AI Data Insights, October 30. https://epoch.ai/data-insights/open-weights-vs-closed-weights-models.

Epoch AI. 2026. Open models lag state-of-the-art closed models by 4 months. Epoch AI Data Insights, May 29. https://epoch.ai/data-insights/open-closed-eci-gap.

Gawer, A., and Henderson, R. 2007. Platform owner entry and innovation in complementary markets: Evidence from Intel. *Journal of Economics & Management Strategy* 16(1):1–34.

Goodman-Bacon, A. 2021. Difference-in-differences with variation in treatment timing. *Journal of Econometrics* 225(2):254–277.

Griliches, Z. 1994. Productivity, R&D, and the data constraint. *American Economic Review* 84(1):1–23.

Grossman, S. J., and Hart, O. D. 1986. The costs and benefits of ownership: A theory of vertical and lateral integration. *Journal of Political Economy* 94(4):691–719.

Gundlach, H., Lynch, J., Mertens, M., and Thompson, N. 2026. The price of progress: Price performance and the future of AI. Preprint, arXiv:2511.23455v2.

Hitt, L. M., and Brynjolfsson, E. 1996. Productivity, business profitability, and consumer surplus: Three different measures of information technology value. *MIS Quarterly* 20(2):121–142.

Humlum, A., and Vestergaard, E. 2025. Large language models, small labor market effects. NBER Working Paper 33777, National Bureau of Economic Research, Cambridge, MA.

Klein, B., Crawford, R. G., and Alchian, A. A. 1978. Vertical integration, appropriable rents, and the competitive contracting process. *Journal of Law and Economics* 21(2):297–326.

Lippman, S. A., and Rumelt, R. P. 1982. Uncertain imitability: An analysis of interfirm differences in efficiency under competition. *Bell Journal of Economics* 13(2):418–438.

Marshall, A. 1890. *Principles of Economics*. London: Macmillan.

Mata, F. J., Fuerst, W. L., and Barney, J. B. 1995. Information technology and sustained competitive advantage: A resource-based analysis. *MIS Quarterly* 19(4):487–505.

Melville, N., Kraemer, K., and Gurbaxani, V. 2004. Review: Information technology and organizational performance: An integrative model of IT business value. *MIS Quarterly* 28(2):283–322.

Milgrom, P., and Roberts, J. 1990. The economics of modern manufacturing: Technology, strategy, and organization. *American Economic Review* 80(3):511–528.

MLQ. 2026. Leaked OpenAI financials reveal $21B operating loss on $13B revenue in 2025. June 17. https://mlq.ai/news/leaked-openai-financials-reveal-21b-operating-loss-on-13b-revenue-in-2025/.

Mussa, M., and Rosen, S. 1978. Monopoly and product quality. *Journal of Economic Theory* 18(2):301–317.

Nordhaus, W. D. 2004. Schumpeterian profits in the American economy: Theory and measurement. NBER Working Paper 10433, National Bureau of Economic Research, Cambridge, MA.

Noy, S., and Zhang, W. 2023. Experimental evidence on the productivity effects of generative artificial intelligence. *Science* 381(6654):187–192.

OpenRouter. 2026. Models and endpoint pricing. Accessed September 2026, https://openrouter.ai/models.

Peng, S., Kalliamvakou, E., Cihon, P., and Demirer, M. 2023. The impact of AI on developer productivity: Evidence from GitHub Copilot. Preprint, arXiv:2302.06590.

Peteraf, M. A. 1993. The cornerstones of competitive advantage: A resource-based view. *Strategic Management Journal* 14(3):179–191.

Piccoli, G., and Ives, B. 2005. IT-dependent strategic initiatives and sustained competitive advantage: A review and synthesis of the literature. *MIS Quarterly* 29(4):747–776.

Rochet, J.-C., and Tirole, J. 2003. Platform competition in two-sided markets. *Journal of the European Economic Association* 1(4):990–1029.

SaaStr. 2026. By year-end, Anthropic will out-earn every public software company except Microsoft. August 21. https://www.saastr.com/.

Sacra. 2026. OpenAI revenue, valuation & funding. Accessed September 2026, https://sacra.com/c/openai/.

Schumpeter, J. A. 1934. *The Theory of Economic Development*. Cambridge, MA: Harvard University Press.

Schumpeter, J. A. 1942. *Capitalism, Socialism and Democracy*. New York: Harper & Brothers.

SEC (U.S. Securities and Exchange Commission). 2026. EDGAR XBRL company facts API. Accessed September 2026, https://data.sec.gov/api/xbrl/companyfacts/.

Shaked, A., and Sutton, J. 1982. Relaxing price competition through product differentiation. *Review of Economic Studies* 49(1):3–13.

Solow, R. M. 1987. We'd better watch out. *New York Times Book Review*, July 12, p. 36.

Spengler, J. J. 1950. Vertical integration and antitrust policy. *Journal of Political Economy* 58(4):347–352.

Teece, D. J. 1986. Profiting from technological innovation: Implications for integration, collaboration, licensing and public policy. *Research Policy* 15(6):285–305.

Zhu, F., and Liu, Q. 2018. Competing with complementors: An empirical look at Amazon.com. *Strategic Management Journal* 39(10):2618–2642.

Zitron, E. 2026. Exclusive: OpenAI losses increased nearly 8X in 2025, with spending hitting $34 billion. *Where's Your Ed At*, June 16. https://www.wheresyoured.at/exclusive-openai-financials/.
