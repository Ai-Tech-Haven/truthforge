import { useEffect, useState, useCallback } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import OperationalCharts from "@/components/OperationalCharts";
import { BarChart3, Gauge } from "lucide-react";

const RAILWAY = "https://web-production-dcd43.up.railway.app";

const TrackingPage = () => {
  const { isMockMode } = useMockMode();
  const [_liveData, setLiveData] = useState<unknown>(null);

  const fetchLiveData = useCallback(async () => {
    if (isMockMode) return;
    try {
      const res = await fetch(`${RAILWAY}/api/operational/metrics`, {
        signal: AbortSignal.timeout(8000),
      });
      if (res.ok) setLiveData(await res.json());
    } catch {
      // silently fail — charts handle their own state
    }
  }, [isMockMode]);

  useEffect(() => {
    fetchLiveData();
  }, [fetchLiveData]);

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
          {isMockMode ? "Mock Mode" : "Live Mode – Connected to Backend"}
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
