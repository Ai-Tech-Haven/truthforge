import AgentCard from "@/components/AgentCard";
import { mockAgents } from "@/lib/mock-data";
import { Cpu, Info } from "lucide-react";

const AgentsPage = () => (
  <div className="space-y-6">
    <div>
      <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
        <Cpu className="h-5 w-5 text-accent" />
        HOL-Registered Operational Agents
      </h2>
      <div className="flex items-center gap-3 mt-1">
        <span className="text-xs font-heading font-bold text-success bg-success/10 border border-success/20 px-2.5 py-1 rounded uppercase tracking-wider">
          5 / 5 Agents Active
        </span>
        <span className="text-xs text-muted-foreground">Registry: HOL Registry</span>
        <span className="text-xs text-muted-foreground">Messaging: HCS-10</span>
        <span className="text-xs text-muted-foreground">Verification Layer: Hedera</span>
      </div>
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
            <th className="py-3 px-4 text-left text-[10px] font-heading font-bold text-muted-foreground uppercase tracking-wider">Operational Status</th>
          </tr>
        </thead>
        <tbody>
          {mockAgents.map((agent) => (
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
                <span className="inline-flex items-center gap-1.5 text-xs font-heading font-bold text-success">
                  <span className="h-2 w-2 rounded-full bg-success" />
                  Active
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>

    {/* Agent Cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {mockAgents.map((agent) => (
        <AgentCard key={agent.id} agent={agent} />
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
      </p>
    </div>
  </div>
);

export default AgentsPage;
