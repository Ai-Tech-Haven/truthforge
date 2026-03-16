import { useState, useEffect, useCallback } from "react";
import { useMockMode } from "@/contexts/MockModeContext";
import { Switch } from "@/components/ui/switch";
import {
  Settings, Database, Globe, Shield, Key, Bell, Copy, RotateCw,
  Code, BookOpen, Loader2, XCircle,
} from "lucide-react";

// ─── Config ───────────────────────────────────────────────────────────────────
// Hardcode Railway URL as the single source of truth for integration calls.
// This bypasses any apiFetch/mock-mode logic and hits the backend directly.
const RAILWAY = "https://web-production-dcd43.up.railway.app";

async function liveGet<T>(path: string): Promise<T> {
  const res = await fetch(`${RAILWAY}${path}`, {
    headers: { "Content-Type": "application/json" },
    signal: AbortSignal.timeout(8000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

async function livePost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${RAILWAY}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(8000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface IntegrationState {
  connected: boolean;
  detail: string;
}

interface WebhookState {
  merchant_url: string;
  carrier_url: string;
  port_authority_url: string;
}

interface IntegrationsStatus {
  hedera: IntegrationState;
  carrier_council: IntegrationState;
  woocommerce: IntegrationState;
  fedex: IntegrationState;
  webhooks: WebhookState;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const copyToClipboard = (text: string) => navigator.clipboard.writeText(text).catch(() => {});

// ─── Integration Row ──────────────────────────────────────────────────────────

interface IntegrationRowProps {
  icon: React.ElementType;
  name: string;
  detail: string;
  connected: boolean;
  loading: boolean;
  isMockMode: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}

const IntegrationRow = ({
  icon: Icon, name, detail, connected, loading, isMockMode, onConnect, onDisconnect,
}: IntegrationRowProps) => (
  <div className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
    <div className="flex items-center gap-3">
      <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
      <div>
        <span className="text-sm font-medium text-foreground">{name}</span>
        <p className="text-[10px] text-muted-foreground">{detail}</p>
      </div>
    </div>
    <div className="flex items-center gap-2">
      <span className={`text-[10px] font-heading font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
        connected ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive"
      }`}>
        {connected ? "Connected" : "Disconnected"}
      </span>
      {!isMockMode && (
        <button
          disabled={loading}
          onClick={connected ? onDisconnect : onConnect}
          className={`flex items-center gap-1 px-2.5 py-1 rounded text-[10px] font-bold uppercase tracking-wider border transition-colors disabled:opacity-50 ${
            connected
              ? "border-destructive/40 bg-destructive/10 text-destructive hover:bg-destructive/20"
              : "border-success/40 bg-success/10 text-success hover:bg-success/20"
          }`}
        >
          {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
          {connected ? "Disconnect" : "Connect"}
        </button>
      )}
    </div>
  </div>
);

// ─── Webhook URL Field ────────────────────────────────────────────────────────

const WebhookField = ({
  label, value, onChange, onSave, saving,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  onSave: () => void;
  saving: boolean;
}) => (
  <div>
    <label className="text-xs font-medium text-foreground block mb-1.5">{label}</label>
    <div className="flex gap-2">
      <input
        type="url"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder="https://..."
        className="flex-1 rounded border border-input bg-secondary/30 px-3 py-2 font-mono text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-accent/50"
      />
      <button
        onClick={() => copyToClipboard(value)}
        className="p-2 rounded border border-input hover:bg-accent/10 hover:border-accent/30 transition-colors"
        aria-label="Copy"
      >
        <Copy className="h-3.5 w-3.5 text-muted-foreground" />
      </button>
      <button
        onClick={onSave}
        disabled={saving || !value}
        className="px-3 py-1.5 rounded border border-accent/40 bg-accent/10 text-accent text-xs font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-40"
      >
        {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : "Save"}
      </button>
    </div>
  </div>
);

// ─── Main Page ────────────────────────────────────────────────────────────────

const SettingsPage = () => {
  const { isMockMode, toggleMockMode } = useMockMode();

  // Integration status state
  const [status, setStatus] = useState<IntegrationsStatus | null>(null);
  const [fetchError, setFetchError] = useState(false);
  const [lastError, setLastError] = useState("");
  const [loadingKey, setLoadingKey] = useState<string | null>(null);

  // Webhook URL local state (editable)
  const [merchantUrl, setMerchantUrl] = useState("");
  const [carrierUrl, setCarrierUrl] = useState("");
  const [portUrl, setPortUrl] = useState("");
  const [savingWebhook, setSavingWebhook] = useState(false);

  // ── Fetch integration status from backend (live mode only) ──────────────────
  const fetchStatus = useCallback(async () => {
    if (isMockMode) return;
    setFetchError(false);
    setLastError("");
    try {
      const data = await liveGet<IntegrationsStatus>("/api/integrations/status");
      setStatus(data);
      setMerchantUrl(data.webhooks.merchant_url || "");
      setCarrierUrl(data.webhooks.carrier_url || "");
      setPortUrl(data.webhooks.port_authority_url || "");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setLastError(msg);
      setFetchError(true);
    }
  }, [isMockMode]);

  useEffect(() => {
    if (!isMockMode) {
      // Reset stale state so loading spinner shows immediately on mode switch
      setStatus(null);
      setFetchError(false);
    }
    fetchStatus();
  }, [fetchStatus]);

  // ── Connect / Disconnect ────────────────────────────────────────────────────
  const toggle = async (key: string, action: "connect" | "disconnect") => {
    setLoadingKey(key);
    try {
      await livePost(`/api/integrations/${key}/${action}`);
      await fetchStatus();
    } catch {
      // silently fail — status will stay as-is
    } finally {
      setLoadingKey(null);
    }
  };

  // ── Save webhook URLs ───────────────────────────────────────────────────────
  const saveWebhook = async (field: "merchant" | "carrier" | "port_authority") => {
    setSavingWebhook(true);
    try {
      const payload: Record<string, string> = {};
      if (field === "merchant") payload.merchant_url = merchantUrl;
      if (field === "carrier") payload.carrier_url = carrierUrl;
      if (field === "port_authority") payload.port_authority_url = portUrl;
      await livePost("/api/integrations/webhook/configure", payload);
      await fetchStatus();
    } catch {
      // silently fail
    } finally {
      setSavingWebhook(false);
    }
  };

  // ── Mock-mode static values ─────────────────────────────────────────────────
  const mockStatus: IntegrationsStatus = {
    hedera: { connected: true, detail: "Testnet — HCS Topics Active" },
    carrier_council: { connected: true, detail: "Council-grade data adapters enabled" },
    woocommerce: { connected: true, detail: "REST API — a-thi.online" },
    fedex: { connected: true, detail: "FedEx Ship API" },
    webhooks: { merchant_url: "", carrier_url: "", port_authority_url: "" },
  };

  const s = isMockMode ? mockStatus : status;

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h2 className="text-xl font-heading font-bold text-foreground flex items-center gap-2">
          <Settings className="h-5 w-5 text-accent" />
          Settings &amp; Documentation
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          System configuration, integration management, and environment controls.
        </p>
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
              <p className="text-xs text-muted-foreground">
                Switch between simulated demo data and live backend connections.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-xs font-heading font-bold uppercase tracking-wider ${
              isMockMode ? "text-warning" : "text-success"
            }`}>
              {isMockMode ? "Mock Mode" : "Live Mode"}
            </span>
            <Switch checked={!isMockMode} onCheckedChange={toggleMockMode} aria-label="Toggle data mode" />
          </div>
        </div>
        {isMockMode && (
          <div className="mt-3 p-3 rounded border border-warning/20 bg-warning/5">
            <p className="text-xs text-warning font-medium">
              Mock mode active — All data is simulated. Switch to Live to connect to Hedera agents and carrier feeds.
            </p>
          </div>
        )}
      </div>

      {/* Integration Configuration */}
      <div className="rounded-lg border border-border bg-card p-5 shadow-card space-y-4">
        <div>
          <h3 className="text-sm font-heading font-bold text-foreground">Integration Configuration</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Configure webhook endpoints for each portal role.
            {isMockMode && <span className="text-warning ml-1">(Read-only in mock mode)</span>}
          </p>
        </div>
        <div className="space-y-3">
          {isMockMode ? (
            <>
              {[
                { label: "Merchant Webhook URL", val: "https://api.truthforge.io/v1/merchant/webhook" },
                { label: "Carrier Webhook URL", val: "https://api.truthforge.io/v1/carrier/webhook" },
                { label: "Port Authority Webhook URL", val: "https://api.truthforge.io/v1/port-authority/webhook" },
              ].map(f => (
                <div key={f.label}>
                  <label className="text-xs font-medium text-foreground block mb-1.5">{f.label}</label>
                  <div className="flex gap-2">
                    <div className="flex-1 rounded border border-input bg-secondary/30 px-3 py-2 font-mono text-xs text-muted-foreground">
                      {f.val}
                    </div>
                    <button
                      onClick={() => copyToClipboard(f.val)}
                      className="p-2 rounded border border-input hover:bg-accent/10 transition-colors"
                      aria-label="Copy"
                    >
                      <Copy className="h-3.5 w-3.5 text-muted-foreground" />
                    </button>
                  </div>
                </div>
              ))}
            </>
          ) : (
            <>
              <WebhookField
                label="Merchant Webhook URL"
                value={merchantUrl}
                onChange={setMerchantUrl}
                onSave={() => saveWebhook("merchant")}
                saving={savingWebhook}
              />
              <WebhookField
                label="Carrier Webhook URL"
                value={carrierUrl}
                onChange={setCarrierUrl}
                onSave={() => saveWebhook("carrier")}
                saving={savingWebhook}
              />
              <WebhookField
                label="Port Authority Webhook URL"
                value={portUrl}
                onChange={setPortUrl}
                onSave={() => saveWebhook("port_authority")}
                saving={savingWebhook}
              />
            </>
          )}
        </div>
      </div>

      {/* API Credentials */}
      <div className="rounded-lg border border-border bg-card p-5 shadow-card space-y-4">
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
      <div className="rounded-lg border border-border bg-card p-5 shadow-card space-y-1">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-heading font-bold text-muted-foreground uppercase tracking-wider">
            Integration Status
          </h3>
          {!isMockMode && (
            <button
              onClick={fetchStatus}
              className="flex items-center gap-1 text-[10px] text-accent hover:underline"
            >
              <RotateCw className="h-3 w-3" /> Refresh
            </button>
          )}
        </div>

        {!isMockMode && fetchError && (
          <div className="flex items-start gap-2 p-3 rounded border border-destructive/30 bg-destructive/5 mb-3">
            <XCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
            <div>
              <p className="text-xs text-destructive font-medium">Could not reach backend.</p>
              {lastError && <p className="text-[10px] text-destructive/70 mt-0.5 font-mono break-all">{lastError}</p>}
            </div>
          </div>
        )}

        {!isMockMode && !s && !fetchError && (
          <div className="flex items-center gap-2 py-4 text-xs text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading integration status...
          </div>
        )}

        {s && (
          <>
            <IntegrationRow
              icon={Globe}
              name="Hedera Network"
              detail={s.hedera.detail}
              connected={s.hedera.connected}
              loading={loadingKey === "hedera"}
              isMockMode={isMockMode}
              onConnect={() => toggle("hedera", "connect")}
              onDisconnect={() => toggle("hedera", "disconnect")}
            />
            <IntegrationRow
              icon={Shield}
              name="Carrier Council"
              detail={s.carrier_council.detail}
              connected={s.carrier_council.connected}
              loading={loadingKey === "carrier-council"}
              isMockMode={isMockMode}
              onConnect={() => toggle("carrier-council", "connect")}
              onDisconnect={() => toggle("carrier-council", "disconnect")}
            />
            <IntegrationRow
              icon={Key}
              name="WooCommerce"
              detail={s.woocommerce.detail}
              connected={s.woocommerce.connected}
              loading={loadingKey === "woocommerce"}
              isMockMode={isMockMode}
              onConnect={() => toggle("woocommerce", "connect")}
              onDisconnect={() => toggle("woocommerce", "disconnect")}
            />
            <IntegrationRow
              icon={Bell}
              name="Webhook Notifications"
              detail={
                s.webhooks.merchant_url || s.webhooks.carrier_url || s.webhooks.port_authority_url
                  ? "Endpoints configured"
                  : isMockMode ? "Configure endpoint URL" : "No endpoints saved yet"
              }
              connected={
                !!(s.webhooks.merchant_url || s.webhooks.carrier_url || s.webhooks.port_authority_url)
              }
              loading={false}
              isMockMode={true /* no connect/disconnect for webhooks — managed via URL fields */}
              onConnect={() => {}}
              onDisconnect={() => {}}
            />
          </>
        )}
      </div>

      {/* System Documentation */}
      <div className="rounded-lg border border-border bg-card p-5 shadow-card">
        <div className="flex items-center gap-2 mb-2">
          <Code className="h-4 w-4 text-accent" />
          <h3 className="text-sm font-heading font-bold text-foreground">System Documentation</h3>
        </div>
        <p className="text-xs text-muted-foreground mb-4">
          Access the official TruthForge operational manuals and technical integration guides.
        </p>
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
