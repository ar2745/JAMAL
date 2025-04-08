/**
 * Generates a unique ID using a timestamp and random string
 * @returns {string} A unique identifier
 */
export const generateUniqueId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}; 