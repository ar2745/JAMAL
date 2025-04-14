# ChatMessage

## Overview
The ChatMessage component is responsible for rendering individual chat messages with support for different message types including text, files, links, and web search results. It includes rich formatting, animations, and interactive elements.

## Props
| Prop Name | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| message | Message | Yes | - | The message object to display |
| isLast | boolean | No | false | Indicates if this is the last message in the chat |

## State Management
The component manages the following state:
- `isVisible`: Boolean state for fade-in animation
- Uses TypeScript type guards for metadata validation

## Subcomponents
1. `SearchResults`
   - Renders search results in a card format
   - Displays title, content, and source

2. `WebSearchResults`
   - Renders web search results as clickable links
   - Includes title, snippet, and URL
   - Opens links in new tab

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

## Styling
The component uses Tailwind CSS for styling and includes:
- Responsive message bubbles
- File type-specific colors
- Hover effects on interactive elements
- Proper spacing and alignment
- Markdown formatting for assistant messages
- Fade-in animations for new messages

## Dependencies
- `@/lib/utils`: For class name merging
- `@/types`: For type definitions
- `lucide-react`: For icons
- `react-markdown`: For markdown rendering
- `react`: For component lifecycle and hooks

## Notes
- Messages are animated with a fade-in effect
- File messages include type-specific icons and colors
- Link messages include fallback handling for failed images
- Web search results are rendered as clickable cards
- Assistant messages support markdown formatting
- All interactive elements have hover states
- Messages are properly aligned based on sender (user/assistant) 