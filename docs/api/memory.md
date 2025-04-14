# Memory Endpoints

## Overview
The memory endpoints handle conversation memory management, allowing the storage and retrieval of chat history and context. This enables the chatbot to maintain context across conversations and provide more relevant responses.

## Store Memory
```http
POST /store_memory
```
Store a conversation in memory for future reference.

### Request
**Headers:**
- Content-Type: application/json

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| userMessage | object | Yes | - | User's message object |
| botMessage | object | Yes | - | Bot's response object |
| documents | string[] | No | [] | Array of document IDs |
| links | string[] | No | [] | Array of link IDs |
| conversationId | string | Yes | - | Conversation identifier |

**Message Object:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| text | string | Yes | - | Message content |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| message | string | Success message |
| memory | object | Stored memory object |

**Error (400 Bad Request):**
| Field | Type | Description |
|-------|------|-------------|
| error | string | Error message |

### Error Cases
| Error Case | Status Code | Description |
|------------|-------------|-------------|
| Missing required fields | 400 | Required fields are missing |
| Invalid conversation ID | 400 | Conversation ID is invalid |
| Storage error | 500 | Error storing memory |
| Memory limit exceeded | 400 | Memory storage limit reached |

## Retrieve Memory
```http
POST /retrieve_memory
```
Retrieve relevant memories for a conversation based on a query.

### Request
**Headers:**
- Content-Type: application/json

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| conversationId | string | Yes | - | Conversation identifier |
| query | string | Yes | - | Search query |
| limit | number | No | 5 | Maximum number of memories to return |

### Response
**Success (200 OK):**
| Field | Type | Description |
|-------|------|-------------|
| memories | Array<Memory> | List of relevant memories |

**Memory Object:**
| Field | Type | Description |
|-------|------|-------------|
| text | string | Memory content |
| timestamp | string | ISO timestamp |
| type | string | Memory type (e.g., "user", "bot", "context") |

**Error (400 Bad Request):**
| Field | Type | Description |
|-------|------|-------------|
| error | string | Error message |

### Error Cases
| Error Case | Status Code | Description |
|------------|-------------|-------------|
| Missing conversation ID | 400 | Conversation ID is required |
| Invalid query | 400 | Query is invalid |
| Retrieval error | 500 | Error retrieving memories |
| No memories found | 404 | No relevant memories found |

### Example Usage
```typescript
const storeMemory = async (
  conversationId: string,
  userMessage: string,
  botMessage: string,
  documents?: string[],
  links?: string[]
) => {
  const response = await fetch('http://localhost:5000/store_memory', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      userMessage: { text: userMessage },
      botMessage: { text: botMessage },
      documents,
      links,
      conversationId
    })
  });
  
  return await response.json();
};

const retrieveMemory = async (conversationId: string, query: string, limit = 5) => {
  const response = await fetch('http://localhost:5000/retrieve_memory', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      conversationId,
      query,
      limit
    })
  });
  
  return await response.json();
};
```

### Notes
- Memories are stored in a vector database for efficient retrieval
- Each memory includes metadata for context and relevance
- Memories can be associated with documents and links
- Memory retrieval uses semantic search
- Memories are automatically cleaned up after a configurable period
- Memory storage is limited per conversation
- Memories can be used to provide context for future responses
- The system maintains conversation history for continuity 