import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Package, Ship, Anchor, ArrowRight } from "lucide-react";
import HeroValueSlider from "@/components/HeroValueSlider";
import PortOverviewMap from "@/components/PortOverviewMap";
import OperationalNetworkFooter from "@/components/OperationalNetworkFooter";
import LiveVerificationFlow from "@/components/LiveVerificationFlow";
import { mockMetrics } from "@/lib/mock-data";
import { useMockMode } from "@/contexts/MockModeContext";
import { apiFetch, MockModeError } from "@/lib/api-client";
import { useEffect, useState } from "react";
import truthforgeLogo from "@/assets/truthforge-logo.png";

const LandingPage = () => {
  const navigate = useNavigate();
  const { isMockMode } = useMockMode();
  const [metrics, setMetrics] = useState(mockMetrics);

  useEffect(() => {
    if (isMockMode) { setMetrics(mockMetrics); return; }
    apiFetch<typeof mockMetrics>("/api/dashboard/metrics")
      .then(setMetrics)
      .catch((err) => { if (!(err instanceof MockModeError)) console.warn("Metrics fetch failed", err); });
  }, [isMockMode]);

  const portals = [
    {
      path: "/merchant",
      label: "Merchant Portal",
      icon: Package,
      bg: "bg-[#0b1f33] hover:bg-[#0d2540]",
      border: "border-accent/30 hover:border-accent/60",
      iconColor: "text-accent",
      accentBar: "bg-accent",
      desc: "Manage shipments, request pre-clearance, connect carriers",
    },
    {
      path: "/carrier",
      label: "Carrier Portal",
      icon: Ship,
      bg: "bg-[#0b1f33] hover:bg-[#0d2540]",
      border: "border-success/30 hover:border-success/60",
      iconColor: "text-success",
      accentBar: "bg-success",
      desc: "Upload documents, verify cargo, issue trust receipts",
    },
    {
      path: "/port-authority",
      label: "Port Authority Portal",
      icon: Anchor,
      bg: "bg-[#0b1f33] hover:bg-[#0d2540]",
      border: "border-[hsl(190,100%,50%)]/30 hover:border-[hsl(190,100%,50%)]/60",
      iconColor: "text-[hsl(190,100%,50%)]",
      accentBar: "bg-[hsl(190,100%,50%)]",
      desc: "Pre-arrival queue, vessel intelligence, container grid",
    },
  ];

  return (
    <div className="space-y-10">
      {/* Hero */}
      <section className="bg-hero rounded-xl p-8 md:p-12 relative overflow-hidden">
        <div className="absolute inset-0 opacity-5 pointer-events-none">
          <div className="absolute top-10 right-10 w-64 h-64 bg-[hsl(190,100%,50%)] rounded-full blur-[120px]" />
        </div>
        <div className="relative z-10 max-w-4xl">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <h2 className="text-3xl md:text-5xl font-heading font-black mb-3 leading-tight text-white">
              Pre-Arrival Verification &amp; Clearance for Global Trade
            </h2>
            <p className="text-base md:text-lg text-white/60 mb-6 max-w-2xl">
              Trusted, verifiable shipment data before cargo arrival — powered by Hedera consensus.
            </p>

            <div className="grid grid-cols-3 gap-4 mb-6 max-w-xl">
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-heading font-black text-white">{metrics.avgClearanceTime}</div>
                <div className="text-[10px] text-white/50 uppercase tracking-wider mt-1">Avg Clearance Reduction</div>
              </div>
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-heading font-black text-white">{metrics.documentsPreArrival.toLocaleString()}</div>
                <div className="text-[10px] text-white/50 uppercase tracking-wider mt-1">Docs Verified Pre-Arrival</div>
              </div>
              <div className="text-center">
                <div className="text-2xl md:text-3xl font-heading font-black text-white">{metrics.shipmentsPreCleared.toLocaleString()}</div>
                <div className="text-[10px] text-white/50 uppercase tracking-wider mt-1">Shipments Pre-Cleared</div>
              </div>
            </div>

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

      {/* What is TruthForge */}
      <section className="rounded-xl border border-border bg-card p-6 md:p-8 shadow-card">
        <div className="flex items-center gap-3 mb-4">
          <img src={truthforgeLogo} alt="TruthForge" className="h-8 w-8 object-contain" />
          <h3 className="text-lg font-heading font-bold text-foreground">What is TruthForge?</h3>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed max-w-3xl">
          TruthForge is a verifiable intelligence layer for global trade logistics. It uses Hedera Consensus Service (HCS) and a network of AI agents to verify shipment documents, issue port trust receipts, and enable pre-arrival clearance — reducing port dwell time and compliance risk for merchants, carriers, and port authorities.
        </p>
      </section>

      {/* Live Verification Flow */}
      <section aria-label="Live verification flow">
        <LiveVerificationFlow />
      </section>

      {/* Portal CTAs — compact navy cards */}
      <section>
        <h3 className="text-sm font-heading font-bold text-muted-foreground uppercase tracking-wider mb-4">Access Your Portal</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {portals.map(({ path, label, icon: Icon, bg, border, iconColor, accentBar, desc }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`rounded-xl border p-5 text-left transition-colors duration-150 shadow-card ${bg} ${border} group`}
            >
              {/* Top accent bar */}
              <div className={`h-0.5 w-8 rounded-full mb-4 ${accentBar} transition-all duration-150 group-hover:w-16`} />
              <Icon className={`h-7 w-7 mb-3 ${iconColor}`} />
              <h4 className="font-heading font-bold text-white text-sm mb-1">{label}</h4>
              <p className="text-xs text-slate-400 mb-4 leading-relaxed">{desc}</p>
              <span className={`inline-flex items-center gap-1 text-xs font-bold uppercase tracking-wider ${iconColor}`}>
                Open Portal <ArrowRight className="h-3 w-3 transition-transform duration-150 group-hover:translate-x-0.5" />
              </span>
            </button>
          ))}
        </div>
      </section>

      {/* Port Overview Map */}
      <section aria-label="Global port overview">
        <PortOverviewMap />
      </section>

      <OperationalNetworkFooter />
    </div>
  );
};

export default LandingPage;
