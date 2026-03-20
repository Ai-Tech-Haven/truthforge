// WalletConnectCard — Header wallet UI
// Click → popup modal with "Connect HashPack" + "Download" buttons.
// Connect HashPack triggers browser extension pairing.
// Download opens hashpack.app/download in a new tab.
// No auto-connect. No forced redirects. No SDK.

import { useState } from "react";
import { useWallet } from "@/contexts/WalletContext";
import {
  Wallet, LogOut, RefreshCw, ExternalLink,
  ChevronDown, Download, X, Zap,
} from "lucide-react";

// Shorten address: 0.0.1234567 → 0.0.123…567
function shortAddr(id: string): string {
  if (id.length <= 12) return id;
  return id.slice(0, 7) + "…" + id.slice(-3);
}

// ── HashPack Connect Modal ────────────────────────────────────────────────────
interface ModalProps {
  isConnecting: boolean;
  error: string | null;
  onConnect: () => void;
  onClose: () => void;
}

const HashPackModal = ({ isConnecting, error, onConnect, onClose }: ModalProps) => (
  <div
    className="fixed inset-0 z-[300] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
    onClick={onClose}
  >
    <div
      className="bg-[#0b1f33] border border-white/10 rounded-xl p-6 w-full max-w-sm shadow-2xl"
      onClick={e => e.stopPropagation()}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <Wallet className="h-5 w-5 text-accent" />
          <span className="text-sm font-bold text-white tracking-wide">Connect Wallet</span>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-colors"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Description */}
      <p className="text-xs text-slate-400 mb-5 leading-relaxed">
        Connect your HashPack wallet to sign transactions and verify shipments on Hedera Testnet.
      </p>

      {/* Error */}
      {error && (
        <div className="mb-4 px-3 py-2 rounded border border-destructive/30 bg-destructive/10 text-xs text-destructive">
          {error}
        </div>
      )}

      {/* Buttons */}
      <div className="flex flex-col gap-3">
        {/* Connect HashPack — triggers browser extension */}
        <button
          onClick={onConnect}
          disabled={isConnecting}
          className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg bg-accent text-white text-sm font-bold uppercase tracking-wider hover:bg-accent/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isConnecting ? (
            <><RefreshCw className="h-4 w-4 animate-spin" /> Connecting…</>
          ) : (
            <><Zap className="h-4 w-4" /> Connect HashPack</>
          )}
        </button>

        {/* Download — opens hashpack.app in new tab */}
        <a
          href="https://www.hashpack.app/download"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg border border-white/20 text-slate-300 text-sm font-medium hover:bg-white/5 hover:text-white transition-colors"
          onClick={onClose}
        >
          <Download className="h-4 w-4" />
          Download HashPack
        </a>
      </div>

      <p className="text-[10px] text-slate-500 text-center mt-4">
        Hedera Testnet · Identity only · No auto-connect
      </p>
    </div>
  </div>
);

// ── Main Component ────────────────────────────────────────────────────────────
const WalletConnectCard = () => {
  const {
    accountId, balance, isConnected, isConnecting,
    error, connectWallet, disconnectWallet, refreshBalance,
  } = useWallet();

  const [modalOpen, setModalOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refreshBalance();
    setRefreshing(false);
  };

  const handleConnect = async () => {
    await connectWallet();
    // Close modal on success (accountId will be set)
    if (!error) setModalOpen(false);
  };

  // ── Connected ──────────────────────────────────────────────────────────────
  if (isConnected && accountId) {
    return (
      <div className="relative z-50">
        <button
          onClick={() => setDropdownOpen(o => !o)}
          className="flex items-center gap-1 rounded border border-success/40 bg-success/10 px-2 h-7 hover:bg-success/15 transition-colors"
          aria-haspopup="true"
          aria-expanded={dropdownOpen}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-success shrink-0" />
          <span className="font-mono text-[9px] text-success hidden sm:block">
            {shortAddr(accountId)}
          </span>
          {balance && (
            <span className="text-[9px] text-success/70 hidden lg:block ml-0.5">{balance}</span>
          )}
          <ChevronDown className={`h-2.5 w-2.5 text-success/60 transition-transform ml-0.5 ${dropdownOpen ? "rotate-180" : ""}`} />
        </button>

        {dropdownOpen && (
          <div
            className="absolute right-0 top-full mt-1 w-48 rounded-lg border border-border bg-card shadow-lg z-50 py-1"
            onMouseLeave={() => setDropdownOpen(false)}
          >
            <div className="px-3 py-2 border-b border-border">
              <div className="text-[9px] text-muted-foreground uppercase tracking-wider mb-1">Connected</div>
              <a
                href={`https://hashscan.io/testnet/account/${accountId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-[10px] text-accent hover:underline flex items-center gap-1"
                onClick={() => setDropdownOpen(false)}
              >
                {accountId}
                <ExternalLink className="h-2.5 w-2.5 shrink-0" />
              </a>
              {balance && <div className="text-[10px] text-success mt-0.5 font-medium">{balance}</div>}
            </div>

            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="w-full flex items-center gap-2 px-3 py-2 text-[10px] text-foreground hover:bg-secondary transition-colors"
            >
              <RefreshCw className={`h-3 w-3 text-muted-foreground ${refreshing ? "animate-spin" : ""}`} />
              {refreshing ? "Refreshing..." : "Refresh Balance"}
            </button>

            <a
              href={`https://hashscan.io/testnet/account/${accountId}`}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center gap-2 px-3 py-2 text-[10px] text-foreground hover:bg-secondary transition-colors"
              onClick={() => setDropdownOpen(false)}
            >
              <ExternalLink className="h-3 w-3 text-muted-foreground" />
              View on HashScan
            </a>

            <button
              onClick={() => { disconnectWallet(); setDropdownOpen(false); }}
              className="w-full flex items-center gap-2 px-3 py-2 text-[10px] text-destructive hover:bg-destructive/10 transition-colors border-t border-border mt-1"
            >
              <LogOut className="h-3 w-3" />
              Disconnect
            </button>
          </div>
        )}
      </div>
    );
  }

  // ── Not connected ──────────────────────────────────────────────────────────
  return (
    <>
      <button
        onClick={() => setModalOpen(true)}
        className="flex items-center gap-1 px-2 h-7 rounded border border-accent/50 bg-accent/10 text-accent text-[10px] font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors whitespace-nowrap"
      >
        <Wallet className="h-2.5 w-2.5 shrink-0" />
        <span className="hidden sm:inline">Connect</span>
      </button>

      {modalOpen && (
        <HashPackModal
          isConnecting={isConnecting}
          error={error}
          onConnect={handleConnect}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
};

export default WalletConnectCard;
