"""Pre-registered check: the estimator must recover Se, Sp and the DiD within 2 SE in >= 90% of replications."""
import numpy as np, sys
sys.path.insert(0, '.')
from latent import fit, did
rng = np.random.default_rng(1)
n_cell = 4300; ptrue = np.array([.12, .15, .10, .17]); Se = np.array([.80, .70, .60]); Sp = np.array([.95, .90, .97])
ok = []; est = []
for r in range(200):
    cell = np.repeat(np.arange(4), n_cell); y = rng.random(cell.size) < ptrue[cell]
    X = np.where(y[:, None], rng.random((cell.size, 3)) < Se, rng.random((cell.size, 3)) < 1 - Sp).astype(float)
    f = fit(X, cell); est.append((did(f['p']), *f['Se'][0], *f['Sp'][0]))
est = np.array(est); truth = np.array([did(ptrue), *Se, *Sp]); sd = est.std(0)
cover = (np.abs(est - truth) <= 2 * sd).mean(0)
print('truth', truth.round(3)); print('mean ', est.mean(0).round(3)); print('sd   ', sd.round(3)); print('share within 2 SD', cover.round(2))
naive = [(Se[0] + Sp[0] - 1) * did(ptrue)]; print('true DiD', round(did(ptrue), 3), 'naive DiD on classifier 1 would be', round(naive[0], 3))
