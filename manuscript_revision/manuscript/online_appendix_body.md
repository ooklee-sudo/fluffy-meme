---
title: "Online Appendix to “Cheap Code, Costly Choices: A Behavioral Economics Theory of Technical Debt Accumulation in LLM-Assisted Software Development”"
---

*Prepared for blind review*

# Contents

This Online Appendix supplements the manuscript. Section OA1 proves Result 4 (debt traps and hysteresis) and Section OA2 proves Result 8 (self-confirming complacency); Section OA3 shows that the sign results of the strategic extension (Results 5 to 7) hold in a more general setting than the closed forms of the main text. Section OA4 lists the parameters of the numerical illustrations and the automated checks of the model. Sections OA5 to OA8 give the construction of the data and additional empirical results. Section OA9 describes the experiment proposed in Section 5.5 of the manuscript and its simulated power. Equation numbers (1) to (4) and the definitions of $D_C$, $D_A$, $\Delta_p$, and $\Delta$ are those of the manuscript.

# OA1. Proof of Result 4 (debt traps and hysteresis)

**Setting.** Let $T(H)=(1-\mu)H+I(H;\beta)$ with $I(H;\beta)=A+C\,F(a(H;\beta))$ and $a(H;\beta)=\lambda vr_0(1+\gamma H)/(\beta\delta)$, where $F$ is the lognormal distribution function with median $R_m$ and log-dispersion $s$, $\mu\in(0,1]$, and $A=nq[1-(1-\alpha)p]>0$, $C=nq(1-\alpha)p>0$. Steady states are the zeros of $g(H;\beta)=I(H;\beta)-\mu H$.

**Lemma OA1 (structure).** (i) $g(0;\beta)>0$. (ii) $g(H;\beta)<0$ for every $H>(A+C)/\mu$. (iii) For every $H$, $g(H;\beta)$ is strictly decreasing in $\beta$. (iv) $T$ is nondecreasing, so every trajectory is monotone and converges to a steady state, and a steady state at which $g$ changes sign from positive to negative (negative to positive) is attracting (repelling).

*Proof.* (i) $g(0)=A+C\,F(a(0))\ge A>0$. (ii) $I\le A+C$, so $g(H)\le A+C-\mu H<0$ above $(A+C)/\mu$. (iii) $a(H;\beta)$ is strictly decreasing in $\beta$ and $F$ is strictly increasing, so $I$ is strictly decreasing in $\beta$ for every $H$. (iv) $T'(H)=1-\mu+C\,F'(a)\,\partial a/\partial H\ge1-\mu\ge0$, so $T$ is nondecreasing. A trajectory $H_{t+1}=T(H_t)$ of a nondecreasing map is monotone, and it is bounded by $\max\{H_0,(A+C)/\mu\}$, so it converges to a fixed point of $T$, that is, to a zero of $g$. From a point where $g>0$ the trajectory increases until the first zero above it, and from a point where $g<0$ it decreases to the first zero below it, so the zeros at which $g$ changes sign from positive to negative are the attracting ones and those at which it changes from negative to positive are the repelling ones. $\square$

**Proof of the bistability condition.** Fix $\epsilon\in(0,1/2)$ and $z=\Phi^{-1}(1-\epsilon)$, so that $F(R_me^{-sz})=\epsilon$ and $F(R_me^{sz})=1-\epsilon$. Define $H_L=(A+C\epsilon)/\mu$ and $H_T=(A+C(1-\epsilon))/\mu$; then $H_L<H_T<(A+C)/\mu$.

*Low state.* At $H_L$, $g(H_L)=A+C\,F(a(H_L))-A-C\epsilon$, which is negative if and only if $F(a(H_L))<\epsilon$, that is, $a(H_L;\beta)<R_me^{-sz}$. This is
$$\beta>\beta_1(\epsilon)=\frac{\lambda vr_0\,[1+\gamma(A+C\epsilon)/\mu]}{\delta R_m e^{-sz}}.$$

*Trap.* At $H_T$, $g(H_T)=C\,[F(a(H_T))-(1-\epsilon)]$, which is positive if and only if $a(H_T;\beta)>R_me^{sz}$. This is
$$\beta<\beta_2(\epsilon)=\frac{\lambda vr_0\,[1+\gamma(A+C(1-\epsilon))/\mu]}{\delta R_m e^{sz}}.$$

Suppose $\beta_1(\epsilon)<\beta<\beta_2(\epsilon)$. Then $g(0)>0$, $g(H_L)<0$, $g(H_T)>0$, and $g(H)<0$ for $H>(A+C)/\mu$. By the intermediate value theorem $g$ has a zero in $(0,H_L)$, a zero in $(H_L,H_T)$, and a zero in $(H_T,(A+C)/\mu)$. Taking the smallest zero, $g$ is positive before it and nonpositive just after it, so it is attracting and lies below $H_L=(A+C\epsilon)/\mu$. Taking the largest zero, $g$ is positive just before it and negative after it, so it is attracting and lies above $H_T=(A+C(1-\epsilon))/\mu$. Between them there is a zero at which $g$ changes sign from negative to positive, which is repelling. This proves that a low-debt state and a debt trap coexist, separated by an unstable steady state, and locates them as stated.

*Nonemptiness.* $\beta_1(\epsilon)<\beta_2(\epsilon)$ if and only if $[1+\gamma(A+C\epsilon)/\mu]\,e^{sz}<[1+\gamma(A+C(1-\epsilon))/\mu]\,e^{-sz}$, that is,
$$e^{2sz}<\frac{1+\gamma(A+C(1-\epsilon))/\mu}{1+\gamma(A+C\epsilon)/\mu}.$$

*Necessity of each edge.* The trap exists only if $\beta\le\lambda vr_0/(\delta R_m e^{sz})$ for some $\epsilon$: the largest zero $H^*$ satisfies $g(H^*)=0$, hence $F(a(H^*))=\mu H^*/C-A/C\ge$ whatever the root requires; as $\epsilon\to0$ the bounds in the statement, $\beta_1(\epsilon)\to\lambda vr_0[1+\gamma A/\mu]/(\delta R_m e^{-s z})$ and $\beta_2(\epsilon)\to\lambda vr_0[1+\gamma(A+C)/\mu]/(\delta R_m e^{sz})$, are the limits of the sufficient conditions and the exact edges are given in the next paragraph. $\square$

**Hysteresis.** Define $\beta_L=\inf\{\beta:\text{an attracting zero exists below any given level}\}$ more simply as follows. If an attracting zero $H_0$ exists at some $\beta$, then for $\beta'>\beta$ Lemma OA1(iii) gives $g(H_0;\beta')<0$ while $g(0;\beta')>0$, so a zero, and hence an attracting smallest zero, exists below $H_0$ at $\beta'$. Thus the low state exists for all $\beta\ge\beta_L$, where $\beta_L$ is the infimum of the $\beta$ at which it exists. By the symmetric argument ($g(H_3;\beta')>0$ at an attracting zero $H_3$ of the upper branch for $\beta'<\beta$, while $g<0$ above $(A+C)/\mu$), the trap exists for all $\beta\le\beta_T$. The bistability interval just constructed lies in $[\beta_L,\beta_T]$, so $\beta_L<\beta_T$ whenever it is nonempty.

Now let $\beta$ fall slowly from a value above $\beta_T$, starting at the low state. The low state persists while $\beta>\beta_L$; at $\beta_L$ the smallest zeros merge and vanish, and below $\beta_L$ the only attracting zero is the trap, so the codebase moves to it. If $\beta$ then rises again, the trap persists up to $\beta_T>\beta_L$, so it does not leave the trap when $\beta$ returns to $\beta_L$, the level at which it tipped, but only when $\beta$ exceeds $\beta_T$. Finally, because $T$ is nondecreasing and the unstable zero $H_2$ separates the basins, a one-time repayment that lowers $H$ below $H_2$ puts the stock in the basin of the low state, where it converges monotonically to it. $\square$

*Remark.* In the illustration of the main text ($n=1$, $q=0.5$, $p=0.9$, $\alpha=0$, $r_0=0.3$, $\gamma=3$, $\mu=0.5$, $R_m=1$, $s=0.25$, $\lambda=v=\delta=1$), the union of $(\beta_1(\epsilon),\beta_2(\epsilon))$ over $\epsilon\in(0,1/2)$ coincides, to the third decimal, with the exact bistable region $(0.646,0.843)$ obtained by counting steady states, and the widest single interval, at $\epsilon=0.14$, is $(0.659,0.829)$. In a simulation of the dynamics in which $\beta$ is lowered and then raised, the codebase tips into the trap near $\beta=0.64$ and leaves it near $\beta=0.85$ (grid step 0.01), as the exact region predicts.

# OA2. Proof of Result 8 (self-confirming complacency)

**Setting.** The perceived defect rate evolves as $\hat q_{t+1}=\hat q_t+\kappa\,w(\hat q_t)\,(q-\hat q_t)$ with $w(\hat q)=s(\hat q)+\theta[1-s(\hat q)]$, where $\kappa\in(0,1]$, $\theta\in[0,1]$, $\hat q_0\le q$, and the inspection probability $s(\hat q)$ is continuous and nondecreasing with $s(\hat q)=0$ if and only if $\hat q\le\hat q_c$, for a threshold $\hat q_c<q$. (If inspection time has support $[k_{\min},K]$ and the perceived value of inspecting is $\hat q(1-\eta\varphi)B/v$, then $\hat q_c=vk_{\min}/[(1-\eta\varphi)B]$.) Write $e_t=q-\hat q_t\ge0$. Then $e_{t+1}=e_t[1-\kappa w(\hat q_t)]$ with $1-\kappa w\in[0,1]$, so $e_t$ is nonincreasing and $\hat q_t$ is nondecreasing and bounded by $q$.

**(a)** If $\theta>0$, then $w\ge\theta$ for every $\hat q$, so $e_{t+1}\le(1-\kappa\theta)e_t$ and $e_t\to0$. If $\theta=0$ and $\hat q_0>\hat q_c$, then $\hat q_t\ge\hat q_0>\hat q_c$ for all $t$ because $\hat q_t$ is nondecreasing, so $w(\hat q_t)=s(\hat q_t)\ge s(\hat q_0)>0$ and again $e_{t+1}\le[1-\kappa s(\hat q_0)]e_t$, so $e_t\to0$.

**(b)** If $\theta=0$ and $\hat q_0\le\hat q_c$, then $s(\hat q_0)=0$ and $w=0$, so $\hat q_1=\hat q_0$, and by induction $\hat q_t=\hat q_0$ for all $t$: no one inspects, no evidence is observed, and the belief never changes.

**(c)** Under a mandate that requires inspection in each of the first $T$ periods, inspection occurs with probability one, so $w=1$ and $e_{t+1}=(1-\kappa)e_t$ for $t<T$, giving $q-\hat q_T=(1-\kappa)^T(q-\hat q_0)$. After the mandate is lifted the belief is $\hat q_T$. If $\hat q_T>\hat q_c$, that is, $(1-\kappa)^T(q-\hat q_0)<q-\hat q_c$, part (a) applies and $\hat q_t\to q$. If $\hat q_T\le\hat q_c$, part (b) applies and the belief stays at $\hat q_T<q$ forever (the wedge is reduced but not removed). Hence the mandate removes the wedge permanently if and only if $(1-\kappa)^T(q-\hat q_0)<q-\hat q_c$. $\square$

*Remark.* In the illustration of the main text ($q=0.5$, $\kappa=0.1$, $k_{\min}=0.05$, $K=0.6$, $B=1$, noticing probability 0.3), $\hat q_c=0.0714$; a belief of $0.05$ is self-confirming; one mandatory period moves it to $0.095$, which exceeds $\hat q_c$, so the belief then converges to $0.5$.

# OA3. Results 5 to 7 in a more general setting

The main text derives closed forms for a quadratic friction cost, a linear default share, a constant rework cost, and uniformly distributed inspection time. The following shows that the signs and the structure of Results 5 to 7 do not depend on these choices.

**Assumptions.** Friction costs the developer $c(f)$ of time per artifact, with $c$ increasing, convex, and $c(0)=0$. The default share is $\alpha(f)$, decreasing and convex with $\alpha(0)=\alpha_0$, so that $\psi(f)=\alpha_0-\alpha(f)$, the share of artifacts moved from default acceptance into deliberation, is increasing and concave with $\psi(0)=0$. Inspection time $k$ has any continuous distribution function $G$ with $G(x)>0$ for $x>0$; write $M(x)=\int_0^xk\,dG(k)$. The rework cost $R$ is heterogeneous with any distribution. For each $R$ the developer inspects an artifact not accepted by default if and only if $vk<\Delta_p(R)\equiv\varphi q(1-\eta\varphi)\max\{0,\beta\delta R-\lambda vr\}$, and the long-run value of a detected defect is $\Delta(R)\equiv q(1-\eta\varphi)(\delta R-vr)$.

**Values of deliberation.** The developer's perceived value of the option to deliberate, and the organization's long-run value of the same inspections, are
$$W_p=\mathbb E_R\!\left[\Delta_p G(\Delta_p/v)-vM(\Delta_p/v)\right],\qquad W_O=\mathbb E_R\!\left[\Delta\,G(\Delta_p/v)-vM(\Delta_p/v)\right],$$
and the corresponding interface costs are $J(f)=vc(f)-\psi(f)W_p$ and $C_O(f)=vc(f)-\psi(f)W_O$. (With constant $R$ and uniform $G$ on $[0,K]$ these reduce to $W_p=\Delta_p^2/(2vK)$ and $W_O=\Delta_p(2\Delta-\Delta_p)/(2vK)$ of the main text.) Let $f_D$ and $f_O$ be the minimizers of $J$ and $C_O$ on $[0,1]$.

**Proposition OA3.** (a) $W_O\ge W_p\ge0$, with equality of the two if and only if $\beta=\varphi=\lambda=1$ on a set of rework costs with $\Delta_p>0$ and positive probability. (b) $f_O\ge f_D$. If $J$ is strictly convex, $f_D$ is interior, $\psi'(f_D)>0$, and $W_O>W_p$, then $f_O>f_D$. In the rational benchmark $f_O=f_D$. (c) Result 6 holds with $f_D$ and $f_O$ as defined here when $J$ and $C_O$ have unique minimizers. (d) Under bypass at cost $\varepsilon$, the organization implements $f=\min\{f_O,\bar f(\varepsilon)\}$ where $\bar f(\varepsilon)=\max\{f\ge f_D:J(f)-J(f_D)\le\varepsilon/v\}$ in the units in which $J$ is expressed; with a quadratic cost this equals $f_D+\sqrt{2\varepsilon/(vc)}$ of Result 7.

*Proof.* (a) $W_O-W_p=\mathbb E_R[(\Delta-\Delta_p)\,G(\Delta_p/v)]$. Where $\Delta_p(R)>0$ we have $\beta\delta R-\lambda vr>0$, and since $\beta\le1$ and $\lambda\ge1$, $\delta R-vr\ge\beta\delta R-\lambda vr$; with $\varphi\le1$ this gives $\Delta(R)\ge\Delta_p(R)$, and $G(\Delta_p/v)>0$. Where $\Delta_p(R)=0$ the inspection set is empty and both terms are zero. So $W_O\ge W_p$. Also $W_p\ge0$ because the integrand is $\int_{k<\Delta_p/v}(\Delta_p-vk)\,dG\ge0$. Equality requires $\Delta=\Delta_p$ wherever $\Delta_p>0$, which holds if and only if $\varphi=1$ and $(1-\beta)\delta R+(\lambda-1)vr=0$, that is, $\beta=\lambda=1$.

(b) The function $vc(f)-\psi(f)W$ has decreasing differences in $(f,W)$ because $\partial^2/\partial f\partial W=-\psi'(f)\le0$, so by the monotone comparative statics theorem (Topkis) the minimizer is nondecreasing in $W$. Since $W_O\ge W_p$, $f_O\ge f_D$. For the strict part, $J$ strictly convex and $f_D$ interior give $vc'(f_D)=\psi'(f_D)W_p$, so $C_O'(f_D)=vc'(f_D)-\psi'(f_D)W_O=-\psi'(f_D)(W_O-W_p)<0$, which with the convexity of $C_O$ places its minimizer strictly to the right of $f_D$. In the rational benchmark $W_O=W_p$ by (a), so $J=C_O$.

(c) The proof of Result 6 uses only that the buyer's surplus, $S_0-p-J(f)$ for the developer and $S_0^O-p-C_O(f)$ for the organization, has a unique maximizer in $f$ at each price. The undercutting arguments are unchanged.

(d) The developer complies if and only if $J(f)-J(f_D)\le\varepsilon'$ for the appropriate conversion $\varepsilon'$ of her bypass cost into units of $J$. Because $J$ is convex with minimum at $f_D$, it is nondecreasing for $f\ge f_D$, so the compliant set above $f_D$ is $[f_D,\bar f]$. The organization's cost $C_O$ is convex with minimizer $f_O\ge f_D$, so it is nonincreasing on $[0,f_O]$ and the best compliant friction is $\min\{f_O,\bar f\}$. With $J(f)-J(f_D)=(vc/2)(f-f_D)^2$ this is the formula of Result 7. $\square$

*Numerical check.* For every combination of three friction costs (quadratic, cubic, exponential), two default shares (linear, concave), and two inspection-time distributions (uniform, exponential), with lognormal heterogeneous rework costs, a grid search confirms $W_O\ge W_p$, $f_O\ge f_D$, $f_O=f_D$ without wedges, and $f=\min\{f_O,\bar f(\varepsilon)\}$ under bypass (12 combinations).

# OA4. Parameters of the illustrations and the numerical checks

**Table OA1. Parameters and results of the numerical illustrations**

| Illustration | Parameters | Reported results |
|---|---|---|
| Section 4.4, Results 1 and 2 | $q=0.8$, $\beta=0.5$, $\varphi=0.6$, $\alpha=0.3$, $\eta=0.5$, $\lambda=1$, $r=0.4a$, $k\sim U[0,0.6a]$, $R$ lognormal with median $va$ and log-dispersion $0.79$, $\sigma=0.5$, $\delta=1$ | Price effect $-0.24$; wedge $+0.32$; debt $0.50\to0.58$; rational acceleration matches at $v_1=2.9v_0$; self-admitted share $0.33$ ($\sigma=0.5$ in the benchmark); possession effect $0.31$; lapse rate $0.21$ (joint probability that the artifact is E and a plan lapses; conditional on a detected E it is $0.27$); with $\lambda=1.8$ alone, possession effect $0.27$ |
| Result 3 | $K=0.3$, $B=1$, $\eta=0.5$, $v=1$; $(\varphi,\alpha)=(1,0),(0.6,0),(0.6,0.6)$ | $\hat q=0.6$ for $\varphi=1$; peak of $D$ at $q^*=\hat q/[2(1-\alpha)]$ |
| Result 4 | $n=1$, $q=0.5$, $p=0.9$, $\alpha=0$, $r_0=0.3$, $\gamma=3$, $\mu=0.5$, $R_m=1$, $s=0.25$, $\lambda=v=\delta=1$ | Bistable region $(0.646,0.843)$; widest interval $(0.659,0.829)$ at $\epsilon=0.14$ |
| Results 5 to 7 | $q=0.5$, $\bar R=2$, $r=0.4$, $K=0.6$, $\alpha_0=0.8$, $c=0.15$, $\eta=0.5$, $v=\delta=1$, $\varepsilon=0.005$; $\beta=0.5$, $\varphi=0.6$, $\lambda=1.2$ | $\Delta_p=0.109$, $\Delta=0.56$; $f_D=0.053$, $f_O=0.491$; implementable $f=0.311$; rational benchmark $f_D=f_O=0.711$ at $v=1$ and $0.100$ at $v=2$ |
| Result 8 | $q=0.5$, $\kappa=0.1$, $k_{\min}=0.05$, $K=0.6$, $B=1$, noticing probability $0.3$ | $\hat q_c=0.0714$; one mandatory period moves $\hat q$ from $0.05$ to $0.095$ |
| Result 9 | Prior $R\sim N(1,0.6^2)$, signal $S=R+N(0,0.5^2)$ | Posterior-mean variance $0.212\le\mathrm{Var}(R)=0.36$; rational possession effect below its Cantelli bound at all thresholds checked |

The log-dispersion $0.79$ and the noticing parameter $\eta=0.5$ of the first row are not stated in the main text of Section 4.4; they are the values under which all the reported numbers of that illustration are reproduced.

**Automated checks.** Two scripts accompany the paper. The first evaluates every closed form of Results 1 to 3, 5 to 7, and 9 and of Lemma 1 against a brute-force simulation or grid search of the decision problem it is derived from, and reproduces the numbers of Table OA1 (54 checks, all passed). The second does the same for Results 4 and 8 and for the general forms in OA3 (34 checks, all passed). Both are part of the code deposited with the paper.

# OA5. Data construction

**Sources.** *GH Archive* (gharchive.org) provides hourly logs of public GitHub events. We extract three event types: pull requests closed in the observation window (with size and review-count fields), pull-request reviews, and inline review comments. *AIDev* (Li et al. 2025, 2026; license CC BY 4.0) provides agent-authored pull requests in repositories with more than 100 stars; we use the curated version with 33,596 agent pull requests (v3), whose commit details carry code patches, and the later version with 71,677 agent pull requests in 6,673 repositories (v4), whose first pull request per repository gives the adoption date used in the event study. *CommitPackFT* (Muennighoff et al. 2023; MIT license) provides human commits with the full content of changed files; we use the files for 14 languages.

**Observation windows.** 1 to 14 August, 1 to 14 September, and 15 to 28 September 2025 for the pull-request comparisons; the first seven days of each month from February to September 2025 for the event study. GH Archive payloads from about October 2025 no longer carry pull-request size or author fields, so later periods cannot be used.

**Identification of agent-authored pull requests.** A pull request is attributed to an agent if its author account is Copilot (or its branch begins with `copilot/`), `google-labs-jules[bot]`, or `devin-ai-integration[bot]`; if its branch begins with `cursor/` or `codex/`; or if its description contains the Claude Code signature or its author is `claude[bot]`. These cues follow AIDev. Authors that are bot accounts and are not agents are excluded. All other authors are classified as human; unlabelled AI-assisted human pull requests are therefore included in the human group, which biases estimates toward zero. Pull requests with zero changed lines are dropped, and only pull requests created and closed within the window are used, so that their reviews are observed.

**Sizes of the agent samples.** September 1 to 14: Codex 102,870; Copilot 16,802; Claude Code 8,929; Cursor 7,982; Jules 3,360; Devin 670 (total 140,613; 807,735 human). August 1 to 14: Codex 102,494; Cursor 13,721; Copilot 11,833; Claude Code 11,610; Jules 3,006; Devin 1,226 (total 143,890; 864,307 human). September 15 to 28: Codex 110,015; Copilot 18,429; Claude Code 7,731; Cursor 5,975; Jules 3,800; Devin 590 (total 146,540; 853,556 human).

**Variables.** *Size* is additions plus deletions. *Net addition* is $\ln[(\text{additions}+1)/(\text{deletions}+1)]$. *Any human review* is one if a nonauthor, nonbot user submitted a review or an inline comment on the pull request in the window. *Review within 24 hours* is one if the first such event occurs within 24 hours of creation. *Inline comments* is the number of inline comments by nonauthor, nonbot users. *Refactor-titled* is a keyword match (refactor, cleanup, clean up, simplif, rename, remove unused, dead code) on the title. *Team repositories* have at least three distinct nonbot pull-request authors in the window, and *solo repositories* have at most one; this is a rough proxy.

**Estimation.** Linear regressions with repository fixed effects (outcomes and regressors demeaned within repository), a control for log size, and standard errors clustered by repository. Repositories with fewer than two pull requests are dropped.

**Marker and smell measures (OA7).** Added lines of code files are taken from commit patches (agent data) or reconstructed with a line-level diff of old and new file contents (human data). Code files are those with extensions for Python, JavaScript, TypeScript, Java, Go, Rust, C, C++, PHP, Kotlin, Swift, Scala, Ruby, or shell, excluding lock files, minified files, generated files, and vendored or build directories. A *strict marker* matches `\b(TODO|FIXME|HACK|XXX)\b` (case-sensitive); a *wide marker* matches `\b(todo|fixme|hack|xxx|workaround|temporary fix|for now)\b` (case-insensitive). The *smell score* is the sum of four counts on added lines: lines over 120 characters; repeated lines (stripped length at least 40, not blank, brace-only or comment-only, counted for each occurrence after the first within a patch); broad exception handlers (`except:`, `except Exception`, `catch (Exception|Throwable`, a bare `rescue`); and warning suppressions (`# type: ignore`, `# noqa`, `@ts-ignore`, `@ts-nocheck`, `eslint-disable`, `@SuppressWarnings`, `# pylint: disable`, `// nolint`, `# rubocop:disable`, `#[allow(`).

# OA6. Additional results on net addition and review

**Table OA2. Agent-versus-human coefficients by window (within repositories, size control; standard errors in parentheses)**

| Outcome and sample | Aug 1–14 | Sep 1–14 | Sep 15–28 | Pooled |
|---|---|---|---|---|
| Net addition, all repositories | +0.473 (0.041) | +0.653 (0.034) | +0.758 (0.036) | +0.597 (0.022) |
| Net addition, solo repositories | +0.468 (0.047) | +0.705 (0.039) | +0.838 (0.042) | +0.625 (0.026) |
| Net addition, team repositories | +0.632 (0.082) | +0.462 (0.079) | +0.392 (0.077) | +0.538 (0.045) |
| Any human review, all repositories | +0.014 (0.002) | +0.037 (0.004) | +0.033 (0.004) | +0.026 (0.002) |
| Any human review, excluding Copilot | −0.003 (0.001) | −0.005 (0.004) | −0.006 (0.003) | −0.005 (0.001) |
| Any human review, team repositories, excluding Copilot | −0.059 (0.014) | −0.071 (0.017) | −0.080 (0.016) | −0.059 (0.008) |
| Review within 24 hours, team repositories, excluding Copilot | −0.043 (0.014) | −0.056 (0.016) | −0.066 (0.015) | −0.045 (0.007) |
| Inline comments, log(1 + count), excluding Copilot | +0.000 (0.001) | +0.000 (0.002) | −0.001 (0.002) | +0.001 (0.001) |

*Notes.* Agent pull requests / human pull requests in the full samples: 143,890 / 864,307 (August), 140,613 / 807,735 (early September), 146,540 / 853,556 (late September), 431,043 / 2,525,598 pooled. In repositories with both: 86,358 / 45,559; 45,922 / 32,058; 47,614 / 34,636; pooled 211,624 / 160,944.

**Table OA3. Robustness, September 1 to 14 (agent coefficient; standard error in parentheses)**

| Specification | N (repositories) | Agent | Agent × log size |
|---|---|---|---|
| Net addition, task-type controls | 77,980 (5,106) | +0.533 (0.037) | +0.010 (0.021) |
| Net addition, excluding refactor-titled | 72,890 (4,999) | +0.648 (0.038) | +0.058 (0.024) |
| Net addition, solo repositories | 56,740 (4,081) | +0.691 (0.040) | +0.014 (0.020) |
| Net addition, team repositories | 16,711 (548) | +0.432 (0.073) | +0.117 (0.051) |
| Any human review, task-type controls | 77,980 (5,106) | +0.039 (0.008) | −0.005 (0.008) |
| Any human review, excluding Copilot | 72,034 (4,573) | +0.001 (0.009) | −0.008 (0.008) |
| Any human review, team, excluding Copilot | 16,268 (548) | −0.067 (0.018) | −0.018 (0.018) |
| Inline comments, log(1 + count), excluding Copilot | 72,034 (4,573) | +0.008 (0.002) | −0.010 (0.001) |
| Inline comments, team repositories, all agents | 16,711 (548) | +0.012 (0.011) | −0.004 (0.005) |
| Inline comments, PRs of 500 lines or more | 12,957 (2,485) | +0.020 (0.005) | not estimated |
| Any human review, PRs of 500 lines or more, excluding Copilot | 10,965 (2,155) | −0.007 (0.004) | not estimated |

Two points on this table. First, the agent coefficient on inline comments, excluding Copilot, is small and positive (+0.008) when the interaction with size is included, while the interaction is negative (−0.010): comments rise with size about 70 percent more slowly for agent pull requests than for human ones. In the pooled specification without the interaction (Table OA2) the agent coefficient is zero. In team repositories the interaction is not significant. Second, the raw gap in the share of pull requests with a human review (11.7 percent for human pull requests against 3.1 percent for agent pull requests in the early-September window) is a gap across repositories: among repositories with both kinds, the 50 with the most pull requests have a human review rate of 23.5 percent for human pull requests and 0.4 percent for agent pull requests, while within a repository the sign differs.

**Table OA4. By agent, September 1 to 14 (agent versus human pull requests in the same repositories)**

| Agent | N (repositories) | Net addition | Any human review |
|---|---|---|---|
| Copilot | 36,010 (3,645) | +1.096 (0.068) | +0.196 (0.013) |
| Codex | 62,283 (3,810) | +0.617 (0.063) | −0.008 (0.005) |
| Cursor | 32,227 (3,236) | +0.700 (0.114) | −0.028 (0.008) |
| Devin | 30,225 (3,095) | +0.267 (0.254) | −0.027 (0.057) |
| Jules | 31,574 (3,229) | +0.227 (0.106) | +0.068 (0.015) |
| Claude Code | 35,893 (3,563) | +0.371 (0.050) | −0.006 (0.006) |

Copilot's positive coefficient on review reflects its workflow, in which a human directs the agent through review comments; Cursor's negative coefficient is significant, and the others are small or imprecise.

# OA7. Self-admitted debt markers: details

**Table OA5. Marker density by agent (strict markers per 1,000 added lines of code; AIDev v3)**

| Agent | PRs | Repositories | Added lines | Strict per 1k | Wide per 1k | PRs with a marker (%) |
|---|---|---|---|---|---|---|
| Claude Code | 375 | 181 | 848,411 | 0.34 | 0.76 | 19.7 |
| Codex | 16,668 | 1,098 | 3,566,611 | 0.26 | 0.51 | 1.7 |
| Codex, excluding one dominant user | 9,635 | 1,097 | 2,241,228 | 0.39 | 0.59 | 2.7 |
| Copilot | 3,471 | 792 | 2,904,772 | 0.59 | 0.90 | 10.0 |
| Cursor | 1,207 | 281 | 850,788 | 0.56 | 1.03 | 9.0 |
| Devin | 3,851 | 273 | 2,827,294 | 0.62 | 0.75 | 9.0 |

One individual user supplies 34 percent of the Codex file changes and is excluded from the comparison with the human baseline.

**Table OA6. Comparison with the human baseline by patch size (raw rates per 1,000 added lines)**

| Added lines in the file change | Agent file changes | Human file changes | Markers, agent | Markers, human | Smell score, agent | Smell score, human |
|---|---|---|---|---|---|---|
| 1–5 | 111,157 | 172,480 | 1.56 | 3.45 | 57.2 | 26.9 |
| 6–20 | 57,643 | 66,973 | 0.95 | 1.73 | 35.3 | 10.5 |
| 21–50 | 32,981 | 30,928 | 0.59 | 1.30 | 30.8 | 11.5 |
| 51–150 | 27,102 | 13,170 | 0.51 | 1.24 | 34.0 | 13.8 |
| 151 or more | agent only | none | — | — | — | — |

The human baseline has no patches over 150 added lines, so the standardized comparison covers 60 cells of language and patch size that hold 60.6 percent of the agent's added lines. The agent's language mix, by share of added lines, is TypeScript 44.0 percent, Python 20.3, JavaScript 7.7, Java 5.6, Go 5.3, Rust 5.1, Ruby 3.4, and smaller shares for the other languages.

**Table OA7. Components of the standardized comparison (per 1,000 added lines)**

| Component | Agent | Human | Ratio |
|---|---|---|---|
| Strict markers | 0.62 | 1.38 | 0.45 |
| Wide markers | 0.89 | 1.86 | 0.48 |
| Lines over 120 characters | 10.05 | 3.61 | 2.78 |
| Repeated lines | 22.84 | 6.85 | 3.34 |
| Broad exception handlers | 1.09 | 0.27 | 3.98 |
| Warning suppressions | 1.94 | 0.42 | 4.60 |
| Smell score | 35.91 | 11.15 | 3.22 |

The ratio of strict markers is 0.29 in modified files and 0.50 in new files (unstandardized by cell). Intervals in Table 4 of the manuscript come from resampling repositories (1,000 draws).

**Within-pull-request comparison.** In 2,429 pull requests by Copilot, Devin, or Cursor in which both the agent's account and a human committed code, strict markers per 1,000 added lines are 0.34 in the agent's commits and 0.59 in the human's (difference 0.25, 95 percent interval 0.13 to 0.36); for wide markers 0.68 and 0.79 (difference 0.11, interval −0.07 to 0.27). By agent, the rates are 0.32 and 0.45 (Copilot, 973 pull requests), 0.39 and 0.68 (Devin, 1,038), and 0.30 and 0.69 (Cursor, 418). In the 473 pull requests with a marker in either part, the human part has the higher rate in 80.5 percent.

# OA8. Event study: details

**Panel.** The panel is built from GH Archive pull requests of the 6,673 AIDev repositories, using the first seven days of February to September 2025 (eight periods, indexed 0 to 7). It contains 7,041 agent and 172,875 human pull requests after the filters of OA5. No required field was missing in any period. The number of pull requests of these repositories declines over the period (for example, from about 45,000 closed pull-request events in February to about 30,000 in September), which is a common trend that the comparison with not-yet-treated repositories removes.

**Treatment.** A repository's treatment period is the first sampled week by whose end it has had an agent pull request, with the first agent pull request taken from AIDev. Repositories treated by the first sampled week (68) have no pre-period and are excluded from the estimates. The cohorts with at least one pull request in the panel are: March 32; April 48; May 41; June 812; July 754; August 847; September 943; and 1,172 repositories first adopting after the last sampled week, who serve as controls throughout.

**Estimator.** For each cohort $g$ and period $t\ne g-1$ the effect is the change in the cohort's repository-level mean outcome between $g-1$ and $t$ minus the same change among not-yet-treated repositories (those with treatment period greater than $\max\{t,g-1\}$ and not in $g$). Cells with fewer than 5 treated or 20 control repositories are dropped. Effects by event time $e=t-g$ average the cohort estimates with weights equal to the numbers of treated repositories; "after adoption" averages $e\ge0$ and "before adoption" averages $e\le-2$. Standard errors come from resampling repositories (400 draws; 300 for count outcomes).

**Table OA8. Event-time estimates, all pull requests (effect, standard error)**

| Event time | −6 | −5 | −4 | −3 | −2 | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|---|---|---|---|---|
| Net addition | +0.186 (0.073) | +0.007 (0.058) | +0.017 (0.050) | −0.004 (0.048) | −0.020 (0.052) | +0.153 (0.051) | +0.014 (0.062) | +0.048 (0.068) | +0.079 (0.097) | +0.331 (0.177) |
| Human review | −0.021 (0.022) | +0.005 (0.016) | +0.002 (0.013) | +0.002 (0.012) | +0.023 (0.012) | −0.004 (0.012) | −0.003 (0.015) | −0.006 (0.019) | −0.044 (0.025) | −0.107 (0.050) |
| Refactor-titled | −0.011 (0.010) | +0.003 (0.007) | −0.001 (0.006) | +0.001 (0.006) | +0.004 (0.006) | +0.002 (0.006) | +0.002 (0.007) | −0.001 (0.008) | +0.008 (0.010) | −0.025 (0.014) |
| Merged | −0.014 (0.015) | +0.008 (0.012) | +0.013 (0.009) | +0.008 (0.009) | +0.025 (0.009) | −0.015 (0.010) | −0.026 (0.011) | −0.025 (0.014) | +0.000 (0.019) | −0.003 (0.044) |

Estimates at event times −7, 5, and 6 rest on very few repository-periods and are not reported here; they are very imprecise (for example +0.802 with standard error 0.544 for net addition at time 6). The corresponding estimates for human pull requests only are close to those for all pull requests, except for net addition at time 0 (+0.057 against +0.153).

**Notes on pre-trends.** The pooled placebo estimates are close to zero (Table 5 of the manuscript), but individual leads are not uniformly clean: net addition at time −6 (+0.186, $t=2.5$) and merge rate at time −2 (+0.025, $t=2.8$). The count of pull requests per repository shows negative leads ($-0.128$ to $-0.040$ at times −7 to −2, on the log(1 + count) scale) and a jump at time 0 ($+0.225$), so activity rises into the adoption period; we therefore report no placebo for that outcome and do not interpret it as an effect of adoption.

# OA9. Experimental protocol and simulated power

OA9_PLACEHOLDER
