# Install E-reader Maker on a Mac

Requires macOS 13 or later. The same download supports Apple Silicon and Intel Macs.

1. Download **E-reader-Maker-0.5.0-macOS.dmg** from [GitHub Releases](https://github.com/navaneethanes/ereader-maker-macos/releases).
2. Open the DMG and drag **EreaderMaker.app** onto **Applications**. Eject the disk image after copying.
3. Open **E-reader Maker** from Applications. This community build is not Apple-notarized. If macOS blocks it, open **System Settings → Privacy & Security → Open Anyway**, then confirm opening the app you downloaded from this repository. Follow [Apple's instructions](https://support.apple.com/102445). Do not disable Gatekeeper globally.
4. Add a document, then click **Set up & convert**. The first conversion asks to download about 60 MB of tools from official GitHub/PyPI endpoints. This happens inside the app; no Terminal, Python installation, developer tools, or administrator password is needed for setup.
5. Once setup finishes, the book is converted. Later conversions work offline. Click **Open folder** to find the EPUB.

A ZIP app download is also provided: unzip it and move EreaderMaker.app to Applications. Do not run the app inside the mounted DMG. The app can be moved independently of the source folder.

## Covers and titles

Select a waiting book and click **Cover & title**. Edit the title, select one of 100 designs, or click **Choose image…** to add your own JPG, PNG, or TIFF. Your image is fitted without cropping. The title stays above it. Save with **Use this cover & title**, then convert.

By default, documents receive a randomly selected built-in cover and ebooks keep their existing covers. The 100 designs comprise 20 original motifs in five color palettes. They are designed for color and monochrome screens. Pick **No new cover** / **Keep existing cover** to preserve the original front pages. Choosing a new cover does not erase a PDF's original first page.

## Storage and privacy

Books default to `~/Documents/E-reader Maker`; **Change…** selects a different destination. Files with the same name get a numbered suffix instead of being overwritten.

The private runtime lives in `~/Library/Application Support/E-reader Maker`. The app never uploads your documents. Setup downloads checksummed tools; Send to Kindle opens Amazon's website and you choose whether to upload there. See PRIVACY.md.

## Troubleshooting

- **Setup fails:** check internet access to github.com, release-assets.githubusercontent.com, pypi.org, and files.pythonhosted.org, then retry. Checksums are verified before a runtime is accepted; do not bypass a failed check.
- **Setup says it is already running after a crash:** quit all copies of the app. In Finder choose Go → Go to Folder and enter `~/Library/Application Support/E-reader Maker`. Remove the `.setup-lock` folder and any `.setup-*` temporary folder left by that failed installation, then reopen the app. Do not remove these while setup is running. Hidden files can be shown with Command-Shift-period.
- **An incomplete runtime exists:** quit the app and remove only the named `runtime-v1-*` folder that has no `.ready` file, then retry. Preserve `native-library.json` and your output books.
- **App cannot read a cover image:** use JPG, PNG, or TIFF below 40 MB and 40 megapixels. HEIC is not supported in this release.
- **Optional inputs unavailable:** install Calibre separately in `/Applications/calibre.app`. For English OCR, install Tesseract separately; if you use Homebrew, `brew install tesseract`. Core conversion and covers need neither.
- **Table or text order looks wrong:** try **Keep page layout** and review the result on your reader.
- **EPUB rejected by Amazon:** existing EPUBs get basic validation, not full conformance testing. Use a publisher's compatible edition if available. Cover thumbnails on Kindle depend on Amazon's processing and device behavior.

## Update or uninstall

Quit the app, replace it with the newer app from Releases, and reopen it. Updates may request a new private runtime; existing books are retained. The conversion list starts empty on every launch. Old runtime directories may be removed while the app is closed if you need disk space; the current one will be reinstalled if removed.

To uninstall, remove the app and optionally `~/Library/Application Support/E-reader Maker`. Keep or delete your output books separately. A Desktop alias can be made with Finder's File → Make Alias. Older history files are no longer loaded or updated.

## Build from source (developers)

Install Python 3.11–3.14 and Apple's Command Line Tools. Clone the repository, run `./setup-macos.sh`, then `open EreaderMaker.app`. To build a universal app, run `./build-app.sh --universal`. The app uses its private runtime even when built from source; the development `.venv` is used only for build tools and tests.

## Code and notebooks

Add `.ipynb`, `.py`, or Databricks `.dbc` files just like a PDF. Markdown headings and code become book sections. Only saved results are included: up to 10 short text/table lines and one saved PNG/JPEG plot per cell. Code is never run. See [notebook details](NOTEBOOKS.md).
