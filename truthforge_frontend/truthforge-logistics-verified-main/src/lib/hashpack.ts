// hashpack.ts — Browser-only HashPack wallet connector
// Zero SDK imports. Uses HashPack browser extension API (window.hashpack).
// Frontend responsibility: identity only (accountId + balance display).
// All Hedera transactions are delegated to the Railway backend.
//
// RULES:
// - Detection happens inside the click handler (never in useEffect)
// - If extension missing: show inline message, NO window.open, NO redirect
// - Connect ONLY on explicit user click

export interface HashPackSession {
  accountId: string;
  network: "testnet" | "mainnet";
}

// Sentinel error type so the hook can distinguish "not installed" from other errors
export class HashPackNotInstalledError extends Error {
  constructor() {
    super("HashPack browser extension not detected.");
    this.name = "HashPackNotInstalledError";
  }
}

// HashPack extension injects window.hashpack in the browser
declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    hashpack?: any;
  }
}

const APP_META = {
  name: "TruthForge",
  description: "Verifiable Trade & Logistics Proof",
  icon: typeof window !== "undefined" ? `${window.location.origin}/favicon.ico` : "",
  url: typeof window !== "undefined" ? window.location.origin : "",
};

/**
 * Connect to HashPack browser extension.
 * Must be called from an explicit user click handler.
 * Throws HashPackNotInstalledError if extension is absent — caller shows inline message.
 * Never opens download pages or redirects.
 */
export async function connectHashPack(): Promise<HashPackSession> {
  if (typeof window === "undefined") {
    throw new Error("Wallet is only available in the browser.");
  }

  // Detection inside click handler — never in useEffect
  const isAvailable = typeof window.hashpack !== "undefined";

  if (!isAvailable) {
    // Throw typed error — hook surfaces this as inline UI, no redirect
    throw new HashPackNotInstalledError();
  }

  const response = await window.hashpack.sendRequest({
    type: "connect",
    network: "testnet",
    dappMetadata: APP_META,
  });

  if (!response?.success || !response?.accountIds?.length) {
    throw new Error(response?.error ?? "Connection rejected in HashPack.");
  }

  return {
    accountId: response.accountIds[0],
    network: "testnet",
  };
}

/**
 * Disconnect from HashPack extension.
 * Fire-and-forget — local state is cleared by the caller regardless.
 */
export async function disconnectHashPack(): Promise<void> {
  if (typeof window === "undefined" || !window.hashpack) return;
  try {
    await window.hashpack.sendRequest({ type: "disconnect" });
  } catch { /* ignore */ }
}
