"""
FlashcardGenerator for managing flashcard creation and editing.

This module provides the FlashcardGenerator class that orchestrates the creation,
editing, and management of flashcards using the LLMClient and Flashcard models.
"""

import time
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..config import ConfigurationError
from ..models.flashcard import Flashcard, ProcessingResult
from .llm_client import LLMClient


class FlashcardGenerationError(Exception):
    """Exception raised when flashcard generation fails."""

    pass


class FlashcardGenerator:
    """
    Manages flashcard creation, editing, and export functionality.

    This class serves as the main orchestrator for flashcard operations,
    integrating with the LLMClient for generation and providing methods
    for editing, validation, and export.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """
        Initialize the FlashcardGenerator with ModelConfig-configured LLMClient.

        Args:
            llm_client: Optional LLMClient instance. If None, creates one with ModelConfig.

        Raises:
            ConfigurationError: If model configuration is invalid.
        """
        try:
            self.llm_client = llm_client or LLMClient()  # LLMClient will use ModelConfig
            self._flashcards: list[Flashcard] = []
            logger.info(f"FlashcardGenerator initialized with model: {self.llm_client.get_current_model()}")
        except ConfigurationError as e:
            logger.error(f"Failed to initialize FlashcardGenerator: {e}")
            raise

    @property
    def flashcards(self) -> list[Flashcard]:
        """Get the current list of flashcards."""
        return self._flashcards.copy()

    def generate_flashcards(self, text_content: list[str], source_files: list[str] | None = None) -> ProcessingResult:
        """
        Generate flashcards from text content using LLM.

        Args:
            text_content: List of text strings to process
            source_files: Optional list of source file names corresponding to text_content

        Returns:
            ProcessingResult containing generated flashcards and processing metadata
        """
        start_time = time.time()
        all_flashcards = []
        errors = []
        warnings: list[str] = []

        if not text_content:
            errors.append("No text content provided for flashcard generation")
            return ProcessingResult(
                flashcards=[],
                source_files=source_files or [],
                processing_time=time.time() - start_time,
                errors=errors,
                warnings=warnings,
            )

        logger.info(f"Starting flashcard generation for {len(text_content)} text chunks")

        # Process each text chunk
        for i, text in enumerate(text_content):
            if not text or not text.strip():
                warnings.append(f"Skipping empty text chunk {i + 1}")
                continue

            try:
                source_file = source_files[i] if source_files and i < len(source_files) else None
                chunk_flashcards = self._generate_flashcards_from_single_text(text, source_file, i + 1, warnings)
                all_flashcards.extend(chunk_flashcards)

            except Exception as e:
                error_msg = f"Failed to generate flashcards from text chunk {i + 1}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        # Validate generated flashcards
        valid_flashcards = []
        for flashcard in all_flashcards:
            if flashcard.validate_content():
                valid_flashcards.append(flashcard)
            else:
                warnings.append(f"Invalid flashcard generated: {flashcard.question[:50]}...")

        # Update internal flashcard list
        self._flashcards = valid_flashcards

        processing_time = time.time() - start_time

        result = ProcessingResult(
            flashcards=valid_flashcards,
            source_files=source_files or [],
            processing_time=processing_time,
            errors=errors,
            warnings=warnings,
        )

        logger.info(f"Flashcard generation completed: {result.get_summary()}")
        return result

    def _generate_flashcards_from_single_text(
        self, text: str, source_file: str | None, chunk_number: int, warnings: list[str] | None = None
    ) -> list[Flashcard]:
        """
        Generate flashcards from a single text chunk.

        Args:
            text: Text content to process
            source_file: Source file name
            chunk_number: Chunk number for logging
            warnings: Optional list to collect warnings

        Returns:
            List of generated Flashcard objects
        """
        logger.info(f"Processing text chunk {chunk_number} ({len(text)} characters)")

        try:
            # Use the LLM client to generate flashcard data
            flashcard_data_list = self.llm_client.generate_flashcards_from_text_sync(text)

            if not flashcard_data_list:
                logger.warning(f"No flashcards generated from chunk {chunk_number}")
                return []

            # Convert to Flashcard objects
            flashcards = []
            for data in flashcard_data_list:
                try:
                    flashcard = Flashcard.create(
                        question=data["question"],
                        answer=data["answer"],
                        card_type=data["card_type"],
                        source_file=source_file,
                    )
                    flashcards.append(flashcard)

                except KeyError as e:
                    warning_msg = f"Malformed flashcard data missing key {e}: {data}"
                    logger.warning(warning_msg)
                    if warnings is not None:
                        warnings.append(warning_msg)
                    continue
                except Exception as e:
                    warning_msg = f"Failed to create flashcard from data {data}: {e}"
                    logger.warning(warning_msg)
                    if warnings is not None:
                        warnings.append(warning_msg)
                    continue

            logger.info(f"Generated {len(flashcards)} flashcards from chunk {chunk_number}")
            return flashcards

        except Exception as e:
            logger.error(f"LLM generation failed for chunk {chunk_number}: {e}")
            raise FlashcardGenerationError(f"Failed to generate flashcards: {e}") from e

    def preview_flashcards(self, flashcards: list[Flashcard] | None = None, console: Console | None = None) -> None:
        """
        Display a rich-formatted preview of flashcards for CLI.

        Args:
            flashcards: Optional list of flashcards to preview. Uses internal list if None.
            console: Optional Rich Console instance. Creates one if None.
        """
        cards_to_preview = flashcards or self._flashcards
        console = console or Console()

        if not cards_to_preview:
            console.print("[yellow]No flashcards to preview.[/yellow]")
            return

        # Create a table for flashcard overview
        table = Table(title=f"Flashcard Preview ({len(cards_to_preview)} cards)")
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Type", style="magenta", width=8)
        table.add_column("Question", style="white", width=40)
        table.add_column("Answer", style="green", width=40)
        table.add_column("Source", style="blue", width=20)

        for card in cards_to_preview:
            # Truncate long text for table display
            question_preview = (card.question[:37] + "...") if len(card.question) > 40 else card.question
            answer_preview = (card.answer[:37] + "...") if len(card.answer) > 40 else card.answer
            source_preview = (
                (card.source_file or "Unknown")[:17] + "..."
                if card.source_file and len(card.source_file) > 20
                else (card.source_file or "Unknown")
            )

            table.add_row(card.id[:8] + "...", card.card_type.upper(), question_preview, answer_preview, source_preview)

        console.print(table)

        # Display detailed view of each flashcard
        console.print("\n[bold]Detailed View:[/bold]")
        for i, card in enumerate(cards_to_preview, 1):
            # Create a panel for each flashcard
            card_content = Text()
            card_content.append("Question: ", style="bold cyan")
            card_content.append(f"{card.question}\n\n", style="white")
            card_content.append("Answer: ", style="bold green")
            card_content.append(f"{card.answer}\n\n", style="white")
            card_content.append("Source: ", style="bold blue")
            card_content.append(f"{card.source_file or 'Unknown'}", style="blue")

            panel_title = f"Card {i} [{card.card_type.upper()}] - ID: {card.id[:8]}..."
            panel = Panel(
                card_content,
                title=panel_title,
                border_style="bright_blue" if card.validate_content() else "red",
                expand=False,
            )
            console.print(panel)

    def get_flashcard_preview_text(self, flashcards: list[Flashcard] | None = None) -> str:
        """
        Get a plain text preview of flashcards (for non-CLI contexts).

        Args:
            flashcards: Optional list of flashcards to preview. Uses internal list if None.

        Returns:
            Formatted string representation of flashcards
        """
        cards_to_preview = flashcards or self._flashcards

        if not cards_to_preview:
            return "No flashcards to preview."

        preview_lines = [f"=== Flashcard Preview ({len(cards_to_preview)} cards) ===\n"]

        for i, card in enumerate(cards_to_preview, 1):
            status = "✓" if card.validate_content() else "✗"
            preview_lines.extend(
                [
                    f"Card {i} [{card.card_type.upper()}] {status} (ID: {card.id[:8]}...)",
                    f"Q: {card.question}",
                    f"A: {card.answer}",
                    f"Source: {card.source_file or 'Unknown'}",
                    "-" * 50,
                ]
            )

        return "\n".join(preview_lines)

    def validate_flashcard_content(self, question: str, answer: str, card_type: str) -> tuple[bool, str]:
        """
        Validate flashcard content without creating a flashcard.

        Args:
            question: Question text to validate
            answer: Answer text to validate
            card_type: Card type to validate

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Basic validation
        if not question or not question.strip():
            return False, "Question cannot be empty"

        if not answer or not answer.strip():
            return False, "Answer cannot be empty"

        if card_type not in ["qa", "cloze"]:
            return False, "Card type must be either 'qa' or 'cloze'"

        question_stripped = question.strip()
        answer_stripped = answer.strip()

        # Length validation
        if len(question_stripped) > 65000:
            return False, "Question cannot exceed 65,000 characters (Anki limit)"

        if len(answer_stripped) > 65000:
            return False, "Answer cannot exceed 65,000 characters (Anki limit)"

        # Cloze format validation
        if card_type == "cloze":
            if "{{c1::" not in question_stripped and "{{c1::" not in answer_stripped:
                return False, "Cloze cards must contain cloze deletion format {{c1::...}}"

        return True, "Content is valid"

    # Backward compatibility methods for existing tests
    def preview_flashcards_text(self, flashcards: list[Flashcard] | None = None) -> str:
        """
        Backward compatibility method that returns text preview.

        Args:
            flashcards: Optional list of flashcards to preview. Uses internal list if None.

        Returns:
            Formatted string representation of flashcards
        """
        return self.get_flashcard_preview_text(flashcards)

    def edit_flashcard(self, flashcard_id: str, question: str, answer: str) -> tuple[bool, str]:
        """
        Edit an existing flashcard with comprehensive validation.

        Args:
            flashcard_id: ID of the flashcard to edit
            question: New question text
            answer: New answer text

        Returns:
            Tuple of (success: bool, message: str) indicating result and any error message
        """
        # Input validation
        if not flashcard_id or not flashcard_id.strip():
            return False, "Flashcard ID cannot be empty"

        if not question or not question.strip():
            return False, "Question cannot be empty"

        if not answer or not answer.strip():
            return False, "Answer cannot be empty"

        # Find the flashcard
        target_flashcard = None
        for flashcard in self._flashcards:
            if flashcard.id == flashcard_id:
                target_flashcard = flashcard
                break

        if not target_flashcard:
            message = f"Flashcard with ID {flashcard_id} not found"
            logger.warning(message)
            return False, message

        # Store original values for rollback
        original_question = target_flashcard.question
        original_answer = target_flashcard.answer

        try:
            # Validate content length
            question_stripped = question.strip()
            answer_stripped = answer.strip()

            if len(question_stripped) > 65000:
                return False, "Question cannot exceed 65,000 characters (Anki limit)"

            if len(answer_stripped) > 65000:
                return False, "Answer cannot exceed 65,000 characters (Anki limit)"

            # For cloze cards, validate cloze format
            if target_flashcard.card_type == "cloze":
                if "{{c1::" not in question_stripped and "{{c1::" not in answer_stripped:
                    return False, "Cloze cards must contain cloze deletion format {{c1::...}}"

            # Create a test flashcard to validate the new content
            Flashcard(
                id=target_flashcard.id,
                question=question_stripped,
                answer=answer_stripped,
                card_type=target_flashcard.card_type,
                source_file=target_flashcard.source_file,
                created_at=target_flashcard.created_at,
            )

            # If we get here, validation passed - update the original flashcard
            target_flashcard.question = question_stripped
            target_flashcard.answer = answer_stripped

            logger.info(f"Successfully edited flashcard {flashcard_id[:8]}...")
            return True, f"Flashcard {flashcard_id[:8]}... updated successfully"

        except Exception as e:
            # Rollback changes
            target_flashcard.question = original_question
            target_flashcard.answer = original_answer

            error_message = f"Edit failed validation: {str(e)}"
            logger.warning(f"Edit failed for flashcard {flashcard_id[:8]}...: {error_message}")
            return False, error_message

    def delete_flashcard(self, flashcard_id: str) -> tuple[bool, str]:
        """
        Delete a flashcard by ID with validation.

        Args:
            flashcard_id: ID of the flashcard to delete

        Returns:
            Tuple of (success: bool, message: str) indicating result and feedback message
        """
        # Input validation
        if not flashcard_id or not flashcard_id.strip():
            return False, "Flashcard ID cannot be empty"

        # Find and delete the flashcard
        for i, flashcard in enumerate(self._flashcards):
            if flashcard.id == flashcard_id:
                deleted_card = self._flashcards.pop(i)
                message = f"Deleted flashcard {flashcard_id[:8]}...: {deleted_card.question[:50]}..."
                logger.info(message)
                return True, message

        message = f"Flashcard with ID {flashcard_id} not found"
        logger.warning(message)
        return False, message

    def add_flashcard(
        self, question: str, answer: str, card_type: str, source_file: str | None = None
    ) -> tuple[Flashcard | None, str]:
        """
        Add a new flashcard manually with comprehensive validation.

        Args:
            question: Question text
            answer: Answer text
            card_type: Type of card ("qa" or "cloze")
            source_file: Optional source file name

        Returns:
            Tuple of (flashcard: Flashcard | None, message: str) with result and feedback
        """
        # Input validation
        if not question or not question.strip():
            return None, "Question cannot be empty"

        if not answer or not answer.strip():
            return None, "Answer cannot be empty"

        if not card_type or card_type not in ["qa", "cloze"]:
            return None, "Card type must be either 'qa' or 'cloze'"

        question_stripped = question.strip()
        answer_stripped = answer.strip()

        # Validate content length
        if len(question_stripped) > 65000:
            return None, "Question cannot exceed 65,000 characters (Anki limit)"

        if len(answer_stripped) > 65000:
            return None, "Answer cannot exceed 65,000 characters (Anki limit)"

        # Validate cloze format for cloze cards
        if card_type == "cloze":
            if "{{c1::" not in question_stripped and "{{c1::" not in answer_stripped:
                return None, "Cloze cards must contain cloze deletion format {{c1::...}}"

        try:
            flashcard = Flashcard.create(
                question=question_stripped,
                answer=answer_stripped,
                card_type=card_type,
                source_file=source_file,
            )

            if flashcard.validate_content():
                self._flashcards.append(flashcard)
                message = f"Added new flashcard: {flashcard.question[:50]}..."
                logger.info(message)
                return flashcard, message
            else:
                return None, "Failed to add flashcard: validation failed"

        except Exception as e:
            error_message = f"Failed to create flashcard: {str(e)}"
            logger.error(error_message)
            return None, error_message

    def export_to_csv(self, output_path: Path, flashcards: list[Flashcard] | None = None) -> tuple[bool, dict]:
        """
        Export flashcards to Anki-compatible CSV format with comprehensive summary reporting.

        Args:
            output_path: Path where to save the CSV file
            flashcards: Optional list of flashcards to export. Uses internal list if None.

        Returns:
            Tuple of (success: bool, summary: dict) containing export result and detailed summary
        """
        cards_to_export = flashcards or self._flashcards

        # Initialize summary data
        summary: dict[str, Any] = {
            "total_flashcards": len(cards_to_export),
            "exported_flashcards": 0,
            "skipped_invalid": 0,
            "qa_cards": 0,
            "cloze_cards": 0,
            "source_files": set(),
            "output_path": str(output_path),
            "file_size_bytes": 0,
            "errors": [],
        }

        if not cards_to_export:
            error_msg = "No flashcards to export"
            logger.warning(error_msg)
            summary["errors"].append(error_msg)
            return False, summary

        try:
            # Prepare data for CSV export and collect statistics
            csv_data = []
            for card in cards_to_export:
                if card.validate_content():
                    csv_data.append(card.to_csv_row())
                    summary["exported_flashcards"] += 1

                    # Count card types
                    if card.card_type == "qa":
                        summary["qa_cards"] += 1
                    elif card.card_type == "cloze":
                        summary["cloze_cards"] += 1

                    # Track source files
                    if card.source_file:
                        summary["source_files"].add(card.source_file)
                else:
                    summary["skipped_invalid"] += 1
                    warning_msg = f"Skipping invalid flashcard during export: {card.id}"
                    logger.warning(warning_msg)

            if not csv_data:
                error_msg = "No valid flashcards to export"
                logger.warning(error_msg)
                summary["errors"].append(error_msg)
                return False, summary

            # Create DataFrame and export to CSV
            df = pd.DataFrame(csv_data, columns=["Question", "Answer", "Card Type", "Source File"])

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Export to CSV with proper encoding for Anki
            df.to_csv(output_path, index=False, encoding="utf-8")

            # Get file size for summary
            if output_path.exists():
                summary["file_size_bytes"] = output_path.stat().st_size

            # Convert source_files set to list for JSON serialization
            summary["source_files"] = list(summary["source_files"])

            # Log comprehensive summary
            self._log_export_summary(summary)

            return True, summary

        except Exception as e:
            error_msg = f"Failed to export flashcards to CSV: {e}"
            logger.error(error_msg)
            summary["errors"].append(error_msg)
            return False, summary

    def get_flashcard_by_id(self, flashcard_id: str) -> Flashcard | None:
        """
        Get a flashcard by its ID.

        Args:
            flashcard_id: ID of the flashcard to retrieve

        Returns:
            The Flashcard object if found, None otherwise
        """
        for flashcard in self._flashcards:
            if flashcard.id == flashcard_id:
                return flashcard
        return None

    def get_flashcards_by_source(self, source_file: str) -> list[Flashcard]:
        """
        Get all flashcards from a specific source file.

        Args:
            source_file: Name of the source file

        Returns:
            List of flashcards from the specified source file
        """
        return [card for card in self._flashcards if card.source_file == source_file]

    def get_flashcards_by_type(self, card_type: str) -> list[Flashcard]:
        """
        Get all flashcards of a specific type.

        Args:
            card_type: Type of cards to retrieve ("qa" or "cloze")

        Returns:
            List of flashcards of the specified type
        """
        return [card for card in self._flashcards if card.card_type == card_type]

    def validate_all_flashcards(self) -> tuple[list[Flashcard], list[Flashcard]]:
        """
        Validate all flashcards and separate valid from invalid ones.

        Returns:
            Tuple of (valid_flashcards, invalid_flashcards)
        """
        valid = []
        invalid = []

        for card in self._flashcards:
            if card.validate_content():
                valid.append(card)
            else:
                invalid.append(card)

        return valid, invalid

    def clear_flashcards(self) -> None:
        """Clear all flashcards from the generator."""
        count = len(self._flashcards)
        self._flashcards.clear()
        logger.info(f"Cleared {count} flashcards")

    def export_to_csv_simple(self, output_path: Path, flashcards: list[Flashcard] | None = None) -> bool:
        """
        Export flashcards to CSV format with simple boolean return (backward compatibility).

        Args:
            output_path: Path where to save the CSV file
            flashcards: Optional list of flashcards to export. Uses internal list if None.

        Returns:
            True if export was successful, False otherwise
        """
        success, _ = self.export_to_csv(output_path, flashcards)
        return success

    def _log_export_summary(self, summary: dict) -> None:
        """
        Log a comprehensive export summary.

        Args:
            summary: Dictionary containing export statistics
        """
        logger.info("=== CSV Export Summary ===")
        logger.info(f"Total flashcards processed: {summary['total_flashcards']}")
        logger.info(f"Successfully exported: {summary['exported_flashcards']}")

        if summary["skipped_invalid"] > 0:
            logger.warning(f"Skipped invalid flashcards: {summary['skipped_invalid']}")

        logger.info(f"Question-Answer cards: {summary['qa_cards']}")
        logger.info(f"Cloze deletion cards: {summary['cloze_cards']}")

        if summary["source_files"]:
            logger.info(f"Source files: {', '.join(summary['source_files'])}")

        logger.info(f"Output file: {summary['output_path']}")

        if summary["file_size_bytes"] > 0:
            # Convert bytes to human-readable format
            if summary["file_size_bytes"] < 1024:
                size_str = f"{summary['file_size_bytes']} bytes"
            elif summary["file_size_bytes"] < 1024 * 1024:
                size_str = f"{summary['file_size_bytes'] / 1024:.1f} KB"
            else:
                size_str = f"{summary['file_size_bytes'] / (1024 * 1024):.1f} MB"
            logger.info(f"File size: {size_str}")

        if summary["errors"]:
            logger.error(f"Errors encountered: {len(summary['errors'])}")
            for error in summary["errors"]:
                logger.error(f"  - {error}")

        logger.info("=== End Export Summary ===")

    def get_statistics(self) -> dict:
        """
        Get statistics about the current flashcards.

        Returns:
            Dictionary containing various statistics
        """
        if not self._flashcards:
            return {
                "total_count": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "qa_count": 0,
                "cloze_count": 0,
                "source_files": [],
            }

        valid, invalid = self.validate_all_flashcards()
        qa_cards = self.get_flashcards_by_type("qa")
        cloze_cards = self.get_flashcards_by_type("cloze")
        source_files = list(set(card.source_file for card in self._flashcards if card.source_file))

        return {
            "total_count": len(self._flashcards),
            "valid_count": len(valid),
            "invalid_count": len(invalid),
            "qa_count": len(qa_cards),
            "cloze_count": len(cloze_cards),
            "source_files": source_files,
        }
