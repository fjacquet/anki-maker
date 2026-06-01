# Document to Anki CLI

Convert documents into high-quality [Anki](https://apps.ankiweb.net/) flashcards using AI-powered content analysis — from the command line or a web interface.

Feed it a PDF, Word, PowerPoint, Markdown, or text file (or a whole folder / ZIP), and it extracts the content, generates question-answer and cloze-deletion cards with an LLM, and exports an Anki-compatible CSV.

## Features

- **Multi-format input** — PDF, DOCX, PPTX, TXT, MD, plus folders and ZIP archives
- **AI flashcard generation** — question/answer and cloze cards via `litellm` (Google Gemini by default, OpenAI supported)
- **Configurable output language** — generate cards in English, French, Italian, or German regardless of the source language
- **Two interfaces** — an interactive CLI and a FastAPI web app
- **Anki-ready export** — CSV you can import directly into Anki

## Quick start

```bash
# Install with uv
uv sync

# Set your API key
export GEMINI_API_KEY=your-key-here

# Convert a document
uv run document-to-anki input.pdf --output flashcards.csv
```

## Documentation

<div class="grid cards" markdown>

- **[API Reference](API.md)** — Python API and CLI commands
- **[Configuration](CONFIGURATION.md)** — environment variables, models, languages
- **[Examples](EXAMPLES.md)** — end-to-end usage walkthroughs
- **[Troubleshooting](TROUBLESHOOTING.md)** — common issues and fixes
- **[Security](SECURITY.md)** — security model and reporting
- **[Migration](MIGRATION.md)** — upgrade notes

</div>

---

Source on [GitHub](https://github.com/fjacquet/anki-maker) · MIT Licensed
