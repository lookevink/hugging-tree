/**
 * Validation utilities
 */

/**
 * Validates an email address using a simple regex
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validates that a string is not empty
 */
export function validateNotEmpty(value: string): boolean {
  return value.trim().length > 0;
}

/**
 * Validates that a number is positive
 */
export function validatePositive(value: number): boolean {
  return value > 0;
}

/**
 * Validates that a number is non-negative
 */
export function validateNonNegative(value: number): boolean {
  return value >= 0;
}

