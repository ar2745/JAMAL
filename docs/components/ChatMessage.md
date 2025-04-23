# ChatMessage

## Overview
The ChatMessage component is responsible for rendering individual chat messages with support for different message types including text, files, links, web search results, and LLM-generated responses. It includes rich formatting, animations, interactive elements, and streaming support for LLM responses.

## Props
| Prop Name | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| message | Message | Yes | - | The message object to display |
| isLast | boolean | No | false | Indicates if this is the last message in the chat |
| isStreaming | boolean | No | false | Indicates if the message is currently streaming |
| streamedContent | string | No | "" | Current content for streaming messages |

## State Management
The component manages the following state:
- `isVisible`: Boolean state for fade-in animation
- `isTyping`: Boolean state for typing animation during streaming
- Uses TypeScript type guards for metadata validation

## Subcomponents
1. `SearchResults`
   - Renders search results in a card format
   - Displays title, content, and source

2. `WebSearchResults`
   - Renders web search results as clickable links
   - Includes title, snippet, and URL
   - Opens links in new tab

3. `LLMResponse`
   - Renders LLM-generated responses
   - Supports streaming with typing animation
   - Displays model metadata and performance metrics
   - Shows confidence scores and processing time

## Message Types
The component supports rendering different types of messages:

1. **Text Messages**
   - Plain text with markdown support for assistant messages
   - Basic text for user messages

2. **File Messages**
   - Displays file preview with icon based on file type
   - Shows file name, size, and extension
   - Includes download button
   - Color-coded icons based on file type

3. **Link Messages**
   - Rich link preview with optional image
   - Displays title, description, and domain
   - Opens in new tab when clicked

4. **Web Search Messages**
   - Markdown-formatted content
   - List of search results with links
   - Each result shows title, snippet, and URL

5. **LLM Response Messages**
   - Streaming support with typing animation
   - Model metadata display (type, temperature, tokens)
   - Performance metrics (processing time, confidence)
   - Markdown formatting for responses
   - Error state handling

## Styling
The component uses Tailwind CSS for styling and includes:
- Responsive message bubbles
- File type-specific colors
- Hover effects on interactive elements
- Proper spacing and alignment
- Markdown formatting for assistant messages
- Fade-in animations for new messages
- Typing animation for streaming responses
- Performance metric badges
- Error state styling

## Dependencies
- `@/lib/utils`: For class name merging
- `@/types`: For type definitions
- `lucide-react`: For icons
- `react-markdown`: For markdown rendering
- `react`: For component lifecycle and hooks
- `@/services/llm`: For LLM integration
- `@/services/analytics`: For performance tracking

## Notes
- Messages are animated with a fade-in effect
- File messages include type-specific icons and colors
- Link messages include fallback handling for failed images
- Web search results are rendered as clickable cards
- Assistant messages support markdown formatting
- All interactive elements have hover states
- Messages are properly aligned based on sender (user/assistant)
- LLM responses include model metadata and performance metrics
- Streaming responses show typing animation
- Error states are handled gracefully with user feedback
- Performance metrics are displayed for LLM responses 