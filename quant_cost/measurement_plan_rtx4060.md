# 측정 계획: RTX 4060 Laptop 8GB

> 파일 크기는 Hugging Face 저장소 목록에서 읽은 값이다. 실행 시간과 tok/s는 **추정**이며 실제와 다를 수 있다. 이 컨테이너에는 GPU가 없어서 GPU 경로(CUDA 오프로드, nvidia-smi 전력 측정)와 **분할(shard) GGUF 로딩**은 아직 시험하지 못했다. 첫 실행에서 아래 "1단계 점검"으로 확인한다.

## 0. 환경 준비
- AC 전원 연결, 제조사 성능 모드, 다른 GPU 사용 프로그램(브라우저 하드웨어 가속, 게임 등) 종료
- 노트북 4060은 모델마다 전력 한도(TGP)가 35~115W로 다르다. `nvidia-smi -q -d POWER`로 확인하고, 이제 `bench.py`가 결과 JSON에 GPU 이름·드라이버·전력 한도를 자동 기록한다.
- Windows에서는 llama-cpp-python의 CUDA 빌드에 Visual Studio Build Tools와 CUDA Toolkit이 필요하다. 빌드가 어렵다면 프로젝트가 제공하는 사전 빌드 CUDA 휠이 있는지 공식 문서를 먼저 확인한다(제가 확인하지 못함).
- 디스크 여유 공간: 파일은 측정 후 지우지만 한 번에 최대 약 8GB, 전체 다운로드 총량은 수십 GB다.

## 1. 1단계 점검 (10분)
```bash
python -m quant_cost.bench --model models/qwen2.5-3b-instruct-q4_k_m.gguf --n 10 --params-b 3 --out-dir results/quant_cost_check
```
확인할 것: ① 로그에 GPU 오프로드 레이어 수가 보이는가 ② 결과의 `energy_method`가 `gpu_smi+...`인가(`no_gpu_meter`이면 nvidia-smi 전력이 안 읽히는 것) ③ `gpu_peak_mem_mib`가 0이 아닌가 ④ tok/s가 CPU 때보다 크게 높은가. 점검 결과 폴더는 지우고 본 측정을 시작한다.

## 2. 모델 사다리 (Qwen2.5 Instruct, 같은 계열이라 크기·양자화 효과를 분리할 수 있음)

| 모델 | 양자화 | 파일 크기(GiB) | 8GB에서 |
| --- | --- | --- | --- |
| 3B | q2_k / q3_k_m / q4_k_m / q5_k_m / q6_k / q8_0 | 1.28 / 1.61 / 1.96 / 2.27 / 2.60 / 3.37 | 모두 여유 |
| 7B | q2_k | 2.81 | 여유 |
| 7B | q3_k_m | 3.55 | 여유 |
| 7B | q4_k_m (2조각) | 약 4.36 | 여유 |
| 7B | q5_k_m (2조각) | 약 5.08 | 가능 |
| 7B | q6_k (2조각) | 약 5.83 | 가능하나 빠듯 |
| 7B | q8_0 (3조각) | 약 7.54 | **전부 오프로드 불가** (제외) |
| 14B | q2_k (2조각) | 약 5.38 | 가능 |
| 14B | q3_k_m (2조각) | 약 6.84 | **매우 빠듯**, `--n-ctx 1024`로 시도 |

- VRAM에는 가중치 외에 KV 캐시와 CUDA 문맥(약 0.5–1GB)이 든다. 경험칙으로 파일 크기가 약 6.5GiB를 넘으면 위험하다.
- 14B q3_k_m이 안 들어가면 `--n-gpu-layers 36` 같이 일부만 올리고 **그 사실을 결과에 표기**한다(속도·에너지가 크게 달라져 다른 모델과 같은 선에 놓으면 안 된다).
- **핵심 비교(iso-memory)**: 5~6GiB 구간의 `14B q2_k` vs `7B q5_k_m/q6_k` vs `3B q8_0`. "같은 8GB에서 큰 모델을 강하게 양자화할까, 작은 모델을 약하게 양자화할까"가 이 연구의 `q_l(b)`에 현실적인 의미를 준다. `analyze.py`가 `memory_frontier.png`로 이 그림을 그린다.

## 3. 실행
```bash
# 3B 전체
python -m quant_cost.sweep --repo Qwen/Qwen2.5-3B-Instruct-GGUF --prefix qwen2.5-3b-instruct --params-b 3 --n 100

# 7B (q8_0 제외)
python -m quant_cost.sweep --repo Qwen/Qwen2.5-7B-Instruct-GGUF --prefix qwen2.5-7b-instruct \
    --quants q2_k,q3_k_m,q4_k_m,q5_k_m,q6_k --params-b 7 --n 100

# 14B
python -m quant_cost.sweep --repo Qwen/Qwen2.5-14B-Instruct-GGUF --prefix qwen2.5-14b-instruct \
    --quants q2_k --params-b 14 --n 100
python -m quant_cost.sweep --repo Qwen/Qwen2.5-14B-Instruct-GGUF --prefix qwen2.5-14b-instruct \
    --quants q3_k_m --params-b 14 --n 100 -- --n-ctx 1024

# API 기준선(어디서든 가능) 후 분석
OPENROUTER_API_KEY=... python -m quant_cost.api_baseline --model qwen/qwen-2.5-72b-instruct --n 100
python -m quant_cost.analyze --pii-loss-usd 0.01
```
- 끝난 모델은 다시 실행하면 건너뛴다. 중간에 끊겨도 이어서 실행한다.
- 기준선 API 모델은 로컬과 같은 계열(Qwen2.5-72B)로 두는 것이 비교에 유리하다. 다른 계열을 쓰려면 별도 라벨로 추가한다.

## 4. 소요 시간 (추정)
- 요청당 생성 토큰은 arith가 가장 많다(최대 256). 모델당 약 5~10분, 로드와 다운로드 별도.
- 3B 6개 + 7B 5개 + 14B 2개 = 13개 모델, **합계 대략 2~4시간** (다운로드 속도에 크게 의존).
- 한 번에 다 돌리기보다 3B → 7B → 14B 순서로 나눠 돌리고, 모델 사이에 노트북이 식도록 한다.

## 5. 에너지 측정 권장
- `nvidia-smi`는 GPU 보드 전력만 잰다. CPU·디스플레이·기타는 Windows에서 **가정값 15W**가 들어간다.
- 스마트플러그/전력계가 있으면 측정 구간의 평균 벽 전력을 `--wall-watts`로, 유휴 전력을 `--wall-idle-watts`로 넣는다(모델마다 별도 실행 필요: `bench.py`를 직접 호출하거나 `sweep.py` 끝에 `-- --wall-watts 95 --wall-idle-watts 25`).
- 논문 본 결과는 벽 전력 기준으로 하고, `nvidia-smi` 기반 값은 보조로 두는 편이 방어하기 쉽다.

## 6. 측정 후 점검 목록
- [ ] 모든 결과 JSON의 `gpu.name`, `gpu.power_limit_w`, `gpu_peak_mem_mib`가 채워져 있다
- [ ] 일부 레이어만 오프로드한 실행이 있다면 표기했다
- [ ] 같은 조건(전원, 성능 모드, 주변 온도)에서 측정했다
- [ ] 로컬 0.5B 같은 퇴화 모델이 없는지 `records`의 출력을 샘플로 읽었다 (예: 티켓 분류가 한 클래스만 출력)
- [ ] 정확도 신뢰구간이 양자화 간 차이보다 좁은지 확인했다 (좁지 않으면 `--n`을 늘린다)
- [ ] `summary.csv`의 값으로 `survey_instrument.md`의 `[REPLACE]` 수치를 교체했다
