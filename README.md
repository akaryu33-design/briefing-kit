# briefing-kit

예약 브리핑 작업(미국·한국 데일리/위클리, 바닥신호 알람)이 실행할 때마다 내려받는 공용 키트.

| 파일 | 용도 | 사용 작업 |
|---|---|---|
| `common.md` | 공통 규칙(문체·표기·데이터 원칙·스코어 절차·파일·채팅 요약형) | 전체 |
| `us_daily.md` / `us_weekly.md` | 미국 데일리·위클리 작업 규칙 + JSON 스키마 | 미국 |
| `kr_daily.md` / `kr_weekly.md` | 한국 데일리·위클리 작업 규칙 + JSON 스키마 | 한국 |
| `alarm.md` | 바닥신호 알람 규칙·본문 형식 | 알람 |
| `score.py` | Bottom Score / Top Risk Score 계산 엔진 (`--mode daily/weekly/alarm`) | 미국·알람 |
| `gen_xlsx.py` / `gen_docx.js` | 미국 엑셀·워드 1페이지 생성기 | 미국 |
| `kr_gen_xlsx.py` / `kr_gen_docx.js` | 한국 엑셀·워드 1페이지 생성기 | 한국 |

수정: 같은 이름의 파일을 다시 업로드하면 다음 실행부터 반영된다(raw 캐시 최대 약 5분).
