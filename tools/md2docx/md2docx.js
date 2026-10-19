// Markdown -> .docx for the insurance scan notes.
// Handles: YAML frontmatter, #/##/### headings, paragraphs, **bold**, *italic*,
// `code`, [text](url), bullet lists, blockquotes, horizontal rules, and GFM tables.
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, ExternalHyperlink, HeadingLevel,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  AlignmentType, PageOrientation, LevelFormat, TableLayoutType,
} = require('docx');

const arg = (f, d) => { const i = process.argv.indexOf(f); return i > -1 ? process.argv[i + 1] : d; };
const INPUT = arg('--input'), OUTPUT = arg('--output');

// Landscape US Letter, 0.5" margins -> usable width in DXA
// docx-js swaps width/height itself for LANDSCAPE, so give it PORTRAIT dimensions.
const PAGE_W = 12240, PAGE_H = 15840, MARGIN = 720;      // US Letter portrait, 0.5in margins
const USABLE = PAGE_H - MARGIN * 2;                      // landscape width = portrait height

const MONO = 'Consolas';
const BODY_PT = 20;   // half-points => 10pt
const TBL_PT = 15;    // 7.5pt for dense tables

// ---------------------------------------------------------------- inline parsing
function inline(text, opts = {}) {
  const sz = opts.size || BODY_PT;
  const base = { size: sz, bold: opts.bold || false, italics: opts.italics || false };
  const runs = [];
  // split on links first so their label can itself be styled
  const re = /\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\(([^)]+)\)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) runs.push(...styled(text.slice(last, m.index), base));
    const label = m[1] || m[2];
    runs.push(new ExternalHyperlink({
      link: m[2],
      children: styled(label, { ...base, style: 'Hyperlink' }),
    }));
    last = m.index + m[0].length;
  }
  if (last < text.length) runs.push(...styled(text.slice(last), base));
  return runs.length ? runs : [new TextRun({ text: '', size: sz })];
}

// **bold**, *italic*, `code`
function styled(text, base) {
  const out = [];
  const re = /(\*\*([^*]+)\*\*|`([^`]+)`|\*([^*]+)\*)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ ...base, text: clean(text.slice(last, m.index)) }));
    if (m[2] !== undefined) out.push(new TextRun({ ...base, text: clean(m[2]), bold: true }));
    else if (m[3] !== undefined) out.push(new TextRun({ ...base, text: m[3], font: MONO, size: base.size - 1 }));
    else out.push(new TextRun({ ...base, text: clean(m[4]), italics: true }));
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(new TextRun({ ...base, text: clean(text.slice(last)) }));
  return out;
}
const clean = (s) => s.replace(/\\([*_`[\]])/g, '$1');

// ---------------------------------------------------------------- tables
function buildTable(rows) {
  const header = rows[0];
  const n = header.length;
  // proportional widths from the longest cell per column, clamped so no column starves
  const plain = (t) => (t || '')
    .replace(/\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\([^)]+\)/g, '$1')
    .replace(/[*`]/g, '');
  const weights = header.map((h, c) => {
    const longest = Math.max(...rows.map(r => plain(r[c]).length));
    const headWord = Math.max(...plain(h).split(/\s+/).map(w => w.length), 4);
    // never narrower than the longest word in the header, or it wraps mid-word
    // cap the widest (title) column so short numeric columns keep their values on one line
    return Math.min(Math.max(longest, headWord + 2, 9), 46);
  });
  const total = weights.reduce((a, b) => a + b, 0);
  // cell padding is not available to text, so hand each column its padding first and
  // share only the remainder proportionally — otherwise narrow headers wrap mid-word
  const PAD = 190;
  const share = Math.max(USABLE - PAD * n, USABLE * 0.4);
  let widths = weights.map(w => PAD + Math.floor(share * w / total));
  // make the widths sum exactly to USABLE (docx requires columnWidths to match)
  widths[n - 1] += USABLE - widths.reduce((a, b) => a + b, 0);

  const mkCell = (txt, c, isHead) => new TableCell({
    width: { size: widths[c], type: WidthType.DXA },
    shading: isHead ? { type: ShadingType.CLEAR, fill: 'E8E8E8' } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({
      spacing: { before: 0, after: 0 },
      children: inline(txt || '', { size: TBL_PT, bold: isHead }),
    })],
  });

  return new Table({
    columnWidths: widths,
    width: { size: USABLE, type: WidthType.DXA },
    layout: TableLayoutType.FIXED,
    borders: ['top', 'bottom', 'left', 'right', 'insideHorizontal', 'insideVertical']
      .reduce((o, k) => (o[k] = { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' }, o), {}),
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0,
      children: Array.from({ length: n }, (_, c) => mkCell(r[c], c, i === 0)),
    })),
  });
}

const splitRow = (line) => line.replace(/^\||\|$/g, '').split('|').map(s => s.trim());
const isSep = (line) => /^\|?[\s:-]*-{2,}[\s:|:-]*\|?$/.test(line) && line.includes('-');

// ---------------------------------------------------------------- document build
function convert(md) {
  const lines = md.split('\n');
  const kids = [];
  let i = 0;

  // YAML frontmatter -> compact metadata block
  if (lines[0].trim() === '---') {
    const end = lines.indexOf('---', 1);
    if (end > 0) {
      const meta = lines.slice(1, end).filter(l => l.trim());
      kids.push(new Paragraph({
        spacing: { after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '999999' } },
        children: meta.flatMap((l, k) => [
          ...(k ? [new TextRun({ text: '   ·   ', size: 16, color: '888888' })] : []),
          new TextRun({ text: l.trim(), size: 16, italics: true, color: '555555' }),
        ]),
      }));
      i = end + 1;
    }
  }

  const flushPara = (buf) => {
    if (!buf.length) return;
    kids.push(new Paragraph({
      spacing: { after: 120, line: 276 },
      children: inline(buf.join(' ')),
    }));
    buf.length = 0;
  };

  let buf = [];
  for (; i < lines.length; i++) {
    const raw = lines[i];
    const line = raw.trim();

    if (!line) { flushPara(buf); continue; }

    // table
    if (line.startsWith('|') && i + 1 < lines.length && isSep(lines[i + 1].trim())) {
      flushPara(buf);
      const rows = [splitRow(line)];
      i += 2;
      while (i < lines.length && lines[i].trim().startsWith('|')) rows.push(splitRow(lines[i++].trim()));
      i--;
      kids.push(buildTable(rows));
      kids.push(new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: '', size: 8 })] }));
      continue;
    }

    // headings
    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      flushPara(buf);
      const lvl = h[1].length;
      const map = { 1: HeadingLevel.TITLE, 2: HeadingLevel.HEADING_1, 3: HeadingLevel.HEADING_2,
                    4: HeadingLevel.HEADING_3, 5: HeadingLevel.HEADING_4, 6: HeadingLevel.HEADING_5 };
      kids.push(new Paragraph({
        heading: map[lvl],
        spacing: { before: lvl <= 2 ? 320 : 240, after: 120 },
        pageBreakBefore: lvl === 2 && kids.length > 2,
        children: inline(h[2], { size: lvl === 1 ? 40 : lvl === 2 ? 30 : 24, bold: true }),
      }));
      continue;
    }

    // horizontal rule
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(line)) {
      flushPara(buf);
      kids.push(new Paragraph({
        spacing: { before: 120, after: 120 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: 'CCCCCC' } },
        children: [new TextRun({ text: '', size: 2 })],
      }));
      continue;
    }

    // blockquote
    if (line.startsWith('>')) {
      flushPara(buf);
      kids.push(new Paragraph({
        indent: { left: 360 },
        spacing: { after: 120 },
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: '999999', space: 8 } },
        children: inline(line.replace(/^>\s?/, ''), { italics: true }),
      }));
      continue;
    }

    // bullet
    const b = line.match(/^[-*]\s+(.*)$/);
    if (b) {
      flushPara(buf);
      kids.push(new Paragraph({
        numbering: { reference: 'bullets', level: Math.floor((raw.length - raw.trimStart().length) / 2) },
        spacing: { after: 80, line: 276 },
        children: inline(b[1]),
      }));
      continue;
    }

    buf.push(line);
  }
  flushPara(buf);
  return kids;
}

const md = fs.readFileSync(INPUT, 'utf8');
const doc = new Document({
  numbering: {
    config: [{
      reference: 'bullets',
      levels: [0, 1, 2].map(l => ({
        level: l, format: LevelFormat.BULLET, text: ['•', '◦', '▪'][l],
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 360 * (l + 1), hanging: 240 } } },
      })),
    }],
  },
  styles: {
    default: { document: { run: { font: 'Calibri', size: BODY_PT } } },
    paragraphStyles: [{
      id: 'Hyperlink', name: 'Hyperlink',
      run: { color: '0B5FA5', underline: {} },
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H, orientation: PageOrientation.LANDSCAPE },
        margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN },
      },
    },
    children: convert(md),
  }],
});

Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUTPUT, b); console.log('wrote', OUTPUT, b.length, 'bytes'); });
