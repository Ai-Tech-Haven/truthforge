/**
 * WalletContext — Vercel-safe HashPack/hedera-wallet-connect integration.
 *
 * SAFETY RULES:
 * - ZERO top-level imports of @hashgraph/* or @hiero-ledger/*
 * - All wallet libs loaded via Function("s","return import(s)") — invisible to Rollup
 * - connectWallet() must only be called from an explicit user click handler
 * - Never auto-called on mount
 */
import React, { createContext, useContext, useState, useRef, useCallback } from "react";

export interface WalletInfo {
  accountId: string;
  network: "testnet" | "mainnet";
}

interface WalletContextType {
  wallet: WalletInfo | null;
  isConnecting: boolean;
  connectWallet: () => Promise<WalletInfo | null>;
  disconnectWallet: () => void;
}

const WalletContext = createContext<WalletContextType>({
  wallet: null,
  isConnecting: false,
  connectWallet: async () => null,
  disconnectWallet: () => {},
});

export const useWallet = () => useContext(WalletContext);

const WC_PROJECT_ID = "b0d4a8b7c3e2f1a9d6e5c4b3a2f1e0d9";

// Runtime-assembled specifiers — Rollup cannot statically analyse these
const _hwc = () => ["@hashgraph", "hedera-wallet-connect"].join("/");
const _sdk = () => ["@hiero-ledger", "sdk"].join("/");

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyConnector = any;

export const WalletProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [wallet, setWallet] = useState<WalletInfo | null>(() => {
    // Restore persisted wallet info (account ID only — no connector state)
    try {
      const stored = localStorage.getItem("tf_wallet");
      return stored ? JSON.parse(stored) : null;
    } catch { return null; }
  });
  const [isConnecting, setIsConnecting] = useState(false);
  const connectorRef = useRef<AnyConnector>(null);
  const initializedRef = useRef(false);

  const connectWallet = useCallback(async (): Promise<WalletInfo | null> => {
    if (typeof window === "undefined") return null;
    setIsConnecting(true);
    try {
      if (!connectorRef.current || !initializedRef.current) {
        // Dynamic imports via runtime-built specifiers — invisible to Rollup/Vercel
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
        connectorRef.current = connector;
        initializedRef.current = true;
      }

      await connectorRef.current.openModal();

      const sessions = connectorRef.current.walletConnectClient?.session.getAll() ?? [];
      const latest = sessions[sessions.length - 1];
      const accountId =
        latest?.namespaces?.hedera?.accounts?.[0]?.split(":")?.[2] ??
        latest?.namespaces?.["hedera:testnet"]?.accounts?.[0]?.split(":")?.[2] ??
        null;

      if (!accountId) return null;

      const info: WalletInfo = { accountId, network: "testnet" };
      setWallet(info);
      localStorage.setItem("tf_wallet", JSON.stringify(info));
      return info;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (!msg.toLowerCase().includes("modal closed") && !msg.toLowerCase().includes("user rejected")) {
        console.error("[WalletContext] connect error:", msg);
      }
      return null;
    } finally {
      setIsConnecting(false);
    }
  }, []);

  const disconnectWallet = useCallback(() => {
    try {
      if (connectorRef.current) {
        connectorRef.current.disconnectAll?.();
        connectorRef.current = null;
        initializedRef.current = false;
      }
    } catch { /* ignore */ }
    setWallet(null);
    localStorage.removeItem("tf_wallet");
  }, []);

  return (
    <WalletContext.Provider value={{ wallet, isConnecting, connectWallet, disconnectWallet }}>
      {children}
    </WalletContext.Provider>
  );
};
