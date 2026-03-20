// WalletConnectCard — Header wallet UI
// Opens HashPack extension popup on click only.
// If extension not installed: shows inline message + download link.
// No auto-connect. No redirects. No SDK.

import { useState } from "react";
import { useWallet } from "@/contexts/WalletContext";
import { Wallet, LogOut, RefreshCw, ExternalLink, ChevronDown, Download } from "lucide-react";

// Shorten address: 0.0.1234567 → 0.0.123…567
function shortAddr(id: string): string {
  if (id.length <= 12) return id;
  return id.slice(0, 7) + "…" + id.slice(-3);
}

const WalletConnectCard = () => {
  const {
    accountId, balance, isConnected, isConnecting,
    error, notInstalled,
    connectWallet, disconnectWallet, refreshBalance,
  } = useWallet();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refreshBalance();
    setRefreshing(false);
  };

  // ── Connected state ──────────────────────────────────────────────────────
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

  // ── Not connected state ──────────────────────────────────────────────────
  return (
    <div className="flex flex-col items-end gap-0.5">
      <button
        onClick={connectWallet}
        disabled={isConnecting}
        className="flex items-center gap-1 px-2 h-7 rounded border border-accent/50 bg-accent/10 text-accent text-[10px] font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isConnecting ? (
          <><RefreshCw className="h-2.5 w-2.5 animate-spin" /><span className="hidden sm:inline">Connecting…</span></>
        ) : (
          <><Wallet className="h-2.5 w-2.5" /><span className="hidden sm:inline">Connect</span></>
        )}
      </button>

      {/* Extension not installed — inline message + download link, no forced redirect */}
      {notInstalled && (
        <div className="flex items-center gap-1 text-[9px] text-warning">
          <span>HashPack not detected.</span>
          <a
            href="https://www.hashpack.app/download"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-0.5 text-accent hover:underline"
          >
            <Download className="h-2 w-2" /> Install
          </a>
        </div>
      )}

      {/* Other errors */}
      {error && !notInstalled && (
        <span className="text-[9px] text-destructive max-w-[130px] truncate">{error}</span>
      )}
    </div>
  );
};

export default WalletConnectCard;
