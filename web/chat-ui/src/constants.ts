/**
 * Environment-derived constants.
 */

/**
 * Base URL for the chatbot API (no trailing slash).
 * Defaults to empty string = same-origin (use Vite proxy in dev).
 * Set VITE_CHATBOT_API_URL to override (e.g. http://localhost:8000).
 */
export const API_BASE = import.meta.env.VITE_CHATBOT_API_URL ?? "";
