# Experiments for "A Real Options Model of LLM Adapter Maintenance"

Code for the three experiments in the paper.

| Script | Paper section | Runs on | What it does |
| --- | --- | --- | --- |
| `real_options.py` | 4, 6 | CPU, seconds | Propositions 1–4: β, retraining thresholds v*, policy costs W_j(v), ACT-optimal region, Γ; tables 6.2 and 6.3; Monte Carlo check of Prop. 1 |
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

## 노트북 NVIDIA GPU(8GB)로 1–2B 모델 실험 돌리기

`run_pairs.py --suite gpu8`은 1–2B 모델 16쌍 × 과제 3개(GSM8K, SAMSum, BoolQ) × seed 3개를 돌립니다
(`act_llama.py --preset gpu8`).

| 묶음 | 쌍 | 목적 |
| --- | --- | --- |
| Pythia-1B, 1.4B | step 133k / 103k / 83k / 73k → 143k | 논문의 drift 시리즈(70M–410M)를 규모 축으로 확장 |
| Base → Instruct | Qwen2.5-0.5B, Qwen2.5-1.5B, SmolLM2-1.7B, OLMo-2-1B | SmolLM2-360M 예외가 instruction tuning 전반의 현상인지 확인 |
| OLMo-2-1B stage 1 | step 1.8M / 1.6M / 1.4M / 1.0M → 1.907M | 두 번째 모델 계열의 drift 시리즈 |

8GB에 맞춘 설정: bf16(RTX 20xx는 fp16), 배치 4, 길이 256, gradient checkpointing, `--offload`(두 모델을 CPU에
두고 필요한 모델이나 층만 GPU로 옮김; 옮기는 시간은 C_A에서 뺌), `--gram-acc mixed`(Gram 행렬 곱은 float32, 합과
ridge solve는 float64; 소비자 GPU는 float64가 느리기 때문), ACT는 cached 구현(`--act-impl fast`).

**1. 설치** (Windows 기준; Python 3.10 이상, NVIDIA 드라이버 설치 상태)

```bash
git clone -b claude/lucid-fermi-145tu8 https://github.com/ooklee-sudo/fluffy-meme.git
cd fluffy-meme
python -m venv .venv
.venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

마지막 줄이 `True`와 GPU 이름을 출력해야 합니다.

**2. 한 쌍으로 시간과 메모리 확인** (가장 먼저)

```bash
python run_pairs.py --suite gpu8 --only "pythia-1b +70k" --tasks gsm8k --seeds 0
```

끝에 나오는 소요 시간과 결과 JSON의 `peak_gpu_mem_gb`를 확인하세요. 메모리가 부족하면 `-- --bs 2`를 붙입니다.

**3. 정밀도 확인** (mixed와 float64 Gram 행렬이 같은 α와 결과를 주는지)

```bash
python run_pairs.py --suite gpu8 --check-precision
```

**4. 전체 실행** (중간에 끊겨도 다시 실행하면 끝난 run은 건너뜀)

```bash
python run_pairs.py --suite gpu8 --tasks gsm8k --seeds 0 --purge
python run_pairs.py --suite gpu8 --purge
```

첫 줄은 16쌍을 GSM8K, seed 0으로 한 번씩 돌리는 1차 패스이고, 둘째 줄이 나머지 과제와 seed를 채웁니다.
`--purge`는 각 source checkpoint를 다 쓴 뒤 Hugging Face 캐시에서 지웁니다. 지우지 않으면 모델을 받는 데만
디스크가 약 60GB 필요합니다. 결과는 `results/gpu8/<task>/*.json`, 요약은 `results/gpu8_table.md`(논문 표 형식:
drift, R_C, R_A, seed 간 표준편차, C_A/C_N, Γ, ACT 최적 구간)와 `results/gpu8_summary.json`에 저장됩니다.
표만 다시 만들려면 `python run_pairs.py --suite gpu8 --summary-only`를 실행합니다.

노트북은 전원을 연결하고, 장시간 실행하면 발열로 느려질 수 있으니 통풍이 되는 곳에 두세요.

**재현성 수정**: LoRA 초기화가 seed 없이 이루어져(torch 기본 seed는 프로세스마다 무작위) 같은 설정으로 돌려도
결과가 달라지던 문제를 고쳤습니다(`--seed`로 초기화를 고정). 이 수정 전의 결과(`results/pairs*`, 논문 수치)는
같은 명령으로 돌려도 정확히 재현되지 않습니다.

## Notes

- Recovery is `R = (L_none − L_method) / (L_none − L_retrain)`, where L is test MSE (toy) or held-out response NLL (LLM), and `none` is the target model without an adapter.
- `act_llama.py` reports `C_A/C_N` from compute time only. The paper argues C_N should also include data acquisition and revalidation labor. Add those before drawing conclusions.
- In `act_llama.py`, calibration inputs are task prompts without answers (Appendix A.4). α is chosen per module from 13 values in [1e-3, 1e3] on an 80/20 split, using a Gram-only validation error. Decoder layers are corrected sequentially from the input side.
