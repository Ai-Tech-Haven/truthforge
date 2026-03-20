// WalletConnectCard — Header wallet UI
// Real connectWallet() on click. No alerts. No auto-connect.

import { useState } from "react";
import { useWallet } from "@/contexts/WalletContext";
import { Wallet, LogOut, RefreshCw, ExternalLink, ChevronDown } from "lucide-react";

const WalletConnectCard = () => {
  const { accountId, balance, isConnected, isConnecting, error, connectWallet, disconnectWallet, refreshBalance } = useWallet();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refreshBalance();
    setRefreshing(false);
  };

  if (isConnected && accountId) {
    return (
      <div className="relative">
        <button
          onClick={() => setDropdownOpen(o => !o)}
          className="flex items-center gap-1.5 rounded-lg border border-success/40 bg-success/10 px-2.5 h-8 hover:bg-success/15 transition-colors"
          aria-haspopup="true"
          aria-expanded={dropdownOpen}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-success shrink-0" />
          <span className="font-mono text-[10px] text-success hidden sm:block truncate max-w-[90px]">
            {accountId}
          </span>
          {balance && (
            <span className="text-[10px] text-success/70 hidden md:block">{balance}</span>
          )}
          <ChevronDown className={`h-3 w-3 text-success/60 transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
        </button>

        {dropdownOpen && (
          <div
            className="absolute right-0 top-full mt-1 w-52 rounded-lg border border-border bg-card shadow-lg z-[9999] py-1"
            onMouseLeave={() => setDropdownOpen(false)}
          >
            <div className="px-3 py-2 border-b border-border">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Connected Wallet</div>
              <a
                href={`https://hashscan.io/testnet/account/${accountId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-xs text-accent hover:underline flex items-center gap-1"
                onClick={() => setDropdownOpen(false)}
              >
                {accountId}
                <ExternalLink className="h-2.5 w-2.5 shrink-0" />
              </a>
              {balance && <div className="text-xs text-success mt-0.5 font-medium">{balance}</div>}
            </div>

            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-foreground hover:bg-secondary transition-colors"
            >
              <RefreshCw className={`h-3.5 w-3.5 text-muted-foreground ${refreshing ? "animate-spin" : ""}`} />
              {refreshing ? "Refreshing..." : "Refresh Balance"}
            </button>

            <a
              href={`https://hashscan.io/testnet/account/${accountId}`}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-foreground hover:bg-secondary transition-colors"
              onClick={() => setDropdownOpen(false)}
            >
              <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
              View on HashScan
            </a>

            <button
              onClick={() => { disconnectWallet(); setDropdownOpen(false); }}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-destructive hover:bg-destructive/10 transition-colors border-t border-border mt-1"
            >
              <LogOut className="h-3.5 w-3.5" />
              Disconnect
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-end gap-0.5">
      <button
        onClick={connectWallet}
        disabled={isConnecting}
        className="flex items-center gap-1.5 px-3 h-8 rounded-lg border border-accent/50 bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isConnecting ? (
          <><RefreshCw className="h-3 w-3 animate-spin" /><span className="hidden sm:inline">Connecting...</span></>
        ) : (
          <><Wallet className="h-3 w-3" /><span className="hidden sm:inline">Connect Wallet</span></>
        )}
      </button>
      {error && (
        <span className="text-[9px] text-destructive max-w-[140px] truncate">{error}</span>
      )}
    </div>
  );
};

export default WalletConnectCard;
