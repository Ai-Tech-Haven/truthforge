// useHashPackWallet — HashPack wallet hook
// Uses singleton DAppConnector from @/lib/hashpack
// No auto-connect. Connect only on explicit user click.

import { useState, useEffect, useCallback } from "react";
import { getConnector, resetConnector } from "@/lib/hashpack";

const STORAGE_KEY = "tf_wallet_account";

export interface WalletState {
  accountId: string | null;
  balance: string | null;
  network: "testnet";
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
}

export function useHashPackWallet() {
  const [state, setState] = useState<WalletState>(() => {
    // Restore persisted account on mount (display-only, no popup)
    if (typeof window === "undefined") {
      return { accountId: null, balance: null, network: "testnet", isConnected: false, isConnecting: false, error: null };
    }
    const saved = localStorage.getItem(STORAGE_KEY);
    return {
      accountId: saved ?? null,
      balance: null,
      network: "testnet",
      isConnected: !!saved,
      isConnecting: false,
      error: null,
    };
  });

  // Fetch balance from mirror node — no SDK needed
  const fetchBalance = useCallback(async (accountId: string): Promise<string | null> => {
    try {
      const res = await fetch(`https://testnet.mirrornode.hedera.com/api/v1/accounts/${accountId}`);
      if (!res.ok) return null;
      const data = await res.json() as { balance?: { balance?: number } };
      const tinybars = data?.balance?.balance ?? 0;
      return (tinybars / 1e8).toFixed(4) + " HBAR";
    } catch {
      return null;
    }
  }, []);

  // Fetch balance on mount if we have a persisted account
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

    setState(s => ({ ...s, isConnecting: true, error: null }));

    try {
      const connector = await getConnector();

      // Open HashPack modal — user must approve
      await connector.openModal();

      // Read account from active sessions
      const sessions = connector.walletConnectClient?.session.getAll() ?? [];
      const latest = sessions[sessions.length - 1];
      const accountId =
        latest?.namespaces?.hedera?.accounts?.[0]?.split(":")?.[2] ??
        latest?.namespaces?.["hedera:testnet"]?.accounts?.[0]?.split(":")?.[2] ??
        null;

      if (!accountId) {
        setState(s => ({ ...s, isConnecting: false, error: "No account found — approve in HashPack." }));
        return null;
      }

      localStorage.setItem(STORAGE_KEY, accountId);
      const balance = await fetchBalance(accountId);

      setState({
        accountId,
        balance,
        network: "testnet",
        isConnected: true,
        isConnecting: false,
        error: null,
      });

      return accountId;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      const dismissed = msg.toLowerCase().includes("modal closed") || msg.toLowerCase().includes("user rejected");
      setState(s => ({ ...s, isConnecting: false, error: dismissed ? null : msg }));
      return null;
    }
  }, [state.isConnecting, fetchBalance]);

  // disconnectWallet — clears storage and resets state, no popup
  const disconnectWallet = useCallback(() => {
    resetConnector();
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
    setState({ accountId: null, balance: null, network: "testnet", isConnected: false, isConnecting: false, error: null });
  }, []);

  // Refresh balance on demand
  const refreshBalance = useCallback(async () => {
    if (!state.accountId) return;
    const balance = await fetchBalance(state.accountId);
    if (balance) setState(s => ({ ...s, balance }));
  }, [state.accountId, fetchBalance]);

  return { ...state, connectWallet, disconnectWallet, refreshBalance };
}
