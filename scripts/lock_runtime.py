# SPDX-License-Identifier: AGPL-3.0-only
"""Regenerate package hashes from PyPI after reviewing pinned versions."""
import json, urllib.request
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent.parent)
lines=['# Generated from PyPI SHA-256 digests; runtime downloads require these hashes.']
for line in Path('requirements.txt').read_text().splitlines():
 if not line or line.startswith('#'): continue
 name,version=line.split('==')
 with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json') as r: data=json.load(r)
 hashes=sorted({f['digests']['sha256'] for f in data['urls'] if f['packagetype']=='bdist_wheel'})
 assert hashes,name
 lines.append(line+' \\\n'+ ' \\\n'.join('    --hash=sha256:'+h for h in hashes))
Path('requirements-runtime.txt').write_text('\n'.join(lines)+'\n')
