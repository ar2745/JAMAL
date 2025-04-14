# LinkInputDialog

## Overview
The LinkInputDialog component provides a modal interface for users to input and validate URLs. It includes URL validation, error handling, and a clean user interface for adding new links to the chat.

## Props
| Prop Name | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| isOpen | boolean | Yes | - | Controls dialog visibility |
| onClose | () => void | Yes | - | Callback for closing the dialog |
| onSubmit | (url: string) => void | Yes | - | Callback for submitting a valid URL |

## State Management
The component manages the following state:
- `url`: Current URL input value
- `error`: Error message for invalid URLs

## Features
1. **URL Validation**
   - Checks for valid URL format
   - Provides clear error messages
   - Trims whitespace from input

2. **User Interface**
   - Clean modal design
   - Input field with placeholder
   - Error message display
   - Cancel and Submit buttons

3. **Error Handling**
   - Empty URL validation
   - Invalid URL format validation
   - Visual error indication
   - Clear error messages

## Styling
The component uses Tailwind CSS for styling and includes:
- Responsive dialog layout
- Error state styling
- Proper spacing and alignment
- Consistent button styling
- Clear visual hierarchy

## Dependencies
- `@/components/ui/button`: For styled buttons
- `@/components/ui/dialog`: For modal functionality
- `@/components/ui/input`: For URL input field
- `@/components/ui/label`: For input label
- `react`: For component lifecycle and hooks

## Notes
- The dialog is responsive and works on all screen sizes
- URL validation uses the native URL constructor
- Error messages are clear and user-friendly
- The component maintains a clean state between uses
- The dialog can be closed by clicking outside or using the cancel button 