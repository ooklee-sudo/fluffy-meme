# Calibration on the Azure LLM inference trace and non-exponential service times

## X  Simulator cross-check

MMPP(k=3,T=2)/M/8 at rho=0.8: simulated E[sojourn] = 2.88 (exact CTMC in results/mmpp_serving.md: 2.91).

## Conversation trace

19366 requests over 3502s: mean rate 5.53/s, inter-arrival CV^2 = 1.20 (Poisson: 1), mean service 6.91s, service-time cs^2 = 0.49 (exponential: 1), offered load 38.2 servers.

### A/B  Arrival burstiness and MMPP(2) fit

| window (s) | IDC trace (Poisson = 1) | IDC fitted MMPP(2) |
|---|---|---|
| 1 | 1.39 | 1.31 |
| 2 | 1.70 | 1.62 |
| 5 | 2.54 | 2.54 |
| 10 | 3.87 | 4.06 |
| 30 | 8.95 | 9.84 |
| 60 | 16.41 | 17.74 |
| 120 | 30.60 | 31.15 |
| 300 | 61.70 | 57.96 |

Fitted MMPP(2): burst rate 11.25/s (2.0x mean) for 5% of time, mean burst 184.5s; off rate 5.23/s.

### C  Replay vs. models (service times from tokens; tau = one mean service time)

| rho | c | real trace: E[wait] / P(wait>tau) | fitted MMPP | Poisson |
|---|---|---|---|---|
| 0.60 | 64 | 0.00 / 0.000 | 3.73 / 0.088 | 0.00 / 0.000 |
| 0.75 | 51 | 0.08 / 0.000 | 12.65 / 0.124 | 0.01 / 0.000 |
| 0.85 | 45 | 0.51 / 0.008 | 32.54 / 0.220 | 0.17 / 0.000 |
| 0.91 | 42 | 2.20 / 0.117 | 105.54 / 0.444 | 0.61 / 0.002 |

(real trace = one 1-hour path; models = mean of 3 long paths of the same rate)

### D  Service-time sensitivity (fitted MMPP vs Poisson; tau = one mean service time)

At c=48 servers (rho=0.8). Servers needed for P(wait>tau)<=5%.

| service | Poisson: E[wait] / P>tau | MMPP: E[wait] / P>tau | delay ratio | c Poisson | c MMPP | extra |
|---|---|---|---|---|---|---|
| exp | 0.06 / 0.000 | 32.19 / 0.210 | 533.6x | 41 | 75 | 83% |
| logn4 | 0.09 / 0.000 | 21.15 / 0.184 | 232.5x | 43 | 72 | 67% |
| logn16 | 0.19 / 0.004 | 23.02 / 0.164 | 121.3x | 45 | 68 | 51% |
| trace | 0.05 / 0.000 | 36.59 / 0.241 | 727.7x | 41 | 76 | 85% |

## Code trace

8819 requests over 3436s: mean rate 2.57/s, inter-arrival CV^2 = 172.96 (Poisson: 1), mean service 1.86s, service-time cs^2 = 1.21 (exponential: 1), offered load 4.8 servers.

### A/B  Arrival burstiness and MMPP(2) fit

| window (s) | IDC trace (Poisson = 1) | IDC fitted MMPP(2) |
|---|---|---|
| 1 | 13.19 | 12.36 |
| 2 | 23.69 | 22.74 |
| 5 | 47.54 | 48.88 |
| 10 | 71.85 | 79.97 |
| 30 | 124.88 | 132.72 |
| 60 | 166.89 | 153.02 |
| 120 | 213.53 | 163.50 |
| 300 | 151.62 | 169.79 |

Fitted MMPP(2): burst rate 26.65/s (10.4x mean) for 5% of time, mean burst 7.7s; off rate 1.30/s.

### C  Replay vs. models (service times from tokens; tau = one mean service time)

| rho | c | real trace: E[wait] / P(wait>tau) | fitted MMPP | Poisson |
|---|---|---|---|---|
| 0.60 | 8 | 31.70 / 0.881 | 40.29 / 0.654 | 0.07 / 0.004 |
| 0.68 | 7 | 44.35 / 0.929 | 76.71 / 0.759 | 0.21 / 0.026 |
| 0.80 | 6 | 116.74 / 0.980 | 122.10 / 0.813 | 0.76 / 0.139 |
| 0.80 | 6 | 116.74 / 0.980 | 132.67 / 0.825 | 0.78 / 0.144 |

(real trace = one 1-hour path; models = mean of 3 long paths of the same rate)

### D  Service-time sensitivity (fitted MMPP vs Poisson; tau = one mean service time)

At c=6 servers (rho=0.8). Servers needed for P(wait>tau)<=5%.

| service | Poisson: E[wait] / P>tau | MMPP: E[wait] / P>tau | delay ratio | c Poisson | c MMPP | extra |
|---|---|---|---|---|---|---|
| exp | 0.78 / 0.152 | 133.78 / 0.798 | 171.1x | 7 | 46 | 557% |
| logn4 | 1.60 / 0.254 | 109.90 / 0.812 | 68.5x | 8 | 42 | 425% |
| logn16 | 4.49 / 0.343 | 115.86 / 0.803 | 25.8x | 8 | 38 | 375% |
| trace | 0.79 / 0.145 | 107.21 / 0.801 | 135.5x | 7 | 45 | 543% |

## Caveat on the conversation-trace fit (trace_fit_sensitivity.py)

Matching IDC(w) with a 2-state MMPP does **not** reproduce the real queueing delay on the conversation trace.
The real 60-s arrival rate stays within 3.2-8.5/s (median 5.5), and the replayed trace is mild (c=45: E[wait] 0.52s,
P(wait>tau)=0.7%). Fitted 2-state MMPPs, simulated on 1-hour paths, overshoot:

| fit | c=51 E[wait] mean / median | c=45 E[wait] mean / median | c=45 P(wait>tau) |
|---|---|---|---|
| real trace (one path) | 0.08 | 0.52 | 0.007 |
| MMPP, 5% bursts of 11.3/s, 184s | 25.8 / 0.44 | 38.4 / 2.93 | 0.235 |
| MMPP, symmetric 50% (6.8 / 4.2 per s, 366s) | 0.38 / 0.38 | 16.8 / 10.3 | 0.480 |

IDC rising almost linearly up to 300 s signals slow rate drift, not a two-level regime; second-order statistics do
not pin down the tail of the rate distribution that drives queueing. The Section D / code-trace numbers are therefore
upper bounds for the conversation trace. The code trace (inter-arrival CV^2 = 173, true spikes) is the case where
the fit and the replay agree in direction (real waits are even larger than the fit).
