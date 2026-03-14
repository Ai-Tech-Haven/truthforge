import { PortTrustReceipt as ReceiptType } from "@/lib/mock-data";
import { Shield, CheckCircle, Clock, AlertTriangle, Link, FileCheck, Users, Stamp, DollarSign, CreditCard, Truck, Package } from "lucide-react";

interface ExtendedReceiptProps {
  receipt: ReceiptType;
  carrierName?: string;
  documents?: { name: string; type: string }[];
  verificationType?: "merchant" | "carrier";
}

const statusConfig = {
  cleared: { icon: CheckCircle, color: "text-success", bg: "border-success/30 bg-success/5", label: "VERIFIED — PRE-ARRIVAL" },
  pending: { icon: Clock, color: "text-warning", bg: "border-warning/30 bg-warning/5", label: "PENDING CONSENSUS" },
  flagged: { icon: AlertTriangle, color: "text-destructive", bg: "border-destructive/30 bg-destructive/5", label: "FLAGGED EXCEPTION" },
};

const PortTrustReceipt = ({ receipt, carrierName, documents, verificationType = "merchant" }: ExtendedReceiptProps) => {
  const cfg = statusConfig[receipt.clearanceStatus];
  const StatusIcon = cfg.icon;

  return (
    <div className={`rounded-xl border-2 ${cfg.bg} p-6 hover:shadow-elevated transition-all duration-200`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-base">🧾</span>
            <span className="text-sm font-heading font-bold text-foreground">Port Trust Receipt</span>
          </div>
          <span className="text-xs text-muted-foreground">Pre-Arrival Clearance Record</span>
        </div>
        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-[10px] font-heading font-bold uppercase tracking-wider border ${cfg.color} ${cfg.bg}`}>
          <StatusIcon className="h-3 w-3" />
          {cfg.label}
        </span>
      </div>

      {/* Shipment Reference */}
      <div className="rounded-lg border border-border bg-secondary/30 px-4 py-3 mb-5">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Shipment Reference</span>
            <div className="font-mono text-sm font-bold text-foreground mt-0.5">{receipt.shipmentId}</div>
          </div>
          <div className="text-right">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Clearance Status</span>
            <div className={`text-sm font-heading font-bold mt-0.5 ${cfg.color}`}>
              {receipt.clearanceStatus === "cleared" ? "✅ Verified — Pre-Arrival" : cfg.label}
            </div>
          </div>
        </div>
      </div>

      {/* Carrier / Verification Type Info */}
      {(carrierName || verificationType === "carrier") && (
        <div className="rounded-lg border border-border bg-secondary/30 px-4 py-3 mb-5">
          <div className="flex items-center gap-2 mb-2">
            <Truck className="h-4 w-4 text-accent" />
            <h4 className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">
              {verificationType === "carrier" ? "Carrier-Initiated Verification" : "Merchant Verification"}
            </h4>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {carrierName && (
              <div>
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Carrier</span>
                <span className="text-sm font-medium text-foreground">{carrierName}</span>
              </div>
            )}
            <div>
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Type</span>
              <span className="text-sm font-medium text-foreground capitalize">{verificationType}</span>
            </div>
          </div>
        </div>
      )}

      {/* Submitted Documents */}
      {documents && documents.length > 0 && (
        <div className="rounded-lg border border-border bg-secondary/30 px-4 py-3 mb-5">
          <div className="flex items-center gap-2 mb-2">
            <Package className="h-4 w-4 text-accent" />
            <h4 className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">
              Submitted Documents ({documents.length})
            </h4>
          </div>
          <div className="space-y-1.5">
            {documents.map((doc, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <FileCheck className="h-3 w-3 text-success shrink-0" />
                <span className="text-foreground truncate">{doc.name}</span>
                <span className="text-muted-foreground shrink-0">{doc.type}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verification Fee Summary */}
      {receipt.verificationFees && (
        <div className="rounded-lg border border-border bg-secondary/30 p-4 mb-5">
          <div className="flex items-center gap-2 mb-3">
            <DollarSign className="h-4 w-4 text-accent" />
            <h4 className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">Verification Fee Summary</h4>
          </div>
          
          <div className="space-y-2 mb-3">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Shipment Verification:</span>
              <span className="text-foreground font-mono">${receipt.verificationFees.shipmentVerification.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Container Checks:</span>
              <span className="text-foreground font-mono">${receipt.verificationFees.containerChecks.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Network Recording Fee:</span>
              <span className="text-foreground font-mono">${receipt.verificationFees.networkRecordingFee.toFixed(2)}</span>
            </div>
            <div className="border-t border-border pt-2 mt-2 flex justify-between text-sm font-heading font-bold">
              <span className="text-foreground">Total Paid:</span>
              <span className="text-accent">${receipt.verificationFees.total.toFixed(2)}</span>
            </div>
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-border">
            <div>
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Payment Network</span>
              <span className="text-xs text-foreground font-medium">{receipt.verificationFees.paymentNetwork}</span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Currency</span>
              <span className="text-xs text-foreground font-medium">{receipt.verificationFees.currency}</span>
            </div>
          </div>
        </div>
      )}

      {/* Payment Transaction Details */}
      {receipt.paymentTransaction && (
        <div className="rounded-lg border border-accent/30 bg-accent/5 p-4 mb-5">
          <div className="flex items-center gap-2 mb-3">
            <CreditCard className="h-4 w-4 text-accent" />
            <h4 className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">Payment Transaction</h4>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs text-muted-foreground">Transaction Status:</span>
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-heading font-bold uppercase tracking-wider ${
                receipt.paymentTransaction.status === 'confirmed' 
                  ? 'bg-success/20 text-success border border-success/30' 
                  : receipt.paymentTransaction.status === 'pending'
                  ? 'bg-warning/20 text-warning border border-warning/30'
                  : 'bg-destructive/20 text-destructive border border-destructive/30'
              }`}>
                {receipt.paymentTransaction.status === 'confirmed' && <CheckCircle className="h-2.5 w-2.5" />}
                {receipt.paymentTransaction.status === 'pending' && <Clock className="h-2.5 w-2.5" />}
                {receipt.paymentTransaction.status === 'failed' && <AlertTriangle className="h-2.5 w-2.5" />}
                {receipt.paymentTransaction.status}
              </span>
            </div>

            {receipt.paymentTransaction.walletUsed && (
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Wallet Used:</span>
                <span className="text-foreground">{receipt.paymentTransaction.walletUsed}</span>
              </div>
            )}

            <div className="rounded border border-border bg-secondary/30 px-3 py-2 mt-2">
              <span className="text-[10px] text-muted-foreground block mb-0.5">Transaction ID:</span>
              <span className="font-mono text-xs text-accent break-all">{receipt.paymentTransaction.transactionId}</span>
            </div>

            <div className="flex justify-between text-xs pt-1">
              <span className="text-muted-foreground">Timestamp:</span>
              <span className="text-foreground font-mono">{receipt.paymentTransaction.timestamp}</span>
            </div>
          </div>
        </div>
      )}

      {/* Steps */}
      <div className="space-y-4 mb-5">
        {/* Step 1 */}
        <div className="flex items-start gap-3">
          <div className="mt-0.5 h-6 w-6 rounded-full bg-success/15 flex items-center justify-center shrink-0 border border-success/20">
            <FileCheck className="h-3 w-3 text-success" />
          </div>
          <div>
            <div className="text-xs font-heading font-bold text-foreground">1. Document Intake & Validation</div>
            <p className="text-[11px] text-muted-foreground mt-1 leading-relaxed">
              Commercial invoice and bill of lading received and parsed. Document integrity, structure, and required signatures validated.
            </p>
          </div>
        </div>

        {/* Step 2 */}
        <div className="flex items-start gap-3">
          <div className="mt-0.5 h-6 w-6 rounded-full bg-success/15 flex items-center justify-center shrink-0 border border-success/20">
            <Users className="h-3 w-3 text-success" />
          </div>
          <div>
            <div className="text-xs font-heading font-bold text-foreground">2. Authorized Agent Verification</div>
            <div className="text-[10px] text-muted-foreground mt-1 mb-2 font-heading font-bold uppercase tracking-wider">
              HOL-Registered Agent Review ({receipt.agentSignatures.length}/5)
            </div>
            <p className="text-[11px] text-muted-foreground leading-relaxed mb-2">
              Compliance checks completed across the authorized agent set, including origin and routing validation, sanctions and restricted party screening, and consistency across submitted records.
            </p>
            <div className="flex flex-wrap gap-1.5">
              {receipt.agentSignatures.map((sig, i) => (
                <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-border bg-secondary/50 text-[10px] font-mono text-muted-foreground">
                  <span className="h-1.5 w-1.5 rounded-full bg-success" />
                  {sig.agentName.split(" ")[0].substring(0, 4).toUpperCase()}
                </span>
              ))}
            </div>
            <p className="text-[10px] text-muted-foreground mt-2 italic">
              All verification steps completed by registered agents operating within approved scope.
            </p>
          </div>
        </div>

        {/* Step 3 */}
        <div className="flex items-start gap-3">
          <div className="mt-0.5 h-6 w-6 rounded-full bg-accent/15 flex items-center justify-center shrink-0 border border-accent/20">
            <Link className="h-3 w-3 text-accent" />
          </div>
          <div>
            <div className="text-xs font-heading font-bold text-foreground">3. Consensus Record Anchored</div>
            <p className="text-[11px] text-muted-foreground mt-1 leading-relaxed mb-2">
              Verification outcome recorded with an immutable consensus reference. Record establishes ordered, time-stamped proof of verification.
            </p>
            <div className="rounded border border-border bg-secondary/30 px-3 py-2">
              <span className="text-[10px] text-muted-foreground block mb-0.5">Audit Reference:</span>
              <span className="font-mono text-xs text-accent">TX-{receipt.hederaTxRef}</span>
            </div>
          </div>
        </div>

        {/* Step 4 */}
        <div className="flex items-start gap-3">
          <div className="mt-0.5 h-6 w-6 rounded-full bg-success/15 flex items-center justify-center shrink-0 border border-success/20">
            <Stamp className="h-3 w-3 text-success" />
          </div>
          <div>
            <div className="text-xs font-heading font-bold text-foreground">4. Clearance Determination</div>
            <p className="text-[11px] text-muted-foreground mt-1 leading-relaxed">
              All required pre-arrival verification criteria satisfied. Shipment is eligible for expedited port processing upon arrival.
            </p>
          </div>
        </div>
      </div>

      {/* Status + Action */}
      <div className="rounded-lg border border-accent/30 bg-accent/5 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-6">
            <div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Status</div>
              <div className="text-sm font-heading font-bold text-success">Clearance Eligible</div>
            </div>
            <div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Action</div>
              <div className="text-sm font-heading font-bold text-foreground">Issue Port Trust Receipt</div>
            </div>
          </div>
          <button className="px-4 py-2 rounded-lg border border-accent bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors">
            Issue Receipt
          </button>
        </div>
      </div>

      {/* Post-Action Notice */}
      <p className="text-[10px] text-muted-foreground mt-4 leading-relaxed">
        Issued receipt will serve as port-readable clearance proof and may be presented to port authorities, carrier operations, and customs and regulatory bodies. Receipt includes agent signatures and consensus reference for independent verification.
      </p>
    </div>
  );
};

export default PortTrustReceipt;
