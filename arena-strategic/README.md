# Strategic User Feedback in Crowdsourced LLM Evaluation — feasibility analysis

Code and result logs for a first pass at the research proposal "Strategic User Feedback in Crowdsourced LLM Evaluation" (Studies 1–3 on public Chatbot Arena / LMArena data).

## Data (downloaded from Hugging Face, not committed)

| Release | Period | Timestamps | User/session id | Identity leaks kept? |
| --- | --- | --- | --- | --- |
| `lmarena-ai/arena-human-preference-55k` | 2023–24 | no | no | almost none (0.1%) |
| `lmarena-ai/arena-human-preference-100k` | Jun–Aug 2024 | yes | hashed user (`judge_hash`) | almost none (0.03%), so it looks scrubbed |
| `lmarena-ai/arena-human-preference-140k` | Apr–Jul 2025 | yes | session id only | yes (~1%) |
| `lmsys/chatbot_arena_conversations` (33k) | 2023 | yes | yes | gated (needs HF login), not used |

Only the 140k release can support Study 1.

## Pipeline

```bash
python src/load.py                 # cache the releases as pickles in /home/user/data
python src/prevalence.py           # leak prevalence per release      -> results/leak_prevalence.txt
python src/build_study1.py         # conversation x model panel, regex leaks, prompt clusters, rule controls
python src/screen.py               # stage-2 LLM screen of regex hits (Claude Haiku 5.5)
python src/study1.py scr           # Study 1 on full panel            -> results/study1_full_panel.txt
python src/judge.py                # matched sample + LLM judges (DeepSeek V3.2, Qwen3-235B; Haiku subsample)
python src/study1_judged.py        # Study 1 with judge controls      -> results/study1_judged.txt
python src/study23.py              # Study 2 event study, Study 3 BT  -> results/study2_3.txt
```

The LLM calls go through OpenRouter (`src/orc.py`, cached). Total spend for this pass was about $1.80.

## Main results

- **Leaks:** the 140k release has 606 usable conversations where exactly one model discloses its own identity and the user did not ask. Grok models account for 56% of them and Claude models for 28%. Many of these are replies to greetings.
- **Study 1 (H1):** a leak does not raise the revealed model's win probability. With judge controls, β = −0.6 pp (SE 2.8). The revealed model loses more (+5 pp, p≈0.09) and ties less (−4 pp). H1a (top-3 developers) has the opposite sign. The "small quality gap" prediction is not supported, because the estimates are flat across terciles.
- **Study 2 (H2):** in a new model's debut week, exact repeat prompts rise by 2 pp and its decisive win share by about 1 pp. Arena boosts sampling of new models, and the 140k release triples in size from 22 May 2025, so volume cannot be read as strategic.
- **Study 3 (H3):** dropping leaked votes leaves the board almost unchanged (τ@20 = 0.98, 2 reversals in the top 20). Bootstrap resampling alone gives a median of 14 reversals.
- **Study 4:** d = 0.3 with 100 per arm has 56% power, not 80%. You need about 175 per arm.
- **PRISM:** the survey has no item on whether people believe their feedback will be used.

## Caveats

- The leak screen used one LLM, and I spot-checked 24 of its labels by hand. The proposal's 500-conversation hand-coded gold standard is still to do.
- Prompt clusters are TF-IDF/k-means, a stand-in for embedding clusters.
- Debut dates are taken from the data. A hand-built calendar of leaderboard updates is still needed.
- Repeat voting can only be measured within a session.
