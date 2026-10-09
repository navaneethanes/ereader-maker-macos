# E-reader Maker for Mac

A small, local macOS app that turns documents into EPUBs for comfortable e-reader reading. One dark window, drag-and-drop files, and a button to find your finished books.

[![CI](https://github.com/navaneethanes/ereader-maker-macos/actions/workflows/ci.yml/badge.svg)](https://github.com/navaneethanes/ereader-maker-macos/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

**Early release · macOS 13+ · build from source.** This release does not include a standalone installer or an Apple-notarized download. It builds a native app on your Mac; Python and the source folder remain required. Apple Silicon is tested locally; CI checks Apple Silicon and Intel builds. Windows and Linux app interfaces are not available.

## Get started

1. Install [Python 3.11–3.14](https://www.python.org/downloads/macos/) (3.12 recommended) and Apple's Command Line Tools. To install the latter, run `xcode-select --install` in Terminal and wait for installation to finish.
2. Download and unzip the [latest source release](https://github.com/navaneethanes/ereader-maker-macos/releases), or clone this repository:

   ```sh
   git clone https://github.com/navaneethanes/ereader-maker-macos.git
   cd ereader-maker-macos
   ./setup-macos.sh
   open EreaderMaker.app
   ```

   For a downloaded archive, open Terminal in the extracted folder and run `./setup-macos.sh`. Setup downloads the pinned dependencies from PyPI, compiles the app, and signs it locally. It does not request administrator access or change macOS security settings.
3. Keep **EreaderMaker.app** beside `.venv` and the source files. To put it on your Desktop, select the app in Finder, choose **File → Make Alias**, and move the alias to your Desktop. Moving just the app will break conversion.

After setup, double-click **EreaderMaker.app** or **Start E-reader Maker.command**. See [installation and troubleshooting](docs/INSTALL.md) if you need help. Review downloaded code before running it. If macOS blocks a downloaded item, follow [Apple's guidance](https://support.apple.com/102445); do not disable Gatekeeper globally.

## Use it

1. Drop files into the window or choose **Add files**.
2. Leave **Smart reading** selected, or choose **Keep page layout** for PDFs whose exact appearance matters.
3. Choose **Convert for Kindle**.
4. Choose **Open folder** or **Show in Finder** to find your EPUBs.
5. For a Kindle, **Send to Kindle** opens [Amazon's upload page](https://www.amazon.com/sendtokindle). You choose what to upload there. E-reader Maker never signs in or sends files for you.

EPUBs are intended for Send to Kindle, not direct USB copying to a Kindle. Other EPUB-compatible readers can open them directly. Amazon controls acceptance, conversion, and device support.

By default, files are saved in **Kindle Books** inside the project folder. Choose **Change…** for another destination. Existing files receive a numbered suffix instead of being overwritten. Removing a row does not delete a saved book. Your originals are read in place and remain unchanged.

## Reading layout

- **Smart PDFs:** reflow straightforward text and preserve illustrations. Complex columns, diagrams, and ambiguous tables keep their original page image to avoid guessing the reading order.
- **Images:** centered, proportionally scaled, and limited to 1800 × 2400 pixels. Transparency is flattened onto white. Multi-frame images use the first frame.
- **Tables:** simple wide tables split into small sections with repeated identifying columns. Long tables repeat headers. Merged cells remain merged; complex layouts may need manual review.
- **Code and typography:** relative text sizes, headings, and code formatting. The reader controls its theme and typeface independently of the app's dark window.
- **Scans:** original page images remain visible. English OCR text is added when optional Tesseract is installed. OCR can make mistakes.
- **Keep page layout:** PDF pages become images, preserving appearance but losing adjustable text size.
- **Existing EPUBs:** basic container validation and unchanged copying preserve the original design. This is not full EPUB conformance validation, sanitization, or a guarantee that Amazon will accept the book.

Conversion is heuristic. Check important tables, technical examples, mathematics, and complex layouts on your reader. Some PDF pages will work better with **Keep page layout**.

## Supported input

| Available by default | Optional tools |
| --- | --- |
| PDF, DOCX, TXT, Markdown, HTML, EPUB, CBZ | [Calibre](https://calibre-ebook.com/download_osx): MOBI, AZW, AZW3, FB2, ODT, LIT, PDB, DJVU, CBR |
| JPG, PNG, WebP, GIF, BMP, TIFF | [Tesseract](https://tesseract-ocr.github.io/): English OCR |
| DOC and RTF through macOS `textutil` | Install optional tools separately; none are bundled |

HTML/Markdown data-embedded images are included; website and local-path images are omitted. External Word resources are disabled. Protected/password-locked files are not unlocked. E-reader Maker includes no DRM-removal feature. Calibre installations and plugins are controlled by the user. Audio and video are unsupported.

Limits: 100 files per batch, 200 MB per input, 500 MB declared archive expansion, 2,000 PDF pages/comic images. These checks reduce accidental resource exhaustion; they are not a sandbox or protection against every hostile document.

## Privacy and security

Native conversion has no server, analytics, account, or automatic upload. Conversion history includes local paths and is saved in `data/native-library.json`. Setup contacts PyPI; links open external websites in your browser. Optional tools have their own behavior. Original EPUBs may retain remote references and metadata. Read the [privacy notice](PRIVACY.md) and [security policy](SECURITY.md).

## Develop and contribute

```sh
./setup-macos.sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_public_tree.py
```

The UI is AppKit/Swift; `native_worker.py` launches local Python conversion. `converter.py` handles inputs and EPUB packaging, and `reading_layout.py` handles reading layout. The icon is drawn from `make-icon.swift`; no third-party icon artwork is bundled. All test documents are generated by the tests. No personal books or conversion history belong in this repository.

See [contributing](CONTRIBUTING.md), [conduct](CODE_OF_CONDUCT.md), [changelog](CHANGELOG.md), and [release procedure](docs/RELEASING.md). To update a checkout, quit E-reader Maker, pull the changes, and rerun `./setup-macos.sh`.

## License and independence

Copyright © 2026 Navaneethan and E-reader Maker contributors. E-reader Maker's original code, documentation, and icon source are licensed under **GNU AGPL-3.0-only**. Use, modification, and redistribution are allowed under [LICENSE](LICENSE), with no warranty. [Third-party dependencies](THIRD_PARTY_NOTICES.md) retain their own licenses. PyMuPDF/MuPDF use the AGPL open-source licensing route; this project does not purchase or grant a commercial Artifex license.

E-reader Maker is independent and is not affiliated with, endorsed by, or sponsored by Amazon or Apple. Amazon, Kindle, Apple, and macOS are trademarks of their respective owners, used only to describe compatibility. Convert and share only material you have the rights or permission to use. The software license does not license your input books or transfer their copyright. See [legal notes](docs/LEGAL.md).
