// WalletContext — thin wrapper around useHashPackWallet
// Provides wallet state app-wide. No top-level SDK imports.

import React, { createContext, useContext } from "react";
import { useHashPackWallet, WalletState } from "@/hooks/useHashPackWallet";

interface WalletContextType extends WalletState {
  connectWallet: () => Promise<string | null>;
  disconnectWallet: () => void;
  refreshBalance: () => Promise<void>;
  // Legacy compat shape used by LiveModeBanner / MerchantPortalPage
  wallet: { accountId: string; network: string } | null;
}

const WalletContext = createContext<WalletContextType>({
  accountId: null,
  balance: null,
  network: "testnet",
  isConnected: false,
  isConnecting: false,
  error: null,
  notInstalled: false,
  connectWallet: async () => null,
  disconnectWallet: () => {},
  refreshBalance: async () => {},
  wallet: null,
});

export const useWallet = () => useContext(WalletContext);

export const WalletProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const hook = useHashPackWallet();
  const wallet = hook.isConnected && hook.accountId
    ? { accountId: hook.accountId, network: hook.network }
    : null;

  return (
    <WalletContext.Provider value={{ ...hook, wallet }}>
      {children}
    </WalletContext.Provider>
  );
};
