import { useState, useEffect, useCallback } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import { mockShipments, mockPortTrustReceipts, ShipmentTracking } from "@/lib/mock-data";
import {
  Package, ChevronDown, CheckCircle, Clock, AlertTriangle,
  Wallet, Shield, Zap, ToggleLeft, ToggleRight, LogOut, LogIn,
  ExternalLink, RefreshCw, X
} from "lucide-react";
import PortTrustReceipt from "@/components/PortTrustReceipt";
import OrderClearanceTimeline, { ClearanceStepData } from "@/components/OrderClearanceTimeline";
import { useToast } from "@/hooks/use-toast";

const RAILWAY = "https://web-production-dcd43.up.railway.app";
const ATHI_LOGO = "https://a-thi.online/wp-content/uploads/2024/01/cropped-a-thi-logo-192x192.png";
const ATHI_NAME = "a-thi.online";
const ATHI_URL = "https://a-thi.online";

type ClearanceMode = "auto" | "manual";
type PreClearanceState = "none" | "pending" | "cleared" | "flagged";

const CARRIERS = [
  { id: "fedex", label: "FedEx", available: true },
  { id: "ups",   label: "UPS",   available: false },
  { id: "msc",   label: "MSC",   available: false },
  { id: "dhl",   label: "DHL",   available: false },
  { id: "maersk",label: "Maersk",available: false },
];

// ─── Merchant user widget ────────────────────────────────────────────────────
interface MerchantUser { name: string; logoUrl: string; siteUrl: string }

const MOCK_MERCHANT: MerchantUser = { name: ATHI_NAME, logoUrl: ATHI_LOGO, siteUrl: ATHI_URL };

// ─── HashPack wallet helper ──────────────────────────────────────────────────
const HASHPACK_EXTENSION_URL = "https://www.hashpack.app/download";

// HashConnect v2 extension injects window.hashconnect
declare global {
  interface Window {
    hashconnect?: {
      init: (appMetadata: object, network: string, debug?: boolean) => Promise<{ topic: string; pairingString: string; savedPairings: { accountIds: string[] }[] }>;
      connectToLocalWallet: (pairingString: string) => void;
      pairingEvent?: { once: (cb: (data: { accountIds: string[] }) => void) => void };
    };
  }
}

async function connectHashPack(): Promise<string | null> {
  // HashConnect v2 — talks to the installed Chrome extension
  if (typeof window !== "undefined" && window.hashconnect) {
    try {
      const appMeta = { name: "TruthForge", description: "Logistics verification platform", icon: "https://truthforge.vercel.app/favicon.ico" };
      const initData = await window.hashconnect.init(appMeta, "testnet", false);
      // If already paired, return first account
      if (initData.savedPairings?.length > 0) {
        const ids = initData.savedPairings[0].accountIds;
        if (ids?.length > 0) return ids[0];
      }
      // Trigger pairing via extension popup
      window.hashconnect.connectToLocalWallet(initData.pairingString);
      // Wait for pairing event (up to 60s)
      return await new Promise<string | null>((resolve) => {
        const timer = setTimeout(() => resolve(null), 60000);
        window.hashconnect?.pairingEvent?.once((data) => {
          clearTimeout(timer);
          resolve(data?.accountIds?.[0] ?? null);
        });
      });
    } catch { return null; }
  }
  return null;
}

// ─── Mock clearance timeline data per shipment ───────────────────────────────
const MOCK_TIMELINES: Record<string, ClearanceStepData> = {
  "SHP-8821A": { order_received: true, carrier_confirmed: true, agents_verified: true, payment_confirmed: true, pre_cleared: true },
  "SHP-8822B": { order_received: true, carrier_confirmed: true, agents_verified: false },
  "SHP-8823C": { order_received: true, carrier_confirmed: true, agents_verified: true, flagged: true },
  "SHP-8824D": { order_received: true, carrier_confirmed: true, agents_verified: true, payment_confirmed: true, pre_cleared: true },
};

// ─── Main component ──────────────────────────────────────────────────────────
const MerchantPortalPage = () => {
  const { isMockMode } = useMockMode();
  const { toast } = useToast();

  // Merchant auth
  const [merchant, setMerchant] = useState<MerchantUser | null>(null);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);

  // Wallet
  const [walletAddress, setWalletAddress] = useState<string | null>(null);
  const [walletModalOpen, setWalletModalOpen] = useState(false);
  const [walletConnecting, setWalletConnecting] = useState(false);

  // Carrier / pre-clearance
  const [selectedCarrier, setSelectedCarrier] = useState("fedex");
  const [carrierDropdownOpen, setCarrierDropdownOpen] = useState(false);
  const [clearanceMode, setClearanceMode] = useState<ClearanceMode>("auto");
  const [preClearanceStates, setPreClearanceStates] = useState<Record<string, PreClearanceState>>({});
  const [pendingConfirm, setPendingConfirm] = useState<string | null>(null);
  const [receiptModal, setReceiptModal] = useState<string | null>(null);

  // Live carrier status
  const [carrierStatus, setCarrierStatus] = useState<"connected" | "disconnected" | "loading">("loading");
  const [liveShipments, setLiveShipments] = useState<ShipmentTracking[]>([]);
  const [shipmentsLoading, setShipmentsLoading] = useState(false);

  const selectedCarrierLabel = CARRIERS.find(c => c.id === selectedCarrier)?.label ?? "FedEx";

  // ── Load persisted merchant/wallet ──
  useEffect(() => {
    const stored = localStorage.getItem("tf_merchant");
    if (stored) { try { setMerchant(JSON.parse(stored)); } catch { localStorage.removeItem("tf_merchant"); } }
    const storedWallet = localStorage.getItem("tf_wallet_address");
    if (storedWallet) setWalletAddress(storedWallet);
  }, []);

  // ── Mock: seed merchant on mount ──
  useEffect(() => {
    if (isMockMode && !merchant) {
      setMerchant(MOCK_MERCHANT);
      localStorage.setItem("tf_merchant", JSON.stringify(MOCK_MERCHANT));
    }
  }, [isMockMode, merchant]);

  // ── Live carrier status check ──
  const checkCarrierStatus = useCallback(async () => {
    if (isMockMode) { setCarrierStatus("connected"); return; }
    try {
      const res = await fetch(`${RAILWAY}/api/carrier/status?carrier=${selectedCarrier}`, { signal: AbortSignal.timeout(6000) });
      setCarrierStatus(res.ok ? "connected" : "disconnected");
    } catch { setCarrierStatus("disconnected"); }
  }, [isMockMode, selectedCarrier]);

  // ── Live shipments fetch ──
  const fetchLiveShipments = useCallback(async () => {
    if (isMockMode) return;
    setShipmentsLoading(true);
    try {
      const res = await fetch(`${RAILWAY}/api/clearance/queue`, { signal: AbortSignal.timeout(8000) });
      if (res.ok) {
        const data = await res.json();
        setLiveShipments(data.shipments ?? []);
      }
    } catch { /* keep empty */ }
    finally { setShipmentsLoading(false); }
  }, [isMockMode]);

  useEffect(() => {
    checkCarrierStatus();
    if (!isMockMode) fetchLiveShipments();
  }, [isMockMode, checkCarrierStatus, fetchLiveShipments]);

  const shipments = isMockMode ? mockShipments : liveShipments;

  // ── Auth ──
  const handleSignIn = async () => {
    setAuthLoading(true);
    try {
      const res = await fetch(`${RAILWAY}/api/merchant/auth`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ site: ATHI_URL }),
        signal: AbortSignal.timeout(8000),
      });
      const data = res.ok ? await res.json() : null;
      const m: MerchantUser = data?.merchant ?? MOCK_MERCHANT;
      setMerchant(m);
      localStorage.setItem("tf_merchant", JSON.stringify(m));
      toast({ title: "Signed in", description: `Welcome, ${m.name}` });
    } catch {
      // fallback: use known merchant
      setMerchant(MOCK_MERCHANT);
      localStorage.setItem("tf_merchant", JSON.stringify(MOCK_MERCHANT));
      toast({ title: "Signed in", description: `Welcome, ${MOCK_MERCHANT.name}` });
    }
    setAuthLoading(false);
  };

  const handleSignOut = async () => {
    setUserMenuOpen(false);
    try { await fetch(`${RAILWAY}/api/merchant/logout`, { method: "POST", signal: AbortSignal.timeout(4000) }); } catch { /* ignore */ }
    setMerchant(null);
    localStorage.removeItem("tf_merchant");
    toast({ title: "Signed out" });
  };

  // ── Wallet ──
  const handleConnectWallet = async () => {
    // If extension not present at all, open download page immediately
    if (typeof window !== "undefined" && !window.hashconnect) {
      window.open(HASHPACK_EXTENSION_URL, "_blank");
      return;
    }
    setWalletConnecting(true);
    const addr = await connectHashPack();
    if (addr) {
      setWalletAddress(addr);
      localStorage.setItem("tf_wallet_address", addr);
      setWalletModalOpen(false);
      toast({ title: "Wallet connected", description: addr });
    } else {
      toast({ title: "Connection timed out", description: "Please approve the pairing request in HashPack.", variant: "destructive" });
    }
    setWalletConnecting(false);
  };

  const handleDisconnectWallet = () => {
    setWalletAddress(null);
    localStorage.removeItem("tf_wallet_address");
    toast({ title: "Wallet disconnected" });
  };

  // ── Pre-clearance ──
  const getShipmentState = (id: string): PreClearanceState =>
    preClearanceStates[id] ?? (mockPortTrustReceipts.find(r => r.shipmentId === id) ? "cleared" : "none");

  const requestPreClearance = async (shipment: ShipmentTracking) => {
    if (!walletAddress) { setWalletModalOpen(true); return; }
    if (clearanceMode === "manual" && pendingConfirm !== shipment.id) { setPendingConfirm(shipment.id); return; }
    setPendingConfirm(null);
    setPreClearanceStates(s => ({ ...s, [shipment.id]: "pending" }));

    if (isMockMode) {
      await new Promise(r => setTimeout(r, 1200));
      setPreClearanceStates(s => ({ ...s, [shipment.id]: "cleared" }));
      toast({ title: "Pre-Clearance Approved", description: `${shipment.id} has been pre-cleared on Hedera.` });
    } else {
      try {
        const res = await fetch(`${RAILWAY}/api/v1/shipments/${shipment.id}/pre-clearance`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ carrier: selectedCarrier, wallet: walletAddress, mode: clearanceMode }),
          signal: AbortSignal.timeout(10000),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setPreClearanceStates(s => ({ ...s, [shipment.id]: "cleared" }));
        toast({ title: "Pre-Clearance Approved", description: `${shipment.id} pre-cleared via live backend.` });
      } catch {
        setPreClearanceStates(s => ({ ...s, [shipment.id]: "flagged" }));
        toast({ title: "Pre-Clearance Failed", description: "Backend returned an error.", variant: "destructive" });
      }
    }
  };

  const receiptForShipment = (id: string) => mockPortTrustReceipts.find(r => r.shipmentId === id);

  const getTimeline = (id: string): ClearanceStepData => {
    if (isMockMode) return MOCK_TIMELINES[id] ?? {};
    const state = getShipmentState(id);
    return {
      order_received: true,
      carrier_confirmed: carrierStatus === "connected",
      agents_verified: state === "cleared",
      payment_confirmed: state === "cleared",
      pre_cleared: state === "cleared",
      flagged: state === "flagged",
    };
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* ── Page Header ── */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
            <Package className="h-5 w-5 text-accent" />
            Merchant Portal
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage shipments, request pre-clearance, and track carrier status.
          </p>
          <div className={`inline-flex items-center gap-1.5 mt-2 px-2.5 py-1 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${
            isMockMode ? "border-warning/40 bg-warning/10 text-warning" : "border-success/40 bg-success/10 text-success"
          }`}>
            {isMockMode ? "Preview Mode" : "Live Mode"}
          </div>
        </div>

        {/* ── Merchant User Widget ── */}
        <div className="relative">
          {merchant ? (
            <>
              <button
                onClick={() => setUserMenuOpen(o => !o)}
                className="flex items-center gap-2 px-3 py-2 rounded-xl border border-border bg-card hover:border-accent/40 transition-colors"
              >
                <img
                  src={merchant.logoUrl}
                  alt={merchant.name}
                  className="h-7 w-7 rounded-full object-cover border border-border"
                  onError={e => { (e.target as HTMLImageElement).src = "https://placehold.co/28x28/1e3a5f/ffffff?text=M"; }}
                />
                <div className="text-left">
                  <div className="text-[10px] font-heading font-bold text-foreground leading-none">{merchant.name}</div>
                  <div className="text-[9px] text-muted-foreground mt-0.5">Merchant</div>
                </div>
                <ChevronDown className={`h-3 w-3 text-muted-foreground transition-transform ${userMenuOpen ? "rotate-180" : ""}`} />
              </button>
              {userMenuOpen && (
                <div className="absolute right-0 top-full mt-1 w-44 rounded-lg border border-border bg-card shadow-elevated z-30 py-1">
                  <a href={merchant.siteUrl} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-2 px-3 py-2 text-xs text-foreground hover:bg-secondary transition-colors">
                    <ExternalLink className="h-3.5 w-3.5 text-accent" /> Visit Store
                  </a>
                  <button onClick={handleSignOut}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-destructive hover:bg-destructive/10 transition-colors">
                    <LogOut className="h-3.5 w-3.5" /> Sign Out
                  </button>
                </div>
              )}
            </>
          ) : (
            <button
              onClick={handleSignIn}
              disabled={authLoading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-accent bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-50"
            >
              <LogIn className="h-3.5 w-3.5" />
              {authLoading ? "Signing in..." : "Sign In"}
            </button>
          )}
        </div>
      </div>

      {/* ── Controls Row: Carrier Card + Pre-Clearance Toggle ── */}
      <div className="flex flex-wrap items-stretch gap-3">
        {/* Carrier Card */}
        <div className="rounded-xl border border-[hsl(213_50%_22%)] bg-[hsl(213_40%_14%)] p-4 flex flex-col gap-2 min-w-[200px]">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-heading font-bold text-white/60 uppercase tracking-wider">Connected Carrier</span>
            <span className={`h-2 w-2 rounded-full ${carrierStatus === "connected" ? "bg-success" : carrierStatus === "loading" ? "bg-warning animate-pulse" : "bg-destructive"}`} />
          </div>
          <div className="relative">
            <button
              onClick={() => setCarrierDropdownOpen(o => !o)}
              className="flex items-center gap-2 w-full px-3 py-2 rounded-lg border border-[hsl(213_40%_28%)] bg-[hsl(213_40%_18%)] text-sm font-medium text-white hover:border-accent/40 transition-colors"
            >
              <Package className="h-4 w-4 text-accent" />
              {selectedCarrierLabel}
              <ChevronDown className={`h-3.5 w-3.5 ml-auto text-white/60 transition-transform ${carrierDropdownOpen ? "rotate-180" : ""}`} />
            </button>
            {carrierDropdownOpen && (
              <div className="absolute top-full left-0 mt-1 w-full rounded-lg border border-border bg-card shadow-elevated z-20 py-1">
                {CARRIERS.map(c => (
                  <button key={c.id} disabled={!c.available}
                    onClick={() => { if (c.available) { setSelectedCarrier(c.id); setCarrierDropdownOpen(false); } }}
                    className={`w-full flex items-center justify-between px-3 py-2 text-xs transition-colors ${
                      !c.available ? "text-muted-foreground/40 cursor-not-allowed"
                        : selectedCarrier === c.id ? "bg-primary/10 text-primary font-medium"
                        : "text-foreground hover:bg-secondary"
                    }`}
                  >
                    {c.label}
                    {!c.available && <span className="text-[9px] border border-muted text-muted-foreground px-1.5 py-0.5 rounded uppercase tracking-wider">Soon</span>}
                    {c.available && selectedCarrier === c.id && <CheckCircle className="h-3.5 w-3.5 text-success" />}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`text-[10px] font-medium ${carrierStatus === "connected" ? "text-success" : "text-white/50"}`}>
              {carrierStatus === "connected" ? "Live feed active" : carrierStatus === "loading" ? "Connecting..." : "Disconnected"}
            </span>
            <button onClick={checkCarrierStatus} className="ml-auto text-white/40 hover:text-white transition-colors">
              <RefreshCw className="h-3 w-3" />
            </button>
          </div>
        </div>

        {/* Pre-Clearance Toggle Card */}
        <div className="rounded-xl border border-[hsl(213_50%_22%)] bg-[hsl(213_40%_14%)] p-4 flex flex-col gap-2 min-w-[200px]">
          <span className="text-[10px] font-heading font-bold text-white/60 uppercase tracking-wider">Pre-Clearance Mode</span>
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-accent" />
            <button
              onClick={() => setClearanceMode(m => m === "auto" ? "manual" : "auto")}
              className="flex items-center gap-2 text-sm font-heading font-bold"
            >
              {clearanceMode === "auto" ? (
                <><ToggleRight className="h-5 w-5 text-success" /><span className="text-success">Auto</span></>
              ) : (
                <><ToggleLeft className="h-5 w-5 text-warning" /><span className="text-warning">Manual</span></>
              )}
            </button>
          </div>
          <p className="text-[10px] text-white/60 leading-snug">
            {clearanceMode === "auto"
              ? "Shipments auto-submit to backend when ready."
              : "Each request requires your confirmation."}
          </p>
        </div>

        {/* Wallet Card */}
        <div className="rounded-xl border border-[hsl(213_50%_22%)] bg-[hsl(213_40%_14%)] p-4 flex flex-col gap-2 min-w-[200px]">
          <span className="text-[10px] font-heading font-bold text-white/60 uppercase tracking-wider">HashPack Wallet</span>
          {walletAddress ? (
            <>
              <div className="flex items-center gap-2">
                <Wallet className="h-4 w-4 text-success" />
                <span className="font-mono text-xs text-success truncate">{walletAddress}</span>
              </div>
              <button onClick={handleDisconnectWallet} className="text-[10px] text-white/40 hover:text-destructive transition-colors text-left">
                Disconnect wallet
              </button>
            </>
          ) : (
            <>
              <div className="flex items-center gap-2 text-white/60">
                <Wallet className="h-4 w-4" />
                <span className="text-xs text-white">No wallet connected</span>
              </div>
              <button
                onClick={() => setWalletModalOpen(true)}
                className="px-3 py-1.5 rounded border border-accent bg-accent/10 text-accent text-[10px] font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors"
              >
                Connect Wallet
              </button>
              <p className="text-[9px] text-warning leading-snug">Required to request pre-clearance</p>
            </>
          )}
        </div>
      </div>

      {/* Manual mode hint */}
      {clearanceMode === "manual" && (
        <div className="rounded border border-warning/30 bg-warning/5 px-4 py-2 text-xs text-warning font-medium flex items-center gap-2">
          <Zap className="h-3.5 w-3.5" />
          Manual mode: each pre-clearance requires your confirmation before submitting.
        </div>
      )}

      {/* ── Shipment Cards ── */}
      <div className="space-y-3">
        {shipmentsLoading && (
          <div className="py-8 text-center text-muted-foreground text-sm animate-pulse">Loading live shipments...</div>
        )}
        {!shipmentsLoading && shipments.length === 0 && !isMockMode && (
          <div className="py-8 text-center text-muted-foreground text-sm">No live shipments yet.</div>
        )}
        {shipments.map(shipment => {
          const state = getShipmentState(shipment.id);
          const receipt = receiptForShipment(shipment.id);
          const isCleared = state === "cleared";
          const isPending = state === "pending";
          const isFlagged = state === "flagged";
          const awaitingConfirm = pendingConfirm === shipment.id;
          const timeline = getTimeline(shipment.id);

          return (
            <div key={shipment.id} className="rounded-xl border border-border bg-card p-5 shadow-card hover:shadow-elevated transition-all">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-sm font-bold text-foreground">{shipment.id}</span>
                    {isCleared && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-success/30 bg-success/10 text-success text-[10px] font-heading font-bold uppercase tracking-wider">
                        <CheckCircle className="h-2.5 w-2.5" /> Pre-Cleared
                      </span>
                    )}
                    {isPending && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-warning/30 bg-warning/10 text-warning text-[10px] font-heading font-bold uppercase tracking-wider">
                        <Clock className="h-2.5 w-2.5" /> Processing...
                      </span>
                    )}
                    {isFlagged && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-destructive/30 bg-destructive/10 text-destructive text-[10px] font-heading font-bold uppercase tracking-wider">
                        <AlertTriangle className="h-2.5 w-2.5" /> Flagged
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {shipment.carrier} · {shipment.origin} → {shipment.destination} · ETA {shipment.eta}
                  </div>
                  {shipment.containerCount && (
                    <div className="text-xs text-muted-foreground">
                      {shipment.containerCount} containers · {shipment.verifiedContainers} verified · {shipment.flaggedContainers} flagged
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  {isCleared && receipt && (
                    <button onClick={() => setReceiptModal(shipment.id)}
                      className="px-3 py-1.5 rounded border border-accent/30 bg-accent/10 text-accent text-xs font-medium hover:bg-accent/20 transition-colors">
                      View Receipt
                    </button>
                  )}
                  {awaitingConfirm && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-warning font-medium">Confirm?</span>
                      <button onClick={() => requestPreClearance(shipment)}
                        className="px-3 py-1.5 rounded border border-success/40 bg-success/10 text-success text-xs font-medium hover:bg-success/20 transition-colors">
                        Yes, Submit
                      </button>
                      <button onClick={() => setPendingConfirm(null)}
                        className="px-3 py-1.5 rounded border border-border text-xs text-muted-foreground hover:bg-secondary transition-colors">
                        Cancel
                      </button>
                    </div>
                  )}
                  {!awaitingConfirm && (
                    <button disabled={isCleared || isPending} onClick={() => requestPreClearance(shipment)}
                      className="px-3 py-1.5 rounded border border-accent bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
                      {isPending ? "Processing..." : isCleared ? "Pre-Cleared" : "Request Pre-Clearance"}
                    </button>
                  )}
                </div>
              </div>

              {/* Order Clearance Timeline */}
              <OrderClearanceTimeline data={timeline} />
            </div>
          );
        })}
      </div>

      {/* ── Receipt Modal ── */}
      {receiptModal && (() => {
        const receipt = receiptForShipment(receiptModal);
        if (!receipt) return null;
        return (
          <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setReceiptModal(null)}>
            <div className="bg-card border border-border rounded-xl max-w-lg w-full max-h-[85vh] overflow-y-auto shadow-elevated" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between p-4 border-b border-border">
                <h3 className="font-heading font-bold text-foreground text-sm">Port Trust Receipt – {receipt.shipmentId}</h3>
                <button onClick={() => setReceiptModal(null)} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
              </div>
              <div className="p-4">
                <PortTrustReceipt receipt={receipt} verificationType="merchant" />
              </div>
            </div>
          </div>
        );
      })()}

      {/* ── HashPack Wallet Modal ── */}
      {walletModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setWalletModalOpen(false)}>
          <div className="bg-card border border-border rounded-xl max-w-sm w-full shadow-elevated p-6 space-y-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-heading font-bold text-foreground text-sm flex items-center gap-2">
                <Wallet className="h-4 w-4 text-accent" /> Connect HashPack Wallet
              </h3>
              <button onClick={() => setWalletModalOpen(false)} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
            </div>
            <p className="text-xs text-muted-foreground">
              A HashPack wallet is required to sign and pay for pre-clearance requests on the Hedera network.
            </p>
            <button
              onClick={handleConnectWallet}
              disabled={walletConnecting}
              className="w-full py-3 rounded-lg border border-accent bg-accent/10 text-accent text-sm font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Wallet className="h-4 w-4" />
              {walletConnecting ? "Connecting..." : "Connect HashPack"}
            </button>
            <p className="text-[10px] text-muted-foreground text-center">
              Don't have HashPack?{" "}
              <a href={HASHPACK_EXTENSION_URL} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
                Download extension
              </a>
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MerchantPortalPage;
