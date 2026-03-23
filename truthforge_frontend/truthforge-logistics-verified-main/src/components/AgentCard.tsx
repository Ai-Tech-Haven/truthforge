import { Agent } from "@/lib/mock-data";
import { Activity, Cpu } from "lucide-react";

const statusColors = {
  online: "bg-success",
  offline: "bg-destructive",
  processing: "bg-warning",
};

const statusLabels = {
  online: "Active",
  offline: "Offline",
  processing: "Processing",
};

interface AgentCardProps {
  agent: Agent;
  navy?: boolean;
}

const AgentCard = ({ agent, navy = false }: AgentCardProps) => (
  <div className={`rounded-xl border p-4 shadow-card hover:shadow-elevated transition-all duration-200 ${
    navy
      ? "border-[#1e3a5f]/60 bg-[#0d2340] hover:border-[#2a5298]/60"
      : "border-border bg-card hover:border-accent/30"
  }`}>
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <Cpu className={`h-4 w-4 ${navy ? "text-[#4a9eff]" : "text-accent"}`} />
        <h4 className={`font-heading font-bold text-sm ${navy ? "text-[#e8f4ff]" : "text-foreground"}`}>
          {agent.name}
        </h4>
      </div>
      <div className="flex items-center gap-1.5">
        <span className={`h-2 w-2 rounded-full ${statusColors[agent.status]} ${agent.status === "processing" ? "animate-pulse" : ""}`} />
        <span className={`text-xs ${navy ? "text-[#8ab4d4]" : "text-muted-foreground"}`}>
          {statusLabels[agent.status]}
        </span>
      </div>
    </div>

    <div className="space-y-2 text-xs">
      <div className="flex justify-between">
        <span className={navy ? "text-[#8ab4d4]" : "text-muted-foreground"}>Agent ID</span>
        <span className={`font-mono ${navy ? "text-[#c8e0f4]" : "text-foreground"}`}>{agent.agentId}</span>
      </div>
      {agent.uaid && (
        <div className="flex justify-between gap-2">
          <span className={`shrink-0 ${navy ? "text-[#8ab4d4]" : "text-muted-foreground"}`}>UAID</span>
          <span className={`font-mono text-right truncate max-w-[65%] ${navy ? "text-[#4a9eff]" : "text-accent"}`} title={agent.uaid}>
            {agent.uaid}
          </span>
        </div>
      )}
      <div className="flex justify-between">
        <span className={navy ? "text-[#8ab4d4]" : "text-muted-foreground"}>HCS Topic</span>
        <span className={`font-mono ${navy ? "text-[#4a9eff]" : "text-foreground"}`}>{agent.hcsTopic}</span>
      </div>
      <div className="flex justify-between">
        <span className={navy ? "text-[#8ab4d4]" : "text-muted-foreground"}>Primary Function</span>
        <span className={`text-right max-w-[60%] ${navy ? "text-[#c8e0f4]" : "text-foreground"}`}>
          {agent.primaryFunction}
        </span>
      </div>
      <div className="flex justify-between items-center">
        <span className={navy ? "text-[#8ab4d4]" : "text-muted-foreground"}>Health</span>
        <div className="flex items-center gap-2">
          <div className={`w-16 h-1.5 rounded-full overflow-hidden ${navy ? "bg-[#1e3a5f]" : "bg-secondary"}`}>
            <div
              className={`h-full rounded-full ${agent.health > 90 ? "bg-success" : agent.health > 50 ? "bg-warning" : "bg-destructive"}`}
              style={{ width: `${agent.health}%` }}
            />
          </div>
          <span className={`font-medium ${navy ? "text-[#c8e0f4]" : "text-foreground"}`}>{agent.health}%</span>
        </div>
      </div>
      <div className="flex justify-between">
        <span className={navy ? "text-[#8ab4d4]" : "text-muted-foreground"}>Last Active</span>
        <div className="flex items-center gap-1">
          <Activity className={`h-3 w-3 ${navy ? "text-[#4a9eff]" : "text-accent"}`} />
          <span className={navy ? "text-[#c8e0f4]" : "text-foreground"}>{agent.lastActive}</span>
        </div>
      </div>
    </div>
  </div>
);

export default AgentCard;
