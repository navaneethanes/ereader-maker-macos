# Release procedure

The downloadable app contains original Swift executables, original Python source, the procedural cover renderer, and notices. First-use setup downloads a checksum-pinned private Python runtime and pinned packages directly from upstream; no third-party runtime binaries are inside the app/DMG.

1. Update versions in `build-app.sh`, `scripts/package-macos.sh`, CHANGELOG.md, and installation documentation. Review the exact runtime URLs and hashes in `runtime-bootstrap.sh` and `requirements-runtime.txt`. When changing dependencies, run `python scripts/lock_runtime.py` and review the generated lockfile.
2. Run `./build-app.sh`, `.venv/bin/python -m unittest discover -s tests -v`, and `.venv/bin/python scripts/smoke_packaged.py`. The smoke test downloads a fresh runtime and converts a book from a moved app without the development checkout. Run `pip-audit -r requirements.txt` and require CI to pass on Apple Silicon and Intel.
3. Inspect `git ls-files` and the staged diff. Run `.venv/bin/python scripts/check_public_tree.py`. Never publish personal documents, history, signing credentials, or the development virtual environment.
4. Run `./scripts/package-macos.sh` on a Mac. It builds universal executables and creates a DMG with an Applications shortcut, instructions, and license, plus a ZIP app download. Inspect the archive inventory and verify `codesign --verify --deep --strict EreaderMaker.app`. Verify both executable architectures with `lipo -info`.
5. Tag the reviewed commit. Use `git archive` to create a matching source ZIP from that exact tag. Publish the DMG, app ZIP, complete corresponding application source ZIP, and SHA256SUMS together. Keep the source accessible for at least as long as the associated binaries. Do not replace an existing release asset silently.
6. Verify remote release digests and tag commit. State the one-time internet requirement and that ad-hoc signing is not Apple notarization. Link the installation guide.

The app currently has no Developer ID certificate. Do not remove quarantine or globally weaken Gatekeeper in an installer. If authorized Apple signing/notarization credentials become available, sign all executables, notarize and staple the distribution, and test the downloaded app on a clean Mac before changing these claims.

If future releases embed third-party binaries, audit every runtime/library/font/model, preserve notices, and supply corresponding sources where required. The present source archive covers the original compiled app and cover renderer; it is not a substitute for third-party corresponding sources if those components are later bundled. See LEGAL.md.
