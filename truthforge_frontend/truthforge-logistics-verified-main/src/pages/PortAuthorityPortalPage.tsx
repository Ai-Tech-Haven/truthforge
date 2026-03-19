import { useState } from "react";
import { mockShipments, mockPortTrustReceipts, ShipmentTracking } from "@/lib/mock-data";
import { useMockMode } from "@/contexts/MockModeContext";
import { useToast } from "@/hooks/use-toast";
import PortClearanceTimeline, { PortClearanceStepData } from "@/components/PortClearanceTimeline";
import PortTrustReceipt from "@/components/PortTrustReceipt";
import {
  Shield, CheckCircle, Clock, AlertTriangle, ExternalLink,
  Flag, X, ChevronDown, ChevronUp, Anchor, Plane, Truck,
} from "lucide-react";

// Port options
const PORTS = [
  { code: "NGLOS", label: "Lagos" },
  { code: "NLRTM", label: "Rotterdam" },
  { code: "SGSIN", label: "Singapore" },
] as const;
type PortCode = typeof PORTS[number]["code"];

// Transport modes
type TransportMode = "sea" | "air" | "land";
const MODES: { key: TransportMode; label: string; icon: typeof Anchor }[] = [
  { key: "sea",  label: "Sea",  icon: Anchor },
  { key: "air",  label: "Air",  icon: Plane  },
  { key: "land", label: "Land", icon: Truck  },
];

// Column labels by transport mode
const modeLabels: Record<TransportMode, { unit: string; batch: string }> = {
  sea:  { unit: "Container",  batch: "Vessel" },
  air:  { unit: "Cargo Unit", batch: "Flight" },
  land: { unit: "Pallet",     batch: "Truck"  },
};

// Derive timeline data from shipment status
function toTimelineData(s: ShipmentTracking, overrideStatus?: string): PortClearanceStepData {
  const status = overrideStatus ?? s.status;
  const isVerified = status === "Verified";
  const isFlagged  = status === "Flagged Exception";
  const isPending  = status === "Pending Consensus";
  return {
    shipment_announced:  true,
    documents_submitted: isVerified || isFlagged || !isPending,
    agents_verified:     isVerified || isFlagged,
    hbar_settled:        isVerified,
    clearance_issued:    isVerified,
    flagged:             isFlagged,
  };
}

// AI recommendation helper
function aiRecommendation(s: ShipmentTracking): string {
  if ((s.flaggedContainers ?? 0) > 0)
    return `Manual inspection recommended for ${s.flaggedContainers} container${s.flaggedContainers === 1 ? "" : "s"}`;
  if ((s.verifiedContainers ?? 0) === (s.containerCount ?? 0) && (s.containerCount ?? 0) > 0)
    return "All containers verified - fast-track clearance eligible";
  return "Verification in progress";
}

const PortAuthorityPortalPage = () => {
  const { isMockMode } = useMockMode();
  const { toast } = useToast();

  const [selectedPort, setSelectedPort]         = useState<PortCode>("NGLOS");
  const [transportMode, setTransportMode]       = useState<TransportMode>("sea");
  const [expandedRow, setExpandedRow]           = useState<string | null>(null);
  const [shipmentStatuses, setShipmentStatuses] = useState<Record<string, string>>({});
  const [selectedReceipt, setSelectedReceipt]   = useState<string | null>(null);
  const [portOpen, setPortOpen]                 = useState(false);

  const shipments = mockShipments;
  const receipts  = mockPortTrustReceipts;

  const filtered = shipments.filter((s) => {
    if (transportMode === "sea")  return !s.freightMode || s.freightMode === "sea";
    if (transportMode === "air")  return s.freightMode === "air";
    if (transportMode === "land") return s.freightMode === "land";
    return true;
  });

  const cleared = filtered.filter((s) => (shipmentStatuses[s.id] ?? s.status) === "Verified").length;
  const pending = filtered.filter((s) => (shipmentStatuses[s.id] ?? s.status) === "Pending Consensus").length;
  const flagged = filtered.filter((s) => (shipmentStatuses[s.id] ?? s.status) === "Flagged Exception").length;

  const handleFlag = (id: string) => {
    setShipmentStatuses((p) => ({ ...p, [id]: "Flagged Exception" }));
    toast({ title: "Shipment Flagged", description: `${id} flagged for inspection.` });
  };
  const handleApprove = (id: string) => {
    setShipmentStatuses((p) => ({ ...p, [id]: "Verified" }));
    toast({ title: "Shipment Approved", description: `${id} approved for clearance.` });
  };

  const openReceipt = receipts.find((r) => r.id === selectedReceipt);
  const portLabel   = PORTS.find((p) => p.code === selectedPort)?.label ?? "Lagos";
  const labels      = modeLabels[transportMode];

  const statusBadge = (status: string) => {
    if (status === "Verified")
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-success/10 text-success">
          <CheckCircle className="h-3 w-3" />Cleared
        </span>
      );
    if (status === "Flagged Exception")
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-destructive/10 text-destructive">
          <AlertTriangle className="h-3 w-3" />Flagged
        </span>
      );
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-warning/10 text-warning">
        <Clock className="h-3 w-3" />Pending
      </span>
    );
  };

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
            <Shield className="h-5 w-5 text-accent" />
            Port Authority Portal
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Incoming shipment clearance, risk intelligence, and port trust receipts.
          </p>
        </div>

        {/* Port selector */}
        <div className="relative">
          <button
            onClick={() => setPortOpen((o) => !o)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-card text-sm font-medium text-foreground hover:bg-accent/10 transition-colors"
            aria-haspopup="listbox"
            aria-expanded={portOpen}
          >
            <Anchor className="h-4 w-4 text-accent" />
            Port: {portLabel} ({selectedPort})
            <ChevronDown className="h-3 w-3 text-muted-foreground" />
          </button>
          {portOpen && (
            <div className="absolute right-0 mt-1 w-48 rounded-lg border border-border bg-card shadow-lg z-20" role="listbox">
              {PORTS.map((p) => (
                <button
                  key={p.code}
                  role="option"
                  aria-selected={selectedPort === p.code}
                  onClick={() => { setSelectedPort(p.code); setPortOpen(false); }}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-accent/10 transition-colors first:rounded-t-lg last:rounded-b-lg ${
                    selectedPort === p.code ? "text-accent font-semibold" : "text-foreground"
                  }`}
                >
                  {p.label} ({p.code})
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Stats */}
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

      {/* Transport mode toggle */}
      <div className="flex items-center gap-1 p-1 rounded-lg bg-secondary w-fit">
        {MODES.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => { setTransportMode(key); setExpandedRow(null); }}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              transportMode === key
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </button>
        ))}
      </div>

      {/* Pre-Arrival Clearance Queue */}
      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="text-sm font-heading font-bold text-foreground">
            Pre-Arrival Clearance Queue &mdash; {portLabel}
          </h3>
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
            {filtered.length} {labels.batch}{filtered.length !== 1 ? "s" : ""}
          </span>
        </div>

        {filtered.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            No {transportMode} shipments in queue.
          </div>
        ) : (
          <div className="divide-y divide-border">
            {filtered.map((s) => {
              const currentStatus = shipmentStatuses[s.id] ?? s.status;
              const receipt       = receipts.find((r) => r.shipmentId === s.id);
              const txRef         = receipt?.hederaTxRef;
              const topicId       = txRef ? txRef.split("@")[0] : null;
              const isLinkable    = !isMockMode && topicId;
              const isExpanded    = expandedRow === s.id;
              const timelineData: PortClearanceStepData = toTimelineData(s, currentStatus);
              const containers    = s.containers ?? [];
              const verifiedCount = s.verifiedContainers ?? 0;
              const flaggedCount  = s.flaggedContainers  ?? 0;
              const totalCount    = s.containerCount     ?? 0;

              return (
                <div key={s.id}>
                  {/* Row */}
                  <div className="p-4 hover:bg-accent/5 transition-colors">
                    <div className="flex flex-wrap items-center gap-3">

                      {/* Expand toggle */}
                      <button
                        onClick={() => setExpandedRow(isExpanded ? null : s.id)}
                        className="p-1 rounded hover:bg-accent/10 text-muted-foreground hover:text-foreground transition-colors shrink-0"
                        aria-label={isExpanded ? "Collapse" : "Expand"}
                      >
                        {isExpanded
                          ? <ChevronUp className="h-4 w-4" />
                          : <ChevronDown className="h-4 w-4" />
                        }
                      </button>

                      {/* Shipment info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-xs font-bold text-foreground">{s.id}</span>
                          {statusBadge(currentStatus)}
                        </div>
                        <div className="text-[11px] text-muted-foreground mt-0.5">
                          {s.vessel ?? s.carrier} &middot; {s.origin} to {s.destination} &middot; ETA {s.eta}
                        </div>
                      </div>

                      {/* HCS ref */}
                      <div className="hidden md:block">
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
                          <span className="text-[11px] text-muted-foreground">No HCS ref</span>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => handleFlag(s.id)}
                          className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors"
                          aria-label={`Flag ${s.id}`}
                        >
                          <Flag className="h-3 w-3" />Flag
                        </button>
                        <button
                          onClick={() => handleApprove(s.id)}
                          className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded bg-success/10 text-success hover:bg-success/20 transition-colors"
                          aria-label={`Approve ${s.id}`}
                        >
                          <CheckCircle className="h-3 w-3" />Approve
                        </button>
                        {receipt && (
                          <button
                            onClick={() => setSelectedReceipt(receipt.id)}
                            className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
                            aria-label={`View receipt for ${s.id}`}
                          >
                            <Shield className="h-3 w-3" />Receipt
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Timeline always visible under each row */}
                    <PortClearanceTimeline data={timelineData} />
                  </div>

                  {/* Expanded detail */}
                  {isExpanded && (
                    <div className="px-4 pb-4 bg-secondary/30 border-t border-border/60 space-y-4">

                      {/* Intelligence card */}
                      <div className="rounded-lg border border-border bg-card p-3 mt-3">
                        <div className="text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider mb-2">
                          {labels.batch} Intelligence
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                          <div>
                            <div className="text-lg font-heading font-black text-foreground">{totalCount || "N/A"}</div>
                            <div className="text-[10px] text-muted-foreground">Total {labels.unit}s</div>
                          </div>
                          <div>
                            <div className="text-lg font-heading font-black text-success">{verifiedCount || "N/A"}</div>
                            <div className="text-[10px] text-muted-foreground">Verified</div>
                          </div>
                          <div>
                            <div className="text-lg font-heading font-black text-destructive">{flaggedCount || "N/A"}</div>
                            <div className="text-[10px] text-muted-foreground">Flagged</div>
                          </div>
                          <div className="col-span-2 sm:col-span-1 text-left sm:text-center">
                            <div className="text-[10px] text-muted-foreground mb-1">AI Recommendation</div>
                            <div className="text-[11px] font-medium text-foreground">{aiRecommendation(s)}</div>
                          </div>
                        </div>
                      </div>

                      {/* Container table + grid */}
                      {containers.length > 0 && (
                        <div className="rounded-lg border border-border bg-card overflow-hidden">
                          <div className="text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider px-3 pt-3 pb-2">
                            {labels.unit} Intelligence
                          </div>
                          <div className="overflow-x-auto">
                            <table className="w-full" role="table">
                              <thead>
                                <tr className="border-b border-border bg-secondary/50">
                                  <th className="py-2 px-3 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">ID</th>
                                  <th className="py-2 px-3 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Status</th>
                                  <th className="py-2 px-3 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Risk</th>
                                </tr>
                              </thead>
                              <tbody>
                                {containers.slice(0, 8).map((c) => (
                                  <tr key={c.id} className="border-b border-border last:border-0">
                                    <td className="py-1.5 px-3 font-mono text-[11px] text-foreground">{c.id}</td>
                                    <td className="py-1.5 px-3">
                                      {c.status === "verified" && <span className="text-[10px] text-success">Verified</span>}
                                      {c.status === "flagged"  && <span className="text-[10px] text-destructive">Flagged</span>}
                                      {c.status === "pending"  && <span className="text-[10px] text-warning">Pending</span>}
                                    </td>
                                    <td className="py-1.5 px-3">
                                      <span className={`text-[10px] font-medium ${
                                        c.riskLevel === "high"   ? "text-destructive" :
                                        c.riskLevel === "medium" ? "text-warning" : "text-success"
                                      }`}>
                                        {c.riskLevel.toUpperCase()}
                                      </span>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>

                          {/* Visual grid */}
                          <div className="px-3 pb-3 pt-2">
                            <div className="text-[10px] text-muted-foreground mb-1.5">
                              {labels.unit} Grid
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {containers.map((c) => (
                                <span
                                  key={c.id}
                                  title={`${c.id} - ${c.status}`}
                                  className="text-base leading-none"
                                  aria-label={`${c.id} ${c.status}`}
                                >
                                  {c.status === "verified" ? "\u{1F7E9}" : c.status === "flagged" ? "\u{1F7E5}" : "\u{1F7E8}"}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Trust proof */}
                      {receipt && (
                        <div className="rounded-lg border border-border bg-card p-3">
                          <div className="text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider mb-2">
                            Port-Readable Clearance Proof - Verifiable on Hedera
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                            <div>
                              <span className="text-muted-foreground">Status: </span>
                              <span className={`font-medium ${
                                receipt.clearanceStatus === "cleared"  ? "text-success" :
                                receipt.clearanceStatus === "flagged"  ? "text-destructive" : "text-warning"
                              }`}>
                                {receipt.clearanceStatus.toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Network: </span>
                              <span className="font-medium text-foreground">{isMockMode ? "Testnet (Mock)" : "Testnet"}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Issued: </span>
                              <span className="font-mono text-foreground">{receipt.issuedAt}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <span className="text-muted-foreground">Tx Hash: </span>
                              {isMockMode ? (
                                <span className="font-mono text-accent truncate max-w-[160px]">{receipt.hederaTxRef}</span>
                              ) : (
                                <a
                                  href={`https://hashscan.io/testnet/account/${receipt.hederaTxRef.split("@")[0]}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 font-mono text-accent hover:underline truncate max-w-[160px]"
                                >
                                  <ExternalLink className="h-3 w-3 shrink-0" />
                                  {receipt.hederaTxRef}
                                </a>
                              )}
                            </div>
                          </div>
                          <button
                            onClick={() => setSelectedReceipt(receipt.id)}
                            className="mt-2 text-[10px] font-medium text-accent hover:underline"
                          >
                            View full receipt
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Receipt modal */}
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
