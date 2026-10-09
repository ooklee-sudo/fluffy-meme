import numpy as np, json, sympy as sp
# ---------- symbolic derivation of the leader's FOC under noisy observation ----------
al,lam,ae,s2=sp.symbols('alpha lambda alpha_e sigma2',real=True)
v,c,w,r,h,N,kap,phi=sp.symbols('v c w r h N kappa phi',positive=True)
D=2*v*r+c*w; A=w*v/D; G=A*(c*w+v*r)/D
xi,eta=sp.symbols('xi eta',real=True)
# attacker: a(z)=A(1-r*(ae+lam*(z-ae))), z=alpha+xi+eta ; realized alpha_r=alpha+xi
z=al+xi+eta
a=A*(1-r*(ae+lam*(z-ae)))
ar=al+xi
harm=a*(1-r*(ar+a/w))
# expectation over (xi,eta) ~ independent normals with var s_xi2, s_eta2 ; lam = s_xi2/(s_xi2+s_eta2)
sx2,se2=sp.symbols('sx2 se2',positive=True)
def E(expr):
    expr=sp.expand(expr)
    P=sp.Poly(expr,xi,eta); tot=0
    m={0:1,1:0,2:None}
    for (i,j),co in P.terms():
        def mom(k,var):
            if k%2==1: return 0
            return sp.factorial2(k-1)*var**(k//2) if k>0 else 1
        tot+=co*mom(i,sx2)*mom(j,se2)
    return sp.simplify(tot)
Eh=E(harm).subs(se2,sx2*(1-lam)/lam)   # lam=sx2/(sx2+se2)
Eh=sp.simplify(Eh)
L=h*Eh+N*(kap/2)*(al**2+sx2)+N*phi*al
dL=sp.diff(L,al).subs(ae,al)           # rational expectations: conjecture = chosen
aL=sp.solve(dL,al)[0]
x=h*A*r*(1+lam*c*w/D)
g=(x-N*phi)/(N*kap+r*x)
print('alpha(lambda) matches g(x):',sp.simplify(aL-g))
# equilibrium expected harm identity
Eh_eq=sp.simplify(Eh.subs(ae,al))
print('E harm identity:',sp.simplify(Eh_eq-(G*(1-r*al)**2+lam*r**2*sx2*G)))
