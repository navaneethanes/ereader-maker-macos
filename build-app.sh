#!/bin/zsh
# SPDX-License-Identifier: AGPL-3.0-only
set -eu
cd "${0:A:h}"
mkdir -p EreaderMaker.app/Contents/MacOS EreaderMaker.app/Contents/Resources .build/module-cache
mkdir -p EreaderMaker.app/Contents/Resources/Legal
cp LICENSE NOTICE.md THIRD_PARTY_NOTICES.md PRIVACY.md EreaderMaker.app/Contents/Resources/Legal/
cp -R licenses EreaderMaker.app/Contents/Resources/Legal/
swift -module-cache-path .build/module-cache make-icon.swift .build/EreaderMaker.iconset
.venv/bin/python -c 'from PIL import Image; Image.open(".build/EreaderMaker.iconset/icon_512x512@2x.png").save("EreaderMaker.app/Contents/Resources/EreaderMaker.icns")'
MACOSX_DEPLOYMENT_TARGET=13.0 swiftc -swift-version 5 -module-cache-path .build/module-cache EreaderMaker.swift -o .build/EreaderMaker -framework Cocoa -framework UniformTypeIdentifiers
cp .build/EreaderMaker EreaderMaker.app/Contents/MacOS/EreaderMaker
cat > EreaderMaker.app/Contents/Info.plist <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>E-reader Maker</string>
<key>CFBundleDisplayName</key><string>E-reader Maker</string>
<key>CFBundleIdentifier</key><string>local.ereadermaker.reader</string>
<key>CFBundleVersion</key><string>3</string>
<key>CFBundleShortVersionString</key><string>0.3.0</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleExecutable</key><string>EreaderMaker</string>
<key>CFBundleIconFile</key><string>EreaderMaker.icns</string>
<key>NSHighResolutionCapable</key><true/>
<key>LSMinimumSystemVersion</key><string>13.0</string>
</dict></plist>
PLIST
codesign --force --sign - EreaderMaker.app
