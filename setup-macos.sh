#!/bin/zsh
# SPDX-License-Identifier: AGPL-3.0-only
set -eu
cd "${0:A:h}"
if [[ "$(uname -s)" != Darwin ]]; then
  echo 'E-reader Maker requires macOS 13 or later.' >&2
  exit 1
fi
macos_version="$(sw_vers -productVersion)"
if (( ${macos_version%%.*} < 13 )); then
  echo 'E-reader Maker requires macOS 13 or later.' >&2
  exit 1
fi
if ! xcode-select -p >/dev/null 2>&1; then
  echo 'Install Apple Command Line Tools with: xcode-select --install' >&2
  echo 'After installation finishes, run this script again.' >&2
  exit 1
fi
python_bin="${EREADER_MAKER_PYTHON:-python3}"
if ! "$python_bin" -c 'import sys; assert (3, 11) <= sys.version_info[:2] < (3, 15)' 2>/dev/null; then
  echo 'Install Python 3.11–3.14 from python.org, then run this script again.' >&2
  echo 'To select it explicitly: EREADER_MAKER_PYTHON=/path/to/python3 ./setup-macos.sh' >&2
  exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
  "$python_bin" -m venv .venv
fi
.venv/bin/python -c 'import sys; assert (3, 11) <= sys.version_info[:2] < (3, 15), "Recreate .venv with a supported Python version"'
echo 'Installing the pinned conversion dependencies from PyPI…'
.venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt
.venv/bin/python -m pip check
./build-app.sh
echo 'Ready. Double-click EreaderMaker.app in this folder.'
echo 'Keep the app beside its source files and .venv; use a Finder alias elsewhere.'
