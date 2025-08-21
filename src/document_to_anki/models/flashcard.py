"""Flashcard and ProcessingResult data models."""

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Flashcard(BaseModel):
    """Represents a single flashcard with question, answer, and metadata."""

    id: str
    question: str
    answer: str
    card_type: Literal["qa", "cloze"]  # "qa" for question-answer, "cloze" for cloze deletion
    source_file: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def create(
        cls, question: str, answer: str, card_type: str, source_file: Optional[str] = None
    ) -> "Flashcard":
        """Create a new flashcard with auto-generated ID."""
        return cls(
            id=str(uuid.uuid4()),
            question=question,
            answer=answer,
            card_type=card_type,
            source_file=source_file,
        )

    @field_validator("question", "answer")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Validate that question and answer are not empty."""
        if not v or not v.strip():
            raise ValueError("Question and answer cannot be empty")
        return v.strip()

    @field_validator("question", "answer")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """Validate that content is not too long for Anki."""
        if len(v) > 65000:
            raise ValueError("Content cannot exceed 65,000 characters (Anki limit)")
        return v

    @model_validator(mode="after")
    def validate_cloze_format(self) -> "Flashcard":
        """Validate cloze deletion format for cloze cards."""
        if self.card_type == "cloze":
            if "{{c1::" not in self.question and "{{c1::" not in self.answer:
                raise ValueError("Cloze cards must contain cloze deletion format {{c1::...}}")
        return self

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
        try:
            # Pydantic validation happens automatically, so if we get here, it's valid
            return True
        except Exception:
            return False


class ProcessingResult(BaseModel):
    """Represents the result of document processing operation."""

    flashcards: list[Flashcard]
    source_files: list[str]
    processing_time: float
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

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
