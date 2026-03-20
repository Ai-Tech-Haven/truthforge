import { useMockMode } from "@/contexts/MockModeContext";
import { useWallet } from "@/contexts/WalletContext";
import { Zap, AlertTriangle, Wallet } from "lucide-react";

/**
 * LiveModeBanner — shown at the top of portal pages.
 * LIVE MODE: prominent red/green banner with wallet status.
 * MOCK MODE: subtle amber notice — wallet popup never fires.
 */
const LiveModeBanner = () => {
  const { isMockMode } = useMockMode();
  const { wallet, connectWallet, isConnecting } = useWallet();

  if (isMockMode) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 rounded-lg border border-warning/30 bg-warning/5 text-warning text-xs font-medium">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
        <span>Mock Mode — simulated flow only. Wallet popup will never open.</span>
      </div>
    );
  }

  // LIVE MODE
  return (
    <div className="rounded-lg border border-success/40 bg-success/5 px-4 py-3 space-y-2">
      {/* Main badge */}
      <div className="flex items-center gap-2">
        <Zap className="h-4 w-4 text-success shrink-0" />
        <span className="text-sm font-heading font-bold text-success uppercase tracking-wider">
          Live Mode &mdash; Real Hedera Transactions
        </span>
      </div>

      {/* Requirements checklist */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
        <span className="text-success flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-success inline-block" />
          Production backend active
        </span>
        <span className="text-success flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-success inline-block" />
          Real document uploads required
        </span>
        <span className="text-success flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-success inline-block" />
          Real HBAR payment on pre-clearance
        </span>
        <span className="text-success flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-success inline-block" />
          HCS transaction hash recorded on-chain
        </span>
      </div>

      {/* Wallet status */}
      {wallet?.accountId ? (
        <div className="flex items-center gap-2 text-[11px] text-success/80">
          <Wallet className="h-3 w-3 shrink-0" />
          Wallet connected: {wallet.accountId}
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-[11px] text-warning">
            <Wallet className="h-3 w-3 shrink-0" />
            Wallet not connected — required for HBAR payment
          </div>
          <button
            onClick={connectWallet}
            disabled={isConnecting}
            className="px-2.5 py-1 rounded border border-accent/50 bg-accent/10 text-accent text-[10px] font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-50"
          >
            {isConnecting ? "Connecting..." : "Connect Wallet"}
          </button>
        </div>
      )}
    </div>
  );
};

export default LiveModeBanner;
