import { mockVerifications, mockPortTrustReceipts } from "@/lib/mock-data";
import VerificationRow from "@/components/VerificationRow";
import PortTrustReceipt from "@/components/PortTrustReceipt";
import { Search, Filter, FileCheck, Shield } from "lucide-react";
import { useState } from "react";

const VerificationPage = () => {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const filtered = mockVerifications.filter((v) => {
    const matchesSearch = v.shipmentId.toLowerCase().includes(search.toLowerCase()) || v.type.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || v.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
          <FileCheck className="h-5 w-5 text-accent" />
          Verification & Compliance Engine
        </h2>
        <p className="text-sm text-muted-foreground mt-1">Document verification outcomes with linked Hedera consensus proofs.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
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
                statusFilter === s ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:text-foreground hover:bg-accent/10"
              }`}
              aria-label={`Filter by ${s}`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border bg-card shadow-card overflow-x-auto">
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
            {filtered.map((v) => (
              <VerificationRow key={v.id} v={v} />
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="py-12 text-center text-muted-foreground text-sm">No verifications match your filters.</div>
        )}
      </div>

      {/* Port Trust Receipts */}
      <div>
        <h3 className="text-sm font-heading font-bold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
          <Shield className="h-4 w-4 text-accent" />
          Generated Port Trust Receipts
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {mockPortTrustReceipts.map((receipt) => (
            <PortTrustReceipt key={receipt.id} receipt={receipt} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default VerificationPage;
