// WalletContext — HashConnect v3 wallet provider
// Uses correct v3 API: events registered BEFORE init(), openPairingModal() triggers extension popup.
// 30s timeout resets isConnecting if user closes popup without pairing.
// Connect ONLY on explicit user click. No auto-connect.

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore — hashconnect is installed on Vercel; not in local node_modules
import { HashConnect, SessionData } from "hashconnect";

// WalletConnect project ID — required by HashConnect v3 (WalletConnect standard)
// Get one free at https://cloud.walletconnect.com
const WC_PROJECT_ID = "2af6f5e4a8b3c1d7e9f0a2b4c6d8e0f2";

type WalletContextType = {
  isConnected: boolean;
  accountId: string | null;
  balance: string | null;
  network: "testnet";
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  refreshBalance: () => Promise<void>;
  isConnecting: boolean;
  error: string | null;
  wallet: { accountId: string; network: string } | null;
};

const WalletContext = createContext<WalletContextType>({
  isConnected: false,
  accountId: null,
  balance: null,
  network: "testnet",
  connectWallet: async () => {},
  disconnectWallet: () => {},
  refreshBalance: async () => {},
  isConnecting: false,
  error: null,
  wallet: null,
});

export const useWallet = () => useContext(WalletContext);

const STORAGE_KEY = "tf_wallet_account";

export const WalletProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [accountId, setAccountId] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(STORAGE_KEY) ?? null;
  });
  const [balance, setBalance] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hcInstance, setHcInstance] = useState<HashConnect | null>(null);

  // Restore balance on mount for persisted account
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && !balance) {
      fetchBalance(saved).then(bal => { if (bal) setBalance(bal); });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchBalance = useCallback(async (id: string): Promise<string | null> => {
    try {
      const res = await fetch(
        `https://testnet.mirrornode.hedera.com/api/v1/accounts/${id}`,
        { signal: AbortSignal.timeout(8000) }
      );
      if (!res.ok) return null;
      const data = await res.json() as { balance?: { balance?: number } };
      const tinybars = data?.balance?.balance ?? 0;
      return (tinybars / 1e8).toFixed(4) + " HBAR";
    } catch {
      return null;
    }
  }, []);

  const connectWallet = useCallback(async () => {
    if (typeof window === "undefined") return;
    if (isConnecting) return;

    setIsConnecting(true);
    setError(null);

    // Safety timeout — reset after 30s if user closes popup without pairing
    const timeoutId = setTimeout(() => {
      setIsConnecting(false);
      setError("Connection timed out. Please try again.");
    }, 30_000);

    try {
      const appMetadata = {
        name: "TruthForge",
        description: "Verifiable Trade Intelligence",
        icons: [`${window.location.origin}/favicon.png`],
        url: window.location.origin,
      };

      // HashConnect v3: (LedgerId, projectId, appMetadata, debug)
      // "testnet" is the string value of LedgerId.TESTNET — avoids @hashgraph/sdk import
      const hc = new HashConnect("testnet" as unknown as Parameters<typeof HashConnect>[0], WC_PROJECT_ID, appMetadata, true);

      // ⚠️ Register events BEFORE calling init() — docs say some events fire immediately on init
      hc.pairingEvent.on(async (pairingData: SessionData) => {
        clearTimeout(timeoutId);
        const acct = pairingData.accountIds?.[0];
        if (!acct) {
          setError("No account returned from HashPack.");
          setIsConnecting(false);
          return;
        }
        localStorage.setItem(STORAGE_KEY, acct);
        setAccountId(acct);
        setHcInstance(hc);
        const bal = await fetchBalance(acct);
        setBalance(bal);
        setIsConnecting(false);
      });

      hc.disconnectionEvent.on(() => {
        localStorage.removeItem(STORAGE_KEY);
        setAccountId(null);
        setBalance(null);
        setHcInstance(null);
      });

      // init() — if HashPack extension is detected, it auto-pops the extension
      await hc.init();

      // openPairingModal() shows QR + pairing code as fallback (also triggers extension)
      hc.openPairingModal();

    } catch (e: unknown) {
      clearTimeout(timeoutId);
      const msg = e instanceof Error ? e.message : String(e);
      const dismissed =
        msg.toLowerCase().includes("rejected") ||
        msg.toLowerCase().includes("cancelled") ||
        msg.toLowerCase().includes("closed") ||
        msg.toLowerCase().includes("user denied");
      setError(dismissed ? null : msg || "Failed to connect. Is HashPack installed?");
      setIsConnecting(false);
    }
  }, [isConnecting, fetchBalance]);

  const disconnectWallet = useCallback(() => {
    if (hcInstance) {
      try { hcInstance.disconnect(); } catch { /* ignore */ }
    }
    localStorage.removeItem(STORAGE_KEY);
    setAccountId(null);
    setBalance(null);
    setHcInstance(null);
    setError(null);
    setIsConnecting(false);
  }, [hcInstance]);

  const refreshBalance = useCallback(async () => {
    if (!accountId) return;
    const bal = await fetchBalance(accountId);
    if (bal) setBalance(bal);
  }, [accountId, fetchBalance]);

  const isConnected = !!accountId;
  const wallet = isConnected && accountId
    ? { accountId, network: "testnet" }
    : null;

  return (
    <WalletContext.Provider value={{
      isConnected,
      accountId,
      balance,
      network: "testnet",
      connectWallet,
      disconnectWallet,
      refreshBalance,
      isConnecting,
      error,
      wallet,
    }}>
      {children}
    </WalletContext.Provider>
  );
};
