import { Verification } from "@/lib/mock-data";
import { CheckCircle, Clock, XCircle, Link } from "lucide-react";

const statusConfig = {
  verified: { icon: CheckCircle, color: "text-success", bg: "bg-success/10", label: "Verified" },
  pending: { icon: Clock, color: "text-warning", bg: "bg-warning/10", label: "Pending" },
  failed: { icon: XCircle, color: "text-destructive", bg: "bg-destructive/10", label: "Failed" },
};

const VerificationRow = ({ v }: { v: Verification }) => {
  const cfg = statusConfig[v.status];
  const Icon = cfg.icon;

  return (
    <tr className="border-b border-border last:border-0 hover:bg-accent/5 transition-colors">
      <td className="py-3 px-4 font-mono text-xs text-foreground whitespace-nowrap">{v.shipmentId}</td>
      <td className="py-3 px-4 text-xs text-foreground whitespace-nowrap">{v.type}</td>
      <td className="py-3 px-4">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium whitespace-nowrap ${cfg.bg} ${cfg.color}`}>
          <Icon className="h-3 w-3 shrink-0" />
          {cfg.label}
        </span>
      </td>
      <td className="py-3 px-4 text-[11px] text-muted-foreground whitespace-nowrap max-w-[140px] truncate" title={v.agent}>{v.agent}</td>
      <td className="py-3 px-4 text-[11px] font-mono text-muted-foreground whitespace-nowrap">{v.timestamp}</td>
      <td className="py-3 px-4">
        {v.hcsProof !== "pending" && v.hcsProof !== "N/A" ? (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-accent whitespace-nowrap">
            <Link className="h-3 w-3 shrink-0" />
            <span className="truncate max-w-[120px]">{v.hcsProof}</span>
          </span>
        ) : (
          <span className="text-[11px] text-muted-foreground">{v.hcsProof}</span>
        )}
      </td>
      <td className="py-3 px-4">
        {v.confidence > 0 ? (
          <span className={`text-xs font-medium whitespace-nowrap ${v.confidence > 90 ? "text-success" : v.confidence > 50 ? "text-warning" : "text-destructive"}`}>
            {v.confidence}%
          </span>
        ) : (
          <span className="text-[11px] text-muted-foreground">—</span>
        )}
      </td>
    </tr>
  );
};

export default VerificationRow;
