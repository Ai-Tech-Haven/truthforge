import React, { createContext, useContext } from 'react';

export interface WalletInfo {
  address: string;
  network: string;
  connected: boolean;
}

interface WalletContextType {
  wallet: WalletInfo | null;
  isWalletConnected: boolean;
  connectWallet: () => Promise<boolean>;
  disconnectWallet: () => void;
}

const WalletContext = createContext<WalletContextType>({
  wallet: null,
  isWalletConnected: false,
  connectWallet: async () => false,
  disconnectWallet: () => {},
});

export const useWallet = () => useContext(WalletContext);

export const WalletProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <WalletContext.Provider value={{
    wallet: null,
    isWalletConnected: false,
    connectWallet: async () => false,
    disconnectWallet: () => {},
  }}>
    {children}
  </WalletContext.Provider>
);
