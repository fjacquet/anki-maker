# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Standing practice: on each release, move `[Unreleased]` to a dated `[X.Y.Z]`
section rather than letting it accumulate indefinitely.

## [Unreleased]

### Changed

- Refreshed `uv.lock` (2026-10-02 dependency sweep).
- The Security workflow now also runs on a weekly schedule and can be triggered manually.

### Security

- `nltk` advisory [GHSA-8mgp-746c-j5xp](https://github.com/advisories/GHSA-8mgp-746c-j5xp)
  has no upstream fix yet; the locked version is the latest available and the alert remains open.

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

[Unreleased]: https://github.com/fjacquet/anki-maker/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/fjacquet/anki-maker/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/fjacquet/anki-maker/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/fjacquet/anki-maker/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fjacquet/anki-maker/releases/tag/v0.1.0
