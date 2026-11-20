# 양자화 성능–비용 측정 (llama.cpp)

로컬 소형 LLM(GGUF 양자화)과 클라우드 API를 같은 과제로 비교해, 소싱 모형에 넣을 값
`q_l(b)`(양자화 비트별 품질), `c_l`(로컬 요청당 비용), `c_a`(API 비용), 프라이버시 노출량을 측정합니다.

| 파일 | 역할 |
| --- | --- |
| `tasks.py` | 합성 과제 3종(ticket 분류 / PII 포함 정보 추출 / 다단계 산수) + 사용자 JSONL 과제 로더 |
| `power.py` | `nvidia-smi` GPU 전력·VRAM, Intel RAPL CPU 에너지 측정 |
| `bench.py` | GGUF 모델 1개 측정: 정확도(Wilson 95% CI), 지연, TTFT, tok/s, 에너지, VRAM |
| `api_baseline.py` | 같은 과제를 OpenRouter API로 실행: 토큰·비용·API로 나간 PII 개수 |
| `sweep.py` | HF에서 양자화 사다리(Q2_K…Q8_0)를 받아 순서대로 `bench.py` 실행 |
| `analyze.py` | 요청당 비용, 정답당 비용, 손익분기 호출량 n*, 그래프(`quant_curves.png`), `summary.csv` |

## 설치 (노트북, NVIDIA 8GB)

```bash
pip install -r quant_cost/requirements.txt
# GPU offload가 되려면 CUDA 빌드가 필요합니다 (Windows는 PowerShell에서 $env:CMAKE_ARGS="-DGGML_CUDA=on")
CMAKE_ARGS="-DGGML_CUDA=on" pip install --force-reinstall --no-cache-dir llama-cpp-python
```

## 실행

```bash
# 1) 양자화 사다리 전체 측정 (3B: 전 구간이 8GB에 들어감; 파일은 측정 후 자동 삭제)
python -m quant_cost.sweep --repo Qwen/Qwen2.5-3B-Instruct-GGUF --prefix qwen2.5-3b-instruct --params-b 3 --n 100

# 7B는 q8_0이 8GB를 넘으므로 q6_k까지만
python -m quant_cost.sweep --repo Qwen/Qwen2.5-7B-Instruct-GGUF --prefix qwen2.5-7b-instruct \
    --quants q2_k,q3_k_m,q4_k_m,q5_k_m,q6_k --params-b 7 --n 100

# 2) 클라우드 기준선
export OPENROUTER_API_KEY=sk-or-...
python -m quant_cost.api_baseline --model qwen/qwen-2.5-72b-instruct --n 100

# 3) 비용·손익분기 분석 (가정은 인자로 조정)
python -m quant_cost.analyze --hw-usd 1500 --elec-usd-kwh 0.12 --setup-usd 2000 --value-usd 0.05
```

한 모델만 측정하려면:

```bash
python -m quant_cost.bench --model models/qwen2.5-3b-instruct-q4_k_m.gguf --n 100 --params-b 3
```

자신의 (비식별) 업무 데이터로 측정하려면 `{"prompt":..., "answer":..., "pii":[...]}` 줄로 된 JSONL을 주세요: `--task-file my.jsonl`.

## 비용 모형

- **로컬 요청당 비용** = 에너지(kWh) × 전기요금 + 지연(초) × 노트북가 / (수명 × 가용률)
- **API 요청당 비용** = (프롬프트 토큰 × 입력단가 + 생성 토큰 × 출력단가)
- **정답당 비용** = 요청당 비용 / 정확도 (품질 차이를 비용에 반영)
- **손익분기 n\*** = 고정비 F / (c_api − c_local); `--value-usd`를 주면 정답 가치까지 포함한 순편익 기준 n\*도 계산
- **프라이버시** = API 전송 프롬프트 안의 PII 개수(`pii_entities_sent_per_req`), 로컬은 0

## 측정할 때 주의

- **에너지**: Linux + NVIDIA면 GPU는 `nvidia-smi`, CPU는 RAPL(root 필요)로 측정합니다. Windows는 RAPL이 없어
  `--assumed-cpu-watts`(기본 15W)를 쓰므로 근사입니다. 가장 방어 가능한 값은 **스마트플러그/전력계**의 평균 전력을
  `--wall-watts`(와 유휴 `--wall-idle-watts`)로 넣는 것입니다.
- 노트북은 열 스로틀링이 있으니 AC 전원, 성능 모드, 같은 조건에서 반복 측정하고 사이에 냉각 시간을 두세요.
- `temperature=0`, `seed=0`이라 재현은 되지만 양자화 간 차이를 보려면 `--n`을 100 이상으로 두고 CI를 확인하세요.
- 합성 과제는 방법 검증용입니다. 논문 결과에는 실제 도메인 데이터(`--task-file`)를 쓰는 것이 설득력이 높습니다.
- 양자화 파일은 모델마다 이름 규칙이 다르니 `--prefix`/`--quants`를 HF 저장소의 파일명에 맞춰 주세요.

---

## 연구 문서 구성

| 연구 | 설계 | 설문 | 사전등록 | 규범 값 |
| --- | --- | --- | --- | --- |
| Study 1 (옵션 가치, H1·H3) — 보류 | `experiment_design.md` | `survey_instrument.md` | `preregistration_aspredicted_final.md` | `normative_check.py` |
| **Study 2 (프라이버시 사고 사례 H2, 성능 제시 H3)** | `study2_design.md` | `study2_survey_instrument.md` (구현), `study2_survey_english.md` (영어 최종 문안), `qualtrics_guide_study2.md` (구현 안내) | `study2_preregistration_aspredicted.md` | `normative_check_study2.py` |
| **Study 3 (비용 × 기밀, 지배 비율 ρ; H6–H8) — 개략 설계** | `study3_outline.md` | (미작성) | (미작성) | `normative_check_study3.py` |

공통: 이론 `theory_h2_h3.md`, 선별 문항 `screening_items.md`, 측정 계획 `measurement_plan_rtx4060.md`.
