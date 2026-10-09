# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 Navaneethan and E-reader Maker contributors
"""Conservative, screen-sized ebook layout helpers."""
import copy
import re
from html import escape

import pymupdf as fitz
from bs4 import BeautifulSoup

READER_CSS = '''
body { margin: 0; padding: 0; line-height: 1.45; }
p { margin: 0 0 .7em; orphans: 2; widows: 2; }
h1, h2, h3, h4, h5, h6 { text-align: left; line-height: 1.2;
  page-break-after: avoid; break-after: avoid; margin: 1.2em 0 .6em; }
h1 { font-size: 1.6em; } h2 { font-size: 1.3em; } h3 { font-size: 1.15em; }
img { max-width: 100% !important; height: auto !important; object-fit: contain; }
.reader-image { display: block; margin: .8em auto; }
figure, .reader-figure { margin: 1em 0; padding: 0; text-align: center;
  page-break-inside: avoid; break-inside: avoid; }
figure img, .reader-figure img { display: inline-block; max-height: 95vh; }
figcaption { font-size: .9em; text-align: center; margin: .4em 0 0; }
.reader-page { text-align: center; margin: 0; page-break-before: always; }
.reader-page img { max-width: 100%; max-height: 95vh; }
table { width: 100%; max-width: 100%; border-collapse: collapse;
  margin: 1em 0; font-size: .95em; text-align: left; }
.reader-table-short { page-break-inside: avoid; break-inside: avoid; }
.reader-table-group { page-break-before: always; break-before: page;
  page-break-inside: avoid; break-inside: avoid; }
th, td { border: 1px solid #888; padding: .35em; vertical-align: top;
  overflow-wrap: anywhere; word-wrap: break-word; }
th { font-weight: bold; } td p, th p { margin: 0 0 .25em; }
thead { display: table-header-group; } tr { page-break-inside: avoid; }
caption { caption-side: top; text-align: left; font-weight: bold; margin-bottom: .5em; }
td img, th img { display: inline; max-width: 100%; }
blockquote { margin: .8em 1em; } ul, ol { padding-left: 1.5em; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; font-size: .9em; }
.reader-code { margin: .8em 0; font-family: monospace; font-size: .9em; }
.reader-code-line { margin: 0; white-space: normal; text-indent: 0; }
a { overflow-wrap: break-word; }
.table-part { font-size: .9em; font-weight: bold; page-break-after: avoid; break-after: avoid; }
'''


def prepare_html(source):
    """Split simple wide/long tables with their row keys and headers repeated."""
    soup = BeautifulSoup(source, 'html.parser')
    for table in list(soup.find_all('table')):
        if table.find_parent('table'):
            continue
        rows = table.find_all('tr')
        cells = [row.find_all(['th', 'td'], recursive=False) for row in rows]
        if not cells:
            continue
        # Merged cells carry relationships: retain their structure, never guess.
        complex_table = table.find('table') or any(c.get('rowspan', '1') != '1' or c.get('colspan', '1') != '1' for row in cells for c in row)
        if complex_table:
            continue
        width = max(map(len, cells))
        if width <= 3 and len(rows) <= 35 and len(table.get_text()) < 12000:
            continue
        if len(set(map(len, cells))) != 1:
            continue
        header = rows[0] if rows[0].find('th') or rows[0].find_parent('thead') else None
        body_rows = rows[1:] if header else rows
        # Repeat the first column as the row identifier in each horizontal slice.
        column_groups = [list(range(width))] if width <= 3 else [[0] + list(range(i, min(i + 2, width))) for i in range(1, width, 2)]
        row_groups, current, chars = [], [], 0
        for row in body_rows:
            count = len(row.get_text())
            if current and (len(current) >= 30 or chars + count > 10000):
                row_groups.append(current); current, chars = [], 0
            current.append(row); chars += count
        if current:
            row_groups.append(current)
        replacement = soup.new_tag('div')
        if table.get('id'):
            replacement['id'] = table['id']
        part = 0
        for group in row_groups:
            for indices in column_groups:
                part += 1
                part_group = soup.new_tag('div')
                part_group['class'] = 'reader-table-group'
                new_table = soup.new_tag('table')
                original_caption = table.find('caption', recursive=False)
                if original_caption:
                    cap = soup.new_tag('caption')
                    cap.string = original_caption.get_text(' ', strip=True) + f' — part {part}'
                    new_table.append(cap)
                for original in ([header] if header else []) + group:
                    row = soup.new_tag('tr')
                    old_cells = original.find_all(['th', 'td'], recursive=False)
                    for index in indices:
                        cell = copy.deepcopy(old_cells[index])
                        # IDs cannot be duplicated when repeating headers/keys.
                        for node in [cell] + list(cell.find_all(True)):
                            node.attrs.pop('id', None)
                        row.append(cell)
                    if original is header:
                        head = soup.new_tag('thead'); head.append(row); new_table.append(head)
                    else:
                        new_table.append(row)
                part_group.append(new_table)
                replacement.append(part_group)
        table.replace_with(replacement)
    for table in soup.find_all('table'):
        if len(table.find_all('tr')) <= 8 and len(table.get_text()) < 2000:
            table['class'] = 'reader-table-short'
    for img in list(soup.find_all('img')):
        if img.find_parent(['figure', 'td', 'th']) or img.find_parent(class_='reader-figure'):
            continue
        # Do not wrap a figure inside a paragraph (invalid XHTML content model).
        parent = img.parent
        if parent and parent.name == 'p' and not parent.get_text(strip=True) and len(parent.find_all('img')) == 1:
            parent.name = 'figure'
        else:
            img['class'] = 'reader-image'
    return str(soup)


def joined_lines(text):
    text = re.sub(r'(?<=\w)-\n(?=[a-z])', '', text)
    return re.sub(r'\s*\n\s*', ' ', text).strip()


def pdf_page_html(page, assets, add_image, ocr, work, preserve=False):
    """Return HTML + note. Ambiguous page layouts stay visually intact."""
    def page_image(note):
        name = add_image(page.get_pixmap(dpi=160).tobytes('png'), assets)
        return f'<div class="reader-page"><img src="{name}" alt="Page {page.number + 1}"/></div>', note
    if preserve:
        return page_image('Original page layout preserved; text on these pages does not resize.')
    info = page.get_text('dict', sort=True)
    text_blocks = [b for b in info['blocks'] if b['type'] == 0]
    images = [b for b in info['blocks'] if b['type'] == 1]
    plain = page.get_text().strip()
    if len(plain) < 40:
        if not plain and not images and not page.get_drawings():
            return '', None  # Empty source pages add no artificial blank chapters.
        try:
            text = ocr(page.get_pixmap(dpi=190).tobytes('png'), work)
        except (ValueError, FileNotFoundError):
            return page_image('Scanned pages were preserved because OCR was unavailable.')
        # Keeping the page image protects illustrations, maths, and scan context.
        # OCR remains in an adjacent readable section so users can resize it.
        body, _ = page_image(None)
        if text.strip():
            paras = re.split(r'\n\s*\n', text.strip())
            body += '<h2>Text from this scan</h2>' + ''.join(f'<p>{escape(joined_lines(p))}</p>' for p in paras)
            return body, 'Scanned pages include their original image and English OCR text. Check OCR for recognition errors.'
        return body, 'No text was recognized on some scanned pages; their original appearance is preserved.'
    # Side-by-side blocks with overlapping vertical spans are likely columns.
    def columns(a, b):
        ax0, ay0, ax1, ay1 = a['bbox']; bx0, by0, bx1, by1 = b['bbox']
        overlap = min(ay1, by1) - max(ay0, by0)
        return overlap > 12 and (ax1 + 8 < bx0 or bx1 + 8 < ax0)
    try:
        tables = page.find_tables().tables
    except Exception:
        return page_image('A page with uncertain table structure was preserved to keep its layout.')
    table_rects = [fitz.Rect(t.bbox) for t in tables]
    def inside_table(b):
        rect = fitz.Rect(b['bbox'])
        return any((rect & t).get_area() > rect.get_area() * .5 for t in table_rects)
    free_text = [b for b in text_blocks if not inside_table(b)]
    if any(columns(a, b) for i, a in enumerate(free_text) for b in free_text[i + 1:]):
        return page_image('Multi-column pages were preserved to avoid scrambling their reading order.')
    drawings = page.get_drawings()
    horizontal_rules = []
    for drawing in drawings:
        for item in drawing.get('items', []):
            if item[0] != 'l':
                continue
            start, end = item[1], item[2]
            midpoint = fitz.Point((start.x + end.x) / 2, (start.y + end.y) / 2)
            if (abs(start.y - end.y) < 1 and abs(start.x - end.x) > page.rect.width * .3
                    and not any(t.contains(midpoint) for t in table_rects)):
                horizontal_rules.append(midpoint.y)
    if len(set(round(y) for y in horizontal_rules)) >= 3:
        return page_image('Pages with lightly ruled tables were preserved to keep their columns aligned.')
    def text_background(drawing):
        # Pale, rectangular paragraph/code backgrounds are decoration, not figures.
        items = drawing.get('items', [])
        fill = drawing.get('fill')
        rect = drawing['rect']
        return (len(items) == 1 and items[0][0] == 're' and fill is not None
                and min(fill) > .80 and any(rect.intersects(fitz.Rect(b['bbox'])) for b in free_text))
    # Vector illustrations outside detected tables cannot be safely flattened to text.
    if any(d['rect'].get_area() > 400 and not text_background(d) and not any(t.intersects(d['rect']) for t in table_rects) for d in drawings):
        return page_image('Pages with vector artwork were preserved to keep diagrams and labels together.')
    elements = []
    for table in tables:
        rows = table.extract()
        if not rows or any(value is None for row in rows for value in row):
            return page_image('A complex table was preserved with its original alignment.')
        head_names = table.header.names if table.header else []
        external_header = bool(table.header and table.header.external)
        if external_header:
            return page_image('A table with an external heading was preserved with its labels.')
        body = '<table>'
        for i, row in enumerate(rows):
            tag = 'th' if i == 0 and head_names else 'td'
            body += '<tr>' + ''.join(f'<{tag}>{escape(joined_lines(v or ""))}</{tag}>' for v in row) + '</tr>'
        body += '</table>'
        elements.append((table.bbox[1], table.bbox[0], body))
    font_sizes = [s['size'] for b in free_text for line in b['lines'] for s in line['spans'] if s['text'].strip()]
    normal = sorted(font_sizes)[len(font_sizes) // 2] if font_sizes else 12
    for block in free_text:
        lines = [''.join(s['text'] for s in line['spans']) for line in block['lines']]
        text = joined_lines('\n'.join(lines))
        if not text:
            continue
        spans = [s for line in block['lines'] for s in line['spans'] if s['text'].strip()]
        def is_mono(span):
            return bool(span.get('flags', 0) & 8) or any(n in span['font'].lower() for n in ('mono', 'courier', 'consolas'))
        mono_chars = sum(len(s['text']) for s in spans if is_mono(s))
        if mono_chars > sum(len(s['text']) for s in spans) * .6:
            base_x = min(line['bbox'][0] for line in block['lines'])
            char_width = max(.1, sum(s['size'] * .6 for s in spans) / len(spans))
            code_lines = []
            for line, raw in zip(block['lines'], lines):
                indent = max(0, round((line['bbox'][0] - base_x) / char_width))
                code_lines.append(' ' * indent + raw)
            if any(len(line) > 52 for line in code_lines):
                # Some EPUB engines ignore pre-wrap. Ordinary code paragraphs
                # wrap at spaces; NBSP retains indentation and repeated spaces.
                wrapped = []
                for raw in code_lines:
                    encoded = escape(raw)
                    encoded = re.sub(r' {2,}|^ +', lambda m: '&#160;' * len(m.group()), encoded)
                    wrapped.append('<p class="reader-code-line"><code>' + (encoded or '&#160;') + '</code></p>')
                body = '<div class="reader-code">' + ''.join(wrapped) + '</div>'
            else:
                body = '<pre><code>' + escape('\n'.join(code_lines)) + '</code></pre>'
            elements.append((block['bbox'][1], block['bbox'][0], body))
            continue
        size = max((s['size'] for line in block['lines'] for s in line['spans']), default=normal)
        tag = 'h2' if size >= normal * 1.25 and len(text) < 180 else 'p'
        formatted_lines = []
        for line in block['lines']:
            fragments = []
            for span in line['spans']:
                fragment = escape(span['text'])
                if span.get('flags', 0) & 16 or 'bold' in span['font'].lower():
                    fragment = '<strong>' + fragment + '</strong>'
                if span.get('flags', 0) & 2:
                    fragment = '<em>' + fragment + '</em>'
                fragments.append(fragment)
            formatted_lines.append(''.join(fragments))
        body = joined_lines('\n'.join(formatted_lines))
        elements.append((block['bbox'][1], block['bbox'][0], f'<{tag}>{body}</{tag}>'))
    for block in images:
        try:
            name = add_image(block['image'], assets)
        except Exception:
            return page_image('A page was preserved because an embedded image could not be extracted.')
        elements.append((block['bbox'][1], block['bbox'][0], f'<figure><img src="{name}" alt="Illustration on page {page.number + 1}"/></figure>'))
    elements.sort(key=lambda e: (round(e[0] / 4), e[1]))
    return ''.join(e[2] for e in elements), None
