# Contributing

Thank you for helping make documents easier to read. Small, focused changes are welcome.

1. Open an issue for a substantial behavior change. For bugs, use a small document you created and have permission to share; do not attach commercial ebooks or private files.
2. Fork the repository and create a branch. Follow README setup instructions.
3. Keep the macOS interface simple and accessible. Keep conversion local and preserve the user's source files. Avoid new network access or dependencies unless clearly justified.
4. Add a regression test for conversion or security behavior you change, using generated fixtures. Run `.venv/bin/python -m unittest discover -s tests -v`, `./build-app.sh`, and `.venv/bin/python scripts/check_public_tree.py` after staging your intended files.
5. Describe the problem, resulting behavior, validation, and limitations in a pull request. Include screenshots only when they contain no private data.

By submitting a contribution, you confirm that you wrote it or have permission to contribute it, and agree to license it under the project's AGPL-3.0-only terms. Preserve third-party notices and disclose provenance for copied or adapted material. Do not submit proprietary code, assets without redistribution rights, or credentials. AI-assisted contributions require the same review and tests as other code; disclose substantial generated contributions in the pull request description.

No separate copyright assignment or CLA is required. Contributors retain their copyright. Follow CODE_OF_CONDUCT.md and use SECURITY.md for vulnerabilities.

Original decorative artwork contributions to the built-in cover templates must also be available under CC0-1.0, matching docs/COVERS.md. Do not contribute stock images or artwork you cannot dedicate under those terms. Application code remains AGPL-3.0-only.
