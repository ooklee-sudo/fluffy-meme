import numpy as np, json, sympy as sp
from scipy.optimize import minimize
# ---------- symbolic ----------
n,v,c,w,r,al=sp.symbols('n v c w r alpha',positive=True)
a=sp.symbols('a',positive=True)
# symmetric Nash from FOC of attacker i: v(1-r al) - (r v/w)(X+a_i) - c a_i =0, X=n a
a_n=sp.solve(v*(1-r*al)-(r*v/w)*(n*a+a)-c*a,a)[0]
print('a_n',sp.simplify(a_n-w*v*(1-r*al)/(c*w+(n+1)*r*v)))
X=n*a_n
pu=1-r*al-r*X/w
print('pu',sp.simplify(pu-(1-r*al)*(c*w+r*v)/(c*w+(n+1)*r*v)))
Kn=n*w*v*(c*w+r*v)/(c*w+(n+1)*r*v)**2
print('Q',sp.simplify(X*pu-Kn*(1-r*al)**2))
# cartel
Xc=sp.symbols('Xc',positive=True)
Xcs=sp.solve(v*(1-r*al)-2*r*v*Xc/w-c*Xc/n,Xc)[0]
print('Xc',sp.simplify(Xcs-n*w*v*(1-r*al)/(2*n*r*v+c*w)))
print('ratio',sp.simplify(X/Xcs))
Anbar=n*w*v/(c*w+(n+1)*r*v)
print('2K-A', sp.simplify(2*Kn-Anbar - Anbar*(c*w+(1-n)*r*v)/(c*w+(n+1)*r*v)))
# derivative of K_n in n
print('dK/dn sign', sp.simplify(sp.diff(Kn,n)*(c*w+(n+1)*r*v)**3/(w*v*(c*w+r*v)) - ((c*w+r*v)-(n)*r*v + 0) ))
