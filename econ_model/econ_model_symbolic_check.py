import sympy as sp
a,al,t=sp.symbols('a alpha t',real=True)
v,c,w,r,h,H,kN,N,tau,kap=sp.symbols('v c w r h H kN N tau kappa',positive=True)
D=2*v*r+c*w
# attacker payoff with price
beta=al+a/w
UA=v*a*(1-r*beta)-c*a**2/2-t*a
asol=sp.solve(sp.diff(UA,a),a)[0]
print('a*=',sp.simplify(asol), ' check', sp.simplify(asol-w*(v*(1-r*al)-t)/D))
pu=1-r*beta
harm=sp.simplify((a*pu).subs(a,asol))
print('harm check', sp.simplify(harm-( asol**2*(c/v+r/w)+asol*t/v)))
# t=0 stackelberg
L0=sp.simplify(h*(a*pu).subs(a,asol).subs(t,0)+kN*al**2/2)
aS=sp.solve(sp.diff(L0,al),al)[0]
G=w*v*(c*w+v*r)/D**2
print('alphaS', sp.simplify(aS-2*h*G*r/(kN+2*h*G*r**2)))
# Nash: platform FOC given a (a fixed): d/dalpha [h a(1-r(al+a/w)) + kN al^2/2]
aN,alN=sp.symbols('aN alN')
foc_p=sp.diff(h*aN*(1-r*(al+aN/w))+kN*al**2/2,al)
sol=sp.solve([foc_p.subs(al,alN), aN-w*(v*(1-r*alN))/D],[aN,alN],dict=True)[0]
print('alphaN', sp.simplify(sol[alN]-h*r*(w*v/D)/(kN+h*r**2*(w*v/D))))
# price model: planner loss
Lam=H*(a*pu).subs(a,asol)+kN*al**2/2+N*t**2/(2*tau)
Lam=sp.expand(sp.simplify(Lam))
Laa=sp.simplify(sp.diff(Lam,al,2)); Ltt=sp.simplify(sp.diff(Lam,t,2)); Lat=sp.simplify(sp.diff(Lam,al,t))
print('Laa',Laa); print('Ltt',Ltt); print('Lat',Lat)
print('Lt at t=0', sp.simplify(sp.diff(Lam,t).subs(t,0)))
