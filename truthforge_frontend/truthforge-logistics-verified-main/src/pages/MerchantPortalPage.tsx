import { useState } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import { useWallet } from "@/contexts/WalletContext";
import { mockShipments, mockPortTrustReceipts, ShipmentTracking } from "@/lib/mock-data";
import { apiFetch, API_BASE } from "@/lib/api-client";
import {
  Package, ChevronDown, CheckCircle, Clock, AlertTriangle,
  Wallet, Shield, Zap, ToggleLeft, ToggleRight
} from "lucide-react";
import PortTrustReceipt from "@/components/PortTrustReceipt";
import { useToast } from "@/hooks/use-toast";

type ClearanceMode = "auto" | "manual";
type PreClearanceState = "none" | "pending" | "cleared" | "flagged";

const CARRIERS = [
  { id: "fedex", label: "FedEx", available: true },
  { id: "ups", label: "UPS", available: false },
  { id: "msc", label: "MSC", available: false },
  { id: "dhl", label: "DHL", available: false },
  { id: "maersk", label: "Maersk", available: false },
];

const MerchantPortalPage = () => {
  const { isMockMode } = useMockMode();
  const { isWalletConnected, wallet } = useWallet();
  const { toast } = useToast();

  const [selectedCarrier, setSelectedCarrier] = useState("fedex");
  const [carrierDropdownOpen, setCarrierDropdownOpen] = useState(false);
  const [clearanceMode, setClearanceMode] = useState<ClearanceMode>("auto");
  const [preClearanceStates, setPreClearanceStates] = useState<Record<string, PreClearanceState>>({});
  const [pendingConfirm, setPendingConfirm] = useState<string | null>(null);
  const [receiptModal, setReceiptModal] = useState<string | null>(null);

  const selectedCarrierLabel = CARRIERS.find(c => c.id === selectedCarrier)?.label ?? "FedEx";

  const getShipmentState = (id: string): PreClearanceState =>
    preClearanceStates[id] ?? (mockPortTrustReceipts.find(r => r.shipmentId === id) ? "cleared" : "none");

  const requestPreClearance = async (shipment: ShipmentTracking) => {
    if (clearanceMode === "manual" && pendingConfirm !== shipment.id) {
      setPendingConfirm(shipment.id);
      return;
    }
    setPendingConfirm(null);
    setPreClearanceStates(s => ({ ...s, [shipment.id]: "pending" }));

    if (isMockMode) {
      await new Promise(r => setTimeout(r, 1200));
      setPreClearanceStates(s => ({ ...s, [shipment.id]: "cleared" }));
      toast({ title: "Pre-Clearance Approved", description: `${shipment.id} has been pre-cleared on Hedera.` });
    } else {
      try {
        await apiFetch(`/api/v1/shipments/${shipment.id}/pre-clearance`, { method: "POST" });
        setPreClearanceStates(s => ({ ...s, [shipment.id]: "cleared" }));
        toast({ title: "Pre-Clearance Approved", description: `${shipment.id} pre-cleared via live backend.` });
      } catch {
        setPreClearanceStates(s => ({ ...s, [shipment.id]: "flagged" }));
        toast({ title: "Pre-Clearance Failed", description: "Backend returned an error.", variant: "destructive" });
      }
    }
  };

  const receiptForShipment = (id: string) => mockPortTrustReceipts.find(r => r.shipmentId === id);

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Page Header */}
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
          {isMockMode ? "Mock Mode – Simulated Responses" : "Live Mode – Connected to Backend"}
        </div>
      </div>

      {/* Sub-header controls */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Carrier Selector */}
        <div className="relative">
          <button
            onClick={() => setCarrierDropdownOpen(o => !o)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-card text-sm font-medium text-foreground hover:border-accent/40 transition-colors"
          >
            <Package className="h-4 w-4 text-accent" />
            Carrier: {selectedCarrierLabel}
            <ChevronDown className={`h-3.5 w-3.5 transition-transform ${carrierDropdownOpen ? "rotate-180" : ""}`} />
          </button>
          {carrierDropdownOpen && (
            <div className="absolute top-full left-0 mt-1 w-52 rounded-lg border border-border bg-card shadow-elevated z-20 py-1">
              {CARRIERS.map(c => (
                <button
                  key={c.id}
                  disabled={!c.available}
                  onClick={() => { if (c.available) { setSelectedCarrier(c.id); setCarrierDropdownOpen(false); } }}
                  className={`w-full flex items-center justify-between px-3 py-2 text-xs transition-colors ${
                    !c.available
                      ? "text-muted-foreground/40 cursor-not-allowed"
                      : selectedCarrier === c.id
                      ? "bg-primary/10 text-primary font-medium"
                      : "text-foreground hover:bg-secondary"
                  }`}
                >
                  {c.label}
                  {!c.available && (
                    <span className="text-[9px] border border-muted text-muted-foreground px-1.5 py-0.5 rounded uppercase tracking-wider">
                      Coming Soon
                    </span>
                  )}
                  {c.available && selectedCarrier === c.id && (
                    <CheckCircle className="h-3.5 w-3.5 text-success" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Pre-Clearance Mode Toggle */}
        <div className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-card">
          <Shield className="h-4 w-4 text-accent" />
          <span className="text-xs font-medium text-foreground">Pre-Clearance:</span>
          <button
            onClick={() => setClearanceMode(m => m === "auto" ? "manual" : "auto")}
            className="flex items-center gap-1.5 text-xs font-heading font-bold"
          >
            {clearanceMode === "auto" ? (
              <><ToggleRight className="h-4 w-4 text-success" /><span className="text-success">Auto</span></>
            ) : (
              <><ToggleLeft className="h-4 w-4 text-warning" /><span className="text-warning">Manual</span></>
            )}
          </button>
        </div>

        {/* Wallet status inline */}
        {isWalletConnected && (
          <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-success/30 bg-success/5 text-success text-xs font-medium">
            <Wallet className="h-3.5 w-3.5" />
            {wallet?.address}
          </div>
        )}
      </div>

      {/* Mode hint */}
      {clearanceMode === "manual" && (
        <div className="rounded border border-warning/30 bg-warning/5 px-4 py-2 text-xs text-warning font-medium flex items-center gap-2">
          <Zap className="h-3.5 w-3.5" />
          Manual mode: each pre-clearance requires your confirmation before submitting.
        </div>
      )}

      {/* Shipment Cards */}
      <div className="space-y-3">
        {mockShipments.map(shipment => {
          const state = getShipmentState(shipment.id);
          const receipt = receiptForShipment(shipment.id);
          const isCleared = state === "cleared";
          const isPending = state === "pending";
          const isFlagged = state === "flagged";
          const awaitingConfirm = pendingConfirm === shipment.id;

          return (
            <div key={shipment.id} className="rounded-xl border border-border bg-card p-5 shadow-card hover:shadow-elevated transition-all">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
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
                  {/* View Receipt */}
                  {isCleared && receipt && (
                    <button
                      onClick={() => setReceiptModal(shipment.id)}
                      className="px-3 py-1.5 rounded border border-accent/30 bg-accent/10 text-accent text-xs font-medium hover:bg-accent/20 transition-colors"
                    >
                      View Receipt
                    </button>
                  )}

                  {/* Manual confirm prompt */}
                  {awaitingConfirm && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-warning font-medium">Confirm pre-clearance?</span>
                      <button
                        onClick={() => requestPreClearance(shipment)}
                        className="px-3 py-1.5 rounded border border-success/40 bg-success/10 text-success text-xs font-medium hover:bg-success/20 transition-colors"
                      >
                        Yes, Submit
                      </button>
                      <button
                        onClick={() => setPendingConfirm(null)}
                        className="px-3 py-1.5 rounded border border-border text-xs text-muted-foreground hover:bg-secondary transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  )}

                  {/* Pre-Clearance Button */}
                  {!awaitingConfirm && (
                    <button
                      disabled={isCleared || isPending}
                      onClick={() => requestPreClearance(shipment)}
                      className="px-3 py-1.5 rounded border border-accent bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {isPending ? "Processing..." : isCleared ? "Pre-Cleared" : "Request Pre-Clearance"}
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Receipt Modal */}
      {receiptModal && (() => {
        const receipt = receiptForShipment(receiptModal);
        if (!receipt) return null;
        return (
          <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setReceiptModal(null)}>
            <div className="bg-card border border-border rounded-xl max-w-lg w-full max-h-[85vh] overflow-y-auto shadow-elevated" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between p-4 border-b border-border">
                <h3 className="font-heading font-bold text-foreground text-sm">Port Trust Receipt – {receipt.shipmentId}</h3>
                <button onClick={() => setReceiptModal(null)} className="text-muted-foreground hover:text-foreground text-sm">✕</button>
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
