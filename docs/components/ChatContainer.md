# ChatContainer

## Overview
The ChatContainer component is the main container for the chat interface. It manages the display of messages, handles message sending, and integrates with our service-based architecture. It supports document and link context, as well as LLM-generated responses with streaming capabilities.

## Props
| Prop Name | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| selectedDocuments | Array<Document> | Yes | - | Array of selected documents to provide context |
| selectedLinks | Array<Link> | Yes | - | Array of selected links to provide context |
| chatTitle | string | Yes | - | Current chat title |
| setChatTitle | (title: string) => void | Yes | - | Function to update chat title |
| messages | Message[] | Yes | - | Array of chat messages |
| onSendMessage | (message: Message) => void | Yes | - | Callback for sending messages |
| conversationId | string | Yes | - | Current conversation ID |
| llmConfig | LLMConfig | No | - | LLM configuration options |

### Document Type
```typescript
interface Document {
  id: string;
  name: string;
  content: string;
  type: string;
  selected?: boolean;
}
```

### Link Type
```typescript
interface Link {
  id: string;
  url: string;
  title: string;
  description?: string;
  content?: string;
  selected?: boolean;
}
```

### LLMConfig Type
```typescript
interface LLMConfig {
  modelType: "SIMPLE" | "REASONED";
  temperature?: number;
  maxTokens?: number;
  stream?: boolean;
}
```

## State Management
The component manages the following state:
- `isLoading`: Boolean state to track message sending status
- `isStreaming`: Boolean state to track streaming response status
- `streamedContent`: String state for accumulating streamed content
- Uses a ref (`messagesEndRef`) to handle auto-scrolling to the latest message

## Service Integration
The component integrates with the following services:
- LLM Integration Service: For generating responses
- Memory Service: For managing conversation history
- Analytics Service: For tracking user interactions

## Usage Examples
```tsx
import ChatContainer from "@/components/ChatContainer";

function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<Document[]>([]);
  const [selectedLinks, setSelectedLinks] = useState<Link[]>([]);
  const [chatTitle, setChatTitle] = useState("New Chat");
  const [conversationId] = useState(generateConversationId());

  const handleSendMessage = async (message: Message) => {
    setMessages(prev => [...prev, message]);
    
    // Handle streaming response
    const stream = await llmService.generateResponse(
      message.content,
      {
        modelType: "REASONED",
        stream: true,
        conversationId
      }
    );

    for await (const chunk of stream) {
      setStreamedContent(prev => prev + chunk);
    }
  };

  return (
    <ChatContainer
      selectedDocuments={selectedDocuments}
      selectedLinks={selectedLinks}
      chatTitle={chatTitle}
      setChatTitle={setChatTitle}
      messages={messages}
      onSendMessage={handleSendMessage}
      conversationId={conversationId}
      llmConfig={{
        modelType: "REASONED",
        temperature: 0.7,
        maxTokens: 1000,
        stream: true
      }}
    />
  );
}
```

## Styling
The component uses Tailwind CSS for styling and includes:
- Flex layout for vertical arrangement
- ScrollArea component for message overflow
- Responsive padding and spacing
- Loading and streaming state styling
- Animated typing indicators for streaming responses

## Dependencies
- `@/components/ui/scroll-area`: For scrollable message container
- `@/types`: For Message type definition
- `react`: For component lifecycle and hooks
- `ChatMessage`: For rendering individual messages
- `UserInput`: For message input handling
- `@/services/llm`: For LLM integration
- `@/services/memory`: For conversation history
- `@/services/analytics`: For user analytics

## Notes
- The component automatically scrolls to the bottom when new messages are added
- It handles both regular text messages and web search messages
- Supports streaming LLM responses with real-time updates
- Maintains conversation history through the conversation ID
- Error handling is implemented for failed API calls
- Context from selected documents and links is automatically included in API requests
- Performance metrics are tracked for LLM responses 