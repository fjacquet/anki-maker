# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`document-to-anki-cli` (package import name: `document_to_anki`) converts documents (PDF, DOCX, PPTX, TXT, MD, plus folders and ZIP archives) into Anki-compatible flashcards using LLMs via `litellm`. It ships **two entry points** over the same core:

- CLI: `document-to-anki` / `anki-maker` → `document_to_anki.cli.main:main` (Click + Rich)
- Web: `document-to-anki-web` / `anki-maker-web` → `document_to_anki.web.app:run_server` (FastAPI)

## Commands

Everything runs through `uv` and the `Makefile`. Prefer Make targets — they wrap `uv run` and set up env checks.

```bash
make install-dev        # uv sync --all-extras (dev setup)
make test               # uv run pytest (full suite, coverage gate --cov-fail-under=65)
make test-fast          # pytest -x (fail-fast)
make test-integration   # pytest -m integration
make lint               # ruff format + ruff check --fix
make format-check       # ruff format --check (read-only)
make type-check         # mypy src/document_to_anki (strict config)
make security           # bandit -r src/document_to_anki
make quality            # ruff + mypy + bandit + pip-audit + security_validation.py
make run-cli            # run CLI in dev mode
make run-web            # run web server in dev mode
make pre-commit         # quality + test (run before committing)
```

Run a single test:

```bash
uv run pytest tests/test_llm_client.py::TestClassName::test_method -v
uv run pytest tests/test_web_integration.py -k "upload" -v
```

Test markers (defined in `pyproject.toml`): `slow`, `integration`, `unit`, `web`, `cli`, `performance`. Performance tests live in `performance_tests/` and run separately (`make test-performance`), not under the default `testpaths=["tests"]`.

### Testing without API keys

LLM calls are gated by env. Set `MOCK_LLM_RESPONSES` to run tests/CI without a real `GEMINI_API_KEY` (see `make check-env`). Tests are async-heavy — `pytest-asyncio` is configured.

Web tests use the `web_client` fixture (`tests/conftest.py`), which installs deterministic offline doubles into `app.state` (a real `FlashcardGenerator` with a mocked LLM client — genuine validate/export logic, no network) and clears `app.dependency_overrides` on teardown. To inject behavior in a web test, configure the `app.state.*` object or override a provider via `app.dependency_overrides[get_flashcard_generator]` — do **not** monkeypatch `web.app.*` module globals (routes read `app.state`, so those patches are dead). `CARDLANG`/`MODEL` come from `.env` locally; CI has no `.env`, so `MODEL` falls back to the supported default `gemini/gemini-2.5-flash` (`ModelConfig.DEFAULT_MODEL`). An invalid `MODEL` makes any model-validating path (web lifespan, `FlashcardGenerator()` init, CLI `main`) raise `ConfigurationError`.

## Architecture

The flow is **document → text → chunks → LLM → flashcards → CSV**, shared by both CLI and web frontends.

### Layers (`src/document_to_anki/`)

- **`config.py`** — The single source of truth for configuration. Contains `Settings` (pydantic-settings, loaded from `.env`), plus three config helper classes that gate behavior:
  - `ModelConfig` — validates `MODEL` env var, maps each model to its required API key (`GEMINI_API_KEY` vs `OPENAI_API_KEY`). Use `ModelConfig.validate_and_get_model()`.
  - `LanguageConfig` — validates `CARDLANG` (english/french/italian/german, or ISO codes en/fr/it/de). Drives which prompt variant is used. Raises `LanguageValidationError` listing supported languages.
  - Custom exceptions `ConfigurationError`, `LanguageValidationError` propagate up to both CLI and web error handlers.

- **`core/`** — business logic, frontend-agnostic:
  - `document_processor.py` (`DocumentProcessor`) — orchestrates upload handling (single file / folder / ZIP), delegates extraction, consolidates text. Returns `DocumentProcessingResult`.
  - `llm_client.py` (`LLMClient`) — wraps `litellm`. Handles text chunking for token limits, prompt construction (per language + detected content type), retry on API calls, JSON response parsing with multiple fallback strategies (`_clean_json_response` → `_attempt_json_fix` → `_fallback_parse`), and **language validation of generated output**. Has both async and sync paths.
  - `flashcard_generator.py` (`FlashcardGenerator`) — orchestrates generation via `LLMClient`, manages the in-memory flashcard collection (add/edit/delete/preview), and CSV export. Holds flashcard state for the CLI session.
  - `prompt_templates.py` (`PromptTemplates`) — language- and content-type-specific prompt strings.

- **`models/flashcard.py`** — `Flashcard` (pydantic) with `card_type` ∈ `{"qa", "cloze"}`, cloze-format validation, and `to_csv_row()`. `ProcessingResult` aggregates errors/warnings/counts. Flashcards get auto-generated UUIDs via `Flashcard.create(...)`.

- **`utils/`** — text extraction. `text_extractor.py` (`TextExtractor`) is a **dispatcher**: `_EXTRACTOR_MAP` routes by file extension to per-format modules (`pdf_extractor`, `docx_extractor`, `pptx_extractor`, `text_extractor_common` for txt/md). To add a format, add an extractor function and register it in both `SUPPORTED_FORMATS` and `_EXTRACTOR_MAP`. `file_handler.py` handles upload/ZIP/folder file resolution and validation. All raise `TextExtractionError` / `FileHandlingError`.

- **`web/`** — FastAPI app (`app.py`) wired from three routers: `routes_upload.py`, `routes_flashcards.py`, `routes_export.py` (all under `/api/...`, keyed by `session_id`). `session_manager.py` holds per-session flashcard state (the web equivalent of the CLI's in-memory collection). `schemas.py` defines request/response pydantic models. `app.py` registers exception handlers that translate the core exceptions (`DocumentProcessingError`, `FlashcardGenerationError`, `LanguageValidationError`) into HTTP responses, plus security-headers/CORS/trusted-host middleware.
  - **`dependencies.py` is the single source of truth for shared web components.** `get_session_manager`, `get_document_processor`, and `get_flashcard_generator` each read from `request.app.state.*` (populated by the lifespan handler, or by the test `web_client` fixture). Routes inject them via `Annotated[..., Depends(...)]`. Do **not** reintroduce module-level singletons for these — the providers must resolve through `app.state` so a single instance is shared and tests can substitute components via `app.dependency_overrides`. The background task `process_files_background` reads the same `app.state.*` attributes directly (it runs outside the request scope). `settings` is imported per-module (`from ..config import settings`) in both `app.py` and `routes_upload.py`, so language-dependent behavior reads the module-local `settings` of whichever module serves the route (e.g. `/` is served by `routes_upload`, `/api/config/language` by `app`).

- **`cli/main.py`** — Click commands (`convert`, `batch_convert`, `language_help`) with Rich progress/tables. `CLIContext` holds the processor + generator instances for an interactive session (preview/edit/delete/add loop).

### Key cross-cutting concerns

- **Language is end-to-end**: source documents can be in any language; `CARDLANG` controls the *output* language. The setting flows config → `LLMClient` prompt selection → post-generation language validation. When touching generation, preserve this chain.
- **Two execution paths** (async + sync) exist in `LLMClient` and `FlashcardGenerator` — keep them in sync when changing generation logic.
- Logging is via `loguru` throughout (not stdlib `logging`).

## Conventions

- Python ≥ 3.12. Line length **120**. Ruff rules: `E, F, B, I, UP` (`F841` ignored). Double quotes, space indent.
- mypy is **strict** (`disallow_untyped_defs`, `warn_unused_ignores`, etc.) for `src/document_to_anki`. Third-party stubs are waived via overrides in `pyproject.toml`. FastAPI dependencies use `Annotated[...]` injection (see recent refactor).
- Coverage gate is **65%** (`--cov-fail-under=65`); CI fails below it.
- Config is centralized in `config.py` — read settings from `settings` / the `*Config` classes rather than reading `os.environ` directly elsewhere.

## Notes

- `tests/test_end_to_end_language_generation.poy` has a `.poy` extension (not `.py`) so it is **not** collected by pytest — likely intentional/disabled; don't assume it runs.
- Many root-level artifacts (`coverage.xml`, `*_report.{json,md}`, `test_*.csv`, `ci_comparison_results.json`) are generated outputs, not source.
