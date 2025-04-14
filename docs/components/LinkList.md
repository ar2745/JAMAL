# LinkList

## Overview
The LinkList component displays a scrollable list of links with options to select, preview, and delete them. It includes a preview dialog for viewing link details and supports bulk selection of links.

## Props
| Prop Name | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| links | Array<Link> | Yes | - | List of links to display |
| onDelete | (id: string) => void | Yes | - | Callback for deleting a link |
| onSelect | (id: string, selected: boolean) => void | Yes | - | Callback for selecting/deselecting a link |

### Link Type
```typescript
interface Link {
  id: string;
  url: string;
  title?: string;
  description?: string;
  content?: string;
  selected?: boolean;
}
```

## State Management
The component manages the following state:
- `previewLink`: Currently selected link for preview
- Uses controlled checkboxes for selection state

## Features
1. **Link Display**
   - Scrollable list of links
   - Title or URL display
   - Link icon indicator
   - Hover effects

2. **Link Actions**
   - Selection via checkbox
   - Preview in dialog
   - Delete option
   - Open in new tab

3. **Preview Dialog**
   - Title display
   - Description preview
   - Content preview
   - External link option

## Styling
The component uses Tailwind CSS for styling and includes:
- Scrollable container
- Hover effects for items
- Hidden action buttons on hover
- Preview dialog with max height
- Proper spacing and alignment
- Truncated text for long titles

## Dependencies
- `@/components/ui/button`: For action buttons
- `@/components/ui/checkbox`: For selection
- `@/components/ui/dialog`: For preview modal
- `@/components/ui/scroll-area`: For scrolling
- `lucide-react`: For icons
- `react`: For component lifecycle and hooks

## Notes
- Links are displayed in a scrollable list
- Action buttons appear on hover
- Preview dialog shows full link details
- Links can be selected for bulk operations
- Long titles are truncated with ellipsis
- The component is fully responsive 