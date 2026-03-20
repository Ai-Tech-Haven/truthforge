// hashpack.ts — Browser-only HashPack wallet connector
// Zero SDK imports. Uses HashPack browser extension API (window.hashpack)
// or falls back to WalletConnect pairing URL display.
// Frontend responsibility: identity only (accountId + balance display).
// All Hedera transactions are delegated to the Railway backend.

export interface HashPackSession {
  accountId: string;
  network: "testnet" | "mainnet";
}

// HashPack extension injects window.hashpack in the browser
declare global {
  interface Window {
    hashpack?: {
      sendRequest: (msg: object) => Promise<{ success: boolean; accountIds?: string[]; error?: string }>;
    };
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
 * Returns the connected accountId or throws.
 */
export async function connectHashPack(): Promise<HashPackSession> {
  if (typeof window === "undefined") {
    throw new Error("HashPack is only available in the browser.");
  }

  if (!window.hashpack) {
    // Extension not installed — open install page
    window.open("https://www.hashpack.app/download", "_blank");
    throw new Error("HashPack extension not found. Please install it and try again.");
  }

  const response = await window.hashpack.sendRequest({
    type: "connect",
    network: "testnet",
    dappMetadata: APP_META,
  });

  if (!response.success || !response.accountIds?.length) {
    throw new Error(response.error ?? "Connection rejected in HashPack.");
  }

  return {
    accountId: response.accountIds[0],
    network: "testnet",
  };
}

/**
 * Disconnect from HashPack extension.
 * Fire-and-forget — clears local state regardless of extension response.
 */
export async function disconnectHashPack(): Promise<void> {
  if (typeof window === "undefined" || !window.hashpack) return;
  try {
    await window.hashpack.sendRequest({ type: "disconnect" });
  } catch { /* ignore — local state is cleared by caller */ }
}
