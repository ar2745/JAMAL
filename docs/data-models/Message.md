# Message Model

## Overview
The Message model represents a single message in the chat system. It supports different types of messages including text messages and web search results.

## Schema
```typescript
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  type: "text" | "web_search";
  timestamp: string;
  metadata?: {
    isWebSearch?: boolean;
    searchResults?: Array<{
      title: string;
      url: string;
      snippet: string;
    }>;
  };
}
```

## Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier for the message |
| role | "user" \| "assistant" | Yes | Sender of the message |
| content | string | Yes | The message content |
| type | "text" \| "web_search" | Yes | Type of message |
| timestamp | string | Yes | ISO timestamp of when the message was sent |
| metadata | object | No | Additional message metadata |

### Metadata Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| isWebSearch | boolean | No | Indicates if this is a web search message |
| searchResults | Array<SearchResult> | No | Results from web search |

### SearchResult Type
```typescript
interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}
```

## Relationships
- Messages are associated with a Chat
- Messages can reference Documents and Links through context
- Messages can include web search results

## Validation Rules
1. `id` must be unique
2. `role` must be either "user" or "assistant"
3. `type` must be either "text" or "web_search"
4. `timestamp` must be a valid ISO string
5. If `type` is "web_search", `metadata.searchResults` must be present

## Usage Examples
```typescript
// Example 1: Regular text message
const message: Message = {
  id: "123456789",
  role: "user",
  content: "Hello, how are you?",
  type: "text",
  timestamp: "2024-04-13T21:30:00.000Z"
};

// Example 2: Web search message
const webSearchMessage: Message = {
  id: "987654321",
  role: "assistant",
  content: "Here are the search results for your query:",
  type: "web_search",
  timestamp: "2024-04-13T21:31:00.000Z",
  metadata: {
    isWebSearch: true,
    searchResults: [
      {
        title: "Latest AI Developments",
        url: "https://example.com/ai-news",
        snippet: "Recent breakthroughs in AI technology..."
      }
    ]
  }
};
```

## Notes
- Messages are immutable once created
- Web search messages include both the response and search results
- Timestamps are stored in ISO format for consistency
- The model supports extensibility through the metadata field 