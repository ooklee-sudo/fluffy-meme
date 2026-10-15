# Optimal search depth under a gameable judge, with an inspection option

Setup. N candidates are generated and the one with the highest judge score J is shipped. Gold value V of an honest
candidate is N(0, s^2); J is a standard-normal score with corr(J, V) = rho, so the expected gold value of the best-of-N
honest candidate is rho*s*m_N, where m_N = E[max of N iid N(0,1)] (increasing and concave in N).
Each candidate is, independently with probability pi, an exploit: it games the rubric, always receives the top J, and has
gold value -d (d > 0, relative to the incumbent). lambda = -ln(1-pi).

1. No inspection. The shipped candidate is an exploit iff at least one exploit is in the pool, probability 1-(1-pi)^N:
   U(N) = (1-pi)^N * rho*s*m_N - (1-(1-pi)^N) * d - c_s*N.
   FOC: e^{-lambda N}[ rho*s*m'_N - lambda(rho*s*m_N + d) ] = c_s.
   U is quasi-concave: the bracket is strictly decreasing, and once it is <= 0 then U' < 0. So N* is unique, decreasing in pi and d.
2. Inspection with detection power phi (a canary that flags an exploit with probability phi; a flagged candidate is
   replaced by the incumbent, value 0) at cost c_G. Effective damage d_phi = (1-phi)*d, so 1. holds with d -> d_phi:
   N*(phi) is increasing in phi. Inspection and search are complements.
3. When to inspect: gain phi*d*(1-(1-pi)^N) > c_G, i.e. N >= N_c = ln(1 - c_G/(phi*d)) / ln(1-pi) (needs c_G < phi*d).
   Below N_c ship on J alone; above N_c inspect before shipping. Staging falls out of the search depth.
Numerical checks (theory/bon_model_check.py): formula equals Monte Carlo; m_N increasing and concave; U unimodal;
N* = 14, 8, 4 for pi = 0.01, 0.02, 0.05 (d=1, rho*s=0.6); N*(phi) = 8, 12, 17, 21 for phi = 0, .5, .8, .95
(pi=.01, d=3); N_c = 10.1 for c_G=.5, phi=.9, d=3, pi=.02.
