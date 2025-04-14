# Dashboard

## Overview
The Dashboard component provides a comprehensive overview of the application's analytics and statistics. It displays real-time metrics for chats, documents, links, and user activity, along with visual representations of usage patterns.

## Props
| Prop Name | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| documents | Array<Document> | Yes | - | List of documents for recent activity |
| links | Array<Link> | Yes | - | List of links for recent activity |

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
- `analyticsData`: Analytics data from the backend
- `loading`: Loading state indicator
- Auto-refreshes data every 30 seconds

## Features
1. **Overview Cards**
   - Total Chats with active chat count
   - Documents with total size
   - Links with unique domain count
   - Active Users with daily active count

2. **Usage Statistics**
   - Hourly activity chart
   - System status indicators
   - Response time monitoring
   - Storage usage tracking

3. **Recent Activity**
   - Latest documents
   - Recent links
   - Activity timestamps

## API Integration
The component integrates with several analytics endpoints:
- `/analytics/chat` for chat statistics
- `/analytics/documents` for document statistics
- `/analytics/links` for link statistics
- `/analytics/usage` for usage statistics

## Styling
The component uses Tailwind CSS for styling and includes:
- Responsive grid layout
- Card-based design
- Status indicators
- Chart visualizations
- Icon integration
- Proper spacing and alignment

## Dependencies
- `lucide-react`: For icons
- `recharts`: For chart components
- `@/components/ui/card`: For card components
- `@/components/ui/chart`: For chart components
- `react`: For component lifecycle and hooks

## Notes
- Data is automatically refreshed every 30 seconds
- Charts are responsive and interactive
- Status indicators show real-time system health
- Recent activity section shows latest documents and links
- All metrics are displayed with appropriate units and formatting
- Error handling for failed API calls 