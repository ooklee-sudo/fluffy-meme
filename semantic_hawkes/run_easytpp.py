"""Run NHP / THP (EasyTPP) and FreeHawkesTPP / SemHawkesTPP (this repo) through the same EasyTPP pipeline.

    python -m semantic_hawkes.run_easytpp --data semantic_hawkes/real_data/tppllm/stack-overflow --model NHP
    python -m semantic_hawkes.run_easytpp --data ... --model SemHawkesTPP --emb emb/stack-overflow_qwen.npy

Prints one RESULT json line: test log-likelihood/event, type accuracy and time RMSE at the epoch with the best
validation log-likelihood. Event times are divided by the mean training inter-event time (rescale_time), so
log-likelihoods are in that rescaled time unit (comparable across models, not across papers).
"""
import argparse
import json
import os
import re
import tempfile

import glob
import random
import shutil

import yaml

HAWKES = dict(lr=1e-2, model_config=dict(hidden_size=8, loss_integral_num_sample_per_step=20))
MODEL_CFG = {
    "FreeHawkesTPP": HAWKES,
    "SemHawkesTPP": HAWKES,
    "NHP": dict(lr=1e-3, model_config=dict(hidden_size=64, loss_integral_num_sample_per_step=20)),
    "THP": dict(lr=1e-3, model_config=dict(hidden_size=32, time_emb_size=16, num_layers=2, num_heads=2,
                                           loss_integral_num_sample_per_step=20)),
}
THINNING = dict(num_seq=10, num_sample=1, num_exp=500, look_ahead_time=10, patience_counter=5,
                over_sample_rate=5, num_samples_boundary=5, dtime_max=5, num_step_gen=1)


def subset_dir(data_dir, n_train, seed, out_dir):
    """Copy of the dataset whose train split keeps n_train random sequences (dev/test untouched)."""
    d = os.path.join(out_dir, "subset")
    os.makedirs(d, exist_ok=True)
    train = json.load(open(os.path.join(data_dir, "train.json")))
    random.Random(seed).shuffle(train)
    json.dump(train[:n_train], open(os.path.join(d, "train.json"), "w"))
    for s in ("dev", "test"):
        shutil.copy(os.path.join(data_dir, f"{s}.json"), os.path.join(d, f"{s}.json"))
    return d


def parse_log(out_dir):
    log = glob.glob(os.path.join(out_dir, "**", "log"), recursive=True)[0]
    text = re.sub(r"\x1b\[[0-9;]*m", "", open(log).read())
    valid = re.findall(r"Epoch (\d+) \(valid\) \]:\s+valid loglike is (\S+),", text)
    test = re.findall(r"Epoch (\d+) \(test\) \]: test loglike is (\S+), num_events is (\d+), acc is (\S+), rmse is (\S+)", text)
    best = max(valid, key=lambda x: float(x[1]))[0]
    for ep, ll, n, acc, rmse in test:
        if ep == best:
            return dict(best_epoch=int(ep), valid_ll=float(dict(valid)[ep]), test_ll=float(ll), n_events=int(n),
                        acc=float(acc), rmse=float(rmse))
    raise RuntimeError("could not parse EasyTPP log")


def build_config(data_dir, model, epochs, batch_size, seed, out_dir, max_len=None):
    first = json.load(open(os.path.join(data_dir, "train.json")))[0]
    K = first["dim_process"]
    specs = dict(num_event_types=K, pad_token_id=K, padding_side="right", truncation_side="right",
                 rescale_time=True)
    if max_len:
        specs.update(padding_strategy="max_length", truncation_strategy="longest_first", max_len=max_len)
    cfg = {
        "pipeline_config_id": "runner_config",
        "data": {"d": dict(data_format="json", data_specs=specs,
                           train_dir=os.path.join(data_dir, "train.json"),
                           valid_dir=os.path.join(data_dir, "dev.json"),
                           test_dir=os.path.join(data_dir, "test.json"))},
        "exp": {
            "base_config": dict(stage="train", backend="torch", dataset_id="d", runner_id="std_tpp",
                                model_id=model, base_dir=out_dir),
            "trainer_config": dict(batch_size=batch_size, max_epoch=epochs, shuffle=True, optimizer="adam",
                                   learning_rate=MODEL_CFG[model]["lr"], valid_freq=1, use_tfb=False,
                                   metrics=["acc", "rmse"], seed=seed, gpu=-1),
            "model_config": dict(MODEL_CFG[model]["model_config"], thinning=THINNING),
        },
    }
    return cfg


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--model", choices=list(MODEL_CFG), required=True)
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--seed", type=int, default=2019)
    p.add_argument("--max_len", type=int, default=None)
    p.add_argument("--n_train", type=int, default=None, help="keep only n random training sequences")
    p.add_argument("--emb", default=None, help=".npy (K, D) type-text embeddings for SemHawkesTPP")
    p.add_argument("--tag", default="")
    a = p.parse_args()
    if a.emb:
        os.environ["SEMHAWKES_EMB"] = os.path.abspath(a.emb)
    from . import easytpp_hawkes  # noqa: F401  (registers the Hawkes models with EasyTPP)

    from easy_tpp.config_factory import Config
    from easy_tpp.runner import Runner

    out = tempfile.mkdtemp(prefix="easytpp_")
    data_dir = subset_dir(a.data, a.n_train, a.seed, out) if a.n_train else a.data
    cfg = build_config(data_dir, a.model, a.epochs, a.batch_size, a.seed, out, a.max_len)
    path = os.path.join(out, "cfg.yaml")
    yaml.safe_dump(cfg, open(path, "w"))
    config = Config.build_from_yaml_file(path, experiment_id="exp")
    runner = Runner.build_from_config(config)
    runner.run()
    res = parse_log(out)
    res.update(data=os.path.basename(a.data.rstrip("/")), model=a.model, n_train=a.n_train, seed=a.seed, tag=a.tag)
    print("RESULT", json.dumps(res))


if __name__ == "__main__":
    main()
