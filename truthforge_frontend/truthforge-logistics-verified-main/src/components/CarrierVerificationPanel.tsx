import { useState } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import { useToast } from "@/hooks/use-toast";
import { API_BASE } from "@/lib/api-client";
import {
  Upload, Ship, Plane, Truck, FileText, X, RefreshCw,
  CheckCircle, AlertTriangle, Clock, Info
} from "lucide-react";

export type TransportMode = "sea" | "air" | "land";

export interface VerificationResult {
  shipmentId: string;
  status: "verified" | "pending" | "flagged";
  transportMode: TransportMode;
  aiReasoning: string;
  hcsRef?: string;
  containers?: CargoItem[];
}

export interface CargoItem {
  id: string;
  count?: number;
  status: "verified" | "flagged" | "pending";
  risk: "low" | "medium" | "high";
}

interface CarrierVerificationPanelProps {
  onVerified?: (result: VerificationResult) => void;
  disabled?: boolean;
  loadingLabel?: string;
}

const DOC_TYPES: Record<TransportMode, { value: string; label: string }[]> = {
  sea: [
    { value: "bol", label: "Bill of Lading (BOL)" },
    { value: "commercial_invoice", label: "Commercial Invoice" },
    { value: "packing_list", label: "Packing List" },
  ],
  air: [
    { value: "awb", label: "Air Waybill (AWB)" },
    { value: "commercial_invoice", label: "Commercial Invoice" },
    { value: "cargo_manifest", label: "Cargo Manifest" },
  ],
  land: [
    { value: "cmr", label: "CMR / Delivery Note" },
    { value: "commercial_invoice", label: "Commercial Invoice" },
    { value: "packing_list", label: "Packing List" },
  ],
};

const MOCK_RESULTS: Record<TransportMode, VerificationResult> = {
  sea: {
    shipmentId: "SHP-8821A",
    status: "verified",
    transportMode: "sea",
    aiReasoning: "All BOL documents verified. Container manifest matches declared cargo. No sanctions hits detected.",
    hcsRef: "hcs-carrier-001#1741437900",
    containers: [
      { id: "MSCU12345", status: "verified", risk: "low" },
      { id: "MSCU12346", status: "verified", risk: "low" },
      { id: "MSCU12347", status: "flagged", risk: "high" },
    ],
  },
  air: {
    shipmentId: "SHP-8824D",
    status: "verified",
    transportMode: "air",
    aiReasoning: "Air Waybill validated. Cargo units match declared manifest. FedEx AWB cross-referenced successfully.",
    hcsRef: "hcs-carrier-001#1741370400",
    containers: [
      { id: "CARGO-001", count: 12, status: "verified", risk: "low" },
      { id: "CARGO-002", count: 8, status: "verified", risk: "low" },
    ],
  },
  land: {
    shipmentId: "SHP-LAND-001",
    status: "pending",
    transportMode: "land",
    aiReasoning: "CMR document received. Awaiting cross-border customs confirmation before final clearance.",
    containers: [
      { id: "PALLET-001", count: 4, status: "pending", risk: "low" },
      { id: "PALLET-002", count: 6, status: "verified", risk: "low" },
    ],
  },
};

const CarrierVerificationPanel = ({ onVerified, disabled: externalDisabled, loadingLabel }: CarrierVerificationPanelProps) => {
  const { isMockMode } = useMockMode();
  const { toast } = useToast();

  const [transportMode, setTransportMode] = useState<TransportMode>("sea");
  const [shipmentId, setShipmentId] = useState("");
  const [selectedDocType, setSelectedDocType] = useState(DOC_TYPES.sea[0].value);
  const [uploadedDocs, setUploadedDocs] = useState<{ name: string; type: string }[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState("");

  const modeLabels: Record<TransportMode, string> = {
    sea: "Container List",
    air: "Cargo / Package List",
    land: "Cargo / Pallet List",
  };

  const handleModeChange = (mode: TransportMode) => {
    setTransportMode(mode);
    setSelectedDocType(DOC_TYPES[mode][0].value);
    setUploadedDocs([]);
  };

  const handleAddDoc = () => {
    const label = DOC_TYPES[transportMode].find(d => d.value === selectedDocType)?.label ?? selectedDocType;
    if (uploadedDocs.find(d => d.type === label)) return;
    setUploadedDocs(prev => [...prev, {
      name: `${label.replace(/ /g, "_")}_${shipmentId || "DOC"}.pdf`,
      type: label,
    }]);
  };

  const handleSubmit = async () => {
    setError("");
    if (!shipmentId.trim()) { setError("Shipment ID is required."); return; }
    if (uploadedDocs.length === 0) { setError("Upload at least one document."); return; }
    if (!isMockMode && uploadedDocs.length === 0) {
      setError("Live mode requires real carrier documents (e.g., FedEx AWB).");
      return;
    }

    setIsSubmitting(true);

    if (isMockMode) {
      await new Promise(r => setTimeout(r, 1400));
      const mockResult = { ...MOCK_RESULTS[transportMode], shipmentId: shipmentId.toUpperCase() };
      setResult(mockResult);
      onVerified?.(mockResult);
      toast({ title: "Verification Complete", description: `${shipmentId.toUpperCase()} – ${mockResult.status}` });
    } else {
      try {
        const res = await fetch(`${API_BASE}/api/v1/carrier/verify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ shipmentId, transportMode, documents: uploadedDocs }),
        });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const data: VerificationResult = await res.json();
        setResult(data);
        onVerified?.(data);
        toast({ title: "Verification Complete", description: `${shipmentId} – ${data.status}` });
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Verification failed. Check backend connection.");
      }
    }

    setIsSubmitting(false);
  };

  const handleReset = () => {
    setResult(null);
    setShipmentId("");
    setUploadedDocs([]);
    setError("");
  };

  return (
    <div className="rounded-xl border border-border bg-card shadow-card p-5 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-heading font-bold text-foreground flex items-center gap-2">
            <Upload className="h-4 w-4 text-accent" />
            Upload & Verify Shipment
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            {isMockMode
              ? "Mock mode – simulated verification with demo documents."
              : "Live mode requires real carrier documents (e.g., FedEx AWB)."}
          </p>
        </div>
        {!isMockMode && (
          <div className="flex items-center gap-1.5 text-xs text-warning border border-warning/30 bg-warning/5 px-2.5 py-1 rounded">
            <Info className="h-3.5 w-3.5" />
            Live Mode
          </div>
        )}
      </div>

      {/* Transport Mode Toggle */}
      <div>
        <label className="text-xs font-heading font-bold text-muted-foreground uppercase tracking-wider block mb-2">
          Transport Mode
        </label>
        <div className="grid grid-cols-3 gap-2">
          {(["sea", "air", "land"] as TransportMode[]).map(mode => {
            const Icon = mode === "sea" ? Ship : mode === "air" ? Plane : Truck;
            return (
              <button
                key={mode}
                type="button"
                onClick={() => handleModeChange(mode)}
                className={`flex items-center justify-center gap-2 py-2 rounded-lg border text-xs font-medium transition-all ${
                  transportMode === mode
                    ? "border-accent bg-accent/10 text-accent"
                    : "border-border bg-secondary/30 text-muted-foreground hover:border-accent/40"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            );
          })}
        </div>
        <p className="text-[10px] text-muted-foreground mt-1.5">
          Mode: <span className="text-foreground font-medium">{modeLabels[transportMode]}</span>
        </p>
      </div>

      {result ? (
        <VerificationResultView result={result} onReset={handleReset} />
      ) : (
        <>
          {/* Shipment ID */}
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

          {/* Document Upload */}
          <div>
            <label className="text-xs font-medium text-foreground block mb-1.5">
              Documents ({DOC_TYPES[transportMode].map(d => d.label).join(", ")})
            </label>
            <div className="flex gap-2">
              <select
                value={selectedDocType}
                onChange={e => setSelectedDocType(e.target.value)}
                className="flex-1 rounded border border-input bg-secondary/30 px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
              >
                {DOC_TYPES[transportMode].map(d => (
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
              <div className="mt-2 space-y-1.5">
                {uploadedDocs.map((doc, i) => (
                  <div key={i} className="flex items-center justify-between rounded border border-border bg-secondary/30 px-3 py-2">
                    <div className="flex items-center gap-2">
                      <FileText className="h-3.5 w-3.5 text-accent shrink-0" />
                      <span className="text-xs text-foreground truncate">{doc.name}</span>
                    </div>
                    <button onClick={() => setUploadedDocs(prev => prev.filter((_, j) => j !== i))} className="text-muted-foreground hover:text-destructive transition-colors ml-2">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground italic mt-2">No documents added. Select a type and click + Add.</p>
            )}
          </div>

          {error && (
            <div className="rounded border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={isSubmitting || externalDisabled}
            className="w-full py-3 rounded-lg border border-accent bg-accent/10 text-accent text-sm font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {(isSubmitting || externalDisabled) ? (
              <><RefreshCw className="h-4 w-4 animate-spin" /> {loadingLabel ?? "Verifying..."}</>
            ) : (
              <><Upload className="h-4 w-4" /> Upload & Verify Shipment</>
            )}
          </button>
        </>
      )}
    </div>
  );
};

const statusConfig = {
  verified: { icon: CheckCircle, color: "text-success", bg: "bg-success/10 border-success/30", label: "Pre-Cleared" },
  pending: { icon: Clock, color: "text-warning", bg: "bg-warning/10 border-warning/30", label: "Pending" },
  flagged: { icon: AlertTriangle, color: "text-destructive", bg: "bg-destructive/10 border-destructive/30", label: "Flagged" },
};

const VerificationResultView = ({ result, onReset }: { result: VerificationResult; onReset: () => void }) => {
  const cfg = statusConfig[result.status];
  const StatusIcon = cfg.icon;

  return (
    <div className={`rounded-xl border-2 p-5 space-y-4 ${cfg.bg}`}>
      <div className="flex items-center justify-between">
        <div>
          <span className="font-mono text-sm font-bold text-foreground">{result.shipmentId}</span>
          <p className="text-xs text-muted-foreground capitalize mt-0.5">{result.transportMode} freight</p>
        </div>
        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${cfg.color} ${cfg.bg}`}>
          <StatusIcon className="h-3 w-3" />
          {cfg.label}
        </span>
      </div>

      {/* AI Reasoning */}
      <div className="rounded border border-border bg-secondary/30 px-3 py-3">
        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">AI Reasoning</span>
        <p className="text-xs text-foreground leading-relaxed">{result.aiReasoning}</p>
      </div>

      {/* HCS Ref */}
      {result.hcsRef && (
        <div className="rounded border border-accent/30 bg-accent/5 px-3 py-2">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">Hedera Transaction</span>
          <span className="font-mono text-xs text-accent break-all">{result.hcsRef}</span>
        </div>
      )}

      <button onClick={onReset} className="w-full py-2 rounded border border-border text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
        Verify Another Shipment
      </button>
    </div>
  );
};

export default CarrierVerificationPanel;
