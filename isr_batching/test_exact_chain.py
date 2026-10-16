import numpy as np, time
from exact_chain import Chain
G0=np.array([[-1.,1.],[1.,-1.]])
# 1) dedicated servers: T(n,0,k) = 1 + (n-M+1)+/M for every theta, k  (paper, below eq. 7)
for th in (0.05,1,20):
    ch=Chain(4,0.0,24,G0,th,20,[1.2,5.0]); ch.lam_cur=np.array([1.0,3.0]); T0=ch.tagged_T0(ch.lam_cur)
    n=np.arange(24); ex=1+np.maximum(n-4+1,0)/4
    assert np.allclose(T0,ex[:,None],atol=1e-9), th
print('ok: dedicated closed form')
# 2) Little's law: sum_k pi_k (1-mu(N|k)) lam_k d_k = E[N]  (batched, beta/alpha = 0.3)
for th in (0.05,1,20):
    ch=Chain(4,0.3,24,G0,th,20,[1.2,5.0]); lam=np.array([0.9,2.0]); d,pi=ch.delays(lam)
    pik=pi.sum(0); adm=lam*(pik-pi[24]); EN=(pi.sum(1)*np.arange(25)).sum()
    print(f'theta={th}: sum lam~ d = {(adm*d).sum():.8f}   E[N] = {EN:.8f}')
    assert abs((adm*d).sum()-EN)<1e-8
print('ok: Little law')
