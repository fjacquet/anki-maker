"""Document processor for handling file uploads and text extraction."""

from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger
from rich.progress import Progress, TaskID

from ..utils.file_handler import FileHandler, FileHandlingError
from ..utils.text_extractor import TextExtractionError, TextExtractor


@dataclass
class DocumentProcessingResult:
    """Represents the result of document processing operation."""

    text_content: str
    source_files: list[str]
    file_count: int
    total_characters: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if processing was successful (no errors)."""
        return len(self.errors) == 0

    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the result."""
        self.warnings.append(warning)

    def get_summary(self) -> str:
        """Get a human-readable summary of the processing result."""
        summary_lines = [
            "Document processing completed",
            f"Processed {self.file_count} files",
            f"Extracted {self.total_characters} characters total",
            f"Source files: {', '.join(self.source_files)}",
        ]

        if self.errors:
            summary_lines.append(f"Errors: {len(self.errors)}")

        if self.warnings:
            summary_lines.append(f"Warnings: {len(self.warnings)}")

        return "\n".join(summary_lines)


class DocumentProcessingError(Exception):
    """Exception raised for document processing errors."""

    pass


class DocumentProcessor:
    """Main orchestrator for document handling and text extraction."""

    def __init__(self):
        """Initialize the DocumentProcessor with required components."""
        self.file_handler = FileHandler()
        self.text_extractor = TextExtractor()
        self.logger = logger

    def process_upload(
        self,
        upload_path: str | Path,
        progress: Progress | None = None,
        task_id: TaskID | None = None,
    ) -> DocumentProcessingResult:
        """
        Process uploaded content (single file, folder, or ZIP archive).

        Args:
            upload_path: Path to the file, folder, or ZIP archive to process
            progress: Optional Rich progress instance for tracking
            task_id: Optional task ID for progress updates

        Returns:
            DocumentProcessingResult containing extracted text and processing metadata

        Raises:
            DocumentProcessingError: If processing fails
        """
        upload_path = Path(upload_path)

        if not upload_path.exists():
            raise DocumentProcessingError(f"Upload path does not exist: {upload_path}")

        self.logger.info(f"Starting document processing for: {upload_path}")

        try:
            # Determine the type of upload and get file paths
            if upload_path.is_file():
                if upload_path.suffix.lower() == ".zip":
                    self.logger.info("Processing ZIP archive")
                    file_paths = self._process_zip_upload(upload_path)
                else:
                    self.logger.info("Processing single file")
                    file_paths = self._process_single_file(upload_path)
            elif upload_path.is_dir():
                self.logger.info("Processing folder")
                file_paths = self._process_folder_upload(upload_path)
            else:
                raise DocumentProcessingError(f"Invalid upload path: {upload_path}")

            # Extract text from all files with progress tracking
            extracted_texts = self._extract_texts_from_files(file_paths, progress, task_id)

            # Consolidate text from multiple files
            consolidated_text = self._consolidate_texts(extracted_texts, file_paths)

            # Create processing result
            result = DocumentProcessingResult(
                text_content=consolidated_text,
                source_files=[str(path) for path in file_paths],
                file_count=len(file_paths),
                total_characters=len(consolidated_text),
                errors=[],
                warnings=[],
            )

            self.logger.info(
                f"Document processing completed successfully. "
                f"Processed {len(file_paths)} files, "
                f"extracted {len(consolidated_text)} characters"
            )

            return result

        except (FileHandlingError, TextExtractionError) as e:
            error_msg = f"Document processing failed: {str(e)}"
            self.logger.error(error_msg)
            raise DocumentProcessingError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during document processing: {str(e)}"
            self.logger.error(error_msg)
            raise DocumentProcessingError(error_msg) from e
        finally:
            # Clean up any temporary files
            self._cleanup()

    def _process_single_file(self, file_path: Path) -> list[Path]:
        """
        Process a single file upload.

        Args:
            file_path: Path to the single file

        Returns:
            List containing the single file path if valid

        Raises:
            DocumentProcessingError: If file processing fails
        """
        try:
            if self.file_handler.validate_file_type(file_path):
                self.logger.debug(f"Single file validated: {file_path}")
                return [file_path]
            else:
                raise DocumentProcessingError(f"Unsupported file type: {file_path}")
        except FileHandlingError as e:
            raise DocumentProcessingError(f"File validation failed: {str(e)}") from e

    def _process_zip_upload(self, zip_path: Path) -> list[Path]:
        """
        Process a ZIP archive upload.

        Args:
            zip_path: Path to the ZIP file

        Returns:
            List of valid file paths extracted from the ZIP

        Raises:
            DocumentProcessingError: If ZIP processing fails
        """
        try:
            file_paths = self.file_handler.process_zip_archive(zip_path)
            self.logger.info(f"ZIP archive processed: {len(file_paths)} valid files found")
            return file_paths
        except FileHandlingError as e:
            raise DocumentProcessingError(f"ZIP processing failed: {str(e)}") from e

    def _process_folder_upload(self, folder_path: Path) -> list[Path]:
        """
        Process a folder upload.

        Args:
            folder_path: Path to the folder

        Returns:
            List of valid file paths found in the folder

        Raises:
            DocumentProcessingError: If folder processing fails
        """
        try:
            file_paths = self.file_handler.process_folder(folder_path)
            self.logger.info(f"Folder processed: {len(file_paths)} valid files found")
            return file_paths
        except FileHandlingError as e:
            raise DocumentProcessingError(f"Folder processing failed: {str(e)}") from e

    def _extract_texts_from_files(
        self,
        file_paths: list[Path],
        progress: Progress | None = None,
        task_id: TaskID | None = None,
    ) -> list[str]:
        """
        Extract text from multiple files with progress tracking.

        Args:
            file_paths: List of file paths to process
            progress: Optional Rich progress instance
            task_id: Optional task ID for progress updates

        Returns:
            List of extracted text content from each file

        Raises:
            DocumentProcessingError: If text extraction fails for all files
        """
        extracted_texts = []
        successful_extractions = 0
        failed_extractions = 0

        total_files = len(file_paths)

        if progress and task_id:
            progress.update(task_id, total=total_files)

        for i, file_path in enumerate(file_paths):
            try:
                self.logger.debug(f"Extracting text from: {file_path}")
                text_content = self.text_extractor.extract_text(file_path)

                if text_content.strip():
                    extracted_texts.append(text_content)
                    successful_extractions += 1
                    self.logger.debug(
                        f"Successfully extracted {len(text_content)} characters from {file_path}"
                    )
                else:
                    self.logger.warning(f"No text content extracted from: {file_path}")
                    failed_extractions += 1

            except TextExtractionError as e:
                self.logger.warning(f"Failed to extract text from {file_path}: {str(e)}")
                failed_extractions += 1
                continue

            # Update progress
            if progress and task_id:
                progress.update(task_id, completed=i + 1)

        # Log extraction summary
        self.logger.info(
            f"Text extraction completed: {successful_extractions} successful, "
            f"{failed_extractions} failed out of {total_files} files"
        )

        if not extracted_texts:
            raise DocumentProcessingError("No text could be extracted from any of the provided files")

        return extracted_texts

    def _consolidate_texts(self, texts: list[str], file_paths: list[Path]) -> str:
        """
        Consolidate text content from multiple files into a single string.

        Args:
            texts: List of extracted text content
            file_paths: List of corresponding file paths

        Returns:
            Consolidated text content with file separators

        Raises:
            DocumentProcessingError: If consolidation fails
        """
        if not texts:
            raise DocumentProcessingError("No text content to consolidate")

        if len(texts) == 1:
            # Single file, no need for separators
            return texts[0]

        # Multiple files, add separators and file information
        consolidated_parts = []

        for i, (text, file_path) in enumerate(zip(texts, file_paths, strict=False)):
            if text.strip():  # Only include non-empty texts
                # Add file separator with file information
                separator = f"\n\n{'=' * 60}\n"
                separator += f"FILE: {file_path.name}\n"
                separator += f"PATH: {file_path}\n"
                separator += f"{'=' * 60}\n\n"

                if i == 0:
                    # First file, no leading separator
                    consolidated_parts.append(f"{separator}{text}")
                else:
                    consolidated_parts.append(f"{separator}{text}")

        consolidated_text = "\n\n".join(consolidated_parts)

        self.logger.info(
            f"Text consolidation completed: {len(texts)} files consolidated into "
            f"{len(consolidated_text)} characters"
        )

        return consolidated_text

    def _cleanup(self) -> None:
        """Clean up temporary files and resources."""
        try:
            self.file_handler.cleanup_extracted_files()
            self.logger.debug("Cleanup completed successfully")
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {str(e)}")

    def get_supported_formats(self) -> set[str]:
        """
        Get the set of supported file formats.

        Returns:
            Set of supported file extensions
        """
        return self.text_extractor.get_supported_formats()

    def validate_upload_path(self, upload_path: str | Path) -> bool:
        """
        Validate if an upload path is acceptable for processing.

        Args:
            upload_path: Path to validate

        Returns:
            True if the path can be processed, False otherwise
        """
        upload_path = Path(upload_path)

        if not upload_path.exists():
            return False

        try:
            if upload_path.is_file():
                if upload_path.suffix.lower() == ".zip":
                    # For ZIP files, we'll validate during processing
                    return True
                else:
                    return self.file_handler.validate_file_type(upload_path)
            elif upload_path.is_dir():
                # For directories, check if there are any supported files
                try:
                    file_paths = self.file_handler.process_folder(upload_path)
                    return len(file_paths) > 0
                except FileHandlingError:
                    return False
            else:
                return False
        except Exception:
            return False
