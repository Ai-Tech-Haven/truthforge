import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { Anchor, Clock, Zap, TrendingDown } from "lucide-react";

function useCountUp(end: number, duration: number = 2000, decimals: number = 0, trigger: boolean = true) {
  const [value, setValue] = useState(0);
  const frameRef = useRef<number>();

  useEffect(() => {
    if (!trigger) return;
    const startTime = performance.now();
    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Number((eased * end).toFixed(decimals)));
      if (progress < 1) frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => { if (frameRef.current) cancelAnimationFrame(frameRef.current); };
  }, [end, duration, decimals, trigger]);

  return value;
}

const PortClearanceWidget = () => {
  const [animate, setAnimate] = useState(false);
  const [showAfter, setShowAfter] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setAnimate(true); setTimeout(() => setShowAfter(true), 1200); } },
      { threshold: 0.3 }
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);

  const beforeDays = useCountUp(5, 1500, 0, animate);
  const percentFaster = useCountUp(99.9, 2000, 1, showAfter);

  return (
    <div ref={ref} className="relative overflow-hidden rounded-xl border border-border bg-card p-5 md:p-6 shadow-card hover:shadow-elevated transition-all duration-200">
      <div className="absolute inset-0 animate-shimmer pointer-events-none" />

      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-1">
          <Anchor className="h-4 w-4 text-accent" />
          <h3 className="text-sm font-heading font-bold text-muted-foreground uppercase tracking-wider">Clearance Time Comparison</h3>
        </div>
        <p className="text-xs text-muted-foreground mb-5">Typical clearance timelines reduced from days to minutes through pre-arrival verification.</p>

        <div className="flex items-center gap-4">
          {/* BEFORE */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={animate ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6 }}
            className="flex-1 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-center"
          >
            <span className="text-[10px] font-heading font-bold text-destructive uppercase tracking-wider">Before</span>
            <div className="flex items-center justify-center gap-1 mt-1">
              <Clock className="h-5 w-5 text-destructive" />
              <span className="text-3xl font-heading font-black text-destructive">{beforeDays}</span>
            </div>
            <div className="text-xs font-heading font-bold text-destructive/70 uppercase tracking-wider">Days</div>
          </motion.div>

          {/* Arrow */}
          <TrendingDown className="h-5 w-5 text-accent shrink-0" />

          {/* AFTER */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={showAfter ? { opacity: 1, x: 0 } : { opacity: 0.3 }}
            transition={{ duration: 0.6 }}
            className={`flex-1 rounded-lg border p-4 text-center transition-all duration-500 ${
              showAfter ? "border-success/30 bg-success/5 shadow-glow" : "border-border bg-secondary"
            }`}
          >
            <span className={`text-[10px] font-heading font-bold uppercase tracking-wider transition-colors ${showAfter ? "text-success" : "text-muted-foreground"}`}>After</span>
            <div className="flex items-center justify-center gap-1 mt-1">
              <Zap className={`h-5 w-5 transition-colors ${showAfter ? "text-success" : "text-muted-foreground"}`} />
            </div>
            <div className={`text-sm font-heading font-black uppercase tracking-wider transition-colors ${showAfter ? "text-success" : "text-muted-foreground"}`}>
              In Minutes
            </div>
          </motion.div>
        </div>

        {/* Stats bar */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={showAfter ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex items-center justify-center gap-4 mt-5 pt-4 border-t border-border"
        >
          <div className="flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-accent" />
            <span className="text-lg font-heading font-black text-gradient">{percentFaster}%</span>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Faster</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default PortClearanceWidget;
