#!/bin/zsh
# SPDX-License-Identifier: AGPL-3.0-only
set -eu
cd "${0:A:h}"
app='EreaderMaker.app'
mkdir -p "$app/Contents/MacOS" "$app/Contents/Helpers" "$app/Contents/Resources/Legal" "$app/Contents/Resources/Engine" .build/module-cache
cp LICENSE NOTICE.md THIRD_PARTY_NOTICES.md PRIVACY.md "$app/Contents/Resources/Legal/"
cp -R licenses "$app/Contents/Resources/Legal/"
cp native_worker.py notebook_reader.py converter.py reading_layout.py book_covers.py requirements-runtime.txt runtime-bootstrap.sh "$app/Contents/Resources/Engine/"
cp docs/INSTALL.md "$app/Contents/Resources/INSTALL.md"
swift -module-cache-path .build/module-cache make-icon.swift .build/EreaderMaker.iconset
.venv/bin/python -c 'from PIL import Image; Image.open(".build/EreaderMaker.iconset/icon_512x512@2x.png").save("EreaderMaker.app/Contents/Resources/EreaderMaker.icns")'
architectures=("$(uname -m)")
if [[ "${1:-}" == '--universal' ]]; then architectures=(arm64 x86_64); fi
for architecture in "${architectures[@]}"; do
  swiftc -swift-version 5 -target "$architecture-apple-macos13.0" -module-cache-path .build/module-cache EreaderMaker.swift CoverArt.swift CoverEditor.swift RuntimeSetup.swift -o ".build/EreaderMaker-$architecture" -framework Cocoa -framework UniformTypeIdentifiers
  swiftc -swift-version 5 -target "$architecture-apple-macos13.0" -module-cache-path .build/module-cache CoverArt.swift cover-render.swift -o ".build/cover-render-$architecture" -framework Cocoa
done
if [[ "${1:-}" == '--universal' ]]; then
  lipo -create .build/EreaderMaker-arm64 .build/EreaderMaker-x86_64 -output "$app/Contents/MacOS/EreaderMaker"
  lipo -create .build/cover-render-arm64 .build/cover-render-x86_64 -output .build/cover-render
else
  cp ".build/EreaderMaker-$(uname -m)" "$app/Contents/MacOS/EreaderMaker"
  cp ".build/cover-render-$(uname -m)" .build/cover-render
fi
cp .build/cover-render "$app/Contents/Helpers/cover-render"
cat > "$app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>E-reader Maker</string>
<key>CFBundleDisplayName</key><string>E-reader Maker</string>
<key>CFBundleIdentifier</key><string>local.ereadermaker.reader</string>
<key>CFBundleVersion</key><string>5</string>
<key>CFBundleShortVersionString</key><string>0.5.0</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleExecutable</key><string>EreaderMaker</string>
<key>CFBundleIconFile</key><string>EreaderMaker.icns</string>
<key>NSHighResolutionCapable</key><true/>
<key>LSMinimumSystemVersion</key><string>13.0</string>
</dict></plist>
PLIST
codesign --force --sign - "$app/Contents/Helpers/cover-render"
codesign --force --sign - "$app"
