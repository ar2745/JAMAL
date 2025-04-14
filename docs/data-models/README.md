# Data Models Documentation

This directory contains documentation for all data models used in the application.

## Documentation Structure

Each data model documentation follows this structure:

```markdown
# ModelName

## Overview
Brief description of the model's purpose and usage.

## Schema
```typescript
interface ModelName {
  // Type definition
}
```

## Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|

## Relationships
Description of relationships with other models.

## Validation Rules
List of validation rules and constraints.

## Usage Examples
```typescript
// Example usage code
```

## Notes
Additional information, warnings, or best practices.
```

## Models to Document
1. Chat Models
   - Chat
   - Message
   - ChatHistory

2. Document Models
   - Document
   - DocumentMetadata
   - DocumentContent

3. Link Models
   - Link
   - LinkMetadata
   - LinkPreview

4. Memory Models
   - Memory
   - MemoryEntry
   - MemoryContext

5. Analytics Models
   - Analytics
   - Metric
   - AnalyticsData 