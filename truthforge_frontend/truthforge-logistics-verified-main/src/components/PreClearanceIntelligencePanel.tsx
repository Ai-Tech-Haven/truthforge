import { Ship, Plane, Truck, CheckCircle, AlertTriangle, Clock, Package } from "lucide-react";
import { ShipmentTracking, PortTrustReceipt, Container } from "@/lib/mock-data";

interface PreClearanceIntelligencePanelProps {
  shipment: ShipmentTracking;
  receipt?: PortTrustReceipt;
}

const PreClearanceIntelligencePanel = ({ shipment, receipt }: PreClearanceIntelligencePanelProps) => {
  const freightMode = shipment.freightMode || "sea";
  
  // Freight mode configuration
  const freightModeConfig = {
    sea: { icon: Ship, label: "Sea Freight", color: "text-blue-400" },
    air: { icon: Plane, label: "Air Cargo", color: "text-sky-400" },
    land: { icon: Truck, label: "Ground Carrier", color: "text-amber-400" },
  };
  
  const FreightIcon = freightModeConfig[freightMode].icon;
  
  // Risk level configuration
  const riskConfig = {
    LOW: { color: "bg-success/10 border-success/30 text-success", label: "Low Risk", badgeColor: "bg-success" },
    MEDIUM: { color: "bg-warning/10 border-warning/30 text-warning", label: "Medium Risk", badgeColor: "bg-warning" },
    HIGH: { color: "bg-destructive/10 border-destructive/30 text-destructive", label: "High Risk", badgeColor: "bg-destructive" },
  };
  
  // Container risk level configuration
  const containerRiskConfig = {
    low: { color: "text-success", bgColor: "bg-success/10 border-success/30" },
    medium: { color: "text-warning", bgColor: "bg-warning/10 border-warning/30" },
    high: { color: "text-destructive", bgColor: "bg-destructive/10 border-destructive/30" },
  };
  
  // Clearance recommendation configuration
  const clearanceConfig = {
    "Fast-Track Port Clearance": { icon: CheckCircle, color: "text-success", bgColor: "bg-success/10 border-success/30" },
    "Manual Inspection Required": { icon: AlertTriangle, color: "text-destructive", bgColor: "bg-destructive/10 border-destructive/30" },
    "Secondary Document Review": { icon: Clock, color: "text-warning", bgColor: "bg-warning/10 border-warning/30" },
  };
  
  const riskLevel = receipt?.riskLevel || "LOW";
  const clearanceRecommendation = receipt?.clearanceRecommendation || "Fast-Track Port Clearance";
  const ClearanceIcon = clearanceConfig[clearanceRecommendation]?.icon || CheckCircle;
  
  // Calculate container verification progress
  const containerProgress = shipment.containerCount && shipment.verifiedContainers
    ? (shipment.verifiedContainers / shipment.containerCount) * 100
    : 0;

  // Calculate Vessel Trust Score
  const calculateTrustScore = (): number => {
    if (!shipment.containerCount || shipment.verifiedContainers === undefined) return 100;
    
    const verificationRate = (shipment.verifiedContainers / shipment.containerCount) * 100;
    const flaggedRate = ((shipment.flaggedContainers || 0) / shipment.containerCount) * 100;
    
    // Base score from verification rate
    let score = verificationRate;
    
    // Deduct points for flagged containers
    score -= flaggedRate * 2;
    
    return Math.max(0, Math.min(100, Math.round(score)));
  };

  const trustScore = calculateTrustScore();
  
  const getTrustScoreColor = (score: number): string => {
    if (score >= 80) return "text-success";
    if (score >= 50) return "text-warning";
    return "text-destructive";
  };
  
  const getTrustScoreInterpretation = (score: number): string => {
    if (score >= 80) return "Low Risk — Fast Track Eligible";
    if (score >= 50) return "Moderate Risk — Standard Processing";
    return "High Risk — Inspection Required";
  };
  
  const getTrustScoreBgColor = (score: number): string => {
    if (score >= 80) return "from-success/20 to-success/5";
    if (score >= 50) return "from-warning/20 to-warning/5";
    return "from-destructive/20 to-destructive/5";
  };

  const containers = shipment.containers || [];

  return (
    <div className="rounded-xl border border-[hsl(213,30%,28%)] bg-[hsl(213,50%,15%)] shadow-card overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-[hsl(213,30%,22%)]">
        <h3 className="text-sm font-heading font-bold text-[hsl(210,20%,88%)]">Pre-Clearance Intelligence Panel</h3>
        <p className="text-xs text-[hsl(210,20%,55%)] mt-1">AI-powered customs clearance analysis</p>
      </div>

      <div className="p-5 space-y-5">
        {/* Freight Mode Indicator */}
        <div className="flex items-center gap-3 p-3 rounded-lg bg-[hsl(213,50%,12%)] border border-[hsl(213,30%,22%)]">
          <FreightIcon className={`h-5 w-5 ${freightModeConfig[freightMode].color}`} />
          <div>
            <div className="text-xs text-[hsl(210,20%,55%)] uppercase tracking-wider">Transport Mode</div>
            <div className="text-sm font-heading font-bold text-[hsl(210,20%,88%)]">{freightModeConfig[freightMode].label}</div>
          </div>
        </div>

        {/* Vessel Information Card (Sea Freight Only) */}
        {freightMode === "sea" && shipment.containerCount && (
          <div className="rounded-lg border border-[hsl(213,30%,25%)] bg-[hsl(213,50%,12%)] p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-base">🚢</span>
              <h4 className="text-xs font-heading font-bold text-[hsl(210,20%,75%)] uppercase tracking-wider">Vessel Verification</h4>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div>
                <div className="text-[10px] text-[hsl(210,20%,50%)] uppercase tracking-wider mb-1">Vessel</div>
                <div className="text-sm font-medium text-[hsl(210,20%,85%)]">{shipment.vessel || "—"}</div>
              </div>
              <div>
                <div className="text-[10px] text-[hsl(210,20%,50%)] uppercase tracking-wider mb-1">Carrier</div>
                <div className="text-sm font-medium text-[hsl(210,20%,85%)]">{shipment.carrier}</div>
              </div>
              <div>
                <div className="text-[10px] text-[hsl(210,20%,50%)] uppercase tracking-wider mb-1">Containers</div>
                <div className="text-sm font-medium text-[hsl(210,20%,85%)]">{shipment.containerCount}</div>
              </div>
              <div>
                <div className="text-[10px] text-[hsl(210,20%,50%)] uppercase tracking-wider mb-1">Verified</div>
                <div className="text-sm font-medium text-success">{shipment.verifiedContainers}</div>
              </div>
              <div>
                <div className="text-[10px] text-[hsl(210,20%,50%)] uppercase tracking-wider mb-1">Flagged</div>
                <div className="text-sm font-medium text-destructive flex items-center gap-1">
                  {shipment.flaggedContainers}
                  {shipment.flaggedContainers && shipment.flaggedContainers > 0 && (
                    <AlertTriangle className="h-3 w-3" />
                  )}
                </div>
              </div>
            </div>

            {/* Container Verification Progress Bar */}
            {shipment.containerCount && shipment.verifiedContainers !== undefined && (
              <div className="mt-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-[hsl(210,20%,55%)]">Container Verification Progress</span>
                  <span className="text-xs font-mono text-[hsl(210,20%,75%)]">{Math.round(containerProgress)}%</span>
                </div>
                <div className="h-2 bg-[hsl(213,50%,10%)] rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-accent to-success transition-all duration-500"
                    style={{ width: `${containerProgress}%` }}
                  />
                </div>
                <div className="text-xs text-[hsl(210,20%,50%)] mt-1">
                  {shipment.verifiedContainers} / {shipment.containerCount} containers verified
                </div>
              </div>
            )}

            {/* Inspection Flag */}
            {shipment.flaggedContainers && shipment.flaggedContainers > 0 && (
              <div className="mt-3 flex items-center gap-2 p-2 rounded bg-destructive/10 border border-destructive/30">
                <AlertTriangle className="h-4 w-4 text-destructive" />
                <span className="text-xs text-destructive font-medium">
                  {shipment.flaggedContainers} container{shipment.flaggedContainers > 1 ? 's' : ''} flagged — Inspection Required
                </span>
              </div>
            )}
          </div>
        )}

        {/* Vessel Trust Score Panel */}
        {freightMode === "sea" && shipment.containerCount && (
          <div className={`rounded-lg border border-[hsl(213,30%,25%)] bg-gradient-to-br ${getTrustScoreBgColor(trustScore)} p-4`}>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-base">📊</span>
              <h4 className="text-xs font-heading font-bold text-[hsl(210,20%,75%)] uppercase tracking-wider">Vessel Trust Score</h4>
            </div>

            <div className="flex items-baseline gap-2 mb-2">
              <span className={`text-4xl font-heading font-black ${getTrustScoreColor(trustScore)}`}>{trustScore}</span>
              <span className="text-lg text-[hsl(210,20%,55%)]">/ 100</span>
            </div>

            {/* Trust Score Progress Bar */}
            <div className="mb-3">
              <div className="h-3 bg-[hsl(213,50%,10%)] rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${
                    trustScore >= 80 ? 'bg-success' : trustScore >= 50 ? 'bg-warning' : 'bg-destructive'
                  }`}
                  style={{ width: `${trustScore}%` }}
                />
              </div>
            </div>

            <div className={`text-sm font-heading font-bold ${getTrustScoreColor(trustScore)}`}>
              {getTrustScoreInterpretation(trustScore)}
            </div>
          </div>
        )}

        {/* Container Intelligence Section */}
        {freightMode === "sea" && containers.length > 0 && (
          <div className="rounded-lg border border-[hsl(213,30%,25%)] bg-[hsl(213,50%,12%)] p-4">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-base">📦</span>
              <h4 className="text-xs font-heading font-bold text-[hsl(210,20%,75%)] uppercase tracking-wider">Container Intelligence</h4>
            </div>

            {/* Container Visualization Grid */}
            <div className="mb-4">
              <div className="text-[10px] text-[hsl(210,20%,50%)] uppercase tracking-wider mb-2">Container Map</div>
              <div className="flex flex-wrap gap-1">
                {containers.map((container) => (
                  <div
                    key={container.id}
                    className={`w-6 h-6 rounded transition-all hover:scale-110 cursor-pointer ${
                      container.status === 'verified' 
                        ? 'bg-success' 
                        : container.status === 'flagged' 
                        ? 'bg-destructive' 
                        : 'bg-[hsl(210,20%,40%)]'
                    }`}
                    title={`${container.id} - ${container.status}`}
                  />
                ))}
              </div>
              <div className="flex items-center gap-4 mt-2 text-xs text-[hsl(210,20%,55%)]">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded bg-success" />
                  <span>Verified</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded bg-destructive" />
                  <span>Flagged</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded bg-[hsl(210,20%,40%)]" />
                  <span>Pending</span>
                </div>
              </div>
            </div>

            {/* Container Verification Table */}
            <div>
              <div className="text-[10px] text-[hsl(210,20%,50%)] uppercase tracking-wider mb-2">Container Verification</div>
              <div className="max-h-64 overflow-y-auto border border-[hsl(213,30%,22%)] rounded-lg">
                <table className="w-full text-xs">
                  <thead className="bg-[hsl(213,50%,10%)] sticky top-0">
                    <tr>
                      <th className="text-left p-2 text-[hsl(210,20%,55%)] font-heading font-bold uppercase tracking-wider">Container ID</th>
                      <th className="text-left p-2 text-[hsl(210,20%,55%)] font-heading font-bold uppercase tracking-wider">Status</th>
                      <th className="text-left p-2 text-[hsl(210,20%,55%)] font-heading font-bold uppercase tracking-wider">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {containers.map((container, index) => (
                      <tr 
                        key={container.id}
                        className={`border-t border-[hsl(213,30%,22%)] hover:bg-[hsl(213,50%,10%)] transition-colors ${
                          index % 2 === 0 ? 'bg-[hsl(213,50%,8%)]' : ''
                        }`}
                      >
                        <td className="p-2 font-mono text-[hsl(210,20%,75%)]">{container.id}</td>
                        <td className="p-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-heading font-bold uppercase tracking-wider ${
                            container.status === 'verified' 
                              ? 'bg-success/20 text-success' 
                              : container.status === 'flagged' 
                              ? 'bg-destructive/20 text-destructive' 
                              : 'bg-[hsl(210,20%,30%)] text-[hsl(210,20%,60%)]'
                          }`}>
                            {container.status === 'verified' && <CheckCircle className="h-2.5 w-2.5" />}
                            {container.status === 'flagged' && <AlertTriangle className="h-2.5 w-2.5" />}
                            {container.status === 'pending' && <Clock className="h-2.5 w-2.5" />}
                            {container.status}
                          </span>
                        </td>
                        <td className="p-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-heading font-bold uppercase tracking-wider border ${
                            container.riskLevel === 'low' 
                              ? containerRiskConfig.low.bgColor + ' ' + containerRiskConfig.low.color
                              : container.riskLevel === 'medium' 
                              ? containerRiskConfig.medium.bgColor + ' ' + containerRiskConfig.medium.color
                              : containerRiskConfig.high.bgColor + ' ' + containerRiskConfig.high.color
                          }`}>
                            {container.riskLevel}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Clearance Recommendation Panel */}
        {receipt && receipt.clearanceRecommendation && (
          <div className={`rounded-lg border p-4 ${clearanceConfig[clearanceRecommendation]?.bgColor || "bg-[hsl(213,50%,12%)] border-[hsl(213,30%,25%)]"}`}>
            <div className="flex items-center gap-2 mb-2">
              <ClearanceIcon className={`h-5 w-5 ${clearanceConfig[clearanceRecommendation]?.color || "text-[hsl(210,20%,75%)]"}`} />
              <h4 className="text-xs font-heading font-bold text-[hsl(210,20%,75%)] uppercase tracking-wider">Clearance Recommendation</h4>
            </div>
            <p className={`text-sm font-heading font-bold ${clearanceConfig[clearanceRecommendation]?.color || "text-[hsl(210,20%,85%)]"}`}>
              {clearanceRecommendation}
            </p>
          </div>
        )}

        {/* Port Risk Intelligence */}
        {receipt && receipt.riskScore !== undefined && (
          <div className="rounded-lg border border-[hsl(213,30%,25%)] bg-[hsl(213,50%,12%)] p-4">
            <div className="flex items-center gap-2 mb-3">
              <Ship className="h-4 w-4 text-accent" />
              <h4 className="text-xs font-heading font-bold text-[hsl(210,20%,75%)] uppercase tracking-wider">Port Risk Intelligence</h4>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-[10px] text-[hsl(210,20%,50%)] uppercase tracking-wider mb-2">Risk Score</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-heading font-black text-[hsl(210,20%,88%)]">{receipt.riskScore}</span>
                  <span className="text-sm text-[hsl(210,20%,55%)]">/ 100</span>
                </div>
              </div>
              <div>
                <div className="text-[10px] text-[hsl(210,20%,50%)] uppercase tracking-wider mb-2">Risk Level</div>
                <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded text-xs font-heading font-bold uppercase tracking-wider border ${riskConfig[riskLevel].color}`}>
                  <span className={`h-2 w-2 rounded-full ${riskConfig[riskLevel].badgeColor}`} />
                  {riskConfig[riskLevel].label}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PreClearanceIntelligencePanel;
