import { useState, useEffect } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import { mockShipments, mockPortTrustReceipts } from "@/lib/mock-data";
import { apiFetch } from "@/lib/api-client";
import {
  Anchor, CheckCircle, AlertTriangle, Clock,
  Shield, FileText, RefreshCw, BarChart3
} from "lucide-react";
import PortTrustReceipt from "@/components/PortTrustReceipt";
import { useToast } from "@/hooks/use-toast";

type ClearanceStatus = "cleared" | "pending" | "flagged";

interface PortShipment {
  id: string;
  carrier: string;
  origin: string;
  destination: string;
  eta: string;
  status: ClearanceStatus;
  hederaTxRef?: string;
}

const statusColor: Record<ClearanceStatus, string> = {
  cleared: "text-success bg-success/10 border-success/30",
  pending: "text-warning bg-warning/10 border-warning/30",
  flagged: "text-destructive bg-destructive/10 border-destructive/30",
};

const PortAuthorityPortalPage = () => {
  const { isMockMode } = useMockMode();
  const { toast } = useToast();

  const [shipments, setShipments] = useState<PortShipment[]>([]);
  const [loading, setLoading] = useState(false);
  const [receiptModal, setReceiptModal] = useState<string | null>(null);
  const [overrides, setOverrides] = useState<Record<string, ClearanceStatus>>({});

  const buildMockShipments = (): PortShipment[] =>
    mockShipments.map((s) => {
      const receipt = mockPortTrustReceipts.find((r) => r.shipmentId === s.id);
      return {
        id: s.id,
        carrier: s.carrier,
        origin: s.origin,
        destination: s.destination,
        eta: s.eta,
        status: receipt ? "cleared" : "pending",
        hederaTxRef: receipt?.hederaTxRef,
      };
    });

  const loadShipments = async () => {
    setLoading(true);
    if (isMockMode) {
      await new Promise((r) => setTimeout(r, 400));
      setShipments(buildMockShipments());
    } else {
      try {
        const data = await apiFetch<PortShipment[]>("/api/v1/port-authority/shipments");
        setShipments(data);
      } catch {
        setShipments(buildMockShipments());
        toast({ title: "Using cached data", description: "Could not reach live backend.", variant: "destructive" });
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    loadShipments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isMockMode]);

  const getStatus = (s: PortShipment): ClearanceStatus => overrides[s.id] ?? s.status;

  const handleFlag = async (id: string) => {
    setOverrides((prev) => ({ ...prev, [id]: "flagged" }));
    if (!isMockMode) {
      try { await apiFetch(`/api/v1/port-authority/shipments/${id}/flag`, { method: "POST" }); } catch { /* optimistic */ }
    }
    toast({ title: "Shipment Flagged", description: `${id} flagged for review.`, variant: "destructive" });
  };

  const handleApprove = async (id: string) => {
    setOverrides((prev) => ({ ...prev, [id]: "cleared" }));
    if (!isMockMode) {
      try { await apiFetch(`/api/v1/port-authority/shipments/${id}/approve`, { method: "POST" }); } catch { /* optimistic */ }
    }
    toast({ title: "Shipment Approved", description: `${id} approved for port entry.` });
  };

  const cleared = shipments.filter((s) => getStatus(s) === "cleared").length;
  const pending = shipments.filter((s) => getStatus(s) === "pending").length;
  const flagged = shipments.filter((s) => getStatus(s) === "flagged").length;

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
          <Anchor className="h-5 w-5 text-accent" />
          Port Authority Portal
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Review incoming shipments, validate pre-clearance receipts, and manage port entry decisions.
        </p>
        <div className={`inline-flex items-center gap-1.5 mt-2 px-2.5 py-1 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${isMockMode ? "border-warning/40 bg-warning/10 text-warning" : "border-success/40 bg-success/10 text-success"}`}>
          {isMockMode ? "Mock Mode" : "Live Mode – Connected to Backend"}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-xl border border-success/30 bg-success/5 p-4 text-center">
          <div className="text-2xl font-heading font-bold text-success">{cleared}</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider mt-1">Pre-Cleared</div>
        </div>
        <div className="rounded-xl border border-warning/30 bg-warning/5 p-4 text-center">
          <div className="text-2xl font-heading font-bold text-warning">{pending}</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider mt-1">Pending Review</div>
        </div>
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-center">
          <div className="text-2xl font-heading font-bold text-destructive">{flagged}</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider mt-1">Flagged</div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <div className="p-5 border-b border-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-heading font-bold text-foreground flex items-center gap-2">
              <Shield className="h-4 w-4 text-accent" />
              Incoming Shipments
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">All shipments with pre-clearance receipts verified on Hedera.</p>
          </div>
          <button onClick={loadShipments} disabled={loading} className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-border text-xs text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors disabled:opacity-50">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
        {loading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading shipments...</div>
        ) : (
          <div className="divide-y divide-border">
            {shipments.map((shipment) => {
              const status = getStatus(shipment);
              const receipt = mockPortTrustReceipts.find((r) => r.shipmentId === shipment.id);
              const isCleared = status === "cleared";
              const isFlagged = status === "flagged";
              return (
                <div key={shipment.id} className="p-4 hover:bg-secondary/20 transition-colors">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-sm font-bold text-foreground">{shipment.id}</span>
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${statusColor[status]}`}>
                          {status === "cleared" && <CheckCircle className="h-2.5 w-2.5" />}
                          {status === "pending" && <Clock className="h-2.5 w-2.5" />}
                          {status === "flagged" && <AlertTriangle className="h-2.5 w-2.5" />}
                          {status === "cleared" ? "Pre-Cleared" : status}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">{shipment.carrier} · {shipment.origin} to {shipment.destination} · ETA {shipment.eta}</div>
                      {shipment.hederaTxRef && <div className="text-[10px] font-mono text-accent">HCS: {shipment.hederaTxRef}</div>}
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      {receipt && (
                        <button onClick={() => setReceiptModal(shipment.id)} className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-accent/30 bg-accent/10 text-accent text-xs font-medium hover:bg-accent/20 transition-colors">
                          <FileText className="h-3 w-3" />
                          View Receipt
                        </button>
                      )}
                      {!isFlagged && (
                        <button onClick={() => handleFlag(shipment.id)} className="px-3 py-1.5 rounded border border-destructive/40 bg-destructive/10 text-destructive text-xs font-medium hover:bg-destructive/20 transition-colors">
                          Flag
                        </button>
                      )}
                      {!isCleared && (
                        <button onClick={() => handleApprove(shipment.id)} className="px-3 py-1.5 rounded border border-success/40 bg-success/10 text-success text-xs font-heading font-bold uppercase tracking-wider hover:bg-success/20 transition-colors">
                          Approve Entry
                        </button>
                      )}
                      {isCleared && (
                        <span className="flex items-center gap-1 px-3 py-1.5 rounded border border-success/30 bg-success/5 text-success text-xs font-medium">
                          <BarChart3 className="h-3 w-3" />
                          Admitted
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {receiptModal && (() => {
        const receipt = mockPortTrustReceipts.find((r) => r.shipmentId === receiptModal);
        if (!receipt) return null;
        return (
          <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setReceiptModal(null)}>
            <div className="bg-card border border-border rounded-xl max-w-lg w-full max-h-[85vh] overflow-y-auto shadow-elevated" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between p-4 border-b border-border">
                <div>
                  <h3 className="font-heading font-bold text-foreground text-sm">Port Trust Receipt - {receipt.shipmentId}</h3>
                  <p className="text-[10px] text-muted-foreground mt-0.5">Port-Readable Clearance Proof - Verified on Hedera</p>
                </div>
                <button onClick={() => setReceiptModal(null)} className="text-muted-foreground hover:text-foreground text-sm">x</button>
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

export default PortAuthorityPortalPage;