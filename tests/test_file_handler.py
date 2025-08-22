"""Tests for file handling utilities."""

import tempfile
import zipfile
from pathlib import Path

import pytest

from src.document_to_anki.utils.file_handler import FileHandler, FileHandlingError


class TestFileHandler:
    """Test cases for FileHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.file_handler = FileHandler()

    def test_init(self):
        """Test FileHandler initialization."""
        handler = FileHandler()
        assert handler.processed_files == []
        assert handler.SUPPORTED_EXTENSIONS == {".pdf", ".docx", ".txt", ".md"}
        assert handler.MAX_FILE_SIZE == 50 * 1024 * 1024
        assert handler.MAX_FILES_COUNT == 100

    def test_validate_file_type_supported_extensions(self):
        """Test validation of supported file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test supported extensions
            for ext in [".pdf", ".docx", ".txt", ".md"]:
                test_file = temp_path / f"test{ext}"
                test_file.write_text("test content")

                assert self.file_handler.validate_file_type(test_file)

    def test_validate_file_type_unsupported_extensions(self):
        """Test validation rejects unsupported file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test unsupported extensions
            for ext in [".jpg", ".png", ".xlsx", ".pptx"]:
                test_file = temp_path / f"test{ext}"
                test_file.write_text("test content")

                assert not self.file_handler.validate_file_type(test_file)

    def test_validate_file_type_nonexistent_file(self):
        """Test validation raises error for nonexistent files."""
        nonexistent_file = Path("/nonexistent/file.txt")

        with pytest.raises(FileHandlingError, match="File does not exist"):
            self.file_handler.validate_file_type(nonexistent_file)

    def test_validate_file_type_directory(self):
        """Test validation raises error for directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with pytest.raises(FileHandlingError, match="Path is not a file"):
                self.file_handler.validate_file_type(temp_path)

    def test_validate_file_type_empty_file(self):
        """Test validation raises error for empty files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            empty_file = temp_path / "empty.txt"
            empty_file.touch()  # Create empty file

            with pytest.raises(FileHandlingError, match="File is empty"):
                self.file_handler.validate_file_type(empty_file)

    def test_validate_file_type_large_file(self, mocker):
        """Test validation raises error for files that are too large."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            large_file = temp_path / "large.txt"
            large_file.write_text("test content")  # Create the file first

            # Mock the stat result to simulate a large file
            import stat

            mock_stat_result = mocker.MagicMock()
            mock_stat_result.st_size = FileHandler.MAX_FILE_SIZE + 1
            mock_stat_result.st_mode = stat.S_IFREG | 0o644  # Regular file mode

            with mocker.patch("pathlib.Path.stat", return_value=mock_stat_result):
                with pytest.raises(FileHandlingError, match="File too large"):
                    self.file_handler.validate_file_type(large_file)

    def test_process_zip_archive_valid(self):
        """Test processing a valid ZIP archive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            test_files = []
            for i, ext in enumerate([".txt", ".md", ".pdf"]):
                test_file = temp_path / f"test{i}{ext}"
                test_file.write_text(f"Test content {i}")
                test_files.append(test_file)

            # Create ZIP file
            zip_file = temp_path / "test.zip"
            with zipfile.ZipFile(zip_file, "w") as zf:
                for test_file in test_files:
                    zf.write(test_file, test_file.name)

            # Process ZIP
            result = self.file_handler.process_zip_archive(zip_file)

            assert len(result) == 3
            assert all(file_path.exists() for file_path in result)
            assert len(self.file_handler.processed_files) == 3

    def test_process_zip_archive_nonexistent(self):
        """Test processing nonexistent ZIP file raises error."""
        nonexistent_zip = Path("/nonexistent/file.zip")

        with pytest.raises(FileHandlingError, match="ZIP file does not exist"):
            self.file_handler.process_zip_archive(nonexistent_zip)

    def test_process_zip_archive_not_zip(self):
        """Test processing non-ZIP file raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            not_zip = temp_path / "not_zip.txt"
            not_zip.write_text("This is not a ZIP file")

            with pytest.raises(FileHandlingError, match="File is not a ZIP archive"):
                self.file_handler.process_zip_archive(not_zip)

    def test_process_zip_archive_too_many_files(self):
        """Test processing ZIP with too many files raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create ZIP with many files
            zip_file = temp_path / "many_files.zip"
            with zipfile.ZipFile(zip_file, "w") as zf:
                for i in range(FileHandler.MAX_FILES_COUNT + 1):
                    zf.writestr(f"file{i}.txt", f"Content {i}")

            with pytest.raises(FileHandlingError, match="Too many files in ZIP"):
                self.file_handler.process_zip_archive(zip_file)

    def test_process_folder_valid(self):
        """Test processing a valid folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            test_files = []
            for i, ext in enumerate([".txt", ".md", ".pdf", ".docx"]):
                test_file = temp_path / f"test{i}{ext}"
                test_file.write_text(f"Test content {i}")
                test_files.append(test_file)

            # Create unsupported file (should be skipped)
            unsupported_file = temp_path / "image.jpg"
            unsupported_file.write_text("fake image content")

            # Process folder
            result = self.file_handler.process_folder(temp_path)

            assert len(result) == 4  # Only supported files
            assert all(file_path.exists() for file_path in result)
            assert len(self.file_handler.processed_files) == 4

    def test_process_folder_nonexistent(self):
        """Test processing nonexistent folder raises error."""
        nonexistent_folder = Path("/nonexistent/folder")

        with pytest.raises(FileHandlingError, match="Folder does not exist"):
            self.file_handler.process_folder(nonexistent_folder)

    def test_process_folder_not_directory(self):
        """Test processing file instead of directory raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text("test content")

            with pytest.raises(FileHandlingError, match="Path is not a directory"):
                self.file_handler.process_folder(test_file)

    def test_process_folder_too_many_files(self):
        """Test processing folder with too many files raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create many files
            for i in range(FileHandler.MAX_FILES_COUNT + 1):
                test_file = temp_path / f"test{i}.txt"
                test_file.write_text(f"Content {i}")

            with pytest.raises(FileHandlingError, match="Too many files in folder"):
                self.file_handler.process_folder(temp_path)

    def test_process_folder_no_valid_files(self):
        """Test processing folder with no valid files raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create only unsupported files
            for ext in [".jpg", ".png", ".xlsx"]:
                test_file = temp_path / f"test{ext}"
                test_file.write_text("test content")

            with pytest.raises(FileHandlingError, match="No valid files found in folder"):
                self.file_handler.process_folder(temp_path)

    def test_get_file_info(self):
        """Test getting file information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text("test content")

            info = self.file_handler.get_file_info(test_file)

            assert info["name"] == "test.txt"
            assert info["path"] == str(test_file)
            assert info["size"] > 0
            assert info["extension"] == ".txt"
            assert info["is_supported"]
            assert "modified" in info

    def test_get_file_info_nonexistent(self):
        """Test getting info for nonexistent file raises error."""
        nonexistent_file = Path("/nonexistent/file.txt")

        with pytest.raises(FileHandlingError, match="File does not exist"):
            self.file_handler.get_file_info(nonexistent_file)

    def test_cleanup_extracted_files(self):
        """Test cleanup of extracted files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Simulate extracted files
            extracted_dir = temp_path / "test_extracted"
            extracted_dir.mkdir()
            extracted_file = extracted_dir / "test.txt"
            extracted_file.write_text("extracted content")

            # Add to processed files
            self.file_handler.processed_files.append(extracted_file)

            # Cleanup
            self.file_handler.cleanup_extracted_files()

            assert not extracted_dir.exists()
            assert len(self.file_handler.processed_files) == 0
