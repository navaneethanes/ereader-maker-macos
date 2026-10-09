#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Exercise a moved app with a fresh downloaded runtime and no development venv."""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree
import zipfile

root = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='ereader-install-') as work:
    work = Path(work)
    app = work / 'A different folder' / 'EreaderMaker.app'
    shutil.copytree(root / 'EreaderMaker.app', app)
    engine = app / 'Contents/Resources/Engine'
    support = work / 'Application Support'
    subprocess.run(['/bin/zsh', str(engine / 'runtime-bootstrap.sh'), str(support)], check=True, timeout=900)
    candidates = list(support.glob('runtime-v1-*/python/bin/python3'))
    assert len(candidates) == 1
    python = candidates[0]
    source = work / 'SQL_notes_and_examples.txt'
    source.write_text('Original sample chapter. Every word must remain available.')
    notebook = work / 'Saved_code.ipynb'
    notebook.write_text(json.dumps({'nbformat': 4, 'cells': [{'cell_type': 'code', 'source': 'print(123)', 'outputs': [{'output_type': 'stream', 'text': ''.join(f'row {i}\n' for i in range(30))}]}]}))
    manifest = work / 'batch.json'
    manifest.write_text(json.dumps([{'id':'sample','path':str(source)}, {'id':'notebook','path':str(notebook)}]))
    env = dict(os.environ, PATH='/usr/bin:/bin', EREADER_COVER_RENDERER=str(app / 'Contents/Helpers/cover-render'), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None); env.pop('PYTHONHOME', None)
    result = subprocess.run([str(python), str(engine / 'native_worker.py'), '--manifest', str(manifest), '--destination', str(work / 'Books')], env=env, cwd=work, capture_output=True, text=True, timeout=120, check=True)
    events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    failures = [event for event in events if event['event'] in {'error','fatal'}]
    assert not failures, failures
    book = Path(next(event['path'] for event in events if event['event'] == 'done'))
    assert book.name == 'SQL Notes and Examples.epub'
    with zipfile.ZipFile(book) as z:
        package = ElementTree.fromstring(z.read('OEBPS/content.opf'))
        assert package.find('.//{http://www.idpf.org/2007/opf}item[@properties="cover-image"]') is not None
        assert b'Every word must remain available.' in z.read('OEBPS/chapter-0.xhtml')
    notebook_book = Path(next(e['path'] for e in events if e.get('id') == 'notebook' and e['event'] == 'done'))
    with zipfile.ZipFile(notebook_book) as z:
        chapter = z.read('OEBPS/chapter-0.xhtml')
        assert b'print(123)' in chapter and b'row 9' in chapter and b'row 10' not in chapter
    before = python.stat().st_mtime_ns
    subprocess.run(['/bin/zsh', str(engine / 'runtime-bootstrap.sh'), str(support)], check=True, timeout=10)
    assert python.stat().st_mtime_ns == before, 'Ready runtimes must be reused without installing again'
    print('Moved app, fresh private runtime, cover and notebook conversion, and offline reuse: passed.')
