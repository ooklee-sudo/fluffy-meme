"""Proposition 8 / Lemma (Section 4.6): numerical check of the closed forms.
Part 1: grid search confirms the entrant's best response a_E = (t+g)/(2 gamma) + c/(2m) and the incumbent's share
x(g) = (3t-g)/(4t) + gamma c/(4tm) under a fixed-margin format with quality gap g, and that best-response iteration
converges to the symmetric full-answer equilibrium a = t/gamma + c/m with profit m t/(2 gamma).
Part 2: threshold Delta_H* = 3t + gamma c/m - 2 m t^2/(gamma (R - c_O)) and comparative statics (Prop. 8(iii)).
Part 3: profit under summaries vs. full answers around the threshold.
Parameters: t=1, gamma=1, m=2, c=0.3, R=1.4, c_O=0.05.
(The session's first attempt used scipy's bounded minimizer, which failed for this objective; it was replaced by
the grid search in Part 1. The threshold printout of that first attempt is kept as Part 3.)
No data needed; runs in a few seconds."""
import numpy as np
t,gam,m,c,R,cO=1.0,1.0,2.0,0.3,1.4,0.05
grid=np.linspace(0,5,500001)
for g in [0,0.5,1.0,1.5]:
    x=np.clip(0.5+(gam*grid-g)/(2*t),0,1); prof=(1-x)*(m*grid-c); i=prof.argmax()
    print(g,"aE",round(grid[i],4),"formula",round((t+g)/(2*gam)+c/(2*m),4),"x",round(x[i],4),"formula",round((3*t-g)/(4*t)+gam*c/(4*t*m),4))
# check symmetric A equilibrium by best-response iteration
aI=aE=1.0
for _ in range(200):
    def br(other):
        x=np.clip(0.5+(gam*other-gam*grid)/(2*t),0,1); return grid[(x*(m*grid-c)).argmax()]
    aI,aE=br(aE),br(aI)
print("A eq a",round(aI,4),"formula",t/gam+c/m,"profit",0.5*(m*aI-c),"formula",m*t/(2*gam))
# comparative statics of threshold
D=lambda R,m,c,cO: 3*t+gam*c/m-2*m*t**2/(gam*(R-cO))
print("dR",D(1.5,m,c,cO)-D(1.4,m,c,cO),"dm",D(R,2.1,c,cO)-D(R,2,c,cO),"dc",D(R,m,0.4,cO)-D(R,m,0.3,cO),"dcO",D(R,m,c,0.1)-D(R,m,c,0.05))

# ---- Part 3 (threshold and profits around it)
piA=m*t/(2*gam)
print("piA",piA)
DH=3*t+gam*c/m-2*m*t**2/(gam*(R-cO)); print("threshold Delta_H*",round(DH,4))
for g in [DH-0.1,DH,DH+0.1]:
    print(round(g,3),"piH",round((R-cO)*((3*t-g)/(4*t)+gam*c/(4*t*m)),4),"piA",piA)
