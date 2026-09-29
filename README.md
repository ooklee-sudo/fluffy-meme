# Experiments for "A Real Options Model of LLM Adapter Maintenance"

Code for the three experiments in the paper.

| Script | Paper section | Runs on | What it does |
| --- | --- | --- | --- |
| `real_options.py` | 4, 6 | CPU, seconds | Propositions 1–4: β, retraining thresholds v*, policy costs W_j(v), ACT-optimal region, Γ; tables 6.2 and 6.3; Monte Carlo check of Prop. 1 |
| `behavioral_options.py` | extension | CPU, seconds | Behavioral-economics extension of the real options model: present bias, loss aversion, status quo, overconfidence, planning fallacy, ambiguity aversion. Reports threshold distortion v*_biased / v* and the regret of the biased policy choice vs. the optimum |
| `act_toy.py` | 5.2, Appendix B | CPU (numpy), ~minutes | Toy MLP upgrade simulation: recovery of copy vs. ACT (sequential, independent, full-output), calibration size, α sweep, drift–α correlation |
| `act_llama.py`, `run_pairs.py` | 7.1, Appendix A | GPU or CPU | Real model pair (e.g. Llama 3.2 1B Base → Instruct): train, retrain, copy, ACT; recovery R_C, R_A and cost ratio C_A/C_N |

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
# Section 6: numerical analysis with the paper's illustrative parameters
python real_options.py --mc

# Appendix B: toy simulation (6 drift levels x 5 seeds)
python act_toy.py
python real_options.py --recovery results/act_toy.json      # feed toy R into the model

# Behavioral extension: regret of biased decision makers (illustrative bias strengths, not estimates)
python behavioral_options.py
python behavioral_options.py --pb 0.8 --lam 2.25 --recovery results/act_toy.json

# Section 7.1: model-pair experiment (needs a GPU and Hugging Face access)
python act_llama.py --source meta-llama/Llama-3.2-1B --target meta-llama/Llama-3.2-1B-Instruct --gen-eval 200
python real_options.py --recovery results/act_llama.json    # uses measured R_C, R_A, C_A/C_N

# CPU smoke test of the act_llama.py pipeline with random tiny Llama models (no downloads)
python act_llama.py --tiny
```

Outputs are written to `results/`.

## 내 PC에서 실제 모델 실험 돌리기 (GPU 없이)

`run_pairs.py`는 승인이 필요 없는 공개 모델 5쌍으로 7.1절 실험을 CPU에서 돌립니다. 끝나면 측정한 (R_C, R_A, C_A/C_N)을 경제 모형에 넣어 줍니다.

| 쌍 | 업그레이드 종류 |
| --- | --- |
| Pythia-160M step 133k / 113k / 73k → step 143k | 같은 모델의 추가 학습 (드리프트가 커지는 순서) |
| SmolLM2-360M → SmolLM2-360M-Instruct | Base → Instruct |
| Qwen2.5-0.5B → Qwen2.5-0.5B-Instruct | Base → Instruct |

**1. 설치** (Python 3.10 이상, 메모리 8GB 이상 권장, 디스크 약 10GB)

```bash
git clone -b claude/run-code-gwkt8k https://github.com/ooklee-sudo/fluffy-meme.git
cd fluffy-meme
python -m venv .venv
# Windows: .venv\Scripts\activate    Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

**2. 먼저 작은 쌍 하나로 확인** (수십 분 내외)

```bash
python run_pairs.py --only "+10k"
```

**3. 전체 실행** (CPU 성능에 따라 몇 시간; 중간에 끊겨도 다시 실행하면 끝난 쌍은 건너뜁니다)

```bash
python run_pairs.py
```

결과는 `results/pairs/*.json`(쌍별), `results/pairs_summary.json`(요약), `results/real_options_pairs.json`과 `results/policy_costs_pairs.png`(경제 모형)에 저장됩니다.

**옵션**

- 더 빨리: `python run_pairs.py -- --steps 150 --n-eval 100`
- CPU 스레드 지정: `python run_pairs.py -- --threads 8`
- Apple Silicon Mac에서 GPU(MPS) 사용: `python run_pairs.py --preset gpu -- --n-train 500 --steps 300 --bs 4 --max-len 256`
- 쌍 하나를 직접: `python act_llama.py --preset cpu --source EleutherAI/pythia-160m --source-revision step113000 --target EleutherAI/pythia-160m --target-revision step143000`

모델과 GSM8K 데이터는 처음 실행할 때 Hugging Face에서 자동으로 내려받습니다.

## Notes

- Recovery is `R = (L_none − L_method) / (L_none − L_retrain)`, where L is test MSE (toy) or held-out response NLL (LLM), and `none` is the target model without an adapter.
- `act_llama.py` reports `C_A/C_N` from compute time only. The paper argues C_N should also include data acquisition and revalidation labor. Add those before drawing conclusions.
- In `act_llama.py`, calibration inputs are task prompts without answers (Appendix A.4). α is chosen per module from 13 values in [1e-3, 1e3] on an 80/20 split, using a Gram-only validation error. Decoder layers are corrected sequentially from the input side.
