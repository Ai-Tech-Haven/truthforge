import { useState, useEffect, useCallback } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import { mockShipments, mockPortTrustReceipts, ShipmentTracking } from "@/lib/mock-data";
import { apiFetch } from "@/lib/api-client";
import LiveModeBanner from "@/components/LiveModeBanner";
import {
  Ship, Plane, Truck, CheckCircle, AlertTriangle, Clock,
  Package, ExternalLink, ChevronDown, LogIn, LogOut,
  RefreshCw, X
} from "lucide-react";
import CarrierVerificationPanel, { VerificationResult, TransportMode } from "@/components/CarrierVerificationPanel";
import PortTrustReceipt from "@/components/PortTrustReceipt";
import CarrierProcessingTimeline, { CarrierTimelineData } from "@/components/CarrierProcessingTimeline";
import { useToast } from "@/hooks/use-toast";

// ─── Constants ───────────────────────────────────────────────────────────────
const RAILWAY = "https://web-production-dcd43.up.railway.app";
const FEDEX_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/FedEx_Corporation_-_2016_Logo.svg/1200px-FedEx_Corporation_-_2016_Logo.svg.png";
const FEDEX_NAME = "FedEx";
const FEDEX_SITE = "https://www.fedex.com";

// ─── Types ────────────────────────────────────────────────────────────────────
type PreClearanceState = "none" | "pending" | "cleared" | "flagged";
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

  const [transportMode, setTransportMode] = useState<TransportMode>("sea");
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [preClearanceStates, setPreClearanceStates] = useState<Record<string, PreClearanceState>>({});
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

  const getShipmentState = (id: string): PreClearanceState =>
    preClearanceStates[id] ?? (mockPortTrustReceipts.find(r => r.shipmentId === id) ? "cleared" : "none");

  const handlePreClearance = async (shipment: ShipmentTracking) => {
    setPreClearanceStates(s => ({ ...s, [shipment.id]: "pending" }));
    if (isMockMode) {
      await new Promise(r => setTimeout(r, 1200));
      setPreClearanceStates(s => ({ ...s, [shipment.id]: "cleared" }));
      toast({ title: "Pre-Clearance Issued", description: `${shipment.id} cleared on Hedera.` });
    } else {
      try {
        await apiFetch(`/api/v1/shipments/${shipment.id}/pre-clearance`, {
          method: "POST",
          body: JSON.stringify({ carrier: "fedex" }),
        });
        setPreClearanceStates(s => ({ ...s, [shipment.id]: "cleared" }));
        toast({ title: "Pre-Clearance Issued", description: `${shipment.id} cleared via live backend.` });
      } catch {
        setPreClearanceStates(s => ({ ...s, [shipment.id]: "flagged" }));
        toast({ title: "Pre-Clearance Failed", description: "Backend returned an error.", variant: "destructive" });
      }
    }
  };

  const receiptForShipment = (id: string) => mockPortTrustReceipts.find(r => r.shipmentId === id);

  const handleVerified = (result: VerificationResult) => {
    setVerificationResult(result);
    setTransportMode(result.transportMode);
  };

  const getTimeline = (shipment: ShipmentTracking): CarrierTimelineData => {
    if (isMockMode) return MOCK_TIMELINES[shipment.id] ?? {};
    const state = getShipmentState(shipment.id);
    return {
      shipment_received: true,
      documents_uploaded: verificationResult?.shipmentId === shipment.id,
      agents_verified: state === "cleared",
      submitted_for_clearance: state === "cleared",
      port_pre_cleared: state === "cleared",
      flagged: state === "flagged",
    };
  };

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

      <div className="rounded-xl border border-[hsl(213_50%_28%)] bg-[hsl(213_45%_16%)] shadow-card overflow-hidden">
        <div className="px-5 py-3 border-b border-[hsl(213_50%_24%)]">
          <h3 className="text-sm font-heading font-bold text-white flex items-center gap-2">
            <Package className="h-4 w-4 text-accent" />
            Upload &amp; Verify Shipment
          </h3>
          <p className="text-xs text-white/60 mt-0.5">Submit carrier documents for Hedera-verified pre-clearance.</p>
        </div>
        <div className="p-5">
          <CarrierVerificationPanel onVerified={handleVerified} />
        </div>
      </div>

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
            const state = getShipmentState(shipment.id);
            const isCleared = state === "cleared";
            const isPending = state === "pending";
            const isFlagged = state === "flagged";
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
                    <button
                      disabled={isCleared || isPending}
                      onClick={() => handlePreClearance(shipment)}
                      className="px-3 py-1.5 rounded border border-accent bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {isPending ? "Processing..." : isCleared ? "Pre-Cleared" : "Initiate Verification"}
                    </button>
                  </div>
                </div>
                <CarrierProcessingTimeline data={timeline} preCleared={isCleared && !!receipt} />
              </div>
            );
          })}
        </div>
      </div>

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
