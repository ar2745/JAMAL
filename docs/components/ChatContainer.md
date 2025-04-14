# ChatContainer

## Overview
The ChatContainer component is the main container for the chat interface. It manages the display of messages, handles message sending, and integrates with the backend API. It also supports document and link context for enhanced chat interactions.

## Props
| Prop Name | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| selectedDocuments | Array<Document> | Yes | - | Array of selected documents to provide context |
| selectedLinks | Array<Link> | Yes | - | Array of selected links to provide context |
| chatTitle | string | Yes | - | Current chat title |
| setChatTitle | (title: string) => void | Yes | - | Function to update chat title |
| messages | Message[] | Yes | - | Array of chat messages |
| onSendMessage | (message: Message) => void | Yes | - | Callback for sending messages |

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

## State Management
The component manages the following state:
- `isLoading`: Boolean state to track message sending status
- Uses a ref (`messagesEndRef`) to handle auto-scrolling to the latest message

## Usage Examples
```tsx
import ChatContainer from "@/components/ChatContainer";

function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<Document[]>([]);
  const [selectedLinks, setSelectedLinks] = useState<Link[]>([]);
  const [chatTitle, setChatTitle] = useState("New Chat");

  const handleSendMessage = (message: Message) => {
    setMessages(prev => [...prev, message]);
  };

  return (
    <ChatContainer
      selectedDocuments={selectedDocuments}
      selectedLinks={selectedLinks}
      chatTitle={chatTitle}
      setChatTitle={setChatTitle}
      messages={messages}
      onSendMessage={handleSendMessage}
    />
  );
}
```

## Styling
The component uses Tailwind CSS for styling and includes:
- Flex layout for vertical arrangement
- ScrollArea component for message overflow
- Responsive padding and spacing
- Loading state styling

## Dependencies
- `@/components/ui/scroll-area`: For scrollable message container
- `@/types`: For Message type definition
- `react`: For component lifecycle and hooks
- `ChatMessage`: For rendering individual messages
- `UserInput`: For message input handling

## Notes
- The component automatically scrolls to the bottom when new messages are added
- It handles both regular text messages and web search messages
- Error handling is implemented for failed API calls
- Context from selected documents and links is automatically included in API requests 