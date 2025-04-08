/**
 * Handles API errors and returns a formatted error message
 * @param {unknown} error - The error object from the API call
 * @returns {string} A formatted error message
 */
export const handleApiError = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'An unexpected error occurred';
}; 