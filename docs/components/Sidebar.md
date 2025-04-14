# Sidebar

## Overview
The Sidebar component provides the main navigation interface for the application, including chat history, file management, link management, and settings access. It features a responsive design that adapts to both desktop and mobile views.

## Props
| Prop Name | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| isMobile | boolean | Yes | - | Indicates if the sidebar is in mobile mode |
| activeSection | string | Yes | - | Currently active section ('dashboard', 'chat', 'files', 'links', 'settings') |
| setActiveSection | (section: string) => void | Yes | - | Callback for changing active section |
| documents | Array<Document> | Yes | - | List of documents |
| links | Array<Link> | Yes | - | List of links |
| onDeleteDocument | (id: string) => void | Yes | - | Callback for deleting a document |
| onDeleteLink | (id: string) => void | Yes | - | Callback for deleting a link |
| onSelectDocument | (id: string, selected: boolean) => void | Yes | - | Callback for selecting a document |
| onSelectLink | (id: string, selected: boolean) => void | Yes | - | Callback for selecting a link |
| chats | Array<Chat> | Yes | - | List of chats |
| currentChatId | string \| null | Yes | - | Currently selected chat ID |
| onChatSelect | (chatId: string) => void | Yes | - | Callback for selecting a chat |
| onCreateNewChat | () => void | Yes | - | Callback for creating a new chat |
| onDeleteChat | (chatId: string) => void | Yes | - | Callback for deleting a chat |

## Subcomponents
1. `SidebarItem`
   - Reusable navigation item component
   - Icon and label display
   - Active state styling
   - Click handler support

## Features
1. **Header Section**
   - Application logo and name
   - Subtitle display
   - Branding elements

2. **Chat Management**
   - New chat button
   - Chat history list
   - Last message preview
   - Chat deletion
   - Active chat indication

3. **Navigation**
   - Dashboard access
   - File management
   - Link management
   - Settings access
   - Active section indication

4. **Responsive Design**
   - Mobile adaptation
   - Collapsible interface
   - Touch-friendly elements

## Styling
The component uses Tailwind CSS for styling and includes:
- Fixed width sidebar
- Responsive layout
- Hover effects
- Active state indicators
- Proper spacing and alignment
- Scrollable chat history
- Border separators

## Dependencies
- `@/lib/utils`: For class name merging
- `@/types`: For type definitions
- `lucide-react`: For icons
- `@/components/ui/button`: For styled buttons
- `@/components/ui/scroll-area`: For scrolling
- `react`: For component lifecycle and hooks

## Notes
- The sidebar is fixed width (72 units)
- Chat history is scrollable
- Last messages are truncated with ellipsis
- Active sections are visually indicated
- Delete buttons appear on hover
- The component supports both desktop and mobile views
- Navigation items have hover and active states 