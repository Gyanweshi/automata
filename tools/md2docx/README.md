# md2docx

Converts a vault research note (Markdown) to `.docx`. Built for the insurance comp-scan
notes: heavy GFM tables, hundreds of hyperlinks, mixed Latin/Indic scripts.

```bash
npm install docx          # once, in this directory
node md2docx.js --input path/to/note.md --output path/to/note.docx
```

Handles YAML frontmatter, `#`–`######` headings (mapped to Word built-in heading styles so
the TOC and navigation pane work), paragraphs, `**bold**`, `*italic*`, `` `code` ``,
`[text](url)`, bullet lists, blockquotes, horizontal rules and GFM tables.

Layout notes worth keeping:

- **Landscape US Letter.** docx-js swaps width/height itself for `LANDSCAPE`, so the script
  passes *portrait* dimensions (12240 x 15840 DXA). Passing pre-swapped dimensions silently
  yields portrait.
- **Column widths** are proportional to the longest cell, floored at the longest header word
  so headers never wrap mid-word, capped at 46 so a long title column cannot starve the
  numeric ones. Each column is handed its cell padding before the remainder is shared.
- **Link labels may contain brackets** (`[ MUST WATCH ]`), so the link regex tolerates one
  level of nesting. A naive `\[([^\]]*)\]` leaves raw Markdown in the output.
- `ShadingType.CLEAR` for header fill — `SOLID` renders black.

Verify output by rendering it, not by assuming:

```bash
soffice --headless --convert-to pdf note.docx && pdftoppm -jpeg -r 70 note.pdf page
```
