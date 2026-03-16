/**
 * TruthForge API Client
 * Central configuration for all backend API calls.
 * Uses VITE_API_URL in production (Railway), falls back to localhost for dev.
 *
 * Live mode is controlled at runtime via MockModeContext (localStorage key: tf_mock_mode).
 * When isMockMode=true, apiFetch throws so callers can fall back to mock data.
 */

// In production (Vercel), VITE_API_URL must be set — falls back to Railway URL.
// localhost:5000 is only used when running the dev server locally.
const RAILWAY_URL = "https://web-production-dcd43.up.railway.app";
const isDev = import.meta.env.DEV;

export const API_BASE = import.meta.env.VITE_API_URL || (isDev ? "http://localhost:5000" : RAILWAY_URL);
export const WS_BASE = import.meta.env.VITE_WS_URL || (isDev ? "ws://localhost:5000" : `wss://${RAILWAY_URL.replace("https://", "")}`);

/** Read current mode directly from storage — usable outside React tree */
export const getRuntimeMockMode = (): boolean => {
  const stored = localStorage.getItem("tf_mock_mode");
  return stored === null ? true : stored === "true";
};

/**
 * Typed fetch wrapper. Respects runtime mock mode:
 * - In mock mode: throws MockModeError so callers fall back to local data.
 * - In live mode: hits the real backend.
 */
export class MockModeError extends Error {
  constructor() {
    super("mock_mode_active");
    this.name = "MockModeError";
  }
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
  forceLive = false
): Promise<T> {
  if (!forceLive && getRuntimeMockMode()) {
    throw new MockModeError();
  }

  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API error ${res.status}: ${error}`);
  }

  return res.json() as Promise<T>;
}

/**
 * WebSocket factory — returns null in mock mode.
 */
export function createWS(path: string): WebSocket | null {
  if (getRuntimeMockMode()) return null;
  return new WebSocket(`${WS_BASE}${path}`);
}
