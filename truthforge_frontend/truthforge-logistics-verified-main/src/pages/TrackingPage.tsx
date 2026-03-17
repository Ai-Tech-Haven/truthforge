import { useEffect, useState, useCallback } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import OperationalCharts from "@/components/OperationalCharts";
import { BarChart3, Gauge } from "lucide-react";

const RAILWAY = "https://web-production-dcd43.up.railway.app";

interface ThroughputPoint { day: string; cleared: number; pending: number; flagged: number }
interface HcsPoint { hour: string; messages: number }
interface LiveMetrics { throughput?: ThroughputPoint[]; hcs?: HcsPoint[] }

const TrackingPage = () => {
  const { isMockMode } = useMockMode();
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics | null>(null);

  const fetchLiveData = useCallback(async () => {
    if (isMockMode) return;
    try {
      const res = await fetch(`${RAILWAY}/api/operational/metrics`, {
        signal: AbortSignal.timeout(8000),
      });
      if (res.ok) {
        const data = await res.json();
        setLiveMetrics(data);
      }
    } catch {
      // silently fail â€” charts fall back to default data
    }
  }, [isMockMode]);

  useEffect(() => {
    if (isMockMode) {
      setLiveMetrics(null);
      return;
    }
    fetchLiveData();
    const interval = setInterval(fetchLiveData, 30000);
    return () => clearInterval(interval);
  }, [isMockMode, fetchLiveData]);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-accent" />
          Operational Oversight
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Clearance throughput, verification rates, exceptions, and consensus activity.
        </p>
        <div className={`inline-flex items-center gap-1.5 mt-2 px-2.5 py-1 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${isMockMode ? "border-warning/40 bg-warning/10 text-warning" : "border-success/40 bg-success/10 text-success"}`}>
          {isMockMode ? "Preview Mode" : "Live Mode"}
        </div>
      </div>

      <section>
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h3 className="text-sm font-heading font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <Gauge className="h-4 w-4 text-accent" />
              System Throughput &amp; Consensus Volume
            </h3>
          </div>
          {!isMockMode && (
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-destructive text-white text-[10px] font-heading font-bold uppercase tracking-wider shrink-0">
              <span className="h-2 w-2 rounded-full bg-white animate-ping" />
              Real-time operational metrics for port authorities
            </span>
          )}
        </div>
        <OperationalCharts
          throughputData={liveMetrics?.throughput}
          hcsData={liveMetrics?.hcs}
        />
      </section>
    </div>
  );
};

export default TrackingPage;
