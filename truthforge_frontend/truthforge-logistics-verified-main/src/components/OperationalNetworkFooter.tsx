import { motion } from "framer-motion";
import { Hexagon, BookOpen, Truck, Ship, Anchor, Scale } from "lucide-react";

const entities = [
  { name: "Hedera", label: "Consensus & Verification Layer", icon: Hexagon },
  { name: "HOL Registry", label: "Registered Agent Discovery", icon: BookOpen },
  { name: "FedEx", label: "Council Member — Carrier Data Adapter Enabled", icon: Truck },
  { name: "Council Carriers", label: "Council-Grade Connectivity", icon: Ship },
  { name: "Port Authorities", label: "Operational Interfaces", icon: Anchor },
  { name: "Customs & Regulatory", label: "Compliance & Oversight", icon: Scale },
];

const OperationalNetworkFooter = () => (
  <section className="mt-8">
    <div className="rounded-xl border border-border bg-[hsl(213,60%,12%)] p-6 md:p-8 shadow-elevated">
      <h3 className="text-sm font-heading font-bold text-[hsl(210,20%,70%)] uppercase tracking-wider mb-6">
        Operational Network & Standards
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {entities.map((entity, i) => {
          const Icon = entity.icon;
          return (
            <motion.div
              key={entity.name}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              className="text-center p-4 rounded-lg border border-[hsl(213,30%,22%)] bg-[hsl(213,50%,15%)] hover:bg-[hsl(213,50%,18%)] hover:border-[hsl(190,100%,50%,0.3)] flex flex-col items-center gap-2.5 transition-all duration-200"
            >
              <div className="p-2.5 rounded-lg bg-[hsl(190,100%,50%,0.1)] border border-[hsl(190,100%,50%,0.2)]">
                <Icon className="h-5 w-5 text-[hsl(190,100%,50%)]" />
              </div>
              <div className="text-sm font-heading font-bold text-[hsl(210,20%,85%)]">{entity.name}</div>
              <div className="text-[10px] text-[hsl(210,20%,55%)] leading-tight">{entity.label}</div>
            </motion.div>
          );
        })}
      </div>

      <p className="text-[10px] text-[hsl(210,20%,45%)] mt-5 text-center">
        This section is informational only. Listings do not imply partnership, endorsement, sponsorship, or exclusivity.
      </p>
    </div>
  </section>
);

export default OperationalNetworkFooter;
