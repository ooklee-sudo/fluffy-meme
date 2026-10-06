# LLM 환각 NHPP + 다층 가드레일 프레임워크 — 실제 LLM 실행 코드

| 파일 | 역할 |
| --- | --- |
| `backends.py` | `hf:` (로컬 HF), `anthropic:`, `openai:` (vLLM/Ollama 포함), `mock` |
| `data.py` | 데이터(SQuAD v2 / jsonl / builtin)와 환각 정답 라벨(오답 or 답 없는 질문에 답함) |
| `layers.py` | L1 규칙/정규식, L2 NLI 분류기, L3 LLM 판정자 (모두 지연시간·오류 측정) |
| `stats_model.py` | 포아송/NHPP: λ 추정, k* 분위수, 산포·균질성·KS(시간재척도) 검정 |
| `analysis.py` | 모든 가드레일 조합 평가, 목적함수 최적화(문서 3.2절), 제약 SLA |
| `run_experiment.py` | CLI: `collect` / `analyze` / `demo` |

```bash
pip install -r requirements.txt
python run_experiment.py demo        # 오프라인 스모크 테스트(가짜 모델)

# 1) 실제 LLM으로 수집 (비싼 단계, 1회)
python run_experiment.py collect --generator hf:Qwen/Qwen2.5-1.5B-Instruct --judge hf:Qwen/Qwen2.5-1.5B-Instruct \
    --dataset hf:rajpurkar/squad_v2 --n 300 --out runs/qwen
#   API 사용 예: --generator anthropic:<model-id> --judge anthropic:<model-id>   (ANTHROPIC_API_KEY)

# 2) 분석 (싸고 반복 가능: 트래픽/α/SLA/가중치 바꿔가며)
python run_experiment.py analyze --run runs/qwen --days 90 --daily-queries 200 --alpha 0.95 --sla-ms 100
```

## 방법
- 실제 LLM이 답을 생성 → 정답과 비교해 환각 라벨 → 3개 가드레일을 **모든 답에 실행**해 플래그·지연 기록.
- 라벨된 풀에서 시간대별(NHPP) 트래픽을 재생해 "치명적 환각" 이벤트열 생성 → λ̂, k*, 포아송 적합 검정.
- 가드레일 조합별 잔여 λ_N을 **독립성 가정 없이** 경험적으로 계산하고, 문서의 Π(1−c_i) 공식과 비교(`lam(indep)` 열).
- L3는 L2 점수가 `--route-thr` 미만일 때만 호출(동적 라우팅).

## 주의
- 트래픽(질의 수/일)은 시뮬레이션이고, 환각 여부·가드레일 성능·지연은 실측입니다.
- 문서의 "k=3이면 42.3% 부족"은 P(X≤2)이며 실제 P(X>3)=35.3%입니다(k*=6은 맞음). 코드는 후자를 계산합니다.
- 가중치 ω와 SLA 기준(mean/p95/sum)은 목적에 맞게 조정하세요.


## 논문 재현 (hallucination_poisson/paper)

```bash
python run_experiment.py collect --generator hf:Qwen/Qwen2.5-0.5B-Instruct --judge hf:Qwen/Qwen2.5-1.5B-Instruct \
    --dataset hf:rajpurkar/squad_v2 --n 300 --out runs/qwen05      # 기본 L2 = qa:deepset/roberta-base-squad2
python run_experiment.py retime --run runs/qwen05                  # 다른 작업 없이 지연시간 재측정 (--l2 로 L2 교체 가능)
./run_all_analyses.sh                                              # 분석 3종(SLA100/SLA500+비용/버스트) + summary.json
python paper_tables.py && python make_figures.py                   # 해석적 표, 그림
cd paper && node build.js                                          # runs/LLM_Hallucination_Poisson_Framework_Revised.docx
```

- `runs/<model>/records_nli.jsonl`: 초기 NLI 분류기(L2) 결과(AUC 0.52~0.58, 사실상 무정보)를 부정적 결과로 보존.
- `runs/summary.json`: 논문 표·그림의 모든 수치.
- 도착 시점은 시뮬레이션(NHPP/Cox), 환각·가드레일 판정·지연은 실측입니다.
