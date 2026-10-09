# Third-party notices

E-reader Maker's original code is AGPL-3.0-only. This inventory covers the pinned Python runtime dependencies in `requirements.txt` for 0.3.0. Upstream code is installed from PyPI; it is not vendored in this source release. Copies of available upstream notices are in `licenses/`; those notices retain their own terms.

| Package | Version | Declared license | Upstream |
| --- | --- | --- | --- |
| PyMuPDF / MuPDF | 1.28.2 | GNU AGPL v3 (open-source route; commercial license available separately) | https://github.com/pymupdf/PyMuPDF |
| Mammoth | 1.13.0 | BSD-2-Clause | https://github.com/mwilliamson/python-mammoth |
| Pillow | 12.3.0 | MIT-CMU | https://github.com/python-pillow/Pillow |
| Python-Markdown | 3.11 | BSD-3-Clause | https://github.com/Python-Markdown/markdown |
| Beautiful Soup | 4.15.0 | MIT | https://www.crummy.com/software/BeautifulSoup/ |
| defusedxml | 0.7.1 | PSF license | https://github.com/tiran/defusedxml |
| Cobble | 0.1.4 | BSD-2-Clause per upstream README | https://github.com/mwilliamson/python-cobble |
| Soup Sieve | 2.10 | MIT | https://github.com/facelessuser/soupsieve |
| typing_extensions | 4.16.0 | PSF-2.0 | https://github.com/python/typing_extensions |

The PyMuPDF wheel's COPYING file is a short dual-license declaration. The complete AGPL v3 text is supplied in the root LICENSE; upstream license/copyright details: https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright. Artifex retains its rights. E-reader Maker uses the AGPL option and does not grant an Artifex commercial license.

Cobble's wheel does not include a separate license file. Its author's README explicitly declares BSD-2-Clause; see `licenses/cobble-NOTICE.txt`. No upstream copyright years have been invented. Resolve the complete notice before redistributing bundled Cobble code.

Native wheels can contain additional components (including MuPDF's dependencies and Pillow's codecs). This table is not a complete binary redistribution inventory. Before bundling wheels or a frozen Python runtime, inventory their embedded components, include their notices, and supply any required corresponding source. This release ships application source only and fetches dependencies during setup.

## Optional and platform components

Calibre (GPL v3) and Tesseract (Apache-2.0) are optional, separately installed command-line tools. No executables, plugins, or OCR models are included here. Their installations retain their own licenses and notices. Python, pip, Apple's frameworks, system fonts, SF Symbols, `textutil`, and developer tools are not bundled. See each provider's terms for your installation and any future distribution.

## Project artwork and examples

The app icon is generated from `make-icon.swift` and covered by the project's AGPL-3.0-only license. No Amazon/Apple logo artwork or user documents are included. Test fixtures are generated from invented text and simple shapes.
