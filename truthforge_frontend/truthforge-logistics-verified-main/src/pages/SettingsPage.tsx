import { useMockMode } from "@/contexts/MockModeContext";
import { Switch } from "@/components/ui/switch";
import { Settings, Database, Globe, Shield, Key, Bell, Copy, RotateCw, Code, BookOpen } from "lucide-react";

const SettingsPage = () => {
  const { isMockMode, toggleMockMode } = useMockMode();

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
          <Settings className="h-5 w-5 text-accent" />
          Settings & Documentation
        </h2>
        <p className="text-sm text-muted-foreground mt-1">System configuration, integration management, and environment controls.</p>
      </div>

      {/* Data Mode */}
      <div className={`rounded-lg border-2 p-5 shadow-card ${
        isMockMode ? "border-warning/30 bg-warning/5" : "border-success/30 bg-success/5"
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="h-5 w-5 text-accent" />
            <div>
              <h3 className="font-heading font-bold text-sm text-foreground">Data Mode</h3>
              <p className="text-xs text-muted-foreground">Switch between simulated demo data and live backend connections.</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-xs font-heading font-bold uppercase tracking-wider ${isMockMode ? "text-warning" : "text-success"}`}>
              {isMockMode ? "Mock Mode" : "Live Mode"}
            </span>
            <Switch checked={!isMockMode} onCheckedChange={toggleMockMode} aria-label="Toggle data mode" />
          </div>
        </div>
        {isMockMode && (
          <div className="mt-3 p-3 rounded border border-warning/20 bg-warning/5">
            <p className="text-xs text-warning font-medium">Mock mode active — All data is simulated. Switch to Live to connect to Hedera agents and carrier feeds.</p>
          </div>
        )}
      </div>

      {/* Integration Configuration */}
      <div className="rounded-lg border border-border bg-card p-5 shadow-card space-y-4 hover:shadow-elevated transition-all duration-200">
        <div>
          <h3 className="text-sm font-heading font-bold text-foreground">Integration Configuration</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Configure connections to port management systems and carrier endpoints.</p>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-foreground block mb-1.5">Port Authority Webhook URL</label>
            <div className="flex gap-2">
              <div className="flex-1 rounded border border-input bg-secondary/30 px-3 py-2 font-mono text-xs text-muted-foreground">
                https://api.port.authority.local/v1/truthforge/webhook
              </div>
              <button className="p-2 rounded border border-input hover:bg-accent/10 hover:border-accent/30 transition-colors" aria-label="Copy">
                <Copy className="h-3.5 w-3.5 text-muted-foreground" />
              </button>
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-foreground block mb-1.5">Hedera Account ID (Billing)</label>
            <div className="rounded border border-input bg-secondary/30 px-3 py-2 font-mono text-xs text-muted-foreground">
              0.0.123456
            </div>
          </div>
        </div>
      </div>

      {/* API Credentials */}
      <div className="rounded-lg border border-border bg-card p-5 shadow-card space-y-4 hover:shadow-elevated transition-all duration-200">
        <div>
          <h3 className="text-sm font-heading font-bold text-foreground">API Credentials</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Credentials for automated ingestion. Keep these secure.</p>
        </div>
        <div>
          <label className="text-xs font-medium text-foreground block mb-1.5">Bearer Token</label>
          <div className="flex gap-2">
            <div className="flex-1 rounded border border-input bg-secondary/30 px-3 py-2 font-mono text-xs text-muted-foreground tracking-widest">
              ••••••••••••••••••••
            </div>
            <button className="px-3 py-2 rounded border border-input text-xs font-medium text-muted-foreground hover:bg-accent/10 hover:border-accent/30 hover:text-foreground transition-colors">
              <span className="flex items-center gap-1.5"><RotateCw className="h-3 w-3" />Rotate</span>
            </button>
          </div>
        </div>
      </div>

      {/* Integration Status */}
      <div className="rounded-lg border border-border bg-card p-5 shadow-card space-y-4 hover:shadow-elevated transition-all duration-200">
        <h3 className="text-sm font-heading font-bold text-muted-foreground uppercase tracking-wider">Integration Status</h3>
        {[
          { icon: Globe, name: "Hedera Network", status: "Connected", connected: true, detail: "Mainnet — HCS Topics Active" },
          { icon: Shield, name: "Carrier Council", status: "Connected", connected: true, detail: "Council-grade data adapters enabled" },
          { icon: Key, name: "WooCommerce", status: "Configured", connected: true, detail: "REST API — a-thi.online" },
          { icon: Bell, name: "Webhook Notifications", status: "Pending Setup", connected: false, detail: "Configure endpoint URL" },
        ].map((item) => (
          <div key={item.name} className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
            <div className="flex items-center gap-3">
              <item.icon className="h-4 w-4 text-muted-foreground" />
              <div>
                <span className="text-sm font-medium text-foreground">{item.name}</span>
                <p className="text-[10px] text-muted-foreground">{item.detail}</p>
              </div>
            </div>
            <span className={`text-[10px] font-heading font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
              item.connected ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
            }`}>
              {item.status}
            </span>
          </div>
        ))}
      </div>

      {/* System Documentation */}
      <div className="rounded-lg border border-border bg-card p-5 shadow-card hover:shadow-elevated transition-all duration-200">
        <div className="flex items-center gap-2 mb-2">
          <Code className="h-4 w-4 text-accent" />
          <h3 className="text-sm font-heading font-bold text-foreground">System Documentation</h3>
        </div>
        <p className="text-xs text-muted-foreground mb-4">Access the official TruthForge operational manuals and technical integration guides.</p>
        <div className="flex flex-wrap gap-3">
          {[
            { label: "REST API Reference", icon: BookOpen },
            { label: "Agent SDK Guide", icon: Code },
            { label: "HCS Data Schema", icon: Database },
          ].map(doc => (
            <button key={doc.label} className="inline-flex items-center gap-1.5 text-xs text-accent font-medium hover:underline">
              <doc.icon className="h-3 w-3" />
              {doc.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
