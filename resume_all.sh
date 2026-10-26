#!/bin/bash
# Relaunch every resumable background job (the cloud container restarts now and then).
R=/home/user/fluffy-meme/nmi_screening/replication; cd $R
pgrep -f "^python3 s2_generate.py --gen deepseek --n 100" >/dev/null || nohup python3 s2_generate.py --gen deepseek --n 100 --workers 12 --human human_econ.jsonl --tag econ_ --cap-usd 125 >> s2_econ_deepseek.log 2>&1 &
pgrep -f "^python3 s12_bestofk" >/dev/null || nohup python3 s12_bestofk.py --k 4 --workers 40 --cap-usd 125 >> s12.log 2>&1 &
pgrep -f "^python3 s13_ext_build.py ds_attacks" >/dev/null || nohup python3 s13_ext_build.py ds_attacks --workers 10 >> s13_ds.log 2>&1 &
cd /home/user/fluffy-meme/reach_pilot/bugsinpy
for s in 0 1 2; do pgrep -f "^python3 bip_study.py run.*--shard $s/3" >/dev/null || nohup python3 bip_study.py run --models anthropic/claude-haiku-5.5,anthropic/claude-sonnet-5.5,deepseek/deepseek-v4.1-flash --k 6 --cap-usd 60 --shard $s/3 >> bip_s$s.log 2>&1 & done
