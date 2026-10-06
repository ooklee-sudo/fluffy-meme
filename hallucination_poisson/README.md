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
(cd paper/misq && node build.js)                                    # MISQ-format manuscript -> paper/MISQ_Manuscript.docx (double-spaced, blind-review front page, proofs in appendices)
python econ_tables.py && (cd paper/econ && node build.js)            # economics-framed variant -> paper/ECON_Manuscript.docx (newsvendor service level, factor substitution, correlated risk)
```

- `runs/<model>/records_nli.jsonl`: 초기 NLI 분류기(L2) 결과(AUC 0.52~0.58, 사실상 무정보)를 부정적 결과로 보존.
- `runs/summary.json`: 논문 표·그림의 모든 수치.
- 도착 시점은 시뮬레이션(NHPP/Cox), 환각·가드레일 판정·지연은 실측입니다.

## 공개 운영 데이터 검증 (real_data.py)

`real_data.py`는 공개 운영 데이터로 포아송 가정을 직접 검정합니다 (환각 로그는 아님).

```bash
mkdir -p data && cd data
for i in 1 2 3; do curl -sSL -O https://github.com/HPMLL/BurstGPT/releases/download/v2.0/BurstGPT_$i.csv; done   # CC BY 4.0, 10.6M 요청
curl -sSL -o outages.zip "https://zenodo.org/records/14018219/files/LLM%20Service%20Outages%20and%20Incident%20Reports.zip?download=1" && unzip -oq outages.zip -d out   # CC BY 4.0
cd .. && python -I real_data.py --burstgpt data \
  --incidents "data/out/LLM Service Outages and Incident Reports/clean_data/incident/2024-08-31/incident_stages.csv" --out runs/real_data.json
./run_all_analyses.sh   # runs/real_data.json 의 시간대 프로파일을 시뮬레이터에 사용 (--profile-file)
```

- BurstGPT (Wang et al., KDD'25): Azure OpenAI 요청, 1초 해상도. 시간대 프로파일, 분 단위 군집성(Fano), 일별 변동성.
- LLM Service Outages and Incident Reports (Chu et al., ICPE'25): OpenAI/Anthropic/Character.AI 상태 페이지 사건. 요일·시간대 층화 과산포 검정, 시간재척도 KS, 지속 시간, M/G/∞ 동시 열린 사건 수.
- 원본 데이터(수백 MB)는 저장소에 포함하지 않습니다.

## 사람 triage 데이터 (triage_data.py)

기업 티켓 데이터로 도착 변동성, 서비스(해결) 시간 분포, 작업량 안전계수, 동시 열린 티켓 수를 분석합니다.

```bash
cd data
# 1) 소프트웨어 회사 Help Desk Tickets (Mendeley, CC BY 4.0, doi:10.17632/btm76zndnt.3)
curl -sSL -o issues.csv "https://data.mendeley.com/public-files/datasets/btm76zndnt/files/2018b884-181a-482b-8a06-a86bbf41f4e7/file_downloaded"
# 2) ServiceNow 인시던트 이벤트 로그 (UCI #498)
curl -sSL -o uci.zip "https://archive.ics.uci.edu/static/public/498/incident+management+process+enriched+event+log.zip" && unzip -oq uci.zip -d uci
# 3) 이탈리아 소프트웨어 회사 Helpdesk (Mendeley, doi:10.17632/39bp3vv62t.1)
curl -sSL -o helpdesk_it.csv "https://data.mendeley.com/public-files/datasets/39bp3vv62t/files/20b5d03f-c6f7-4fdc-91c3-67defd4c67bb/file_downloaded"
cd .. && python -I triage_data.py --issues data/issues.csv --uci data/uci/incident_event_log.csv --italian data/helpdesk_it.csv --out runs/triage_data.json
python summarize.py && cd paper && node build.js
```

## 타입별 고장 모형 (failure_models.py, run_failure_models.py)

고장을 종류별로 나눠 계절성 NHPP, Hawkes(자기흥분), 복합 포아송(에피소드 × 크기)으로 적합합니다.

```bash
python -I run_failure_models.py --burstgpt data \
  --incidents "data/out/LLM Service Outages and Incident Reports/clean_data/incident/2024-08-31/incident_stages.csv" \
  --out runs/failure_models.json --boot 200        # 약 10분 (parametric bootstrap 포함)
python summarize.py && cd paper && node build.js
```

- 공급자 장애: 계절성 NHPP 대비 Hawkes 개선 (분기비 α≈0.11~0.22, 월별 수준 보정 후 0.05~0.09).
- BurstGPT 실패 요청: 활성 분의 약 4%에 실패의 68%가 몰리는 에피소드, 크기 heavy-tail, 정의 민감도(표 10).
- 용량 비교: 단일 포아송 vs 타입별 중첩 (예시 조직, 클래스 독립 가정).


## 전체 재현 순서 (논문 수치)

```bash
pip install -r requirements.txt && (cd . && npm install)            # npm: docx (논문 빌더)
# 1) 모델 실행 (한 번): collect -> retime (3개 generator; 위 "논문 재현" 참고)
# 2) 공개 데이터 내려받기 (data/): BurstGPT, 장애 이력, 티켓 3종, Charlotin CSV (각 절의 curl 명령)
python -I real_data.py --burstgpt data --incidents "data/out/.../incident_stages.csv" --out runs/real_data.json
python -I triage_data.py --issues data/issues.csv --uci data/uci/incident_event_log.csv --italian data/helpdesk_it.csv --out runs/triage_data.json
python -I hallucination_cases.py data/charlotin.csv --out runs/hallucination_cases.json   # https://www.damiencharlotin.com/hallucinations/hallucinations/download.csv
./run_all_analyses.sh                                               # runs/<model>/analysis_*.json, paper_tables.json, summary.json
python -I run_failure_models.py --burstgpt data --incidents "data/out/.../incident_stages.csv" --out runs/failure_models.json --boot 200   # ~30 min
python summarize.py && python make_figures.py                        # summary.json (+ failure/triage/cases), figures
(cd paper && node build.js)                                          # -> runs/LLM_Hallucination_Poisson_Framework_Revised.docx (copy to paper/)
python checks/check_thinning.py; python checks/check_hawkes_recovery.py   # sanity checks of Prop. 3 and the Hawkes estimator
```

- 논문의 모든 수치는 `runs/*.json`에서 `paper/*.js`가 계산해 넣습니다(손으로 쓴 숫자는 일부 문구에 한정).
- 본문 인용은 'et al.'(저자 3명 이상), 참고문헌에는 arXiv API로 대조한 전체 저자(성만)를 적었습니다(2026-10-06; 18편). 저널판(예: Ji 외 CSUR)은 arXiv판과 저자 목록이 다를 수 있으니 최종본에서 확인하세요.

## 2차 검토 반영 요약 (코드)

- `analysis.load_arrays(records, timeout_ms)`: 2초 초과·예외 호출은 fail-open(판정 폐기, 지연 2초로 상한). 이전에는 시간 초과 호출의 판정도 반영했으나(낙관적), 논문 정의에 맞춰 수정. 민감도(느린 판정 대기)는 `summarize.py`의 `late_credit_sensitivity`.
- `triage_data.py`: 근무일을 데이터에서 감지(워크로드 계산에도 적용), 저빈도 휴일/연휴 제외 변형(`arrivals_excl_low_days`, `arrivals_excl_holidays`), ServiceNow 12주 구간, 인과적 용량 계획, 비정상 High-priority 하위집합 제외.
- `real_data.py`: `detrended_daily_cv`가 진짜 CV(표준편차/평균) 반환.
- `hallucination_cases.py`: 미국 연방 공휴일 제외 변형, 최근 월(보고 지연) 제외 기록.
- `run_failure_models.py`: 서빙 에피소드의 부하량 조건부 분산을 정의별로 계산.
