import React, { createContext, useContext, useState, useEffect } from 'react';

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

const WalletContext = createContext<WalletContextType | undefined>(undefined);

export const useWallet = () => {
  const context = useContext(WalletContext);
  if (!context) {
    throw new Error('useWallet must be used within a WalletProvider');
  }
  return context;
};

export const WalletProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [wallet, setWallet] = useState<WalletInfo | null>(null);

  // Load wallet from localStorage on mount
  useEffect(() => {
    const storedWallet = localStorage.getItem('truthforge_wallet');
    if (storedWallet) {
      try {
        setWallet(JSON.parse(storedWallet));
      } catch (e) {
        localStorage.removeItem('truthforge_wallet');
      }
    }
  }, []);

  const connectWallet = async (): Promise<boolean> => {
    // Mock wallet connection - in production, this would integrate with HashPack or other Hedera wallets
    try {
      // Simulate wallet connection delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock wallet info
      const mockWallet: WalletInfo = {
        address: '0.0.123456',
        network: 'testnet',
        connected: true,
      };
      
      setWallet(mockWallet);
      localStorage.setItem('truthforge_wallet', JSON.stringify(mockWallet));
      return true;
    } catch (error) {
      console.error('Failed to connect wallet:', error);
      return false;
    }
  };

  const disconnectWallet = () => {
    setWallet(null);
    localStorage.removeItem('truthforge_wallet');
  };

  const value: WalletContextType = {
    wallet,
    isWalletConnected: wallet?.connected || false,
    connectWallet,
    disconnectWallet,
  };

  return <WalletContext.Provider value={value}>{children}</WalletContext.Provider>;
};
