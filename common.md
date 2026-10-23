# 공통 규칙 — 모든 브리핑·알람 작업

## 사용자와 문체
- 20년차 증권사 애널리스트 출신(운송·자동차·반도체 등 커버) 개인투자자. 개인 투자판단용이다.
- 관점: 절대수익형(absolute return) 헤지펀드 매니저.
- 한국어로 쓰고 영문 전문용어를 병기한다. 표 중심, 애널리스트 수준 깊이.
- 헤지·양비론 없이 증거 강도대로 직설적으로 쓴다. 원인은 증거 강도순으로 가중해서 제시하고, 동등하게 나열하지 않는다.
- 교육업·크레버스 IR 시사점은 넣지 않는다.

## 표기
- 미국 기업은 "한글 풀네임(티커)"로 쓴다. 예: 엔비디아(NVDA), 메타 플랫폼스(META).
- 한국 기업은 "한글 기업명(6자리 종목코드)"로 쓴다. 예: 삼성전자(005930), SK하이닉스(000660).
  - 코드를 확인하지 못한 신규상장 종목은 "엘리스그룹(코스닥 신규)"처럼 쓴다.
- 근사치에는 "~" 대신 "약"을 쓴다. "~"는 마이너스로 오인될 수 있다.
- 워드 파일에는 이모지를 쓰지 않는다(글꼴 미지원). 채팅에서는 써도 된다.
- 금리 곡선 용어:
  - 2Y·10Y가 함께 오르면 bear, 함께 내리면 bull, 방향이 엇갈리면 twist.
  - 2s10s 확대는 steepening, 축소는 flattening.

## 데이터 원칙
- 확인하지 못한 값은 추정하지 않는다. JSON에는 null을 넣고 비고에 "확인 실패"라고 쓴다.
- 원자료가 없는 수치는 만들지 않는다. 계산으로 구한 값은 계산치임을 명시한다.
- 날짜가 맞지 않는 기사는 쓰지 않는다.
- 차단된 사이트는 우회하지 않는다(curl, 캐시, 미러 모두 금지).
- **검색 예산**: 1차 출처에서 확보한 항목은 다시 검색하지 않는다.
  - 같은 항목이 2회 실패하면 "확인 실패"로 처리하고 넘어간다.
  - 검색은 한 턴에 병렬로 묶어서 보낸다.
  - WebSearch·WebFetch 합계 상한은 작업별 규칙 파일에 따른다.

## 관심 종목 (종목 섹션에 우선 반영)
- 미국: SOXX, 엔비디아(NVDA), AMD(AMD), 브로드컴(AVGO), 마이크론 테크놀로지(MU), TSMC(TSM), ASML(ASML), 램리서치(LRCX), 어플라이드 머티어리얼즈(AMAT)
- 한국: 삼성전자(005930), SK하이닉스(000660), 펩트론(087010), 한국콜마(161890), 코스맥스(192820)

## 스코어 (미국 작업)
- 직접 계산하지 않는다. `kit/score.py`로 계산한다.
- 절차:
  1. `kit/inputs.json`을 작성한다. 형식은 `score.py` 상단 docstring을 따른다.
  2. 아래 명령을 실행한다.
     ```
     mkdir -p fg && curl -sS -m 40 -L https://raw.githubusercontent.com/whit3rabbit/fear-greed-data/main/json/cnn_output.json -o fg/cnn.json && curl -sS -m 40 -L https://raw.githubusercontent.com/whit3rabbit/fear-greed-data/main/fear-greed.csv -o fg/fg.csv
     python3 -I kit/score.py fg/cnn.json fg/fg.csv kit/inputs.json --mode <daily|weekly|alarm> --out kit/scores_out.json
     ```
  3. 출력된 점수·판정·유형을 채팅·포지셔닝 판단에 그대로 쓴다. 포지셔닝 판단은 스코어와 일관되게 쓴다.
  4. data.json에 `"scores_from": "scores_out.json"` 한 줄을 넣는다. 생성기가 스코어 시트·워드 표·한 줄 요약을 자동으로 채우므로 scores_detail·doc.scores를 손으로 쓰지 않는다.
     - 예외: 유형을 뉴스로 확정해 바꿔야 하면 doc.scores만 직접 쓴다. 6칸: 구분, 점수, 판정, 국면/유형, 핵심 근거(26자), 전환 조건(16자).
- 입력 데이터 출처:
  - CBOE: `https://cdn-api.cboe.com/api/global/delayed_quotes/quotes/_VIX.json`, `_VIX3M.json`, `_VIX9D.json`. 각각 close, high, price_change, last_trade_time을 확인한다. last_trade_time이 직전 거래일 16:15 ET인지 확인한다.
  - Put/Call: `https://www.cboe.com/us/options/market_statistics/daily/`의 TOTAL PUT/CALL RATIO.
  - 금리: 미 재무부 `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value_month=YYYYMM`
    - 필요한 영업일 수가 이번 달 표에 없으면 지난달도 조회한다.
    - 실패하면 FRED DGS2·DGS10으로 대체하고 "FRED(T−1) 대체"로 표기한다.
  - EFFR: `https://fred.stlouisfed.org/series/DFF`
  - HY OAS: `https://fred.stlouisfed.org/data/BAMLH0A0HYM2.txt`
  - S&P 사상 최고 종가: 참고값은 2026.10.06 7,818.93이다. 경신 여부만 WebSearch로 확인한다.
- CNN 아카이브 timestamp가 직전 거래일 장 마감 이후가 아니면 "아카이브 미갱신"으로 표기한다.

## 파일 생성·검증·전송
1. 작업별 규칙의 스키마대로 `kit/data.json`을 작성한다.
   - 퍼센트·금리 수준은 소수로 쓴다. 예: +1.02% → 0.0102, 5.12% → 0.0512.
   - 한국 수급은 억원 단위 정수로 쓴다.
2. 생성기를 실행한다. `python3 kit/<xlsx 생성기> kit/data.json <파일명>.xlsx`, 이어서 `node kit/<docx 생성기> kit/data.json <파일명>.docx`.
   - docx 패키지가 없으면 `npm install docx`.
   - recalc 검사는 생략한다. 수식이 고정돼 있다.
3. 1페이지를 확인한다.
   - `python3 /mnt/skills/public/docx/scripts/office/soffice.py --headless --convert-to pdf <docx>`를 실행하고 `pdfinfo`로 Pages가 1인지만 확인한다.
   - 2페이지 이상이면 작업별 축약 순서대로 doc 블록을 줄여 다시 생성한다.
   - 렌더링 이미지 확인은 하지 않는다.
4. `SendUserFile`(status "proactive", display "attach")로 xlsx·docx를 한 번에 보낸다.
5. 파일 생성이 실패해도 채팅 브리핑은 반드시 보내고, 실패 사유를 한 줄로 적는다.

## 채팅 브리핑 — 요약형 (SendUserMessage, 지연 로드 상태면 ToolSearch로 먼저 로드)
- 15줄 이내로 쓴다. 상세는 엑셀·워드에 있으므로 채팅에서 반복하지 않는다.
- 줄 구성은 작업별 규칙의 "채팅" 항목을 따른다.
- 표는 최대 1개(지수·매크로 핵심)만 쓴다. 나머지는 한 줄 bullet.
- Sources는 핵심 3개 링크만 넣는다.

## 마무리
- 최종 응답은 한 줄로 쓴다. 예: "전송 완료 — 채팅 + 파일 2개 (Bottom 10 / Top 63)" 또는 실패 사유.
- 채팅 브리핑을 최종 응답에 반복하지 않는다.
