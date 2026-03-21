import { createContext, useContext, useEffect, useRef, useState } from 'react';
// @ts-ignore — hashconnect installed on Vercel; may not be in local node_modules
import { HashConnect } from 'hashconnect';

const WalletContext = createContext<any>(null);

const WC_PROJECT_ID = '2af6f5e4a8b3c1d7e9f0a2b4c6d8e0f2';

export const WalletProvider = ({ children }: { children: React.ReactNode }) => {
  const hashconnectRef = useRef<HashConnect | null>(null);
  const initializedRef = useRef(false);

  const [accountId, setAccountId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined' || initializedRef.current) return;

    const appMetadata = {
      name: 'TruthForge',
      description: 'Live Trade Verification',
      icons: [`${window.location.origin}/favicon.png`],
      url: window.location.origin,
    };

    // v3: new HashConnect(LedgerId, projectId, appMetadata, debug)
    // Cast 'testnet' string to avoid @hashgraph/sdk static import
    const hc = new HashConnect(
      'testnet' as any,
      WC_PROJECT_ID,
      appMetadata,
      false
    );

    hashconnectRef.current = hc;
    initializedRef.current = true;

    // Register events BEFORE init() — some fire immediately on init
    hc.pairingEvent.on((data: { accountIds?: string[] }) => {
      if (data?.accountIds?.length) {
        setAccountId(data.accountIds[0]);
        setLoading(false);
        setError(null);
      }
    });

    hc.disconnectionEvent.on(() => {
      setAccountId(null);
    });

    hc.connectionStatusChangeEvent?.on((status: string) => {
      if (status === 'Disconnected') {
        setLoading(false);
      }
    });

    // init() on mount — does NOT auto-connect, just prepares the instance
    hc.init().catch((e: unknown) => {
      console.warn('[HashConnect] init error:', e);
    });
  }, []);

  const connectWallet = async () => {
    if (!hashconnectRef.current) return;

    setLoading(true);
    setError(null);

    try {
      // openPairingModal() — triggers HashPack Chrome extension popup
      await hashconnectRef.current.openPairingModal();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to open HashPack';
      console.error('[HashConnect]', e);
      setError('Make sure HashPack extension is installed.');
      setLoading(false);
    }
    // loading stays true until pairingEvent fires with accountIds
  };

  const disconnectWallet = () => {
    if (hashconnectRef.current) {
      try { hashconnectRef.current.disconnect(); } catch { /* ignore */ }
    }
    setAccountId(null);
    setLoading(false);
    setError(null);
  };

  return (
    <WalletContext.Provider value={{
      connectWallet,
      disconnectWallet,
      accountId,
      isConnected: !!accountId,
      loading,
      error,
    }}>
      {children}
    </WalletContext.Provider>
  );
};

export const useWallet = () => useContext(WalletContext);
