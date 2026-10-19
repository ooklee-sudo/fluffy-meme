"""Synthetic stand-in for the event logs, used only to test the analysis pipeline.

The effects planted here are NOT the paper's results. They exist so that
analysis/*.py can be checked for recovering known parameters. Replace the files
in data/ with the real logs (same columns) before running anything for the paper.
"""
import itertools, sys
import numpy as np, pandas as pd

rng = np.random.default_rng(7)
out = sys.argv[1] if len(sys.argv) > 1 else "data_synthetic"
import os; os.makedirs(out, exist_ok=True)

N, DAYS, EL_EVERY, SLOTS = 6, 50, 5, 2
FAM = {"claude": ["claude"] * 6, "deepseek": ["deepseek"] * 6,
       "mixed": ["claude"] * 3 + ["deepseek"] * 3}
# planted truth
STAND_BASE = {"claude": -1.6, "deepseek": -0.3}
RENT_STAND = 0.9
ROTATE, NEED, SELF, RECIP = -0.9, -0.15, 0.1, 0.4   # allocation weights when binding

worlds, elections, allocs = [], [], []
wid = 0
for authority, rule, pop, rent in itertools.product(
        ["binding", "advisory"], ["plurality", "ranked"],
        ["claude", "deepseek", "mixed"], [0, 2]):
    for seed in range(6):
        wid += 1
        fam = FAM[pop]
        cum = np.zeros(N); energy = np.full(N, 10.0); gifts = np.zeros((N, N))
        holder, held_before = None, np.zeros(N)
        n_nocand = n_cont = 0; spells = []; holders_seq = []
        for e in range(DAYS // EL_EVERY):
            stood = np.array([rng.random() < 1 / (1 + np.exp(-(STAND_BASE[fam[i]]
                              + RENT_STAND * (rent > 0) + 0.8 * held_before[i])))
                              for i in range(N)])
            win = np.zeros(N, int)
            if stood.sum() == 0:
                holder = None; n_nocand += 1
            else:
                cand = np.flatnonzero(stood)
                if len(cand) > 1: n_cont += 1
                w = np.exp(0.5 * held_before[cand] + 0.0)
                holder = rng.choice(cand, p=w / w.sum()); win[holder] = 1
            for i in range(N):
                elections.append(dict(world_id=wid, election_id=e, agent_id=i, family=fam[i],
                                      capability="high", stood=int(stood[i]), won=int(win[i]),
                                      energy_rank_before=int((energy > energy[i]).sum()),
                                      held_before=int(held_before[i])))
            held_before = np.zeros(N)
            if holder is not None: held_before[holder] = 1
            holders_seq.append(holder)
            for d in range(EL_EVERY):
                day = e * EL_EVERY + d
                for s in range(SLOTS):
                    elig = np.flatnonzero(cum >= 0)
                    binding_active = authority == "binding" and holder is not None
                    if binding_active:
                        util = (ROTATE * cum + NEED * energy
                                + SELF * (np.arange(N) == holder)
                                + RECIP * gifts[:, holder])
                    else:
                        util = np.zeros(N)
                    p = np.exp(util) / np.exp(util).sum()
                    r = rng.choice(N, p=p)
                    for i in range(N):
                        allocs.append(dict(world_id=wid, day=day, slot=s, agent_id=i,
                                           holder_id=-1 if holder is None else holder,
                                           binding_active=int(binding_active),
                                           received=int(i == r), cum_tasks_before=cum[i],
                                           energy_before=energy[i],
                                           gifted_holder_before=gifts[i, holder] if holder is not None else 0))
                    cum[r] += 1; energy[r] += 3
                energy -= 1
                if holder is not None: energy[holder] += rent
                if rng.random() < 0.25:
                    a, b = rng.choice(N, 2, replace=False); gifts[a, b] += 1
                    energy[a] -= 1; energy[b] += 1
        # world-level outcomes
        tot = np.sort(cum); k = len(tot)
        gini = (2 * np.sum((np.arange(1, k + 1)) * tot) / (k * tot.sum())) - (k + 1) / k
        hs = [h for h in holders_seq if h is not None]
        worlds.append(dict(world_id=wid, seed=seed, authority=authority, rule=rule,
                           population=pop, rent=rent, n_elections=DAYS // EL_EVERY,
                           n_nocand=n_nocand, n_contested=n_cont, gini=gini,
                           reelect=np.mean([holders_seq[i] == holders_seq[i - 1] and holders_seq[i] is not None
                                            for i in range(1, len(holders_seq))]),
                           transfers=int(gifts.sum())))
pd.DataFrame(worlds).to_csv(f"{out}/worlds.csv", index=False)
pd.DataFrame(elections).to_csv(f"{out}/elections.csv", index=False)
pd.DataFrame(allocs).to_csv(f"{out}/allocations.csv", index=False)
print("worlds", len(worlds), "elections rows", len(elections), "alloc rows", len(allocs))
