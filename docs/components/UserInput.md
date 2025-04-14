# UserInput

## Overview
The UserInput component provides the input interface for the chat application, supporting text messages, file uploads, link sharing, and web search functionality. It includes a text input field with auto-resize capability and action buttons for different input types.

## Props
| Prop Name | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| onSendMessage | (message: Message) => void | Yes | - | Callback for sending messages |
| onFileUpload | (file: File) => void | No | - | Optional callback for file uploads |
| isLoading | boolean | No | false | Loading state indicator |

## State Management
The component manages the following state:
- `message`: Current input text
- `isLinkDialogOpen`: Controls link input dialog visibility
- `isWebSearchMode`: Toggles web search functionality
- Uses refs for textarea and file input elements

## Features
1. **Text Input**
   - Auto-resizing textarea
   - Enter key support for sending
   - Shift+Enter for new lines
   - Placeholder text changes based on mode

2. **File Upload**
   - Hidden file input
   - File type validation
   - Upload progress handling
   - Error handling with fallback

3. **Link Sharing**
   - Link input dialog
   - URL validation
   - Metadata extraction
   - Error handling

4. **Web Search**
   - Toggle button with visual indicator
   - Mode-specific placeholder text
   - Search button text changes

## API Integration
The component integrates with several API endpoints:
- `/document_upload` for file uploads
- `/link_upload` for link processing
- Uses environment variables for API URL configuration

## Styling
The component uses Tailwind CSS for styling and includes:
- Responsive input field
- Icon buttons with hover states
- Loading state indicators
- Mode-specific button styling
- Proper spacing and alignment

## Dependencies
- `@/components/ui/button`: For styled buttons
- `@/components/ui/input`: For styled input field
- `@/types`: For Message type definition
- `lucide-react`: For icons
- `react`: For component lifecycle and hooks
- `LinkInputDialog`: For link input functionality

## Notes
- The component handles all types of user input in one interface
- File uploads include fallback handling for failed uploads
- Link processing includes metadata extraction
- Web search mode is visually indicated with a green dot
- All interactive elements are disabled during loading
- The component uses environment variables for API configuration 