import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, Shield, ShoppingCart, GitBranch, Globe } from "lucide-react";

const slides = [
  {
    icon: Clock,
    title: "Pre-Arrival Clearance",
    description: "Typical clearance timelines reduced from days to minutes (pre-arrival).",
    subtext: "Clearance based on verified documentation submitted prior to vessel or aircraft arrival.",
  },
  {
    icon: Shield,
    title: "Document & Cargo Integrity",
    description: "Automated detection of altered, incomplete, or fraudulent shipment records.",
    subtext: "Verification executed by registered agents. Outcomes notarized immutably.",
  },
  {
    icon: ShoppingCart,
    title: "Shipper & Merchant Integration",
    description: "Shipment intent registered directly from connected commerce and ERP systems.",
    subtext: "Example integration: www.a-thi.online (WooCommerce).",
  },
  {
    icon: GitBranch,
    title: "Network-Optimized Routing",
    description: "Verified rerouting decisions reduce congestion and idle time.",
    subtext: "Verified agents make clearance decisions using defined rules, and every decision is automatically logged for audit.",
  },
  {
    icon: Globe,
    title: "Shared Trade Truth",
    description: "A single, verifiable source of shipment truth across organizations.",
    subtext: "Readable by ports, carriers, freight forwarders, and regulators.",
  },
];

const HeroValueSlider = () => {
  const [current, setCurrent] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  const advance = useCallback(() => {
    setCurrent((prev) => (prev + 1) % slides.length);
  }, []);

  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(advance, 5000);
    return () => clearInterval(interval);
  }, [isPaused, advance]);

  const slide = slides[current];
  const Icon = slide.icon;

  return (
    <div
      className="relative rounded-lg border border-white/10 bg-white/5 backdrop-blur-sm p-5 min-h-[140px]"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={current}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.4 }}
        >
          <div className="flex items-start gap-3">
            <div className="shrink-0 p-2 rounded-md bg-white/10 border border-white/15">
              <Icon className="h-4 w-4 text-[hsl(190,100%,50%)]" />
            </div>
            <div>
              <h4 className="text-sm font-heading font-bold text-white">{slide.title}</h4>
              <p className="text-sm text-white/80 mt-1">{slide.description}</p>
              <p className="text-xs text-white/50 mt-2">{slide.subtext}</p>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Slide indicators */}
      <div className="flex gap-1.5 mt-4 justify-center">
        {slides.map((_, i) => (
          <button
            key={i}
            onClick={() => setCurrent(i)}
            aria-label={`Go to slide ${i + 1}`}
            className={`h-1 rounded-full transition-all duration-300 ${
              i === current ? "w-6 bg-[hsl(190,100%,50%)]" : "w-2 bg-white/30"
            }`}
          />
        ))}
      </div>

      {/* Pause indicator */}
      {isPaused && (
        <div className="absolute top-2 right-2 text-[9px] text-white/40 uppercase tracking-wider">
          Paused
        </div>
      )}
    </div>
  );
};

export default HeroValueSlider;
