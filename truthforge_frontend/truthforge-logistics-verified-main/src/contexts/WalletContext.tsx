import { createContext, useContext, useEffect, useRef, useState } from 'react';
// @ts-ignore — hashconnect installed on Vercel; not in local node_modules
import { HashConnect, HashConnectConnectionState } from 'hashconnect';

const WalletContext = createContext<any>(null);

const WC_PROJECT_ID = import.meta.env.VITE_WC_PROJECT_ID as string;
const TIMEOUT_MS = 12_000;

// Persist pairing across page reloads
const STORAGE_KEY = 'tf_hc_account';

export const WalletProvider = ({ children }: { children: React.ReactNode }) => {
  const hcRef = useRef<HashConnect | null>(null);
  const initDoneRef = useRef(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryRef = useRef(false);

  // Restore from localStorage so UI shows "Connected" immediately on reload
  const [accountId, setAccountId] = useState<string | null>(
    () => localStorage.getItem(STORAGE_KEY)
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connState, setConnState] = useState<string>('Disconnected');

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

    const hc = new HashConnect('testnet' as any, WC_PROJECT_ID, appMetadata, false);
    hcRef.current = hc;

    // ── Events registered BEFORE init() ──────────────────────────────────────

    // pairingEvent fires on init() if a saved session exists (session restore),
    // AND fires again when user approves a new pairing in the extension.
    hc.pairingEvent.on((data: { accountIds?: string[]; network?: string }) => {
      console.log('[HashConnect] pairingEvent:', data);
      if (data?.accountIds?.length) {
        const id = data.accountIds[0];
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        setAccountId(id);
        localStorage.setItem(STORAGE_KEY, id);
        setLoading(false);
        setError(null);
        retryRef.current = false;
      }
    });

    hc.disconnectionEvent?.on(() => {
      console.log('[HashConnect] disconnectionEvent');
      setAccountId(null);
      localStorage.removeItem(STORAGE_KEY);
      setConnState('Disconnected');
    });

    // connectionStatusChangeEvent: "Connecting" | "Connected" | "Disconnected" | "Paired"
    hc.connectionStatusChangeEvent?.on((status: string) => {
      console.log('[HashConnect] connectionStatus:', status);
      setConnState(status);
      // If status goes to Paired/Connected and we have an account, clear loading
      if (status === HashConnectConnectionState?.Paired || status === 'Paired') {
        setLoading(false);
      }
      if (status === HashConnectConnectionState?.Disconnected || status === 'Disconnected') {
        setLoading(false);
      }
    });

    // init() — restores existing WalletConnect session if one exists.
    // pairingEvent will fire synchronously during init if session is found.
    hc.init()
      .then(() => {
        initDoneRef.current = true;
        console.log('[HashConnect] init() complete');
      })
      .catch((e: unknown) => {
        initDoneRef.current = true;
        console.warn('[HashConnect] init error:', e);
      });

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const _attemptConnect = async () => {
    const hc = hcRef.current;
    if (!hc) return;

    setLoading(true);
    setError(null);

    // Timeout — auto-retry once
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
      // openPairingModal() triggers the HashPack extension popup.
      // If already paired, the extension shows the existing session — user
      // does NOT need to re-approve; pairingEvent fires immediately.
      await hc.openPairingModal();
    } catch (e: unknown) {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      console.error('[HashConnect] openPairingModal error:', e);
      setError('Make sure HashPack extension is installed and unlocked.');
      setLoading(false);
    }
  };

  const connectWallet = async () => {
    console.log('[HashConnect] connectWallet — hcRef:', hcRef.current, '| WC_PROJECT_ID:', !!WC_PROJECT_ID);
    if (loading) return;

    if (!WC_PROJECT_ID) {
      setError('WalletConnect Project ID is not configured. Contact support.');
      return;
    }
    if (!hcRef.current) {
      setError('HashConnect not initialized. Please refresh the page.');
      return;
    }

    // Already connected — nothing to do
    if (accountId) {
      console.log('[HashConnect] already connected:', accountId);
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
    localStorage.removeItem(STORAGE_KEY);
    setLoading(false);
    setError(null);
    retryRef.current = false;
    setConnState('Disconnected');
  };

  return (
    <WalletContext.Provider value={{
      connectWallet,
      disconnectWallet,
      accountId,
      isConnected: !!accountId,
      loading,
      error,
      connState,
    }}>
      {children}
    </WalletContext.Provider>
  );
};

export const useWallet = () => useContext(WalletContext);
