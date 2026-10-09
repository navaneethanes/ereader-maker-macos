# macOS installation and troubleshooting

Requirements: macOS 13 or newer, Python 3.11–3.14 (3.12 recommended), Apple's Xcode Command Line Tools, and internet access for initial dependency installation. Build for the architecture of your Python interpreter and compiler; use native arm64 tools on Apple Silicon. Intel is included in CI. No Windows/Linux desktop UI is provided.

Install Command Line Tools with `xcode-select --install`, then wait for Apple's installation to complete. Download Python from https://www.python.org/downloads/macos/ or use an existing compatible installation.

Download a source archive from GitHub Releases and extract it to a permanent, writable location in your home folder. In Terminal, change to that folder and run:

```sh
./setup-macos.sh
open EreaderMaker.app
```

Alternatively, clone the repository as shown in README.md. You may select an explicit interpreter with `EREADER_MAKER_PYTHON=/absolute/path/to/python3 ./setup-macos.sh`.

Setup installs pinned dependencies into `.venv`, compiles Swift for the current Mac, includes the generated icon and legal notices, and applies an ad-hoc signature. This is not Developer ID signing or Apple notarization. It does not disable Gatekeeper. Follow https://support.apple.com/102445 if macOS blocks an item you have reviewed and trust.

Keep the app and supporting folder together. For a Desktop launcher, use Finder's File → Make Alias on EreaderMaker.app and move the alias. Do not copy just the app into Applications.

## Common problems

- **Python is too old:** install a supported version, then pass its path through `EREADER_MAKER_PYTHON`. If an incompatible `.venv` already exists, quit the app, remove only that `.venv` folder, and rerun setup.
- **No compiler:** complete Command Line Tools installation and retry.
- **Conversion cannot start:** keep the app beside `native_worker.py`, `converter.py`, `reading_layout.py`, and `.venv`. Rerun setup if dependencies were removed.
- **Optional inputs unavailable:** install Calibre separately in `/Applications/calibre.app`; install Tesseract separately for English OCR, for example `brew install tesseract` if you already use Homebrew. E-reader Maker checks the usual Homebrew command paths.
- **Bad table or text order:** retry using Keep page layout. Preserve the original and check the output on your reader.
- **Amazon rejects an EPUB:** original EPUBs receive only basic checks. Use the publisher's compatible edition where available. Amazon can change supported features independently of E-reader Maker.
- **Interrupted conversion:** after quitting the app, remove abandoned `.ereader-maker-*` folders or empty reserved outputs in the destination only if you are certain no conversion is active.

## Update or uninstall

Quit E-reader Maker before updating. In a Git checkout, run `git pull --ff-only` and then `./setup-macos.sh`. Setup does not intentionally delete books or history.

To uninstall, first move any books you want to keep out of the project folder. Delete the project folder and any Finder aliases. Conversion history resides in that folder. The `local.ereadermaker.reader` preference domain can be removed using `defaults delete local.ereadermaker.reader`; external output books are not deleted by that command.
