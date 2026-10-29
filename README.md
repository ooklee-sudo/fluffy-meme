# Experiments for "A Real Options Model of LLM Adapter Maintenance"

Code for the three experiments in the paper.

| Script | Paper section | Runs on | What it does |
| --- | --- | --- | --- |
| `real_options.py` | 4, 6 | CPU, seconds | Propositions 1–4: β, retraining thresholds v*, policy costs W_j(v), ACT-optimal region, Γ; tables 6.2 and 6.3; Monte Carlo check of Prop. 1 |
| `act_toy.py` | 5.2, Appendix B | CPU (numpy), ~minutes | Toy MLP upgrade simulation: recovery of copy vs. ACT (sequential, independent, full-output), calibration size, α sweep, drift–α correlation |
| `act_llama.py`, `run_pairs.py` | 7.1, Appendix A | GPU or CPU | Real model pair (e.g. Llama 3.2 1B Base → Instruct): train, retrain, copy, ACT; recovery R_C, R_A and cost ratio C_A/C_N |
| `nhpp_retrain.py` | (new) | CPU, ~20 s | Retraining timing from production error logs: NHPP (Poisson GLM) fit, optimal retrain age T*, simulation vs. fixed-interval and threshold policies |

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

## 운영 로그로 재학습 시점 정하기 (`nhpp_retrain.py`)

**모형.** 일별 로그를 씁니다. 재학습 후 t일째 요청 수가 n, 오류 수가 y이면 y ~ Poisson(n·ρ(t))로 둡니다(비동질 포아송 과정). ρ(t)는 요청당 오류율이고, 두 가지 모양을 적합한 뒤 AIC가 작은 쪽을 씁니다.
- log-linear: log ρ = a + b·t
- power-law(Crow-AMSAA): log ρ = a + b·log t

b > 0이면 모델 성능이 떨어지고 있다는 뜻입니다. 과분산은 quasi-Poisson 방식(φ = Pearson χ²/df)으로 표준오차를 보정합니다.

**결정 규칙.** 재학습 비용이 C_r, 오류 1건 비용이 C_e이면 T일마다 재학습할 때 하루 비용은 g(T) = (C_r + C_e·Λ(T)) / T입니다. 이를 최소화하는 T*는 T·λ(T) − Λ(T) = C_r / C_e의 해입니다. 매일 재학습 이후 데이터로 다시 적합하고, 추세가 유의하고(단측 p < 0.05) 현재 나이가 T* 이상이면 재학습합니다.

**시뮬레이션 결과** (30 seeds × 730일, C_r = 5000, C_e = 1, 과분산 있음, 드리프트 속도 τ가 사이클마다 바뀜)

| 정책 | 하루 비용 | 오라클 대비 |
| --- | --- | --- |
| NHPP (제안) | 351.4 ± 1.8 | 0.0% |
| 오라클 (τ를 앎, 전역 최적) | 351.5 ± 2.0 | — |
| 사이클별 T* (τ를 앎) | 357.0 ± 2.7 | +1.6% |
| 임계값 1.5배 | 358.2 ± 2.0 | +1.9% |
| 고정 60일 | 377.0 ± 2.9 | +7.2% |
| 고정 30일 | 398.7 ± 0.8 | +13.4% |
| 고정 90일 | 435.8 ± 6.2 | +24.0% |

τ가 사이클마다 바뀌면 사이클별 T*는 전역 최적이 아닙니다. 갱신-보상(renewal-reward) 최적해는 모든 사이클에서 현재 비용률 C_e·n·ρ(t)가 하나의 공통 수준 g*에 도달할 때 재학습하는 것입니다. 오라클은 이 규칙을 씁니다.

```bash
python nhpp_retrain.py                              # 시뮬레이션 + results/nhpp_retrain.{json,png}
python nhpp_retrain.py --csv logs.csv --cr 5000 --ce 1   # 실제 로그: 오늘 재학습할지 출력
```

CSV 열: `requests`, `errors`, 선택적으로 `retrained`(재학습 다음 날 1).

## Notes

- Recovery is `R = (L_none − L_method) / (L_none − L_retrain)`, where L is test MSE (toy) or held-out response NLL (LLM), and `none` is the target model without an adapter.
- `act_llama.py` reports `C_A/C_N` from compute time only. The paper argues C_N should also include data acquisition and revalidation labor. Add those before drawing conclusions.
- In `act_llama.py`, calibration inputs are task prompts without answers (Appendix A.4). α is chosen per module from 13 values in [1e-3, 1e3] on an 80/20 split, using a Gram-only validation error. Decoder layers are corrected sequentially from the input side.
