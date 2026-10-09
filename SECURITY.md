# Security policy

The latest published release and the current main branch receive best-effort security fixes. There is no guaranteed response time or commercial support commitment.

## Report privately

Use [GitHub private vulnerability reporting](https://github.com/navaneethanes/ereader-maker-macos/security/advisories/new). Include the version, macOS/Python versions, impact, reproduction steps, and a minimal synthetic example. Do not post an exploit or personal document in a public issue. If private reporting is temporarily unavailable, open a public issue asking for a private contact without disclosing the vulnerability.

## Threat model and limits

E-reader Maker processes complex files with native libraries and external tools. It is not sandboxed. A separate worker and archive/page/input limits reduce some failure modes but do not make malicious documents safe. Process only documents from sources you trust, keep dependencies updated, and avoid running the app with elevated permissions.

DOCX external-file access is explicitly disabled. HTML content is filtered before conversion, but unchanged EPUB copies retain their original active content and remote references. The app is not an EPUB sanitizer. Optional Calibre plugins run under the user's own installation and must be reviewed separately.

Never commit credentials, signing certificates, personal books, history, or logs. CI uses generated test fixtures, dependency audits, and a public-tree check. Passing checks are not a guarantee that all vulnerabilities have been found.
