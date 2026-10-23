// 미국증시 브리핑 1페이지 워드 생성기 v2 (데일리·위클리 공용). 사용: node gen_docx.js data.json out.docx
// v2: data.json의 "scores_from"(score.py 출력 경로)이 있으면 스코어 표·한 줄을 자동 병합. doc.sources_n(기본 6)으로 Sources 표기 개수 조정.
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, BorderStyle, LevelFormat } = require('docx');
const d = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')); const out = process.argv[3];
const doc_ = d.doc;
if (d.scores_from) {
  const p = path.isAbsolute(d.scores_from) ? d.scores_from : path.resolve(path.dirname(process.argv[2]), d.scores_from);
  const s = JSON.parse(fs.readFileSync(fs.existsSync(p) ? p : d.scores_from, 'utf8'));
  if (!doc_.scores) doc_.scores = s.doc_scores;
  if (!doc_.scores_title) doc_.scores_title = s.doc_scores_title;
  if (doc_.scores_line === undefined && s.scores_line) doc_.scores_line = s.scores_line;
}
const SRC_N = doc_.sources_n || 6;
const F = "Malgun Gothic", S = 18, NAVY = "1F3864", RED = "C00000", BLUE = "1F4E9F", W = 10466;

const run = (t, o = {}) => new TextRun({ text: t, font: F, size: o.size || S, bold: o.bold, color: o.color, italics: o.italics });
const para = (runs, o = {}) => new Paragraph({ children: runs, spacing: { before: o.before || 0, after: o.after ?? 30, line: 250 } });
const h = (t) => new Paragraph({ children: [run("■ " + t, { bold: true, size: 19, color: NAVY })], spacing: { before: 70, after: 25 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: NAVY, space: 1 } } });
const bullet = (runs) => new Paragraph({ children: runs, numbering: { reference: "b", level: 0 }, spacing: { after: 15, line: 250 } });
const bl = ([k, v, red]) => bullet([run(k, { bold: true, color: red ? RED : undefined }), run(v)]);
const border = { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
const signColor = (t) => /^\+/.test(t) ? RED : /^-/.test(t) ? BLUE : undefined;
const krDate = (s) => { const [y, m, dd] = s.slice(0, 10).split("-").map(Number); return `${y}년 ${m}월 ${dd}일`; };
const writtenKst = d.written_kst || new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Seoul", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date());
const pct = (v) => (v > 0 ? "+" : "") + (v * 100).toFixed(2) + "%";

function table(widths, rows, center = []) {
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ children: r.map((c, j) => {
      const isH = i === 0, cell = typeof c === "string" ? { t: c } : c;
      return new TableCell({ width: { size: widths[j], type: WidthType.DXA }, borders,
        shading: isH ? { type: ShadingType.CLEAR, fill: "D9E1F2", color: "auto" } : (cell.fill ? { type: ShadingType.CLEAR, fill: cell.fill, color: "auto" } : undefined),
        margins: { top: 20, bottom: 20, left: 60, right: 60 },
        children: [new Paragraph({ alignment: (j === 0 && !center.includes(0)) ? AlignmentType.LEFT : AlignmentType.CENTER,
          spacing: { after: 0, line: 230 }, children: [run(String(cell.t ?? ""), { bold: isH || cell.bold, color: cell.color, size: 16 })] })] });
    }) })) });
}

const macro = doc_.macro.map((r, i) => r.map(c => {
  const cell = typeof c === "string" ? { t: c } : c;
  if (i % 2 === 1 && cell.dir) cell.color = cell.dir === "up" ? RED : BLUE;
  if (i % 2 === 0) cell.bold = true;
  return cell;
}));

// 바닥·고점 신호 스코어 (doc.scores: [구분, 점수, 판정, 국면/유형, 핵심 근거, 전환 조건])
const judgeCell = (t) => /매수|축소|방어/.test(t) ? { t, bold: true, color: RED, fill: "FDECEA" } : /경계|관찰/.test(t) ? { t, bold: true, fill: "FFF4E5" } : { t };
const scoreRows = doc_.scores ? [["구분", "점수", "판정", "국면/유형", "핵심 근거 (증거 강도순)", "전환 조건"]].concat(
  doc_.scores.map(([k, s, j, r, why, cond]) => [{ t: k, bold: true }, { t: s, bold: true }, judgeCell(j), r, why, cond])) : null;

const sec = [...d.sectors].sort((a, b) => b[1] - a[1]);
const top = sec.slice(0, 3), bot = [...sec].sort((a, b) => a[1] - b[1]).slice(0, 3);
const ab = (n) => n.replace("Consumer Discretionary", "Cons. Discretionary").replace("Communication Services", "Comm. Services");
const note = (n) => (d.sector_notes || {})[n] || "";
const secRows = [["상승순위", "상위 섹터", "등락", "비고", "하락순위", "하위 섹터", "등락", "비고"]];
for (let i = 0; i < 3; i++) secRows.push([{ t: String(i + 1) }, ab(top[i][0]), { t: pct(top[i][1]), color: signColor(pct(top[i][1])) }, note(top[i][0]),
  { t: String(i + 1) }, ab(bot[i][0]), { t: pct(bot[i][1]), color: signColor(pct(bot[i][1])) }, note(bot[i][0])]);
const nUp = d.sectors.filter(s => s[1] > 0).length;

const stockRows = [["기업명(티커)", doc_.chg_header || "등락", "원인", "시각", "근거"]].concat(doc_.stocks.map(([t, c, r, v, b, hl]) =>
  [t, { t: c, color: signColor(c) }, r, hl ? { t: v, bold: true, color: RED } : v, b]));

const children = [
  new Paragraph({ children: [run(`${krDate(d.written)} ${d.title || "미국증시 데일리 브리핑"}`, { bold: true, size: 28, color: NAVY }),
    run(`   ${d.date} ${d.basis_label || "정규장 마감 기준"} | 작성 ${d.written} ${writtenKst} (한국시각)`, { size: 16, color: "595959" })], spacing: { after: 60 } }),
  new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], rows: [new TableRow({ children: [new TableCell({
    width: { size: W, type: WidthType.DXA }, borders: { top: { style: BorderStyle.SINGLE, size: 8, color: NAVY }, bottom: border, left: border, right: border },
    shading: { type: ShadingType.CLEAR, fill: "F2F2F2", color: "auto" }, margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [para([run("Headline  ", { bold: true, color: NAVY }), run(d.headline_bold + " ", { bold: true }), run(d.headline_rest)], { after: 0 })] })] })] }),
  ...(scoreRows ? [h(doc_.scores_title || "바닥·고점 신호 스코어"), table([1800, 900, 1250, 1200, 3166, 2150], scoreRows)] : []),
  ...(doc_.scores_line ? [para([run(doc_.scores_line, { size: 15, color: "595959", italics: true })], { before: 20, after: 20 })] : []),
  h("지수·매크로"), table([2110, 1680, 1660, 1660, 1660, 1696], macro),
  h("시장 드라이버 (증거 강도순)"), ...doc_.drivers.map(bl),
  ...(doc_.weekend ? [h(doc_.weekend_title || "주말 뉴스"), ...doc_.weekend.map(bl)] : []),
  h("섹터 · 주요 종목"), table([900, 1850, 950, 1533, 900, 1850, 950, 1533], secRows, [0]),
  para([run(`${d.sectors.length}개 섹터 중 ${nUp}개 상승 → ${doc_.sector_comment}`, { size: 15, color: "595959", italics: true })], { before: 20, after: 50 }),
  table([2450, 950, 3266, 1500, 2300], stockRows),
  h(doc_.earnings_title || "실적 (주가 반응)"), ...doc_.earnings.map(bl),
  h(doc_.today_title || "오늘 체크 & 포지셔닝"), ...doc_.today.map(bl), ...doc_.positioning.map(bl),
  para([run("Sources: " + d.sources.slice(0, SRC_N).map(s => s[0]).join(", ") + (d.sources.length > SRC_N ? ` 외 ${d.sources.length - SRC_N}건(엑셀 Sources 시트)` : "") + ". " + (d.data_note || ""), { size: 13, color: "7F7F7F", italics: true })], { before: 60, after: 0 }),
];
const docx = new Document({ styles: { default: { document: { run: { font: F, size: S } } } },
  numbering: { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 280, hanging: 200 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 560, bottom: 480, left: 720, right: 720 } } }, children }] });
Packer.toBuffer(docx).then(b => { fs.writeFileSync(out, b); console.log(out); });
