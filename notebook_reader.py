# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 Navaneethan and E-reader Maker contributors
"""Read saved notebook data. Never import, evaluate, or execute input code."""
import base64
import io
import json
import math
import re
import tokenize
import zipfile
from html import escape
from pathlib import PurePosixPath

import markdown
from bs4 import BeautifulSoup

MAX_NOTEBOOK = 40 * 1024 * 1024
MAX_CELLS = 10000
OUTPUT_LINES = 10
OUTPUT_WIDTH = 80


def text(value):
    if isinstance(value, list):
        return ''.join(v for v in value if isinstance(v, str))
    return value if isinstance(value, str) else ''


def xml_text(value):
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]', '', value)


def code_html(source, kind='reader-code'):
    # Individual paragraphs wrap on small readers, without pre's fixed-width
    # overflow. Nonbreaking spaces preserve indentation and repeated spaces.
    lines = []
    for line in xml_text(source).expandtabs(4).split('\n'):
        # Some EPUB engines ignore overflow-wrap for long identifiers. Invisible
        # break opportunities prevent clipping without inserting visible hyphens.
        line = re.sub(r'\S{25,}', lambda m: '\u200b'.join(m.group()[i:i + 20] for i in range(0, len(m.group()), 20)), line)
        encoded = escape(line)
        encoded = re.sub(r' {2,}|^ +', lambda m: '&#160;' * len(m.group()), encoded)
        lines.append('<p class="reader-code-line"><code>' + (encoded or '&#160;') + '</code></p>')
    return f'<div class="{kind}">' + ''.join(lines) + '</div>'


def html_lines(value):
    soup = BeautifulSoup(value, 'html.parser')
    for node in soup(['script', 'style', 'iframe', 'object', 'svg']):
        node.decompose()
    for row in soup.find_all('tr'):
        row.replace_with('\n' + ' | '.join(c.get_text(' ', strip=True) for c in row.find_all(['th', 'td'])) + '\n')
    return soup.get_text('\n', strip=True).splitlines()


def dbc_outputs(result, depth=0):
    if not isinstance(result, dict) or depth > 8:
        return
    kind, data = result.get('type'), result.get('data')
    if kind == 'listResults' and isinstance(data, list):
        for item in data:
            yield from dbc_outputs(item, depth + 1)
    elif kind == 'table' and isinstance(data, list):
        schema = result.get('schema', [])
        if isinstance(schema, list) and schema:
            yield ' | '.join(str(c.get('name', '')) for c in schema if isinstance(c, dict))
        for row in data:
            if isinstance(row, list):
                yield ' | '.join(json.dumps(c, ensure_ascii=False) if isinstance(c, (dict, list)) else str(c) for c in row)
        if result.get('overflow'):
            yield '[More rows were not saved in this export.]'
    elif kind in {'html', 'htmlSandbox'}:
        yield from html_lines(text(data))
    elif kind in {'text', 'error'}:
        yield from text(data).splitlines()
    elif data:
        yield '[Interactive or unsupported saved output omitted.]'


def jupyter_outputs(outputs, assets, add_image, plots):
    for output in outputs:
        if not isinstance(output, dict):
            continue
        kind = output.get('output_type')
        if kind == 'stream':
            yield from text(output.get('text')).splitlines()
        elif kind == 'error':
            yield from (text(output.get('ename')) + ': ' + text(output.get('evalue'))).splitlines()
            for line in output.get('traceback', []):
                yield from text(line).splitlines()
        elif kind in {'display_data', 'execute_result', 'update_display_data'}:
            data = output.get('data', {})
            if not isinstance(data, dict):
                continue
            mime = next((m for m in ('image/png', 'image/jpeg') if m in data), None)
            if mime and len(plots) < 1:
                try:
                    encoded = text(data[mime])
                    if len(encoded) > 12 * 1024 * 1024:
                        raise ValueError('Plot too large')
                    plots.append(add_image(base64.b64decode(encoded, validate=True), assets))
                except Exception:
                    yield '[Saved plot could not be imported.]'
            elif 'text/plain' in data:
                yield from text(data['text/plain']).splitlines()
            elif 'text/html' in data:
                yield from html_lines(text(data['text/html']))
            elif data:
                yield '[Interactive or unsupported saved output omitted.]'


def output_html(lines, plots):
    preview, shortened = [], False
    for line in lines:
        # Strip terminal escape sequences, not code. One budget shared by all
        # outputs of this cell; wide table rows cannot flood the preview.
        line = re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))', '', str(line))
        line = xml_text(line).expandtabs(4)
        if len(preview) == OUTPUT_LINES:
            shortened = True
            break
        if len(line) > OUTPUT_WIDTH:
            line = line[:OUTPUT_WIDTH - 1] + '…'
            shortened = True
        preview.append(line)
    result = ''
    if preview:
        result = '<h4>Saved output</h4>' + code_html('\n'.join(preview), 'reader-code reader-output')
    if shortened:
        result += '<p class="output-note"><em>Output preview shortened. Up to 10 lines; long rows are clipped.</em></p>'
    for name in plots:
        result += f'<figure><img src="{escape(name)}" alt="Saved notebook plot"/></figure>'
    return result


def source_cells(source):
    """Decode Databricks SOURCE comments only when its header is present."""
    if not source.startswith('# Databricks notebook source'):
        return [{'cell_type': 'code', 'source': source}]
    cells = []
    for chunk in re.split(r'^# COMMAND -+\s*$', source, flags=re.M):
        lines = chunk.splitlines()
        label = ''
        decoded = []
        for line in lines:
            if line == '# Databricks notebook source':
                continue
            if line.startswith('# DBTITLE '):
                label = line.partition(',')[2]
                continue
            decoded.append(re.sub(r'^# MAGIC(?: |$)', '', line))
        content = '\n'.join(decoded).strip('\n')
        # Databricks may put environment comments before the first %md cell.
        magic = re.search(r'^%md(?:\s|$)', content, re.M)
        if magic and all(not l.strip() or l.startswith('#') for l in content[:magic.start()].splitlines()):
            cells.append({'cell_type': 'markdown', 'source': content[magic.end():].lstrip('\n'), 'label': label})
        elif content.strip():
            cells.append({'cell_type': 'code', 'source': content, 'label': label})
    return cells


def load_notebooks(source, title):
    if source.stat().st_size > MAX_NOTEBOOK:
        raise ValueError('Please split notebooks or code files larger than 40 MB.')
    if source.suffix.lower() == '.py':
        # Honors Python's encoding cookie, without importing the file.
        raw = source.read_bytes()
        encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
        return [(title, source_cells(raw.decode(encoding)))]
    if source.suffix.lower() == '.ipynb':
        doc = json.loads(source.read_text(encoding='utf-8-sig'))
        if not isinstance(doc, dict) or doc.get('nbformat') != 4 or not isinstance(doc.get('cells'), list):
            raise ValueError('Use a Jupyter notebook saved in version 4 format (.ipynb).')
        return [(title, doc['cells'])]
    notebooks = []
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        if len(entries) > 15000 or sum(e.file_size for e in entries) > 500 * 1024 * 1024:
            raise ValueError('This archive expands beyond the 500 MB safety limit.')
        for entry in sorted(entries, key=lambda e: e.filename):
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in entry.filename:
                raise ValueError('The DBC archive contains an unsafe entry name.')
            if entry.flag_bits & 1:
                raise ValueError('Password-protected archives cannot be converted.')
            if entry.is_dir() or entry.filename.startswith('__MACOSX/') or path.name.startswith('.'):
                continue
            if path.suffix.lower() not in {'.python', '.scala', '.sql', '.r', '.ipynb'}:
                continue
            if entry.file_size > MAX_NOTEBOOK:
                raise ValueError('A notebook in this DBC archive exceeds 40 MB. Export smaller notebooks.')
            doc = json.loads(archive.read(entry))
            if not isinstance(doc, dict) or not isinstance(doc.get('commands'), list):
                raise ValueError('Unsupported DBC notebook structure. Export it as Jupyter (.ipynb) instead.')
            commands = doc['commands']
            if not all(isinstance(c, dict) for c in commands):
                raise ValueError('This DBC contains a malformed command.')
            def position(c):
                value = c.get('position')
                return value if isinstance(value, (int, float)) and math.isfinite(value) else 0
            cells = []
            for cmd in sorted(commands, key=position):
                content = text(cmd.get('command'))
                match = re.match(r'^%md(?:\s|$)', content)
                cells.append({'cell_type': 'markdown' if match else 'code',
                              'source': content[match.end():] if match else content,
                              'label': text(cmd.get('commandTitle')),
                              'dbc_result': cmd.get('results')})
            notebooks.append((text(doc.get('name')) or path.stem, cells))
    if not notebooks:
        raise ValueError('No supported Databricks notebooks found. Export as Jupyter (.ipynb) or Python SOURCE instead.')
    return notebooks


def notebook_chapters(source, title, assets, clean_html, add_image):
    notebooks = load_notebooks(source, title)
    if sum(len(cells) for _, cells in notebooks) > MAX_CELLS:
        raise ValueError('Please split exports containing more than 10,000 cells.')
    chapters = []
    for name, cells in notebooks:
        label, body = name, []
        for index, cell in enumerate(cells, 1):
            if not isinstance(cell, dict):
                raise ValueError('This notebook contains a malformed cell.')
            content = xml_text(text(cell.get('source')))
            kind = cell.get('cell_type')
            if kind == 'markdown':
                html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
                # Inline Jupyter attachments are safe to pass to the existing
                # embedded-image importer; local paths and URLs stay blocked.
                soup = BeautifulSoup(html, 'html.parser')
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    if src.startswith('attachment:'):
                        attachment = cell.get('attachments', {}).get(src[11:], {})
                        mime = next((m for m in ('image/png', 'image/jpeg') if m in attachment), None)
                        if mime:
                            img['src'] = 'data:' + mime + ';base64,' + text(attachment[mime])
                heading = soup.find(re.compile('^h[1-3]$'))
                if heading:
                    if body:
                        chapters.append((label, ''.join(body)))
                    label, body = heading.get_text(' ', strip=True)[:160] or name, []
                body.append(clean_html(str(soup), assets))
            elif kind in {'code', 'raw'}:
                if content.strip():
                    cell_label = text(cell.get('label')) or f'Code {index}'
                    body.append(f'<h3>{escape(xml_text(cell_label))}</h3>' + code_html(content))
                plots = []
                lines = dbc_outputs(cell['dbc_result']) if 'dbc_result' in cell else jupyter_outputs(cell.get('outputs', []), assets, add_image, plots)
                body.append(output_html(lines, plots))
            else:
                raise ValueError('Unsupported notebook cell type. Save a standard Jupyter v4 notebook.')
        if body and any(body):
            chapters.append((xml_text(label), ''.join(body)))
    return chapters
