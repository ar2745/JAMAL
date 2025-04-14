# FileList

## Overview
The FileList component displays a scrollable list of documents with options to select, preview, and delete them. It includes a preview dialog for viewing file content and supports bulk selection of documents.

## Props
| Prop Name | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| documents | Array<File> | Yes | - | List of documents to display |
| onDelete | (id: string) => void | Yes | - | Callback for deleting a document |
| onSelect | (id: string, selected: boolean) => void | Yes | - | Callback for selecting/deselecting a document |

### File Type
```typescript
interface File {
  id: string;
  name: string;
  content: string;
  type: string;
  selected?: boolean;
}
```

## State Management
The component manages the following state:
- `previewFile`: Currently selected file for preview
- Uses controlled checkboxes for selection state

## Features
1. **File Display**
   - Scrollable list of files
   - File name display
   - File icon indicator
   - Hover effects

2. **File Actions**
   - Selection via checkbox
   - Preview in dialog
   - Delete option
   - Content viewing

3. **Preview Dialog**
   - File name display
   - Content preview
   - Scrollable content area
   - Preserved whitespace

## Styling
The component uses Tailwind CSS for styling and includes:
- Scrollable container
- Hover effects for items
- Hidden action buttons on hover
- Preview dialog with max height
- Proper spacing and alignment
- Truncated text for long filenames

## Dependencies
- `@/components/ui/button`: For action buttons
- `@/components/ui/checkbox`: For selection
- `@/components/ui/dialog`: For preview modal
- `@/components/ui/scroll-area`: For scrolling
- `lucide-react`: For icons
- `react`: For component lifecycle and hooks

## Notes
- Files are displayed in a scrollable list
- Action buttons appear on hover
- Preview dialog shows file content
- Files can be selected for bulk operations
- Long filenames are truncated with ellipsis
- The component is fully responsive
- Content is displayed with preserved whitespace 