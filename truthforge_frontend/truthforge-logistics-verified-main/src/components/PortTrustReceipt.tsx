import { useState, useEffect } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import { PortTrustReceipt as ReceiptType } from "@/lib/mock-data";
import {
  Shield, CheckCircle, AlertTriangle, ExternalLink,
  FileCheck, Users, Stamp, DollarSign, CreditCard, Link,
  Truck, Ship, Plane, QrCode,
} from "lucide-react";

// ── New canonical props interface (as specified) ───────────────────────────
export interface PortTrustReceiptProps {
  shipmentId: string;
  status: "PRE_CLEARED" | "FLAGGED";
  hcsTopicId: string;
  transactionId: string;
  timestamp: string;
  verificationFee?: number;
  transportMode: "SEA" | "AIR" | "LAND";
}

// ── Legacy receipt prop (backward compat with portals) ─────────────────────
interface LegacyReceiptProps {
  receipt: ReceiptType;
  carrierName?: string;
  documents?: { name: string; type: string }[];
  verificationType?: "merchant" | "carrier";
}

type Props = PortTrustReceiptProps | LegacyReceiptProps;

// ── Mock fallback values ───────────────────────────────────────────────────
const MOCK_DEFAULTS: PortTrustReceiptProps = {
  shipmentId: "SHP-MOCK-001",
  status: "PRE_CLEARED",
  hcsTopicId: "0.0.8161244",
  transactionId: "0.0.4521983-1719329922-000000001",
  timestamp: "2026-03-08 14:02 UTC",
  verificationFee: 0.24,
  transportMode: "SEA",
};

// ── QR Code via Google Charts (no library needed) ──────────────────────────
const QRCodeImage = ({ value, size = 112 }: { value: string; size?: number }) => {
  const [failed, setFailed] = useState(false);
  const src = `https://chart.googleapis.com/chart?cht=qr&chs=${size}x${size}&chl=${encodeURIComponent(value)}&choe=UTF-8&chld=M|2`;

  if (failed) {
    return (
      <div
        style={{ width: size, height: size }}
        className="bg-white rounded flex items-center justify-center border border-border"
      >
        <QrCode className="h-10 w-10 text-muted-foreground" />
      </div>
    );
  }
  return (
    <img
      src={src}
      alt="Verification QR Code"
      width={size}
      height={size}
      className="rounded border border-border bg-white"
      onError={() => setFailed(true)}
    />
  );
};

// ── Normalize: convert either prop shape to canonical PortTrustReceiptProps ─
function normalize(props: Props, isMockMode: boolean): PortTrustReceiptProps & {
  agentSignatures?: { agentName: string; agentId: string }[];
  carrierName?: string;
  documents?: { name: string; type: string }[];
  verificationFees?: ReceiptType["verificationFees"];
  paymentTransaction?: ReceiptType["paymentTransaction"];
} {
  if ("receipt" in props) {
    const r = props.receipt;
    const txId = r.paymentTransaction?.transactionId ?? r.hederaTxRef;
    const hcsTopicId = r.hederaTxRef.includes("@")
      ? r.hederaTxRef.split("@")[0]
      : r.hederaTxRef;
    const rawMode = (r as any).transportMode as string | undefined;
    const transportMode: "SEA" | "AIR" | "LAND" =
      rawMode === "air" || rawMode === "AIR" ? "AIR"
      : rawMode === "land" || rawMode === "LAND" ? "LAND"
      : "SEA";
    return {
      shipmentId: r.shipmentId,
      status: r.clearanceStatus === "flagged" ? "FLAGGED" : "PRE_CLEARED",
      hcsTopicId,
      transactionId: txId,
      timestamp: r.paymentTransaction?.timestamp ?? r.issuedAt,
      verificationFee: r.verificationFees?.total,
      transportMode,
      agentSignatures: r.agentSignatures,
      carrierName: props.carrierName,
      documents: props.documents,
      verificationFees: r.verificationFees,
      paymentTransaction: r.paymentTransaction,
    };
  }

  // Direct PortTrustReceiptProps — fill missing fields with mock in MOCK_MODE
  if (isMockMode) {
    return {
      ...MOCK_DEFAULTS,
      ...Object.fromEntries(
        Object.entries(props).filter(([, v]) => v !== undefined && v !== "")
      ),
    } as ReturnType<typeof normalize>;
  }
  return props as ReturnType<typeof normalize>;
}

const TransportIcon = ({ mode }: { mode: "SEA" | "AIR" | "LAND" }) => {
  if (mode === "AIR") return <Plane className="h-3.5 w-3.5 text-accent" />;
  if (mode === "LAND") return <Truck className="h-3.5 w-3.5 text-accent" />;
  return <Ship className="h-3.5 w-3.5 text-accent" />;
};

// ── Main component ──────────────────────────────────────────────────────────
const PortTrustReceipt = (props: Props) => {
  const { isMockMode } = useMockMode();
  const [issued, setIssued] = useState(false);

  const data = normalize(props, isMockMode);

  // In LIVE_MODE, don't render if critical fields are missing
  if (!isMockMode && (!data.transactionId || !data.hcsTopicId || !data.shipmentId)) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 text-center text-sm text-muted-foreground">
        Receipt data unavailable — waiting for live Hedera confirmation.
      </div>
    );
  }

  const isCleared = data.status === "PRE_CLEARED";
  const statusColor = isCleared ? "text-success" : "text-destructive";
  const statusBg = isCleared
    ? "border-success/30 bg-success/5"
    : "border-destructive/30 bg-destructive/5";
  const StatusIcon = isCleared ? CheckCircle : AlertTriangle;
  const statusLabel = isCleared ? "VERIFIED — PRE-ARRIVAL" : "FLAGGED EXCEPTION";

  const verifyUrl = `${window.location.origin}/verify?shipmentId=${encodeURIComponent(data.shipmentId)}&tx=${encodeURIComponent(data.transactionId)}`;
  const hashscanUrl = `https://hashscan.io/testnet/transaction/${data.transactionId}`;

  return (
    <div className={`relative rounded-xl border-2 ${statusBg} p-5`}>

      {/* ── Issued stamp banner ── */}
      {issued && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-success/40 bg-success/10 px-4 py-2">
          <Stamp className="h-4 w-4 text-success shrink-0" />
          <span className="text-xs font-heading font-bold text-success">
            Receipt Issued &amp; Anchored to Hedera — Present to port authorities, carrier ops, and customs.
          </span>
        </div>
      )}

      {/* ── Header ── */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <Shield className="h-4 w-4 text-accent" />
            <span className="text-sm font-heading font-bold text-foreground">Port Trust Receipt</span>
          </div>
          <span className="text-xs text-muted-foreground">Pre-Arrival Clearance Record</span>
        </div>
        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-[10px] font-heading font-bold uppercase tracking-wider border ${statusColor} ${statusBg}`}>
          <StatusIcon className="h-3 w-3" />
          {statusLabel}
        </span>
      </div>

      {/* ── Core fields grid ── */}
      <div className="rounded-lg border border-border bg-secondary/30 p-4 mb-4 space-y-3">

        {/* Row 1: Shipment ID + Status */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Shipment ID</span>
            <span className="font-mono text-sm font-bold text-foreground">{data.shipmentId}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Status</span>
            <span className={`text-sm font-heading font-bold ${statusColor}`}>
              {isCleared ? "✅ Pre-Cleared" : "🚩 Flagged"}
            </span>
          </div>
        </div>

        {/* Row 2: Transport Mode + Network */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Transport Mode</span>
            <span className="flex items-center gap-1.5 text-sm font-medium text-foreground capitalize">
              <TransportIcon mode={data.transportMode} />
              {data.transportMode.charAt(0) + data.transportMode.slice(1).toLowerCase()}
            </span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Hedera Network</span>
            <span className="text-sm font-medium text-foreground">Testnet</span>
          </div>
        </div>

        {/* Row 3: HCS Topic ID */}
        <div>
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">HCS Topic ID</span>
          <span className="font-mono text-xs text-accent">{data.hcsTopicId}</span>
        </div>

        {/* Row 4: Transaction ID */}
        <div>
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Transaction ID</span>
          <span className="font-mono text-xs text-accent break-all">{data.transactionId}</span>
        </div>

        {/* Row 5: Timestamp + Fee */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Timestamp</span>
            <span className="font-mono text-xs text-foreground">{data.timestamp}</span>
          </div>
          {data.verificationFee !== undefined && (
            <div>
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Verification Fee</span>
              <span className="flex items-center gap-1 text-sm font-bold text-accent">
                <DollarSign className="h-3 w-3" />
                {data.verificationFee.toFixed(2)} HBAR
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ── Verification Fee breakdown (if legacy receipt has it) ── */}
      {data.verificationFees && (
        <div className="rounded-lg border border-border bg-secondary/30 p-4 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <DollarSign className="h-4 w-4 text-accent" />
            <h4 className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">Fee Breakdown</h4>
          </div>
          <div className="space-y-1.5 mb-3">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Shipment Verification:</span>
              <span className="font-mono text-foreground">{data.verificationFees.shipmentVerification.toFixed(2)} {data.verificationFees.currency}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Container Checks:</span>
              <span className="font-mono text-foreground">{data.verificationFees.containerChecks.toFixed(2)} {data.verificationFees.currency}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Network Recording Fee:</span>
              <span className="font-mono text-foreground">{data.verificationFees.networkRecordingFee.toFixed(2)} {data.verificationFees.currency}</span>
            </div>
            <div className="border-t border-border pt-2 flex justify-between text-sm font-heading font-bold">
              <span className="text-foreground">Total Paid:</span>
              <span className="text-accent">{data.verificationFees.total.toFixed(2)} {data.verificationFees.currency}</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Payment Transaction (legacy) ── */}
      {data.paymentTransaction && (
        <div className="rounded-lg border border-accent/30 bg-accent/5 p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <CreditCard className="h-4 w-4 text-accent" />
            <h4 className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">Payment Transaction</h4>
          </div>
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs">
              <span className="text-muted-foreground">Status:</span>
              <span className={`font-bold uppercase ${data.paymentTransaction.status === "confirmed" ? "text-success" : data.paymentTransaction.status === "pending" ? "text-warning" : "text-destructive"}`}>
                {data.paymentTransaction.status}
              </span>
            </div>
            {data.paymentTransaction.walletUsed && (
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Wallet:</span>
                <span className="text-foreground">{data.paymentTransaction.walletUsed}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Hedera Network Record ── */}
      <div className="rounded-lg border border-border bg-secondary/30 p-4 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <Link className="h-4 w-4 text-accent" />
          <h4 className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">Hedera Network Record</h4>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Network</span>
            <span className="text-xs font-medium text-foreground">Hedera Testnet</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">HCS Topic ID</span>
            <span className="font-mono text-xs text-accent">{data.hcsTopicId}</span>
          </div>
        </div>
        <div className="rounded border border-border bg-secondary/50 px-3 py-2 mb-3">
          <span className="text-[10px] text-muted-foreground block mb-0.5">Transaction ID:</span>
          <span className="font-mono text-xs text-accent break-all">{data.transactionId}</span>
        </div>
        {/* MANDATORY HashScan link */}
        <a
          href={hashscanUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-accent/40 bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors w-full justify-center"
        >
          <ExternalLink className="h-3.5 w-3.5" />
          View on HashScan
        </a>
      </div>

      {/* ── Agent Signatures (legacy) ── */}
      {data.agentSignatures && data.agentSignatures.length > 0 && (
        <div className="rounded-lg border border-border bg-secondary/30 p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Users className="h-4 w-4 text-accent" />
            <h4 className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">
              HOL-Registered Agent Signatures ({data.agentSignatures.length}/5)
            </h4>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {data.agentSignatures.map((sig, i) => (
              <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-border bg-secondary/50 text-[10px] font-mono text-muted-foreground">
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                {sig.agentName.split(" ")[0].substring(0, 4).toUpperCase()}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ── Documents (legacy) ── */}
      {data.documents && data.documents.length > 0 && (
        <div className="rounded-lg border border-border bg-secondary/30 px-4 py-3 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <FileCheck className="h-4 w-4 text-accent" />
            <h4 className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">
              Submitted Documents ({data.documents.length})
            </h4>
          </div>
          <div className="space-y-1.5">
            {data.documents.map((doc, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <FileCheck className="h-3 w-3 text-success shrink-0" />
                <span className="text-foreground truncate">{doc.name}</span>
                <span className="text-muted-foreground shrink-0">{doc.type}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── QR Code ── */}
      <div className="rounded-lg border border-border bg-secondary/30 p-4 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <QrCode className="h-4 w-4 text-accent" />
          <h4 className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">Port-Scannable Verification</h4>
        </div>
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <div className="shrink-0">
            <QRCodeImage value={verifyUrl} size={112} />
          </div>
          <div className="flex-1 space-y-2 text-center sm:text-left">
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              Scan to verify this shipment's clearance status. Port officers can independently confirm authenticity.
            </p>
            <div className="rounded border border-border bg-secondary/50 px-2 py-1.5">
              <span className="text-[9px] text-muted-foreground block mb-0.5 uppercase tracking-wider">Verification URL</span>
              <span className="font-mono text-[10px] text-accent break-all">{verifyUrl}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Issue Receipt button ── */}
      <div className="rounded-lg border border-accent/30 bg-accent/5 p-4">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Action</div>
            <div className="text-sm font-heading font-bold text-foreground">
              {issued ? "Receipt Issued & Anchored" : "Issue Port Trust Receipt"}
            </div>
          </div>
          <button
            onClick={() => setIssued(true)}
            disabled={issued}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-xs font-heading font-bold uppercase tracking-wider transition-colors ${
              issued
                ? "border-success/40 bg-success/10 text-success cursor-default"
                : "border-accent bg-accent text-white hover:bg-accent/80"
            }`}
          >
            <Stamp className="h-3.5 w-3.5" />
            {issued ? "Issued ✓" : "Issue Receipt"}
          </button>
        </div>
      </div>

      <p className="text-[10px] text-muted-foreground mt-4 leading-relaxed">
        {isMockMode ? "Preview mode — simulated Hedera values. " : ""}
        Issued receipt serves as port-readable clearance proof. Includes agent signatures and consensus reference for independent verification.
      </p>
    </div>
  );
};

export default PortTrustReceipt;
