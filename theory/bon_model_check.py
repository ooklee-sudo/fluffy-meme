import numpy as np
from math import erf, sqrt, exp, pi as PI, log
rng = np.random.default_rng(0)
# exact m_N = E[max of N std normals] by numerical integration of 1-Phi^N
xs = np.linspace(-9, 9, 40001); dx = xs[1]-xs[0]
Phi = 0.5*(1+np.vectorize(erf)(xs/sqrt(2)))
def mN(N):
    return float(np.sum(xs*N*Phi**(N-1)*np.exp(-xs**2/2)/sqrt(2*PI))*dx)
Ns = np.arange(1, 400)
m = np.array([mN(int(n)) for n in Ns])
print('m_N increasing:', bool(np.all(np.diff(m) > 0)), ' concave:', bool(np.all(np.diff(m, 2) < 1e-9)))
print('m_N vs sqrt(2lnN):', [(n, round(m[n-1], 3), round(sqrt(2*log(n)), 3)) for n in (2, 10, 100, 399)])

def U(N, rho, sig, pi, d, phi=0.0, cs=0.0):
    q = (1-pi)**N; dphi = (1-phi)*d
    return q*(rho*sig*m[N-1] + dphi) - dphi - cs*N
# Monte Carlo check of U with always-winning exploiters
def mc(N, rho, sig, pi, d, reps=100000):
    tot = 0.0
    for _ in range(reps//1):
        ex = rng.random(N) < pi
        if ex.any(): tot += -d
        else:
            V = rng.normal(0, sig, N); J = rho*V/sig + sqrt(1-rho**2)*rng.normal(0, 1, N)
            tot += V[np.argmax(J)]
    return tot/reps
for N in (5, 30):
    print('N', N, 'formula', round(U(N, .6, 1, .02, 3), 3), 'MC', round(mc(N, .6, 1, .02, 3, 40000), 3))
# optimal N and approx
def Nstar(rho, sig, pi, d, phi=0.0, cs=0.0):
    u = [U(int(n), rho, sig, pi, d, phi, cs) for n in Ns]; return int(Ns[int(np.argmax(u))])
for pi in (0.01, 0.02, 0.05):
    for d in (1, 3):
        print('pi', pi, 'd', d, 'N*', Nstar(.6, 1, pi, d), ' approx rho*sig/(pi*d)=', round(.6/(pi*d), 1))
print('inspection raises N*:', [(phi, Nstar(.6, 1, .01, 3, phi)) for phi in (0, .5, .8, .95)])
# unimodality
u = np.array([U(int(n), .6, 1, .02, 3, 0, 0.0005) for n in Ns]); dd = np.diff(u)
print('sign changes of dU:', int(np.sum(np.diff(np.sign(dd)) != 0)))
# inspection threshold Nc
c_G, phi_, d_, pi_ = 0.05, 0.9, 3, 0.02
Nc = log(1-c_G/(phi_*d_))/log(1-pi_); print('Nc', round(Nc, 2))
print('gain from inspection at N=Nc-3, Nc+3:', [round((1-(1-pi_)**N)*phi_*d_ - c_G, 4) for N in (int(Nc)-3, int(Nc)+3)])
