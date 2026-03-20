// useHashPackWallet — Vercel-safe HashPack wallet hook
// RULES:
//   - Zero top-level @hashgraph / @hiero-ledger imports
//   - All SDK code inside connectWallet() only
//   - No auto-connect on mount
//   - localStorage for persistence (display-only after refresh)

import { useState, useCallback } from "react";

const STORAGE_KEY_ACCOUNT = "tf_wallet_account";
const STORAGE_KEY_NETWORK = "tf_wallet_network";

// Runtime-assembled specifiers — Rollup cannot statically analyse these
const _hwc = () => ["@hashgraph", "hedera-wallet-connect"].join("/");
const _sdk = () => ["@hiero-ledger", "sdk"].join("/");
const WC_PROJECT_ID = "b0d4a8b7c3e2f1a9d6e5c4b3a2f1e0d9";

export interface WalletState {
  accountId: string | null;
  balance: string | null;
  network: "testnet" | "mainnet";
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
}

// Read persisted account from localStorage (client-only, display-only)
function readPersistedAccount(): { accountId: string | null; network: "testnet" | "mainnet" } {
  if (typeof window === "undefined") return { accountId: null, network: "testnet" };
  try {
    const accountId = localStorage.getItem(STORAGE_KEY_ACCOUNT);
    const network = (localStorage.getItem(STORAGE_KEY_NETWORK) ?? "testnet") as "testnet" | "mainnet";
    return { accountId, network };
  } catch {
    return { accountId: null, network: "testnet" };
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _connector: any = null;
let _initialized = false;

export function useHashPackWallet() {
  const persisted = readPersistedAccount();

  const [state, setState] = useState<WalletState>({
    accountId: persisted.accountId,
    balance: null,
    network: persisted.network,
    isConnected: !!persisted.accountId,
    isConnecting: false,
    error: null,
  });

  // Fetch HBAR balance from Hedera mirror node (no SDK needed)
  const fetchBalance = useCallback(async (accountId: string, network: "testnet" | "mainnet") => {
    try {
      const base = network === "mainnet"
        ? "https://mainnet-public.mirrornode.hedera.com"
        : "https://testnet.mirrornode.hedera.com";
      const res = await fetch(`${base}/api/v1/accounts/${accountId}`);
      if (!res.ok) return null;
      const data = await res.json() as { balance?: { balance?: number } };
      const tinybars = data?.balance?.balance ?? 0;
      return (tinybars / 1e8).toFixed(4) + " HBAR";
    } catch {
      return null;
    }
  }, []);

  // connectWallet — MUST be called from explicit user click only
  const connectWallet = useCallback(async (): Promise<string | null> => {
    if (typeof window === "undefined") return null;

    setState(s => ({ ...s, isConnecting: true, error: null }));

    try {
      if (!_connector || !_initialized) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const dynImport = Function("s", "return import(s)") as (s: string) => Promise<any>;
        const [hwc, sdk] = await Promise.all([dynImport(_hwc()), dynImport(_sdk())]);
        const { DAppConnector, HederaJsonRpcMethod, HederaSessionEvent, HederaChainId } = hwc;
        const { LedgerId } = sdk;

        const meta = {
          name: "TruthForge",
          description: "Logistics verification platform on Hedera",
          icons: [`${window.location.origin}/favicon.ico`],
          url: window.location.origin,
        };

        const connector = new DAppConnector(
          meta,
          LedgerId.TESTNET,
          WC_PROJECT_ID,
          Object.values(HederaJsonRpcMethod),
          [HederaSessionEvent.ChainChanged, HederaSessionEvent.AccountsChanged],
          [HederaChainId.Testnet],
        );
        await connector.init({ logger: "error" });
        _connector = connector;
        _initialized = true;
      }

      // Open HashPack popup — user must approve
      await _connector.openModal();

      const sessions = _connector.walletConnectClient?.session.getAll() ?? [];
      const latest = sessions[sessions.length - 1];
      const accountId =
        latest?.namespaces?.hedera?.accounts?.[0]?.split(":")?.[2] ??
        latest?.namespaces?.["hedera:testnet"]?.accounts?.[0]?.split(":")?.[2] ??
        null;

      if (!accountId) {
        setState(s => ({ ...s, isConnecting: false, error: "No account found. Approve in HashPack." }));
        return null;
      }

      // Persist to localStorage (display-only on next load)
      localStorage.setItem(STORAGE_KEY_ACCOUNT, accountId);
      localStorage.setItem(STORAGE_KEY_NETWORK, "testnet");

      // Fetch balance
      const balance = await fetchBalance(accountId, "testnet");

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
      const userRejected =
        msg.toLowerCase().includes("modal closed") ||
        msg.toLowerCase().includes("user rejected");
      setState(s => ({
        ...s,
        isConnecting: false,
        error: userRejected ? null : msg,
      }));
      return null;
    }
  }, [fetchBalance]);

  // disconnectWallet — clears localStorage and resets state, no SDK call needed
  const disconnectWallet = useCallback(() => {
    try {
      if (_connector) {
        _connector.disconnectAll?.();
        _connector = null;
        _initialized = false;
      }
    } catch { /* ignore */ }
    try {
      localStorage.removeItem(STORAGE_KEY_ACCOUNT);
      localStorage.removeItem(STORAGE_KEY_NETWORK);
    } catch { /* ignore */ }
    setState({
      accountId: null,
      balance: null,
      network: "testnet",
      isConnected: false,
      isConnecting: false,
      error: null,
    });
  }, []);

  // Refresh balance on demand (no popup, no SDK)
  const refreshBalance = useCallback(async () => {
    if (!state.accountId) return;
    const balance = await fetchBalance(state.accountId, state.network);
    setState(s => ({ ...s, balance }));
  }, [state.accountId, state.network, fetchBalance]);

  return {
    ...state,
    connectWallet,
    disconnectWallet,
    refreshBalance,
  };
}
