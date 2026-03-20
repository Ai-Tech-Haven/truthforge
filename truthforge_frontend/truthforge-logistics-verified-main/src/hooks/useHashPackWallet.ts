// useHashPackWallet — HashPack wallet hook
// Zero SDK imports. Uses browser extension API via @/lib/hashpack.
// Connect ONLY on explicit user click. No auto-connect. No redirects.

import { useState, useEffect, useCallback } from "react";
import { connectHashPack, disconnectHashPack, HashPackNotInstalledError } from "@/lib/hashpack";

const STORAGE_KEY = "tf_wallet_account";

export interface WalletState {
  accountId: string | null;
  balance: string | null;
  network: "testnet";
  isConnected: boolean;
  isConnecting: boolean;
  /** null = no error; "not_installed" = extension absent; string = other error */
  error: string | null;
  notInstalled: boolean;
}

export function useHashPackWallet() {
  const [state, setState] = useState<WalletState>(() => {
    if (typeof window === "undefined") {
      return { accountId: null, balance: null, network: "testnet", isConnected: false, isConnecting: false, error: null, notInstalled: false };
    }
    const saved = localStorage.getItem(STORAGE_KEY);
    return {
      accountId: saved ?? null,
      balance: null,
      network: "testnet",
      isConnected: !!saved,
      isConnecting: false,
      error: null,
      notInstalled: false,
    };
  });

  // Fetch balance from Hedera Mirror Node REST API — no SDK needed
  const fetchBalance = useCallback(async (accountId: string): Promise<string | null> => {
    try {
      const res = await fetch(
        `https://testnet.mirrornode.hedera.com/api/v1/accounts/${accountId}`,
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

  // Restore balance on mount for persisted account — no popup, no detection
  useEffect(() => {
    if (state.accountId && !state.balance) {
      fetchBalance(state.accountId).then(balance => {
        if (balance) setState(s => ({ ...s, balance }));
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // connectWallet — MUST be called from explicit user click only
  const connectWallet = useCallback(async (): Promise<string | null> => {
    if (typeof window === "undefined") return null;
    if (state.isConnecting) return null;

    setState(s => ({ ...s, isConnecting: true, error: null, notInstalled: false }));

    try {
      const session = await connectHashPack();
      const { accountId } = session;

      localStorage.setItem(STORAGE_KEY, accountId);
      const balance = await fetchBalance(accountId);

      setState({
        accountId,
        balance,
        network: "testnet",
        isConnected: true,
        isConnecting: false,
        error: null,
        notInstalled: false,
      });

      return accountId;
    } catch (err: unknown) {
      if (err instanceof HashPackNotInstalledError) {
        // Extension not found — show inline message + download link, no redirect
        setState(s => ({ ...s, isConnecting: false, error: null, notInstalled: true }));
        return null;
      }

      const msg = err instanceof Error ? err.message : String(err);
      const dismissed =
        msg.toLowerCase().includes("rejected") ||
        msg.toLowerCase().includes("cancelled") ||
        msg.toLowerCase().includes("closed");

      setState(s => ({
        ...s,
        isConnecting: false,
        error: dismissed ? null : msg,
        notInstalled: false,
      }));
      return null;
    }
  }, [state.isConnecting, fetchBalance]);

  // disconnectWallet — clears storage and resets state
  const disconnectWallet = useCallback(() => {
    disconnectHashPack();
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
    setState({ accountId: null, balance: null, network: "testnet", isConnected: false, isConnecting: false, error: null, notInstalled: false });
  }, []);

  // Refresh balance on demand
  const refreshBalance = useCallback(async () => {
    if (!state.accountId) return;
    const balance = await fetchBalance(state.accountId);
    if (balance) setState(s => ({ ...s, balance }));
  }, [state.accountId, fetchBalance]);

  return { ...state, connectWallet, disconnectWallet, refreshBalance };
}
