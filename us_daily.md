# 미국증시 데일리 브리핑 (모닝 미팅형) — KST 08:45, 화~토

## 0. 휴장 확인
- Bash로 `TZ=Asia/Seoul date`와 `TZ=America/New_York date`를 확인하고 직전 미국 거래일을 확정한다.
- 직전 거래일이 NYSE 휴장이면 "전일 미국 휴장(사유)" 한 줄과 당일 일정만 보내고 종료한다. 파일은 만들지 않는다.
- 토요일 실행분은 '오늘 일정'을 '다음 주 월요일 일정'으로 바꿔 쓴다.

## 1. 수집 — WebSearch·WebFetch 합계 18회 이내 (스코어 입력 포함)
- **정규장 1차 출처**: CappNotes "Closing Look — <요일>, <Month D, YYYY>" (cappnotes.substack.com).
  - 지수·금리·원자재·11개 섹터·breadth·시간외 실적·Kalshi·다음날 일정이 모두 들어 있다.
  - 여기서 확보한 항목은 재검색하지 않는다.
- **빈 항목만 보조 출처**로 채운다: Investrade "Market Review", 서울경제 영문(en.sedaily.com, Mag 7·반도체 등락률), AP "How major US stock indexes fared".
- **오버나이트**:
  - 지수선물 최신 등락률과 기준 시각(ET): CNBC "Stock futures", Yahoo.
  - 장후 실적: 매출·EPS vs 컨센서스, 가이던스, 콜 핵심, 시간외 반응. 출처는 investingLive "Americas FX news wrap" 또는 회사 보도자료.
  - 지정학·매크로 뉴스.
  - 아시아는 실행 시점에 개장 전이므로 "개장 전"으로 표기한다.
- **오늘 일정**:
  - Newsquawk "Daily US Earnings Estimates": 컨센서스·발표 시각.
  - earnings-watcher.com 주간 implied moves.
  - Investrade "Weekly Event Calendar".
- **BTC·금**: 가격과 일간 등락률을 반드시 채운다. CappNotes에 없을 때만 Kitco(금)와 CoinDesk(BTC)를 1회씩 검색한다.
- **스코어 입력** (`common.md` 스코어 절차): CBOE 3개, Put/Call, 재무부(이번 달), DFF, HY OAS.
  - `ust`에는 y2·y10 최신값과 5영업일 전 값(y2_5d, y10_5d)을 넣는다. 가능하면 6영업일 전 값(y2_6d, y10_6d)과 전일 값(y2_prev, y10_prev)도 넣는다. 전일 대비 계산용이다.
  - `hy_oas`에는 now와 d5를 넣는다. `--mode daily`로 실행한다.

## 2. 채팅 (요약형, 15줄 이내)
제목: "🇺🇸 미국증시 데일리 | YYYY-MM-DD(요일) — 모닝 미팅용"
1. Headline 1줄: 정규장 + 선물 방향.
2. Bottom Score 1줄: 점수(전일 대비) · 판정 · 유형 · 핵심 근거 · 전환 조건.
3. 지수·매크로 표 1개 (2~3행): S&P·Nasdaq·SOX·VIX / 2Y·10Y(bp) / 유가·BTC·금(가격·등락률).
4. 드라이버 Top 3: 증거 강도순 각 1줄.
5. 오버나이트 1~2줄: 선물 + 장후 핵심.
6. 오늘 볼 것 1줄: 핵심 실적(implied move)과 지표.
7. 포지셔닝 2줄: 판단(개장 후 확인 조건 포함) + 페어·헤지.
8. Sources 3개.

## 3. 파일
- 생성기: `gen_xlsx.py`, `gen_docx.js`.
- 파일명: `US_Market_Briefing_YYYY-MM-DD.xlsx/.docx` (작성일 = 한국 날짜).
- 캡션: "YYYY-MM-DD 미국증시 데일리 — 엑셀 + 워드 1페이지 (Bottom Score xx)".
- 분량 기본값: 종목은 엑셀 12개 이내·워드 6행, 드라이버 3줄, 오버나이트 4줄, 실적 2줄.
- 2페이지일 때 축약 순서: ① 오버나이트 3줄 → ② 종목 5행 → ③ data_note 1문장. 스코어 표와 한 줄 요약은 줄이지 않는다.

## 4. JSON 스키마 (data.json)
```
{
 "title": "미국증시 데일리 브리핑",
 "basis_label": "정규장 마감 + 오버나이트(ET 10/21 20시) 기준",
 "date": "2026-10-21(수)", "written": "<TZ=Asia/Seoul date +%F>", "written_kst": "<TZ=Asia/Seoul date +%H:%M>",
 "headline_bold": "핵심 한 문장.", "headline_rest": "보충 1~2문장.",
 "indices": [ [이름, 수준|null, 등락률(소수)|null, 금리bp|null, 비고, 금리여부(bool, 생략 가능)], ... ],
   이름 고정: "S&P 500","Nasdaq Composite","Dow Jones","Russell 2000","S&P 500 Equal Weight (RSP)","SOX (필라델피아 반도체)","VIX",
             "UST 2Y","UST 10Y","UST 30Y","DXY","Brent (Dec)","WTI (Dec)","Gold (Dec, $/oz)","Copper (Dec, $/lb)","Bitcoin ($)"
             (근월물 월만 실제에 맞게 변경). 금리 행 예: ["UST 10Y", 0.0513, null, 1, "", true].
             BTC 비고에는 기준 시점(24h 등)을 적는다.
 "breadth": [상승, 하락] | null,
 "scores_from": "scores_out.json",
 "drivers": [ [1, 요인, 근거, "높음"], [2, ...], [3, ...], ["참고", 요인, 근거, 비고] ],
 "fed": "Fed 기대 한 문장(Kalshi/FedWatch)",
 "sectors": [ ["Information Technology", 0.0167], ... 11개 전부(영문 표준명) ],
 "sector_notes": { "섹터": "8자 내외", ... 상·하위 3개에만 }, "sector_comment": "2~3문장",
 "stocks": [ [기업명(티커), 종가|null, 등락률(소수), 원인(장후 반응 포함), 헤지펀드 시각, 근거], ... 최대 12개 ], "stock_note": "",
 "earnings": [ ["메타 플랫폼스(META), 장후", 결과, 주가 반응, 시사점], ... ],
 "today_sheet_title": "오늘 볼 것 (MM/DD, 미국시간)",
 "today": [ [시간, "유니언 퍼시픽(UNP)", implied move|null, "컨센 EPS $3.47 · 포인트"], ... ],
 "weekend_sheet_title": "오버나이트 & 프리마켓 (모닝 미팅용)", "weekend_sheet_name": "오버나이트",
 "weekend": [ [시점(ET), 뉴스, 영향], ... 5~7개: 선물 → 장후 실적 → 이벤트 → 아시아 → 금리 ],
 "positioning": [ ["판단", ...], ["페어 아이디어", ...], ["헤지", ...], ["모닝 미팅 논점", "① ② ③ ④"] ],
 "sources": [ [제목, URL], ... ], "data_note": "2문장 이내",
 "doc": {
   "macro": 4행×6열 고정.
     1행 ["S&P 500","Nasdaq","Dow","Russell 2000","SOX","VIX"]
     2행 값 셀, 예: {"t":"7,757.2 (+0.58%)","dir":"up"|"dn"}
     3행 ["UST 2Y / 10Y","30Y · 2s10s","Brent (Dec)","WTI (Dec)","BTC","Gold (Dec)"]
     4행 예: ["4.81% / 5.13% (+2/+1bp)","5.42%(0bp) · 32bp",{"t":"$108.82 (+0.03%)","dir":"up"},...]
     BTC·Gold 셀은 "가격 (등락률)" 형식으로 쓴다.
   "drivers": [ ["① 요인 [높음] ", "— 근거 한 줄"], ... 3줄 ],
   "weekend_title": "오버나이트 & 프리마켓", "weekend": [ ["선물(ET 19:38): ", "..."], ... 4줄 이내 ],
   "sector_comment": "20자 내외",
   "stocks": [ [기업명(티커), "+9.55%", 원인(22자), 시각, 근거(16자), 강조여부], ... 6개 ],
   "earnings_title": "실적 (주가 반응)", "earnings": [ ["램리서치(LRCX) 장후 -6.3%: ", "내용"], ... 2줄 ],
   "today_title": "오늘(MM/DD) 체크 & 포지셔닝",
   "today": [ ["장전: ", "유니언 퍼시픽(UNP, ±3.8%, EPS $3.47), ... / 08:30 ET 지표"], ["장후: ", "..."] ],
   "positioning": [ ["판단: ... ", "— 근거·개장 후 확인 조건", true], ["페어/헤지: ", "..."] ]
 }
}
```
