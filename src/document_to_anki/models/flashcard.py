"""Flashcard and ProcessingResult data models."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Flashcard:
    """Represents a single flashcard with question, answer, and metadata."""

    id: str
    question: str
    answer: str
    card_type: str  # "qa" for question-answer, "cloze" for cloze deletion
    source_file: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls, question: str, answer: str, card_type: str, source_file: str | None = None
    ) -> "Flashcard":
        """Create a new flashcard with auto-generated ID."""
        return cls(
            id=str(uuid.uuid4()),
            question=question,
            answer=answer,
            card_type=card_type,
            source_file=source_file,
        )

    def to_csv_row(self) -> list[str]:
        """Convert flashcard to Anki-compatible CSV format.

        Returns a list of strings representing the CSV row for Anki import.
        Format: [question, answer, card_type, source_file]
        """
        return [self.question.strip(), self.answer.strip(), self.card_type, self.source_file or ""]

    def validate(self) -> bool:
        """Validate flashcard content.

        Returns:
            bool: True if flashcard is valid, False otherwise
        """
        # Check required fields are not empty
        if not self.question or not self.question.strip():
            return False

        if not self.answer or not self.answer.strip():
            return False

        # Check card_type is valid
        if self.card_type not in ["qa", "cloze"]:
            return False

        # Check question and answer are not too long (Anki limit is ~65k chars)
        if len(self.question) > 65000 or len(self.answer) > 65000:
            return False

        # For cloze cards, ensure proper cloze deletion format
        if self.card_type == "cloze":
            if "{{c1::" not in self.question and "{{c1::" not in self.answer:
                return False

        return True


@dataclass
class ProcessingResult:
    """Represents the result of document processing operation."""

    flashcards: list[Flashcard]
    source_files: list[str]
    processing_time: float
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if processing was successful (no errors)."""
        return len(self.errors) == 0

    @property
    def flashcard_count(self) -> int:
        """Get the total number of flashcards generated."""
        return len(self.flashcards)

    @property
    def valid_flashcard_count(self) -> int:
        """Get the number of valid flashcards."""
        return sum(1 for card in self.flashcards if card.validate())

    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the result."""
        self.warnings.append(warning)

    def get_summary(self) -> str:
        """Get a human-readable summary of the processing result."""
        summary_lines = [
            f"Processing completed in {self.processing_time:.2f} seconds",
            f"Generated {self.flashcard_count} flashcards from {len(self.source_files)} files",
            f"Valid flashcards: {self.valid_flashcard_count}/{self.flashcard_count}",
        ]

        if self.errors:
            summary_lines.append(f"Errors: {len(self.errors)}")

        if self.warnings:
            summary_lines.append(f"Warnings: {len(self.warnings)}")

        return "\n".join(summary_lines)
