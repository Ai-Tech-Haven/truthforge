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

const AgentCard = ({ agent }: { agent: Agent }) => (
  <div className="rounded-xl border border-border bg-card p-4 shadow-card hover:shadow-elevated hover:border-accent/30 transition-all duration-200">
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <Cpu className="h-4 w-4 text-accent" />
        <h4 className="font-heading font-bold text-sm text-foreground">{agent.name}</h4>
      </div>
      <div className="flex items-center gap-1.5">
        <span className={`h-2 w-2 rounded-full ${statusColors[agent.status]} ${agent.status === "processing" ? "animate-pulse" : ""}`} />
        <span className="text-xs text-muted-foreground">{statusLabels[agent.status]}</span>
      </div>
    </div>

    <div className="space-y-2 text-xs">
      <div className="flex justify-between">
        <span className="text-muted-foreground">Agent ID</span>
        <span className="font-mono text-foreground">{agent.agentId}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">HCS Topic</span>
        <span className="font-mono text-foreground">{agent.hcsTopic}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Primary Function</span>
        <span className="text-foreground text-right max-w-[60%]">{agent.primaryFunction}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-muted-foreground">Health</span>
        <div className="flex items-center gap-2">
          <div className="w-16 h-1.5 bg-secondary rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${agent.health > 90 ? "bg-success" : agent.health > 50 ? "bg-warning" : "bg-destructive"}`}
              style={{ width: `${agent.health}%` }}
            />
          </div>
          <span className="font-medium text-foreground">{agent.health}%</span>
        </div>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Last Active</span>
        <div className="flex items-center gap-1">
          <Activity className="h-3 w-3 text-accent" />
          <span className="text-foreground">{agent.lastActive}</span>
        </div>
      </div>
    </div>
  </div>
);

export default AgentCard;
