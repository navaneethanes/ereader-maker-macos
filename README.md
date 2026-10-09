# E-reader Maker for Mac

A small, local macOS app that turns documents into EPUBs for comfortable e-reader reading. One dark window, drag-and-drop files, and a button to find your finished books.

[![CI](https://github.com/navaneethanes/ereader-maker-macos/actions/workflows/ci.yml/badge.svg)](https://github.com/navaneethanes/ereader-maker-macos/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

**macOS 13+ · Apple Silicon and Intel · one-time setup inside the app.**

## Install

1. Download the **macOS DMG** from [Releases](https://github.com/navaneethanes/ereader-maker-macos/releases).
2. Open it and drag **EreaderMaker.app** to **Applications**.
3. Open the app. If macOS blocks this community build, use **System Settings → Privacy & Security → Open Anyway** for the download from this repository. It is ad-hoc signed, not Apple-notarized; [Apple's guidance](https://support.apple.com/102445) explains this step.
4. Add a document and click **Set up & convert**. The app downloads about 60 MB of checksum-verified tools once, then converts offline. **No Terminal, Python installation, or developer tools are needed.**

See the [illustrated-cover guide](docs/COVERS.md) and [installation/troubleshooting instructions](docs/INSTALL.md). A ZIP app download and matching source archive are also provided.

## Make each book your own

Select a waiting book and click **Cover & title**. Clean up its title, choose from **100 cover designs** (20 original motifs in five palettes), or add your own JPG/PNG/TIFF. Flowers, animals, landscapes, and geometric illustrations are generated locally. The title is typeset above the artwork; custom images are fitted without cropping.

![Examples of original locally generated book covers](docs/cover-examples.jpg)

Documents receive a randomly selected built-in cover automatically. Existing EPUB covers are kept by default, and can be replaced explicitly. No book content is uploaded to make a cover. Built-in decorative artwork is CC0; your photos and original books retain their own rights.

## Use it

1. Drop files into the window or choose **Add files**.
2. Leave **Smart reading** selected, or choose **Keep page layout** for PDFs whose exact appearance matters.
3. Choose **Convert for Kindle**.
4. Choose **Open folder** or **Show in Finder** to find your EPUBs.
5. For a Kindle, **Send to Kindle** opens [Amazon's upload page](https://www.amazon.com/sendtokindle). You choose what to upload there. E-reader Maker never signs in or sends files for you.

EPUBs are intended for Send to Kindle, not direct USB copying to a Kindle. Other EPUB-compatible readers can open them directly. Amazon controls acceptance, conversion, and device support.

Each launch starts with an empty list. Completed books stay in their output folder, and the app remembers your folder choice.

By default, files are saved in **E-reader Maker** in your Documents folder (`~/Documents/E-reader Maker`). Choose **Change…** for another destination. Existing files receive a numbered suffix instead of being overwritten. Removing a row does not delete a saved book. Your originals are read in place and remain unchanged.

## Reading layout

- **Smart PDFs:** reflow straightforward text and preserve illustrations. Complex columns, diagrams, and ambiguous tables keep their original page image to avoid guessing the reading order.
- **Images:** centered, proportionally scaled, and limited to 1800 × 2400 pixels. Transparency is flattened onto white. Multi-frame images use the first frame.
- **Tables:** simple wide tables split into small sections with repeated identifying columns. Long tables repeat headers. Merged cells remain merged; complex layouts may need manual review.
- **Notebooks and Python:** headings, Markdown, complete code cells, and saved outputs become readable book sections. Code is never executed. Each cell gets at most 10 saved text/table output lines, clipped at 80 characters per line; up to one saved PNG/JPEG plot is included. Font size may cause preview lines to wrap on your device. See the [notebook guide](docs/NOTEBOOKS.md).
- **Code and typography:** relative text sizes, headings, and code formatting. The reader controls its theme and typeface independently of the app's dark window.
- **Scans:** original page images remain visible. English OCR text is added when optional Tesseract is installed. OCR can make mistakes.
- **Keep page layout:** PDF pages become images, preserving appearance but losing adjustable text size.
- **Existing EPUBs:** by default, basic container validation and unchanged copying preserve the original design. Explicit title or cover edits change the EPUB package metadata while keeping chapter bytes. This is not full EPUB conformance validation, sanitization, or a guarantee that Amazon will accept the book.

Conversion is heuristic. Check important tables, technical examples, mathematics, and complex layouts on your reader. Some PDF pages will work better with **Keep page layout**.

## Supported input

| Available by default | Optional tools |
| --- | --- |
| PDF, DOCX, TXT, Markdown, HTML, EPUB, CBZ | [Calibre](https://calibre-ebook.com/download_osx): MOBI, AZW, AZW3, FB2, ODT, LIT, PDB, DJVU, CBR |
| JPG, PNG, WebP, GIF, BMP, TIFF | [Tesseract](https://tesseract-ocr.github.io/): English OCR |
| Jupyter IPYNB, Python PY (including Databricks SOURCE), Databricks DBC notebook archives | No notebook kernel or Databricks account needed |
| DOC and RTF through macOS `textutil` | Install optional tools separately; none are bundled |

HTML/Markdown data-embedded images are included; website and local-path images are omitted. External Word resources are disabled. Protected/password-locked files are not unlocked. E-reader Maker includes no DRM-removal feature. Calibre installations and plugins are controlled by the user. Audio and video are unsupported.

Limits: 100 files per batch, 200 MB per input, 500 MB declared archive expansion, 2,000 PDF pages/comic images; 40 MB per notebook/code file or DBC notebook entry, 10,000 cells per export. These checks reduce accidental resource exhaustion; they are not a sandbox or protection against every hostile document.

## Privacy and security

Native conversion has no server, analytics, account, or automatic upload. The file list lives only in memory and starts empty each launch. Earlier versions' history files are no longer read or updated. First setup contacts the official Astral Python-build-standalone GitHub release and PyPI; links open external websites in your browser. Optional tools have their own behavior. Original EPUBs may retain remote references and metadata. Read the [privacy notice](PRIVACY.md) and [security policy](SECURITY.md).

## Develop and contribute

Build prerequisites: Python 3.11–3.14 and Apple Command Line Tools. These are only required for development, not the app download.

```sh
./setup-macos.sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_public_tree.py
```

The UI is AppKit/Swift; `native_worker.py` launches local Python conversion. `converter.py` handles inputs and EPUB packaging, `notebook_reader.py` reads saved code/notebook data, and `reading_layout.py` handles reading layout. The icon is drawn from `make-icon.swift`; no third-party icon artwork is bundled. All test documents are generated by the tests. No personal books or conversion history belong in this repository.

See [contributing](CONTRIBUTING.md), [conduct](CODE_OF_CONDUCT.md), [changelog](CHANGELOG.md), and [release procedure](docs/RELEASING.md). To update a checkout, quit E-reader Maker, pull the changes, and rerun `./setup-macos.sh`.

## License and independence

Copyright © 2026 Navaneethan and E-reader Maker contributors. E-reader Maker's original code, documentation, and icon source are licensed under **GNU AGPL-3.0-only**. Use, modification, and redistribution are allowed under [LICENSE](LICENSE), with no warranty. Generated decorative cover artwork is separately dedicated under [CC0](docs/COVERS.md). [Third-party dependencies](THIRD_PARTY_NOTICES.md) retain their own licenses. PyMuPDF/MuPDF use the AGPL open-source licensing route; this project does not purchase or grant a commercial Artifex license.

E-reader Maker is independent and is not affiliated with, endorsed by, or sponsored by Amazon or Apple. Amazon, Kindle, Apple, and macOS are trademarks of their respective owners, used only to describe compatibility. Convert and share only material you have the rights or permission to use. The software license does not license your input books or transfer their copyright. See [legal notes](docs/LEGAL.md).
