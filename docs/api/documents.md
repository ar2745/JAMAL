# Document Endpoints

## Overview
The document endpoints handle document management, including uploading, listing, and deleting documents. Documents can be used as context for chat conversations.

## List Documents
```http
GET /documents
```
Retrieve a list of all uploaded documents with their metadata.

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| documents | Array<Document> | List of documents with metadata |

**Document Object:**
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique document identifier |
| filename | string | Original filename |
| content | string | Extracted text content |
| type | string | MIME type (e.g., "text/plain", "application/pdf") |
| size | number | File size in bytes |
| timestamp | string | ISO timestamp of upload |

## Upload Document
```http
POST /document_upload
```
Upload a new document for processing and storage.

### Request
**Headers:**
- Content-Type: multipart/form-data

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| file | File | Yes | - | The document file to upload |
| chat_id | string | No | - | Associated chat ID |
| user_id | string | No | - | User identifier |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| message | string | Success message |
| content | string | Extracted text content |
| metadata | object | Document metadata |

**Metadata Object:**
| Field | Type | Description |
|-------|------|-------------|
| type | string | MIME type |
| size | number | File size in bytes |
| timestamp | string | ISO timestamp |
| content | string | Extracted text content |

**Error (400 Bad Request):**
| Field | Type | Description |
|-------|------|-------------|
| error | string | Error message |

### Error Cases
| Error Case | Status Code | Description |
|------------|-------------|-------------|
| No file provided | 400 | File is required |
| Invalid file type | 400 | Unsupported file format |
| File processing error | 500 | Error processing file |
| Storage error | 500 | Error saving file |

## Delete Document
```http
POST /document_delete
```
Delete an uploaded document.

### Request
**Headers:**
- Content-Type: application/json

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| filename | string | Yes | - | Name of the file to delete |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| message | string | Success message |

**Error (404 Not Found):**
| Field | Type | Description |
|-------|------|-------------|
| error | string | Error message |

### Error Cases
| Error Case | Status Code | Description |
|------------|-------------|-------------|
| File not found | 404 | Document does not exist |
| Deletion permission error | 403 | Insufficient permissions |
| Storage system error | 500 | Error deleting file |

### Example Usage
```typescript
const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:5000/document_upload', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
};

const deleteDocument = async (filename: string) => {
  const response = await fetch('http://localhost:5000/document_delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ filename })
  });
  
  return await response.json();
};
```

### Notes
- Supported file types: PDF, TXT, DOCX, JSON
- Maximum file size: 10MB
- Documents are processed asynchronously
- Content extraction may vary by file type
- Documents are stored in the server's uploads directory
- Metadata is stored in separate JSON files
- Document content is indexed for search functionality 