import { useState } from "react";
import { mockShipments, mockPortTrustReceipts } from "@/lib/mock-data";
import { useMockMode } from "@/contexts/MockModeContext";
import { useToast } from "@/hooks/use-toast";
import GlobalTradeRiskCommandCenter from "@/components/GlobalTradeRiskCommandCenter";
import PreClearanceIntelligencePanel from "@/components/PreClearanceIntelligencePanel";
import PortTrustReceipt from "@/components/PortTrustReceipt";
import { Shield, CheckCircle, Clock, AlertTriangle, ExternalLink, Flag, X } from "lucide-react";

const PortAuthorityPortalPage = () => {
  const { isMockMode } = useMockMode();
  const { toast } = useToast();
  const [selectedReceipt, setSelectedReceipt] = useState<string | null>(null);
  const [shipmentStatuses, setShipmentStatuses] = useState<Record<string, string>>({});

  const shipments = mockShipments;
  const receipts = mockPortTrustReceipts;

  const cleared = shipments.filter((s) => (shipmentStatuses[s.id] ?? s.status) === "Verified").length;
  const pending = shipments.filter((s) => (shipmentStatuses[s.id] ?? s.status) === "Pending Consensus").length;
  const flagged = shipments.filter((s) => (shipmentStatuses[s.id] ?? s.status) === "Flagged Exception").length;

  const firstWithContainers = shipments.find((s) => s.containerCount && s.containerCount > 0);
  const receiptForFirst = firstWithContainers ? receipts.find((r) => r.shipmentId === firstWithContainers.id) : undefined;

  const handleFlag = (id: string) => {
    setShipmentStatuses((prev) => ({ ...prev, [id]: "Flagged Exception" }));
    toast({ title: "Shipment Flagged", description: `${id} has been flagged for inspection.` });
  };

  const handleApprove = (id: string) => {
    setShipmentStatuses((prev) => ({ ...prev, [id]: "Verified" }));
    toast({ title: "Shipment Approved", description: `${id} has been approved for clearance.` });
  };

  const openReceipt = receipts.find((r) => r.id === selectedReceipt);

  const statusBadge = (status: string) => {
    if (status === "Verified")
      return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-success/10 text-success"><CheckCircle className="h-3 w-3" />Cleared</span>;
    if (status === "Flagged Exception")
      return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-destructive/10 text-destructive"><AlertTriangle className="h-3 w-3" />Flagged</span>;
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-warning/10 text-warning"><Clock className="h-3 w-3" />Pending</span>;
  };

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
            <Shield className="h-5 w-5 text-accent" />
            Port Authority Portal
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Incoming shipment clearance, risk intelligence, and port trust receipts.
          </p>
        </div>
        <span className="text-[10px] font-heading font-bold px-2 py-1 rounded uppercase tracking-wider border bg-warning/10 text-warning border-warning/30">
          Preview Mode
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <div className="text-2xl font-heading font-black text-success">{cleared}</div>
          <div className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">Cleared</div>
        </div>
        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <div className="text-2xl font-heading font-black text-warning">{pending}</div>
          <div className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">Pending</div>
        </div>
        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <div className="text-2xl font-heading font-black text-destructive">{flagged}</div>
          <div className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">Flagged</div>
        </div>
      </div>

      {firstWithContainers && (
        <div>
          <h3 className="text-sm font-heading font-bold text-muted-foreground uppercase tracking-wider mb-3">
            Pre-Arrival Clearance Queue
          </h3>
          <PreClearanceIntelligencePanel shipment={firstWithContainers} receipt={receiptForFirst} />
        </div>
      )}

      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <div className="p-4 border-b border-border">
          <h3 className="text-sm font-heading font-bold text-foreground">Incoming Shipments</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full" role="table">
            <thead>
              <tr className="border-b border-border bg-secondary/50">
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Shipment</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Carrier</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Route</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">ETA</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">HCS Ref</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              {shipments.map((s) => {
                const currentStatus = shipmentStatuses[s.id] ?? s.status;
                const receipt = receipts.find((r) => r.shipmentId === s.id);
                const txRef = receipt?.hederaTxRef;
                const topicId = txRef ? txRef.split("@")[0] : null;
                const isLinkable = !isMockMode && topicId;
                return (
                  <tr key={s.id} className="border-b border-border last:border-0 hover:bg-accent/5 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-foreground">{s.id}</td>
                    <td className="py-3 px-4 text-xs text-foreground">{s.carrier}</td>
                    <td className="py-3 px-4 text-xs text-muted-foreground">{s.origin} to {s.destination}</td>
                    <td className="py-3 px-4">{statusBadge(currentStatus)}</td>
                    <td className="py-3 px-4 text-xs font-mono text-muted-foreground">{s.eta}</td>
                    <td className="py-3 px-4">
                      {txRef ? (
                        isLinkable ? (
                          <a
                            href={`https://hashscan.io/testnet/account/${topicId}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] font-mono text-accent hover:underline"
                          >
                            <ExternalLink className="h-3 w-3 shrink-0" />
                            <span className="truncate max-w-[100px]">{txRef}</span>
                          </a>
                        ) : (
                          <span className="text-[11px] font-mono text-accent truncate max-w-[100px] block">{txRef}</span>
                        )
                      ) : (
                        <span className="text-[11px] text-muted-foreground">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleFlag(s.id)}
                          className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors"
                          aria-label={`Flag ${s.id}`}
                        >
                          <Flag className="h-3 w-3" />
                          Flag
                        </button>
                        <button
                          onClick={() => handleApprove(s.id)}
                          className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded bg-success/10 text-success hover:bg-success/20 transition-colors"
                          aria-label={`Approve ${s.id}`}
                        >
                          <CheckCircle className="h-3 w-3" />
                          Approve
                        </button>
                        {receipt && (
                          <button
                            onClick={() => setSelectedReceipt(receipt.id)}
                            className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
                            aria-label={`View receipt for ${s.id}`}
                          >
                            <Shield className="h-3 w-3" />
                            Receipt
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <GlobalTradeRiskCommandCenter />

      {openReceipt && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Port Trust Receipt"
        >
          <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl bg-card border border-border shadow-xl">
            <button
              onClick={() => setSelectedReceipt(null)}
              className="absolute top-4 right-4 p-1 rounded hover:bg-accent/10 text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Close receipt"
            >
              <X className="h-5 w-5" />
            </button>
            <div className="p-6">
              <PortTrustReceipt receipt={openReceipt} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortAuthorityPortalPage;
