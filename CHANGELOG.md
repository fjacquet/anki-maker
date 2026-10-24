# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Standing practice: on each release, move `[Unreleased]` to a dated `[X.Y.Z]`
section rather than letting it accumulate indefinitely.

## [Unreleased]

## [0.1.5] - 2026-10-24

### Security

- **`make vuln` and the Security workflow now actually scan.** `uvx osv-scanner` never resolved
  (osv-scanner is a Go binary, not on PyPI) and `|| true` hid the failure, so no CI run had ever
  scanned `uv.lock`. `make vuln` now runs `osv-scanner scan source --recursive .` and fails on
  findings; fjacquet/ci v1.6.0 installs a pinned, checksum-verified binary in CI.
- Full `uv lock --upgrade` refresh (`litellm` 1.106.3 among others); no open advisory.

## [0.1.4] - 2026-10-24

### Security

- `pillow` 12.3.0 → 13.0.0 for 41 advisories (5 critical, e.g. GHSA-w889-685w-c8fh and
  GHSA-v9pv-5gc8-w2m6: heap overflows and DoS in the TIFF, JPEG, FPX, PDF and GIF decoders).
- `filelock` → 4.2.4 for GHSA-v4x8-3wr5-3wq8 (High), GHSA-9vhv-jxww-xfm5 and GHSA-567q-5qvw-pf92,
  through a uv `override-dependencies` entry `filelock>=4.2.1,<5`: litellm caps `filelock<4`.
  Dependents use only `FileLock`, `SoftFileLock`, `BaseFileLock` and `Timeout`. Drop the override
  once litellm allows filelock 4.2.1.
- `pypdf` (11 advisories), `aiohttp` (8), `virtualenv` (12), `certifi` → 2026.10.23 for GHSA-6q48-6c7w-9gw2, `opentelemetry-api` → 1.45.1 for GHSA-xcq7-p3pf-p88h.
- `nltk` → 3.10.4 closes GHSA-8mgp-746c-j5xp (affected ≤ 3.10.3).

### Changed

- Full `uv lock --upgrade` refresh, replacing the 2026-10-02 lock.
- The Security workflow now also runs on a weekly schedule and can be triggered manually.
- `document-to-anki --version` reads `__version__` instead of a hard-coded string.

## [0.1.3] - 2026-09-13

### Changed

- Container base image names are now fully qualified for Podman.

### Security

- Bumped `nltk` to 3.10.3 and refreshed all locked dependencies.
- Resolved Dependabot security alerts.

## [0.1.2] - 2026-08-01

### Added

- Documentation site published to GitHub Pages with MkDocs Material.
- Generated brand icon and standard README status badges.

### Changed

- Standardised CI on the shared `fjacquet/ci@v1` reusable workflows.
- Applied `ruff format` after the tool bump.

### Security

- Full `uv.lock` upgrade to clear Dependabot alerts.

## [0.1.1] - 2026-06-01

### Changed

- Pruned unused dependencies and consolidated the dev toolchain.

## [0.1.0] - 2026-06-01

First tagged release. The project itself dates from August 2025; by this tag it had:

- Document processing (text extraction, file handling) with Gemini/OpenAI LLM clients, flashcard generation and CSV export with summary reporting.
- A FastAPI web application (routers, session manager, typed dependency injection) and multi-language configuration with prompt templates.
- A configurable model system, integration tests, code-quality and security checks, and CI/Makefile alignment.
- Updated README and docs (API, configuration, examples, troubleshooting).
- A fix resolving web components uniformly through `app.state` dependency providers, and tests decoupled from a local `.env`.

[Unreleased]: https://github.com/fjacquet/anki-maker/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/fjacquet/anki-maker/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/fjacquet/anki-maker/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/fjacquet/anki-maker/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/fjacquet/anki-maker/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/fjacquet/anki-maker/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fjacquet/anki-maker/releases/tag/v0.1.0
