# Privacy notice

Effective for E-reader Maker 0.4.0, 9 October 2026.

## Local conversion

The native app reads files you select, runs a local Python worker, and writes converted books to your selected folder. It has no analytics, advertising, sign-in, background upload, or local HTTP server. Source files are not intentionally modified.

`~/Library/Application Support/E-reader Maker/native-library.json` records up to 100 completed entries, including source paths, output paths, edited titles, selected cover designs, custom-image paths, and conversion notes. Built-in artwork and title rendering run locally; selected images are read from disk. Custom images are embedded in the resulting EPUB, but their source file remains unchanged. Folder selection is stored in macOS preferences for `local.ereadermaker.reader`. Pending batch paths are written to a randomly named temporary manifest. That manifest is removed when the batch finishes or is cancelled normally. Temporary conversion directories and a reserved output filename may remain after a forced termination or power loss.

To clear history, quit the app and delete `~/Library/Application Support/E-reader Maker/native-library.json`. To reset the folder preference, run `defaults delete local.ereadermaker.reader destination` in Terminal. Delete output books separately if desired; removing rows does not delete them. macOS backups and cloud-synced folders may retain copies under your own settings.

## Network boundaries

The first conversion asks to download a private Python runtime from Astral’s official python-build-standalone GitHub release and pinned packages from PyPI (including their release/CDN domains). SHA-256 hashes are verified. Runtime files live under `~/Library/Application Support/E-reader Maker/runtime-v1-*`. No document content or titles are sent with these downloads. App updates may use a new runtime directory; old directories remain until removed. Git cloning and repository links contact GitHub. Send to Kindle opens Amazon's website; E-reader Maker itself does not upload files, receive Amazon credentials, or manage your Amazon account. If you upload there, Amazon's policies govern that transfer. Browser behavior, OS services, and separately installed Calibre/Tesseract are outside E-reader Maker's control.

Converted HTML/Markdown ignores external images, and Word conversion disables external file access. Existing EPUBs are copied unchanged after basic validation. They can retain metadata, links, scripts, and remote-resource references that your reading software may act on. Conversion is not an anonymization or document-sanitization service.

## Reports

GitHub issues and attachments are public. Do not include personal documents, credentials, real file paths, or copyrighted books. Use a synthetic reproduction. Report vulnerabilities privately as described in SECURITY.md. Maintainers do not receive your conversion history unless you voluntarily share it.
