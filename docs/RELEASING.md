# Release procedure

Current distribution: source-only macOS preview. Do not upload a local EreaderMaker.app, virtual environment, personal book, screenshot showing user data, or entire working folder.

1. Review license notices, pinned dependencies, changelog, privacy claims, and known limitations. Update the version in build-app.sh and CHANGELOG.md.
2. Run the tests, native build, public-tree scan, and `pip-audit -r requirements.txt`. CI must pass on the commit being tagged. Use a fresh checkout to verify setup; do not depend on local files ignored by Git.
3. Inspect `git ls-files` and `git diff --cached` for personal data, credentials, or content without redistribution permission. Test fixtures must be generated or explicitly licensed.
4. Create a version tag on the reviewed commit. Package source with `git archive --format=zip --prefix=ereader-maker-macos-VERSION/ --output=dist/ereader-maker-macos-VERSION-source.zip TAG`. This includes only committed files. Run `shasum -a 256` on the archive.
5. Create a GitHub prerelease with that source ZIP and its SHA256SUMS file. Explain setup requirements, changes, limitations, and that there is no standalone/notarized binary. Verify download visibility, tag commit, CI, and checksum.

A future standalone installer needs a relocatable runtime, both target architectures where supported, testing outside the development checkout, an inventory of all bundled components and full license compliance (including corresponding sources), and Apple signing/notarization. Do not label ad-hoc signing as Developer ID signing. See LEGAL.md.
