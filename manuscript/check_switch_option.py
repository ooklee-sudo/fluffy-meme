from math import erf,exp,sqrt,pi as PI
cdf=lambda x:0.5*(1+erf(x/sqrt(2))); pdf=lambda x:exp(-x*x/2)/sqrt(2*PI)
def F(sig,a,p,nu,tau=1,om=0.2,d=0.95,cg=0.02):
    sa2=(sig**2+p*nu**2)/a**2; sJ2=1/(1/tau**2+1/sa2); v=sJ2**2/(sJ2+om**2); r=sqrt(v)
    g=lambda x: x-(d*(x*cdf(x/r)+r*pdf(x/r))-cg)
    lo,hi=-50,50
    for _ in range(200):
        m=(lo+hi)/2
        if g(m)>0: hi=m
        else: lo=m
    return max(0,m)
print([round(F(s,0.8,0,1.5),2) for s in (0.4,0.7,1.2)], round(F(0.7,0.01,0,1.5),2))
print([round(F(0.7,0.8,p,1.5),2) for p in (0,0.1,0.3)])
for a in (0.8,0.3,0.1,0.03,0.01): print(a, round(F(0.7,a,0.3,1.5)-F(0.7,a,0,1.5),4))
