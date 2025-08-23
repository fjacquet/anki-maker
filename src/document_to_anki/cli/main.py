"""
CLI main entry point for document-to-anki conversion.

This module provides the command-line interface using Click framework,
integrating with the core document processing and flashcard generation components.

The CLI supports:
- Single file, folder, and ZIP archive processing
- Interactive flashcard preview and editing
- Batch processing mode for automation
- Rich progress indicators and error handling
- Comprehensive logging and diagnostics

Usage Examples:
    # Basic conversion
    document-to-anki input.pdf

    # Batch processing
    document-to-anki batch-convert *.pdf --output-dir ./flashcards/

    # Automated mode (no interaction)
    document-to-anki input.pdf --no-preview --batch

Classes:
    CLIContext: Context object to hold CLI state and components

Functions:
    main: Main CLI entry point with version and help
    convert: Convert documents to flashcards with interactive management
    batch_convert: Process multiple documents in batch mode
    setup_logging: Configure loguru logging based on verbosity

Private Functions:
    _handle_edit_flashcard: Interactive flashcard editing
    _handle_delete_flashcard: Interactive flashcard deletion
    _handle_add_flashcard: Interactive flashcard creation
    _show_statistics: Display flashcard statistics
    _process_single_input: Process single input for batch mode
"""

import sys
from pathlib import Path

import click
from loguru import logger
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..config import ConfigurationError, LanguageConfig, LanguageValidationError, ModelConfig
from ..core.document_processor import DocumentProcessingError, DocumentProcessor
from ..core.flashcard_generator import FlashcardGenerationError, FlashcardGenerator


# Configure loguru logger
def _show_language_help(console: Console) -> None:
    """Display comprehensive language configuration help."""
    console.print("\n[bold blue]📚 Language Configuration Help[/bold blue]")
    console.print("┌─────────────────────────────────────────────────────────────┐")
    console.print("│ Set the CARDLANG environment variable to control the        │")
    console.print("│ language of generated flashcard content.                    │")
    console.print("└─────────────────────────────────────────────────────────────┘")

    console.print("\n[bold]Supported Languages:[/bold]")
    supported_languages = LanguageConfig.get_supported_languages_list()
    for lang in supported_languages:
        console.print(f"  • {lang}")

    console.print("\n[bold]Usage Examples:[/bold]")
    console.print("  export CARDLANG=english && document-to-anki input.pdf")
    console.print("  export CARDLANG=fr && document-to-anki input.pdf")
    console.print("  CARDLANG=italian document-to-anki batch-convert *.pdf")

    console.print("\n[bold]Configuration Methods:[/bold]")
    console.print("  1. Environment variable: export CARDLANG=french")
    console.print("  2. .env file: Add CARDLANG=french to your .env file")
    console.print("  3. Inline: CARDLANG=french document-to-anki input.pdf")

    console.print("\n[bold]Notes:[/bold]")
    console.print("  • Default language is English if CARDLANG is not set")
    console.print("  • Both full names (english) and codes (en) are supported")
    console.print("  • Language affects flashcard content, not CLI interface")
    console.print("  • Case-insensitive: 'English', 'ENGLISH', 'english' all work")


def setup_logging(verbose: bool = False) -> None:
    """
    Configure loguru logging based on verbosity level.

    Args:
        verbose: If True, enables DEBUG level logging with detailed format.
                If False, shows only INFO level and above with simple format.

    Note:
        This function removes the default loguru handler and adds a new one
        with appropriate formatting and level based on the verbose flag.
    """
    logger.remove()  # Remove default handler

    if verbose:
        # Verbose mode: detailed logging to stderr
        verbose_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        logger.add(sys.stderr, format=verbose_format, level="DEBUG")
    else:
        # Normal mode: only INFO and above to stderr
        logger.add(sys.stderr, format="<level>{level}</level>: {message}", level="INFO")


class CLIContext:
    """
    Context object to hold CLI state and components.

    This class encapsulates the CLI application state including:
    - Verbose logging flag
    - Rich console for formatted output
    - Document processor for file handling
    - Flashcard generator for AI-powered flashcard creation

    Attributes:
        verbose (bool): Whether verbose logging is enabled
        console (Console): Rich console for formatted output
        document_processor (DocumentProcessor): Handles document processing
        flashcard_generator (FlashcardGenerator): Manages flashcard operations
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize the CLI context with required components.

        Args:
            verbose: Enable verbose logging and detailed output

        Raises:
            ConfigurationError: If model configuration is invalid.
        """
        self.verbose = verbose
        self.console = Console()

        # Setup logging first
        setup_logging(verbose)

        # Validate model configuration early
        try:
            model = ModelConfig.validate_and_get_model()
            logger.info(f"Using model: {model}")
        except ConfigurationError as e:
            self.console.print(f"[red]❌ Model Configuration Error:[/red] {e}")
            self.console.print("\n[yellow]💡 How to fix this:[/yellow]")

            current_model = ModelConfig.get_model_from_env()
            if current_model not in ModelConfig.SUPPORTED_MODELS:
                supported = ", ".join(ModelConfig.get_supported_models())
                self.console.print(f"• Set MODEL environment variable to one of: {supported}")
                self.console.print(f"• Current MODEL value: '{current_model}'")
            else:
                required_key = ModelConfig.get_required_api_key(current_model)
                self.console.print(f"• Set the {required_key} environment variable")
                self.console.print("• Get your API key from the appropriate provider")

            self.console.print("\n[yellow]Example:[/yellow]")
            self.console.print("export MODEL=gemini/gemini-pro")
            self.console.print("export GEMINI_API_KEY=your_api_key_here")
            raise

        # Validate language configuration early
        try:
            from ..config import settings

            language_info = settings.get_language_info()
            logger.info(f"Using language: {language_info.name} ({language_info.code})")
        except (LanguageValidationError, ValueError) as e:
            self.console.print(f"[red]❌ Language Configuration Error:[/red] {e}")
            self.console.print("\n[yellow]💡 How to fix this:[/yellow]")

            supported_languages = LanguageConfig.get_supported_languages_list()
            self.console.print("• Set CARDLANG environment variable to a supported language:")
            for lang in supported_languages:
                self.console.print(f"  - {lang}")

            self.console.print("\n[yellow]Examples:[/yellow]")
            self.console.print("export CARDLANG=english     # English flashcards (default)")
            self.console.print("export CARDLANG=fr          # French flashcards")
            self.console.print("export CARDLANG=italian     # Italian flashcards")
            self.console.print("export CARDLANG=de          # German flashcards")

            self.console.print("\n[yellow]💡 Note:[/yellow]")
            self.console.print("• Language affects flashcard content, not the CLI interface")
            self.console.print("• If CARDLANG is not set, English is used by default")
            self.console.print("• Both full names and ISO codes are supported")
            self.console.print("• Run 'document-to-anki language-help' for detailed configuration help")
            raise

        self.document_processor = DocumentProcessor()
        self.flashcard_generator = FlashcardGenerator()


@click.group(invoke_without_command=True)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging output")
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def main(ctx: click.Context, verbose: bool, version: bool) -> None:
    """
    Document to Anki CLI - Convert documents into Anki flashcards using AI.

    Supports PDF, DOCX, TXT, and MD files. Can process single files, folders, or ZIP archives.

    LANGUAGE CONFIGURATION:
    Set the CARDLANG environment variable to control flashcard language:
    • English: CARDLANG=english or CARDLANG=en (default)
    • French: CARDLANG=french or CARDLANG=fr
    • Italian: CARDLANG=italian or CARDLANG=it
    • German: CARDLANG=german or CARDLANG=de

    Example: export CARDLANG=french && document-to-anki input.pdf
    """
    if version:
        click.echo("Document to Anki CLI v0.1.0")
        return

    # Create CLI context - this will validate model configuration
    ctx.ensure_object(dict)
    try:
        ctx.obj = CLIContext(verbose=verbose)
    except ConfigurationError:
        # Configuration error was already printed by CLIContext
        ctx.exit(1)

    # If no subcommand is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path), required=True)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output CSV file path (default: input_name_flashcards.csv)",
)
@click.option("--no-preview", is_flag=True, help="Skip flashcard preview and editing step")
@click.option("--batch", is_flag=True, help="Enable batch processing mode (no interactive prompts)")
@click.pass_obj
def convert(cli_ctx: CLIContext, input_path: Path, output: Path | None, no_preview: bool, batch: bool) -> None:
    """
    Convert documents to Anki flashcards.

    INPUT_PATH can be a single file, folder, or ZIP archive containing documents.
    Supported formats: PDF, DOCX, TXT, MD

    LANGUAGE CONFIGURATION:
    Flashcards are generated in the language specified by the CARDLANG environment variable.
    Supported languages: English (en), French (fr), Italian (it), German (de)
    Default: English if CARDLANG is not set

    Examples:
      document-to-anki input.pdf                    # English (default)
      CARDLANG=french document-to-anki input.pdf    # French flashcards
      CARDLANG=de document-to-anki input.pdf        # German flashcards
    """
    console = cli_ctx.console

    try:
        # Validate input path with detailed feedback
        if not cli_ctx.document_processor.validate_upload_path(input_path):
            console.print(f"[red]❌ Invalid input path:[/red] {input_path}")

            if not input_path.exists():
                console.print("[red]The specified path does not exist.[/red]")
            elif input_path.is_file():
                console.print(f"[red]Unsupported file format: {input_path.suffix}[/red]")
            elif input_path.is_dir():
                console.print("[red]No supported files found in the directory.[/red]")

            supported_formats = cli_ctx.document_processor.get_supported_formats()
            console.print(f"\n[yellow]💡 Supported formats:[/yellow] {', '.join(sorted(supported_formats))}")
            console.print("\n[yellow]💡 What you can do:[/yellow]")
            console.print("• Convert your files to a supported format")
            console.print("• Check the file path spelling")
            console.print("• Ensure files are not corrupted")
            console.print("• For folders, make sure they contain supported files")
            console.print("• For ZIP files, ensure they contain supported documents")
            sys.exit(1)

        # Determine output path if not provided
        if not output:
            if input_path.is_file():
                output = input_path.parent / f"{input_path.stem}_flashcards.csv"
            else:
                output = input_path / "flashcards.csv"

        # Ensure output directory exists
        output.parent.mkdir(parents=True, exist_ok=True)

        console.print(f"[bold blue]Processing:[/bold blue] {input_path}")
        console.print(f"[bold blue]Output:[/bold blue] {output}")

        # Step 1: Document Processing
        console.print("\n[bold]Step 1: Processing documents...[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            # Create progress task
            task = progress.add_task("Processing documents...", total=None)

            try:
                # Process documents
                doc_result = cli_ctx.document_processor.process_upload(input_path, progress, task)

                progress.update(task, completed=100, total=100)

                if not doc_result.success:
                    console.print("[red]Document processing failed:[/red]")
                    for error in doc_result.errors:
                        console.print(f"  • {error}")
                    sys.exit(1)

                # Display processing summary
                console.print(f"[green]✓[/green] Processed {doc_result.file_count} files")
                console.print(f"[green]✓[/green] Extracted {doc_result.total_characters:,} characters")

                if doc_result.warnings:
                    console.print("[yellow]Warnings:[/yellow]")
                    for warning in doc_result.warnings:
                        console.print(f"  • {warning}")

            except DocumentProcessingError as e:
                progress.stop()
                console.print(f"[red]❌ Document processing failed:[/red] {e}")

                # Provide actionable error guidance
                console.print("\n[yellow]💡 Troubleshooting tips:[/yellow]")
                console.print("• Ensure all files are in supported formats (PDF, DOCX, TXT, MD)")
                console.print("• Check that files are not corrupted or password-protected")
                console.print("• Verify file permissions allow reading")
                console.print("• Try processing files individually to identify problematic ones")
                console.print("• For ZIP files, ensure they contain supported document types")

                if "permission" in str(e).lower():
                    console.print("• [bold]Permission issue detected:[/bold] Check file access rights")
                elif "corrupted" in str(e).lower() or "invalid" in str(e).lower():
                    console.print("• [bold]File corruption detected:[/bold] Try with different files")
                elif "unsupported" in str(e).lower():
                    console.print("• [bold]Unsupported format:[/bold] Convert to PDF, DOCX, TXT, or MD")

                sys.exit(1)

        # Step 2: Flashcard Generation
        console.print("\n[bold]Step 2: Generating flashcards...[/bold]")

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Generating flashcards with AI...", total=None)

            try:
                # Generate flashcards
                generation_result = cli_ctx.flashcard_generator.generate_flashcards(
                    [doc_result.text_content], doc_result.source_files
                )

                progress.update(task, completed=100, total=100)

                if not generation_result.success:
                    console.print("[red]Flashcard generation failed:[/red]")
                    for error in generation_result.errors:
                        console.print(f"  • {error}")
                    sys.exit(1)

                # Display generation summary
                console.print(f"[green]✓[/green] Generated {generation_result.flashcard_count} flashcards")
                console.print(f"[green]✓[/green] Processing time: {generation_result.processing_time:.1f}s")

                # Show language information
                try:
                    from ..config import settings

                    language_info = settings.get_language_info()
                    console.print(f"[green]✓[/green] Language: {language_info.name} ({language_info.code})")
                except Exception:
                    console.print("[yellow]⚠️[/yellow] Language configuration may be invalid")

                if generation_result.warnings:
                    console.print("[yellow]Warnings:[/yellow]")
                    for warning in generation_result.warnings:
                        console.print(f"  • {warning}")

            except FlashcardGenerationError as e:
                progress.stop()
                console.print(f"[red]❌ Flashcard generation failed:[/red] {e}")

                # Provide actionable error guidance
                console.print("\n[yellow]💡 Troubleshooting tips:[/yellow]")
                console.print("• Check your internet connection for AI model access")
                console.print("• Verify API credentials are properly configured")
                console.print("• Try again in a few minutes (API rate limiting)")
                console.print("• Ensure document content is substantial enough for flashcard generation")
                console.print("• Check that extracted text contains meaningful educational content")

                if "api" in str(e).lower() or "key" in str(e).lower():
                    console.print("• [bold]API issue detected:[/bold] Check your API key configuration")
                elif "rate" in str(e).lower() or "limit" in str(e).lower():
                    console.print("• [bold]Rate limiting detected:[/bold] Wait before retrying")
                elif "network" in str(e).lower() or "connection" in str(e).lower():
                    console.print("• [bold]Network issue detected:[/bold] Check internet connectivity")
                elif "content" in str(e).lower() or "text" in str(e).lower():
                    console.print("• [bold]Content issue detected:[/bold] Ensure documents have readable text")
                elif "language" in str(e).lower():
                    console.print("• [bold]Language issue detected:[/bold] Check CARDLANG configuration")
                    console.print("• Run 'document-to-anki language-help' for language setup guidance")

                # Show current language configuration
                try:
                    from ..config import settings

                    language_info = settings.get_language_info()
                    console.print(
                        f"\n[blue]ℹ️  Current language setting:[/blue] {language_info.name} ({language_info.code})"
                    )
                    console.print("[dim]Use 'document-to-anki language-help' to change language settings[/dim]")
                except Exception:
                    console.print("\n[yellow]⚠️  Language configuration may be invalid[/yellow]")
                    console.print("[dim]Run 'document-to-anki language-help' for setup guidance[/dim]")

                sys.exit(1)

        # Step 3: Preview and Edit (unless skipped)
        if not no_preview and not batch:
            console.print("\n[bold]Step 3: Review and edit flashcards...[/bold]")

            # Show flashcard preview
            cli_ctx.flashcard_generator.preview_flashcards(console=console)

            # Interactive editing loop with enhanced menu
            while True:
                flashcard_count = len(cli_ctx.flashcard_generator.flashcards)
                console.print(f"\n[bold]📚 Flashcard Management Menu ({flashcard_count} cards)[/bold]")
                console.print("┌─────────────────────────────────────────────┐")
                console.print("│  [cyan]e[/cyan] - ✏️  Edit a flashcard                │")
                console.print("│  [cyan]d[/cyan] - 🗑️  Delete a flashcard              │")
                console.print("│  [cyan]a[/cyan] - ➕ Add a new flashcard             │")
                console.print("│  [cyan]p[/cyan] - 👀 Preview flashcards again        │")
                console.print("│  [cyan]s[/cyan] - 📊 Show statistics                 │")
                console.print("│  [cyan]c[/cyan] - ✅ Continue to export              │")
                console.print("│  [cyan]q[/cyan] - ❌ Quit without saving             │")
                console.print("└─────────────────────────────────────────────┘")

                choice = Prompt.ask(
                    "What would you like to do?", choices=["e", "d", "a", "p", "s", "c", "q"], default="c"
                )

                if choice == "e":
                    _handle_edit_flashcard(cli_ctx, console)
                elif choice == "d":
                    _handle_delete_flashcard(cli_ctx, console)
                elif choice == "a":
                    _handle_add_flashcard(cli_ctx, console)
                elif choice == "p":
                    cli_ctx.flashcard_generator.preview_flashcards(console=console)
                elif choice == "s":
                    _show_statistics(cli_ctx, console)
                elif choice == "c":
                    break
                elif choice == "q":
                    console.print("[yellow]Exiting without saving.[/yellow]")
                    sys.exit(0)

        # Step 4: Export to CSV
        console.print("\n[bold]Step 4: Exporting to CSV...[/bold]")

        # Show export confirmation prompt unless in batch mode
        if not batch:
            flashcard_count = len(cli_ctx.flashcard_generator.flashcards)
            console.print(f"[cyan]Ready to export {flashcard_count} flashcards to:[/cyan] {output}")

            if not Confirm.ask("Proceed with export?", default=True):
                console.print("[yellow]Export cancelled by user.[/yellow]")
                sys.exit(0)

        try:
            success, summary = cli_ctx.flashcard_generator.export_to_csv(output)

            if success:
                console.print(f"[green]✓[/green] Successfully exported {summary['exported_flashcards']} flashcards")  # noqa: E501
                console.print(f"[green]✓[/green] Output file: {summary['output_path']}")

                # Show detailed export summary
                if summary["qa_cards"] > 0:
                    console.print(f"  • Question-Answer cards: {summary['qa_cards']}")
                if summary["cloze_cards"] > 0:
                    console.print(f"  • Cloze deletion cards: {summary['cloze_cards']}")

                if summary["skipped_invalid"] > 0:
                    console.print(f"  • [yellow]Skipped invalid cards: {summary['skipped_invalid']}[/yellow]")

                if summary["file_size_bytes"] > 0:
                    if summary["file_size_bytes"] < 1024:
                        size_str = f"{summary['file_size_bytes']} bytes"
                    elif summary["file_size_bytes"] < 1024 * 1024:
                        size_str = f"{summary['file_size_bytes'] / 1024:.1f} KB"
                    else:
                        size_str = f"{summary['file_size_bytes'] / (1024 * 1024):.1f} MB"
                    console.print(f"  • File size: {size_str}")

                console.print("\n[bold green]🎉 Conversion completed successfully![/bold green]")

                # Show language information in success message
                try:
                    from ..config import settings

                    language_info = settings.get_language_info()
                    console.print(
                        f"[dim]Flashcards generated in {language_info.name}. "
                        f"Import the CSV file into Anki to start studying.[/dim]"
                    )
                except Exception:
                    console.print("[dim]Import the CSV file into Anki to start studying.[/dim]")

                # Show next steps
                console.print("\n[bold]Next steps:[/bold]")
                console.print("1. Open Anki on your computer")
                console.print("2. Go to File → Import")
                console.print(f"3. Select the exported file: {output}")
                console.print("4. Choose your deck and import settings")
                console.print("5. Start studying!")

                # Add language configuration tip
                console.print("\n[bold]💡 Language Tip:[/bold]")
                console.print("To generate flashcards in a different language next time:")
                console.print("• Run 'document-to-anki language-help' for configuration options")
                console.print("• Set CARDLANG environment variable (e.g., CARDLANG=french)")

            else:
                console.print("[red]❌ Export failed:[/red]")
                for error in summary.get("errors", []):
                    console.print(f"  • {error}")

                # Provide actionable error guidance
                console.print("\n[yellow]💡 Troubleshooting tips:[/yellow]")
                console.print("• Check that the output directory exists and is writable")
                console.print("• Ensure you have sufficient disk space")
                console.print("• Verify that no other application is using the output file")
                console.print("• Try a different output location")

                sys.exit(1)

        except PermissionError as e:
            console.print(f"[red]❌ Permission denied:[/red] Cannot write to {output}")
            console.print("\n[yellow]💡 Solutions:[/yellow]")
            console.print("• Choose a different output location")
            console.print("• Check file/folder permissions")
            console.print("• Run with appropriate privileges")
            console.print(f"• Error details: {e}")
            sys.exit(1)
        except FileNotFoundError as e:
            console.print(f"[red]❌ Directory not found:[/red] {output.parent}")
            console.print("\n[yellow]💡 Solutions:[/yellow]")
            console.print("• Create the output directory first")
            console.print("• Use an existing directory path")
            console.print("• Check the path spelling")
            console.print(f"• Error details: {e}")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]❌ Unexpected export error:[/red] {e}")
            console.print("\n[yellow]💡 Troubleshooting:[/yellow]")
            console.print("• Try again with a different output file")
            console.print("• Check available disk space")
            console.print("• Restart the application")
            console.print("• Report this issue if it persists")
            logger.exception("Unexpected error during CSV export")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️  Operation cancelled by user.[/yellow]")
        console.print("[dim]No files were modified. You can run the command again anytime.[/dim]")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during conversion")
        console.print(f"[red]❌ Unexpected error:[/red] {e}")

        # Provide comprehensive troubleshooting guidance
        console.print("\n[yellow]💡 General troubleshooting:[/yellow]")
        console.print("• Restart the application and try again")
        console.print("• Check available disk space and memory")
        console.print("• Verify internet connection for AI processing")
        console.print("• Try with smaller or different input files")
        console.print("• Update the application to the latest version")

        # Specific error type guidance
        error_str = str(e).lower()
        if "memory" in error_str or "ram" in error_str:
            console.print("\n[red]🧠 Memory issue detected:[/red]")
            console.print("• Close other applications to free up memory")
            console.print("• Try processing smaller files or fewer files at once")
            console.print("• Restart your computer if the issue persists")
        elif "network" in error_str or "connection" in error_str:
            console.print("\n[red]🌐 Network issue detected:[/red]")
            console.print("• Check your internet connection")
            console.print("• Try again in a few minutes")
            console.print("• Check if a firewall is blocking the application")
        elif "permission" in error_str or "access" in error_str:
            console.print("\n[red]🔒 Permission issue detected:[/red]")
            console.print("• Run with appropriate privileges")
            console.print("• Check file and folder permissions")
            console.print("• Ensure no other application is using the files")

        console.print(f"\n[dim]Error details logged for debugging: {e}[/dim]")
        sys.exit(1)


@main.command()
@click.argument("input_paths", nargs=-1, type=click.Path(exists=True, path_type=Path), required=True)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory for CSV files (default: current directory)",
)
@click.option("--batch", is_flag=True, help="Enable batch processing mode (no interactive prompts)")
@click.pass_obj
def batch_convert(cli_ctx: CLIContext, input_paths: tuple[Path, ...], output_dir: Path | None, batch: bool) -> None:
    """
    Convert multiple documents to Anki flashcards in batch mode.

    INPUT_PATHS can be multiple files, folders, or ZIP archives.
    Each input will generate a separate CSV file.

    LANGUAGE CONFIGURATION:
    All flashcards are generated in the language specified by CARDLANG environment variable.
    Supported: English (en), French (fr), Italian (it), German (de)

    Example:
      CARDLANG=italian document-to-anki batch-convert *.pdf --output-dir ./cards/
    """
    console = cli_ctx.console

    if not input_paths:
        console.print("[red]Error:[/red] No input paths provided")
        sys.exit(1)

    # Set default output directory
    if not output_dir:
        output_dir = Path.cwd()

    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold blue]Batch processing {len(input_paths)} inputs...[/bold blue]")
    console.print(f"[bold blue]Output directory:[/bold blue] {output_dir}")

    successful_conversions = 0
    failed_conversions = 0

    for i, input_path in enumerate(input_paths, 1):
        console.print(f"\n[bold]Processing {i}/{len(input_paths)}: {input_path}[/bold]")

        try:
            # Validate input path
            if not cli_ctx.document_processor.validate_upload_path(input_path):
                console.print(f"[red]✗[/red] Skipping invalid input: {input_path}")
                failed_conversions += 1
                continue

            # Determine output path
            if input_path.is_file():
                output_file = output_dir / f"{input_path.stem}_flashcards.csv"
            else:
                output_file = output_dir / f"{input_path.name}_flashcards.csv"

            # Process single input (reuse convert logic but without interactive parts)
            success = _process_single_input(cli_ctx, input_path, output_file, console)

            if success:
                successful_conversions += 1
                console.print(f"[green]✓[/green] Completed: {output_file}")
            else:
                failed_conversions += 1
                console.print(f"[red]✗[/red] Failed: {input_path}")

        except KeyboardInterrupt:
            console.print("\n[yellow]Batch processing cancelled by user.[/yellow]")
            break
        except Exception as e:
            logger.exception(f"Error processing {input_path}")
            console.print(f"[red]✗[/red] Error processing {input_path}: {e}")
            failed_conversions += 1

    # Show batch summary
    console.print("\n[bold]Batch Processing Summary:[/bold]")
    console.print(f"[green]✓[/green] Successful: {successful_conversions}")
    console.print(f"[red]✗[/red] Failed: {failed_conversions}")
    console.print(f"[blue]Total:[/blue] {len(input_paths)}")

    if failed_conversions > 0:
        sys.exit(1)


@main.command()
@click.pass_obj
def language_help(cli_ctx: CLIContext) -> None:
    """
    Show detailed language configuration help and examples.

    Displays supported languages, configuration methods, and usage examples
    for setting up flashcard generation in different languages.
    """
    _show_language_help(cli_ctx.console)


def _process_single_input(cli_ctx: CLIContext, input_path: Path, output_path: Path, console: Console) -> bool:
    """
    Process a single input for batch mode.

    Returns:
        True if processing was successful, False otherwise
    """
    try:
        # Document processing
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Processing documents...", total=None)

            doc_result = cli_ctx.document_processor.process_upload(input_path, progress, task)

            if not doc_result.success:
                for error in doc_result.errors:
                    console.print(f"  [red]Error:[/red] {error}")
                return False

        # Flashcard generation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Generating flashcards...", total=None)

            generation_result = cli_ctx.flashcard_generator.generate_flashcards(
                [doc_result.text_content], doc_result.source_files
            )

            if not generation_result.success:
                for error in generation_result.errors:
                    console.print(f"  [red]Error:[/red] {error}")
                return False

        # Export
        success, summary = cli_ctx.flashcard_generator.export_to_csv(output_path)

        if not success:
            for error in summary["errors"]:
                console.print(f"  [red]Error:[/red] {error}")
            return False

        console.print(f"  Generated {summary['exported_flashcards']} flashcards")
        return True

    except Exception as e:
        console.print(f"  [red]Error:[/red] {e}")
        return False


def _handle_edit_flashcard(cli_ctx: CLIContext, console: Console) -> None:
    """Handle interactive flashcard editing with comprehensive validation and confirmation."""
    flashcards = cli_ctx.flashcard_generator.flashcards

    if not flashcards:
        console.print("[yellow]No flashcards to edit.[/yellow]")
        console.print("[dim]Add some flashcards first or generate them from documents.[/dim]")
        return

    # Show available flashcards with short IDs and validation status
    console.print("\n[bold]Available flashcards:[/bold]")
    for i, card in enumerate(flashcards, 1):
        short_id = card.id[:8]
        question_preview = (card.question[:50] + "...") if len(card.question) > 50 else card.question
        status_icon = "✓" if card.validate_content() else "⚠️"
        console.print(f"  {i}. [{short_id}] {status_icon} {question_preview}")

    # Get flashcard selection with validation
    try:
        while True:
            selection = Prompt.ask("Enter flashcard number or ID (or 'cancel' to go back)", default="1")

            if selection.lower() in ["cancel", "c", "back", "b"]:
                console.print("[yellow]Edit cancelled.[/yellow]")
                return

            target_card = None

            # Try to parse as number first
            try:
                index = int(selection) - 1
                if 0 <= index < len(flashcards):
                    target_card = flashcards[index]
                    break
                else:
                    console.print(f"[red]Invalid number. Please enter 1-{len(flashcards)}.[/red]")
                    continue
            except ValueError:
                # Try to find by ID
                target_card = cli_ctx.flashcard_generator.get_flashcard_by_id(selection)
                if target_card:
                    break
                else:
                    console.print("[red]Flashcard ID not found. Try the number instead.[/red]")
                    continue

        # Show current content with formatting
        console.print(f"\n[bold]Editing flashcard {target_card.id[:8]}...[/bold]")
        console.print(f"[cyan]Type:[/cyan] {target_card.card_type.upper()}")
        console.print(f"[cyan]Source:[/cyan] {target_card.source_file or 'Manual'}")
        console.print(f"[cyan]Current Question:[/cyan]\n{target_card.question}")
        console.print(f"[cyan]Current Answer:[/cyan]\n{target_card.answer}")

        # Confirm edit intention
        if not Confirm.ask("\nProceed with editing this flashcard?", default=True):
            console.print("[yellow]Edit cancelled.[/yellow]")
            return

        # Get new content with validation
        console.print("\n[bold]Enter new content (press Enter to keep current):[/bold]")

        new_question = Prompt.ask("New question", default=target_card.question)
        new_answer = Prompt.ask("New answer", default=target_card.answer)

        # Show preview of changes
        if new_question != target_card.question or new_answer != target_card.answer:
            console.print("\n[bold]Preview of changes:[/bold]")
            if new_question != target_card.question:
                console.print(f"[yellow]Question will change to:[/yellow]\n{new_question}")
            if new_answer != target_card.answer:
                console.print(f"[yellow]Answer will change to:[/yellow]\n{new_answer}")

            # Final confirmation
            if not Confirm.ask("\nSave these changes?", default=True):
                console.print("[yellow]Changes discarded.[/yellow]")
                return
        else:
            console.print("[dim]No changes made.[/dim]")
            return

        # Apply edit with error handling
        try:
            success, message = cli_ctx.flashcard_generator.edit_flashcard(target_card.id, new_question, new_answer)

            if success:
                console.print(f"[green]✓[/green] {message}")
            else:
                console.print(f"[red]❌[/red] {message}")
                console.print("\n[yellow]💡 Edit tips:[/yellow]")
                console.print("• Ensure both question and answer are not empty")
                console.print("• For cloze cards, include {{c1::...}} format")
                console.print("• Keep content under 65,000 characters")

        except Exception as e:
            console.print(f"[red]❌ Edit failed:[/red] {e}")
            console.print("\n[yellow]💡 Try again with different content.[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Edit cancelled.[/yellow]")


def _handle_delete_flashcard(cli_ctx: CLIContext, console: Console) -> None:
    """Handle interactive flashcard deletion with comprehensive confirmation."""
    flashcards = cli_ctx.flashcard_generator.flashcards

    if not flashcards:
        console.print("[yellow]No flashcards to delete.[/yellow]")
        console.print("[dim]Generate or add flashcards first.[/dim]")
        return

    # Show available flashcards with status
    console.print("\n[bold]Available flashcards:[/bold]")
    for i, card in enumerate(flashcards, 1):
        short_id = card.id[:8]
        question_preview = (card.question[:50] + "...") if len(card.question) > 50 else card.question
        status_icon = "✓" if card.validate_content() else "⚠️"
        console.print(f"  {i}. [{short_id}] {status_icon} {question_preview}")

    try:
        while True:
            selection = Prompt.ask("Enter flashcard number or ID to delete (or 'cancel' to go back)")

            if selection.lower() in ["cancel", "c", "back", "b"]:
                console.print("[yellow]Delete cancelled.[/yellow]")
                return

            target_card = None

            # Try to parse as number first
            try:
                index = int(selection) - 1
                if 0 <= index < len(flashcards):
                    target_card = flashcards[index]
                    break
                else:
                    console.print(f"[red]Invalid number. Please enter 1-{len(flashcards)}.[/red]")
                    continue
            except ValueError:
                # Try to find by ID
                target_card = cli_ctx.flashcard_generator.get_flashcard_by_id(selection)
                if target_card:
                    break
                else:
                    console.print("[red]Flashcard ID not found. Try the number instead.[/red]")
                    continue

        # Show detailed flashcard info before deletion
        console.print("\n[bold red]⚠️  Confirm Deletion[/bold red]")
        console.print(f"[cyan]ID:[/cyan] {target_card.id[:8]}...")
        console.print(f"[cyan]Type:[/cyan] {target_card.card_type.upper()}")
        console.print(f"[cyan]Source:[/cyan] {target_card.source_file or 'Manual'}")

        question_preview = (
            (target_card.question[:150] + "...") if len(target_card.question) > 150 else target_card.question
        )
        console.print(f"[cyan]Question:[/cyan] {question_preview}")

        # Multiple confirmation steps for safety
        console.print("\n[red]This action cannot be undone![/red]")

        if not Confirm.ask("Are you sure you want to delete this flashcard?", default=False):
            console.print("[yellow]Deletion cancelled.[/yellow]")
            return

        # Final confirmation
        if not Confirm.ask("Final confirmation - permanently delete this flashcard?", default=False):
            console.print("[yellow]Deletion cancelled.[/yellow]")
            return

        # Perform deletion with error handling
        try:
            success, message = cli_ctx.flashcard_generator.delete_flashcard(target_card.id)

            if success:
                console.print(f"[green]✓[/green] {message}")
                remaining_count = len(cli_ctx.flashcard_generator.flashcards)
                console.print(f"[dim]{remaining_count} flashcards remaining.[/dim]")
            else:
                console.print(f"[red]❌[/red] {message}")
                console.print("\n[yellow]💡 If this persists, try restarting the application.[/yellow]")

        except Exception as e:
            console.print(f"[red]❌ Delete failed:[/red] {e}")
            console.print("\n[yellow]💡 The flashcard may have already been removed.[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Delete cancelled.[/yellow]")


def _handle_add_flashcard(cli_ctx: CLIContext, console: Console) -> None:
    """Handle interactive flashcard addition with validation and guidance."""
    try:
        console.print("\n[bold]Add new flashcard:[/bold]")
        console.print("[dim]Create a custom flashcard to add to your collection.[/dim]")

        # Get card type first to provide appropriate guidance
        card_type = Prompt.ask("Card type", choices=["qa", "cloze"], default="qa")

        # Provide guidance based on card type
        if card_type == "qa":
            console.print("\n[cyan]Question-Answer Card Tips:[/cyan]")
            console.print("• Write a clear, specific question")
            console.print("• Provide a concise, accurate answer")
            console.print("• Example: Q: 'What is the capital of France?' A: 'Paris'")
        else:
            console.print("\n[cyan]Cloze Deletion Card Tips:[/cyan]")
            console.print("• Use {{c1::text}} to mark what should be hidden")
            console.print("• Example: 'The capital of {{c1::France}} is {{c1::Paris}}'")
            console.print("• You can put the cloze in either question or answer field")

        # Get question with validation loop
        while True:
            question = Prompt.ask("\nQuestion", default="")
            if question.strip():
                break
            console.print("[red]Question cannot be empty. Please try again.[/red]")

        # Get answer with validation loop
        while True:
            answer = Prompt.ask("Answer", default="")
            if answer.strip():
                break
            console.print("[red]Answer cannot be empty. Please try again.[/red]")

        # Validate cloze format if needed
        if card_type == "cloze":
            if "{{c1::" not in question and "{{c1::" not in answer:
                console.print("\n[yellow]⚠️  Cloze format not detected![/yellow]")
                console.print("Cloze cards should contain {{c1::...}} format.")

                if not Confirm.ask("Continue anyway?", default=False):
                    console.print("[yellow]Add cancelled.[/yellow]")
                    return

        # Show preview before adding
        console.print("\n[bold]Preview:[/bold]")
        console.print(f"[cyan]Type:[/cyan] {card_type.upper()}")
        console.print(f"[cyan]Question:[/cyan] {question}")
        console.print(f"[cyan]Answer:[/cyan] {answer}")

        # Confirm addition
        if not Confirm.ask("\nAdd this flashcard?", default=True):
            console.print("[yellow]Add cancelled.[/yellow]")
            return

        # Add flashcard with error handling
        try:
            flashcard, message = cli_ctx.flashcard_generator.add_flashcard(
                question, answer, card_type, source_file="Manual"
            )

            if flashcard:
                console.print(f"[green]✓[/green] {message}")
                total_count = len(cli_ctx.flashcard_generator.flashcards)
                console.print(f"[dim]Total flashcards: {total_count}[/dim]")
            else:
                console.print(f"[red]❌[/red] {message}")
                console.print("\n[yellow]💡 Add tips:[/yellow]")
                console.print("• Ensure both question and answer are not empty")
                console.print("• For cloze cards, include {{c1::...}} format")
                console.print("• Keep content under 65,000 characters")

        except Exception as e:
            console.print(f"[red]❌ Add failed:[/red] {e}")
            console.print("\n[yellow]💡 Try again with different content.[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Add cancelled.[/yellow]")


def _show_statistics(cli_ctx: CLIContext, console: Console) -> None:
    """Show comprehensive flashcard statistics with rich formatting."""
    stats = cli_ctx.flashcard_generator.get_statistics()

    # Create a statistics table
    table = Table(title="📊 Flashcard Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", width=25)
    table.add_column("Count", style="white", width=10)
    table.add_column("Details", style="dim", width=30)

    # Add basic statistics
    table.add_row("Total Flashcards", str(stats["total_count"]), "All cards in collection")
    table.add_row("Valid Cards", str(stats["valid_count"]), "Ready for export")

    if stats["invalid_count"] > 0:
        table.add_row("Invalid Cards", str(stats["invalid_count"]), "[red]Need attention[/red]")

    table.add_row("Question-Answer", str(stats["qa_count"]), "Standard Q&A format")
    table.add_row("Cloze Deletion", str(stats["cloze_count"]), "Fill-in-the-blank format")
    table.add_row("Source Files", str(len(stats["source_files"])), "Documents processed")

    console.print(table)

    # Show source files if any
    if stats["source_files"]:
        console.print("\n[bold]📁 Source Files:[/bold]")
        for i, source in enumerate(stats["source_files"], 1):
            # Count cards from this source
            cards_from_source = len(cli_ctx.flashcard_generator.get_flashcards_by_source(source))
            console.print(f"  {i}. {source} ({cards_from_source} cards)")

    # Show quality assessment
    if stats["total_count"] > 0:
        valid_percentage = (stats["valid_count"] / stats["total_count"]) * 100
        console.print(f"\n[bold]✅ Quality Score:[/bold] {valid_percentage:.1f}% valid")

        if valid_percentage == 100:
            console.print("[green]🎉 Excellent! All flashcards are valid and ready for export.[/green]")
        elif valid_percentage >= 90:
            console.print("[green]👍 Great! Most flashcards are valid.[/green]")
        elif valid_percentage >= 75:
            console.print("[yellow]⚠️  Good, but some flashcards may need attention.[/yellow]")
        else:
            console.print("[red]❗ Several flashcards need fixing before export.[/red]")

    # Show recommendations
    if stats["total_count"] == 0:
        console.print("\n[yellow]💡 No flashcards yet. Generate some from documents or add manually![/yellow]")
    elif stats["invalid_count"] > 0:
        console.print(f"\n[yellow]💡 Consider editing the {stats['invalid_count']} invalid flashcard(s).[/yellow]")
    elif stats["total_count"] < 5:
        console.print("\n[yellow]💡 Consider adding more flashcards for better study sessions.[/yellow]")
    else:
        console.print(f"\n[green]💡 You have {stats['total_count']} flashcards ready for studying![/green]")


if __name__ == "__main__":
    main()
