/**
 * ID generation utilities
 */

/**
 * Generates a simple UUID-like string
 * In production, you'd use a proper UUID library
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Generates a shorter ID for display purposes
 */
export function generateShortId(): string {
  return Math.random().toString(36).substr(2, 8);
}

