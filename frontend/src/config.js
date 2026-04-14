/**
 * Central API config — reads from environment variables at build time.
 * Set VITE_API_URL in your .env or deployment platform (Vercel, Netlify).
 * Falls back to localhost for local development.
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const API_BASE = `${API_BASE_URL}/api/v1`;

// WebSocket URL: converts http(s):// to ws(s)://
export const WS_URL = `${API_BASE_URL.replace(/^http/, "ws")}/ws/updates`;
