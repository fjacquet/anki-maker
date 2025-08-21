"""
FlashcardGenerator for managing flashcard creation and editing.

This module provides the FlashcardGenerator class that orchestrates the creation,
editing, and management of flashcards using the LLMClient and Flashcard models.
"""

import time
from pathlib import Path

import pandas as pd
from loguru import logger

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
        Initialize the FlashcardGenerator.
        
        Args:
            llm_client: Optional LLMClient instance. If None, creates a default one.
        """
        self.llm_client = llm_client or LLMClient()
        self._flashcards: list[Flashcard] = []
        
    @property
    def flashcards(self) -> list[Flashcard]:
        """Get the current list of flashcards."""
        return self._flashcards.copy()
    
    def generate_flashcards(
        self, 
        text_content: list[str], 
        source_files: list[str] | None = None
    ) -> ProcessingResult:
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
        warnings = []
        
        if not text_content:
            errors.append("No text content provided for flashcard generation")
            return ProcessingResult(
                flashcards=[],
                source_files=source_files or [],
                processing_time=time.time() - start_time,
                errors=errors,
                warnings=warnings
            )
        
        logger.info(f"Starting flashcard generation for {len(text_content)} text chunks")
        
        # Process each text chunk
        for i, text in enumerate(text_content):
            if not text or not text.strip():
                warnings.append(f"Skipping empty text chunk {i + 1}")
                continue
                
            try:
                source_file = source_files[i] if source_files and i < len(source_files) else None
                chunk_flashcards = self._generate_flashcards_from_single_text(
                    text, source_file, i + 1, warnings
                )
                all_flashcards.extend(chunk_flashcards)
                
            except Exception as e:
                error_msg = f"Failed to generate flashcards from text chunk {i + 1}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        # Validate generated flashcards
        valid_flashcards = []
        for flashcard in all_flashcards:
            if flashcard.validate():
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
            warnings=warnings
        )
        
        logger.info(f"Flashcard generation completed: {result.get_summary()}")
        return result
    
    def _generate_flashcards_from_single_text(
        self, 
        text: str, 
        source_file: str | None, 
        chunk_number: int,
        warnings: list[str] | None = None
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
                        source_file=source_file
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
            raise FlashcardGenerationError(f"Failed to generate flashcards: {e}")
    
    def preview_flashcards(self, flashcards: list[Flashcard] | None = None) -> str:
        """
        Generate a formatted preview of flashcards.
        
        Args:
            flashcards: Optional list of flashcards to preview. Uses internal list if None.
            
        Returns:
            Formatted string representation of flashcards
        """
        cards_to_preview = flashcards or self._flashcards
        
        if not cards_to_preview:
            return "No flashcards to preview."
        
        preview_lines = [
            f"=== Flashcard Preview ({len(cards_to_preview)} cards) ===\n"
        ]
        
        for i, card in enumerate(cards_to_preview, 1):
            preview_lines.extend([
                f"Card {i} [{card.card_type.upper()}] (ID: {card.id[:8]}...)",
                f"Q: {card.question}",
                f"A: {card.answer}",
                f"Source: {card.source_file or 'Unknown'}",
                "-" * 50
            ])
        
        return "\n".join(preview_lines)
    
    def edit_flashcard(self, flashcard_id: str, question: str, answer: str) -> bool:
        """
        Edit an existing flashcard.
        
        Args:
            flashcard_id: ID of the flashcard to edit
            question: New question text
            answer: New answer text
            
        Returns:
            True if flashcard was found and edited, False otherwise
        """
        for flashcard in self._flashcards:
            if flashcard.id == flashcard_id:
                old_question = flashcard.question
                old_answer = flashcard.answer
                
                try:
                    # Create a new flashcard with the updated values to trigger validation
                    updated_flashcard = Flashcard(
                        id=flashcard.id,
                        question=question.strip(),
                        answer=answer.strip(),
                        card_type=flashcard.card_type,
                        source_file=flashcard.source_file,
                        created_at=flashcard.created_at
                    )
                    
                    # If validation passes, update the original flashcard
                    flashcard.question = updated_flashcard.question
                    flashcard.answer = updated_flashcard.answer
                    
                    logger.info(f"Edited flashcard {flashcard_id[:8]}...")
                    return True
                    
                except Exception as e:
                    logger.warning(f"Edit failed validation for flashcard {flashcard_id[:8]}...: {e}")
                    return False
        
        logger.warning(f"Flashcard with ID {flashcard_id} not found")
        return False
    
    def delete_flashcard(self, flashcard_id: str) -> bool:
        """
        Delete a flashcard by ID.
        
        Args:
            flashcard_id: ID of the flashcard to delete
            
        Returns:
            True if flashcard was found and deleted, False otherwise
        """
        for i, flashcard in enumerate(self._flashcards):
            if flashcard.id == flashcard_id:
                deleted_card = self._flashcards.pop(i)
                logger.info(f"Deleted flashcard {flashcard_id[:8]}...: {deleted_card.question[:50]}...")
                return True
        
        logger.warning(f"Flashcard with ID {flashcard_id} not found")
        return False
    
    def add_flashcard(
        self, 
        question: str, 
        answer: str, 
        card_type: str, 
        source_file: str | None = None
    ) -> Flashcard | None:
        """
        Add a new flashcard manually.
        
        Args:
            question: Question text
            answer: Answer text
            card_type: Type of card ("qa" or "cloze")
            source_file: Optional source file name
            
        Returns:
            The created Flashcard object if successful, None otherwise
        """
        try:
            flashcard = Flashcard.create(
                question=question.strip(),
                answer=answer.strip(),
                card_type=card_type,
                source_file=source_file
            )
            
            if flashcard.validate():
                self._flashcards.append(flashcard)
                logger.info(f"Added new flashcard: {flashcard.question[:50]}...")
                return flashcard
            else:
                logger.warning("Failed to add flashcard: validation failed")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create flashcard: {e}")
            return None
    
    def export_to_csv(
        self, 
        output_path: Path, 
        flashcards: list[Flashcard] | None = None
    ) -> bool:
        """
        Export flashcards to Anki-compatible CSV format.
        
        Args:
            output_path: Path where to save the CSV file
            flashcards: Optional list of flashcards to export. Uses internal list if None.
            
        Returns:
            True if export was successful, False otherwise
        """
        cards_to_export = flashcards or self._flashcards
        
        if not cards_to_export:
            logger.warning("No flashcards to export")
            return False
        
        try:
            # Prepare data for CSV export
            csv_data = []
            for card in cards_to_export:
                if card.validate():
                    csv_data.append(card.to_csv_row())
                else:
                    logger.warning(f"Skipping invalid flashcard during export: {card.id}")
            
            if not csv_data:
                logger.warning("No valid flashcards to export")
                return False
            
            # Create DataFrame and export to CSV
            df = pd.DataFrame(csv_data, columns=["Question", "Answer", "Card Type", "Source File"])
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export to CSV with proper encoding for Anki
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            logger.info(f"Exported {len(csv_data)} flashcards to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export flashcards to CSV: {e}")
            return False
    
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
            if card.validate():
                valid.append(card)
            else:
                invalid.append(card)
        
        return valid, invalid
    
    def clear_flashcards(self) -> None:
        """Clear all flashcards from the generator."""
        count = len(self._flashcards)
        self._flashcards.clear()
        logger.info(f"Cleared {count} flashcards")
    
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
                "source_files": []
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
            "source_files": source_files
        }