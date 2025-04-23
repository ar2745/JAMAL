# Chat Endpoints

## Overview
The chat endpoints handle all communication with the chatbot, utilizing a service-based architecture for improved modularity and maintainability. The system now integrates with an LLM service for enhanced response generation.

## Send Message
```http
POST /chat
```
Send a message to the chatbot and receive a response. The message is processed through the LLM integration service for intelligent response generation.

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
| llm_config | object | No | {} | LLM-specific configuration options |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| response | string | The chatbot's response |
| metadata | object | Response metadata including processing time and confidence scores |
| conversation_id | string | ID of the current conversation |

**Error (400 Bad Request):**
| Field | Type | Description |
|-------|------|-------------|
| error | string | Error message |
| code | string | Error code |
| details | object | Additional error details |

### Error Cases
| Error Case | Status Code | Description |
|------------|-------------|-------------|
| Empty input message | 400 | Message cannot be empty |
| Message too long | 400 | Message exceeds 512 characters |
| Invalid input type | 400 | Message must be a string |
| LLM service error | 503 | LLM service unavailable or error |
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
      conversation_id: conversationId,
      llm_config: {
        model: "gpt-4",
        temperature: 0.7,
        max_tokens: 150
      }
    })
  });
  
  const data = await response.json();
  return {
    response: data.response,
    conversationId: data.conversation_id,
    metadata: data.metadata
  };
};
```

### Notes
- The endpoint now uses a service-based architecture for improved modularity
- LLM integration provides enhanced response generation capabilities
- Messages are processed asynchronously with improved error handling
- Response time may vary based on message complexity and LLM configuration
- Maximum message length is 512 characters
- The endpoint supports both simple chat and document/link-based conversations
- All responses include metadata for improved tracking and analytics 