#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Fail if the Git index contains likely private/generated files or secrets.

This conservative release guard supplements human review; it is not a complete
secret scanner. Run after staging all intended public files.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED_DIRS = {'.github', 'docs', 'licenses', 'scripts', 'tests'}
ALLOWED_ROOT = {
    '.gitignore', '.gitattributes', '.editorconfig', 'LICENSE', 'README.md',
    'NOTICE.md', 'THIRD_PARTY_NOTICES.md', 'PRIVACY.md', 'SECURITY.md',
    'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md', 'CHANGELOG.md', 'requirements.txt',
    'EreaderMaker.swift', 'make-icon.swift', 'converter.py', 'reading_layout.py',
    'native_worker.py', 'build-app.sh', 'setup-macos.sh', 'Start E-reader Maker.command',
}
ALLOWED_SUFFIXES = {'.py', '.md', '.txt', '.yml', '.yaml', '.sh'}
PATTERNS = {
    'personal absolute path': rb'/(?:Users|home)/[A-Za-z0-9_.-]+/',
    'private key': rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'GitHub token': rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})',
    'AWS access key': rb'AKIA[A-Z0-9]{16}',
    'API key': rb'sk-(?:proj-)?[A-Za-z0-9_-]{32,}',
}


def main():
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    errors = []
    for name in filter(None, paths):
        path = Path(name)
        if path.parts[0] not in ALLOWED_DIRS and name not in ALLOWED_ROOT:
            errors.append(f'{name}: unexpected public file')
        if path.parts[0] in ALLOWED_DIRS and path.suffix not in ALLOWED_SUFFIXES:
            errors.append(f'{name}: unsupported public file type')
        data = subprocess.check_output(['git', 'show', f':{name}'], cwd=ROOT)
        if len(data) > 500_000 or b'\0' in data:
            errors.append(f'{name}: binary or oversized file')
        for label, pattern in PATTERNS.items():
            if re.search(pattern, data):
                errors.append(f'{name}: possible {label}')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'Public-tree check passed for {len([p for p in paths if p])} tracked files.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
