# Chat Endpoints

## Overview
The chat endpoints handle all communication with the chatbot, including sending messages, managing conversations, and retrieving chat history.

## Send Message
```http
POST /chat
```
Send a message to the chatbot and receive a response.

### Request
**Headers:**
- Content-Type: application/json

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| message | string | Yes | - | The message to send to the chatbot |
| type | string | No | "text" | Type of message (e.g., "text", "command") |
| metadata | object | No | {} | Additional metadata |
| conversation_id | string | No | - | ID of the conversation |
| document | string | No | - | Document ID to reference |
| link | string | No | - | Link ID to reference |
| user_id | string | No | - | User identifier |
| context | string | No | - | Additional context |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| response | string | The chatbot's response |

**Error (400 Bad Request):**
| Field | Type | Description |
|-------|------|-------------|
| error | string | Error message |

### Error Cases
| Error Case | Status Code | Description |
|------------|-------------|-------------|
| Empty input message | 400 | Message cannot be empty |
| Message too long | 400 | Message exceeds 512 characters |
| Invalid input type | 400 | Message must be a string |
| Server error | 500 | Internal server error |

### Example Usage
```typescript
const sendMessage = async (message: string, conversationId?: string) => {
  const response = await fetch('http://localhost:5000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId
    })
  });
  
  const data = await response.json();
  return data.response;
};
```

### Notes
- The endpoint supports both simple chat and document/link-based conversations
- Messages are processed asynchronously
- Response time may vary based on message complexity
- The endpoint tracks user activity and chat analytics
- Maximum message length is 512 characters 