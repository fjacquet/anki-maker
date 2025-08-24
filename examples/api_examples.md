# API Examples and Swagger Documentation

This document provides practical examples for using the Document to Anki CLI API, including how to access and use the interactive Swagger documentation.

## Interactive API Documentation (Swagger/OpenAPI)

### Quick Start

1. **Start the web server**:
   ```bash
   document-to-anki-web
   ```

2. **Access the documentation**:
   - **Swagger UI**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc
   - **OpenAPI JSON**: http://localhost:8000/openapi.json

### Using Swagger UI

The Swagger UI provides an interactive interface where you can:

#### 1. **Explore Endpoints**
- Browse all available API endpoints
- View HTTP methods (GET, POST, PUT, DELETE)
- See detailed parameter descriptions
- Review response schemas and examples

#### 2. **Test API Calls**
- Click "Try it out" on any endpoint
- Fill in required parameters
- Execute requests directly from the browser
- View real responses with status codes and data

#### 3. **View Schemas**
- Examine Pydantic model definitions
- Understand request/response data structures
- See validation rules and constraints

### Example: Testing File Upload via Swagger

1. Navigate to http://localhost:8000/docs
2. Find the `POST /api/upload` endpoint
3. Click "Try it out"
4. Upload a test file:
   - Click "Choose Files" and select a PDF, DOCX, TXT, or MD file
   - Optionally provide a session_id
5. Click "Execute"
6. View the response with your new session_id

### Example: Monitoring Processing Status

1. Copy the session_id from the upload response
2. Find the `GET /api/status/{session_id}` endpoint
3. Click "Try it out"
4. Paste your session_id in the parameter field
5. Click "Execute"
6. See real-time processing status and progress

## REST API Examples

### Python Examples

#### Basic File Upload and Processing

```python
import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
FILE_PATH = "example.pdf"

def upload_and_process_file():
    """Complete example of uploading and processing a file."""
    
    # Step 1: Upload file
    print("Uploading file...")
    with open(FILE_PATH, 'rb') as f:
        files = {'files': f}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        return None
    
    data = response.json()
    session_id = data['session_id']
    print(f"Upload successful! Session ID: {session_id}")
    
    # Step 2: Monitor processing
    print("Monitoring processing...")
    while True:
        status_response = requests.get(f"{BASE_URL}/status/{session_id}")
        if status_response.status_code != 200:
            print(f"Status check failed: {status_response.text}")
            return None
        
        status_data = status_response.json()
        print(f"Status: {status_data['status']}, Progress: {status_data['progress']}%")
        
        if status_data['status'] == 'completed':
            print(f"Processing completed! Generated {status_data['flashcard_count']} flashcards")
            break
        elif status_data['status'] == 'error':
            print(f"Processing failed: {status_data['message']}")
            return None
        
        time.sleep(2)  # Wait 2 seconds before checking again
    
    # Step 3: Get flashcards
    print("Retrieving flashcards...")
    flashcards_response = requests.get(f"{BASE_URL}/flashcards/{session_id}")
    if flashcards_response.status_code != 200:
        print(f"Failed to get flashcards: {flashcards_response.text}")
        return None
    
    flashcards = flashcards_response.json()
    print(f"Retrieved {len(flashcards)} flashcards")
    
    # Step 4: Export to CSV
    print("Exporting to CSV...")
    export_data = {"filename": "my-flashcards.csv"}
    export_response = requests.post(
        f"{BASE_URL}/export/{session_id}", 
        json=export_data
    )
    
    if export_response.status_code == 200:
        with open("my-flashcards.csv", 'wb') as f:
            f.write(export_response.content)
        print("Export successful!")
    else:
        print(f"Export failed: {export_response.text}")
    
    return session_id

if __name__ == "__main__":
    session_id = upload_and_process_file()
    if session_id:
        print(f"✅ Processing completed successfully! Session: {session_id}")
    else:
        print("❌ Processing failed!")
```

#### Flashcard Management Example

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

def manage_flashcards(session_id: str):
    """Example of managing flashcards via API."""
    
    # Get current flashcards
    response = requests.get(f"{BASE_URL}/flashcards/{session_id}")
    flashcards = response.json()
    print(f"Current flashcards: {len(flashcards)}")
    
    if flashcards:
        # Edit the first flashcard
        first_card = flashcards[0]
        edit_data = {
            "question": "Updated: " + first_card['question'],
            "answer": "Updated: " + first_card['answer']
        }
        
        edit_response = requests.put(
            f"{BASE_URL}/flashcards/{session_id}/{first_card['id']}", 
            json=edit_data
        )
        print(f"Edit result: {edit_response.json()}")
    
    # Add a new flashcard
    new_card = {
        "question": "What is the Document to Anki CLI?",
        "answer": "A tool that converts documents into Anki flashcards using AI",
        "card_type": "qa",
        "source_file": "manual_entry"
    }
    
    add_response = requests.post(
        f"{BASE_URL}/flashcards/{session_id}", 
        json=new_card
    )
    print(f"Add result: {add_response.json()}")
    
    # Get updated count
    response = requests.get(f"{BASE_URL}/flashcards/{session_id}")
    updated_flashcards = response.json()
    print(f"Updated flashcard count: {len(updated_flashcards)}")

# Usage
# manage_flashcards("your-session-id-here")
```

### cURL Examples

#### Upload File

```bash
# Upload a single file
curl -X POST "http://localhost:8000/api/upload" \
  -F "files=@document.pdf"

# Upload multiple files
curl -X POST "http://localhost:8000/api/upload" \
  -F "files=@document1.pdf" \
  -F "files=@document2.docx"
```

#### Check Processing Status

```bash
# Replace SESSION_ID with actual session ID
curl -X GET "http://localhost:8000/api/status/SESSION_ID"
```

#### Get Flashcards

```bash
curl -X GET "http://localhost:8000/api/flashcards/SESSION_ID"
```

#### Edit Flashcard

```bash
curl -X PUT "http://localhost:8000/api/flashcards/SESSION_ID/FLASHCARD_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Updated question text",
    "answer": "Updated answer text"
  }'
```

#### Add New Flashcard

```bash
curl -X POST "http://localhost:8000/api/flashcards/SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is machine learning?",
    "answer": "A subset of AI that enables computers to learn from data",
    "card_type": "qa",
    "source_file": "manual_entry"
  }'
```

#### Export to CSV

```bash
curl -X POST "http://localhost:8000/api/export/SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"filename": "my-flashcards.csv"}' \
  --output flashcards.csv
```

#### Health Check

```bash
curl -X GET "http://localhost:8000/api/health"
```

### JavaScript/Node.js Examples

#### Using Fetch API

```javascript
// Upload file and process
async function uploadAndProcess(file) {
    const formData = new FormData();
    formData.append('files', file);
    
    try {
        // Upload
        const uploadResponse = await fetch('http://localhost:8000/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const uploadData = await uploadResponse.json();
        const sessionId = uploadData.session_id;
        console.log('Upload successful:', sessionId);
        
        // Monitor processing
        while (true) {
            const statusResponse = await fetch(`http://localhost:8000/api/status/${sessionId}`);
            const statusData = await statusResponse.json();
            
            console.log(`Status: ${statusData.status}, Progress: ${statusData.progress}%`);
            
            if (statusData.status === 'completed') {
                console.log(`Completed! Generated ${statusData.flashcard_count} flashcards`);
                break;
            } else if (statusData.status === 'error') {
                console.error('Processing failed:', statusData.message);
                return null;
            }
            
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
        }
        
        // Get flashcards
        const flashcardsResponse = await fetch(`http://localhost:8000/api/flashcards/${sessionId}`);
        const flashcards = await flashcardsResponse.json();
        console.log('Retrieved flashcards:', flashcards.length);
        
        return { sessionId, flashcards };
        
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

// Usage in browser
// const fileInput = document.getElementById('file-input');
// const file = fileInput.files[0];
// uploadAndProcess(file);
```

#### Using Axios

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function processDocument(filePath) {
    const baseURL = 'http://localhost:8000/api';
    
    try {
        // Create form data
        const formData = new FormData();
        formData.append('files', fs.createReadStream(filePath));
        
        // Upload file
        const uploadResponse = await axios.post(`${baseURL}/upload`, formData, {
            headers: formData.getHeaders()
        });
        
        const sessionId = uploadResponse.data.session_id;
        console.log('Session ID:', sessionId);
        
        // Wait for completion
        let completed = false;
        while (!completed) {
            const statusResponse = await axios.get(`${baseURL}/status/${sessionId}`);
            const status = statusResponse.data;
            
            console.log(`Progress: ${status.progress}%`);
            
            if (status.status === 'completed') {
                completed = true;
                console.log(`Generated ${status.flashcard_count} flashcards`);
            } else if (status.status === 'error') {
                throw new Error(status.message);
            }
            
            if (!completed) {
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
        
        // Export CSV
        const exportResponse = await axios.post(`${baseURL}/export/${sessionId}`, {
            filename: 'flashcards.csv'
        }, {
            responseType: 'blob'
        });
        
        fs.writeFileSync('flashcards.csv', exportResponse.data);
        console.log('CSV exported successfully!');
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

// Usage
// processDocument('document.pdf');
```

## Testing with Postman

### Import OpenAPI Specification

1. Start the web server: `document-to-anki-web`
2. In Postman, click "Import"
3. Choose "Link" and enter: `http://localhost:8000/openapi.json`
4. Postman will automatically create a collection with all endpoints

### Environment Variables

Create a Postman environment with:
- `base_url`: `http://localhost:8000/api`
- `session_id`: (set this after uploading a file)

### Example Collection Structure

```
Document to Anki API/
├── Upload Files
├── Check Status
├── Get Flashcards
├── Edit Flashcard
├── Add Flashcard
├── Delete Flashcard
├── Export CSV
├── Health Check
└── Clean Session
```

## Error Handling Examples

### Python Error Handling

```python
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

def robust_api_call(url, method='GET', **kwargs):
    """Make API call with comprehensive error handling."""
    try:
        response = requests.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return response.json()
        
    except ConnectionError:
        print("❌ Connection error: Cannot reach the server")
        print("💡 Make sure the web server is running: document-to-anki-web")
        
    except Timeout:
        print("❌ Request timeout: Server took too long to respond")
        print("💡 Try again or check server performance")
        
    except requests.HTTPError as e:
        print(f"❌ HTTP error {e.response.status_code}: {e.response.text}")
        if e.response.status_code == 404:
            print("💡 Check that the session ID is correct")
        elif e.response.status_code == 400:
            print("💡 Check request data format and required fields")
            
    except ValueError as e:
        print(f"❌ JSON decode error: {e}")
        print("💡 Server response was not valid JSON")
        
    except RequestException as e:
        print(f"❌ Request error: {e}")
        
    return None

# Usage
result = robust_api_call("http://localhost:8000/api/health")
if result:
    print("✅ API is healthy:", result)
```

### JavaScript Error Handling

```javascript
async function safeApiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            timeout: 30000,
            ...options
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        return { success: true, data };
        
    } catch (error) {
        console.error('API call failed:', error.message);
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            console.log('💡 Check that the web server is running');
        } else if (error.message.includes('timeout')) {
            console.log('💡 Request timed out, try again');
        } else if (error.message.includes('404')) {
            console.log('💡 Check that the session ID is correct');
        }
        
        return { success: false, error: error.message };
    }
}

// Usage
const result = await safeApiCall('http://localhost:8000/api/health');
if (result.success) {
    console.log('✅ API response:', result.data);
} else {
    console.log('❌ API call failed:', result.error);
}
```

## Best Practices

### 1. **Session Management**
- Always store session IDs for ongoing operations
- Clean up sessions when done: `DELETE /api/sessions/{session_id}`
- Sessions expire after 1 hour of inactivity

### 2. **File Upload Guidelines**
- Maximum file size: 50MB per file
- Supported formats: PDF, DOCX, TXT, MD, ZIP
- Use multipart/form-data for file uploads
- Check file validation before uploading

### 3. **Polling for Status**
- Poll status every 2-5 seconds during processing
- Implement exponential backoff for failed requests
- Set reasonable timeouts (5-10 minutes for large documents)

### 4. **Error Handling**
- Always check HTTP status codes
- Parse error messages for actionable guidance
- Implement retry logic for transient failures
- Log errors for debugging

### 5. **Performance Optimization**
- Process multiple files in separate sessions for parallel processing
- Use appropriate chunk sizes for large documents
- Monitor memory usage for large file uploads

This comprehensive guide should help you effectively use both the interactive Swagger documentation and the REST API programmatically!