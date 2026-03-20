import { useState, useEffect, useCallback } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import { useWallet } from "@/contexts/WalletContext";
import { mockShipments, mockPortTrustReceipts, ShipmentTracking } from "@/lib/mock-data";
import LiveModeBanner from "@/components/LiveModeBanner";
import {
  Package, ChevronDown, CheckCircle, Clock, AlertTriangle,
  Shield, Zap, ToggleLeft, ToggleRight, LogOut, LogIn,
  ExternalLink, RefreshCw, X, CreditCard, Loader2
} from "lucide-react";
import PortTrustReceipt from "@/components/PortTrustReceipt";
import OrderClearanceTimeline, { ClearanceStepData } from "@/components/OrderClearanceTimeline";
import { useToast } from "@/hooks/use-toast";

const RAILWAY = "https://web-production-dcd43.up.railway.app";
const ATHI_LOGO = "https://a-thi.online/wp-content/uploads/2024/01/cropped-a-thi-logo-192x192.png";
const ATHI_NAME = "a-thi.online";
const ATHI_URL = "https://a-thi.online";
const VERIFICATION_FEE_HBAR = 0.24;

type ClearanceMode = "auto" | "manual";

// Per-shipment payment state machine
type PaymentPhase =
  | "idle"           // nothing started
  | "verifying"      // running verification (both modes)
  | "verified"       // manual: verified, awaiting payment click
  | "paying"         // wallet open / tx in flight
  | "cleared"        // fully done
  | "flagged";       // verification or payment failed

interface ShipmentState {
  phase: PaymentPhase;
  txId?: string;
  hcsRef?: string;
  error?: string;
}

interface MerchantUser { name: string; logoUrl: string; siteUrl: string }
const MOCK_MERCHANT: MerchantUser = { name: ATHI_NAME, logoUrl: ATHI_LOGO, siteUrl: ATHI_URL };

const CARRIERS = [
  { id: "fedex",  label: "FedEx",  available: true },
  { id: "ups",    label: "UPS",    available: false },
  { id: "msc",    label: "MSC",    available: false },
  { id: "dhl",    label: "DHL",    available: false },
  { id: "maersk", label: "Maersk", available: false },
];

// ─── Mock helpers ─────────────────────────────────────────────────────────────
const MOCK_TIMELINES: Record<string, ClearanceStepData> = {
  "SHP-8821A": { order_received: true, carrier_confirmed: true, agents_verified: true, payment_confirmed: true, pre_cleared: true },
  "SHP-8822B": { order_received: true, carrier_confirmed: true, agents_verified: false },
  "SHP-8823C": { order_received: true, carrier_confirmed: true, agents_verified: true, flagged: true },
  "SHP-8824D": { order_received: true, carrier_confirmed: true, agents_verified: true, payment_confirmed: true, pre_cleared: true },
};

function buildTimeline(
  shipmentId: string,
  phase: PaymentPhase,
  carrierConnected: boolean,
  isMockMode: boolean,
): ClearanceStepData {
  if (isMockMode) return MOCK_TIMELINES[shipmentId] ?? {};
  return {
    order_received: true,
    carrier_confirmed: carrierConnected,
    agents_verified: phase === "verified" || phase === "paying" || phase === "cleared",
    payment_pending: phase === "verified",   // manual: awaiting payment click
    payment_confirmed: phase === "cleared",
    pre_cleared: phase === "cleared",
    flagged: phase === "flagged",
  };
}

// ─── Component ────────────────────────────────────────────────────────────────
const MerchantPortalPage = () => {
  const { isMockMode } = useMockMode();
  const { wallet, connectWallet } = useWallet();
  const { toast } = useToast();

  const [merchant, setMerchant] = useState<MerchantUser | null>(null);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);

  const [selectedCarrier, setSelectedCarrier] = useState("fedex");
  const [carrierDropdownOpen, setCarrierDropdownOpen] = useState(false);
  const [clearanceMode, setClearanceMode] = useState<ClearanceMode>("auto");

  // Per-shipment state
  const [shipmentStates, setShipmentStates] = useState<Record<string, ShipmentState>>({});

  const [receiptModal, setReceiptModal] = useState<string | null>(null);
  const [carrierStatus, setCarrierStatus] = useState<"connected" | "disconnected" | "loading">("loading");
  const [liveShipments, setLiveShipments] = useState<ShipmentTracking[]>([]);
  const [shipmentsLoading, setShipmentsLoading] = useState(false);

  const selectedCarrierLabel = CARRIERS.find(c => c.id === selectedCarrier)?.label ?? "FedEx";

  const setState = (id: string, patch: Partial<ShipmentState>) =>
    setShipmentStates(prev => ({ ...prev, [id]: { ...(prev[id] ?? { phase: "idle" }), ...patch } }));

  const getState = (id: string): ShipmentState =>
    shipmentStates[id] ?? { phase: mockPortTrustReceipts.find(r => r.shipmentId === id) ? "cleared" : "idle" };

  // ── Persist merchant ──
  useEffect(() => {
    const stored = localStorage.getItem("tf_merchant");
    if (stored) { try { setMerchant(JSON.parse(stored)); } catch { localStorage.removeItem("tf_merchant"); } }
  }, []);

  useEffect(() => {
    if (isMockMode && !merchant) {
      setMerchant(MOCK_MERCHANT);
      localStorage.setItem("tf_merchant", JSON.stringify(MOCK_MERCHANT));
    }
  }, [isMockMode, merchant]);

  const checkCarrierStatus = useCallback(async () => {
    if (isMockMode) { setCarrierStatus("connected"); return; }
    try {
      const res = await fetch(`${RAILWAY}/api/carrier/status?carrier=${selectedCarrier}`, { signal: AbortSignal.timeout(6000) });
      setCarrierStatus(res.ok ? "connected" : "disconnected");
    } catch { setCarrierStatus("disconnected"); }
  }, [isMockMode, selectedCarrier]);

  const fetchLiveShipments = useCallback(async () => {
    if (isMockMode) return;
    setShipmentsLoading(true);
    try {
      const res = await fetch(`${RAILWAY}/api/clearance/queue`, { signal: AbortSignal.timeout(8000) });
      if (res.ok) { const d = await res.json(); setLiveShipments(d.shipments ?? []); }
    } catch { /* keep empty */ }
    finally { setShipmentsLoading(false); }
  }, [isMockMode]);

  useEffect(() => {
    checkCarrierStatus();
    if (!isMockMode) fetchLiveShipments();
  }, [isMockMode, checkCarrierStatus, fetchLiveShipments]);

  const shipments = isMockMode ? mockShipments : liveShipments;
  const receiptForShipment = (id: string) => mockPortTrustReceipts.find(r => r.shipmentId === id);

  // ── Auth ──
  const handleSignIn = async () => {
    setAuthLoading(true);
    try {
      const res = await fetch(`${RAILWAY}/api/merchant/auth`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ site: ATHI_URL }), signal: AbortSignal.timeout(8000),
      });
      const data = res.ok ? await res.json() : null;
      const m: MerchantUser = data?.merchant ?? MOCK_MERCHANT;
      setMerchant(m);
      localStorage.setItem("tf_merchant", JSON.stringify(m));
      toast({ title: "Signed in", description: `Welcome, ${m.name}` });
    } catch {
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

  // ── Step 1: Verification (both modes) ──
  async function runVerification(shipment: ShipmentTracking): Promise<boolean> {
    if (isMockMode) {
      await new Promise(r => setTimeout(r, 1000));
      return shipment.id !== "SHP-8823C"; // SHP-8823C is flagged in mock
    }
    try {
      const res = await fetch(`${RAILWAY}/api/v1/shipments/${shipment.id}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ carrier: selectedCarrier }),
        signal: AbortSignal.timeout(10000),
      });
      return res.ok;
    } catch { return false; }
  }

  // ── Step 2: Payment (explicit user click only) ──
  async function runPayment(shipment: ShipmentTracking): Promise<{ txId?: string; error?: string; userRejected?: boolean }> {
    if (isMockMode) {
      await new Promise(r => setTimeout(r, 1200));
      return { txId: `MOCK-TX-${shipment.id}-${Date.now()}` };
    }
    // In live mode, wallet must be connected first
    if (!wallet?.accountId) {
      toast({ title: "Wallet required", description: "Connect your HashPack wallet to make HBAR payments.", variant: "destructive" });
      connectWallet();
      return { userRejected: true };
    }
    // Dynamic import — only runs on explicit user click, never at module load
    const { submitHederaPayment } = await import("@/lib/hedera-payment");
    return submitHederaPayment(shipment.id, VERIFICATION_FEE_HBAR);
  }

  // ── Step 3: Notify backend of txId ──
  async function notifyBackend(shipmentId: string, txId: string) {
    if (isMockMode) return;
    try {
      await fetch(`${RAILWAY}/api/v1/shipments/${shipmentId}/pre-clearance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ carrier: selectedCarrier, txId }),
        signal: AbortSignal.timeout(10000),
      });
    } catch { /* non-fatal — UI already updated */ }
  }

  // ── AUTO MODE: single click → verify → wallet → clear ──
  const handleAutoPreClearance = async (shipment: ShipmentTracking) => {
    const s = getState(shipment.id);
    if (s.phase === "verifying" || s.phase === "paying" || s.phase === "cleared") return;

    setState(shipment.id, { phase: "verifying" });
    toast({ title: "Verifying shipment...", description: shipment.id });

    const verified = await runVerification(shipment);
    if (!verified) {
      setState(shipment.id, { phase: "flagged", error: "Verification failed" });
      toast({ title: "Verification Failed", description: `${shipment.id} could not be verified.`, variant: "destructive" });
      return;
    }

    // Verification passed — now open wallet (still within the same click handler call stack)
    setState(shipment.id, { phase: "paying" });
    toast({ title: "Verification passed", description: "Opening wallet for payment..." });

    const result = await runPayment(shipment);
    if (!result.txId) {
      if (!result.userRejected) {
        toast({ title: "Payment failed", description: result.error ?? "Unknown error", variant: "destructive" });
      } else {
        toast({ title: "Payment cancelled", description: "You can retry by clicking the button again." });
      }
      // Revert to verified so user can retry payment
      setState(shipment.id, { phase: "verified" });
      return;
    }

    setState(shipment.id, { phase: "cleared", txId: result.txId });
    await notifyBackend(shipment.id, result.txId);
    toast({ title: "Pre-Clearance Complete", description: `${shipment.id} cleared. TX: ${result.txId.slice(0, 24)}...` });
  };

  // ── MANUAL MODE step A: verify only ──
  const handleManualVerify = async (shipment: ShipmentTracking) => {
    const s = getState(shipment.id);
    if (s.phase === "verifying" || s.phase === "paying" || s.phase === "cleared") return;

    setState(shipment.id, { phase: "verifying" });
    toast({ title: "Running verification...", description: shipment.id });

    const verified = await runVerification(shipment);
    if (!verified) {
      setState(shipment.id, { phase: "flagged", error: "Verification failed" });
      toast({ title: "Verification Failed", description: `${shipment.id} flagged.`, variant: "destructive" });
      return;
    }

    setState(shipment.id, { phase: "verified" });
    toast({ title: "Verified", description: `${shipment.id} verified. Click "Complete Payment" to pre-clear.` });
  };

  // ── MANUAL MODE step B: explicit payment click ──
  const handleManualPayment = async (shipment: ShipmentTracking) => {
    const s = getState(shipment.id);
    if (s.phase !== "verified") return;

    setState(shipment.id, { phase: "paying" });

    const result = await runPayment(shipment);
    if (!result.txId) {
      if (!result.userRejected) {
        toast({ title: "Payment failed", description: result.error ?? "Unknown error", variant: "destructive" });
      } else {
        toast({ title: "Payment cancelled", description: "Click 'Complete Payment' to retry." });
      }
      setState(shipment.id, { phase: "verified" }); // allow retry
      return;
    }

    setState(shipment.id, { phase: "cleared", txId: result.txId });
    await notifyBackend(shipment.id, result.txId);
    toast({ title: "Pre-Clearance Complete", description: `${shipment.id} cleared. TX: ${result.txId.slice(0, 24)}...` });
  };

  // ── Render ────────────────────────────────────────────────────────────────
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

        {/* Merchant User Widget */}
        <div className="relative">
          {merchant ? (
            <>
              <button onClick={() => setUserMenuOpen(o => !o)}
                className="flex items-center gap-2 px-3 py-2 rounded-xl border border-border bg-card hover:border-accent/40 transition-colors">
                <img src={merchant.logoUrl} alt={merchant.name}
                  className="h-7 w-7 rounded-full object-cover border border-border"
                  onError={e => { (e.target as HTMLImageElement).src = "https://placehold.co/28x28/1e3a5f/ffffff?text=M"; }} />
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
            <button onClick={handleSignIn} disabled={authLoading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-accent bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-50">
              <LogIn className="h-3.5 w-3.5" />
              {authLoading ? "Signing in..." : "Sign In"}
            </button>
          )}
        </div>
      </div>

      {/* ── Controls Row ── */}
      <LiveModeBanner />
      <div className="flex flex-wrap items-stretch gap-3">
        {/* Carrier Card */}
        <div className="rounded-xl border border-[hsl(213_50%_22%)] bg-[hsl(213_40%_14%)] p-4 flex flex-col gap-2 min-w-[200px]">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-heading font-bold text-white/60 uppercase tracking-wider">Connected Carrier</span>
            <span className={`h-2 w-2 rounded-full ${carrierStatus === "connected" ? "bg-success" : carrierStatus === "loading" ? "bg-warning animate-pulse" : "bg-destructive"}`} />
          </div>
          <div className="relative">
            <button onClick={() => setCarrierDropdownOpen(o => !o)}
              className="flex items-center gap-2 w-full px-3 py-2 rounded-lg border border-[hsl(213_40%_28%)] bg-[hsl(213_40%_18%)] text-sm font-medium text-white hover:border-accent/40 transition-colors">
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
                    }`}>
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

        {/* Pre-Clearance Mode Toggle */}
        <div className="rounded-xl border border-[hsl(213_50%_22%)] bg-[hsl(213_40%_14%)] p-4 flex flex-col gap-2 min-w-[220px]">
          <span className="text-[10px] font-heading font-bold text-white/60 uppercase tracking-wider">Pre-Clearance Mode</span>
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-accent" />
            <button onClick={() => setClearanceMode(m => m === "auto" ? "manual" : "auto")}
              className="flex items-center gap-2 text-sm font-heading font-bold">
              {clearanceMode === "auto"
                ? <><ToggleRight className="h-5 w-5 text-success" /><span className="text-success">Auto Pre-Clearance</span></>
                : <><ToggleLeft className="h-5 w-5 text-warning" /><span className="text-warning">Manual Pre-Clearance</span></>}
            </button>
          </div>
          <p className="text-[10px] text-white/60 leading-snug">
            {clearanceMode === "auto"
              ? "One click: verify + pay + pre-clear automatically."
              : "Two steps: verify first, then confirm payment separately."}
          </p>
        </div>
      </div>

      {/* Manual mode hint */}
      {clearanceMode === "manual" && (
        <div className="rounded border border-warning/30 bg-warning/5 px-4 py-2 text-xs text-warning font-medium flex items-center gap-2">
          <Zap className="h-3.5 w-3.5" />
          Manual mode: verification runs first. A second "Complete Payment" button appears after verification passes.
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
          const s = getState(shipment.id);
          const receipt = receiptForShipment(shipment.id);
          const timeline = buildTimeline(shipment.id, s.phase, carrierStatus === "connected", isMockMode);

          const isIdle      = s.phase === "idle";
          const isVerifying = s.phase === "verifying";
          const isVerified  = s.phase === "verified";
          const isPaying    = s.phase === "paying";
          const isCleared   = s.phase === "cleared";
          const isFlagged   = s.phase === "flagged";

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
                    {(isVerifying || isPaying) && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-warning/30 bg-warning/10 text-warning text-[10px] font-heading font-bold uppercase tracking-wider">
                        <Loader2 className="h-2.5 w-2.5 animate-spin" />
                        {isVerifying ? "Verifying..." : "Processing Payment..."}
                      </span>
                    )}
                    {isVerified && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-primary/30 bg-primary/10 text-primary text-[10px] font-heading font-bold uppercase tracking-wider">
                        <Clock className="h-2.5 w-2.5" /> Verified - Payment Pending
                      </span>
                    )}
                    {isFlagged && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-destructive/30 bg-destructive/10 text-destructive text-[10px] font-heading font-bold uppercase tracking-wider">
                        <AlertTriangle className="h-2.5 w-2.5" /> Flagged
                      </span>
                    )}
                  </div>

                  <div className="text-xs text-muted-foreground">
                    {shipment.carrier} · {shipment.origin} &rarr; {shipment.destination} · ETA {shipment.eta}
                  </div>
                  {shipment.containerCount && (
                    <div className="text-xs text-muted-foreground">
                      {shipment.containerCount} containers · {shipment.verifiedContainers} verified · {shipment.flaggedContainers} flagged
                    </div>
                  )}
                  {isCleared && s.txId && (
                    <div className="text-[10px] text-muted-foreground font-mono mt-0.5">
                      TX: {s.txId.slice(0, 32)}...
                      {!isMockMode && (
                        <a href={`https://hashscan.io/testnet/transaction/${s.txId}`} target="_blank" rel="noopener noreferrer"
                          className="ml-2 text-accent hover:underline inline-flex items-center gap-0.5">
                          HashScan <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      )}
                    </div>
                  )}
                </div>

                {/* Action buttons */}
                <div className="flex items-center gap-2 flex-wrap">
                  {isCleared && receipt && (
                    <button onClick={() => setReceiptModal(shipment.id)}
                      className="px-3 py-1.5 rounded border border-accent/30 bg-accent/10 text-accent text-xs font-medium hover:bg-accent/20 transition-colors">
                      View Receipt
                    </button>
                  )}

                  {/* AUTO mode button */}
                  {clearanceMode === "auto" && !isCleared && (
                    <button
                      disabled={isVerifying || isPaying}
                      onClick={() => handleAutoPreClearance(shipment)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-accent bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {(isVerifying || isPaying) && <Loader2 className="h-3 w-3 animate-spin" />}
                      {isVerifying ? "Verifying..." : isPaying ? "Processing..." : isFlagged ? "Retry" : "Request Pre-Clearance"}
                    </button>
                  )}

                  {/* MANUAL mode: step A */}
                  {clearanceMode === "manual" && (isIdle || isFlagged) && (
                    <button
                      onClick={() => handleManualVerify(shipment)}
                      className="px-3 py-1.5 rounded border border-accent bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors"
                    >
                      {isFlagged ? "Retry Verification" : "Request Pre-Clearance"}
                    </button>
                  )}

                  {/* MANUAL mode: step A in-progress */}
                  {clearanceMode === "manual" && isVerifying && (
                    <button disabled className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-border text-muted-foreground text-xs font-heading font-bold uppercase tracking-wider opacity-50 cursor-not-allowed">
                      <Loader2 className="h-3 w-3 animate-spin" /> Verifying...
                    </button>
                  )}

                  {/* MANUAL mode: step B — explicit payment */}
                  {clearanceMode === "manual" && isVerified && (
                    <button
                      onClick={() => handleManualPayment(shipment)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-success/50 bg-success/10 text-success text-xs font-heading font-bold uppercase tracking-wider hover:bg-success/20 transition-colors"
                    >
                      <CreditCard className="h-3 w-3" />
                      Complete Payment &amp; Pre-Clear
                    </button>
                  )}

                  {/* MANUAL mode: payment in-progress */}
                  {clearanceMode === "manual" && isPaying && (
                    <button disabled className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-border text-muted-foreground text-xs font-heading font-bold uppercase tracking-wider opacity-50 cursor-not-allowed">
                      <Loader2 className="h-3 w-3 animate-spin" /> Processing Payment...
                    </button>
                  )}
                </div>
              </div>

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
                <h3 className="font-heading font-bold text-foreground text-sm">Port Trust Receipt - {receipt.shipmentId}</h3>
                <button onClick={() => setReceiptModal(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>
              <div className="p-4">
                <PortTrustReceipt receipt={receipt} verificationType="merchant" />
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

export default MerchantPortalPage;
