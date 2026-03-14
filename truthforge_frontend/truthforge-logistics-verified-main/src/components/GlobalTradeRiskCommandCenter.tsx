import { Globe, CheckCircle, AlertTriangle, Clock, Shield, TrendingUp } from "lucide-react";
import { mockShipmentRoutes, mockActivityEvents, mockRiskAlerts } from "@/lib/mock-data";

const GlobalTradeRiskCommandCenter = () => {
  const routeStatusConfig = {
    verified: { color: "stroke-success", label: "Fully Verified" },
    under_review: { color: "stroke-warning", label: "Under Review" },
    flagged: { color: "stroke-destructive", label: "Flagged Shipment" },
  };

  const eventTypeConfig = {
    verified: { icon: CheckCircle, color: "text-success", bg: "bg-success/10" },
    flagged: { icon: AlertTriangle, color: "text-destructive", bg: "bg-destructive/10" },
    completed: { icon: Shield, color: "text-accent", bg: "bg-accent/10" },
  };

  const alertTypeConfig = {
    risk: { icon: AlertTriangle, color: "text-destructive", bg: "bg-destructive/10 border-destructive/30" },
    compliance: { icon: CheckCircle, color: "text-success", bg: "bg-success/10 border-success/30" },
    inspection: { icon: Clock, color: "text-warning", bg: "bg-warning/10 border-warning/30" },
  };

  const alertSeverityConfig = {
    high: { badge: "bg-destructive/20 text-destructive border-destructive/30" },
    medium: { badge: "bg-warning/20 text-warning border-warning/30" },
    low: { badge: "bg-success/20 text-success border-success/30" },
  };

  return (
    <section aria-label="Global Trade Risk Command Center" className="mb-8">
      <div className="rounded-xl border border-[hsl(213,30%,28%)] bg-[hsl(213,50%,15%)] shadow-card overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-[hsl(213,30%,22%)] bg-gradient-to-r from-[hsl(213,50%,12%)] to-[hsl(213,50%,15%)]">
          <div className="flex items-center gap-2 mb-1">
            <Globe className="h-5 w-5 text-accent" />
            <h2 className="text-base font-heading font-black text-[hsl(210,20%,88%)]">Global Trade Risk Command Center</h2>
          </div>
          <p className="text-xs text-[hsl(210,20%,55%)]">Real-time shipment verification activity across global trade routes</p>
        </div>

        <div className="p-5">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {/* Global Shipment Map */}
            <div className="lg:col-span-2 rounded-lg border border-[hsl(213,30%,25%)] bg-[hsl(213,50%,12%)] p-4">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-base">🌍</span>
                <h3 className="text-xs font-heading font-bold text-[hsl(210,20%,75%)] uppercase tracking-wider">Global Shipment Map</h3>
              </div>

              {/* Simplified World Map Visualization */}
              <div className="relative h-64 bg-[hsl(213,50%,10%)] rounded-lg border border-[hsl(213,30%,22%)] overflow-hidden">
                {/* World map background pattern */}
                <div className="absolute inset-0 opacity-10">
                  <svg viewBox="0 0 800 400" className="w-full h-full">
                    {/* Simplified continents outline */}
                    <path d="M 100 150 Q 150 120 200 140 L 250 130 L 280 160 L 250 180 L 200 170 L 150 190 Z" fill="currentColor" className="text-[hsl(210,20%,40%)]" />
                    <path d="M 350 100 L 450 90 L 500 120 L 480 160 L 420 170 L 380 140 Z" fill="currentColor" className="text-[hsl(210,20%,40%)]" />
                    <path d="M 550 180 L 620 170 L 680 200 L 650 240 L 580 230 L 540 210 Z" fill="currentColor" className="text-[hsl(210,20%,40%)]" />
                  </svg>
                </div>

                {/* Route Lines */}
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 800 400">
                  {mockShipmentRoutes.map((route, index) => {
                    const startX = 100 + (index * 150);
                    const startY = 150 + (index % 2) * 50;
                    const endX = startX + 200;
                    const endY = startY + (index % 2 === 0 ? -30 : 30);
                    const cfg = routeStatusConfig[route.status];

                    return (
                      <g key={route.id}>
                        {/* Route line */}
                        <path
                          d={`M ${startX} ${startY} Q ${(startX + endX) / 2} ${(startY + endY) / 2 - 40} ${endX} ${endY}`}
                          fill="none"
                          className={`${cfg.color} opacity-60`}
                          strokeWidth="2"
                          strokeDasharray={route.status === "under_review" ? "5,5" : "none"}
                        />
                        {/* Origin point */}
                        <circle cx={startX} cy={startY} r="4" className={`${cfg.color} fill-current`} />
                        {/* Destination point */}
                        <circle cx={endX} cy={endY} r="4" className={`${cfg.color} fill-current`} />
                      </g>
                    );
                  })}
                </svg>

                {/* Legend */}
                <div className="absolute bottom-3 left-3 flex flex-wrap gap-3 text-xs">
                  <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[hsl(213,50%,8%)] border border-[hsl(213,30%,22%)]">
                    <div className="w-3 h-0.5 bg-success" />
                    <span className="text-[hsl(210,20%,65%)]">Verified</span>
                  </div>
                  <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[hsl(213,50%,8%)] border border-[hsl(213,30%,22%)]">
                    <div className="w-3 h-0.5 bg-warning" style={{ backgroundImage: "repeating-linear-gradient(90deg, currentColor 0, currentColor 3px, transparent 3px, transparent 6px)" }} />
                    <span className="text-[hsl(210,20%,65%)]">Under Review</span>
                  </div>
                  <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[hsl(213,50%,8%)] border border-[hsl(213,30%,22%)]">
                    <div className="w-3 h-0.5 bg-destructive" />
                    <span className="text-[hsl(210,20%,65%)]">Flagged</span>
                  </div>
                </div>
              </div>

              {/* Route List */}
              <div className="mt-4 space-y-2">
                {mockShipmentRoutes.slice(0, 3).map((route) => {
                  const cfg = routeStatusConfig[route.status];
                  return (
                    <div key={route.id} className="flex items-center justify-between p-2 rounded bg-[hsl(213,50%,10%)] border border-[hsl(213,30%,22%)]">
                      <div className="flex items-center gap-2">
                        <TrendingUp className={`h-3 w-3 ${cfg.color.replace('stroke-', 'text-')}`} />
                        <span className="text-xs text-[hsl(210,20%,75%)]">{route.origin} → {route.destination}</span>
                      </div>
                      <span className={`text-[10px] font-heading font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                        route.status === 'verified' ? 'text-success bg-success/10 border border-success/20' :
                        route.status === 'under_review' ? 'text-warning bg-warning/10 border border-warning/20' :
                        'text-destructive bg-destructive/10 border border-destructive/20'
                      }`}>
                        {cfg.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right Column: Activity Feed + Risk Alerts */}
            <div className="space-y-5">
              {/* Active Shipment Feed */}
              <div className="rounded-lg border border-[hsl(213,30%,25%)] bg-[hsl(213,50%,12%)] p-4">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-base">📡</span>
                  <h3 className="text-xs font-heading font-bold text-[hsl(210,20%,75%)] uppercase tracking-wider">Active Shipment Feed</h3>
                </div>

                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {mockActivityEvents.map((event) => {
                    const cfg = eventTypeConfig[event.type];
                    const EventIcon = cfg.icon;
                    return (
                      <div key={event.id} className="flex items-start gap-2 p-2 rounded bg-[hsl(213,50%,10%)] border border-[hsl(213,30%,22%)]">
                        <div className={`mt-0.5 h-6 w-6 rounded-full ${cfg.bg} flex items-center justify-center shrink-0`}>
                          <EventIcon className={`h-3 w-3 ${cfg.color}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-[hsl(210,20%,85%)] leading-snug">{event.message}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[10px] text-[hsl(210,20%,50%)]">{event.timestamp}</span>
                            <span className="text-[10px] text-[hsl(210,20%,50%)]">•</span>
                            <span className="text-[10px] text-[hsl(210,20%,50%)]">{event.location}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* AI Risk Alerts */}
              <div className="rounded-lg border border-[hsl(213,30%,25%)] bg-[hsl(213,50%,12%)] p-4">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-base">⚠️</span>
                  <h3 className="text-xs font-heading font-bold text-[hsl(210,20%,75%)] uppercase tracking-wider">AI Risk Alerts</h3>
                </div>

                <div className="space-y-3">
                  {mockRiskAlerts.map((alert) => {
                    const cfg = alertTypeConfig[alert.type];
                    const severityCfg = alertSeverityConfig[alert.severity];
                    const AlertIcon = cfg.icon;
                    return (
                      <div key={alert.id} className={`rounded-lg border p-3 ${cfg.bg}`}>
                        <div className="flex items-start gap-2 mb-2">
                          <AlertIcon className={`h-4 w-4 ${cfg.color} mt-0.5 shrink-0`} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="text-xs font-heading font-bold text-[hsl(210,20%,85%)]">{alert.title}</h4>
                              <span className={`text-[9px] font-heading font-bold px-1.5 py-0.5 rounded uppercase tracking-wider border ${severityCfg.badge}`}>
                                {alert.severity}
                              </span>
                            </div>
                            <p className="text-xs text-[hsl(210,20%,75%)] leading-snug">{alert.message}</p>
                            <span className="text-[10px] text-[hsl(210,20%,50%)] mt-1 block">{alert.timestamp}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default GlobalTradeRiskCommandCenter;
