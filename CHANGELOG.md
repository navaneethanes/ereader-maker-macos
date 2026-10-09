# Changelog

## 0.5.0 — 2026-10-09

- Jupyter v4 notebooks, Python scripts/Databricks SOURCE exports, and DBC notebook archives convert to EPUB without executing code.
- Preserve Markdown headings and complete code; saved text/table output previews share a 10-line budget per cell, with long rows clipped and a visible notice. Include one saved PNG/JPEG plot per cell.
- Pick automatic covers randomly from the 100 bundled designs; keep manual/custom choices and existing ebook-cover defaults.
- Start each launch with an empty conversion list. Keep saved books and the output-folder preference. Older history files are no longer loaded or updated.

## 0.4.0 — 2026-10-09

- Universal Mac app download with drag-to-Applications installation and first-use setup.
- Private checksum-verified runtime; no manual Python installation or Terminal needed.
- 100 locally generated cover designs: 20 motifs × five palettes, with title typography.
- Editable book titles and optional custom JPG/PNG/TIFF cover images.
- EPUB cover metadata and front page; existing ebook covers preserved by default.
- Recent history moved to Application Support; books default to Documents/E-reader Maker.
- Original decorative cover artwork dedicated under CC0-1.0.

The community app is ad-hoc signed, not Apple-notarized.

## 0.3.0 — 2026-10-09

First public macOS source release (preview).

- Native dark AppKit window, drag-and-drop batches, cancellation, and Finder actions.
- EPUB output from PDFs, Word documents, ebooks, text, images, and comics.
- Reflow for simple PDFs; page-image fallback for complex layouts; table and image adjustments.
- Optional local English OCR and Calibre conversion.
- Guided macOS setup, generated test fixtures, CI, and dependency auditing.
- AGPL-3.0 license, dependency notices, privacy/security policies, and contribution guidance.
- Explicitly disabled external file access in Word conversion.

Known limits: source installation required; no standalone/notarized binary, no DRM removal, no guarantee of Send to Kindle acceptance. Complex layouts require review on a real reader. No physical Kindle certification is claimed.
