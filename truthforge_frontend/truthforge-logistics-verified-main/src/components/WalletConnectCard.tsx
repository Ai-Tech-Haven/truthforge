import { useWallet } from "@/contexts/WalletContext";
import { Wallet, LogOut, RefreshCw, ExternalLink } from "lucide-react";

/**
 * WalletConnectCard — shown in the Header for Merchant & Carrier portals.
 * Connects to HashPack on testnet. Vercel-safe: no static hashgraph imports.
 */
const WalletConnectCard = () => {
  const { wallet, isConnecting, connectWallet, disconnectWallet } = useWallet();

  if (wallet?.accountId) {
    return (
      <div className="flex items-center gap-1.5 rounded-lg border border-success/40 bg-success/10 px-2.5 h-8">
        <span className="h-1.5 w-1.5 rounded-full bg-success shrink-0" />
        <a
          href={`https://hashscan.io/testnet/account/${wallet.accountId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="font-mono text-[10px] text-success hover:underline flex items-center gap-0.5 hidden sm:flex"
          title={wallet.accountId}
        >
          {wallet.accountId}
          <ExternalLink className="h-2.5 w-2.5 shrink-0" />
        </a>
        <span className="font-mono text-[10px] text-success sm:hidden">
          {wallet.accountId.slice(0, 8)}…
        </span>
        <button
          onClick={disconnectWallet}
          title="Disconnect wallet"
          className="ml-1 text-success/60 hover:text-success transition-colors"
        >
          <LogOut className="h-3 w-3" />
        </button>
      </div>
    );
  }

  return (
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
  );
};

export default WalletConnectCard;
