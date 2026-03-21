// WalletConnectCard — compact wallet button in header.
// Uses init() + connectToLocalWallet() via WalletContext.
// No auto-connect. No SDK. No polyfills.

import { useState, useRef, useEffect } from 'react'
import { useWallet } from '@/contexts/WalletContext'
import { Wallet, LogOut, ExternalLink, ChevronDown, Download, Zap, RefreshCw } from 'lucide-react'

function shortAddr(id: string): string {
  if (id.length <= 12) return id
  return id.slice(0, 7) + '…' + id.slice(-3)
}

const WalletConnectCard = () => {
  const { accountId, isConnected, loading, error, connectWallet, disconnectWallet } = useWallet()

  const [dropdownOpen, setDropdownOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Close dropdown after successful connection
  useEffect(() => {
    if (isConnected) setDropdownOpen(false)
  }, [isConnected])

  // ── Connected ──────────────────────────────────────────────────────────────
  if (isConnected && accountId) {
    return (
      <div className="relative z-50" ref={ref}>
        <button
          onClick={() => setDropdownOpen(o => !o)}
          className="flex items-center gap-1 rounded border border-success/40 bg-success/10 px-2 h-7 hover:bg-success/15 transition-colors"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-success shrink-0" />
          <span className="font-mono text-[9px] text-success hidden sm:block">{shortAddr(accountId)}</span>
          <ChevronDown className={`h-2.5 w-2.5 text-success/60 transition-transform ml-0.5 ${dropdownOpen ? 'rotate-180' : ''}`} />
        </button>

        {dropdownOpen && (
          <div className="absolute right-0 top-full mt-1 w-52 rounded-lg border border-border bg-card shadow-lg z-[200] py-1">
            <div className="px-3 py-2 border-b border-border">
              <div className="text-[9px] text-muted-foreground uppercase tracking-wider mb-1">Connected · Hedera Testnet</div>
              <a
                href={`https://hashscan.io/testnet/account/${accountId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-[10px] text-accent hover:underline flex items-center gap-1"
                onClick={() => setDropdownOpen(false)}
              >
                {accountId}<ExternalLink className="h-2.5 w-2.5 shrink-0" />
              </a>
            </div>
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
              onClick={() => { disconnectWallet(); setDropdownOpen(false) }}
              className="w-full flex items-center gap-2 px-3 py-2 text-[10px] text-destructive hover:bg-destructive/10 transition-colors border-t border-border mt-1"
            >
              <LogOut className="h-3 w-3" />
              Disconnect
            </button>
          </div>
        )}
      </div>
    )
  }

  // ── Not connected ──────────────────────────────────────────────────────────
  return (
    <div className="relative z-50" ref={ref}>
      <button
        onClick={() => setDropdownOpen(o => !o)}
        className="flex items-center gap-1 px-2 h-7 rounded border border-accent/50 bg-accent/10 text-accent text-[10px] font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors whitespace-nowrap"
      >
        <Wallet className="h-2.5 w-2.5 shrink-0" />
        <span className="hidden sm:inline">Connect</span>
        <ChevronDown className={`h-2.5 w-2.5 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
      </button>

      {dropdownOpen && (
        <div className="absolute right-0 top-full mt-1 w-56 rounded-lg border border-white/10 bg-[#0b1f33] shadow-xl z-[200] p-3">
          <p className="text-[10px] text-slate-400 mb-3 leading-relaxed">
            Connect your HashPack wallet to verify shipments on Hedera Testnet.
          </p>

          {error && (
            <div className="mb-3 px-2 py-1.5 rounded border border-destructive/30 bg-destructive/10 text-[10px] text-destructive">
              {error}
            </div>
          )}

          {/* Connect HashPack — triggers extension popup via init() + connectToLocalWallet() */}
          <button
            onClick={connectWallet}
            disabled={loading}
            className="flex items-center justify-center gap-1.5 w-full px-3 py-2 rounded-lg bg-accent text-white text-xs font-bold uppercase tracking-wider hover:bg-accent/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed mb-2"
          >
            {loading
              ? <><RefreshCw className="h-3 w-3 animate-spin" /> Connecting…</>
              : <><Zap className="h-3 w-3" /> Connect HashPack</>
            }
          </button>

          {/* Download fallback */}
          <a
            href="https://www.hashpack.app/download"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-1.5 w-full px-3 py-2 rounded-lg border border-white/20 text-slate-300 text-xs font-medium hover:bg-white/5 hover:text-white transition-colors"
            onClick={() => setDropdownOpen(false)}
          >
            <Download className="h-3 w-3" />
            Download HashPack
          </a>
        </div>
      )}
    </div>
  )
}

export default WalletConnectCard
