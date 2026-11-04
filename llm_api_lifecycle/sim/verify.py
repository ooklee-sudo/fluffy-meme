import sys; sys.path.insert(0,'.')
import numpy as np
from sim import simulate, summarize, theta_of, RATE
from data import *
from samplers import km_sample_pool
L=lifetimes(SETS['Gemini API (stable)']); pool=km_sample_pool(L)
o=simulate(pool,[365]*10,[1],N=20000,price_shock=False,surcharge=0,outage_usd=0,sigma=1e-9,strategies=('rigid','flex'))
r=summarize(o,B=200)
lam=o['rigid']['mig'].sum()/o['rigid']['nmig'].size  # discounted labor
# analytic: (1-phi)*E[K]*Lambda where Lambda = E[sum disc] ; mig labor rigid = E[K]*RATE*Lambda
Lam=lam/(16/3*RATE)
print('Lambda',round(Lam,3),'analytic BE',round(0.5*16/3*Lam,2),'sim BE',round(r['flex']['breakeven_pw'],2),'migrations',r['migrations'])
print('theta', [round(theta_of(s,0.1/12),2) for s in (0.05,0.10,0.20,0.36)])
