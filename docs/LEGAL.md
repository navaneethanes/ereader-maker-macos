# Licensing and release boundaries

E-reader Maker is published under GNU AGPL version 3 only. The full LICENSE governs; this document is practical guidance, not a substitute for the license or advice from a qualified lawyer.

## Why AGPL

E-reader Maker imports PyMuPDF, whose open-source licensing route is AGPL. The original application code is therefore offered under AGPL-3.0-only, with its build and installation scripts, source, notices, and warranty disclaimer. There is no MIT or proprietary licensing claim for the combined application. PyMuPDF and MuPDF retain Artifex's copyright and terms. See https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright.

People may use, study, modify, share, and sell copies when they follow the applicable license conditions. Redistributors must preserve required notices and provide Corresponding Source under the terms that apply to their distribution. If you modify and expose an AGPL-covered program for interaction over a network, review the AGPL's network source-offer requirement. See LICENSE and https://www.gnu.org/licenses/gpl-faq.html.

The Mac application download bundles compiled original Swift code, original Python source, build-related notices, and procedural cover artwork code. It does not bundle Python packages, Python itself, Calibre, Tesseract, Apple frameworks, or commercial ebook content. First-use setup downloads a checksum-pinned runtime and packages separately from their upstream distributors. A matching source archive and build scripts accompany each app release. Third-party notices identify the pinned runtime dependencies. A future binary distributor must separately audit everything bundled, retain notices, and provide the required corresponding dependency sources; linking to this app repository alone is insufficient for bundled third-party binaries.

## Documents and DRM

Users are responsible for having the rights or permission needed to convert and share documents. The application does not grant rights to input or output books, promise that every conversion is lawful in every jurisdiction, or remove DRM. Do not add circumvention plugins or instructions to the project. No commercial ebooks, user's study notes, or other private samples are distributed with the source. Tests generate their own content.

## Name, artwork, and affiliation

The book icon is drawn by the project's source code. Amazon/Kindle and Apple/macOS names describe compatibility; no endorsement or affiliation is claimed. No Amazon or Apple logo artwork is bundled. An initial search found existing apps using the working name Paperbound, so this public release uses the descriptive name E-reader Maker. The new name has not undergone a comprehensive trademark clearance search or registration. Before commercial branding, advertising, an App Store launch, or wider distribution, obtain jurisdiction-specific trademark and legal review and rename the project if needed. Publication of source code does not itself establish freedom to use a name everywhere.

## Warranty and security

The license includes warranty and liability provisions subject to applicable law. These are not immunity from legal claims. Layout conversion can lose information; keep originals and review results. The project is not security-certified, Apple-notarized, or certified by Amazon. It makes no universal compatibility promise.

## Maintainer review before binary distribution

- Review all embedded libraries, fonts, artwork, runtime components, license notices, and corresponding-source obligations for the exact build.
- Build in a clean environment for each architecture, test the installed app, and publish checksums plus matching source.
- Use authorized Apple Developer ID credentials for signing/notarization; never commit certificates or credentials.
- Revisit trademark clearance, privacy disclosures, and applicable consumer obligations for the jurisdictions and distribution model involved.
