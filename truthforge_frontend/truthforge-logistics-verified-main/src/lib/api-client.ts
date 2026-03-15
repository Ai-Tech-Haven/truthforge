/**
 * TruthForge API Client
 * Central configuration for all backend API calls.
 * Uses VITE_API_URL in production (Railway), falls back to localhost for dev.
 */

export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';
export const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:5000';
export const IS_MOCK = import.meta.env.VITE_MOCK_MODE === 'false' ? false : true;

/**
 * Typed fetch wrapper with base URL and default JSON headers.
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API error ${res.status}: ${error}`);
  }

  return res.json() as Promise<T>;
}
