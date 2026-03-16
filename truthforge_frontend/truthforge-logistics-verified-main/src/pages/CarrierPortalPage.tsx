import { useState } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import { useWallet } from "@/contexts/WalletContext";
import { mockShipments, mockPortTrustReceipts, ShipmentTracking } from "@/lib/mock-data";
import { apiFetch } from "@/lib/api-client";
import {
  Ship, Plane, Truck, CheckCircle, AlertTriangle, Clock,
  Package, Wallet, ExternalLink
} from "lucide-react";
import CarrierVerificationPanel, { VerificationResult, TransportMode } from "@/components/CarrierVerificationPanel";
import PortTrustReceipt from "@/components/PortTrustReceipt";
import { useToast } from "@/hooks/use-toast";

type PreClearanceState = "none" | "pending" | "cleared" | "flagged";

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

const CarrierPortalPage = () => {
  const { isMockMode } = useMockMode();
  const { isWalletConnected, wallet } = useWallet();
  const { toast } = useToast();

  const [transportMode, setTransportMode] = useState<TransportMode>("sea");
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [preClearanceStates, setPreClearanceStates] = useState<Record<string, PreClearanceState>>({});
  const [receiptModal, setReceiptModal] = useState<string | null>(null);

  const getShipmentState = (id: string): PreClearanceState =>
    preClearanceStates[id] ?? (mockPortTrustReceipts.find(r => r.shipmentId === id) ? "cleared" : "none");

  const handleVerified = (result: VerificationResult) => {
    setVerificationResult(result);
    setTransportMode(result.transportMode);
  };

  const handlePreClearance = async (shipment: ShipmentTracking) => {
    setPreClearanceStates(s => ({ ...s, [shipment.id]: "pending" }));

    if (isMockMode) {
      await new Promise(r => setTimeout(r, 1200));
      setPreClearanceStates(s => ({ ...s, [shipment.id]: "cleared" }));
      toast({ title: "Pre-Clearance Issued", description: `${shipment.id} cleared on Hedera.` });
    } else {
      try {
        await apiFetch(`/api/v1/shipments/${shipment.id}/pre-clearance`, { method: "POST" });
        setPreClearanceStates(s => ({ ...s, [shipment.id]: "cleared" }));
        toast({ title: "Pre-Clearance Issued", description: `${shipment.id} cleared via live backend.` });
      } catch {
        setPreClearanceStates(s => ({ ...s, [shipment.id]: "flagged" }));
        toast({ title: "Pre-Clearance Failed", description: "Backend returned an error.", variant: "destructive" });
      }
    }
  };

  const receiptForShipment = (id: string) => mockPortTrustReceipts.find(r => r.shipmentId === id);

  const modeLabel: Record<TransportMode, string> = {
    sea: "Container",
    air: "Cargo",
    land: "Pallet",
  };

  const ModeIcon = transportMode === "sea" ? Ship : transportMode === "air" ? Plane : Truck;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
          <Package className="h-5 w-5 text-accent" />
          Carrier Portal
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Upload carrier documents, verify shipments, and manage pre-clearance status.
        </p>
        <div className="flex items-center gap-3 mt-2 flex-wrap">
          <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${
            isMockMode ? "border-warning/40 bg-warning/10 text-warning" : "border-success/40 bg-success/10 text-success"
          }`}>
            {isMockMode ? "Mock Mode – Simulated Responses" : "Live Mode – Connected to Backend"}
          </div>
          {isWalletConnected && (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded border border-success/30 bg-success/5 text-success text-[10px] font-medium">
              <Wallet className="h-3 w-3" />
              {wallet?.address} · Hedera Testnet
            </div>
          )}
        </div>
      </div>

      {/* Carrier Verification Panel */}
      <CarrierVerificationPanel onVerified={handleVerified} />

      {/* Shipment Intelligence Card (shown after verification) */}
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

          {/* AI Reasoning */}
          <div className="rounded border border-border bg-secondary/30 px-3 py-3">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">AI Reasoning</span>
            <p className="text-xs text-foreground leading-relaxed">{verificationResult.aiReasoning}</p>
          </div>

          {/* Container / Cargo Intelligence Table */}
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
                          <td className="px-3 py-2 text-muted-foreground">{item.count ?? "—"}</td>
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

      {/* Shipment List with Pre-Clearance Sync */}
      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <div className="p-5 border-b border-border">
          <h3 className="text-sm font-heading font-bold text-foreground flex items-center gap-2">
            <Ship className="h-4 w-4 text-accent" />
            Merchant Shipments
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Shipments from merchant portal. Pre-clearance status is synced in real time.
          </p>
        </div>

        <div className="divide-y divide-border">
          {mockShipments.map(shipment => {
            const state = getShipmentState(shipment.id);
            const isCleared = state === "cleared";
            const isPending = state === "pending";
            const isFlagged = state === "flagged";
            const receipt = receiptForShipment(shipment.id);
            const MIcon = shipment.freightMode === "air" ? Plane : shipment.freightMode === "land" ? Truck : Ship;

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
                      {shipment.carrier} · {shipment.origin} → {shipment.destination} · ETA {shipment.eta}
                    </div>
                    {isCleared && (
                      <div className="text-[10px] text-success font-medium">Verified upstream by merchant</div>
                    )}
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
              </div>
            );
          })}
        </div>
      </div>

      {/* Port Trust Receipt Modal */}
      {receiptModal && (() => {
        const receipt = receiptForShipment(receiptModal);
        if (!receipt) return null;
        return (
          <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setReceiptModal(null)}>
            <div className="bg-card border border-border rounded-xl max-w-lg w-full max-h-[85vh] overflow-y-auto shadow-elevated" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between p-4 border-b border-border">
                <div>
                  <h3 className="font-heading font-bold text-foreground text-sm">Port Trust Receipt – {receipt.shipmentId}</h3>
                  <p className="text-[10px] text-muted-foreground mt-0.5">Port-Readable Clearance Proof – Verified on Hedera</p>
                </div>
                <button onClick={() => setReceiptModal(null)} className="text-muted-foreground hover:text-foreground text-sm">✕</button>
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
