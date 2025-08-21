"""File handling utilities for document processing."""

import mimetypes
import os
import zipfile
from pathlib import Path

from loguru import logger


class FileHandlingError(Exception):
    """Exception raised for file handling errors."""
    pass


class FileHandler:
    """Handles file uploads, validation, and processing."""
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}
    
    # Maximum file size in bytes (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    # Maximum number of files to process from a ZIP or folder
    MAX_FILES_COUNT = 100
    
    def __init__(self):
        """Initialize the FileHandler."""
        self.processed_files: list[Path] = []
        
    def validate_file_type(self, file_path: Path) -> bool:
        """
        Validate if the file type is supported.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file type is supported, False otherwise
            
        Raises:
            FileHandlingError: If file doesn't exist or has security issues
        """
        if not file_path.exists():
            raise FileHandlingError(f"File does not exist: {file_path}")
            
        if not file_path.is_file():
            raise FileHandlingError(f"Path is not a file: {file_path}")
            
        # Check file extension
        extension = file_path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file type: {extension} for file {file_path}")
            return False
            
        # Additional MIME type validation
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            expected_mimes = {
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.txt': 'text/plain',
                '.md': 'text/markdown'
            }
            
            expected_mime = expected_mimes.get(extension)
            if expected_mime and not mime_type.startswith(expected_mime.split('/')[0]):
                logger.warning(f"MIME type mismatch for {file_path}: expected {expected_mime}, got {mime_type}")
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise FileHandlingError(f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE} bytes)")
            
        if file_size == 0:
            raise FileHandlingError(f"File is empty: {file_path}")
            
        # Security check: ensure file is readable
        if not os.access(file_path, os.R_OK):
            raise FileHandlingError(f"File is not readable: {file_path}")
            
        logger.debug(f"File validation passed for: {file_path}")
        return True
        
    def _validate_path_security(self, path: Path) -> None:
        """
        Validate path for security issues like path traversal.
        
        Args:
            path: Path to validate
            
        Raises:
            FileHandlingError: If path has security issues
        """
        try:
            # Resolve the path to check for path traversal attempts
            resolved_path = path.resolve()
            
            # Check for suspicious path components
            path_parts = resolved_path.parts
            for part in path_parts:
                if part.startswith('.') and part not in {'.', '..'}:
                    continue  # Hidden files are okay
                if any(char in part for char in ['<', '>', ':', '"', '|', '?', '*']):
                    raise FileHandlingError(f"Invalid characters in path: {part}")
                    
        except (OSError, ValueError) as e:
            raise FileHandlingError(f"Path security validation failed: {e}")     
       
    def process_zip_archive(self, zip_path: Path) -> list[Path]:
        """
        Extract and process ZIP archive contents.
        
        Args:
            zip_path: Path to the ZIP file
            
        Returns:
            List of valid file paths extracted from the ZIP
            
        Raises:
            FileHandlingError: If ZIP processing fails
        """
        if not zip_path.exists() or not zip_path.is_file():
            raise FileHandlingError(f"ZIP file does not exist: {zip_path}")
            
        if zip_path.suffix.lower() != '.zip':
            raise FileHandlingError(f"File is not a ZIP archive: {zip_path}")
            
        # Check ZIP file size
        zip_size = zip_path.stat().st_size
        if zip_size > self.MAX_FILE_SIZE:
            raise FileHandlingError(f"ZIP file too large: {zip_size} bytes")
            
        valid_files: list[Path] = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get list of files in the ZIP
                file_list = zip_ref.namelist()
                
                if len(file_list) > self.MAX_FILES_COUNT:
                    raise FileHandlingError(f"Too many files in ZIP: {len(file_list)} (max: {self.MAX_FILES_COUNT})")
                
                # Create temporary extraction directory
                extract_dir = zip_path.parent / f"{zip_path.stem}_extracted"
                extract_dir.mkdir(exist_ok=True)
                
                logger.info(f"Extracting ZIP archive {zip_path} to {extract_dir}")
                
                for file_info in zip_ref.infolist():
                    # Skip directories
                    if file_info.is_dir():
                        continue
                        
                    # Security check: prevent path traversal
                    if '..' in file_info.filename or file_info.filename.startswith('/'):
                        logger.warning(f"Skipping potentially unsafe file: {file_info.filename}")
                        continue
                        
                    # Extract file
                    try:
                        extracted_path = Path(zip_ref.extract(file_info, extract_dir))
                        self._validate_path_security(extracted_path)
                        
                        # Validate the extracted file
                        if self.validate_file_type(extracted_path):
                            valid_files.append(extracted_path)
                            logger.debug(f"Added valid file from ZIP: {extracted_path}")
                        else:
                            logger.debug(f"Skipped unsupported file from ZIP: {extracted_path}")
                            
                    except (FileHandlingError, zipfile.BadZipFile, OSError) as e:
                        logger.warning(f"Failed to extract {file_info.filename}: {e}")
                        continue
                        
        except zipfile.BadZipFile as e:
            raise FileHandlingError(f"Invalid or corrupted ZIP file: {e}")
        except OSError as e:
            raise FileHandlingError(f"Failed to process ZIP file: {e}")
            
        if not valid_files:
            raise FileHandlingError("No valid files found in ZIP archive")
            
        logger.info(f"Successfully extracted {len(valid_files)} valid files from ZIP")
        self.processed_files.extend(valid_files)
        return valid_files
        
    def process_folder(self, folder_path: Path) -> list[Path]:
        """
        Process all supported files in a folder recursively.
        
        Args:
            folder_path: Path to the folder to process
            
        Returns:
            List of valid file paths found in the folder
            
        Raises:
            FileHandlingError: If folder processing fails
        """
        if not folder_path.exists():
            raise FileHandlingError(f"Folder does not exist: {folder_path}")
            
        if not folder_path.is_dir():
            raise FileHandlingError(f"Path is not a directory: {folder_path}")
            
        # Security validation
        self._validate_path_security(folder_path)
        
        valid_files: list[Path] = []
        
        try:
            # Recursively find all files
            all_files = []
            for file_path in folder_path.rglob('*'):
                if file_path.is_file():
                    all_files.append(file_path)
                    
            if len(all_files) > self.MAX_FILES_COUNT:
                raise FileHandlingError(f"Too many files in folder: {len(all_files)} (max: {self.MAX_FILES_COUNT})")
                
            logger.info(f"Processing folder {folder_path} with {len(all_files)} files")
            
            for file_path in all_files:
                try:
                    # Security check for each file
                    self._validate_path_security(file_path)
                    
                    # Validate file type and add if supported
                    if self.validate_file_type(file_path):
                        valid_files.append(file_path)
                        logger.debug(f"Added valid file from folder: {file_path}")
                    else:
                        logger.debug(f"Skipped unsupported file: {file_path}")
                        
                except FileHandlingError as e:
                    logger.warning(f"Skipped file {file_path}: {e}")
                    continue
                    
        except OSError as e:
            raise FileHandlingError(f"Failed to process folder: {e}")
            
        if not valid_files:
            raise FileHandlingError("No valid files found in folder")
            
        logger.info(f"Successfully processed {len(valid_files)} valid files from folder")
        self.processed_files.extend(valid_files)
        return valid_files
        
    def get_file_info(self, file_path: Path) -> dict:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file information
        """
        if not file_path.exists():
            raise FileHandlingError(f"File does not exist: {file_path}")
            
        stat = file_path.stat()
        return {
            'name': file_path.name,
            'path': str(file_path),
            'size': stat.st_size,
            'extension': file_path.suffix.lower(),
            'modified': stat.st_mtime,
            'is_supported': file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
        }
        
    def cleanup_extracted_files(self) -> None:
        """Clean up any temporary extracted files."""
        for file_path in self.processed_files:
            if '_extracted' in str(file_path.parent):
                try:
                    # Remove the entire extracted directory
                    import shutil
                    extract_dir = file_path.parent
                    if extract_dir.exists():
                        shutil.rmtree(extract_dir)
                        logger.debug(f"Cleaned up extracted directory: {extract_dir}")
                        break  # Only need to remove the directory once
                except OSError as e:
                    logger.warning(f"Failed to cleanup extracted files: {e}")
                    
        self.processed_files.clear()