import { createContext, useContext, useEffect, useRef, useState } from 'react';
// @ts-ignore — hashconnect installed on Vercel; may not be in local node_modules
import { HashConnect } from 'hashconnect';

const WalletContext = createContext<any>(null);

// Read from Vite env — set VITE_WC_PROJECT_ID in .env (local) and Vercel env vars (production)
const WC_PROJECT_ID = import.meta.env.VITE_WC_PROJECT_ID as string;
const TIMEOUT_MS = 12_000;

export const WalletProvider = ({ children }: { children: React.ReactNode }) => {
  const hcRef = useRef<HashConnect | null>(null);
  const initPromiseRef = useRef<Promise<void> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryRef = useRef(false);

  const [accountId, setAccountId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!WC_PROJECT_ID) {
      console.error('[HashConnect] VITE_WC_PROJECT_ID is not set');
      return;
    }

    const appMetadata = {
      name: 'TruthForge',
      description: 'Live Trade Verification',
      icons: [`${window.location.origin}/favicon.png`],
      url: window.location.origin,
    };

    // v3: new HashConnect(LedgerId, projectId, appMetadata, debug)
    // Cast 'testnet' string to avoid @hashgraph/sdk static import
    const hc = new HashConnect('testnet' as any, WC_PROJECT_ID, appMetadata, false);
    hcRef.current = hc;

    // Register events BEFORE init() — some fire immediately on init
    hc.pairingEvent.on((data: { accountIds?: string[] }) => {
      if (data?.accountIds?.length) {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        setAccountId(data.accountIds[0]);
        setLoading(false);
        setError(null);
        retryRef.current = false;
      }
    });

    hc.disconnectionEvent?.on(() => {
      setAccountId(null);
    });

    hc.connectionStatusChangeEvent?.on((status: string) => {
      if (status === 'Disconnected') {
        setLoading(false);
      }
    });

    // init() on mount — stored so connectWallet can await it
    initPromiseRef.current = hc.init().catch((e: unknown) => {
      console.warn('[HashConnect] init error:', e);
    });

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const _attemptConnect = async () => {
    if (!hcRef.current) return;

    // Wait for init() to fully resolve before opening modal
    if (initPromiseRef.current) await initPromiseRef.current;

    setLoading(true);
    setError(null);

    // 12-second timeout — auto-retry once if extension doesn't respond
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(async () => {
      if (!retryRef.current) {
        retryRef.current = true;
        console.warn('[HashConnect] Timeout — retrying once');
        await _attemptConnect();
      } else {
        setLoading(false);
        setError('HashPack did not respond. Make sure the extension is installed and unlocked.');
        retryRef.current = false;
      }
    }, TIMEOUT_MS);

    try {
      // openPairingModal() — triggers HashPack Chrome extension popup instantly
      await hcRef.current.openPairingModal();
    } catch (e: unknown) {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      console.error('[HashConnect]', e);
      setError('Make sure HashPack extension is installed.');
      setLoading(false);
    }
  };

  const connectWallet = async () => {
    console.log('[HashConnect] connectWallet called — hcRef:', hcRef.current, '| WC_PROJECT_ID set:', !!WC_PROJECT_ID);
    if (loading) return;
    if (!WC_PROJECT_ID) {
      setError('WalletConnect Project ID is not configured. Contact support.');
      return;
    }
    if (!hcRef.current) {
      setError('HashConnect not initialized. Please refresh the page.');
      return;
    }
    retryRef.current = false;
    await _attemptConnect();
  };

  const disconnectWallet = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (hcRef.current) {
      try { hcRef.current.disconnect(); } catch { /* ignore */ }
    }
    setAccountId(null);
    setLoading(false);
    setError(null);
    retryRef.current = false;
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
