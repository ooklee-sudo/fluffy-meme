"""Evaluation pipeline: compare each synthetic condition against a real count sample."""
import numpy as np

import count_metrics as cm


def evaluate_condition(real_y, real_treat, synth_y, synth_treat):
    s_real, s_syn = cm.summary(real_y), cm.summary(synth_y)
    alpha, t, p = cm.cameron_trivedi(synth_y)
    row = {f"syn_{k}": v for k, v in s_syn.items()}
    row.update({f"real_{k}": v for k, v in s_real.items()})
    row.update(cm.distances(real_y, synth_y))
    row.update({"ct_alpha": alpha, "ct_p": p, "best_model": cm.fit_count_models(synth_y)["best"]})
    i_real, i_syn = cm.irr(real_y, real_treat), cm.irr(synth_y, synth_treat)
    row.update({"irr_real": i_real[0], "irr_syn": i_syn[0], "irr_syn_lo": i_syn[1], "irr_syn_hi": i_syn[2],
                "irr_ratio": i_syn[0] / i_real[0]})
    return row
