import { motion } from "framer-motion";
import { Shield, Clock, FileCheck, CheckCircle, BarChart3, CloudUpload, Anchor, Ship, AlertTriangle, Eye } from "lucide-react";
import PortClearanceWidget from "@/components/PortClearanceWidget";
import HeroValueSlider from "@/components/HeroValueSlider";
import MetricCard from "@/components/MetricCard";
import OperationalNetworkFooter from "@/components/OperationalNetworkFooter";
import PortOverviewMap from "@/components/PortOverviewMap";
import GlobalTradeRiskCommandCenter from "@/components/GlobalTradeRiskCommandCenter";
import { mockMetrics, mockShipments, mockPortTrustReceipts } from "@/lib/mock-data";
import { useEffect, useState, useRef } from "react";

const clearanceStatusConfig: Record<string, { color: string; label: string }> = {
  "Verified": { color: "text-success", label: "Verified" },
  "Pending Consensus": { color: "text-warning", label: "Pending Consensus" },
  "Flagged Exception": { color: "text-destructive", label: "Flagged Exception" },
};

const DashboardPage = () => {
  const [heroVisible, setHeroVisible] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);
  const [receiptModal, setReceiptModal] = useState<string | null>(null);
  const [selectedPort, setSelectedPort] = useState<string>("all");

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setHeroVisible(true); }, { threshold: 0.2 });
    if (heroRef.current) obs.observe(heroRef.current);
    return () => obs.disconnect();
  }, []);

  const receiptForShipment = (shipId: string) => mockPortTrustReceipts.find(r => r.shipmentId === shipId);

  // Get unique ports from shipments
  const ports = ["all", ...Array.from(new Set(mockShipments.map(s => s.destination)))];

  // Filter shipments by selected port
  const filteredShipments = selectedPort === "all" 
    ? mockShipments 
    : mockShipments.filter(s => s.destination === selectedPort);

  return (
    <div className="space-y-8">
      {/* Global Trade Risk Command Center */}
      <GlobalTradeRiskCommandCenter />

      {/* Hero Section */}
      <section ref={heroRef} className="bg-hero rounded-xl p-8 md:p-10 relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-10 right-10 w-64 h-64 bg-[hsl(190,100%,50%)] rounded-full blur-[120px]" />
        </div>
        <div className="relative z-10 max-w-4xl">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={heroVisible ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.5 }}>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-heading font-black mb-3 leading-tight text-white">
              Pre-Arrival Verification & Clearance for Global Trade
            </h2>
            <p className="text-base md:text-lg text-white/60 mb-5 max-w-2xl">
              Trusted, verifiable shipment data before cargo arrival.
            </p>

            {/* Outcome Indicators */}
            <div className="grid grid-cols-3 gap-4 mb-6 max-w-xl">
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-heading font-black text-white">{mockMetrics.avgClearanceTime}</div>
                <div className="text-[10px] text-white/50 uppercase tracking-wider mt-1">Avg Clearance Reduction</div>
              </div>
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-heading font-black text-white">{mockMetrics.documentsPreArrival.toLocaleString()}</div>
                <div className="text-[10px] text-white/50 uppercase tracking-wider mt-1">Docs Verified Pre-Arrival</div>
              </div>
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-heading font-black text-white">{mockMetrics.shipmentsPreCleared.toLocaleString()}</div>
                <div className="text-[10px] text-white/50 uppercase tracking-wider mt-1">Shipments Pre-Cleared</div>
              </div>
            </div>

            {/* Capability Badges */}
            <div className="flex flex-wrap gap-2 mb-6">
              {["Hedera Network — Live", "Council Node Compatible", "Carrier Data Adapters (Council-grade)"].map(badge => (
                <span key={badge} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-[hsl(122,39%,49%,0.15)] border border-[hsl(122,39%,49%,0.25)] text-[hsl(122,39%,70%)]">
                  <span className="h-1.5 w-1.5 rounded-full bg-[hsl(122,39%,49%)]" />
                  {badge}
                </span>
              ))}
            </div>

            <HeroValueSlider />
          </motion.div>
        </div>
      </section>

      {/* Operational Summary — reduced */}
      <section aria-label="Operational metrics">
        <h3 className="text-sm font-heading font-bold text-muted-foreground uppercase tracking-wider mb-4">Operational Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MetricCard icon={Clock} label="Avg Clearance" value={mockMetrics.avgClearanceTime} variant="accent" />
          <MetricCard icon={FileCheck} label="Docs Pre-Arrival" value={mockMetrics.documentsPreArrival.toLocaleString()} variant="default" />
          <MetricCard icon={CheckCircle} label="Pre-Cleared" value={mockMetrics.shipmentsPreCleared.toLocaleString()} variant="success" />
          <MetricCard icon={BarChart3} label="Shipments Today" value={mockMetrics.shipmentsToday} variant="default" />
        </div>
      </section>

      {/* Port Overview Map */}
      <section aria-label="Global port overview">
        <PortOverviewMap />
      </section>

      {/* Port Clearance Comparison */}
      <section aria-label="Port clearance comparison">
        <PortClearanceWidget />
      </section>

      {/* Pre-Arrival Clearance Queue — light navy */}
      <section aria-label="Pre-arrival clearance queue">
        <div className="rounded-xl border border-[hsl(213,30%,28%)] bg-[hsl(213,50%,15%)] shadow-card overflow-hidden">
          <div className="p-5 border-b border-[hsl(213,30%,22%)]">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Ship className="h-4 w-4 text-accent" />
                  <h3 className="text-sm font-heading font-bold text-[hsl(210,20%,88%)]">Pre-Arrival Clearance Queue</h3>
                </div>
                <p className="text-xs text-[hsl(210,20%,55%)] mt-1">Live feed of inbound shipments and their trust status.</p>
              </div>
              
              {/* Port Filter Dropdown */}
              <div className="flex items-center gap-2">
                <Anchor className="h-3.5 w-3.5 text-[hsl(210,20%,55%)]" />
                <select
                  value={selectedPort}
                  onChange={(e) => setSelectedPort(e.target.value)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[hsl(213,50%,12%)] border border-[hsl(213,30%,25%)] text-[hsl(210,20%,85%)] hover:border-accent/40 focus:outline-none focus:border-accent transition-colors"
                >
                  <option value="all">All Ports</option>
                  {ports.slice(1).map(port => (
                    <option key={port} value={port}>{port}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full" role="table">
              <thead>
                <tr className="border-b border-[hsl(213,30%,22%)] bg-[hsl(213,50%,13%)]">
                  <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-[hsl(210,20%,55%)] uppercase tracking-wider">Shipment ID</th>
                  <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-[hsl(210,20%,55%)] uppercase tracking-wider">Carrier / Vessel</th>
                  <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-[hsl(210,20%,55%)] uppercase tracking-wider">ETA</th>
                  <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-[hsl(210,20%,55%)] uppercase tracking-wider">Status</th>
                  <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-[hsl(210,20%,55%)] uppercase tracking-wider">Trust Receipt</th>
                </tr>
              </thead>
              <tbody>
                {filteredShipments.map((s) => {
                  const cfg = clearanceStatusConfig[s.status] || { color: "text-muted-foreground", label: s.status };
                  const receipt = receiptForShipment(s.id);
                  return (
                    <tr key={s.id} className="border-b border-[hsl(213,30%,20%)] last:border-0 hover:bg-[hsl(213,50%,18%)] transition-colors">
                      <td className="py-3 px-4 font-mono text-xs text-[hsl(210,20%,85%)]">{s.id}</td>
                      <td className="py-3 px-4 text-xs text-[hsl(210,20%,85%)]">{s.carrier} / {s.vessel || "—"}</td>
                      <td className="py-3 px-4 text-xs font-mono text-[hsl(210,20%,60%)]">{s.eta}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1.5 text-xs font-heading font-bold ${cfg.color}`}>
                          {s.status === "Verified" && <CheckCircle className="h-3 w-3" />}
                          {s.status === "Pending Consensus" && <Clock className="h-3 w-3" />}
                          {s.status === "Flagged Exception" && <AlertTriangle className="h-3 w-3" />}
                          {cfg.label}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {receipt ? (
                          <button
                            onClick={() => setReceiptModal(receipt.id)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium text-accent border border-accent/30 bg-accent/10 hover:bg-accent/20 transition-colors"
                          >
                            <Eye className="h-3 w-3" />
                            View Receipt
                          </button>
                        ) : (
                          <span className="text-xs text-[hsl(210,20%,45%)]">Unavailable</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Receipt Modal */}
      {receiptModal && (() => {
        const receipt = mockPortTrustReceipts.find(r => r.id === receiptModal);
        if (!receipt) return null;
        return (
          <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setReceiptModal(null)}>
            <div className="bg-card border border-border rounded-xl p-6 max-w-lg w-full max-h-[80vh] overflow-y-auto shadow-elevated" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-heading font-bold text-foreground">Port Trust Receipt — {receipt.shipmentId}</h3>
                <button onClick={() => setReceiptModal(null)} className="text-muted-foreground hover:text-foreground text-sm">✕</button>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">Vessel</span><span className="text-foreground">{receipt.vessel}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Port</span><span className="text-foreground">{receipt.port}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Issued</span><span className="text-foreground">{receipt.issuedAt}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Status</span><span className="text-success font-heading font-bold uppercase text-xs">{receipt.clearanceStatus}</span></div>
                <div className="border-t border-border pt-3">
                  <span className="text-xs text-muted-foreground block mb-2">Agent Signatures ({receipt.agentSignatures.length}/5)</span>
                  {receipt.agentSignatures.map((sig, i) => (
                    <div key={i} className="flex justify-between text-xs py-1">
                      <span className="text-foreground">{sig.agentName}</span>
                      <span className="font-mono text-muted-foreground">{sig.agentId}</span>
                    </div>
                  ))}
                </div>
                <div className="border-t border-border pt-3">
                  <span className="text-xs text-muted-foreground block mb-1">Hedera TX Reference</span>
                  <span className="font-mono text-xs text-accent">{receipt.hederaTxRef}</span>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Ingest Shipment Data — light navy */}
      <section aria-label="Ingest shipment data">
        <div className="rounded-xl border border-[hsl(213,30%,28%)] bg-[hsl(213,50%,15%)] p-6 shadow-card hover:shadow-elevated transition-all duration-200">
          <div className="flex items-center gap-2 mb-1">
            <CloudUpload className="h-4 w-4 text-accent" />
            <h3 className="text-sm font-heading font-bold text-[hsl(210,20%,88%)]">Ingest Shipment Data</h3>
          </div>
          <p className="text-xs text-[hsl(210,20%,55%)] mb-5">Upload manifests, bills of lading, or connect carrier feeds for automated processing.</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Upload area */}
            <div className="border-2 border-dashed border-[hsl(213,30%,25%)] rounded-lg p-8 text-center hover:border-accent/40 transition-colors cursor-pointer bg-[hsl(213,50%,12%)]">
              <CloudUpload className="h-8 w-8 text-[hsl(210,20%,50%)] mx-auto mb-3" />
              <p className="text-sm font-medium text-[hsl(210,20%,85%)]">Upload Manifest or BOL</p>
              <p className="text-[11px] text-[hsl(210,20%,50%)] mt-1">Supported formats: EDIFACT, JSON, PDF</p>
            </div>

            {/* Carrier Feeds */}
            <div>
              <h4 className="font-heading font-bold text-[hsl(210,20%,75%)] text-xs uppercase tracking-wider mb-3">Connected Carrier Feeds</h4>
              <div className="space-y-3">
                {[
                  { name: "Maersk API", connected: true },
                  { name: "FedEx Cargo", connected: true },
                  { name: "MSC Connect", connected: false },
                ].map(feed => (
                  <div key={feed.name} className="flex items-center justify-between py-2 px-3 rounded-lg bg-[hsl(213,50%,12%)] border border-[hsl(213,30%,22%)]">
                    <div className="flex items-center gap-2">
                      <span className={`h-2 w-2 rounded-full ${feed.connected ? "bg-success" : "bg-[hsl(210,20%,35%)]"}`} />
                      <span className="text-xs text-[hsl(210,20%,80%)]">{feed.name}</span>
                    </div>
                    <span className={`text-[10px] font-heading font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                      feed.connected ? "text-success bg-success/10 border border-success/20" : "text-[hsl(210,20%,45%)] bg-[hsl(213,40%,18%)] border border-[hsl(213,30%,25%)]"
                    }`}>
                      {feed.connected ? "Connected" : "Available"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Operational Network & Standards */}
      <OperationalNetworkFooter />
    </div>
  );
};

export default DashboardPage;
