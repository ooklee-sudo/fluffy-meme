#!/bin/bash
# Public inputs. Nothing is redistributed in this package.
# SQuAD 2.0 dev set (CC BY-SA 4.0): needed by run_heldout.py (path can be changed with the SQUAD_DEV variable)
curl -L -o /tmp/dev-v2.0.json https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v2.0.json
# Model weights are downloaded automatically from Hugging Face on first use:
#   Qwen/Qwen2.5-0.5B-Instruct, HuggingFaceTB/SmolLM2-360M-Instruct, Qwen/Qwen2.5-1.5B-Instruct,
#   HuggingFaceTB/SmolLM2-1.7B-Instruct, deepset/roberta-base-squad2
# WildChat-1M (ODC-BY) is downloaded shard by shard by wildchat_arrivals.py (about 3 GB in total, deleted after use).
