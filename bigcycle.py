# 빅사이클 바닥 판단 (신규 2트랙). 사용: python3 -I kit/bigcycle.py fg/cnn.json kit/bigcycle_inputs.json kit/scores_out.json kit/scores_merged.json
import json, sys, datetime as dt

cnn_p, inp_p, cur_p, out_p = sys.argv[1:5]
D = json.load(open(cnn_p)); I = json.load(open(inp_p)); S = json.load(open(cur_p))


def ser(k):
    o = {}
    for p in D[k]["data"]:
        o[dt.datetime.fromtimestamp(p["x"] / 1000, dt.timezone.utc).date().isoformat()] = p["y"]
    return o


spx = ser("market_momentum_sp500"); vx = ser("market_volatility_vix")
asof = I.get("asof") or max(spx)
days = [d for d in sorted(spx) if d <= asof]; C = [spx[d] for d in days]; n = len(C) - 1
dd52 = C[n] / max(C[max(0, n - 251):]) - 1
dd6 = min(C[i] / max(C[max(0, i - 251):i + 1]) - 1 for i in range(max(0, n - 125), n + 1))
vv = [vx[d] for d in days[-20:] if d in vx]; vmax = max(vv) if vv else None

hy = I.get("hy_oas") or {}; hn, hm = hy.get("now"), hy.get("max6m")
nar = None if hn is None or hm is None else (hm - hn) * 100
cf = I.get("cfnai_ma3") or []; cf_now = cf[-1] if cf else None; cf_min = min(cf) if cf else None
g10 = I.get("gs10") or []; r_drop = (max(g10) - g10[-1]) * 100 if g10 else None
fails = [k for k, v in [("VIX", vmax), ("HY OAS", nar), ("CFNAI", cf_now), ("10Y 월평균", r_drop)] if v is None]

a1 = dd52 <= -0.15; a2 = vmax is not None and vmax >= 35; af = cf_now is not None and cf_now > -0.70
b1 = dd6 <= -0.20; b2 = nar is not None and nar >= 50
b3e = cf_min is not None and cf_min <= -0.70 and cf_now >= cf_min + 0.50
b3r = r_drop is not None and r_drop >= 40 and cf_min is not None and cf_min > -0.70
b3 = b3e or b3r
A = a1 and a2 and af; B = b1 and b2 and b3; recess = b1 and cf_now is not None and cf_now <= -0.70

if B: judge, track, cond = "빅사이클 바닥: 비중 확대", "B 사이클형" + ("(경기)" if b3e else "(금리)"), "신용 재확대 +50bp 시 해제"
elif A: judge, track, cond = "이벤트 바닥: 1차 분할매수", "A 이벤트형", "CFNAI ≤-0.7 시 무효"
elif recess: judge, track, cond = "침체형 하락 진행: 매수 보류", "B 대기", "신용·경기 정점 통과"
elif dd52 <= -0.10: judge, track, cond = "관찰", "게이트 통과", "고점-15%+VIX≥35"
else: judge, track, cond = "대상 아님", "평상", "52주 고점 -10%"
if len(fails) >= 2: judge = "(제한적 판단) " + judge

pa = sum([a1, a2]); pb = sum([b1, b2, b3])
score_txt = f"A{pa}·B{pb}"
why = f"고점{dd52*100:.1f}%·VIX{vmax:.0f}" if vmax is not None else f"고점{dd52*100:.1f}%"
if cf_now is not None: why += f"·CFNAI{cf_now:+.2f}"
yn = lambda x: "충족" if x else "미충족"
f2 = lambda x, s="": "확인 실패" if x is None else f"{x:.0f}{s}"
detail = [
    ["빅사이클(신규)", "게이트: 52주 고점 대비", f"{dd52*100:.2f}%", "≤ -10%", None, yn(dd52 <= -0.10)],
    ["빅사이클(신규)", "A1 가격 (52주 고점 대비)", f"{dd52*100:.2f}%", "≤ -15%", int(a1), yn(a1)],
    ["빅사이클(신규)", "A2 공포 (VIX 20일 최고)", "확인 실패" if vmax is None else f"{vmax:.2f}", "≥ 35", int(a2), yn(a2)],
    ["빅사이클(신규)", "A 필터: 침체 아님 (CFNAI-MA3)", "확인 실패" if cf_now is None else f"{cf_now:+.2f} ({I.get('cfnai_month','')})", "> -0.70", None, yn(af)],
    ["빅사이클(신규)", "B1 6개월 내 최대 하락", f"{dd6*100:.2f}%", "≤ -20%", int(b1), yn(b1)],
    ["빅사이클(신규)", "B2 신용 정점 통과 (HY 6M 최고−현재)", f2(nar, "bp") + (f" (현재 {hn}% / 최고 {hm}%)" if nar is not None else ""), "≥ 50bp", int(b2), yn(b2)],
    ["빅사이클(신규)", "B3 경기 저점 또는 금리 정점 통과",
     f"CFNAI 6M 최저 {'확인 실패' if cf_min is None else f'{cf_min:+.2f}'} · 10Y 6M 최고 대비 {f2(r_drop, 'bp')} ({I.get('gs10_month','')})",
     "경기: 최저≤-0.7 & +0.5 회복 / 금리: −40bp & 비침체", int(b3), "경기 " + yn(b3e) + " · 금리 " + yn(b3r)],
    ["빅사이클(신규)", "판정", f"A {pa}/2 · B {pb}/3", "B → A → 침체 진행 → 관찰 → 대상 아님", None, judge],
]
cur = [[("Bottom (현행)" if r[0].startswith("Bottom Score") else r[0])] + list(r[1:]) for r in (S.get("doc_scores") or [])]
S["doc_scores"] = cur + [["빅사이클 (신규)", score_txt, judge, track, why[:26], cond]]
S["scores_detail"] = (S.get("scores_detail") or []) + detail
S["scores_line"] = (S.get("scores_line") or "") + f" | 신규 2트랙: {judge} ({score_txt})"
S["bigcycle"] = {"judge": judge, "track": track, "score": score_txt, "dd52": dd52, "dd6": dd6, "vix20max": vmax,
                 "hy_narrow_bp": nar, "cfnai_now": cf_now, "cfnai_min6": cf_min, "gs10_drop_bp": r_drop,
                 "flags": {"a1": a1, "a2": a2, "a_filter": af, "b1": b1, "b2": b2, "b3_econ": b3e, "b3_rate": b3r}, "fails": fails}
json.dump(S, open(out_p, "w"), ensure_ascii=False, indent=1)
print(f"[빅사이클 신규 2트랙] {judge} | {score_txt} | {track} | {why} | 전환: {cond}" + (f" | 확인 실패: {', '.join(fails)}" if fails else ""))
