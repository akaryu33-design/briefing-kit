"""바닥·고점 신호 공통 스코어 엔진 (Bottom Score / Top Risk Score).

사용:
  python3 -I score.py cnn.json fg.csv inputs.json --mode daily|weekly|alarm [--out scores_out.json]

- cnn.json, fg.csv : whit3rabbit/fear-greed-data 아카이브 (curl로 받음)
- inputs.json      : WebFetch로 확인한 시장 데이터 (아래 INPUTS 예시). 모르는 값은 null → 0점 + "확인 실패".
- mode            : daily = Bottom(전일 대비) / weekly = Bottom+Top(전주 대비) / alarm = Bottom + 알람 조건 판정
- 출력            : 화면 요약 + scores_out.json (scores_detail·doc_scores·scores_line·alarm 등; 생성기가 scores_from 으로 읽음)

INPUTS 예시 (금리·OAS는 % 단위, 예: 4.81):
{
 "asof": "2026-10-22",
 "vix":   {"close": 19.03, "high": 20.4, "price_change": -0.41},
 "vix3m": {"close": 20.9, "price_change": -0.2},
 "vix9d": {"close": 18.1, "price_change": -0.6},
 "cboe_pc_total": 0.94,
 "ust": {"y2": 4.81, "y2_5d": 4.85, "y2_20d": 4.70, "y10": 5.13, "y10_5d": 5.20, "y10_20d": 5.00, "y10_20d_high": 5.25,
         "y2_6d": null, "y10_6d": null,            # (daily 전일 비교용, 선택) 6영업일 전
         "y2_10d": null, "y10_10d": null, "y2_25d": null, "y10_25d": null},   # (weekly 전주 비교용, 선택)
 "effr": 4.33,
 "hy_oas": {"now": 3.10, "d5": 3.02, "low3m": 2.80, "low3m_date": "2026-08-01", "w1": 3.02, "d10": null},
 "factset": {"fwd_pe": 23.4, "eps_4w_change_pct": 0.6, "guid_neg": 32, "guid_pos": 21},   # weekly만
 "spx_ath": 7818.93, "spx_ath_date": "2026-10-06",
 "prev": {"vix9d_close": null, "cboe_pc_total": null}   # 선택: 전일/전주 값 직접 지정
}
"""
import json, sys, csv, datetime, argparse

ap = argparse.ArgumentParser()
ap.add_argument("cnn"); ap.add_argument("fgcsv"); ap.add_argument("inputs")
ap.add_argument("--mode", default="daily", choices=["daily", "weekly", "alarm"])
ap.add_argument("--out", default="scores_out.json")
a = ap.parse_args()

D = json.load(open(a.cnn)); I = json.load(open(a.inputs))
FG_ROWS = [(r["Date"], float(r["Fear Greed"])) for r in csv.DictReader(open(a.fgcsv))]


def g(dct, *keys):
    for k in keys:
        if dct is None: return None
        dct = dct.get(k) if isinstance(dct, dict) else None
    return dct


def daily(k):
    o = {}
    for p in D[k]["data"]:
        o[datetime.datetime.fromtimestamp(p["x"] / 1000, datetime.timezone.utc).date().isoformat()] = p["y"]
    return sorted(o.items())


SER = {k: daily(k) for k in ["market_momentum_sp500", "market_momentum_sp125", "fear_and_greed_historical", "stock_price_strength",
                              "put_call_options", "market_volatility_vix", "junk_bond_demand"]}
DATES = [x for x, _ in SER["market_momentum_sp500"]]


def upto(k, date):
    return [(x, v) for x, v in SER[k] if x <= date]


def at(k, date):
    s = upto(k, date)
    return s[-1][1] if s else None


def cnn_ctx(offset):
    """CNN 아카이브에서 offset 거래일 전 시점의 지표."""
    date = DATES[-1 - offset]
    spx = upto("market_momentum_sp500", date)
    cur = spx[-1]
    prior20 = min(v for _, v in spx[-21:-1])
    pl = min(spx[-60:-5], key=lambda x: x[1])
    jb = upto("junk_bond_demand", date); vx = upto("market_volatility_vix", date)
    rows = [r for r in FG_ROWS if r[0] <= date]
    fg_now = D["fear_and_greed"]["score"] if offset == 0 else at("fear_and_greed_historical", date)
    mx = max(rows[-121:], key=lambda x: x[1]) if rows else (None, None)
    return {
        "date": date, "spx": cur[1], "ma125": at("market_momentum_sp125", date),
        "new20low": cur[1] <= prior20, "prior20low": prior20,
        "swing_date": pl[0], "fg_then": at("fear_and_greed_historical", pl[0]), "fg_now": fg_now,
        "str_then": at("stock_price_strength", pl[0]), "str_now": at("stock_price_strength", date),
        "pc5": at("put_call_options", date),
        "junk": jb[-1][1], "junk20max": max(v for _, v in jb[-20:]),
        "vix_cnn": vx[-1][1], "vix20min": min(v for _, v in vx[-21:-1]),
        "fg120max": mx[1], "fg120max_date": mx[0],
        "spx_cnn_max": max(v for _, v in spx),
    }


def r1(x, n=2):
    return None if x is None else round(x, n)


def fit(parts, n=26, sep=" · "):
    out = ""
    for x in parts:
        t = x if not out else out + sep + x
        if len(t) > n: break
        out = t
    return out


SHORT = {"A": "A 긴축형", "B": "B 외생형", "C": "C 포지셔닝", "D": "D 신용형", "E": "E 쏠림형"}


def fmt(x, n=2, suf=""):
    return "확인 실패" if x is None else f"{x:.{n}f}{suf}"


# ───────────── Bottom Score ─────────────
def bottom(c, m):
    """c: CNN ctx, m: 시장 입력 {vix, vix_high, vix3m, vix9d, pc_total, y10_5d_bp, spread_5d_bp, hy_5d_bp}"""
    rows, fails = [], []
    fg = c["fg_now"]
    s_fg = 0 if fg is None else (30 if fg <= 10 else 20 if fg < 15 else 10 if fg < 25 else 0)
    if fg is None: fails.append("F&G")
    rows.append(["Bottom Score", "F&G (투매)", fmt(fg, 1), "<25:10 / <15:20 / ≤10:30", s_fg, f"CNN {c['date']}"])

    v, v3, v9 = m["vix"], m["vix3m"], m["vix9d"]
    ratio = v / v3 if v and v3 else None
    r9 = v9 / v if v and v9 else None
    s_ts = 0
    if ratio is None: fails.append("VIX÷VIX3M")
    else:
        s_ts = 20 if ratio > 1.10 else 10 if ratio >= 1.00 else 0
        if r9 is not None and r9 > 1.05: s_ts = min(20, s_ts + 5)
    rows.append(["Bottom Score", "VIX÷VIX3M (+VIX9D÷VIX)", f"{fmt(ratio)} (9D÷VIX {fmt(r9)})", "1.00~1.10:10 / >1.10:20 / 9D>1.05:+5", s_ts, f"VIX {fmt(v)} · 3M {fmt(v3)} · 9D {fmt(v9)}"])

    pc, pc5 = m["pc_total"], c["pc5"]
    s_pc = 10 if ((pc is not None and pc > 1.2) or (pc5 is not None and pc5 > 1.0)) else 0
    if pc is None and pc5 is None: fails.append("Put/Call")
    rows.append(["Bottom Score", "Put/Call", f"CBOE {fmt(pc)} · CNN 5일 {fmt(pc5)}", "CBOE>1.2 또는 CNN>1.0:10", s_pc, ""])

    hy5 = m["hy_5d_bp"]
    stress = hy5 is not None and hy5 >= 50
    junk_narrow = c["junk20max"] - c["junk"]
    s_cr = 0 if stress else (20 if junk_narrow >= 0.25 else 0)
    rows.append(["Bottom Score", "신용 (정크 스프레드 축소)", f"{c['junk']:.2f}%p (20일 최고 {c['junk20max']:.2f}, 축소 {junk_narrow:.2f}) · HY OAS 5일 {fmt(hy5, 0, 'bp')}",
                 "20일 최고 대비 −0.25%p 축소:20 / HY 5일 ≥+50bp:0", s_cr, "신용 스트레스 경고" if stress else ""])

    div = c["new20low"] and ((c["fg_now"] or 0) >= (c["fg_then"] or 999) + 5 or (c["str_now"] or -999) > (c["str_then"] or 999))
    s_br = 20 if div else 0
    rows.append(["Bottom Score", "breadth 다이버전스", f"{'20일 신저가' if c['new20low'] else '신저가 아님'} · FG {fmt(c['fg_then'],1)}→{fmt(c['fg_now'],1)} · strength {fmt(c['str_then'])}→{fmt(c['str_now'])}",
                 "신저가 + (FG +5 또는 strength 상승):20", s_br, f"직전 스윙저점 {c['swing_date']}"])

    y10, sp = m["y10_5d_bp"], m["spread_5d_bp"]
    if y10 is None and sp is None: fails.append("게이트 금리"); mult = 1.0
    elif (y10 is not None and y10 >= 15) or (sp is not None and sp >= 10): mult = 0.5
    elif sp is not None and sp <= -15: mult = 1.2
    else: mult = 1.0
    rows.append(["Bottom Score", "게이트 승수", f"10Y 5일 {fmt(y10, 0, 'bp')} · 2Y−EFFR 5일 {fmt(sp, 0, 'bp')}", "긴축 ×0.5 / 피벗 ×1.2 / 그 외 ×1.0", None, f"×{mult}"])

    raw = s_fg + s_ts + s_pc + s_cr + s_br
    score = min(100, round(raw * mult))
    judge = "적극 분할매수" if score >= 70 else "1차 분할매수" if score >= 50 else "관찰" if score >= 30 else "바닥 신호 없음"
    if len(fails) >= 3: judge = "(제한적 판단) " + judge
    # 유형 후보 (수치 조건만 — B 원인 확인·최종 판정은 뉴스로)
    dd = c["dd"]
    types = []
    if (y10 is not None and y10 >= 15) or (sp is not None and sp >= 10): types.append("A 긴축·금리")
    if y10 is not None and y10 <= -10: types.append("B 외생 쇼크(원인 확인)")
    if v and ((m["vix_high"] and m["vix_high"] - v >= 5) or (c["vix20min"] and v / c["vix20min"] >= 2.5)): types.append("C 포지셔닝 붕괴")
    if stress: types.append("D 신용 이벤트")
    if fg is not None and fg < 25 and dd is not None and dd > -0.05 and v is not None and v < 25: types.append("E 쏠림·breadth 공포")
    if not types: types = ["해당 없음(평상)"] if (fg is None or fg >= 25) else ["유형 불명"]
    rows.append(["Bottom Score", "합계", f"{raw} × {mult}", "≥70 적극 / 50~69 1차 / 30~49 관찰 / <30 없음", score, judge])
    rows.append(["Bottom Score", "유형 후보", " / ".join(types), "A 긴축 · B 외생 · C 포지셔닝 · D 신용 · E 쏠림", None, "수치 조건 기준"])
    parts = {"F&G": s_fg, "VIX 기간구조": s_ts, "P/C": s_pc, "신용": s_cr, "breadth": s_br}
    return {"score": score, "raw": raw, "mult": mult, "judge": judge, "types": types, "rows": rows, "fails": fails, "parts": parts,
            "ratio": ratio, "r9": r9, "stress": stress, "fg": fg}


# ───────────── Top Risk Score ─────────────
W = {"R1": (35, 30, 15, 15, 5), "R2": (15, 20, 30, 15, 20), "R3": (10, 30, 15, 35, 10), "R4": (25, 25, 25, 15, 10)}


def top(c, m):
    rows, fails = [], []
    y2, y10, effr = m["y2"], m["y10"], m["effr"]
    sp = (y2 - effr) * 100 if y2 is not None and effr is not None else None
    d2 = m["y2_20d_bp"]; d10 = m["y10_20d_bp"]
    pe = m["fwd_pe"]; erp = (100 / pe - y10) if pe and y10 is not None else None
    eps = m["eps_4w"]; gneg, gpos = m["guid_neg"], m["guid_pos"]
    hy, low = m["hy_now"], m["hy_low3m"]
    wid = (hy - low) * 100 if hy is not None and low is not None else None
    dd = c["dd"]
    for nm, val in [("2Y−EFFR", sp), ("ERP", erp), ("HY OAS 확대폭", wid), ("선행 EPS 4주", eps)]:
        if val is None: fails.append(nm)
    # 국면
    r3 = d2 is not None and d2 <= -50 and ((eps is not None and eps < 0) or (wid is not None and wid >= 50))
    r1c = [sp is not None and sp > 25, d2 is not None and d2 >= 25, d10 is not None and d10 >= 30, erp is not None and erp < 1.0]
    r2 = sp is not None and sp < -25 and eps is not None and eps > 0 and wid is not None and wid < 25
    regime = "R3" if r3 else "R1" if any(r1c) else "R2" if r2 else "R4"
    names = {"R1": "R1 긴축 압력", "R2": "R2 연착륙형 완화", "R3": "R3 침체형 인하", "R4": "R4 중립"}
    rows.append(["Top Risk Score", "국면 판정", names[regime],
                 f"R3 {'✅' if r3 else '❌'} · R1 [2Y−EFFR>25 {'✅' if r1c[0] else '❌'} 2Y20d≥25 {'✅' if r1c[1] else '❌'} 10Y20d≥30 {'✅' if r1c[2] else '❌'} ERP<1 {'✅' if r1c[3] else '❌'}] · R2 {'✅' if r2 else '❌'}",
                 None, f"2Y−EFFR {fmt(sp,0,'bp')} · 2Y 20일 {fmt(d2,0,'bp')} · 10Y 20일 {fmt(d10,0,'bp')} · ERP {fmt(erp,2,'%p')}"])
    w = W[regime]
    f_rate = min(1, (0.4 if r1c[0] else 0) + (0.4 if r1c[3] else 0) + (0.2 if (r1c[1] or r1c[2]) else 0))
    f_cr = 0 if wid is None else 1.0 if wid >= 100 else 0.6 if wid >= 50 else 0.3 if wid >= 25 else 0
    near5 = dd is not None and dd > -0.05
    sps, spb = m["str_score"], m["breadth_score"]
    f_br = min(1, (0.6 if near5 and sps is not None and sps < 30 else 0) + (0.4 if near5 and spb is not None and spb < 30 else 0))
    f_ep = min(1, (0.6 if eps is not None and eps < 0 else 0) + (0.4 if gneg is not None and gpos is not None and gneg > gpos else 0))
    gap = (c["fg_now"] - c["fg120max"]) if c["fg_now"] is not None and c["fg120max"] is not None else None
    near3 = dd is not None and dd > -0.03
    f_se = 0 if not near3 or gap is None else 1.0 if gap <= -15 else 0.5 if gap <= -10 else 0
    areas = [("금리·유동성", f"2Y−EFFR {fmt(sp,0,'bp')} · ERP {fmt(erp,2,'%p')} · 10Y/2Y 20일 {fmt(d10,0)}/{fmt(d2,0)}bp", f_rate),
             ("신용", f"HY OAS {fmt(hy)}% (3M 저점 {fmt(low)}% {m['hy_low3m_date'] or ''}, +{fmt(wid,0,'bp')})", f_cr),
             ("breadth", f"고점 대비 {fmt(dd*100 if dd is not None else None,2,'%')} · strength {fmt(sps,1)} · breadth {fmt(spb,1)}", f_br),
             ("이익", f"선행 EPS 4주 {fmt(eps,2,'%')} · 가이던스 부정 {gneg}/긍정 {gpos} · P/E {fmt(pe,1)}", f_ep),
             ("심리 다이버전스", f"F&G {fmt(c['fg_now'],1)} vs 120일 최고 {fmt(c['fg120max'],1)} ({fmt(gap,1)})", f_se)]
    total = 0
    for (nm, val, f), wt in zip(areas, w):
        pts = round(wt * f, 1); total += pts
        rows.append(["Top Risk Score", nm, val, f"가중치 {wt} × 충족도 {f:.1f}", pts, ""])
    score = round(total)
    pconf = (c["ma125"] is not None and c["spx"] < c["ma125"]) or (dd is not None and dd <= -0.05)
    judge = "방어 전환" if score >= 80 or (score >= 60 and pconf) else "리스크 축소" if score >= 60 else "경계" if score >= 40 else "정상"
    if len(fails) >= 3: judge = "(제한적 판단) " + judge
    rows.append(["Top Risk Score", "합계", f"{names[regime]}", "<40 정상 / 40~59 경계 / 60~79 축소 / ≥80·60+가격확인 방어", score, judge])
    rows.append(["Top Risk Score", "가격 확인", f"S&P {c['spx']:,.2f} · 125일선 {fmt(c['ma125'])} · 고점 대비 {fmt(dd*100 if dd is not None else None,2,'%')}",
                 "S&P<125일선 또는 고점 −5%", None, "충족" if pconf else "미충족"])
    # 경계 해제 조건
    rel = []
    if regime == "R1":
        rel.append(["2Y−EFFR < +25bp", "<25bp", fmt(sp, 0, "bp"), fmt(None if sp is None else sp - 25, 0, "bp")])
        hi = m["y10_20d_high"]
        rel.append(["10Y 최근 고점 대비 −25bp", f"≤{fmt(None if hi is None else hi - 0.25, 2, '%')}", fmt(y10, 2, "%"),
                    fmt(None if hi is None or y10 is None else (y10 - (hi - 0.25)) * 100, 0, "bp")])
        rel.append(["ERP ≥ 1.0%p", "≥1.0%p", fmt(erp, 2, "%p"), fmt(None if erp is None else 1.0 - erp, 2, "%p")])
        rel.append(["HY OAS 3M 저점 +25bp 이내", f"≤{fmt(None if low is None else low + 0.25, 2, '%')}", fmt(hy, 2, "%"), fmt(None if wid is None else wid - 25, 0, "bp")])
        cond_short = "2Y−EFFR <25bp"
    elif regime == "R2":
        rel.append(["stock_price_strength > 50", ">50", fmt(sps, 1), fmt(None if sps is None else 50 - sps, 1)])
        rel.append(["F&G 120일 최고 대비 −10 이내", "≥−10", fmt(gap, 1), fmt(None if gap is None else -10 - gap, 1)])
        cond_short = "strength >50"
    elif regime == "R3":
        rel.append(["선행 EPS 4주 변화 ≥ 0", "≥0%", fmt(eps, 2, "%"), fmt(None if eps is None else -eps, 2, "%")])
        rel.append(["HY OAS 축소 전환", "5일 변화 <0", fmt(m["hy_5d_bp"], 0, "bp"), ""])
        cond_short = "EPS 4주 ≥0"
    else:
        rel.append(["Top Risk < 40 2주 연속", "<40", str(score), str(max(0, score - 39))])
        cond_short = "2주 연속 <40"
    for x in rel:
        rows.append(["Top Risk Score", "경계 해제: " + x[0], x[2], x[1], None, "남은 거리 " + x[3]])
    return {"score": score, "judge": judge, "regime": regime, "regime_name": names[regime], "rows": rows, "fails": fails,
            "release": rel, "cond_short": cond_short, "areas": [(nm, f, wt) for (nm, _, f), wt in zip(areas, w)],
            "sp": sp, "erp": erp, "wid": wid, "pconf": pconf}


# ───────────── 입력 정리 ─────────────
def bp(a_, b_):
    return None if a_ is None or b_ is None else (a_ - b_) * 100


ust = I.get("ust", {}) or {}; hy = I.get("hy_oas", {}) or {}; fs = I.get("factset", {}) or {}; pv = I.get("prev", {}) or {}
vix = I.get("vix", {}) or {}; v3 = I.get("vix3m", {}) or {}; v9 = I.get("vix9d", {}) or {}
effr = I.get("effr")


def ath_dd(c):
    ath = max([x for x in [I.get("spx_ath"), c["spx_cnn_max"]] if x is not None])
    c["ath"] = ath; c["dd"] = c["spx"] / ath - 1
    return c


def prevclose(q):
    return None if q.get("close") is None or q.get("price_change") is None else q["close"] - q["price_change"]


m_now = {"vix": vix.get("close"), "vix_high": vix.get("high"), "vix3m": v3.get("close"), "vix9d": v9.get("close"),
         "pc_total": I.get("cboe_pc_total"), "y10_5d_bp": bp(ust.get("y10"), ust.get("y10_5d")),
         "spread_5d_bp": bp(ust.get("y2"), ust.get("y2_5d")),  # EFFR 5일 불변 가정 (변경 시 effr_5d 입력)
         "hy_5d_bp": bp(hy.get("now"), hy.get("d5"))}
if I.get("effr_5d") is not None and m_now["spread_5d_bp"] is not None:
    m_now["spread_5d_bp"] -= (effr - I["effr_5d"]) * 100

c0 = ath_dd(cnn_ctx(0))
off = 5 if a.mode == "weekly" else 1
c1 = ath_dd(cnn_ctx(off))
notes = []
if a.mode == "weekly":
    m_prev = {"vix": pv.get("vix_close"), "vix_high": None, "vix3m": pv.get("vix3m_close"), "vix9d": pv.get("vix9d_close"),
              "pc_total": pv.get("cboe_pc_total"), "y10_5d_bp": bp(ust.get("y10_5d"), ust.get("y10_10d")),
              "spread_5d_bp": bp(ust.get("y2_5d"), ust.get("y2_10d")), "hy_5d_bp": bp(hy.get("w1"), hy.get("d10"))}
    if m_prev["vix"] is None:
        m_prev["vix"] = c1["vix_cnn"]; notes.append("전주 VIX는 CNN 아카이브 값")
else:
    m_prev = {"vix": prevclose(vix), "vix_high": None, "vix3m": prevclose(v3), "vix9d": pv.get("vix9d_close", prevclose(v9)),
              "pc_total": pv.get("cboe_pc_total"), "y10_5d_bp": bp(ust.get("y10_prev"), ust.get("y10_6d")),
              "spread_5d_bp": bp(ust.get("y2_prev"), ust.get("y2_6d")), "hy_5d_bp": m_now["hy_5d_bp"]}
    if m_prev["y10_5d_bp"] is None and m_prev["spread_5d_bp"] is None:
        m_prev["y10_5d_bp"] = m_now["y10_5d_bp"]; m_prev["spread_5d_bp"] = m_now["spread_5d_bp"]; notes.append("전일 게이트는 당일 값 재사용")

B0 = bottom(c0, m_now); B1 = bottom(c1, m_prev)
arrow = lambda a_, b_: "▲" if a_ > b_ else "▼" if a_ < b_ else "−"
cmp_lbl = "전주" if a.mode == "weekly" else "전일"

out = {"asof": c0["date"], "mode": a.mode, "bottom": {"score": B0["score"], "prev": B1["score"], "judge": B0["judge"], "types": B0["types"],
                                                       "parts": B0["parts"], "mult": B0["mult"], "fails": B0["fails"]}}
detail = list(B0["rows"])
doc_rows = []
_bp = B0["parts"]; _lab = {"F&G": f"F&G {fmt(B0['fg'],1)}", "VIX 기간구조": f"VIX÷3M {fmt(B0['ratio'])}", "P/C": "P/C", "신용": "신용", "breadth": "breadth"}
why_b = fit([f"{_lab[k]}({v}점)" for k, v in sorted(_bp.items(), key=lambda x: -x[1]) if v or k in ("F&G", "VIX 기간구조")])
doc_rows.append(["Bottom Score (바닥)", f"{B0['score']}/100 {arrow(B0['score'], B1['score'])}", B0["judge"], SHORT.get(B0["types"][0][0], B0["types"][0][:8]),
                 why_b, "F&G ≤10 + VIX 역전" if B0["score"] < 50 else "점수 70 돌파"])

if a.mode == "weekly":
    def mt(o, c):
        return {"y2": ust.get("y2") if o == 0 else ust.get("y2_5d"), "y10": ust.get("y10") if o == 0 else ust.get("y10_5d"), "effr": effr,
                "y2_20d_bp": bp(ust.get("y2"), ust.get("y2_20d")) if o == 0 else bp(ust.get("y2_5d"), ust.get("y2_25d")),
                "y10_20d_bp": bp(ust.get("y10"), ust.get("y10_20d")) if o == 0 else bp(ust.get("y10_5d"), ust.get("y10_25d")),
                "y10_20d_high": ust.get("y10_20d_high"),
                "fwd_pe": fs.get("fwd_pe"), "eps_4w": fs.get("eps_4w_change_pct"), "guid_neg": fs.get("guid_neg"), "guid_pos": fs.get("guid_pos"),
                "hy_now": hy.get("now") if o == 0 else hy.get("w1"), "hy_low3m": hy.get("low3m"), "hy_low3m_date": hy.get("low3m_date"),
                "hy_5d_bp": bp(hy.get("now"), hy.get("d5")),
                "str_score": D["stock_price_strength"]["score"], "breadth_score": D["stock_price_breadth"]["score"]}
    T0 = top(c0, mt(0, c0)); T1 = top(c1, mt(5, c1))
    notes.append("전주 Top Risk: FactSet·CNN 하위지표 점수는 이번 주 값 재사용")
    detail += T0["rows"]
    top_why = fit([f"{nm} {round(f*wt)}점" for nm, f, wt in sorted(T0["areas"], key=lambda x: -x[1] * x[2]) if f]) or "충족 영역 없음"
    doc_rows.append(["Top Risk Score (고점)", f"{T0['score']}/100 {arrow(T0['score'], T1['score'])}", T0["judge"], T0["regime_name"].split(" ")[0] + " " + T0["regime_name"].split(" ")[1][:2],
                     top_why, T0["cond_short"]])
    out["top"] = {"score": T0["score"], "prev": T1["score"], "judge": T0["judge"], "regime": T0["regime_name"], "prev_regime": T1["regime_name"],
                  "release": T0["release"], "price_confirm": T0["pconf"], "fails": T0["fails"]}

line = (f"F&G {fmt(B0['fg'],1)} → {B0['parts']['F&G']} · VIX÷VIX3M {fmt(B0['ratio'])} → {B0['parts']['VIX 기간구조']} · P/C → {B0['parts']['P/C']} · "
        f"신용 → {B0['parts']['신용']} · breadth → {B0['parts']['breadth']} · 게이트 ×{B0['mult']}")
# 알람 조건
v = m_now["vix"]; fg = B0["fg"]
alarm = {"vix25": bool(v and v >= 25), "vix_intraday25": bool(vix.get("high") and vix["high"] >= 25 and not (v and v >= 25)),
         "fg_extreme": bool(fg is not None and fg < 25), "score30": B0["score"] >= 30}
alarm["fire"] = alarm["vix25"] or alarm["fg_extreme"] or alarm["score30"] or alarm["vix_intraday25"]
tags = [t for k, t in [("vix25", "[VIX 25 돌파]"), ("vix_intraday25", "[VIX 장중 25 터치]"), ("fg_extreme", "[CNN 극도의 공포]"), ("score30", "[Bottom ≥30]")] if alarm[k]]
alarm["tags"] = tags
out.update({"scores_title": f"바닥{'·고점' if a.mode == 'weekly' else ''}신호 스코어 산출 내역 ({c0['date']} 종가 기준)",
            "doc_scores_title": f"바닥{'·고점' if a.mode == 'weekly' else ''}신호 스코어 ({c0['date'][5:].replace('-', '/')} 종가 기준)",
            "scores_detail": detail, "doc_scores": doc_rows, "scores_line": line[:110], "alarm": alarm,
            "scores_note": f"CNN 아카이브 {D['fear_and_greed']['timestamp']} · {cmp_lbl} 비교 기준 {c1['date']} · " + " · ".join(notes)
                           + (" · 확인 실패: " + ", ".join(B0["fails"] + (out.get('top', {}).get('fails') or [])) if B0["fails"] or out.get('top', {}).get('fails') else ""),
            "market": {"spx": c0["spx"], "ma125": c0["ma125"], "ath": c0["ath"], "dd_pct": round(c0["dd"] * 100, 2), "fg": r1(fg, 1),
                       "fg_rating": D["fear_and_greed"]["rating"], "fg_120max": c0["fg120max"], "vix": v,
                       "cnn_sub": {k: [round(D[k]["score"], 1), D[k]["rating"]] for k in ["market_momentum_sp500", "stock_price_strength", "stock_price_breadth",
                                                                                         "put_call_options", "market_volatility_vix", "junk_bond_demand", "safe_haven_demand"]}}})
json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 화면 요약
ts = D["fear_and_greed"]["timestamp"]
print(f"[기준] {c0['date']} (CNN {ts}) / {cmp_lbl} {c1['date']}")
print(f"[Bottom] {B0['score']}/100 ({cmp_lbl} {B1['score']} {arrow(B0['score'], B1['score'])}) → {B0['judge']} | 유형 {', '.join(B0['types'])} | 확인 실패 {B0['fails'] or '없음'}")
print("  " + line)
if a.mode == "weekly":
    print(f"[Top] {T0['score']}/100 (전주 {T1['score']} {arrow(T0['score'], T1['score'])}) → {T0['judge']} | {T0['regime_name']} (전주 {T1['regime_name']}) | 가격확인 {'충족' if T0['pconf'] else '미충족'}")
    for x in T0["release"]: print("  해제조건:", x)
print(f"[시장] S&P {c0['spx']:,.2f} · 125일선 {fmt(c0['ma125'])} · 고점 {c0['ath']:,.2f} 대비 {c0['dd']*100:.2f}% · F&G {fmt(fg,1)} ({D['fear_and_greed']['rating']}) · 120일 최고 {fmt(c0['fg120max'],1)}")
print("[CNN 하위]", {k: v_ for k, v_ in out["market"]["cnn_sub"].items()})
print(f"[알람] {'발송' if alarm['fire'] else '미충족'} {' '.join(tags)}")
print(f"[출력] {a.out}")
