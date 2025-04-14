# Link Endpoints

## Overview
The link endpoints handle URL processing, storage, and management. Links can be used as context for chat conversations and are processed to extract relevant content.

## List Links
```http
GET /links
```
Retrieve a list of all processed links with their metadata.

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| links | Array<Link> | List of processed links |

**Link Object:**
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique link identifier |
| url | string | Original URL |
| title | string | Page title |
| description | string | Page description |
| content | string | Extracted content |
| timestamp | string | ISO timestamp of processing |

## Process Link
```http
POST /link_upload
```
Process and store a new URL.

### Request
**Headers:**
- Content-Type: application/json

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | Yes | - | URL to process |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| message | string | Success message |
| link | object | Processed link data |

**Link Object:**
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique link identifier |
| title | string | Page title |
| description | string | Page description |
| image | string | Optional: Featured image URL |
| timestamp | string | ISO timestamp |

**Error (400 Bad Request):**
| Field | Type | Description |
|-------|------|-------------|
| error | string | Error message |

### Error Cases
| Error Case | Status Code | Description |
|------------|-------------|-------------|
| Invalid URL | 400 | URL format is invalid |
| URL not accessible | 400 | Cannot access the URL |
| Processing timeout | 408 | Processing took too long |
| Content extraction error | 500 | Error extracting content |

## Delete Link
```http
POST /link_delete
```
Delete a processed link.

### Request
**Headers:**
- Content-Type: application/json

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| filename | string | Yes | - | Name of the link file to delete |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| response | string | Success message |

**Error (404 Not Found):**
| Field | Type | Description |
|-------|------|-------------|
| response | string | Error message |

### Error Cases
| Error Case | Status Code | Description |
|------------|-------------|-------------|
| Link not found | 404 | Link does not exist |
| Deletion permission error | 403 | Insufficient permissions |
| Storage system error | 500 | Error deleting link |

## Get Link Metadata
```http
POST /api/link_metadata
```
Retrieve metadata for a URL without storing it.

### Request
**Headers:**
- Content-Type: application/json

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | Yes | - | URL to analyze |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| title | string | Page title |
| description | string | Page description |
| image | string | Optional: Featured image URL |
| content | string | Extracted content |

### Example Usage
```typescript
const processLink = async (url: string) => {
  const response = await fetch('http://localhost:5000/link_upload', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ url })
  });
  
  return await response.json();
};

const getLinkMetadata = async (url: string) => {
  const response = await fetch('http://localhost:5000/api/link_metadata', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ url })
  });
  
  return await response.json();
};
```

### Notes
- Links are processed asynchronously
- Content extraction includes title, description, and main content
- Images and other media may be extracted when available
- Links are stored in the server's links directory
- Metadata is stored in JSON format
- Link content is indexed for search functionality
- Processing timeouts after 30 seconds
- Rate limiting may apply to prevent abuse 