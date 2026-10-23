# 미국증시 위클리 브리핑 — 월요일 KST 08:16 (Bottom + Top Risk Score 포함)

## 0. 기간 확정
- `TZ=Asia/Seoul date`로 직전 미국 주간(월~금)과 주말을 확정한다. 주중 휴장일은 비고에 적는다.
- 주말 뉴스 컷오프: 미국 금요일 장 마감 후부터 월요일 KST 09:00 전까지. 그 이후 나온 정보는 '예정'으로만 쓴다.

## 1. 수집 — WebSearch·WebFetch 합계 22회 이내 (스코어 입력 포함)
- **주간 1차 출처**:
  - portfolio-terminal.com "Stock Market Week in Review <Month D, YYYY>": 지수·섹터 ETF·종목 주간 등락률.
  - AP "How major US stock indexes fared Friday <M/D/YYYY>": 주간·YTD.
  - CappNotes "Closing Look — Friday".
- **빈 항목만 보조 출처**로 채운다: Investrade "Market Review", Wealth Enhancement "Weekly Market Movers".
- **주말 뉴스·월요일 선물**: Tickmill "Daily Market Outlook <월요일>".
- **이번 주 일정**: earnings-watcher.com 주간 implied moves, 실적 캘린더, 매크로·국채 입찰·Fed 일정.
- **BTC·금 주간**: 가격과 주간 등락률을 반드시 채운다.
  - 금: Investing.com·Kitco 주간 기사.
  - BTC: Rio Times "Bitcoin ... on the Week" 또는 CoinDesk 주간 리뷰.
- **스코어 입력** (`common.md` 스코어 절차, `--mode weekly`):
  - CBOE 3개, Put/Call.
  - 재무부(이번 달 + 지난달): y2·y10 최신값과 5·10·20·25영업일 전 값, 20일 내 10Y 최고치.
  - DFF.
  - HY OAS: now, d5, w1(5영업일 전), d10, 3개월 저점과 날짜.
  - FactSet Earnings Insight 직전 금요일호: `https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_MMDDYY.pdf`.
    - 실패하면 WebSearch "FactSet Earnings Insight"로 찾는다.
    - 추출 항목: fwd_pe, eps_4w_change_pct(선행 12M EPS 4주 변화 %), guid_neg, guid_pos.
  - 전주 비교용 `prev`(선택): vix_close, vix3m_close, vix9d_close.

## 2. 채팅 (요약형, 15줄 이내)
제목: "🇺🇸 미국증시 위클리 | YYYY-MM-DD~MM-DD"
1. Headline 1줄: 그 주를 정의한 테마.
2. 스코어 2줄:
   - Bottom: 점수(전주 대비) · 판정 · 유형.
   - Top Risk: 점수(전주 대비) · 판정 · 국면. 국면이 바뀌었으면 "국면 변경 R?→R?"로 강조한다.
   - 이어서 조합 해석 1줄. 예: "Bottom 10 / Top 63 → 지금의 공포는 바닥이 아니라 고점 형성 과정".
3. 경계 해제 조건 1줄: score.py 출력 release를 쓴다. 조건 | 현재값 | 남은 거리.
4. 지수·매크로 주간 표 1개 (2~3행): S&P·Nasdaq·Russell·SOX·VIX / 2Y·10Y(bp) / 유가·BTC·금.
5. 드라이버 Top 3: 증거 강도순 각 1줄 + Fed 기대 1줄.
6. 섹터 1줄: 상위 3 / 하위 3.
7. 주말 뉴스·월요일 선물 1~2줄.
8. 이번 주 볼 것 1줄: 국면 판단을 바꿀 수 있는 지표를 표시한다.
9. 포지셔닝 2줄: 리스크 온/오프/중립 판단(두 스코어와 일관되게) + 페어·헤지.
10. Sources 3개.

## 3. 파일
- 생성기: `gen_xlsx.py`, `gen_docx.js`.
- 파일명: `US_Market_Weekly_YYYY-MM-DD_DD.xlsx/.docx` (미국 주간 월~금).
- 캡션: "YYYY-MM-DD~DD 위클리 — 엑셀 + 워드 1페이지 (Bottom xx / Top xx)".
- 분량: 엑셀 종목은 최대 15개, 워드 종목은 7행.
- 2페이지일 때 축약 순서: ① 드라이버 "참고" 줄 삭제 → ② 주말뉴스 2줄 → ③ 종목 6행 → ④ 실적 2줄 → ⑤ data_note 1문장. 스코어 표는 줄이지 않는다.

## 4. JSON 스키마 — us_daily.md 스키마와 동일하며 아래만 다름
```
"title": "미국증시 위클리 브리핑", "basis_label": "주간+주말 뉴스", "chg_label": "주간 등락률",
"date": "2026-10-12~16"(짧게), "written": 월요일 날짜, "written_kst": "08:16",
"today_sheet_title": "이번 주 볼 것 (MM/DD~MM/DD, 미국시간)",
"earnings_sheet_title": "주간 실적 리뷰",
"indices": 값은 금요일 종가, 등락률은 주간, 금리 bp는 주간 변화. Gold·Bitcoin 주간 등락률 필수.
"weekend_sheet_title": "주말 뉴스 (미국 금요일 장 마감 후)", "weekend_sheet_name": "주말뉴스",
"weekend": [ ["10/17(토)", 뉴스, 시장 영향], ... 3~6개, 마지막 줄은 월요일 아침 선물·유가 ],
"positioning": [ ["판단", ...], ["페어 아이디어", ...], ["헤지", ...], ["경계 해제 조건", "score.py release 요약"] ],
"doc": { ..., "chg_header": "주간", "sources_n": 8,
  "macro" 2·4행 값: 주간 등락률. 예: {"t":"7,659.4 (-1.95%)","dir":"dn"}, "4.73% / 5.10% (-6/-15bp)",
  "weekend_title": "주말 뉴스 (MM/DD~DD) & 월요일 아침", "weekend": 3줄 이내,
  "earnings_title": "주간 실적 (주가 반응)",
  "today_title": "이번 주(MM/DD~DD) 체크 & 포지셔닝",
  "today": [ ["화: ", "제너럴 모터스(GM, ±9.5%), ... | 수: ..."], ["목·금: ", "... | 매크로: ..."] ] }
```
