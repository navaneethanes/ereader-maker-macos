#!/bin/zsh
# SPDX-License-Identifier: AGPL-3.0-only
set -eu
cd "${0:A:h}"
if [[ ! -x .venv/bin/python || ! -x EreaderMaker.app/Contents/MacOS/EreaderMaker ]]; then
  ./setup-macos.sh
fi
open EreaderMaker.app
