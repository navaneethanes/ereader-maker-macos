#!/bin/zsh
# SPDX-License-Identifier: AGPL-3.0-only
set -eu
cd "${0:A:h:h}"
version='0.5.0'
./build-app.sh --universal
mkdir -p dist
stage="$(mktemp -d "$PWD/.build/dmg-XXXXXX")"
trap 'rm -rf "$stage"' EXIT
/usr/bin/ditto EreaderMaker.app "$stage/EreaderMaker.app"
ln -s /Applications "$stage/Applications"
cat > "$stage/INSTALL FIRST.txt" <<'TEXT'
E-reader Maker — install in five steps

1. Drag EreaderMaker.app onto Applications.
2. Eject this disk image.
3. Open E-reader Maker from Applications.
4. If macOS blocks this unsigned community build, use System Settings > Privacy & Security > Open Anyway. Only do this for the download from github.com/navaneethanes/ereader-maker-macos. Never disable Gatekeeper globally.
5. Add a book and click Set up & convert. The app downloads about 60 MB of verified tools once. No Terminal or Python installation is needed. Later conversions work offline.

Select a waiting book and click Cover & title to edit its title, choose a design, or use your own image.

Books save to Documents/E-reader Maker by default. Open folder shows them in Finder.

macOS 13+ · Intel and Apple Silicon · Internet needed for first setup
This build is ad-hoc signed, not Apple-notarized.
Source, license, help: https://github.com/navaneethanes/ereader-maker-macos
TEXT
cp LICENSE "$stage/LICENSE.txt"
/usr/bin/hdiutil create -volname 'Install E-reader Maker' -srcfolder "$stage" -format UDZO -ov "dist/E-reader-Maker-$version-macOS.dmg"
/usr/bin/ditto -c -k --sequesterRsrc --keepParent EreaderMaker.app "dist/E-reader-Maker-$version-macOS.zip"
