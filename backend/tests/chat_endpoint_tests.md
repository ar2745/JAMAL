# Chat Endpoint Test Cases

## Base URL
```
http://localhost:5000/chat
```

## Test Cases

### 1. Basic Chat Tests
- **Test Case**: Simple chat without any context
  - Method: POST
  - Body:
    ```json
    {
        "message": "Hello, how are you?"
    }
    ```
  - Expected: 200 OK with response

- **Test Case**: Empty message
  - Method: POST
  - Body:
    ```json
    {
        "message": ""
    }
    ```
  - Expected: 200 OK with error message

- **Test Case**: Message too long (>512 chars)
  - Method: POST
  - Body:
    ```json
    {
        "message": "a".repeat(513)
    }
    ```
  - Expected: 200 OK with error message

### 2. Reasoning Tests
- **Test Case**: Simple reasoning request
  - Method: POST
  - Body:
    ```json
    {
        "message": "What is the meaning of life?",
        "reasoning": true
    }
    ```
  - Expected: 200 OK with reasoned response

### 3. Document Context Tests
- **Test Case**: Chat with document context
  - Method: POST
  - Body:
    ```json
    {
        "message": "What does this document say about X?",
        "document": "test_document.pdf"
    }
    ```
  - Expected: 200 OK with document-aware response

- **Test Case**: Non-existent document
  - Method: POST
  - Body:
    ```json
    {
        "message": "What does this document say?",
        "document": "nonexistent.pdf"
    }
    ```
  - Expected: 200 OK with error message

### 4. Link Context Tests
- **Test Case**: Chat with link context
  - Method: POST
  - Body:
    ```json
    {
        "message": "What does this webpage say about Y?",
        "link": "example.com.json"
    }
    ```
  - Expected: 200 OK with link-aware response

- **Test Case**: Non-existent link
  - Method: POST
  - Body:
    ```json
    {
        "message": "What does this webpage say?",
        "link": "nonexistent.json"
    }
    ```
  - Expected: 200 OK with error message

### 5. Combined Context Tests
- **Test Case**: Chat with both document and link context
  - Method: POST
  - Body:
    ```json
    {
        "message": "Compare the information from both sources",
        "document": "test_document.pdf",
        "link": "example.com.json"
    }
    ```
  - Expected: 200 OK with combined context response

### 6. Memory Tests
- **Test Case**: Chat with memory context
  - Method: POST
  - Body:
    ```json
    {
        "message": "Based on our previous conversation",
        "memories": [
            {
                "userMessage": {"text": "Previous question"},
                "botMessage": {"text": "Previous answer"}
            }
        ]
    }
    ```
  - Expected: 200 OK with memory-aware response

### 7. Special Commands
- **Test Case**: Goodbye command
  - Method: POST
  - Body:
    ```json
    {
        "message": "/bye"
    }
    ```
  - Expected: 200 OK with goodbye response

## Test Setup

1. Create a test document:
   - Upload a test PDF file using the `/document_upload` endpoint
   - Save the returned filename

2. Create a test link:
   - Upload a test URL using the `/link_upload` endpoint
   - Save the returned filename

3. Create test memories:
   - Use the `/store_memory` endpoint to create some test memories
   - Save the conversation ID

## Postman Collection Structure

```
Chat Endpoint Tests
├── Basic Chat
│   ├── Simple Chat
│   ├── Empty Message
│   └── Long Message
├── Reasoning
│   └── Simple Reasoning
├── Document Context
│   ├── With Document
│   └── Invalid Document
├── Link Context
│   ├── With Link
│   └── Invalid Link
├── Combined Context
│   └── Document and Link
├── Memory Context
│   └── With Memories
└── Special Commands
    └── Goodbye
```

## Environment Variables

Create a Postman environment with:
- `base_url`: http://localhost:5000
- `test_document`: [filename from document upload]
- `test_link`: [filename from link upload]
- `conversation_id`: [ID from memory creation] 