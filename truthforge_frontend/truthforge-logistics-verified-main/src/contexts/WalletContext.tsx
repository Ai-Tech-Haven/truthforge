// WalletContext — thin wrapper around useHashPackWallet
// Provides wallet state to the entire app via React context.
// ZERO top-level @hashgraph imports — Vercel-safe.

import React, { createContext, useContext } from "react";
import { useHashPackWallet, WalletState } from "@/hooks/useHashPackWallet";

interface WalletContextType extends WalletState {
  connectWallet: () => Promise<string | null>;
  disconnectWallet: () => void;
  refreshBalance: () => Promise<void>;
  // Legacy compat alias
  wallet: { accountId: string; network: string } | null;
}

const WalletContext = createContext<WalletContextType>({
  accountId: null,
  balance: null,
  network: "testnet",
  isConnected: false,
  isConnecting: false,
  error: null,
  connectWallet: async () => null,
  disconnectWallet: () => {},
  refreshBalance: async () => {},
  wallet: null,
});

export const useWallet = () => useContext(WalletContext);

export const WalletProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const walletHook = useHashPackWallet();

  // Legacy compat: expose wallet.accountId shape used by LiveModeBanner / MerchantPortalPage
  const wallet = walletHook.isConnected && walletHook.accountId
    ? { accountId: walletHook.accountId, network: walletHook.network }
    : null;

  return (
    <WalletContext.Provider value={{ ...walletHook, wallet }}>
      {children}
    </WalletContext.Provider>
  );
};
