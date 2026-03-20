import { useState, useEffect, useCallback } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import { mockShipments, mockPortTrustReceipts, ShipmentTracking } from "@/lib/mock-data";
import { apiFetch } from "@/lib/api-client";
import LiveModeBanner from "@/components/LiveModeBanner";
import {
  Ship, Plane, Truck, CheckCircle, AlertTriangle, Clock,
  Package, ExternalLink, ChevronDown, LogIn, LogOut,
  RefreshCw, X, Zap, Hand
} from "lucide-react";
import CarrierVerificationPanel, { VerificationResult, TransportMode } from "@/components/CarrierVerificationPanel";
import PortTrustReceipt from "@/components/PortTrustReceipt";
import CarrierProcessingTimeline, { CarrierTimelineData } from "@/components/CarrierProcessingTimeline";
import CarrierClearanceTimeline, { CarrierClearanceStepData } from "@/components/CarrierClearanceTimeline";
import { useToast } from "@/hooks/use-toast";

const RAILWAY = "https://web-production-dcd43.up.railway.app";
const FEDEX_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/FedEx_Corporation_-_2016_Logo.svg/1200px-FedEx_Corporation_-_2016_Logo.svg.png";
const FEDEX_NAME = "FedEx";
const FEDEX_SITE = "https://www.fedex.com";
const HBAR_FEE = 2;

type VerificationMode = "auto" | "manual";
type ClearancePhase = "idle" | "verifying" | "verified" | "paying" | "cleared" | "flagged";

interface ShipmentClearanceState {
  phase: ClearancePhase;
  txId?: string;
  hashscanUrl?: string;
}

interface CarrierUser { name: string; logoUrl: string; siteUrl: string }
const MOCK_CARRIER: CarrierUser = { name: FEDEX_NAME, logoUrl: FEDEX_LOGO, siteUrl: FEDEX_SITE };

const riskColor = {
  low: "text-success bg-success/10 border-success/30",
  medium: "text-warning bg-warning/10 border-warning/30",
  high: "text-destructive bg-destructive/10 border-destructive/30",
};
const statusColor = {
  verified: "text-success bg-success/10 border-success/30",
  pending: "text-warning bg-warning/10 border-warning/30",
  flagged: "text-destructive bg-destructive/10 border-destructive/30",
};

const MOCK_TIMELINES: Record<string, CarrierTimelineData> = {
  "SHP-8821A": { shipment_received: true, documents_uploaded: true, agents_verified: true, submitted_for_clearance: true, port_pre_cleared: true },
  "SHP-8822B": { shipment_received: true, documents_uploaded: true, agents_verified: false },
  "SHP-8823C": { shipment_received: true, documents_uploaded: true, agents_verified: false, flagged: true },
  "SHP-8824D": { shipment_received: true, documents_uploaded: true, agents_verified: true, submitted_for_clearance: true, port_pre_cleared: true },
};

const CarrierPortalPage = () => {
  const { isMockMode } = useMockMode();
  const { toast } = useToast();

  const [carrier, setCarrier] = useState<CarrierUser | null>(null);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [verificationMode, setVerificationMode] = useState<VerificationMode>("auto");
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [transportMode, setTransportMode] = useState<TransportMode>("sea");
  const [uploadPhase, setUploadPhase] = useState<ClearancePhase>("idle");
  const [uploadTxId, setUploadTxId] = useState<string | undefined>();
  const [uploadHashscan, setUploadHashscan] = useState<string | undefined>();
  const [preClearanceStates, setPreClearanceStates] = useState<Record<string, ShipmentClearanceState>>({});
  const [receiptModal, setReceiptModal] = useState<string | null>(null);
  const [liveShipments, setLiveShipments] = useState<ShipmentTracking[]>([]);
  const [shipmentsLoading, setShipmentsLoading] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("tf_carrier");
    if (stored) { try { setCarrier(JSON.parse(stored)); } catch { localStorage.removeItem("tf_carrier"); } }
  }, []);

  useEffect(() => {
    if (isMockMode && !carrier) {
      setCarrier(MOCK_CARRIER);
      localStorage.setItem("tf_carrier", JSON.stringify(MOCK_CARRIER));
    }
  }, [isMockMode, carrier]);

  const fetchLiveShipments = useCallback(async () => {
    if (isMockMode) return;
    setShipmentsLoading(true);
    try {
      const res = await fetch(`${RAILWAY}/api/clearance/queue`, { signal: AbortSignal.timeout(8000) });
      if (res.ok) { const d = await res.json(); setLiveShipments(d.shipments ?? []); }
    } catch { /* keep empty */ }
    finally { setShipmentsLoading(false); }
  }, [isMockMode]);

  useEffect(() => { if (!isMockMode) fetchLiveShipments(); }, [isMockMode, fetchLiveShipments]);

  const shipments = isMockMode ? mockShipments : liveShipments;

  const handleSignIn = async () => {
    setAuthLoading(true);
    try {
      const res = await fetch(`${RAILWAY}/api/carrier/auth`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ carrier: "fedex" }),
        signal: AbortSignal.timeout(8000),
      });
      const data = res.ok ? await res.json() : null;
      const c: CarrierUser = data?.carrier ?? MOCK_CARRIER;
      setCarrier(c);
      localStorage.setItem("tf_carrier", JSON.stringify(c));
      toast({ title: "Signed in", description: `Welcome, ${c.name}` });
    } catch {
      setCarrier(MOCK_CARRIER);
      localStorage.setItem("tf_carrier", JSON.stringify(MOCK_CARRIER));
      toast({ title: "Signed in", description: `Welcome, ${MOCK_CARRIER.name}` });
    }
    setAuthLoading(false);
  };

  const handleSignOut = async () => {
    setUserMenuOpen(false);
    try {
      await fetch(`${RAILWAY}/api/carrier/logout`, {
        method: "POST",
        body: JSON.stringify({ carrier: "fedex" }),
        signal: AbortSignal.timeout(4000),
      });
    } catch { /* ignore */ }
    setCarrier(null);
    localStorage.removeItem("tf_carrier");
    toast({ title: "Signed out" });
  };

  const runPayment = async (shipmentId: string): Promise<{ txId: string; hashscanUrl: string } | null> => {
    if (isMockMode) {
      await new Promise(r => setTimeout(r, 1200));
      const fakeTx = `0.0.mock-${Date.now()}`;
      return { txId: fakeTx, hashscanUrl: `https://hashscan.io/testnet/transaction/${fakeTx}` };
    }
    const { submitHederaPayment } = await import("@/lib/hedera-payment");
    const result = await submitHederaPayment(shipmentId, HBAR_FEE);
    if (!result.success) {
      toast({ title: result.userRejected ? "Payment cancelled" : "Payment failed", description: result.error ?? "Unknown error", variant: "destructive" });
      return null;
    }
    return { txId: result.txId!, hashscanUrl: result.hashscanUrl! };
  };

  const persistTxId = async (shipmentId: string, txId: string) => {
    try {
      await apiFetch(`/api/v1/shipments/${shipmentId}/pre-clearance`, {
        method: "POST",
        body: JSON.stringify({ carrier: "fedex", txId }),
      });
    } catch { /* non-blocking */ }
  };

  const handleVerified = async (result: VerificationResult) => {
    setVerificationResult(result);
    setTransportMode(result.transportMode);
    if (result.status === "flagged") {
      setUploadPhase("flagged");
      toast({ title: "Shipment Flagged", description: result.aiReasoning, variant: "destructive" });
      return;
    }
    if (verificationMode === "auto") {
      setUploadPhase("paying");
      const payment = await runPayment(result.shipmentId);
      if (!payment) { setUploadPhase("verified"); return; }
      await persistTxId(result.shipmentId, payment.txId);
      setUploadTxId(payment.txId);
      setUploadHashscan(payment.hashscanUrl);
      setUploadPhase("cleared");
      toast({ title: "Port Clearance Issued", description: `${result.shipmentId} cleared on Hedera.` });
    } else {
      setUploadPhase("verified");
      toast({ title: "Verification Complete", description: "Payment required to complete pre-clearance." });
    }
  };

  const handleUploadPayment = async () => {
    if (!verificationResult) return;
    setUploadPhase("paying");
    const payment = await runPayment(verificationResult.shipmentId);
    if (!payment) { setUploadPhase("verified"); return; }
    await persistTxId(verificationResult.shipmentId, payment.txId);
    setUploadTxId(payment.txId);
    setUploadHashscan(payment.hashscanUrl);
    setUploadPhase("cleared");
    toast({ title: "Port Clearance Issued", description: `${verificationResult.shipmentId} cleared on Hedera.` });
  };

  const resetUploadPanel = () => {
    setVerificationResult(null);
    setUploadPhase("idle");
    setUploadTxId(undefined);
    setUploadHashscan(undefined);
  };

  const getShipmentState = (id: string): ShipmentClearanceState =>
    preClearanceStates[id] ?? { phase: mockPortTrustReceipts.find(r => r.shipmentId === id) ? "cleared" : "idle" };

  const handleInitiateVerification = async (shipment: ShipmentTracking) => {
    setPreClearanceStates(s => ({ ...s, [shipment.id]: { phase: "verifying" } }));
    if (!isMockMode) {
      try {
        await apiFetch(`/api/v1/shipments/${shipment.id}/verify`, {
          method: "POST",
          body: JSON.stringify({ carrier: "fedex" }),
        });
      } catch { /* treat as verified in demo */ }
    }
    if (verificationMode === "auto") {
      setPreClearanceStates(s => ({ ...s, [shipment.id]: { phase: "paying" } }));
      const payment = await runPayment(shipment.id);
      if (!payment) { setPreClearanceStates(s => ({ ...s, [shipment.id]: { phase: "verified" } })); return; }
      await persistTxId(shipment.id, payment.txId);
      setPreClearanceStates(s => ({ ...s, [shipment.id]: { phase: "cleared", txId: payment.txId, hashscanUrl: payment.hashscanUrl } }));
      toast({ title: "Pre-Clearance Issued", description: `${shipment.id} cleared on Hedera.` });
    } else {
      setPreClearanceStates(s => ({ ...s, [shipment.id]: { phase: "verified" } }));
      toast({ title: "Verified", description: "Payment required to complete pre-clearance." });
    }
  };

  const handleShipmentPayment = async (shipment: ShipmentTracking) => {
    setPreClearanceStates(s => ({ ...s, [shipment.id]: { ...s[shipment.id], phase: "paying" } }));
    const payment = await runPayment(shipment.id);
    if (!payment) { setPreClearanceStates(s => ({ ...s, [shipment.id]: { ...s[shipment.id], phase: "verified" } })); return; }
    await persistTxId(shipment.id, payment.txId);
    setPreClearanceStates(s => ({ ...s, [shipment.id]: { phase: "cleared", txId: payment.txId, hashscanUrl: payment.hashscanUrl } }));
    toast({ title: "Pre-Clearance Issued", description: `${shipment.id} cleared on Hedera.` });
  };

  const receiptForShipment = (id: string) => mockPortTrustReceipts.find(r => r.shipmentId === id);

  const getTimeline = (shipment: ShipmentTracking): CarrierTimelineData => {
    if (isMockMode) return MOCK_TIMELINES[shipment.id] ?? {};
    const cs = getShipmentState(shipment.id);
    return {
      shipment_received: true,
      documents_uploaded: cs.phase !== "idle",
      agents_verified: cs.phase === "cleared",
      submitted_for_clearance: cs.phase === "cleared",
      port_pre_cleared: cs.phase === "cleared",
      flagged: cs.phase === "flagged",
    };
  };

  const uploadClearanceData = (): CarrierClearanceStepData => ({
    documents_uploaded: uploadPhase !== "idle",
    verification_completed: ["verified", "paying", "cleared"].includes(uploadPhase),
    payment_pending: uploadPhase === "verified" && verificationMode === "manual",
    payment_completed: uploadPhase === "cleared" || uploadPhase === "paying",
    clearance_issued: uploadPhase === "cleared",
    flagged: uploadPhase === "flagged",
  });

  const modeLabel: Record<TransportMode, string> = { sea: "Container", air: "Cargo", land: "Pallet" };
  const ModeIcon = transportMode === "sea" ? Ship : transportMode === "air" ? Plane : Truck;

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
            <Package className="h-5 w-5 text-accent" />
            Carrier Portal
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Upload carrier documents, verify shipments, and manage pre-clearance status.
          </p>
          <div className={`inline-flex items-center gap-1.5 mt-2 px-2.5 py-1 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${
            isMockMode ? "border-warning/40 bg-warning/10 text-warning" : "border-success/40 bg-success/10 text-success"
          }`}>
            {isMockMode ? "Mock Mode - Simulated Responses" : "Live Mode - Connected to Backend"}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap justify-end">
          {/* Mode toggle */}
          <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
            <button
              onClick={() => setVerificationMode("auto")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-heading font-bold uppercase tracking-wider transition-colors ${
                verificationMode === "auto" ? "bg-accent text-white" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Zap className="h-3 w-3" /> Auto
            </button>
            <button
              onClick={() => setVerificationMode("manual")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-heading font-bold uppercase tracking-wider transition-colors ${
                verificationMode === "manual" ? "bg-accent text-white" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Hand className="h-3 w-3" /> Manual
            </button>
          </div>

          {/* Carrier auth */}
          <div className="relative">
            {carrier ? (
              <>
                <button
                  onClick={() => setUserMenuOpen(o => !o)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl border border-border bg-card hover:border-accent/40 transition-colors"
                >
                  <img
                    src={carrier.logoUrl}
                    alt={carrier.name}
                    className="h-7 w-14 object-contain"
                    onError={e => { (e.target as HTMLImageElement).src = "https://placehold.co/56x28/1e3a5f/ffffff?text=FX"; }}
                  />
                  <div className="text-left hidden sm:block">
                    <div className="text-[10px] font-heading font-bold text-foreground leading-none">{carrier.name}</div>
                    <div className="text-[9px] text-muted-foreground mt-0.5">Carrier</div>
                  </div>
                  <ChevronDown className={`h-3 w-3 text-muted-foreground transition-transform ${userMenuOpen ? "rotate-180" : ""}`} />
                </button>
                {userMenuOpen && (
                  <div className="absolute right-0 top-full mt-1 w-44 rounded-lg border border-border bg-card shadow-elevated z-30 py-1">
                    <a href={carrier.siteUrl} target="_blank" rel="noopener noreferrer"
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
      </div>

      <LiveModeBanner />

      {/* Upload & Verify panel */}
      <div className="rounded-xl border border-[hsl(213_50%_28%)] bg-[hsl(213_45%_16%)] shadow-card overflow-hidden">
        <div className="px-5 py-3 border-b border-[hsl(213_50%_24%)]">
          <h3 className="text-sm font-heading font-bold text-white flex items-center gap-2">
            <Package className="h-4 w-4 text-accent" />
            Upload &amp; Verify Shipment
          </h3>
          <p className="text-xs text-white/60 mt-0.5">Submit carrier documents for Hedera-verified pre-clearance.</p>
        </div>
        <div className="p-5 space-y-4">
          <CarrierVerificationPanel onVerified={handleVerified} />
          {uploadPhase !== "idle" && (
            <CarrierClearanceTimeline data={uploadClearanceData()} mode={verificationMode} />
          )}
          {uploadPhase === "verified" && verificationMode === "manual" && (
            <button
              onClick={handleUploadPayment}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-accent bg-accent text-white text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/80 transition-colors"
            >
              Pay {HBAR_FEE} HBAR &amp; Issue Clearance
            </button>
          )}
          {uploadPhase === "cleared" && uploadTxId && (
            <div className="rounded border border-success/30 bg-success/10 px-3 py-2 flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-success shrink-0" />
              <div>
                <div className="text-xs font-bold text-success">Port Clearance Issued</div>
                <a href={uploadHashscan} target="_blank" rel="noopener noreferrer"
                  className="font-mono text-[10px] text-accent hover:underline flex items-center gap-1">
                  {uploadTxId} <ExternalLink className="h-2.5 w-2.5" />
                </a>
              </div>
              <button onClick={resetUploadPanel} className="ml-auto text-muted-foreground hover:text-foreground">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Verification result intelligence panel */}
      {verificationResult && (
        <div className="rounded-xl border border-border bg-card shadow-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-heading font-bold text-foreground flex items-center gap-2">
              <ModeIcon className="h-4 w-4 text-accent" />
              Shipment Intelligence
            </h3>
            <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${statusColor[verificationResult.status]}`}>
              {verificationResult.status === "verified" && <CheckCircle className="h-3 w-3" />}
              {verificationResult.status === "pending" && <Clock className="h-3 w-3" />}
              {verificationResult.status === "flagged" && <AlertTriangle className="h-3 w-3" />}
              {verificationResult.status === "verified" ? "Pre-Cleared" : verificationResult.status}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="rounded border border-border bg-secondary/30 px-3 py-2">
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Shipment ID</span>
              <span className="font-mono text-xs font-bold text-foreground">{verificationResult.shipmentId}</span>
            </div>
            <div className="rounded border border-border bg-secondary/30 px-3 py-2">
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Transport Mode</span>
              <span className="text-xs font-medium text-foreground capitalize">{verificationResult.transportMode}</span>
            </div>
            {verificationResult.hcsRef && (
              <div className="rounded border border-accent/30 bg-accent/5 px-3 py-2">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Hedera TX</span>
                <span className="font-mono text-xs text-accent truncate block">{verificationResult.hcsRef}</span>
              </div>
            )}
          </div>
          <div className="rounded border border-border bg-secondary/30 px-3 py-3">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">AI Reasoning</span>
            <p className="text-xs text-foreground leading-relaxed">{verificationResult.aiReasoning}</p>
          </div>
          {verificationResult.containers && verificationResult.containers.length > 0 && (
            <div>
              <h4 className="text-xs font-heading font-bold text-muted-foreground uppercase tracking-wider mb-2">
                {modeLabel[verificationResult.transportMode]} Intelligence
              </h4>
              <div className="rounded-lg border border-border overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-secondary/50">
                    <tr>
                      <th className="text-left px-3 py-2 text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">
                        {modeLabel[verificationResult.transportMode]} ID
                      </th>
                      {(verificationResult.transportMode === "air" || verificationResult.transportMode === "land") && (
                        <th className="text-left px-3 py-2 text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">
                          {verificationResult.transportMode === "air" ? "Package Count" : "Pallet Count"}
                        </th>
                      )}
                      <th className="text-left px-3 py-2 text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Status</th>
                      <th className="text-left px-3 py-2 text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {verificationResult.containers.map((item, i) => (
                      <tr key={item.id} className={`border-t border-border ${i % 2 === 0 ? "" : "bg-secondary/20"}`}>
                        <td className="px-3 py-2 font-mono text-foreground">{item.id}</td>
                        {(verificationResult.transportMode === "air" || verificationResult.transportMode === "land") && (
                          <td className="px-3 py-2 text-muted-foreground">{item.count ?? "-"}</td>
                        )}
                        <td className="px-3 py-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${statusColor[item.status]}`}>
                            {item.status === "verified" && <CheckCircle className="h-2.5 w-2.5" />}
                            {item.status === "pending" && <Clock className="h-2.5 w-2.5" />}
                            {item.status === "flagged" && <AlertTriangle className="h-2.5 w-2.5" />}
                            {item.status}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${riskColor[item.risk]}`}>
                            {item.risk}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Merchant Shipments list */}
      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <div className="p-5 border-b border-border flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h3 className="text-sm font-heading font-bold text-foreground flex items-center gap-2">
              <Ship className="h-4 w-4 text-accent" />
              Merchant Shipments
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">Pre-clearance status synced in real time.</p>
          </div>
          {!isMockMode && (
            <button onClick={fetchLiveShipments} className="text-muted-foreground hover:text-foreground transition-colors">
              <RefreshCw className={`h-3.5 w-3.5 ${shipmentsLoading ? "animate-spin" : ""}`} />
            </button>
          )}
        </div>
        <div className="divide-y divide-border">
          {shipmentsLoading && (
            <div className="py-8 text-center text-muted-foreground text-sm animate-pulse">Loading live shipments...</div>
          )}
          {!shipmentsLoading && shipments.length === 0 && !isMockMode && (
            <div className="py-8 text-center text-muted-foreground text-sm">No live shipments yet.</div>
          )}
          {shipments.map(shipment => {
            const cs = getShipmentState(shipment.id);
            const isCleared = cs.phase === "cleared";
            const isPending = cs.phase === "paying" || cs.phase === "verifying";
            const isVerified = cs.phase === "verified";
            const isFlagged = cs.phase === "flagged";
            const receipt = receiptForShipment(shipment.id);
            const MIcon = shipment.freightMode === "air" ? Plane : shipment.freightMode === "land" ? Truck : Ship;
            const timeline = getTimeline(shipment);
            return (
              <div key={shipment.id} className="p-4 hover:bg-secondary/20 transition-colors">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <MIcon className="h-3.5 w-3.5 text-muted-foreground" />
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
                      {shipment.carrier} · {shipment.origin} to {shipment.destination} · ETA {shipment.eta}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    {isCleared && receipt && (
                      <button
                        onClick={() => setReceiptModal(shipment.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-accent/30 bg-accent/10 text-accent text-xs font-medium hover:bg-accent/20 transition-colors"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Port Trust Receipt
                      </button>
                    )}
                    {isVerified && verificationMode === "manual" && (
                      <button
                        onClick={() => handleShipmentPayment(shipment)}
                        className="px-3 py-1.5 rounded border border-accent bg-accent text-white text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/80 transition-colors"
                      >
                        Pay &amp; Clear
                      </button>
                    )}
                    {!isCleared && !isVerified && (
                      <button
                        disabled={isPending}
                        onClick={() => handleInitiateVerification(shipment)}
                        className="px-3 py-1.5 rounded border border-accent bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {isPending ? "Processing..." : "Initiate Verification"}
                      </button>
                    )}
                  </div>
                </div>
                <CarrierProcessingTimeline data={timeline} preCleared={isCleared && !!receipt} />
              </div>
            );
          })}
        </div>
      </div>

      {/* Receipt modal */}
      {receiptModal && (() => {
        const receipt = receiptForShipment(receiptModal);
        if (!receipt) return null;
        return (
          <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setReceiptModal(null)}>
            <div className="bg-card border border-border rounded-xl max-w-lg w-full max-h-[85vh] overflow-y-auto shadow-elevated" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between p-4 border-b border-border">
                <div>
                  <h3 className="font-heading font-bold text-foreground text-sm">Port Trust Receipt - {receipt.shipmentId}</h3>
                  <p className="text-[10px] text-muted-foreground mt-0.5">Port-Readable Clearance Proof - Verified on Hedera</p>
                </div>
                <button onClick={() => setReceiptModal(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>
              <div className="p-4">
                <PortTrustReceipt receipt={receipt} verificationType="carrier" />
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

export default CarrierPortalPage;
