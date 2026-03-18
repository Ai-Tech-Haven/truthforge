import React, { createContext, useContext, useState, useEffect, useRef } from 'react';

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

const WC_PROJECT_ID = 'b0d4a8b7c3e2f1a9d6e5c4b3a2f1e0d9';
const APP_METADATA = {
  name: 'TruthForge',
  description: 'Logistics verification platform on Hedera',
  icons: [`${typeof window !== 'undefined' ? window.location.origin : ''}/favicon.ico`],
  url: typeof window !== 'undefined' ? window.location.origin : 'https://truthforge.app',
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyConnector = any;

const WalletContext = createContext<WalletContextType | undefined>(undefined);

export const useWallet = () => {
  const context = useContext(WalletContext);
  if (!context) throw new Error('useWallet must be used within a WalletProvider');
  return context;
};

export const WalletProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [wallet, setWallet] = useState<WalletInfo | null>(null);
  const connectorRef = useRef<AnyConnector>(null);
  const initializedRef = useRef(false);

  useEffect(() => {
    const stored = localStorage.getItem('truthforge_wallet');
    if (stored) {
      try { setWallet(JSON.parse(stored)); } catch { localStorage.removeItem('truthforge_wallet'); }
    }
  }, []);

  const connectWallet = async (): Promise<boolean> => {
    try {
      if (!connectorRef.current || !initializedRef.current) {
        // Dynamic import — keeps hedera-wallet-connect out of Rollup's static analysis
        const [hwc, { LedgerId }] = await Promise.all([
          import('@hashgraph/hedera-wallet-connect'),
          import('@hiero-ledger/sdk'),
        ]);

        const { DAppConnector, HederaJsonRpcMethod, HederaSessionEvent, HederaChainId } = hwc;

        const connector = new DAppConnector(
          APP_METADATA,
          LedgerId.TESTNET,
          WC_PROJECT_ID,
          Object.values(HederaJsonRpcMethod),
          [HederaSessionEvent.ChainChanged, HederaSessionEvent.AccountsChanged],
          [HederaChainId.Testnet],
        );
        await connector.init({ logger: 'error' });
        connectorRef.current = connector;
        initializedRef.current = true;
      }

      await connectorRef.current.openModal();

      const sessions = connectorRef.current.walletConnectClient?.session.getAll() ?? [];
      const latest = sessions[sessions.length - 1];
      const accountId =
        latest?.namespaces?.hedera?.accounts?.[0]?.split(':')?.[2] ??
        latest?.namespaces?.['hedera:testnet']?.accounts?.[0]?.split(':')?.[2] ?? null;

      if (accountId) {
        const info: WalletInfo = { address: accountId, network: 'testnet', connected: true };
        setWallet(info);
        localStorage.setItem('truthforge_wallet', JSON.stringify(info));
        return true;
      }
      return false;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (!msg.toLowerCase().includes('modal closed') && !msg.toLowerCase().includes('user rejected')) {
        console.error('Wallet connect error:', err);
      }
      return false;
    }
  };

  const disconnectWallet = async () => {
    try {
      if (connectorRef.current) {
        await connectorRef.current.disconnectAll();
        connectorRef.current = null;
        initializedRef.current = false;
      }
    } catch { /* ignore */ }
    setWallet(null);
    localStorage.removeItem('truthforge_wallet');
  };

  return (
    <WalletContext.Provider value={{
      wallet,
      isWalletConnected: wallet?.connected ?? false,
      connectWallet,
      disconnectWallet,
    }}>
      {children}
    </WalletContext.Provider>
  );
};
