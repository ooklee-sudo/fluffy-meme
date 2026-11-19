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

## Notes

- Recovery is `R = (L_none − L_method) / (L_none − L_retrain)`, where L is test MSE (toy) or held-out response NLL (LLM), and `none` is the target model without an adapter.
- `act_llama.py` reports `C_A/C_N` from compute time only. The paper argues C_N should also include data acquisition and revalidation labor. Add those before drawing conclusions.
- In `act_llama.py`, calibration inputs are task prompts without answers (Appendix A.4). α is chosen per module from 13 values in [1e-3, 1e3] on an 80/20 split, using a Gram-only validation error. Decoder layers are corrected sequentially from the input side.

## QEC 디코더 트랜스포머 (양자 오류정정, 별도 실험)

`qec_decoder.py`: Stim으로 surface code(회로 수준 노이즈) 신드롬을 즉석 생성하고, 트랜스포머 디코더를 학습해 MWPM(PyMatching)과 논리 오류율을 비교합니다. 데이터 다운로드가 필요 없습니다. 위치 인코딩이 좌표 기반이라 작은 거리로 학습한 모델을 큰 거리에서 평가할 수 있습니다(`--eval-d`).

```bash
python qec_decoder.py --smoke                                   # CPU 스모크 테스트 (~10초)
python qec_decoder.py --d 5 --p 0.005 --steps 20000 --device cuda
python qec_decoder.py --d 3 --eval-d 3 5 7 --eval-p 0.003 0.008 --steps 20000 --device cuda   # 거리/노이즈 일반화
```

**하이브리드 모드** (`--hybrid`): MWPM의 예측·가중치를 입력으로 주고 신경망은 "MWPM이 틀리는가"만 학습합니다. 최종 예측은 MWPM XOR 보정이라 MWPM 수준에서 시작합니다. `--large`는 dim 256, 6층, bs 512, 6만 스텝 프리셋입니다(학습 중 20%마다 간이 평가를 출력).

```bash
python qec_decoder.py --d 5 --p 0.005 --hybrid --large --device cuda
python qec_decoder.py --d 5 --p 0.005 --large --device cuda      # 비하이브리드 대조군
```

8GB GPU 기준 d=3~7, dim 128~256, 4~6층까지 여유 있습니다. 결과는 `results/qec_decoder.json`에 저장됩니다.

### 노이즈 불일치 실험 (신경망이 유리할 수 있는 설정)

MWPM/belief-matching은 노이즈 모델(DEM)을 미리 알아야 합니다. 실제 장비에서는 노이즈가 틀어지므로, 데이터는 실제 노이즈로 만들고 매칭 그래프는 틀린 노이즈로 만들어 비교합니다.

| 옵션 | 의미 |
| --- | --- |
| `--p` | 실제 물리 오류율 |
| `--meas-mult`, `--data-mult` | 실제 측정/리셋 오류 = p×meas_mult, 데이터 큐빗 오류 = p×data_mult |
| `--assume-p` | 매칭 그래프가 가정하는 균일 노이즈 (기본: `--p`) |
| `--eval-p` | 실제 p만 바꿔 평가 (drift), 가정은 고정 |
| `--bm` | belief-matching 기준선 포함 (`*` 표시는 실제 노이즈를 아는 oracle) |
| `--init` / `--load` / `--ckpt` | 가중치에서 이어 학습(fine-tune) / 평가만 / 저장 |

출력의 `MWPM*`, `BM*`는 실제 노이즈를 아는 기준선이고, `fixed`/`broken`은 하이브리드가 MWPM을 뒤집어 고친/망친 샷 수입니다.

```bash
# d=5, 측정 오류가 5배 큰 노이즈. 매칭 그래프는 균일 p=0.005로 가정. 작은 모델 (~20분 내외)
python qec_decoder.py --d 5 --p 0.005 --meas-mult 5 --hybrid --steps 20000 --bs 256 --bm --ckpt results/h_meas5.pt --device cuda
# 같은 설정, 큰 모델
python qec_decoder.py --d 5 --p 0.005 --meas-mult 5 --hybrid --large --steps 40000 --bm --ckpt results/h_meas5_large.pt --device cuda
# drift: 가정 p=0.005 고정, 실제 p 변화
python qec_decoder.py --d 5 --p 0.005 --hybrid --eval-p 0.003 0.008 0.012 --bm --device cuda
```

참고(d=5, p=0.005, 20000샷, 일치 노이즈): MWPM 0.0136, belief-matching 0.0100.

### 보정(calibrated) 기준선: 신경망 없이 불일치 손해 회복

`--baselines-only`는 신경망 없이 MWPM/BM을 세 가지 그래프로 비교합니다: 가정된 노이즈(`MWPM`, `BM`), 신드롬 통계로 가중치를 다시 추정한 그래프(`MWPMc`, `BMc`; 라벨 없는 `--calib-shots`개 샷 사용), 실제 노이즈를 아는 oracle(`MWPM*`, `BM*`). 추정식은 검출기 쌍 상관 p_ij = 1/2 − 1/2·sqrt(1 − 4cov_ij/(1 − 2⟨x_i⟩ − 2⟨x_j⟩ + 4⟨x_i x_j⟩)) 입니다(Spitz 등의 방법 계열; 구현은 근사).

```bash
python qec_decoder.py --baselines-only --d 5 --p 0.005 --meas-mult 5 --eval-n 20000 --bm
```

결과 (d=5, p=0.005, 매칭 그래프는 균일 p=0.005 가정, 보정 샷 200000):

| 실제 노이즈 | MWPM | MWPMc | MWPM* | BM | BMc | BM* |
| --- | --- | --- | --- | --- | --- | --- |
| 측정 오류 ×5 (20000샷) | 0.0644 | 0.0525 | 0.0537 | 0.0583 | 0.0461 | 0.0460 |
| 가정 p=0.015 (40000샷, MWPM만) | 0.0153 | 0.0130 | 0.0134 | | | |
| 데이터 오류 ×5 | 0.0697 | 0.0642 | 0.0648 | | | |
| 측정 ×3, 데이터 ×0.3 | 0.0244 | 0.0212 | 0.0217 | | | |

보정은 oracle 수준(통계 오차 범위 이내)까지 회복합니다. 보정 샷 수 의존성(측정 ×5, 40000샷 평가): 1000샷은 오히려 악화(0.0697), 5000샷 0.0575, 20000샷 이상 oracle 수준. p만 균일하게 바뀌는 drift에서는 MWPM의 가정 불일치 손해가 거의 없습니다.
