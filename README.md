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

### 상관 오류 실험 (그래프 모형 밖의 노이즈)

`--corr-p q`는 매 라운드 데이터 큐빗 depolarization 직후, 같은 행/열에서 거리 4인(인접하지 않은) 데이터 큐빗 쌍마다 독립적인 상관 오류(`--corr-type X|Y|Z`, 기본 X)를 확률 q로 넣습니다(d=5: 쌍 30개). 가정/보정 그래프는 이 오류를 모르고(`MWPM`, `MWPMc`, `BM`, `BMc`), `*` oracle DEM은 포함하지만 hyperedge 분해가 근사라 "진짜 최적"은 아닙니다.

CPU 기준선 (d=5, p=0.005, 20000샷, 보정 샷 200000):

| corr-p | MWPM | MWPMc | MWPM* | BM | BMc | BM* |
| --- | --- | --- | --- | --- | --- | --- |
| 0.002 | 0.0418 | 0.0405 | 0.0399 | 0.0364 | **0.0360** | 0.0425 |
| 0.006 | 0.1009 | 0.0954 | 0.0900 | 0.0948 | **0.0903** | 0.0946 |

신경망이 BMc(그래프 기준선 중 최선)보다 낮아야 의미가 있습니다. 같은 노이즈를 보는 신경망:

```bash
python qec_decoder.py --d 5 --p 0.005 --corr-p 0.002 --steps 20000 --bs 256 --bm --ckpt results/c_plain.pt --device cuda
python qec_decoder.py --d 5 --p 0.005 --corr-p 0.002 --hybrid --steps 20000 --bs 256 --bm --ckpt results/c_hybrid.pt --device cuda
python qec_decoder.py --d 5 --p 0.005 --corr-p 0.002 --large --bm --ckpt results/c_large.pt --device cuda   # 큰 모델, 6만 스텝
```

### hyperedge를 쓰는 강한 기준선 (BMh, BPOSD)

`--hcalib-shots N`: 오류 메커니즘의 **구조**(상관 hyperedge 포함)는 실제 회로의 DEM에서 가져오고(기준선에 유리한 가정), **확률**은 라벨 없는 N샷에서 추정한 `MWPMh`/`BMh`. 검출기 부분집합 A에 대해 E[Π(−1)^x] = Π_{|A∩S_m| 홀수}(1−2p_m)이므로 log E_A가 log(1−2p_m)에 선형이며, 모든 단일/쌍/3개 이상 메커니즘 집합에 대한 가중 최소제곱으로 풉니다(d=5, 50만 샷: 메커니즘 확률 상대오차 중앙값 5%).

`--bposd`: DEM 검사행렬 위의 BP+OSD(`ldpc`, 반복 100, osd_cs 차수 30). MWPM과 달리 hyperedge를 직접 씁니다. `BPOSD`(가정 그래프), `BPOSDh`(보정), `BPOSD*`(oracle). `pip install ldpc beliefmatching` 필요.

```bash
python qec_decoder.py --baselines-only --d 5 --p 0.005 --corr-p 0.002 --hcalib-shots 500000 --eval-n 12000 --bposd
```

d=5, p=0.005, corr-p=0.002 (샘플 수가 다른 두 번의 측정):

| 디코더 | 오류율 | 샷 |
| --- | --- | --- |
| MWPM / MWPMc / MWPM* | 0.0413 / 0.0401 / 0.0399 | 100000 |
| BM / BMc / BM* | 0.0372 / 0.0364 / 0.0415 | 100000 |
| MWPMh | 0.0378 | 12000 |
| BPOSD / BPOSDh / BPOSD* | 0.0350 / 0.0351 / 0.0354 | 12000 |

주의: BP+OSD는 설정에 매우 민감합니다(반복 30, 차수 0: 0.053 / 반복 100, 차수 30: 0.035). d=3에서는 oracle 구조의 BPOSD가 가정 그래프보다 나빴습니다(0.0646 vs 0.0496, 원인 미확인). d=5 설정에서만 점검했습니다.

### `--bm` / `--bposd` 설치 (C 컴파일러가 없는 환경 포함)

`pip install ldpc beliefmatching`이 numpy를 소스에서 빌드하려다 `gcc` 없음으로 실패할 수 있습니다(파이썬 3.14 등). 의존성을 건드리지 않고 설치하면 됩니다.

```bash
pip install --no-deps ldpc beliefmatching sinter
```

### 결과 기록: 큰 모델(비하이브리드) vs 기준선, 같은 5만 샷

`python qec_decoder.py --d 5 --p 0.005 --corr-p 0.002 --large --load results/c_large.pt --bposd --eval-n 50000` (모델: dim 256, 6층, 4.75M, 6만 스텝, bs 512, 학습 노이즈와 평가 노이즈 동일, 시드 1개)

| 디코더 | 논리 오류율 (50000샷) |
| --- | --- |
| **NN** | **0.0282** |
| BPOSD (가정 그래프) | 0.0336 |
| BPOSD* (oracle 구조) | 0.0373 |
| MWPMc / MWPM* / MWPM | 0.0383 / 0.0386 / 0.0398 |

NN은 가장 강한 기준선(BPOSD)보다 약 16%, MWPMc보다 약 26% 낮음(표준오차 약 0.0008). 같은 모델의 거리 일반화는 실패(d=3: 0.1091, d=7: 0.3385; MWPMc는 각각 0.0372, 0.0432).
한계: 단일 시드/노이즈 모형, BPOSD* > BPOSD(구조를 더 알수록 나빠짐)는 BP+OSD가 최적이 아니라는 신호, 최대우도 하한은 미측정.

### 결과 기록: p 스윕 (같은 모델, d=5, corr-p=0.002 고정, 2만 샷, 학습은 p=0.005만)

| p | NN | BPOSD | BPOSD* | MWPMc | MWPM* |
| --- | --- | --- | --- | --- | --- |
| 0.003 | 0.0120 | 0.0181 | 0.0295 | 0.0202 | 0.0193 |
| 0.004 | 0.0208 | 0.0274 | 0.0306 | 0.0314 | 0.0299 |
| 0.005 | 0.0281 | 0.0355 | 0.0383 | 0.0401 | 0.0398 |
| 0.007 | 0.0542 | 0.0610 | 0.0563 | 0.0655 | 0.0654 |

NN의 이득은 p가 낮을수록 큼(p=0.003에서 BPOSD 대비 −34%), p=0.007에서는 BPOSD* 대비 통계적으로 무의미. 주의: corr-p를 고정했으므로 p가 낮을수록 상관 오류의 비중이 커짐(p 일반화만 분리한 실험이 아님).

BP+OSD 점검 (p=0.003, 5000샷): 가정 그래프 0.0206, oracle 구조 0.0328(반복 300: 0.0328, OSD 차수 100: 0.0312, 스케일 0.9: 0.0436). oracle 구조(hyperedge 포함)가 일관되게 나빠 반복/차수 조정으로 해결되지 않음 → BP+OSD는 hyperedge가 많은 DEM에서 신뢰할 수 있는 기준선이 아님. 비교는 MWPM/BM 계열을 주 기준선으로 하고 BPOSD는 참고로만.
