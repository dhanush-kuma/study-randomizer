// Use VITE_API_URL if explicitly set (cross-origin dev), otherwise use relative URLs
// (same-origin deploy: FastAPI serves the React build on the same domain).
// NOTE: Use ?? not || so that an empty string VITE_API_URL stays as "" (relative).
export const API_URL = import.meta.env.VITE_API_URL ?? ''
