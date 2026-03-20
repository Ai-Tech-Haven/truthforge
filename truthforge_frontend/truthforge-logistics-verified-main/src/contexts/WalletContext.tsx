// WalletContext — HashConnect-based wallet provider
// Uses hashconnect package to open HashPack Chrome extension popup.
// Connect ONLY on explicit user click. No auto-connect. No SDK imports.

import React, { createContext, useContext, useState, useCallback } from "react";
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
  // Legacy compat shape used by MerchantPortalPage / LiveModeBanner
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

  // connectWallet — MUST be called from explicit user click only
  const connectWallet = useCallback(async () => {
    if (typeof window === "undefined") return;
    setIsConnecting(true);
    setError(null);

    try {
      const hc = new HashConnect(
        true,       // debug
        "testnet",
        {
          name: "TruthForge",
          description: "Verifiable Trade Intelligence",
          icon: `${window.location.origin}/favicon.png`,
        }
      );

      await hc.init();

      // THIS opens the HashPack Chrome extension popup
      await hc.pair();

      hc.pairingEvent.once(async (pairingData) => {
        const acct = pairingData.accountIds[0];
        localStorage.setItem(STORAGE_KEY, acct);
        setAccountId(acct);
        setHcInstance(hc);
        const bal = await fetchBalance(acct);
        setBalance(bal);
        setIsConnecting(false);
      });

    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      const dismissed =
        msg.toLowerCase().includes("rejected") ||
        msg.toLowerCase().includes("cancelled") ||
        msg.toLowerCase().includes("closed");
      setError(dismissed ? null : msg);
      setIsConnecting(false);
    }
  }, [fetchBalance]);

  const disconnectWallet = useCallback(() => {
    if (hcInstance) {
      try { hcInstance.disconnect(); } catch { /* ignore */ }
    }
    localStorage.removeItem(STORAGE_KEY);
    setAccountId(null);
    setBalance(null);
    setHcInstance(null);
    setError(null);
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
