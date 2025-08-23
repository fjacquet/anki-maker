# Security Guidelines

This document outlines the security measures and best practices implemented in the Document to Anki CLI application.

## Security Features

### 1. Environment Variable Security

- **Centralized Configuration**: All environment variables are handled through the `ModelConfig` and `Settings` classes in `config.py`
- **No Hardcoded Secrets**: API keys and sensitive data are only accessed via environment variables
- **Validation**: Model configuration is validated on startup with clear error messages
- **Default Values**: Secure defaults are provided for all configuration options

### 2. Input Validation and Sanitization

#### File Upload Security
- **File Type Validation**: Only supported file types (.pdf, .docx, .txt, .md, .zip) are accepted
- **File Size Limits**: Maximum file size of 50MB to prevent DoS attacks
- **Path Traversal Protection**: All file paths are validated to prevent directory traversal attacks
- **MIME Type Checking**: Additional validation using MIME type detection
- **ZIP Bomb Protection**: Limits on number of files and extraction size for ZIP archives

#### Web Interface Security
- **Pydantic Validation**: All API inputs are validated using Pydantic models
- **Request Size Limits**: File upload size limits enforced at multiple levels
- **Session Management**: Secure session handling with automatic cleanup
- **Input Sanitization**: All user inputs are sanitized and validated

### 3. Web Application Security

#### Security Headers
The web interface implements comprehensive security headers:

```python
# Security headers automatically added to all responses
"X-Content-Type-Options": "nosniff"
"X-Frame-Options": "DENY"
"X-XSS-Protection": "1; mode=block"
"Referrer-Policy": "strict-origin-when-cross-origin"
"Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; ..."
```

#### CORS Configuration
- **Restricted Origins**: Only specific origins are allowed for CORS
- **Credential Handling**: Secure credential handling for cross-origin requests
- **Method Restrictions**: Only necessary HTTP methods are allowed

#### Session Security
- **Automatic Cleanup**: Sessions expire after 1 hour of inactivity
- **Temporary File Management**: All temporary files are cleaned up automatically
- **Memory Management**: Session data is properly managed to prevent memory leaks

### 4. File System Security

#### Path Security
- **Path Validation**: All file paths are validated for security issues
- **Directory Restrictions**: File operations are restricted to safe directories
- **Temporary File Handling**: Secure creation and cleanup of temporary files
- **Permission Checks**: File permissions are validated before processing

#### Archive Security
- **ZIP Extraction Safety**: Protection against ZIP bombs and path traversal in archives
- **File Count Limits**: Maximum number of files that can be extracted from archives
- **Size Limits**: Total extraction size limits to prevent disk space exhaustion

### 5. Dependency Security

#### Security Scanning
- **Bandit**: Static security analysis for Python code
- **pip-audit**: Dependency vulnerability scanning
- **Regular Updates**: Dependencies are regularly updated to address security issues

#### Configuration
```toml
[tool.bandit]
exclude_dirs = ["tests", "venv", ".venv"]
skips = ["B101", "B601"]  # Skip specific checks where appropriate
```

### 6. API Security

#### Authentication
- **API Key Validation**: LLM API keys are validated before use
- **Provider-Specific Keys**: Different API keys for different LLM providers
- **Key Rotation**: Support for easy API key rotation via environment variables

#### Rate Limiting
- **Request Limits**: Built-in rate limiting for LLM API calls
- **Retry Logic**: Exponential backoff for failed requests
- **Timeout Handling**: Proper timeout handling for all external API calls

## Security Best Practices

### For Developers

1. **Environment Variables**
   - Never commit API keys or secrets to version control
   - Use `.env.example` for documentation, never `.env`
   - Validate all environment variables on startup

2. **Input Validation**
   - Always validate user inputs using Pydantic models
   - Sanitize file paths and names
   - Check file types and sizes before processing

3. **Error Handling**
   - Don't expose sensitive information in error messages
   - Log security events appropriately
   - Provide helpful but safe error messages to users

4. **Dependencies**
   - Regularly update dependencies
   - Run security scans before releases
   - Monitor for security advisories

### For Users

1. **API Keys**
   - Store API keys in environment variables, not in code
   - Use different API keys for different environments
   - Rotate API keys regularly

2. **File Uploads**
   - Only upload trusted documents
   - Be aware of file size limits
   - Verify file contents before processing

3. **Web Interface**
   - Use HTTPS in production
   - Keep browser updated
   - Be cautious with file uploads from untrusted sources

## Security Validation

### Automated Checks

The application includes automated security validation:

```bash
# Run comprehensive security checks
make security-full

# Run security validation script
make security-validate

# Individual security tools
make security  # Bandit code analysis
make audit     # Dependency vulnerability scan
```

### Manual Security Review

Regular security reviews should include:

1. **Code Review**: Review all code changes for security implications
2. **Dependency Audit**: Check for known vulnerabilities in dependencies
3. **Configuration Review**: Ensure secure configuration in all environments
4. **Access Control**: Verify proper access controls and permissions

## Incident Response

### Security Issue Reporting

If you discover a security vulnerability:

1. **Do not** create a public GitHub issue
2. Email security concerns to the maintainers
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be addressed before public disclosure

### Response Process

1. **Assessment**: Evaluate the severity and impact of the issue
2. **Fix Development**: Develop and test a fix for the vulnerability
3. **Release**: Release a security update as quickly as possible
4. **Communication**: Notify users about the security update
5. **Post-Mortem**: Review the incident and improve security measures

## Compliance and Standards

### Security Standards

The application follows these security standards:

- **OWASP Top 10**: Protection against common web application vulnerabilities
- **NIST Cybersecurity Framework**: Implementation of cybersecurity best practices
- **Secure Coding Practices**: Following secure coding guidelines for Python

### Privacy Considerations

- **Data Minimization**: Only necessary data is processed and stored
- **Temporary Storage**: User documents are processed temporarily and cleaned up
- **No Persistent Storage**: No user data is permanently stored by default
- **API Privacy**: LLM API calls follow provider privacy policies

## Security Configuration

### Production Deployment

For production deployments:

1. **Environment Variables**
   ```bash
   # Required
   GEMINI_API_KEY=your-api-key-here
   MODEL=gemini/gemini-2.5-flash
   
   # Security
   SECRET_KEY=your-secure-secret-key
   WEB_HOST=127.0.0.1  # Bind to localhost only
   WEB_DEBUG=false
   
   # Optional security enhancements
   HTTPS_ONLY=true
   SECURE_COOKIES=true
   ```

2. **Web Server Configuration**
   - Use HTTPS with valid SSL certificates
   - Configure proper firewall rules
   - Set up reverse proxy with security headers
   - Enable request logging and monitoring

3. **File System Security**
   - Restrict file permissions appropriately
   - Use dedicated user account for the application
   - Configure secure temporary directory
   - Set up log rotation and monitoring

### Development Environment

For development:

1. Use `.env` file for local configuration
2. Never commit real API keys
3. Use test/mock API keys when possible
4. Run security checks before committing code

## Security Updates

### Staying Updated

- Monitor security advisories for Python and dependencies
- Subscribe to security mailing lists for used libraries
- Regularly run security scans and address findings
- Keep the application and its dependencies updated

### Update Process

1. **Assessment**: Evaluate security updates for applicability
2. **Testing**: Test security updates in development environment
3. **Deployment**: Deploy security updates promptly
4. **Verification**: Verify that security updates are effective
5. **Documentation**: Update security documentation as needed

---

For questions about security practices or to report security issues, please contact the maintainers through appropriate channels.