// 한국증시 브리핑 1페이지 워드 생성기 (데일리·위클리 공용). 사용: node kr_gen_docx.js data.json out.docx
const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, BorderStyle, LevelFormat } = require('docx');
const d = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')); const out = process.argv[3];
const doc_ = d.doc;
const F = "Malgun Gothic", S = 17, NAVY = "1F3864", RED = "C00000", BLUE = "1F4E9F", W = 10466;

const run = (t, o = {}) => new TextRun({ text: t, font: F, size: o.size || S, bold: o.bold, color: o.color, italics: o.italics });
const para = (runs, o = {}) => new Paragraph({ children: runs, spacing: { before: o.before || 0, after: o.after ?? 30, line: 245 } });
const h = (t) => new Paragraph({ children: [run("■ " + t, { bold: true, size: 19, color: NAVY })], spacing: { before: 80, after: 30 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: NAVY, space: 1 } } });
const bullet = (runs) => new Paragraph({ children: runs, numbering: { reference: "b", level: 0 }, spacing: { after: 12, line: 245 } });
const bl = ([k, v, red]) => bullet([run(k, { bold: true, color: red ? RED : undefined }), run(v)]);
const border = { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
// 한국 관행: 상승 빨강, 하락 파랑
const signColor = (t) => /^\+/.test(t) ? RED : /^-/.test(t) ? BLUE : undefined;
const krDate = (s) => { const [y, m, dd] = s.slice(0, 10).split("-").map(Number); return `${y}년 ${m}월 ${dd}일`; };
const writtenKst = d.written_kst || new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Seoul", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date());
const pct = (v) => (v > 0 ? "+" : "") + (v * 100).toFixed(2) + "%";

function table(widths, rows, center = []) {
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ children: r.map((c, j) => {
      const isH = i === 0, cell = typeof c === "string" ? { t: c } : c;
      return new TableCell({ width: { size: widths[j], type: WidthType.DXA }, borders,
        shading: isH ? { type: ShadingType.CLEAR, fill: "D9E1F2", color: "auto" } : undefined,
        margins: { top: 15, bottom: 15, left: 55, right: 55 },
        children: [new Paragraph({ alignment: (j === 0 && !center.includes(0)) ? AlignmentType.LEFT : AlignmentType.CENTER,
          spacing: { after: 0, line: 225 }, children: [run(String(cell.t ?? ""), { bold: isH || cell.bold, color: cell.color, size: 15 })] })] });
    }) })) });
}

// 지수·매크로 (4행 x 6열: 이름행/값행 반복). dir: up=빨강, dn=파랑
const macro = doc_.macro.map((r, i) => r.map(c => {
  const cell = typeof c === "string" ? { t: c } : { ...c };
  if (i % 2 === 1 && cell.dir) cell.color = cell.dir === "up" ? RED : BLUE;
  if (i % 2 === 0) cell.bold = true;
  return cell;
}));

// 업종 상승/하락 Top3
const sec = [...d.sectors].sort((a, b) => b[1] - a[1]);
const top = sec.slice(0, 3), bot = [...sec].sort((a, b) => a[1] - b[1]).slice(0, 3);
const note = (n) => (d.sector_notes || {})[n] || "";
const secRows = [["상승순위", "상위 업종", "등락", "비고", "하락순위", "하위 업종", "등락", "비고"]];
for (let i = 0; i < Math.min(3, sec.length); i++) secRows.push([{ t: String(i + 1) }, top[i][0], { t: pct(top[i][1]), color: signColor(pct(top[i][1])) }, note(top[i][0]),
  { t: String(i + 1) }, bot[i][0], { t: pct(bot[i][1]), color: signColor(pct(bot[i][1])) }, note(bot[i][0])]);
const nUp = d.sectors.filter(s => s[1] > 0).length;

const stockRows = [["기업명(종목코드)", doc_.chg_header || "등락", "원인", "시각", "근거"]].concat(doc_.stocks.map(([t, c, r, v, b, hl]) =>
  [t, { t: c, color: signColor(c) }, r, hl ? { t: v, bold: true, color: RED } : v, b]));

const children = [
  new Paragraph({ children: [run(`${krDate(d.written)} ${d.title || "한국증시 데일리 브리핑"}`, { bold: true, size: 28, color: NAVY }),
    run(`   ${d.date} ${d.basis_label || "정규장 마감 기준"} | 작성 ${d.written} ${writtenKst} (한국시각)`, { size: 15, color: "595959" })], spacing: { after: 50 } }),
  new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], rows: [new TableRow({ children: [new TableCell({
    width: { size: W, type: WidthType.DXA }, borders: { top: { style: BorderStyle.SINGLE, size: 8, color: NAVY }, bottom: border, left: border, right: border },
    shading: { type: ShadingType.CLEAR, fill: "F2F2F2", color: "auto" }, margins: { top: 50, bottom: 50, left: 100, right: 100 },
    children: [para([run("Headline  ", { bold: true, color: NAVY }), run(d.headline_bold + " ", { bold: true }), run(d.headline_rest)], { after: 0 })] })] })] }),
  h(doc_.macro_title || "지수·매크로·수급"), table([1750, 1750, 1700, 1800, 1700, 1766], macro),
  h("시장 드라이버 (증거 강도순)"), ...doc_.drivers.map(bl),
  ...(doc_.weekend ? [h(doc_.weekend_title || "주말 뉴스"), ...doc_.weekend.map(bl)] : []),
  h(doc_.sector_title || "업종 · 주요 종목"), table([850, 1700, 900, 1783, 850, 1700, 900, 1783], secRows, [0]),
  para([run(`${doc_.sector_universe || `확인된 ${d.sectors.length}개 업종`} 중 ${nUp}개 상승 → ${doc_.sector_comment}`, { size: 14, color: "595959", italics: true })], { before: 20, after: 40 }),
  table([2300, 900, 3366, 1500, 2400], stockRows),
  h(doc_.earnings_title || "실적·지표·공시"), ...doc_.earnings.map(bl),
  h(doc_.today_title || "내일 체크 & 포지셔닝"), ...doc_.today.map(bl), ...doc_.positioning.map(bl),
  para([run("Sources: " + d.sources.map(s => s[0]).join(", ") + ". " + (d.data_note || ""), { size: 12, color: "7F7F7F", italics: true })], { before: 60, after: 0 }),
];
const docx = new Document({ styles: { default: { document: { run: { font: F, size: S } } } },
  numbering: { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 280, hanging: 200 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 620, bottom: 560, left: 720, right: 720 } } }, children }] });
Packer.toBuffer(docx).then(b => { fs.writeFileSync(out, b); console.log(out); });
