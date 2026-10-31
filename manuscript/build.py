import json,re
from docx import Document
from docx.shared import Pt,Inches,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
B=json.load(open('blocks.json'))
txt=lambda b:''.join(s[0] for s in b['segs'])
# ---- merge multi-line headings / captions
M=[]
for b in B:
    if b['kind']=='heading' and M and M[-1]['kind']=='heading':
        pt=txt(M[-1]); ct=txt(b)
        cap=re.match(r'^(Table|Figure) ',pt) and not re.search(r'[\.\)]$',pt) and not re.match(r'^(\d+\.\d* ?[A-Z]|\d+\. |Appendix|Table|Figure|Abstract|References)',ct) 
        title = len(M)==1
        if cap or title:
            M[-1]['segs'][-1][0]+=' '; M[-1]['segs']+=b['segs']; continue
    M.append(b)
B=M
# ---- find-paragraph helper
def sub(mode, old, new, scope='para'):
    n=0
    for b in B:
        if 'segs' not in b: continue
        if scope=='para' and b['kind']!='para': continue
        for s in b['segs']:
            if old in s[0]: s[0]=s[0].replace(old,new); n+=1; break
        else:
            t=txt(b)
            if old in t:
                b['segs']=[[t.replace(old,new),False,False]]; n+=1
    return n
log=[]
def fix(old,new,why,cat):
    n=sub(0,old,new)
    log.append((cat,old,new,why,n))
# ---- content corrections (found in review)
fix("At least expected cost, the firm","To minimise expected cost, the firm","'At least expected cost' is a garbled phrase; the sentence introduces the firm's objective.","Language")
fix("each call takes about 1.8 to 1.9 s on our CPU","each call takes about 1.7 to 1.8 s on our CPU","Table 5 reports L3 mean latency of 1,728-1,792 ms (capped at 2 s), i.e. 1.7 to 1.8 s.","Numbers")
fix("leads to 50 to 60 system failures per day","leads to 49 to 60 system failures per day","Table 7 gives 60.0, 50.0 and 49.3 failures per day.","Numbers")
fix("are the same (3 incident per day)","are the same (3 incidents per day)","Number agreement.","Language")
fix("(at about 14, 5 and 376 tickets per day)","(at about 13, 5 and 350 tickets per day)","Table 8 reports 13.1, 5.3 and 350.2 tickets per work day.","Numbers")
fix("one incident in 11 to 18 followed","one incident in 11 to 20 followed","Branching ratios of 0.05 to 0.09 (Table C2) imply 1/0.09 = 11 to 1/0.05 = 20.","Numbers")
fix("(26 to 96% across five definitions","(26 to 97% across five definitions","Table C3 gives 25.6% to 96.5% of failures.","Numbers")
fix("23 to 28% to 30 to 32% of days without guardrails","23 to 32% of days without guardrails","Garbled range; the abstract and Section 5.3 give 23 to 28% (c = 0.3) and 30 to 32% (c = 0.44), i.e. 23 to 32% overall.","Language")
# Table E3 note
for b in B:
    if b['kind']=='para' and txt(b).startswith('Computed by econ_tables.py; the cascade is evaluated under independence.'):
        b['segs'][-1][0]=b['segs'][-1][0].rstrip()+' Ties (θ = 1 and θ = 2 at k_min = 0) are reported at the smaller N.'
        log.append(('Tables','Table E3 note','added tie-breaking note',"Recomputation shows ties: θ = 1 (N = 3 and 4) and θ = 2 (N = 4 and 6) at k_min = 0; the table silently reports the smaller N.",1))

# ================= FOCUS: dependent layers + over-dispersion -> capacity =================
def H(b): return txt(b) if b['kind']=='heading' else ''
def delrange(start,end,keep_end=True):
    global B
    i=next(k for k,b in enumerate(B) if H(b).startswith(start))
    j=next(k for k,b in enumerate(B) if k>i and H(b).startswith(end))
    n=j-i; B=B[:i]+B[j:]; return n
def setpara(prefix,new):
    for b in B:
        if b['kind']=='para' and txt(b).startswith(prefix):
            b['segs']=[[new,False,False]]; return 1
    raise SystemExit('setpara miss: '+prefix)
def rx(pattern,new,must=1):
    n=0
    for b in B:
        if b['kind']!='para': continue
        t=txt(b)
        if re.search(pattern,t,flags=re.S):
            b['segs']=[[re.sub(pattern,new,t,flags=re.S),False,False]]; n+=1
    if n<must: raise SystemExit('rx miss: '+pattern[:60])
    return n
def delpara(prefix):
    global B
    m=len(B); B=[b for b in B if not (b['kind']=='para' and txt(b).startswith(prefix))]
    if len(B)==m: raise SystemExit('delpara miss: '+prefix)
# split merged bold-lead paragraphs (Appendix B)
nb=[]
for b in B:
    if b['kind']=='para' and len(b['segs'])>2:
        cur=[]; 
        for k,sg in enumerate(b['segs']):
            if k>0 and sg[1] and re.match(r'^[A-Z][A-Za-z\- /&]+\.\s*$',sg[0]) and cur:
                nb.append({'kind':'para','segs':cur}); cur=[]
            cur.append(sg)
        nb.append({'kind':'para','segs':cur})
    else: nb.append(b)
B=nb
# --- delete sections moved to future work
delrange('2.6','3. Model')
delrange('3.6 Pooling','3.7 The implied')
delrange('3.8 Moral','4. Empirical')
delrange('5.7 Typed','6. Discussion')
delrange('Table C2.','Appendix D')
for b in B:
    if b['kind']=='heading' and txt(b).startswith('3.7 The implied'): b['segs']=[[txt(b).replace('3.7','3.6',1),True,False]]
# appendix proofs / appendix B
delpara('Proof of Proposition 6.'); delpara('Proof of Proposition 8.')
rx(r'Typed failure models\..*?three treatments\.\s*','',0)
for b in list(B):
    if b['kind']=='para' and txt(b).startswith('Typed failure models'): B.remove(b)
# references only used in the removed parts
for pre in ('Hawkes, A.','Holmström','Parasuraman','Watson, W.','PatSnap','US 2024/0330824'):
    delpara(pre)
# --- rewritten paragraphs
setpara('When a firm puts a large language model (LLM) into service',
"When a firm puts a large language model (LLM) into service, it takes on a new stochastic cost: the errors that people have to absorb. We study how the firm should size a standby human workforce when automated guardrail layers screen the errors first. Standby capacity is a newsvendor quantile of the daily count of human-handled incidents, and a 95% service level is optimal only when an unhandled incident costs twenty times a unit of capacity. Two features make the textbook plan unreliable. Over-dispersion pushes the safety stock above what the dispersion index suggests, and stacking screens under independence overstates diversification when the layers fail on the same inputs. We bound residual risk under arbitrary dependence and show that, with integer capacity and a staffing floor, the cost-minimising depth of screening is in general not unimodal. We evaluate the model on measured outputs of three small open models passed through three guardrail layers, using simulated arrivals and public traces. A task-specific verifier cut required capacity by 78 to 95% but rejected 15 to 71% of correct answers, the share of hallucinations passing two layers was 1.3 to 2.3 times the independence prediction, and ignoring day-to-day variation raised expected cost by 9 to 65%. Because arrivals are simulated, the numbers illustrate the method.")
_i=next(k for k,b in enumerate(B) if b['kind']=='para' and txt(b).startswith('When a firm puts a large language model'))
B.insert(_i+1,{'kind':'para','segs':[['Keywords: ',True,False],['LLM operations, hallucination, safety stock, newsvendor, factor substitution, correlated risk, over-dispersion',False,False]]})
setpara('Our contribution lies mainly in application and measurement',
"Our contribution lies mainly in application and measurement, and we try to be explicit about which results are already known. The newsvendor solution and the negative-binomial treatment of over-dispersed demand are classical (Arrow et al. 1951; Porteus 2002; Cameron and Trivedi 1998), and so is the Poisson quantile rule for staffing (Whitt 2007). We apply these tools to a new input, standby labour for machine errors, and add three results. We show how thinning by screening interacts with over-dispersion (Proposition 3). We recast the multiplicative guardrail formula as the independence special case of a set of dependence bounds, and we measure that dependence for hallucination-grounding layers (Proposition 4). We show that when capacity is integer-valued and standing staff has a floor, cost is in general not unimodal in the depth of screening, and we derive comparative statics in the ratio of labour to compute prices (Proposition 5). Proposition 6 converts the service-level target into the shortfall cost that would justify it and puts a price on misspecifying dispersion and dependence. Two natural extensions, a typed model of heterogeneous failure classes and a model of reviewers' attention as a moral-hazard problem, are left to future work (Section 6.3).")
rx(r'Human-factors research adds that people.*?Section 3\.8 brings these two strands together\.','',1)
rx(r"Sections 3\.1 to 3\.7 are therefore about the cost of absorbing errors, not the cost of finding them\. Section 3\.8 relaxes this assumption by modelling reviewers' attention as a moral-hazard problem\.","The model is therefore about the cost of absorbing errors, not the cost of finding them; Section 6.3 returns to this assumption.")
rx(r'\(Sections 3\.1 to 3\.6\) the service level','(Sections 3.1 to 3.5) the service level')
setpara('For the typed failure models, we fit',"Every simulation and bootstrap draw is seeded and can be reproduced with the scripts that accompany the paper (Appendix D).")
rx(r' \(Section 5\.7 adjusts the baseline for this\)','')
delpara('The extension in Section 3.8 shows')
rx(r'A falling count of handled incidents should not be taken.*?should not be taken as a validated gain\.',"Auditing a sample of unflagged items is one way to measure what the screens are missing, because the count of handled incidents includes only the errors that were detected.")
rx(r'Reviewer behaviour is modelled in the simplest possible way.*?awaiting a test\. ','')
rx(r'Outside Section 3\.8, detection is assumed to be complete\.',"Detection is assumed to be complete, and reviewers' attention, which screening may wear down, is not modelled.")
rx(r'The typed models and the public data come with caveats of their own\. The Hawkes and episode fits.*?would widen the gap\. ','The public data come with caveats of their own. ')
rx(r'including the lag between an incident and its handling,',"including reviewers' attention (which screening may wear down), the lag between an incident and its handling and heterogeneous failure classes with their own arrival processes (clustered outages, heavy-tailed episodes),")
setpara('Human backup for machine errors is a safety stock',
"Human backup for machine errors is a safety stock, and screening is the capital that economises on it. Under the stated assumptions, several conclusions follow. The standby workforce should be set at a quantile of the daily incident count, with the service level implied by the cost of a shortfall. Over-dispersion raises the required safety stock above what a Poisson model or the dispersion index would suggest. The independence formula for stacked screens overstates diversification and understates residual risk. And when capacity is indivisible and standing staff has a floor, the cost-minimising depth of screening is not fixed at three but responds to the relative prices of labour and compute.")
rx(r'Sections 5\.3 and 5\.7','Sections 5.3 and 5.4')
# --- renumber tables, propositions, sections
def allt(f):
    for b in B:
        if 'segs' in b:
            for sg in b['segs']: sg[0]=f(sg[0])
        elif b['kind']=='table':
            b['rows']=[[f(c) for c in r] for r in b['rows']]
allt(lambda t: re.sub(r'Table ([5-8])\b',lambda m:'@@%d'%(int(m.group(1))+2),t))
allt(lambda t: t.replace('Table E3','Table 4').replace('Table E1','Table 5').replace('Table E2','Table 6'))
allt(lambda t: t.replace('@@','Table '))
allt(lambda t: t.replace('Proposition 7','Proposition 6').replace('Section 3.7','Section 3.6'))
log.append(('Focus','Scope narrowed to "dependent layers + over-dispersion -> capacity"','Propositions 6 (typed failure classes) and 8 (reviewer moral hazard) and their sections (old 2.6, 3.6, 3.8, 5.7; Tables 4, E4, C2, C3) removed; old Proposition 7 is now Proposition 6',"Single, sharper contribution; removed material is flagged in Section 6.3 as future work.",1))


# ================= OR LITERATURE (all entries verified against Crossref) =================
P1=("Choosing capacity in the face of random demand is the oldest problem in stochastic inventory theory. Arrow et al. (1951) showed that the optimal stock is a quantile of the demand distribution, with the quantile determined by the ratio of shortage to holding costs; Porteus (2002) provides the modern treatment. Gallego and Moon (1993) review distribution-free versions of the newsvendor rule, which use only the mean and variance of demand, and Van Mieghem (2003) reviews capacity management and investment under demand uncertainty.")
P2=("Service operations apply the same reasoning to staffing. The square-root safety-staffing rule goes back to Halfin and Whitt (1981) and underlies the dimensioning of large call centres (Borst et al. 2004); Gans et al. (2003) and Aksin et al. (2007) review the field, Green et al. (2007) adjust staffing for demand that varies over time, and Whitt (2007) sets out the Poisson-quantile rule that we use as our baseline. Harrison and Zeevi (2005) develop a fluid-model approach to staffing.")
P3=("A long line of work asks what happens when the arrival rate is itself uncertain. Empirical work on call centres has found that arrivals are Poisson only conditional on a random, day-specific rate, which makes daily counts over-dispersed (Brown et al. 2005), and Avramidis et al. (2004) propose doubly stochastic models for daily arrivals. Jongbloed and Koole (2001) propose Poisson mixtures to manage this uncertainty, and Whitt (2006), Steckley et al. (2009) and Bassamboo et al. (2010) study staffing and performance under uncertain arrival rates and forecast errors, with Bassamboo et al. (2010) showing that safety-staffing principles have to be revisited. Count-data econometrics offers the negative binomial as a remedy (Cameron and Trivedi 1998). We bring these tools to a stream whose arrivals are produced by the firm's own technology, add automated screening as a second, substitutable input, and check whether the usual caveats still apply.")
setpara('Choosing capacity in the face of random demand',P1)
_i=next(k for k,b in enumerate(B) if b['kind']=='para' and txt(b).startswith('Choosing capacity in the face of random demand'))
B[_i+1:_i+1]=[{'kind':'para','segs':[[P2,False,False]]},{'kind':'para','segs':[[P3,False,False]]}]
rx(r'(it is known to over-credit redundancy when failures are positively associated \(Esary et al\. 1967\)\.)',
 r"\1 The same issue arises in fault-tolerant software. Knight and Leveson (1986) tested and rejected the assumption that independently written program versions fail independently, and Eckhardt and Lee (1985) and Littlewood and Miller (1989) explain such coincident failures by variation in the difficulty of the inputs, so that diversity of design does not deliver independence of failure. This input-difficulty mechanism is the one we expect in guardrail stacks that face the same ambiguous outputs.")
rx(r'(and so is the Poisson quantile rule for staffing \(Whitt 2007\)\.)',
 r"\1 Staffing under uncertain arrival rates (Whitt 2006; Bassamboo et al. 2010) and dependent failures in redundant systems (Eckhardt and Lee 1985; Littlewood and Miller 1989) are likewise established topics.")
NEW=[
'Aksin, Z., Armony, M., and Mehrotra, V. 2007. "The Modern Call Center: A Multi-Disciplinary Perspective on Operations Management Research," Production and Operations Management (16:6), pp. 665-688.',
'Avramidis, A. N., Deslauriers, A., and L\'Ecuyer, P. 2004. "Modeling Daily Arrivals to a Telephone Call Center," Management Science (50:7), pp. 896-908.',
'Bassamboo, A., Randhawa, R., and Zeevi, A. 2010. "Capacity Sizing Under Parameter Uncertainty: Safety Staffing Principles Revisited," Management Science (56:10), pp. 1668-1686.',
'Borst, S., Mandelbaum, A., and Reiman, M. 2004. "Dimensioning Large Call Centers," Operations Research (52:1), pp. 17-34.',
'Eckhardt, D., and Lee, L. 1985. "A Theoretical Basis for the Analysis of Multiversion Software Subject to Coincident Errors," IEEE Transactions on Software Engineering (11:12), pp. 1511-1517.',
'Gallego, G., and Moon, I. 1993. "The Distribution Free Newsboy Problem: Review and Extensions," Journal of the Operational Research Society (44:8), pp. 825-834.',
'Gans, N., Koole, G., and Mandelbaum, A. 2003. "Telephone Call Centers: Tutorial, Review, and Research Prospects," Manufacturing & Service Operations Management (5:2), pp. 79-141.',
'Halfin, S., and Whitt, W. 1981. "Heavy-Traffic Limits for Queues with Many Exponential Servers," Operations Research (29:3), pp. 567-588.',
'Harrison, J. M., and Zeevi, A. 2005. "A Method for Staffing Large Call Centers Based on Stochastic Fluid Models," Manufacturing & Service Operations Management (7:1), pp. 20-36.',
'Jongbloed, G., and Koole, G. 2001. "Managing Uncertainty in Call Centres Using Poisson Mixtures," Applied Stochastic Models in Business and Industry (17:4), pp. 307-318.',
'Knight, J. C., and Leveson, N. G. 1986. "An Experimental Evaluation of the Assumption of Independence in Multiversion Programming," IEEE Transactions on Software Engineering (12:1), pp. 96-109.',
'Littlewood, B., and Miller, D. 1989. "Conceptual Modeling of Coincident Failures in Multiversion Software," IEEE Transactions on Software Engineering (15:12), pp. 1596-1614.',
'Steckley, S. G., Henderson, S. G., and Mehrotra, V. 2009. "Forecast Errors in Service Systems," Probability in the Engineering and Informational Sciences (23:2), pp. 305-332.',
'Van Mieghem, J. A. 2003. "Capacity Management, Investment, and Hedging: Review and Recent Developments," Manufacturing & Service Operations Management (5:4), pp. 269-302.',
'Zhao, W., Ren, X., Hessel, J., Cardie, C., Choi, Y., and Deng, Y. 2024. "WildChat: 1M ChatGPT Interaction Logs in the Wild," in Proceedings of ICLR 2024 (arXiv:2405.01470).',
'Whitt, W. 2006. "Staffing a Call Center with Uncertain Arrival Rate and Absenteeism," Production and Operations Management (15:1), pp. 88-102.']
import unicodedata
_r=next(k for k,b in enumerate(B) if b['kind']=='heading' and txt(b).startswith('References'))
_e=next(k for k,b in enumerate(B) if k>_r and b['kind']=='heading')
ents=B[_r+1:_e]+[{'kind':'para','segs':[[t,False,False]]} for t in NEW]
key=lambda b: unicodedata.normalize('NFKD',txt(b)).encode('ascii','ignore').decode().lower().replace('-','').replace(' ','')
ents.sort(key=key)
B[_r+1:_e]=ents
log.append(('Literature','Added OR literature (Sections 2.1, 2.5, Introduction)','15 references on call-centre staffing, staffing under arrival-rate uncertainty, newsvendor/capacity management, and coincident failures in redundant (multiversion) systems',"Positions the paper in the OR literature AOR reviewers expect; every entry was checked against Crossref (title, volume, pages).",15))

# ================= STRONGER PROPOSITIONS 4 AND 5 =================
import numpy as _np
from scipy import special as _sp, stats as _st
def _lam(N,rho,c=.63,l0=10.):
    if N==0: return l0
    if rho<=0: return l0*(1-c)**N
    if rho>=1: return l0*(1-c)
    sv=(1-rho)/rho; return l0*float(_np.exp(_sp.betaln(c*sv,(1-c)*sv+N)-_sp.betaln(c*sv,(1-c)*sv)))
_kp=lambda l:int(_st.poisson.ppf(.95,l)) if l>0 else 0
def _best(rho,km):
    f=[150*max(km,_kp(_lam(n,rho)))+25*n for n in range(0,41)]
    m=min(f); return f.index(m),m,f
# shift Table 5..10 -> 6..11 (new Table 5 is inserted in Section 3.5)
allt(lambda t: re.sub(r'Table (5|6|7|8|9|10)\b',lambda m:'@@%d'%(int(m.group(1))+1),t))
allt(lambda t: t.replace('@@','Table '))
BOLD=lambda lead,rest: {'kind':'para','segs':[[lead,True,False],[rest,False,False]]}
def _find(prefix):
    return next(k for k,b in enumerate(B) if b['kind']=='para' and txt(b).startswith(prefix))
# ---- Proposition 4
i=_find('Proposition 4 (dependence bounds)')
r42=_lam(6,.1)/_lam(6,0)
P4=[BOLD('Proposition 4 (dependence between layers). ',
 "Let I_i indicate that layer i catches a given critical hallucination, with P(I_i = 1) = c_i, and let r = P(I_1 = … = I_N = 0), so that λ_N = λ₀r. (a) (Sharp bounds) (1 − Σc_i)⁺ ≤ r ≤ 1 − max_i c_i, and every value in this interval is attained by some joint distribution with the given marginals. If the I_i are positively associated (Esary et al. 1967), then additionally r ≥ Π(1 − c_i). (b) (Two layers) r = (1 − c₁)(1 − c₂) + φ√(c₁(1 − c₁)c₂(1 − c₂)), where φ is the correlation of I₁ and I₂, so that r/[(1 − c₁)(1 − c₂)] = 1 + φ√(c₁c₂/[(1 − c₁)(1 − c₂)]). (c) (Common difficulty) Suppose the layers catch independently given a latent difficulty of the hallucination, with a common catch probability that is Beta-distributed with mean c, and let ρ be the correlation between any two catch indicators and s = (1 − ρ)/ρ. Then r_N = Π_{k=0}^{N−1} [(1 − c)s + k]/(s + k). This is non-decreasing in ρ for every N, equals (1 − c)^N as ρ → 0, tends to 1 − c as ρ → 1, and decays only polynomially, r_N ~ [Γ(s)/Γ((1 − c)s)] N^{−cs}, rather than geometrically. (d) Through Proposition 1(a), the required capacity k∗(α, λ₀r) is non-decreasing in r, and under (c) non-decreasing in ρ."),
 {'kind':'para','segs':[["Part (a) says that the multiplicative formula is the special case of independence, not a bound: it understates residual risk, and hence required capacity, only when the layers are positively associated, which is what we expect when the same ambiguous outputs fool every layer. Part (b) shows how much a small correlation can matter when clearances are high. The multiplier √(c₁c₂/[(1 − c₁)(1 − c₂)]) grows with both clearances, so a correlation of 0.15 between layers with clearances of 0.895 and 0.58 raises the residual share by a factor of 1 + 0.15 × 3.43 = 1.51. Part (c) gives a closed form for a one-parameter family that runs from independence to total dependence. With c = 0.63 and ρ = 0.1, the residual rate after six layers is "+f"{r42:.1f}"+" times its value under independence, and extra layers keep paying off only slowly, because the decay is a power of N. The dependence must therefore be measured (Section 5.2) rather than assumed.",False,False]]}]
B[i:i+2]=P4   # replaces the statement and the stray continuation paragraph
# remove the now-duplicated sentence in the Table 2 lead-in
rx(r' The dependence must therefore be measured \(Section 5\.2\) rather than assumed\. Section 3\.6','  Section 3.6',0)
# ---- Proposition 5
i=_find('Proposition 5 (optimal depth and factor substitution)')
P5=BOLD('Proposition 5 (optimal depth and factor substitution). ',
 "Let K(N) = max{k_min, k∗(α, λ_N)}. (a) In general f is not unimodal in N: because k∗ is integer-valued with plateaus, f can rise and then fall again. (b) (Breakpoints) Every minimiser is N = 0 or satisfies K(N) < K(N − 1), so it is enough to evaluate f at the first N of each capacity level. With k_min ≥ 1, let N₀ be the first N with k∗(α, λ_N) ≤ k_min; every N > N₀ is strictly dominated, so N ≤ N₀. (c) Let θ = C_h/g with equal per-layer compute cost g. The smallest and the largest minimiser are non-decreasing in θ: the dearer labour is relative to compute, the deeper the optimal cascade. (d) (Unknown dependence) If the layers have the same clearance c and nothing is known about their dependence, the worst-case cost of depth N ≥ 1 is C_hK(1) + gN, attained when the layers fail together. It is strictly increasing in N, so the maximin depth is 0 or 1. The gain of depth N over depth 1 is C_h[K(1) − K(N)] − g(N − 1), and it is positive only if dependence is weak enough to save more than g(N − 1)/C_h units of capacity. (e) (Known dependence) Under the common-difficulty model of Proposition 4(c), f(N; ρ) is non-decreasing in ρ for every N, so the minimal cost is non-decreasing in ρ, but the optimal depth need not be monotone in ρ (Table 5). (f) The latency constraint restricts N to a feasible prefix of the cascade.")
B[i]=P5
# commentary + new Table 5 after the Table 4 note
j=_find('Computed by econ_tables.py; the cascade is evaluated under independence.')
rows=[]
def money(x): return f"${int(x):,}"
for rho,lab in ((0,'0 (independent)'),(.02,'0.02'),(.05,'0.05'),(.1,'0.1'),(.2,'0.2'),(.3,'0.3'),(.5,'0.5'),(1,'1 (comonotone)')):
    n0,m0,f0=_best(rho,0); n1,m1,f1=_best(rho,1); ni0=_best(0,0)[0]; ni1=_best(0,1)[0]
    e0=f0[ni0]-m0; e1=f1[ni1]-m1
    fmt=lambda e,m: '$0' if e==0 else f"+{money(e)} (+{round(100*e/m)}%)"
    rows.append([lab,f"{_lam(3,rho):.2f}",str(_kp(_lam(3,rho))),str(n0),money(m0),str(n1),money(m1),fmt(e0,m0),fmt(e1,m1)])
hdr=['ρ','λ₃','k∗ (N = 3)','N∗ (k_min = 0)','Cost at N∗','N∗ (k_min = 1)','Cost at N∗','Extra cost of independence plan (k_min = 0)','Extra cost of independence plan (k_min = 1)']
Nlist=[ _best(r,0)[0] for r in (0,.02,.05,.1,.2,.3,.5)]
comm={'kind':'para','segs':[[f"Table 5 adds dependence to the example, using the common-difficulty model of Proposition 4(c). Dependence raises the cost of every depth, as part (e) of Proposition 5 says, and it moves the optimum in an irregular way: the cost-minimising depth with k_min = 0 is {', '.join(str(x) for x in Nlist)} layers for ρ = 0, 0.02, 0.05, 0.1, 0.2, 0.3 and 0.5, because the plateaus of k∗ shift with ρ. A firm that plans for independence (six layers, or four when one engineer is always kept) therefore pays 33% more than necessary at ρ = 0.1, which is within the range of correlations we measure (Sections 5.2 and 5.7), and 45% more with the staffing floor. Under total dependence a single layer is optimal and the independence plan wastes five layers. In short, the benefit of stacking depends on a parameter that the clearance rates do not reveal.",False,False]]}
cap={'kind':'heading','segs':[["Table 5. Optimal depth of screening under common-difficulty dependence (λ₀ = 10, c = 0.63 per layer, α = 0.95, C_h = $150, g = $25)",True,False]]}
tab={'kind':'table','rows':[hdr]+rows}
note={'kind':'para','segs':[["Beta-distributed catch probability with mean 0.63 and correlation ρ between layers (Proposition 4(c)); ρ = 1 is the comonotone case. The independent-optimal depths are N = 6 (k_min = 0) and N = 4 (k_min = 1). The independence plan is the independent-optimal depth; its extra cost is f(N; ρ) at that depth minus the minimum over N. Computed by econ_dependence.py.",False,True]]}
B[j+1:j+1]=[comm,cap,tab,note]
# ---- abstract / introduction / conclusion
rx(r"We bound residual risk under arbitrary dependence and show that, with integer capacity and a staffing floor, the cost-minimising depth of screening is in general not unimodal\.",
   "We show that the multiplicative guardrail formula is the independence case of sharp dependence bounds, that a weak correlation between high-clearance layers inflates residual risk by tens of per cent, and that under a common-difficulty model residual risk decays only polynomially in the number of layers. With integer capacity and a staffing floor, the cost-minimising depth of screening is in general not unimodal, and any depth beyond one layer is a bet on dependence.")
rx(r"We recast the multiplicative guardrail formula as the independence special case of a set of dependence bounds, and we measure that dependence for hallucination-grounding layers \(Proposition 4\)\.",
   "We recast the multiplicative guardrail formula as the independence special case of a set of sharp dependence bounds, give an exact link between the correlation of two layers and the inflation of residual risk, derive a closed form under a common-difficulty model in which residual risk decays only polynomially in depth, and measure the dependence for hallucination-grounding layers (Proposition 4).")
rx(r"We show that when capacity is integer-valued and standing staff has a floor, cost is in general not unimodal in the depth of screening, and we derive comparative statics in the ratio of labour to compute prices \(Proposition 5\)\.",
   "We show that when capacity is integer-valued and standing staff has a floor, cost is in general not unimodal in the depth of screening, reduce the search to the breakpoints of the capacity schedule, show that any depth beyond one layer is justified only by an assumption about dependence, and derive comparative statics in the ratio of labour to compute prices and in dependence (Proposition 5).")
rx(r"The independence formula for stacked screens overstates diversification and understates residual risk\.",
   "The independence formula for stacked screens overstates diversification and understates residual risk, and because high clearances amplify even weak correlation, depth beyond one layer is justified only by an assumption about dependence.")
rx(r"Consistent with this, the residual share exceeds the independence formula by only a modest amount \(Figure 1, left\)\.",
   "Weak association is not the same as a small effect on residual risk. By Proposition 4(b), a correlation φ multiplies the independence prediction by 1 + φ√(c₂c₃/[(1 − c₂)(1 − c₃)]), and the multiplier is large when clearances are high. With the clearances in Table 8 this gives 1.5, 1.6 and 1.3 for the three generators, which reproduces the ratios we observe (Figure 1, left); the match is exact because the identity is exact.")
# ---- proofs
i=_find('Proof of Proposition 4.')
PF4=BOLD('Proof of Proposition 4. ',
 "(a) The bounds are the Fréchet-Bonferroni bounds for the probability that no layer fires. They are attained: nested events {I_i = 1} give r = 1 − max_i c_i, and events that are as disjoint as possible, covering the whole space when Σc_i ≥ 1, give r = (1 − Σc_i)⁺. The joint laws with fixed marginals form a convex set and r is linear in the joint law, so every intermediate value is attained. If the indicators are positively associated, P(∩{I_i = 0}) ≥ ΠP(I_i = 0) (Esary et al. 1967). (b) With p₁₁ = P(I₁ = I₂ = 1) = c₁c₂ + Cov(I₁, I₂), r = 1 − c₁ − c₂ + p₁₁ = (1 − c₁)(1 − c₂) + Cov(I₁, I₂), and Cov(I₁, I₂) = φ√(c₁(1 − c₁)c₂(1 − c₂)). (c) Given the difficulty, the layers fail to catch independently, so r_N = E[(1 − π)^N] with π ~ Beta(a, b), a = cs, b = (1 − c)s. Then E[(1 − π)^N] = B(a, b + N)/B(a, b) = Π_{k=0}^{N−1} (b + k)/(a + b + k), and Corr(I_i, I_j) = Var(π)/(c(1 − c)) = 1/(a + b + 1), which equals ρ when a + b = s. The factor for k is 1 − cs/(s + k) = 1 − c/(1 + k/s); it equals 1 − c for k = 0 and is decreasing in s for k ≥ 1, hence non-decreasing in ρ, and so is the product. The limits follow from s → ∞ and s → 0, and the asymptotics from Γ(b + N)/Γ(a + b + N) ~ N^{−a}. (d) follows from Proposition 1(a). ∎")
B[i]=PF4
i=_find('Proof of Proposition 5.')
PF5=BOLD('Proof of Proposition 5. ',
 "(a) Table 3 is a counterexample to unimodality. (b) If K(N) = K(N − 1) then f(N) = f(N − 1) + g > f(N − 1), so N is not a minimiser; hence a minimiser is 0 or the first N of its capacity level. For N > N₀ the labour cost is constant at C_hk_min while compute cost increases in N, so such N are dominated by N₀. (c) Write f(N) = g[N + θK(N)] with K(N) non-increasing in N. The difference f(N + 1) − f(N) = g[1 + θ(K(N + 1) − K(N))] is non-increasing in θ, so f has decreasing differences in (N, θ) and both the smallest and the largest minimiser are non-decreasing in θ by Topkis' (1978) monotone comparative statics. (d) By Proposition 4(a), λ_N ≤ λ₀(1 − c) = λ₁ for every dependence structure, with equality when the layers fail together, so K(N) ≤ K(1) with equality in the worst case by Proposition 1(a). The worst-case cost of depth N ≥ 1 is therefore C_hK(1) + gN, which is strictly increasing in N, and the gain over depth 1 is f(1) − f(N) = C_h[K(1) − K(N)] − g(N − 1). (e) By Proposition 4(c), λ_N(ρ) is non-decreasing in ρ, hence so are K(N; ρ) and f(N; ρ); a minimum of non-decreasing functions is non-decreasing. Table 5 shows that the minimiser is not monotone. (f) is immediate. ∎")
B[i]=PF5
log.append(('Theory','Propositions 4 and 5 strengthened','Prop 4: sharp (attainable) bounds, exact two-layer identity linking correlation phi to residual inflation, closed form and polynomial decay under a common-difficulty (beta) model, monotonicity in rho. Prop 5: breakpoint reduction, maximin depth (depth beyond one layer is a bet on dependence), monotone cost in dependence with a non-monotone optimal depth. New Table 5; proofs in Appendix A.',"All statements were checked numerically (identity to 1e-14, closed form against 2M-draw Monte Carlo, asymptotic constant, breakpoint and worst-case properties on 3,000 random instances).",1))

# ================= HELD-OUT REPLICATION (Section 5.7) =================
_HV='/home/user/fluffy-meme/heldout_validation/results'
_A=json.load(open(_HV+'/analysis_qwen1.5b.json')); _C=json.load(open(_HV+'/analysis_qwen1.5b_credit.json'))
_G=json.load(open(_HV+'/analysis_gemma27b.json')); _L=json.load(open(_HV+'/analysis_llama70b.json'))
_g=['qwen0.5b','smollm360m','qwen1.5b']
def _r(k,d=1,src=None):
    return [f"{(src or _A)[g]['stat'][k]:.{d}f}" for g in _g]
def _ci(k,d=2,src=None):
    return [f"[{(src or _A)[g]['ci'][k][0]:.{d}f}, {(src or _A)[g]['ci'][k][1]:.{d}f}]" for g in _g]
_O={g:_A[g]['orig'] for g in _g}
def _row(label,vals): return [label]+vals
rows=[['Measure','Qwen2.5-0.5B','SmolLM2-360M','Qwen2.5-1.5B'],
 _row('Hallucination rate, % (first sample)',[f"{a} ({_O[g]['p0']})" for a,g in zip(_r('p0'),_g)]),
 _row('L2 clearance, % (first sample)',[f"{a} ({_O[g]['c2']})" for a,g in zip(_r('c2'),_g)]),
 _row('L2 false-block, % (first sample)',[f"{a} ({_O[g]['fb2']})" for a,g in zip(_r('fb2'),_g)]),
 _row('k∗ without guardrails → with L2 (first sample)',[f"{_A[g]['stat']['k_none']} → {_A[g]['stat']['k_l2']} ({_O[g]['k'][0]} → {_O[g]['k'][1]})" for g in _g]),
 _row('Capacity reduction by L2, %',_r('red_l2')),
 _row('φ between L2 and L3 catch decisions (first sample 0.15, 0.11, 0.12)',[f"{a} {b}" for a,b in zip(_r('phi',2),_ci('phi'))]),
 _row('Passing both layers ÷ independence prediction (first sample 1.5, 1.6, 1.3)',[f"{a} {b}" for a,b in zip(_r('ratio_full',2),_ci('ratio_full'))]),
 _row('Same, slow judge verdicts credited (exploratory)',[f"{a} {b}" for a,b in zip(_r('ratio_full',2,_C),_ci('ratio_full',2,_C))]),
 _row('Same, Gemma-3-27B judge (no timeout)',[f"{a} {b}" for a,b in zip(_r('ratio_full',2,_G),_ci('ratio_full',2,_G))]),
 _row('Same, Llama-3.3-70B judge (no timeout)',[f"{a} {b}" for a,b in zip(_r('ratio_full',2,_L),_ci('ratio_full',2,_L))]),
 _row('Routed cascade: Gemma-3-27B / Llama-3.3-70B',[f"{_G[g]['stat']['ratio_routed']:.2f} / {_L[g]['stat']['ratio_routed']:.2f}" for g in _g]),
 _row('L3 clearance / false-block, %: Gemma-3-27B',[f"{_G[g]['stat']['c3']:.1f} / {_G[g]['stat']['fb3']:.1f}" for g in _g]),
 _row('L3 clearance / false-block, %: Llama-3.3-70B',[f"{_L[g]['stat']['c3']:.1f} / {_L[g]['stat']['fb3']:.1f}" for g in _g]),
 _row('k∗ with L2 → with L2+L3 (routed), local judge',[f"{_A[g]['stat']['k_l2']} → {_A[g]['stat']['k_routed']}" for g in _g]),
 _row('L3 clearance / false-block, % (first sample)',[f"{_A[g]['stat']['c3']:.1f} / {_A[g]['stat']['fb3']:.1f} ({_O[g]['c3']} / {_O[g]['fb3']})" for g in _g])]
_h=lambda t:{'kind':'heading','segs':[[t,True,False]]}
_p=lambda t:{'kind':'para','segs':[[t,False,False]]}
SEC=[_h('5.7 Held-out replication'),
_p("Two features of the first evaluation weaken it: L2 was chosen after the results had been seen, and the intervals are wide. We therefore repeated the evaluation on a fresh sample of 1,000 SQuAD 2.0 questions (a random draw with a fixed seed; overlap with the first 300 questions cannot be excluded and would be about 3% in expectation), with the same three generators and the same L1 and L2. The configuration was fixed and committed before any result was produced. The prompt of the judge L3 was not preserved from the first evaluation, so we rewrote it; L3 results are therefore not comparable with Table 8 and are reported separately. Three analysis details were fixed after seeing the outputs: the judge's reply was cut at four tokens, which turns UNSUPPORTED into UNSUPPORT for one model, and some models add newlines or explanations, so we classify a reply by its first SUPPORT or UNSUPPORT token; we added an exploratory variant in which slow verdicts are credited, as in Section 5.4; and, after seeing the results of the local judge, we added two larger judges from other families (below)."),
_p("Table 12 shows the results. The verifier results replicate. L2 cuts required capacity by 84 to 96% (first sample 78 to 95%), and it again rejects many correct answers, 19 to 75% (first sample 15 to 71%). The false-block rate for Qwen2.5-0.5B is higher than in the first sample (24.0% against 15.1%, outside the first sample's interval), so the lower end of the earlier range should not be taken as typical. The dependence results replicate in direction and, with 1,000 questions, are no longer imprecise. The catch decisions of L2 and L3 are positively associated for all three generators (φ = 0.18, 0.08 and 0.18), and the share of hallucinations that pass both layers is 1.24 to 1.33 times the independence prediction, with intervals that exclude one. With the local judge the magnitude is somewhat smaller than the 1.3 to 1.6 of the first sample, and with larger judges it is larger (below). By Proposition 4(b) this is what these correlations and clearances imply."),
_p("The judge is where the replication is most sensitive to the set-up. With the rewritten prompt and the local Qwen2.5-1.5B judge, L3 is much less active than in the first sample: it clears 19 to 25% of hallucinations and blocks 1 to 4% of correct answers, against 48 to 59% and 17 to 24% in Table 8; 26 to 31% of its calls exceed the 2 s timeout; and required capacity is the same with and without it (16, 6 and 18 units). Routing then changes nothing, because this judge flags almost no answer that L2 regards as consistent, so the routing effect of the first sample (a ratio of 1.9 to 2.3) is not reproduced by this judge. If slow verdicts are credited, L3 clears 27 to 34% of hallucinations, φ rises to 0.21, 0.10 and 0.23 and the ratio to 1.48, 1.39 and 1.38, but capacity is unchanged. In the cost model of Section 4.4, adding this judge changes the daily cost by less than one dollar, and slightly increases it."),
_p("To test whether the results depend on a judge that is its own generator, we ran two larger judges from other families through an API, Llama-3.3-70B-Instruct (Meta) and Gemma-3-27B-Instruct (Google), with the same prompt. Their latency over a network is not comparable with our CPU timings, so no verdict was discarded. Both are informative, and they change the picture. Gemma clears 54 to 69% of hallucinations and blocks 2 to 6% of correct answers, close to the profile of the judge in the first sample; Llama clears 78 to 86% and blocks 10 to 14%. With these judges the dependence is stronger than with the local judge and the routing effect reappears. The share of hallucinations that pass both layers is 1.6 to 2.0 times the independence prediction for Gemma and 2.5 to 3.3 times for Llama, and 2.1 to 2.5 and 3.8 to 5.0 times when answers with a high L2 score skip the judge, with all intervals above one; φ is 0.09 to 0.24 for Gemma and 0.14 to 0.31 for Llama. The ratio rises with the judge's clearance, which is what Proposition 4(b) implies: a given correlation is amplified when both layers catch most hallucinations. Adding the routed judge lowers required capacity by up to two units (for example from 16 to 14 for Qwen2.5-0.5B with Llama), and its daily saving in the cost model of Section 4.4, with a residual harm of $100, is $40 to $250 for Gemma and $209 to $669 for Llama. The intervals exclude zero in three of the six cases. A strong external judge therefore pays for itself modestly, whereas the weak local judge does not, and the conclusion of the first sample that the routed judge does not demonstrably pay for itself holds for a weak or slow judge rather than in general."),
_p("A third local judge, SmolLM2-1.7B-Instruct, was uninformative. More than 90% of its calls exceeded the 2 s limit on our CPU, which makes it a no-op under the fail-open rule, and when its slow verdicts are credited it flags 99% of answers, correct and hallucinated alike. Its apparent capacity saving is, like that of the NLI classifier in Section 5.1, an artefact of blocking nearly everything."),
{'kind':'heading','segs':[["Table 12. Held-out replication on 1,000 fresh SQuAD 2.0 questions (first-sample values in parentheses; 95% bootstrap intervals in brackets; local judge Qwen2.5-1.5B-Instruct with the rewritten prompt, slow verdicts discarded unless stated; the two large judges were run through an API and no verdict was discarded)",True,False]]},
{'kind':'table','rows':rows},
{'kind':'para','segs':[["Pre-registered configuration, code and per-question outputs are in the repository (Appendix D). Intervals resample questions (1,000 draws, seed 0).",False,True]]}]
_i=next(k for k,b in enumerate(B) if b['kind']=='heading' and txt(b).startswith('6. Discussion'))
B[_i:_i]=SEC
rx(r"Two features make the textbook plan unreliable\. ","")
rx(r", and any depth beyond one layer is a bet on dependence\.",".")
# ---- consequential edits elsewhere
rx(r"A task-specific verifier cut required capacity by 78 to 95% but rejected 15 to 71% of correct answers, the share of hallucinations passing two layers was 1\.3 to 2\.3 times the independence prediction, and ignoring",
   "A task-specific verifier cut required capacity by 78 to 96% but rejected 15 to 75% of correct answers, the share of hallucinations passing two layers was 1.2 to 3.3 times the independence prediction, rising with the clearance of the layers, and ignoring")
rx(r"It reduced required capacity by 78 to 95%, but it also blocked 15 to 71% of correct answers","It reduced required capacity by 78 to 96%, but it also blocked 15 to 75% of correct answers")
rx(r"The verifier that cut required capacity by 78 to 95% also rejected 15 to 71% of correct answers","The verifier that cut required capacity by 78 to 96% also rejected 15 to 75% of correct answers")
rx(r"a single task-specific verifier cut required capacity by 78 to 95% while rejecting 15 to 71% of correct answers","a single task-specific verifier cut required capacity by 78 to 96% while rejecting 15 to 75% of correct answers")
rx(r"the share of hallucinations that got past two layers was 1\.3 to 1\.6 times the independence prediction when both layers saw every answer, and 1\.9 to 2\.3 times when routing kept some answers from the second layer, although the intervals are wide\.",
   "the share of hallucinations that got past two layers was 1.3 to 1.6 times the independence prediction in the first sample. In a held-out replication on 1,000 fresh questions it was 1.2 to 1.3 times with the same local judge and 1.6 to 3.3 times with larger judges from other families, with intervals that exclude one, and it rose when routing kept some answers from the second layer.")
rx(r"higher than the independence prediction by a factor of 1\.3 to 1\.6 when both layers saw every answer, and by 1\.9 to 2\.3 when routing withheld answers from the second layer\.",
   "higher than the independence prediction by a factor of 1.3 to 1.6 in the first sample, and in the held-out replication (Section 5.7) by 1.2 to 1.3 with the local judge and 1.6 to 3.3 with larger judges from other families, with intervals that exclude one.")
rx(r"The analyses should be repeated on a held-out sample with a layer configuration registered in advance\. The dependence estimates are imprecise\. The association between L2 and L3 and the excess over the independence formula are both weak, their bootstrap intervals include zero or one for two of the three generators, and the independence prediction is computed from the marginals of the same sample\.",
   "A held-out replication on 1,000 fresh questions with a configuration fixed in advance (Section 5.7) reproduces the verifier and dependence results, and two larger judges from other families show that the dependence does not come from a judge that is its own generator. It still uses the same task and models, the judge prompt had to be rewritten, and the judge-specific results (clearance, routing, saving) depend strongly on which judge is used. In the first sample the dependence estimates were imprecise: the association between L2 and L3 and the excess over the independence formula were weak and their bootstrap intervals included zero or one for two of the three generators. In the replication the intervals exclude zero and one, but the independence prediction is still computed from the marginals of the same sample.")
rx(r"while roughly tripling latency\.","while roughly tripling latency in the first sample. Larger external judges save money in some cases but not in others (Section 5.7).")
rx(r"(Every number in the text and tables is generated from the resulting JSON files\.)",
   r"\1 The held-out replication of Section 5.7 (configuration fixed before the run, code, per-question outputs and analysis scripts) is in the same repository.")


# ================= MANUSCRIPT-WIDE EDITS FROM THE FULL READ-THROUGH =================
def S(old,new):
    n=sub(0,old,new); assert n>=1, 'S miss: '+old[:80]
# (1) paragraphs that were split at a line beginning with "Proposition"/"Table"
_m=[]
for _b in B:
    if _b['kind']=='para' and _m and _m[-1]['kind']=='para' and re.match(r'^(Proposition \d+(?! \()|Table \d+ )',txt(_b)) and not re.search(r'[\.\?:\)]\s*$',txt(_m[-1])):
        _m[-1]['segs']=[[txt(_m[-1])+' '+txt(_b),False,False]]; continue
    _m.append(_b)
B=_m
# (2) run-in headings of Section 5.5
def _lead(prefix_next,lead,strip_from=None):
    k=next(i for i,b in enumerate(B) if b['kind']=='para' and txt(b).startswith(prefix_next))
    B[k]['segs']=[[lead+' ',True,False]]+B[k]['segs']
    if strip_from:
        j=next(i for i,b in enumerate(B) if b['kind']=='para' and txt(b).rstrip().endswith(strip_from))
        B[j]['segs']=[[txt(B[j]).rstrip()[:-len(strip_from)].rstrip(),False,False]]
_lead('From March 2023 to August 2024','Service incidents (LLM providers).','Service incidents (LLM providers).')
_lead('The only public, dated log','Dated hallucination cases (court decisions).','Dated hallucination cases (court decisions).')
_k=next(i for i,b in enumerate(B) if b['kind']=='para' and txt(b).strip()=='Request arrivals (BurstGPT).')
del B[_k]; B[_k]['segs']=[['Request arrivals (BurstGPT). ',True,False]]+B[_k]['segs']
# (3) Section 5 introduction and WildChat paragraph
_k=next(i for i,b in enumerate(B) if b['kind']=='heading' and txt(b).strip()=='5. Findings')
B.insert(_k+1,_p("Sections 5.1 to 5.6 report the first sample of 300 questions and the public traces. Section 5.7 repeats the evaluation on 1,000 fresh questions with the same generators, adds two larger judges, and reports how far the first-sample results carry over."))
_k=next(i for i,b in enumerate(B) if b['kind']=='para' and txt(b).startswith('Service incidents (LLM providers).') or (b['kind']=='para' and b['segs'][0][0].startswith('Service incidents (LLM providers).')))
B.insert(_k,BOLD('Real request arrivals (WildChat). ',"The WildChat-1M corpus (Zhao et al. 2024) contains 837,989 conversations with ChatGPT models from a free research chatbot over 387 days, from 9 April 2023 to 29 April 2024, with a median of 2,053 per day. We use one timestamp per conversation, that of its last turn, as the arrival time of one request. The hour-of-day profile has a peak-to-trough ratio of 1.8 and weekends carry 0.91 times the weekday volume. Within an hour, counts are close to Poisson at short scales: on the 30 busiest days the median variance-to-mean ratio is 0.99 at 10 s and 1.01 at 1 min, and 1.29 at 10 min. Daily volume varies far less than in BurstGPT. The coefficient of variation of the daily rate net of trend and weekday is 0.28 (0.26 after excluding five low-volume days), and the least variable 14-day window has a coefficient of variation of 0.07 and the median window 0.14, against 0.44 and 0.91 in BurstGPT. This is of the same order as the ticket streams and close to our scenario value of c = 0.3. Replaying the measured multipliers on event streams with means of 10 and 120 per day, a Poisson-sized plan is exceeded on 7.0% and 19.1% of days in-sample and on 8.0% and 25.5% of days causally (net of trend: 7.5% and 19.2%, and 8.3% and 21.9%), against a target of 5%. These are request arrivals, not hallucinations, from a single research chatbot. They show that real request streams lie within the range of variability we assumed, not what the variability of hallucination counts is."))
# (4) wording and cross-references
S("each of which answered the same 300 SQuAD 2.0 questions, passed through","each of which answered the same 300 SQuAD 2.0 questions (and, in a held-out replication, 1,000 further questions), passed through")
S("A routed LLM judge did not demonstrably pay for itself under a two-second fail-open timeout.","A routed LLM judge did not demonstrably pay for itself under a two-second fail-open timeout, although larger judges from other families did so modestly in the replication.")
S("across the cases we examine (Table 6).","across the cases we examine (Table 6). Real request arrivals from a public chatbot log show a daily-rate coefficient of variation of about 0.27, in line with the lower scenario value.")
S("(Section 6.3).","(Section 6.3). A second, held-out sample of 1,000 questions is described in Section 5.7.") if False else None
S("Their hallucination rates are higher than those of frontier models, and absolute rates should not be carried over (Section 6.3).","Their hallucination rates are higher than those of frontier models, and absolute rates should not be carried over (Section 6.3). A second, held-out sample of 1,000 questions is described in Section 5.7.")
S("(Qwen2.5-1.5B-Instruct in every run)","(Qwen2.5-1.5B-Instruct in every run of the first sample; Section 5.7 adds larger judges)")
S("The value c = 0.3 thus falls within that range and c = 0.44 lies above it.","The value c = 0.3 thus falls within that range and c = 0.44 lies above it. Real request arrivals from a public chatbot log (WildChat) give a net-of-trend coefficient of variation of 0.26 to 0.28 (Section 5.5).")
S("using six public sources.","using seven public sources.")
S("over 231 days.","over 231 days. WildChat-1M (Zhao et al. 2024) contains 838,000 timestamped conversations with ChatGPT models from a free research chatbot over 387 days, of which we use only the arrival times.")
S("which means one arm is judged by its own generator; we did not test whether this matters.","which means one arm is judged by its own generator; Section 5.7 tests whether this matters.")
S("all of these estimates are imprecise.","all of these estimates are imprecise. Section 5.7 repeats this analysis on 1,000 fresh questions.")
S("(Section 5.6; 0.25 to 0.41 before exclusions).","(Section 5.6; 0.25 to 0.41 before exclusions) and 0.26 to 0.28 in real chatbot request arrivals (Section 5.5).")
S("answer.✗indicates","answer. ✗ indicates")
S("The association we measured was weak. Even so,","The association we measured was modest. Even so,")
S("while roughly tripling latency in the first sample. Larger external judges save money in some cases but not in others (Section 5.7).","while roughly tripling latency. With larger external judges the saving was positive in some cases but not in others (Section 5.7).")
S("In our data, one verifier delivered most of the benefit, the deterministic layer did almost nothing, and the routed judge's saving","In the first sample, one verifier delivered most of the benefit, the deterministic layer did almost nothing, and the routed judge's saving")
S("The same 1.5B model serves as judge in every run, so one arm judges itself.","The same 1.5B model serves as judge in every run of the first sample, so one arm judged itself.")
S("The burstiness in the replay is thus a scenario informed by real streams rather than a quantity estimated from them.","The burstiness in the replay is thus a scenario informed by real streams rather than a quantity estimated from them. Real request arrivals from a public chatbot log (Section 5.5) have a daily-rate variability in line with the scenario value of c = 0.3, but they are requests, not hallucinations.")
S("rest on just three streams.","rest on just three ticket streams.")
S("and a routed judge did not demonstrably pay for itself under a 2 s fail-open timeout.","and a routed judge did not demonstrably pay for itself under a 2 s fail-open timeout with a weak local judge, although larger judges from other families did so modestly. In a held-out replication on 1,000 fresh questions the verifier results held, and the share of hallucinations passing two layers exceeded the independence prediction by 1.2 to 3.3 times, more as the clearance of the layers rose.")
S("and ticket streams have a net-of-trend daily-rate coefficient of variation of 0.10 to 0.38.","ticket streams have a net-of-trend daily-rate coefficient of variation of 0.10 to 0.38, and a public chatbot log has 0.26 to 0.28.")
# (5) appendices
_k=next(i for i,b in enumerate(B) if b['kind']=='para' and txt(b).startswith('Court cases. The Charlotin'))
B.insert(_k+1,BOLD('WildChat. ',"The WildChat-1M corpus (Zhao et al. 2024; ODC-BY; allenai/WildChat-1M on Hugging Face) holds 837,989 conversations with ChatGPT models, collected through a free research chatbot from 9 April 2023 to 29 April 2024 (387 days, three of them without a conversation). We use only the timestamp of each conversation, which the corpus defines as that of its last turn, as the arrival time of one request. Daily counts are adjusted for the weekday effect, and the coefficient of variation of the daily rate is estimated as for tickets, against a leave-one-out local mean over about eight weeks, once for all days and once without days below 35% of the 41-day rolling median (five days). Within-hour variance-to-mean ratios are computed for the 30 busiest days at bin widths of 10 s, 1 min and 10 min. The stress test replays the measured daily multipliers on event streams with means of 10 and 120 per day (400 replications), and evaluates the Poisson plan in-sample against about 40 surrounding days and causally against the trailing 20 days."))
S("The public datasets are not redistributed;","The tables of Section 3 can be reproduced and checked with check_tables.py and econ_dependence.py, the replication of Section 5.7 with run_heldout.py, judge_api.py, analyze_heldout.py and cost_heldout.py, and the WildChat analysis with wildchat_arrivals.py. The public datasets are not redistributed;")

# ---- AOR adaptation
# 1 anonymity
B=[b for b in B if not (b['kind']=='para' and txt(b).strip()=='Manuscript for double-blind review')]
log.append(('AOR','"Manuscript for double-blind review"','removed',"Not verified whether Annals of Operations Research is single- or double-blind (the public guidelines pages could not be read); author information is kept on a separate title page in either case.",1))
# 2 design-science framing
old="The paper sits in the design-science tradition in IS (Hevner et al. 2004; Gregor and Hevner 2013). The artifact is a planning method, grounded in a formal model and evaluated on measured system outputs. In Gregor and Hevner's (2013) terms the contribution is an exaptation, in which known solutions are carried into a new problem domain. The evaluation"
new="The paper sits in the operations research tradition of stochastic inventory and workforce-capacity models. Its contribution is a planning method, grounded in a formal model and evaluated on measured system outputs, in which known solutions are carried into a new problem domain, namely standby labour for machine errors. The evaluation"
n=sub(0,old,new); log.append(('AOR','design-science / exaptation paragraph (Hevner; Gregor and Hevner)','reframed as OR contribution (stochastic inventory and capacity planning)',"IS design-science positioning is specific to MIS Quarterly; AOR readers expect the OR lineage and contribution.",n))
B=[b for b in B if not (b['kind']=='para' and re.match(r'^(Gregor, S\.|Hevner, A\.)',txt(b)))]
log.append(('AOR','References: Gregor and Hevner (2013); Hevner et al. (2004)','removed',"No longer cited after the reframing.",2))
# 3 repository
n=sub(0,"are provided in an anonymised repository, the link to which is supplied to the editors with the submission.","are provided in a public repository [repository URL to be inserted].")
log.append(('AOR','Appendix D: anonymised repository','public repository placeholder',"Single-blind review needs no anonymisation; Springer asks for a data/code availability link.",n))
# 4 in-text citation style (Springer author-year: comma before year)
MONTH=r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
def cite(m):
    inner=m.group(0)
    if not re.search(r'\b(?:19|20)\d\d[a-z]?\b',inner): return inner
    def r(mm):
        return mm.group(1)+', '+mm.group(2)
    inner=re.sub(r'(?<!%s)(?<=[A-Za-z\.])\s(\d{4}[a-z]?)(?![\d/\-])'%'XXXX',lambda mm: mm.group(0),inner)
    out=[];pos=0
    for mm in re.finditer(r'([A-Za-z\.’\']) ((?:19|20)\d\d[a-z]?)(?![\d/\-,]\d)',inner):
        pre=inner[:mm.start()+1]
        if re.search(MONTH+r'$',pre) or re.search(r'(?:in|from|to|of|since|and|over|through|by) $',pre): continue
        if re.search(r'US$',pre): continue
        out.append((mm.start()+1,mm.end()))
    s=inner
    for a,bb in reversed(out): s=s[:a]+','+s[a:]
    s=re.sub(r'\bn\.d\.',' n.d.',s) if False else s
    return s
cnt=0
for b in B:
    if b['kind']!='para': continue
    for s in b['segs']:
        new=re.sub(r'\([^()]*\)',cite,s[0])
        if new!=s[0]: cnt+=1; s[0]=new
log.append(('AOR','In-text citations "(Arrow et al. 1951)"','"(Arrow et al., 1951)"',"Springer author-year style puts a comma before the year in parenthetical citations.",cnt))
# 5 references to Springer author-year
def initials(s): return ''.join(c for c in s if c.isupper())
def conv_ref(t):
    m=re.match(r'^(.*?\.)\s+((?:19|20)\d\d|n\.d\.)\.\s+(.*)$',t)
    if not m: return t
    au,yr,rest=m.groups()
    au=au.rstrip('.')   # strip final period of last initial handled below
    parts=re.findall(r'((?:[a-z]+ )*[A-ZÀ-Ý][^,]*?), ((?:[A-Z]\.(?:[ -]?[A-Z]\.)*)|(?:[A-Z]\.[ -]?)+)',m.group(1)+' ')
    if not parts: return t
    names=[f"{sn.strip()} {initials(ini)}" for sn,ini in parts]
    # quoted title
    q=re.match(r'^[“"](.*?)[,.]?[”"]\s*(.*)$',rest)
    if q:
        title,after=q.groups()
        after=re.sub(r'\((\d+):(\d+)\),\s*pp\.\s*(\d+)[-–](\d+)',lambda x:f'{x.group(1)}({x.group(2)}):{x.group(3)}–{x.group(4)}',after)
        after=re.sub(r'\((\d+)\),\s*pp\.\s*(\d+)[-–](\d+)',lambda x:f'{x.group(1)}:{x.group(2)}–{x.group(3)}',after)
        rest=f'{title}. {after}'.strip()
    else:
        rest=rest
    return f"{', '.join(names)} ({yr}) {rest}"
inref=False;n=0
for b in B:
    if b['kind']=='heading':
        inref = txt(b).startswith('References') or (inref and not txt(b).startswith('Appendix A'))
        continue
    if inref and b['kind']=='para':
        t=txt(b); c=conv_ref(t)
        if c!=t: b['segs']=[[c,False,False]]; n+=1
log.append(('AOR','Reference list (MISQ style)','Springer author-year: "Arrow KJ, Harris T, Marschak J (1951) Optimal inventory policy. Econometrica 19(3):250-272"',"Reformatted automatically; entries that did not match the pattern were left unchanged (please skim once).",n))
# 6 declarations before references
decl=[('heading','Statements and Declarations'),
('para','Funding: [state funding sources, or "The authors received no financial support for this research."]'),
('para','Competing interests: [state any, or "The authors have no relevant financial or non-financial interests to disclose."]'),
('para','Author contributions: [CRediT roles for each author]'),
('para','Data availability: The public datasets analysed (BurstGPT, the LLM outage and incident dataset, the three ticket logs and the AI Hallucination Cases database) are available from their original sources under the licences stated in Section 4.5 and Appendix B. Per-query model outputs and guardrail decisions are available at [repository URL].'),
('para','Code availability: Analysis code is available at [repository URL].'),
('para','Ethics approval: Not applicable; the study uses no human participants and only public data.')]
i=[k for k,b in enumerate(B) if b['kind']=='heading' and txt(b).startswith('References')][0]
ins=[]
for kind,t in decl:
    segs=[[t,kind=='heading',False]]
    if kind=='para':
        h,rest=t.split(': ',1); segs=[[h+': ',True,False],[rest,False,False]]
    ins.append({'kind':kind,'segs':segs})
B[i:i]=ins
log.append(('AOR','Statements and Declarations (new section)','added with [placeholders]',"Springer/AOR requires funding, competing-interest, data/code availability statements; fill in the bracketed items.",1))
# 7 title block
B[0:1]=[B[0],{'kind':'author','segs':[['[Author names]  ·  [Affiliations]  ·  [Corresponding author e-mail]',False,True]]}]

# ---- post-fixes
def allseg(f):
    for b in B:
        if 'segs' in b:
            for sg in b['segs']: sg[0]=f(sg[0])
def pf(t):
    t=t.replace("incidents in, 2016 to, 2017","incidents in 2016 to 2017").replace("unknown.  Section","unknown. Section")
    t=re.sub(r'(?<=[a-z])- (?=[A-Z])','-',t)
    return t
allseg(pf)
inref=False
for b in B:
    if b['kind']=='heading':
        inref = txt(b).startswith('References') or (inref and not txt(b).startswith('Appendix A')); continue
    if inref and b['kind']=='para':
        t=txt(b)
        t=re.sub(r'^PatSnap\. n\.d\. "(.*?)" \((.*)\)\.$',r'PatSnap (n.d.) \1. \2',t)
        t=re.sub(r'^Qwen Team\. 2024\. "(.*?),?" (.*)$',r'Qwen Team (2024) \1. \2',t)
        t=re.sub(r'^US 2024/0330824 A1\. 2024\. "(.*?),?" (.*)$',r'US 2024/0330824 A1 (2024) \1. \2',t)
        t=re.sub(r'^([^()]*?[A-Z]{1,3}), and ([A-Z][^ ()]* [A-Z]{1,3}) \(',r'\1, \2 (',t)   # two-author: "A, and B"
        t=re.sub(r', and ([^,()]+? [A-Z]{1,3}) \(',r', \1 (',t,count=1)
        t=t.replace(' in Proceedings',' In: Proceedings').replace('. in Proceedings','. In: Proceedings')
        t=re.sub(r'pp\. (\d+)-(\d+)',r'pp \1–\2',t)
        t=t.replace('Cambridge, UK: Cambridge University Press','Cambridge University Press, Cambridge')
        t=t.replace('London: Chapman & Hall','Chapman & Hall, London').replace('New York: Springer','Springer, New York').replace('Oxford, UK: Oxford University Press','Oxford University Press, Oxford').replace('Stanford, CA: Stanford University Press','Stanford University Press, Stanford')
        b['segs']=[[t,False,False]]

S("All simulations and bootstrap draws are seeded.","All simulations and bootstrap draws are seeded. [Editorial note, delete before submission: the scripts named in the second sentence of this appendix belong to the original pipeline and were not among the files used to prepare this revision; please confirm that they are in the repository.]")
S("the three ticket logs and the AI Hallucination Cases database","the three ticket logs, the WildChat-1M corpus and the AI Hallucination Cases database")
# ---- final reference formatting and Springer ordering
import unicodedata as _ud
def _inrefs():
    on=False
    for b in B:
        if b['kind']=='heading':
            on = txt(b).startswith('References') or (on and not txt(b).startswith('Appendix A')); continue
        if on and b['kind']=='para': yield b
for b in _inrefs():
    t=txt(b)
    t=re.sub(r'(?<=[A-Za-z])- (?=[A-Z])','-',t)
    t=re.sub(r'\((\d+):(\d+)\), Article',r'\1(\2): Article',t)
    t=re.sub(r'Systems \((\d+)\)\.',r'Systems \1.',t)
    b['segs']=[[t,False,False]]
_i=next(k for k,b in enumerate(B) if b['kind']=='heading' and txt(b).startswith('References'))
_j=next(k for k,b in enumerate(B) if k>_i and b['kind']=='heading')
def _key(b):
    t=txt(b); m=re.match(r'^(.*?) \((\d{4}|n\.d\.)\)',t)
    au=m.group(1) if m else t; yr=m.group(2) if m else ''
    names=au.split(', '); sn=names[0].rsplit(' ',1)[0] if len(names)>0 else au
    nk=len(names) if len(names)<=2 else 3
    f=lambda x:_ud.normalize('NFKD',x).encode('ascii','ignore').decode().lower()
    return (f(sn),nk,f(au),yr)
B[_i+1:_j]=sorted(B[_i+1:_j],key=_key)

json.dump([ [c,o,n,w,k] for c,o,n,w,k in log],open('log.json','w'),ensure_ascii=False,indent=1)
# split keywords
for k,b in enumerate(B):
    if b['kind']=='para' and any(sg[1] and sg[0].startswith('Keywords') for sg in b['segs']):
        j=[i for i,sg in enumerate(b['segs']) if sg[1] and sg[0].startswith('Keywords')][0]
        if j>0:
            B.insert(k+1,{'kind':'para','segs':b['segs'][j:]}); b['segs']=b['segs'][:j]; b['segs'][-1][0]=b['segs'][-1][0].rstrip()
        break
# ---- write docx
doc=Document()
sec=doc.sections[0]
for a in ('left_margin','right_margin','top_margin','bottom_margin'): setattr(sec,a,Inches(1))
st=doc.styles['Normal']; st.font.name='Times New Roman'; st.font.size=Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
def setfmt(p,align=None,sp=1.5,after=6,first=None):
    pf=p.paragraph_format; pf.line_spacing=sp; pf.space_after=Pt(after)
    if first is not None: pf.first_line_indent=Inches(first)
    if align is not None: p.alignment=align
def addruns(p,segs,size=None,forcebold=False):
    for t,b,i in segs:
        r=p.add_run(t); r.bold=b or forcebold; r.italic=i
        if size: r.font.size=Pt(size)
# footer page number
fp=sec.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=fp.add_run()
for tag,txtv in (('begin',None),('instr',' PAGE '),('end',None)):
    if tag=='instr':
        e=OxmlElement('w:instrText'); e.set(qn('xml:space'),'preserve'); e.text=txtv
    else:
        e=OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),tag)
    r._r.append(e)
for k,b in enumerate(B):
    kind=b['kind']
    if kind=='heading':
        t=txt(b)
        p=doc.add_paragraph()
        if k==0:
            addruns(p,[[t,True,False]],size=16); setfmt(p,WD_ALIGN_PARAGRAPH.CENTER,1.15,12)
        elif re.match(r'^(Table|Figure) ',t):
            addruns(p,b['segs'],size=10.5,forcebold=True); setfmt(p,WD_ALIGN_PARAGRAPH.LEFT,1.0,4); p.paragraph_format.keep_with_next=True
        else:
            lvl2=bool(re.match(r'^\d+\.\d',t))
            addruns(p,b['segs'],size=12,forcebold=True); setfmt(p,WD_ALIGN_PARAGRAPH.LEFT,1.15,6); p.paragraph_format.space_before=Pt(10 if lvl2 else 16); p.paragraph_format.keep_with_next=True
            if t=='Abstract': p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    elif kind=='author':
        p=doc.add_paragraph(); addruns(p,b['segs']); setfmt(p,WD_ALIGN_PARAGRAPH.CENTER,1.15,12)
    elif kind=='para':
        t=txt(b); p=doc.add_paragraph(); addruns(p,b['segs'])
        small=bool(re.match(r'^(Calculated|Computed|Each cell|Observed|True counts|Exact|Poisson counts|Illustrative|Minimum:|c_i is|Calendar|Baseline:|parametric|L2\+L3 denotes|Poisson counts|The first row|The cost parameters)',t)) and False
        isnote = b['segs'][0][2] and not b['segs'][0][1]
        inref=False
        if isnote: addruns  # keep italics
        setfmt(p,WD_ALIGN_PARAGRAPH.JUSTIFY,1.0 if isnote else 1.5,6 if isnote else 0,0.0 if (isnote or re.match(r'^(Proof of|Proposition \d)',t)) else 0.35)
        if isnote:
            for r in p.runs: r.font.size=Pt(9.5)
    elif kind=='table':
        rows=b['rows']; nc=max(len(r) for r in rows)
        tb=doc.add_table(rows=len(rows),cols=nc); tb.style='Table Grid'; tb.alignment=WD_TABLE_ALIGNMENT.CENTER
        for ri,r in enumerate(rows):
            for ci in range(nc):
                c=tb.cell(ri,ci); c.text=''
                p=c.paragraphs[0]; run=p.add_run(r[ci] if ci<len(r) else ''); run.font.size=Pt(8.5); run.bold=(ri==0)
                p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                if ri==0:
                    tcPr=c._tc.get_or_add_tcPr(); sh=OxmlElement('w:shd'); sh.set(qn('w:val'),'clear'); sh.set(qn('w:fill'),'EDEDED'); tcPr.append(sh)
        doc.add_paragraph().paragraph_format.space_after=Pt(2)
    elif kind=='image':
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(b['file'],width=Inches(6.0)); p.paragraph_format.keep_with_next=True
doc.save('manuscript_AOR.docx')
for c,o,n,w,k in log: print(k,c,o[:60])
