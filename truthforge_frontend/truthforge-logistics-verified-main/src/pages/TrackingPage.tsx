import { useState } from "react";
import { mockShipments, mockVerifications } from "@/lib/mock-data";
import OperationalCharts from "@/components/OperationalCharts";
import PreClearanceRequestModal, { PreClearanceFormData } from "@/components/PreClearanceRequestModal";
import { BarChart3, Package, Ship, MapPin, Calendar, ExternalLink, Truck, CheckCircle, AlertTriangle, Activity, Gauge, FileCheck } from "lucide-react";

const statusColors: Record<string, string> = {
  "Verified": "bg-success/10 text-success",
  "Pending Consensus": "bg-warning/10 text-warning",
  "Flagged Exception": "bg-destructive/10 text-destructive",
};

const TrackingPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const verifiedCount = mockVerifications.filter(v => v.status === "verified").length;
  const flaggedCount = mockVerifications.filter(v => v.status === "failed").length;

  const handlePreClearanceSubmit = (data: PreClearanceFormData) => {
    console.log("Pre-clearance request submitted:", data);
    // TODO: Send to backend API
    alert("Pre-clearance request submitted successfully!");
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-accent" />
            Operational Oversight
          </h2>
          <p className="text-sm text-muted-foreground mt-1">Clearance throughput, verification rates, exceptions, and consensus activity.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 rounded-lg bg-accent text-white text-sm font-heading font-bold uppercase tracking-wider hover:bg-accent/90 transition-colors flex items-center gap-2"
        >
          <FileCheck className="h-4 w-4" />
          Request Pre-Clearance
        </button>
      </div>

      <PreClearanceRequestModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handlePreClearanceSubmit}
      />

      {/* Throughput Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="rounded-lg border border-border bg-card p-3 shadow-card hover:shadow-elevated hover:border-accent/30 transition-all duration-200">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle className="h-3.5 w-3.5 text-success" />
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Verified</span>
          </div>
          <div className="text-xl font-heading font-black text-foreground">{verifiedCount}</div>
        </div>
        <div className="rounded-lg border border-border bg-card p-3 shadow-card hover:shadow-elevated hover:border-accent/30 transition-all duration-200">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="h-3.5 w-3.5 text-destructive" />
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Exceptions</span>
          </div>
          <div className="text-xl font-heading font-black text-foreground">{flaggedCount}</div>
        </div>
        <div className="rounded-lg border border-border bg-card p-3 shadow-card hover:shadow-elevated hover:border-accent/30 transition-all duration-200">
          <div className="flex items-center gap-2 mb-1">
            <Activity className="h-3.5 w-3.5 text-accent" />
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">HCS Messages</span>
          </div>
          <div className="text-xl font-heading font-black text-foreground">1,247</div>
        </div>
        <div className="rounded-lg border border-success/20 bg-success/5 p-3 shadow-card hover:shadow-elevated transition-all duration-200">
          <div className="flex items-center gap-2 mb-1">
            <Ship className="h-3.5 w-3.5 text-success" />
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Council Status</span>
          </div>
          <div className="text-xs font-heading font-bold text-success uppercase">Active</div>
          <div className="text-[10px] text-muted-foreground">Council-grade Integration</div>
        </div>
      </div>

      {/* Active Shipments */}
      <div>
        <h3 className="text-sm font-heading font-bold text-muted-foreground uppercase tracking-wider mb-4">Active Shipments</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {mockShipments.map((s) => (
            <div key={s.id} className="rounded-lg border border-border bg-card p-5 shadow-card hover:shadow-elevated hover:border-accent/30 transition-all duration-200">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Package className="h-4 w-4 text-accent" />
                  <span className="font-heading font-bold text-sm text-foreground">{s.id}</span>
                </div>
                <span className={`px-2.5 py-1 rounded text-[10px] font-medium uppercase tracking-wider ${statusColors[s.status] || "bg-secondary text-muted-foreground"}`}>
                  {s.status}
                </span>
              </div>
              <div className="space-y-2.5 text-sm">
                <div className="flex items-center gap-3">
                  <MapPin className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  <span className="text-foreground text-xs">{s.origin} → {s.destination}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Ship className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  <span className="text-foreground text-xs">{s.carrier}{s.vessel ? ` / ${s.vessel}` : ""}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Calendar className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  <span className="text-muted-foreground text-xs">ETA:</span>
                  <span className="text-foreground text-xs font-mono">{s.eta}</span>
                </div>
                <div className="flex flex-wrap gap-2 pt-2 border-t border-border">
                  {s.fedexTracking && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-border text-[10px] font-medium text-foreground hover:bg-accent/5 transition-colors">
                      <Truck className="h-3 w-3" />
                      FedEx: {s.fedexTracking}
                      <ExternalLink className="h-2.5 w-2.5 text-muted-foreground" />
                    </span>
                  )}
                  {s.woocommerceOrder && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-border text-[10px] font-medium text-foreground">
                      <Package className="h-3 w-3" />
                      WC: {s.woocommerceOrder}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Throughput & Consensus Volume */}
      <section>
        <div className="mb-4">
          <h3 className="text-sm font-heading font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
            <Gauge className="h-4 w-4 text-accent" />
            System Throughput & Consensus Volume
          </h3>
          <p className="text-xs text-muted-foreground mt-1">Real-time operational metrics for port authorities.</p>
        </div>
        <OperationalCharts />
      </section>
    </div>
  );
};

export default TrackingPage;
