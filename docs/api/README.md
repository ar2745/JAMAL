# API Documentation

## Overview
The API provides endpoints for chat functionality, document management, link processing, memory management, and analytics. All endpoints return JSON responses and use standard HTTP status codes.

## Base URL
```
http://localhost:5000
```

## Authentication
Currently, the API does not require authentication. All endpoints are publicly accessible.

## Endpoints

### Chat

#### Send Message
```http
POST /chat
```
Send a message to the chatbot and receive a response.

**Request Body:**
```json
{
  "message": "string",
  "type": "string",
  "metadata": {},
  "conversation_id": "string",
  "document": "string",
  "link": "string",
  "user_id": "string",
  "context": "string"
}
```

**Response:**
```json
{
  "response": "string"
}
```

### Documents

#### List Documents
```http
GET /documents
```
Retrieve a list of all uploaded documents.

**Response:**
```json
{
  "documents": [
    {
      "id": "string",
      "filename": "string",
      "content": "string",
      "type": "string",
      "size": "number",
      "timestamp": "string"
    }
  ]
}
```

#### Upload Document
```http
POST /document_upload
```
Upload a new document for processing.

**Request:**
- Content-Type: multipart/form-data
- Parameter: `file` (file)

**Response:**
```json
{
  "message": "string",
  "content": "string",
  "metadata": {
    "type": "string",
    "size": "number",
    "timestamp": "string",
    "content": "string"
  }
}
```

#### Delete Document
```http
POST /document_delete
```
Delete an uploaded document.

**Request Body:**
```json
{
  "filename": "string"
}
```

**Response:**
```json
{
  "message": "string"
}
```

### Links

#### List Links
```http
GET /links
```
Retrieve a list of all processed links.

**Response:**
```json
{
  "links": [
    {
      "id": "string",
      "url": "string",
      "title": "string",
      "description": "string",
      "content": "string",
      "timestamp": "string"
    }
  ]
}
```

#### Process Link
```http
POST /link_upload
```
Process and store a new link.

**Request Body:**
```json
{
  "url": "string"
}
```

**Response:**
```json
{
  "message": "string",
  "link": {
    "id": "string",
    "title": "string",
    "description": "string",
    "image": "string",
    "timestamp": "string"
  }
}
```

#### Delete Link
```http
POST /link_delete
```
Delete a processed link.

**Request Body:**
```json
{
  "filename": "string"
}
```

**Response:**
```json
{
  "response": "string"
}
```

### Memory Management

#### Store Memory
```http
POST /store_memory
```
Store a conversation in memory.

**Request Body:**
```json
{
  "userMessage": "string",
  "botMessage": "string",
  "documents": ["string"],
  "links": ["string"],
  "conversationId": "string"
}
```

**Response:**
```json
{
  "message": "string",
  "memory": {}
}
```

#### Retrieve Memory
```http
POST /retrieve_memory
```
Retrieve relevant memories for a conversation.

**Request Body:**
```json
{
  "conversationId": "string",
  "query": "string",
  "limit": "number"
}
```

**Response:**
```json
{
  "memories": [
    {
      "text": "string",
      "timestamp": "string",
      "type": "string"
    }
  ]
}
```

### Analytics

#### Chat Analytics
```http
GET /analytics/chat
```
Get chat analytics data.

**Query Parameters:**
- `chat_id` (optional): Specific chat ID for statistics

**Response:**
```json
{
  "message_count": "number",
  "last_activity": "string",
  "document_count": "number",
  "link_count": "number"
}
```

#### Document Analytics
```http
GET /analytics/documents
```
Get document analytics data.

**Query Parameters:**
- `chat_id` (optional): Specific chat ID for statistics

**Response:**
```json
{
  "count": "number",
  "total_size": "number",
  "types": {}
}
```

#### Link Analytics
```http
GET /analytics/links
```
Get link analytics data.

**Query Parameters:**
- `chat_id` (optional): Specific chat ID for statistics

**Response:**
```json
{
  "count": "number",
  "domains": {}
}
```

#### Usage Analytics
```http
GET /analytics/usage
```
Get usage analytics data.

**Response:**
```json
{
  "daily_active": "number",
  "weekly_active": "number",
  "monthly_active": "number",
  "peak_hours": ["number"]
}
```

## Error Responses

All endpoints may return the following error responses:

- `400 Bad Request`: Invalid input data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Error responses include a message explaining the error:

```json
{
  "error": "string"
}
```

## Rate Limiting
Currently, there are no rate limits implemented on the API endpoints.

## CORS
The API supports Cross-Origin Resource Sharing (CORS) for all origins. 