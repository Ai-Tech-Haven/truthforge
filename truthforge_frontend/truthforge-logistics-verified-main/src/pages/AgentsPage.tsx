import { useEffect, useState, useCallback } from "react";
import AgentCard from "@/components/AgentCard";
import { mockAgents, Agent } from "@/lib/mock-data";
import { useMockMode } from "@/contexts/MockModeContext";
import { Cpu, Info, RefreshCw, XCircle } from "lucide-react";

const RAILWAY = "https://web-production-dcd43.up.railway.app";
const POLL_INTERVAL = 15_000; // 15 s real-time refresh

// Agents that get the navy highlight card
const NAVY_AGENTS = new Set([
  "truthforge-orch-001",
  "truthforge-carrier-001",
  "truthforge-evidence-001",
]);

// Shape returned by /api/agents
interface LiveAgent {
  id: string;
  name: string;
  agentId: string;
  uaid?: string;
  primaryFunction: string;
  hcsTopic: string;
  status: string;
  health?: number;
  lastActive?: string;
  capabilities?: string[];
}

function mapLiveAgent(a: LiveAgent): Agent {
  return {
    id: a.id,
    name: a.name,
    agentId: a.agentId,
    uaid: a.uaid || "",
    hcsTopic: a.hcsTopic || "—",
    status: (a.status === "online" ? "online" : a.status === "processing" ? "processing" : "offline") as Agent["status"],
    health: typeof a.health === "number" ? a.health : 95,
    lastActive: a.lastActive || "Unknown",
    primaryFunction: a.primaryFunction,
  };
}

const AgentsPage = () => {
  const { isMockMode } = useMockMode();
  const [agents, setAgents] = useState<Agent[]>(mockAgents);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSync, setLastSync] = useState<string | null>(null);

  const fetchAgents = useCallback(async (isBackground = false) => {
    if (isMockMode) {
      setAgents(mockAgents);
      setError(null);
      return;
    }
    if (!isBackground) setLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 12000);
      const res = await fetch(`${RAILWAY}/api/agents`, {
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json() as { agents: LiveAgent[] };
      const mapped = (data.agents || []).map(mapLiveAgent);
      if (mapped.length > 0) {
        setAgents(mapped);
        setError(null);
        setLastSync(new Date().toLocaleTimeString());
      } else {
        setError("Backend returned no agents — check Railway deployment");
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      const isTimeout = msg.includes("abort") || msg.includes("timeout") || msg.includes("signal");
      setError(`Backend unreachable — ${isTimeout ? "request timed out" : msg}`);
      // In live mode keep last known data (don't overwrite with mock)
    } finally {
      if (!isBackground) setLoading(false);
    }
  }, [isMockMode]);

  // Initial fetch + mode-change reset
  useEffect(() => {
    if (isMockMode) {
      setAgents(mockAgents);
      setError(null);
      setLastSync(null);
      return;
    }
    fetchAgents(false);
  }, [isMockMode, fetchAgents]);

  // Real-time polling in live mode
  useEffect(() => {
    if (isMockMode) return;
    const id = setInterval(() => fetchAgents(true), POLL_INTERVAL);
    return () => clearInterval(id);
  }, [isMockMode, fetchAgents]);

  const onlineCount = agents.filter(a => a.status === "online").length;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
          <Cpu className="h-5 w-5 text-accent" />
          HOL-Registered Operational Agents
        </h2>
        <div className="flex items-center gap-3 mt-1 flex-wrap">
          <span className={`text-xs font-heading font-bold px-2.5 py-1 rounded uppercase tracking-wider border ${
            onlineCount === agents.length
              ? "text-success bg-success/10 border-success/20"
              : onlineCount === 0
              ? "text-destructive bg-destructive/10 border-destructive/20"
              : "text-warning bg-warning/10 border-warning/20"
          }`}>
            {onlineCount} / {agents.length} Agents Active
          </span>
          <span className="text-xs text-muted-foreground">Registry: HOL Registry</span>
          <span className="text-xs text-muted-foreground">Messaging: HCS-10</span>
          <span className="text-xs text-muted-foreground">Verification Layer: Hedera</span>
          {loading && (
            <span className="flex items-center gap-1 text-xs text-accent">
              <RefreshCw className="h-3 w-3 animate-spin" /> Syncing…
            </span>
          )}
          {!isMockMode && !loading && lastSync && (
            <span className="text-xs text-success font-heading font-bold bg-success/10 border border-success/20 px-2 py-0.5 rounded uppercase tracking-wider">
              Live · {lastSync}
            </span>
          )}
          {!isMockMode && (
            <button
              onClick={() => fetchAgents(false)}
              className="flex items-center gap-1 text-[10px] text-accent hover:underline"
            >
              <RefreshCw className="h-3 w-3" /> Refresh
            </button>
          )}
        </div>

        {error && (
          <div className="flex items-start gap-2 mt-2 p-2.5 rounded border border-destructive/30 bg-destructive/5">
            <XCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
            <p className="text-xs text-destructive">{error}</p>
          </div>
        )}

        <p className="text-sm text-muted-foreground mt-2">
          This registry lists all authorized agents permitted to participate in verification, clearance, and evidence generation workflows.
          Only registered agents may produce auditable outcomes.
        </p>
      </div>

      {/* Agent Table */}
      <div className="rounded-xl border border-border bg-card shadow-card overflow-x-auto">
        <table className="w-full" role="table">
          <thead>
            <tr className="border-b border-border bg-secondary/50">
              <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Agent Name</th>
              <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Agent ID</th>
              <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Primary Function</th>
              <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">HCS Topic</th>
              <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Health</th>
              <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((agent) => (
              <tr key={agent.id} className="border-b border-border last:border-0 hover:bg-accent/5 transition-colors">
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-3.5 w-3.5 text-accent" />
                    <span className="text-sm font-medium text-foreground">{agent.name}</span>
                  </div>
                </td>
                <td className="py-3 px-4 font-mono text-xs text-muted-foreground">{agent.agentId}</td>
                <td className="py-3 px-4 text-xs text-muted-foreground">{agent.primaryFunction}</td>
                <td className="py-3 px-4 font-mono text-xs text-accent">{agent.hcsTopic}</td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <div className="w-14 h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${agent.health > 90 ? "bg-success" : agent.health > 50 ? "bg-warning" : "bg-destructive"}`}
                        style={{ width: `${agent.health}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">{agent.health}%</span>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <span className={`inline-flex items-center gap-1.5 text-xs font-heading font-bold ${
                    agent.status === "online" ? "text-success" :
                    agent.status === "processing" ? "text-warning" : "text-destructive"
                  }`}>
                    <span className={`h-2 w-2 rounded-full ${
                      agent.status === "online" ? "bg-success" :
                      agent.status === "processing" ? "bg-warning animate-pulse" : "bg-destructive"
                    }`} />
                    {agent.status === "online" ? "Active" : agent.status === "processing" ? "Processing" : "Offline"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            navy={NAVY_AGENTS.has(agent.agentId)}
          />
        ))}
      </div>

      {/* Registry Notices */}
      <div className="rounded-lg border border-border bg-secondary/30 p-4 space-y-2">
        <div className="flex items-center gap-2">
          <Info className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs font-heading font-bold text-muted-foreground uppercase tracking-wider">Registry Notices</span>
        </div>
        <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
          <li>This system operates with a fixed set of five (5) registered agents.</li>
          <li>Agent addition or removal requires registry update and redeployment.</li>
          <li>Only actions signed by registered agents may generate a Port Trust Receipt.</li>
        </ul>
        <p className="text-[10px] text-muted-foreground/60 pt-2 border-t border-border">
          Agent registry status reflects the current operational configuration approved for clearance and verification activities.
          {!isMockMode && lastSync && ` Last synced: ${lastSync}`}
        </p>
      </div>
    </div>
  );
};

export default AgentsPage;
