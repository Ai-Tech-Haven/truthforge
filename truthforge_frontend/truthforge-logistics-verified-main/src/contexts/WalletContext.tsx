// WalletContext — HashConnect v3 wallet provider
// Constructor: new HashConnect(debug, network, appMetadata)
// pair() triggers the HashPack Chrome extension popup instantly.
// No auto-connect. Connect ONLY on explicit user click.

import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from "react";
// @ts-ignore — hashconnect installed on Vercel; may not be in local node_modules
import { HashConnect } from "hashconnect";

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
  const hcRef = useRef<InstanceType<typeof HashConnect> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Restore balance on mount for persisted account
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      fetchBalance(saved).then(bal => { if (bal) setBalance(bal); });
    }
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
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

    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    // 45s safety timeout — clears spinner if user never responds to HashPack
    timeoutRef.current = setTimeout(() => {
      setIsConnecting(false);
    }, 45_000);

    try {
      const appMetadata = {
        name: "TruthForge",
        description: "Verifiable Intelligence Layer for Global Trade",
        icon: `${window.location.origin}/favicon.png`,
      };

      // HashConnect v3: new HashConnect(debug, network, appMetadata)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const hc = new HashConnect(false, "testnet", appMetadata);

      // Register pairingEvent BEFORE calling pair()
      hc.pairingEvent.once((pairingData: { accountIds: string[] }) => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        const acct = pairingData.accountIds?.[0];
        if (!acct) {
          setError("No account returned from HashPack.");
          setIsConnecting(false);
          return;
        }
        localStorage.setItem(STORAGE_KEY, acct);
        setAccountId(acct);
        hcRef.current = hc;
        setIsConnecting(false);
        setError(null);
        fetchBalance(acct).then(bal => { if (bal) setBalance(bal); });
      });

      hc.disconnectionEvent?.on(() => {
        localStorage.removeItem(STORAGE_KEY);
        setAccountId(null);
        setBalance(null);
        hcRef.current = null;
      });

      // pair() — instantly triggers the HashPack Chrome extension popup
      await hc.pair();

    } catch (e: unknown) {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      const msg = e instanceof Error ? e.message : String(e);
      const isDismissed =
        msg.toLowerCase().includes("rejected") ||
        msg.toLowerCase().includes("cancelled") ||
        msg.toLowerCase().includes("closed") ||
        msg.toLowerCase().includes("user denied");
      if (!isDismissed) {
        setError(msg || "Failed to connect. Is HashPack installed?");
      }
      setIsConnecting(false);
    }
  }, [isConnecting, fetchBalance]);

  const disconnectWallet = useCallback(() => {
    if (hcRef.current) {
      try { hcRef.current.disconnect(); } catch { /* ignore */ }
      hcRef.current = null;
    }
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    localStorage.removeItem(STORAGE_KEY);
    setAccountId(null);
    setBalance(null);
    setError(null);
    setIsConnecting(false);
  }, []);

  const refreshBalance = useCallback(async () => {
    if (!accountId) return;
    const bal = await fetchBalance(accountId);
    if (bal) setBalance(bal);
  }, [accountId, fetchBalance]);

  const isConnected = !!accountId;
  const wallet = isConnected && accountId ? { accountId, network: "testnet" } : null;

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
