import { useState } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import { Package, Upload, CheckCircle, Clock, AlertTriangle, FileText, Truck, RefreshCw, X, CalendarCheck } from "lucide-react";
import { mockCarrierVerifications, CarrierVerification } from "@/lib/mock-data";
import { useToast } from "@/hooks/use-toast";
import { API_BASE } from "@/lib/api-client";

const ACCEPTED_DOC_TYPES = [
  { value: "bill_of_lading", label: "Bill of Lading" },
  { value: "commercial_invoice", label: "Commercial Invoice" },
  { value: "packing_list", label: "Packing List" },
  { value: "certificate_of_origin", label: "Certificate of Origin" },
  { value: "customs_declaration", label: "Customs Declaration" },
  { value: "phytosanitary", label: "Phytosanitary Certificate" },
];

interface UploadedDoc {
  name: string;
  type: string;
  size: string;
}

const statusConfig = {
  verified: { icon: CheckCircle, color: "text-success", bg: "bg-success/10 border-success/30", label: "Verified" },
  pending: { icon: Clock, color: "text-warning", bg: "bg-warning/10 border-warning/30", label: "Pending" },
  failed: { icon: AlertTriangle, color: "text-destructive", bg: "bg-destructive/10 border-destructive/30", label: "Failed" },
};

const CarrierPortal = () => {
  const { isMockMode } = useMockMode();
  const { toast } = useToast();
  const [carrierName, setCarrierName] = useState("");
  const [shipmentId, setShipmentId] = useState("");
  const [selectedDocType, setSelectedDocType] = useState(ACCEPTED_DOC_TYPES[0].value);
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDoc[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<CarrierVerification | null>(null);
  const [error, setError] = useState("");
  const [pickupStatus, setPickupStatus] = useState<"none" | "scheduled">("none");
  const [pickupTime, setPickupTime] = useState<string | null>(null);

  const handleAddDoc = () => {
    const label = ACCEPTED_DOC_TYPES.find(d => d.value === selectedDocType)?.label ?? selectedDocType;
    if (uploadedDocs.find(d => d.type === label)) return;
    setUploadedDocs(prev => [...prev, {
      name: `${label.replace(/ /g, "_")}_${shipmentId || "DOC"}.pdf`,
      type: label,
      size: `${(Math.random() * 2 + 0.5).toFixed(1)} MB`,
    }]);
  };

  const handleRemoveDoc = (idx: number) => {
    setUploadedDocs(prev => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = async () => {
    setError("");
    if (!carrierName.trim()) { setError("Carrier name is required."); return; }
    if (!shipmentId.trim()) { setError("Shipment ID is required."); return; }
    if (uploadedDocs.length === 0) { setError("Upload at least one document."); return; }
    setIsSubmitting(true);
    setPickupStatus("none");
    setPickupTime(null);

    if (isMockMode) {
      await new Promise(r => setTimeout(r, 1400));
      const mock = mockCarrierVerifications.find(v => v.shipmentId === shipmentId.toUpperCase())
        ?? {
          id: `CV-${Date.now()}`,
          shipmentId: shipmentId.toUpperCase(),
          carrierName,
          status: "pending" as const,
          documents: uploadedDocs,
          submittedAt: new Date().toISOString().replace("T", " ").slice(0, 19),
          verificationFee: { amount: 0.18, currency: "HBAR", paymentNetwork: "Hedera" },
          hcsRef: null,
          agentUsed: "truthforge-carrier-001",
        };
      setSubmitResult({ ...mock, carrierName, documents: uploadedDocs });
    } else {
      try {
        const res = await fetch(`${API_BASE}/api/v1/carrier/verify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ carrierName, shipmentId, documents: uploadedDocs }),
        });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const data = await res.json();
        setSubmitResult(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Verification request failed. Check backend connection.");
      }
    }
    setIsSubmitting(false);
  };

  const handleSchedulePickup = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(10, 0, 0, 0);
    const formatted = tomorrow.toLocaleString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
    setPickupTime(formatted);
    setPickupStatus("scheduled");
    toast({
      title: "Pickup Scheduled",
      description: `FedEx pickup confirmed for ${formatted}`,
    });
  };

  const handleReset = () => {
    setSubmitResult(null);
    setCarrierName("");
    setShipmentId("");
    setUploadedDocs([]);
    setError("");
    setPickupStatus("none");
    setPickupTime(null);
  };

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div>
        <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
          <Package className="h-5 w-5 text-accent" />
          Carrier Portal
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Upload shipping documents and initiate independent carrier verification on Hedera.
        </p>
        <div className={`inline-flex items-center gap-1.5 mt-2 px-2.5 py-1 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${
          isMockMode ? "border-warning/40 bg-warning/10 text-warning" : "border-success/40 bg-success/10 text-success"
        }`}>
          {isMockMode ? "Mock Mode â€” Simulated Responses" : "Live Mode â€” Connected to Backend"}
        </div>
      </div>

      {/* Result View */}
      {submitResult ? (
        <>
          <VerificationResult result={submitResult} onReset={handleReset} />

          {/* Pickup Scheduling â€” only show after verified status */}
          {submitResult.status === "verified" && pickupStatus === "none" && (
            <div className="rounded-lg border border-accent/30 bg-accent/5 p-5 space-y-3">
              <div className="flex items-center gap-2">
                <Truck className="h-4 w-4 text-accent" />
                <h4 className="text-sm font-heading font-bold text-foreground">Ready for Pickup</h4>
              </div>
              <p className="text-xs text-muted-foreground">
                Shipment verified and pre-cleared. Schedule a FedEx pickup for the next available window.
              </p>
              <button
                onClick={handleSchedulePickup}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-accent bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors"
              >
                <CalendarCheck className="h-3.5 w-3.5" />
                Schedule Pickup
              </button>
            </div>
          )}

          {pickupStatus === "scheduled" && pickupTime && (
            <div className="rounded-lg border border-success/30 bg-success/5 p-5">
              <div className="flex items-start gap-3">
                <div className="h-8 w-8 rounded-full bg-success/15 border border-success/20 flex items-center justify-center shrink-0">
                  <CalendarCheck className="h-4 w-4 text-success" />
                </div>
                <div>
                  <h4 className="text-sm font-heading font-bold text-foreground">Pickup Confirmed</h4>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Scheduled for: <span className="font-medium text-foreground">{pickupTime}</span>
                  </p>
                  <p className="text-[10px] text-muted-foreground mt-1.5">
                    Tracking updates will appear here when the shipment is in transit.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Show pickup option for pending too â€” but with different message */}
          {submitResult.status === "pending" && pickupStatus === "none" && (
            <div className="rounded-lg border border-warning/30 bg-warning/5 p-4">
              <p className="text-xs text-warning font-medium">
                Verification pending â€” pickup scheduling will be available once verification is confirmed.
              </p>
            </div>
          )}
        </>
      ) : (
        <>
          {/* Submission Form */}
          <div className="rounded-lg border border-border bg-card p-5 shadow-card space-y-4">
            <div className="flex items-center gap-2 mb-1">
              <Truck className="h-4 w-4 text-accent" />
              <h3 className="text-sm font-heading font-bold text-foreground">Carrier Details</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-foreground block mb-1.5">Carrier Name *</label>
                <input
                  type="text"
                  value={carrierName}
                  onChange={e => setCarrierName(e.target.value)}
                  placeholder="e.g. Maersk, FedEx, MSC"
                  className="w-full rounded border border-input bg-secondary/30 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-foreground block mb-1.5">Shipment ID *</label>
                <input
                  type="text"
                  value={shipmentId}
                  onChange={e => setShipmentId(e.target.value.toUpperCase())}
                  placeholder="e.g. SHP-8821A"
                  className="w-full rounded border border-input bg-secondary/30 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent font-mono"
                />
              </div>
            </div>
          </div>

          {/* Document Upload */}
          <div className="rounded-lg border border-border bg-card p-5 shadow-card space-y-4">
            <div className="flex items-center gap-2 mb-1">
              <Upload className="h-4 w-4 text-accent" />
              <h3 className="text-sm font-heading font-bold text-foreground">Document Upload</h3>
            </div>
            <div className="flex gap-2">
              <select
                value={selectedDocType}
                onChange={e => setSelectedDocType(e.target.value)}
                className="flex-1 rounded border border-input bg-secondary/30 px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
              >
                {ACCEPTED_DOC_TYPES.map(d => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
              <button
                onClick={handleAddDoc}
                className="px-4 py-2 rounded border border-accent bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors"
              >
                + Add
              </button>
            </div>
            {uploadedDocs.length > 0 ? (
              <div className="space-y-2">
                {uploadedDocs.map((doc, i) => (
                  <div key={i} className="flex items-center justify-between rounded border border-border bg-secondary/30 px-3 py-2">
                    <div className="flex items-center gap-2">
                      <FileText className="h-3.5 w-3.5 text-accent shrink-0" />
                      <span className="text-xs text-foreground truncate">{doc.name}</span>
                      <span className="text-[10px] text-muted-foreground">{doc.size}</span>
                    </div>
                    <button onClick={() => handleRemoveDoc(i)} aria-label="Remove document" className="text-muted-foreground hover:text-destructive transition-colors ml-2">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground italic">No documents added yet. Select a type and click + Add.</p>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="rounded border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full py-3 rounded-lg border border-accent bg-accent/10 text-accent text-sm font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <><RefreshCw className="h-4 w-4 animate-spin" /> Submitting Verification...</>
            ) : (
              <><Upload className="h-4 w-4" /> Submit for Verification</>
            )}
          </button>
        </>
      )}

      {/* Past Verifications */}
      <PastVerifications isMockMode={isMockMode} />
    </div>
  );
};

const VerificationResult = ({ result, onReset }: { result: CarrierVerification; onReset: () => void }) => {
  const cfg = statusConfig[result.status];
  const StatusIcon = cfg.icon;

  return (
    <div className={`rounded-xl border-2 p-6 ${cfg.bg}`}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-sm font-heading font-bold text-foreground">Verification Submitted</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Carrier-initiated verification record</p>
        </div>
        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${cfg.color} ${cfg.bg}`}>
          <StatusIcon className="h-3 w-3" />
          {cfg.label}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        {[
          { label: "Shipment ID", value: result.shipmentId, mono: true },
          { label: "Carrier", value: result.carrierName },
          { label: "Submitted", value: result.submittedAt },
          { label: "Agent Used", value: result.agentUsed, mono: true },
        ].map(item => (
          <div key={item.label} className="rounded border border-border bg-secondary/30 px-3 py-2">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">{item.label}</span>
            <span className={`text-xs font-medium text-foreground ${item.mono ? "font-mono" : ""}`}>{item.value}</span>
          </div>
        ))}
      </div>

      {result.documents.length > 0 && (
        <div className="rounded border border-border bg-secondary/30 px-3 py-3 mb-4">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-2">Documents ({result.documents.length})</span>
          <div className="space-y-1">
            {result.documents.map((doc, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <CheckCircle className="h-3 w-3 text-success shrink-0" />
                <span className="text-foreground">{doc.name}</span>
                <span className="text-muted-foreground">{doc.type}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between rounded border border-border bg-secondary/30 px-3 py-2 mb-4">
        <div>
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Verification Fee</span>
          <span className="text-sm font-heading font-bold text-accent">{result.verificationFee.amount} {result.verificationFee.currency}</span>
        </div>
        <div className="text-right">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Network</span>
          <span className="text-xs text-foreground">{result.verificationFee.paymentNetwork}</span>
        </div>
      </div>

      {result.hcsRef && (
        <div className="rounded border border-accent/30 bg-accent/5 px-3 py-2 mb-4">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">HCS Reference</span>
          <span className="font-mono text-xs text-accent break-all">{result.hcsRef}</span>
        </div>
      )}

      <button onClick={onReset} className="w-full py-2 rounded border border-border text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
        Submit Another Verification
      </button>
    </div>
  );
};

const PastVerifications = ({ isMockMode }: { isMockMode: boolean }) => {
  const verifications = isMockMode ? mockCarrierVerifications : [];

  if (verifications.length === 0 && !isMockMode) {
    return (
      <div className="rounded-lg border border-border bg-card p-5 shadow-card">
        <h3 className="text-sm font-heading font-bold text-foreground mb-2">Past Verifications</h3>
        <p className="text-xs text-muted-foreground">No verifications found. Connect to backend to load live data.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card p-5 shadow-card">
      <h3 className="text-sm font-heading font-bold text-foreground mb-3">Past Verifications</h3>
      <div className="space-y-2">
        {verifications.map(v => {
          const cfg = statusConfig[v.status];
          const StatusIcon = cfg.icon;
          return (
            <div key={v.id} className="flex items-center justify-between rounded border border-border bg-secondary/30 px-3 py-2.5">
              <div className="flex items-center gap-3">
                <Truck className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                <div>
                  <span className="text-xs font-mono font-medium text-foreground">{v.shipmentId}</span>
                  <span className="text-[10px] text-muted-foreground ml-2">{v.carrierName}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[10px] text-muted-foreground hidden sm:block">{v.submittedAt}</span>
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${cfg.color} ${cfg.bg}`}>
                  <StatusIcon className="h-2.5 w-2.5" />
                  {cfg.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CarrierPortal;
