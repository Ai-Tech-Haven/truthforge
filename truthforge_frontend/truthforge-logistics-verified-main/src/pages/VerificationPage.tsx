import { mockVerifications } from "@/lib/mock-data";
import { Verification } from "@/lib/mock-data";
import { Search, Filter, FileCheck, CheckCircle, Clock, XCircle, ExternalLink } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { useMockMode } from "@/contexts/MockModeContext";

const RAILWAY = "https://web-production-dcd43.up.railway.app";

const statusConfig: Record<string, { icon: typeof CheckCircle; color: string; bg: string; label: string }> = {
  verified: { icon: CheckCircle, color: "text-success", bg: "bg-success/10", label: "Verified" },
  pending:  { icon: Clock,        color: "text-warning",     bg: "bg-warning/10",     label: "Pending"  },
  failed:   { icon: XCircle,      color: "text-destructive", bg: "bg-destructive/10", label: "Failed"   },
};

const VerificationPage = () => {
  const { isMockMode } = useMockMode();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  // live mode starts empty â€” no cached mock data shown
  const [verifications, setVerifications] = useState<Verification[]>(isMockMode ? mockVerifications : []);
  const [loading, setLoading] = useState(!isMockMode);
  const [error, setError] = useState<string | null>(null);

  const fetchLive = useCallback(async () => {
    setLoading(true);
    setError(null);
    setVerifications([]); // clear any stale data before fetching
    try {
      const res = await fetch(`${RAILWAY}/api/verifications`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setVerifications(data.verifications ?? data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to fetch verifications");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isMockMode) {
      fetchLive();
    } else {
      setVerifications(mockVerifications);
      setLoading(false);
      setError(null);
    }
  }, [isMockMode, fetchLive]);

  const filtered = verifications.filter((v: Verification) => {
    const matchesSearch =
      v.shipmentId.toLowerCase().includes(search.toLowerCase()) ||
      v.type.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || v.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
            <FileCheck className="h-5 w-5 text-accent" />
            Verification &amp; Compliance Engine
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Document verification outcomes with linked Hedera consensus proofs.
          </p>
        </div>
        <span
          className={`text-[10px] font-heading font-bold px-2 py-1 rounded uppercase tracking-wider border ${
            isMockMode
              ? "bg-warning/10 text-warning border-warning/30"
              : "bg-success/10 text-success border-success/30"
          }`}
        >
          {isMockMode ? "Preview Mode" : "Live Mode"}
        </span>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
            placeholder="Search by shipment ID or document type..."
            className="w-full pl-10 pr-4 py-2 text-sm rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            aria-label="Search verifications"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          {["all", "verified", "pending", "failed"].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 text-xs font-medium rounded capitalize transition-colors ${
                statusFilter === s
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-muted-foreground hover:text-foreground hover:bg-accent/10"
              }`}
              aria-label={`Filter by ${s}`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive flex items-center justify-between gap-4">
          <span>{error}</span>
          <button
            onClick={fetchLive}
            className="text-xs font-medium underline hover:no-underline shrink-0"
          >
            Retry
          </button>
        </div>
      )}

      <div className="rounded-xl border border-border bg-card shadow-card overflow-x-auto">
        {loading ? (
          <div className="py-12 text-center text-muted-foreground text-sm">Loading live verifications...</div>
        ) : (
          <table className="w-full table-fixed" role="table">
            <thead>
              <tr className="border-b border-border bg-secondary/50">
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider w-[100px]">Shipment</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider w-[130px]">Document</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider w-[90px]">Status</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider w-[140px]">Agent</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider w-[140px]">Timestamp</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider w-[140px]">HCS Proof</th>
                <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider w-[70px]">Score</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((v: Verification) => {
                const cfg = statusConfig[v.status] ?? statusConfig.pending;
                const Icon = cfg.icon;
                const topicMatch = v.hcsProof && v.hcsProof.match(/^([\w-]+)#/);
                const topicId = topicMatch ? topicMatch[1] : null;
                const isLinkable = !isMockMode && topicId && v.hcsProof !== "pending" && v.hcsProof !== "N/A";
                return (
                  <tr key={v.id} className="border-b border-border last:border-0 hover:bg-accent/5 transition-colors">
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
                      {isLinkable ? (
                        <a
                          href={`https://hashscan.io/testnet/topic/${topicId}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] font-mono text-accent hover:underline whitespace-nowrap"
                        >
                          <ExternalLink className="h-3 w-3 shrink-0" />
                          <span className="truncate max-w-[110px]">{v.hcsProof}</span>
                        </a>
                      ) : v.hcsProof !== "pending" && v.hcsProof !== "N/A" ? (
                        <span className="text-[11px] font-mono text-accent whitespace-nowrap truncate max-w-[120px] block">{v.hcsProof}</span>
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
                        <span className="text-[11px] text-muted-foreground">-</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        {!loading && filtered.length === 0 && (
          <div className="py-12 text-center text-muted-foreground text-sm">
            {isMockMode ? "No verifications match your filters." : "No live verification data available yet."}
          </div>
        )}
      </div>
    </div>
  );
};

export default VerificationPage;
