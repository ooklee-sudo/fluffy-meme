# 사전 점검(10명) 실행 절차: 노트북 서버 + 터널

목적은 **작동 여부와 소요 시간 확인**입니다. 가설 검정에는 쓰지 않습니다. 터널 명령은 제가 직접 시험하지 못했으니(기억 기준) 각 서비스의 현재 안내와 다르면 안내를 따르세요.

## 0. 시작 전 결정 (사용자 확인 필요)
1. **터널은 제3자(예: Cloudflare)를 거쳐 응답이 지나갑니다.** 노트북에만 저장되지만, 전송 경로가 IRB 계획서의 "저장·전송" 설명과 맞는지 확인하세요. 사전 점검에서는 응답이 가명 ID와 선택 문항뿐이라 위험이 작지만, 본 수집은 학교 서버나 국내 VPS를 권합니다.
2. **부적격 처리**: 사전 점검에서는 Prolific 필터로 대상을 좁히면 부적격자가 거의 없습니다. 생기면 `config.js`의 `screenoutUrl`에 Prolific의 안내 주소를 넣거나, 비워 두고 Prolific 메시지로 따로 처리합니다.

## 1. 서버 켜기 (터미널 1)
```bash
cd ~/llm-sourcing && git pull
python3 quant_cost/webapp/server.py --port 8765 --data-dir ~/study2_pilot_data
```
응답은 `~/study2_pilot_data/participants/`에 저장됩니다(저장소 밖).

## 2. 터널 열기 (터미널 2)
```bash
cloudflared tunnel --url http://localhost:8765
```
출력에 `https://<무작위>.trycloudflare.com` 주소가 나옵니다(임시 주소이며 재시작하면 바뀝니다). `cloudflared`가 없으면 Cloudflare의 설치 안내를 따르세요.

## 3. 휴대폰으로 직접 확인
휴대폰(와이파이 끄고 LTE)에서 아래 주소를 열어 끝까지 한 번 통과합니다.
```
https://<터널 주소>/?PROLIFIC_PID=TESTPHONE&STUDY_ID=S1&SESSION_ID=X1
```
확인: 글자가 잘리지 않는지, 지불 의사 입력이 편한지, 마지막 화면까지 가는지. 끝나면 `~/study2_pilot_data/participants/TESTPHONE__X1.json`을 지웁니다(점검 보고서에 섞이지 않도록).

## 4. Prolific 초안 연구 만들기 (사용자가 직접)
- 연구 유형: 외부 설문 링크. 설문 주소: `https://<터널 주소>/?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}` (표기가 현재 Prolific 화면과 같은지 확인).
- 참가 인원 10, 예상 소요 19분, 보상 시급 $12 기준 약 $3.80, 선별 필터는 본 수집 계획과 같게.
- Prolific이 보여 주는 **완료 URL**을 복사해 `public/config.js`의 `completeUrl`에 넣고 서버를 재시작하지 않아도 되며(정적 파일) 브라우저만 새로고침합니다.
- 공개(게시)와 결제는 사용자가 직접 합니다. 먼저 Prolific의 미리보기로 완료 화면의 리디렉션을 확인하세요.

## 5. 진행 중
- 노트북은 AC 전원, 절전 해제, 두 터미널 모두 켜 둡니다.
- 진행 확인: `ls ~/study2_pilot_data/participants | wc -l`

## 6. 끝난 뒤
```bash
python3 quant_cost/webapp/pilot_report.py --data-dir ~/study2_pilot_data
python3 quant_cost/webapp/export_csv.py --data-dir ~/study2_pilot_data --out ~/study2_pilot_data/pilot_wide.csv --all
```
두 터미널에서 `Ctrl+C`로 터널과 서버를 닫습니다. 보고서의 소요 시간, 이탈 지점, 지불 의사 품질, 대체 규칙 발동 여부를 보고 문안이나 가격을 조정한 뒤 설문을 **동결**하고 사전등록을 제출합니다. 사전 점검 응답은 본 분석에 포함하지 않습니다.
