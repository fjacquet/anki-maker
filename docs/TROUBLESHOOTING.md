# Troubleshooting Guide

This guide helps you resolve common issues when using Document to Anki CLI.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Problems](#configuration-problems)
- [File Processing Errors](#file-processing-errors)
- [API and Network Issues](#api-and-network-issues)
- [Memory and Performance Issues](#memory-and-performance-issues)
- [Web Interface Problems](#web-interface-problems)
- [Export and Output Issues](#export-and-output-issues)
- [Getting Help](#getting-help)

## Installation Issues

### Problem: `uv` command not found
```bash
uv: command not found
```

**Solutions:**
1. Install uv following the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/)
2. For macOS: `brew install uv`
3. For Linux/Windows: `curl -LsSf https://astral.sh/uv/install.sh | sh`
4. Alternative: Use pip instead: `pip install -e .`

### Problem: Python version compatibility
```
ERROR: This package requires Python >=3.12
```

**Solutions:**
1. Check your Python version: `python --version`
2. Install Python 3.12+ from [python.org](https://python.org)
3. Use pyenv to manage multiple Python versions
4. Update your system Python if possible

### Problem: Missing dependencies
```
ModuleNotFoundError: No module named 'litellm'
```

**Solutions:**
1. Ensure you've run the installation: `uv sync` (or `uv sync --all-extras` for development)
2. Activate the virtual environment: `source .venv/bin/activate`
3. Install missing packages manually: `uv add litellm`
4. Try reinstalling: `uv sync --reinstall`

## Configuration Problems

### Problem: API key not found
```
Error: Missing API key for model 'gemini/gemini-2.5-flash'. Please set the GEMINI_API_KEY environment variable.
Error: Missing API key for model 'openai/gpt-4o'. Please set the OPENAI_API_KEY environment variable.
```

**Solutions:**
1. Create a `.env` file in the project root
2. Add the appropriate API key for your chosen model:
   - For Gemini models: `GEMINI_API_KEY=your-gemini-key-here`
   - For OpenAI models: `OPENAI_API_KEY=your-openai-key-here`
3. Alternatively, set environment variable: 
   - `export GEMINI_API_KEY=your-key`
   - `export OPENAI_API_KEY=your-key`
4. Verify the key is valid:
   - Gemini: [Google AI Studio](https://makersuite.google.com/app/apikey)
   - OpenAI: [OpenAI Platform](https://platform.openai.com/api-keys)

### Problem: Invalid API key
```
Error: 401 Unauthorized - Invalid API key
Error: Unsupported model 'invalid/model'. Supported models: gemini/gemini-2.5-flash, openai/gpt-4o, ...
```

**Solutions:**
1. Check that your API key is correct (no extra spaces)
2. Verify the key hasn't expired
3. Ensure you have API access enabled for your chosen provider:
   - Gemini: Enable Gemini API in Google Cloud Console
   - OpenAI: Verify account has API access
4. Check that your model selection matches your API key:
   - Use `MODEL=gemini/gemini-2.5-flash` with `GEMINI_API_KEY`
   - Use `MODEL=openai/gpt-4o` with `OPENAI_API_KEY`
5. Try generating a new API key

### Problem: Environment variables not loading
```
Error: Configuration not found
Error: Unsupported model 'None'. Supported models: ...
```

**Solutions:**
1. Ensure `.env` file is in the project root directory
2. Check file permissions: `chmod 644 .env`
3. Verify file format (no BOM, Unix line endings)
4. Use absolute paths if relative paths don't work
5. Test configuration validation:
   ```bash
   python -c "from document_to_anki.config import ModelConfig; print(ModelConfig.validate_and_get_model())"
   ```

## File Processing Errors

### Problem: Unsupported file format
```
Error: Unsupported file type: .xyz
```

**Solutions:**
1. Convert files to supported formats: PDF, DOCX, TXT, MD
2. Check file extensions are correct
3. For images with text, use OCR tools first
4. For other formats, copy text manually to a .txt file

### Problem: File too large
```
Error: File too large: 52428800 bytes (max: 52428800 bytes)
```

**Solutions:**
1. Split large documents into smaller files
2. Compress images in PDF files
3. Remove unnecessary content
4. Process files individually instead of in batches

### Problem: Corrupted or password-protected files
```
Error: Invalid or corrupted PDF file
Error: PDF file is encrypted
Error: No text content could be extracted from PDF
```

**Solutions:**
1. **For encrypted PDFs**: Remove password protection using PDF software
2. **For corrupted PDFs**: The application now handles malformed PDFs more gracefully with:
   - Automatic fallback to lenient parsing mode (`strict=False`)
   - Page-by-page error recovery (skips problematic pages)
   - Enhanced error reporting showing successful vs failed pages
3. **For image-based PDFs**: Use OCR software to convert images to text first
4. **For severely corrupted files**: Try re-saving or converting the file using different PDF software
5. **Check processing logs**: Enable verbose mode (`--verbose`) to see detailed page-by-page processing status

### Problem: No text extracted
```
Warning: No text content extracted from file
Error: No text content could be extracted from PDF
Warning: Skipping malformed page X in filename.pdf
```

**Solutions:**
1. **For image-based PDFs**: The file contains scanned images rather than text
   - Use OCR software (Adobe Acrobat, ABBYY FineReader) to convert images to text
   - Try online OCR services for small files
2. **For partially corrupted PDFs**: The application now processes pages individually
   - Check verbose logs to see which pages were successfully processed
   - Some pages may be extracted even if others fail
3. **For completely corrupted files**: 
   - Try opening and re-saving the file in different PDF software
   - Convert to a different format (DOCX, TXT) if possible
4. **Check file content**: Verify the file actually contains extractable text by opening it manually

### Problem: Permission denied
```
Error: Permission denied accessing file
```

**Solutions:**
1. Check file permissions: `ls -la filename`
2. Change permissions: `chmod 644 filename`
3. Ensure you own the file or have read access
4. Try copying the file to a different location

### Problem: Malformed or partially corrupted PDFs
```
Warning: Skipping malformed page X in filename.pdf
Info: Successfully extracted text from PDF: filename.pdf (15/20 pages processed)
```

**What this means:**
- The application detected and handled malformed pages in your PDF
- Some pages were successfully processed while others were skipped
- This is normal behavior for PDFs with mixed content or minor corruption

**Solutions:**
1. **Check the results**: Even with some failed pages, you may have extracted useful content
2. **Enable verbose logging**: Use `--verbose` to see detailed page-by-page processing
3. **For better results**: Try re-saving the PDF in different software to fix formatting issues
4. **Alternative extraction**: For critical content, manually copy text from problematic pages

## API and Network Issues

### Problem: Network connection failed
```
Error: Failed to connect to AI service
```

**Solutions:**
1. Check your internet connection
2. Verify firewall isn't blocking the application
3. Try using a VPN if in a restricted network
4. Check if the Gemini API service is operational

### Problem: Rate limiting
```
Error: Rate limit exceeded
```

**Solutions:**
1. Wait a few minutes before retrying
2. Process smaller batches of text
3. Check your API quota and usage
4. Consider upgrading your API plan

### Problem: Timeout errors
```
Error: Request timeout after 300 seconds
```

**Solutions:**
1. Process smaller documents
2. Check your internet connection speed
3. Increase timeout in configuration: `LITELLM_TIMEOUT=600`
4. Try again during off-peak hours

### Problem: API quota exceeded
```
Error: Quota exceeded for Gemini API
```

**Solutions:**
1. Check your usage at [Google Cloud Console](https://console.cloud.google.com)
2. Wait for quota reset (usually monthly)
3. Upgrade your API plan
4. Use smaller text chunks to reduce token usage

## Memory and Performance Issues

### Problem: Out of memory
```
Error: Memory allocation failed
MemoryError: Unable to allocate array
```

**Solutions:**
1. Close other applications to free memory
2. Process files individually instead of in batches
3. Restart the application
4. Use a machine with more RAM

### Problem: Slow processing
```
Processing is taking too long...
```

**Solutions:**
1. Process smaller files or fewer files at once
2. Check your internet connection speed
3. Use batch mode to skip interactive features: `--batch`
4. Monitor system resources (CPU, memory, network)

### Problem: High CPU usage
```
System becomes unresponsive during processing
```

**Solutions:**
1. Process files sequentially instead of in parallel
2. Close other CPU-intensive applications
3. Use verbose mode to monitor progress: `--verbose`
4. Consider processing during off-peak hours

## Web Interface Problems

### Problem: Web server won't start
```
Error: Address already in use
```

**Solutions:**
1. Check if another application is using port 8000: `lsof -i :8000`
2. Use a different port: `uvicorn document_to_anki.web.app:app --port 8080`
3. Kill the process using the port: `kill -9 <PID>`
4. Restart your computer if necessary

### Problem: File upload fails
```
Error: Upload failed - file too large
```

**Solutions:**
1. Check file size limits (50MB maximum)
2. Compress files before uploading
3. Upload files individually instead of in batches
4. Use the CLI for very large files

### Problem: Session expired
```
Error: Session not found
```

**Solutions:**
1. Refresh the page and start over
2. Sessions expire after 1 hour of inactivity
3. Complete your work within the session timeout
4. Use the CLI for long-running processes

### Problem: Browser compatibility
```
Interface not working properly in browser
```

**Solutions:**
1. Use a modern browser (Chrome, Firefox, Safari, Edge)
2. Enable JavaScript
3. Clear browser cache and cookies
4. Disable browser extensions that might interfere

## Export and Output Issues

### Problem: CSV export fails
```
Error: Failed to export flashcards to CSV
```

**Solutions:**
1. Check output directory exists and is writable
2. Ensure sufficient disk space
3. Close any applications using the output file
4. Try a different output location

### Problem: Invalid CSV format
```
Error: Anki import failed - invalid format
```

**Solutions:**
1. Open the CSV file in a text editor to check format
2. Ensure proper UTF-8 encoding
3. Check for special characters that might break CSV
4. Re-export with a different filename

### Problem: Empty output file
```
Warning: No flashcards to export
```

**Solutions:**
1. Check that flashcards were actually generated
2. Verify input documents contained meaningful text
3. Review any error messages during processing
4. Try with different input documents

### Problem: Permission denied writing output
```
Error: Permission denied writing to output file
```

**Solutions:**
1. Check directory permissions: `ls -la directory/`
2. Choose a different output location
3. Run with appropriate privileges
4. Ensure the output directory exists

## Getting Help

### Enable Verbose Logging

For better debugging information, enable verbose mode:

```bash
# CLI
document-to-anki input.pdf --verbose

# Environment variable
export LOG_LEVEL=DEBUG
```

### Check Log Files

The application uses structured logging. Look for:
- Error messages with specific error codes
- Warning messages about skipped content
- Debug information about processing steps

### Collect System Information

When reporting issues, include:
- Operating system and version
- Python version: `python --version`
- Package versions: `uv show`
- Error messages (full stack trace)
- Input file types and sizes
- Steps to reproduce the issue

### Common Diagnostic Commands

```bash
# Check Python and package versions
python --version
uv show

# Test model configuration
python -c "from document_to_anki.config import ModelConfig; print('Current model:', ModelConfig.get_model_from_env()); print('Supported models:', ModelConfig.get_supported_models())"

# Validate configuration
python -c "from document_to_anki.config import ModelConfig; ModelConfig.validate_and_get_model()"

# Run comprehensive integration test
python test_integration_check.py

# Run web app startup validation test
python test_startup_validation.py

# Test API connectivity
python -c "import litellm; print('litellm available')"

# Check file permissions
ls -la input-file.pdf

# Test with minimal example
echo "Test content for flashcard generation." > test.txt
document-to-anki test.txt --verbose

# Run code quality checks (includes automatic formatting)
make quality

# Check code formatting and style
uv run ruff check
uv run ruff format  # This will automatically format your code
```

### Report Issues

If you can't resolve the issue:

1. **Check existing issues** in the project repository
2. **Create a minimal reproduction case**
3. **Include system information** and error messages
4. **Describe expected vs actual behavior**
5. **Provide sample files** if possible (without sensitive content)

### Performance Optimization Tips

1. **Use appropriate file sizes**: Smaller files process faster
2. **Batch processing**: Use `batch-convert` for multiple files
3. **Skip preview**: Use `--no-preview --batch` for automated workflows
4. **Monitor resources**: Watch CPU, memory, and network usage
5. **Process incrementally**: Handle large document sets in smaller batches
6. **PDF processing optimization**: 
   - The application now handles malformed PDFs more efficiently
   - Pages are processed individually, so partial extraction is possible
   - Use verbose mode to monitor page-by-page processing progress
   - Corrupted pages are automatically skipped to continue processing

### Best Practices

1. **Test with sample files first** before processing important documents
2. **Keep backups** of original documents
3. **Use version control** for generated flashcards
4. **Monitor API usage** to avoid quota issues
5. **Regular updates**: Keep the application and dependencies updated

## Still Need Help?

If this guide doesn't solve your problem:

1. Search the project documentation
2. Check the project's issue tracker
3. Ask questions in the project's discussion forum
4. Contact the maintainers with detailed information

Remember to include:
- Your operating system
- Python version
- Complete error messages
- Steps to reproduce the issue
- Sample files (if applicable and non-sensitive)