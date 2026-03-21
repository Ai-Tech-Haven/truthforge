import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Switch } from "@/components/ui/switch";
import { useMockMode } from "@/contexts/MockModeContext";
import { useTheme } from "@/contexts/ThemeContext";
import WalletConnectCard from "@/components/WalletConnectCard";
import logo from "@/assets/truthforge-logo.png";
import {
  Database, Sun, Moon, ChevronDown, Anchor, BarChart3,
  FileText, Cpu, Plug, HelpCircle, Building2, Package,
  Ship, X, BookOpen, Code, MessageSquare,
} from "lucide-react";

const RAILWAY = "https://web-production-dcd43.up.railway.app";

// ─── Types ───────────────────────────────────────────────────────────────────

interface DropdownItem {
  path?: string;
  label: string;
  icon?: React.ElementType;
  badge?: string;
  badgeColor?: string;
  disabled?: boolean;
}

interface DropdownMenuProps {
  label: string;
  icon?: React.ElementType;
  items: DropdownItem[];
}

// ─── Dropdown ────────────────────────────────────────────────────────────────

const DropdownMenu = ({ label, icon: Icon, items }: DropdownMenuProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setOpen(true);
  };

  const handleMouseLeave = () => {
    closeTimer.current = setTimeout(() => setOpen(false), 120);
  };

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => {
      document.removeEventListener("mousedown", handler);
      if (closeTimer.current) clearTimeout(closeTimer.current);
    };
  }, []);

  const isActive = items.some(i => i.path && location.pathname === i.path);

  return (
    <div
      className="relative"
      ref={ref}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Trigger button — fixed height, no layout-shifting transitions */}
      <button
        onClick={() => setOpen(o => !o)}
        className={`flex items-center gap-1.5 px-3 h-9 text-xs font-semibold uppercase tracking-wide rounded whitespace-nowrap transition-colors duration-150 ${
          isActive
            ? "bg-accent/20 text-white"
            : "text-slate-300 hover:text-white hover:bg-white/10"
        }`}
      >
        {Icon && <Icon className="h-4 w-4 shrink-0" />}
        <span className="hidden md:inline">{label}</span>
        <ChevronDown
          className={`h-3.5 w-3.5 shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>

      {/* Dropdown panel — rendered outside header flow via absolute positioning */}
      {open && (
        <div
          className="absolute top-full left-0 mt-1.5 min-w-[210px] rounded-md border border-white/10 bg-[#0b1f33] shadow-lg z-[9999] py-1 overflow-hidden"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          {items.map(item => {
            const ItemIcon = item.icon;
            const isItemActive = item.path ? location.pathname === item.path : false;
            return (
              <button
                key={item.label}
                disabled={item.disabled}
                onClick={() => {
                  if (!item.disabled && item.path) {
                    navigate(item.path);
                    setOpen(false);
                  }
                }}
                className={`w-full flex items-center justify-between gap-2 px-4 py-2.5 text-sm transition-colors duration-100 ${
                  item.disabled
                    ? "text-slate-600 cursor-not-allowed"
                    : isItemActive
                    ? "bg-accent/20 text-white font-semibold"
                    : "text-slate-200 hover:bg-white/8 hover:text-white"
                }`}
              >
                <span className="flex items-center gap-2.5">
                  {ItemIcon && <ItemIcon className="h-4 w-4 shrink-0 opacity-70" />}
                  {item.label}
                </span>
                {item.badge && (
                  <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${item.badgeColor || "border-white/20 text-slate-400"}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

// ─── Help Modal ───────────────────────────────────────────────────────────────

const HelpModal = ({ onClose }: { onClose: () => void }) => (
  <div
    className="fixed inset-0 z-[200] bg-black/60 flex items-center justify-center p-4"
    onClick={onClose}
  >
    <div
      className="bg-card border border-border rounded-xl p-6 max-w-md w-full shadow-elevated"
      onClick={e => e.stopPropagation()}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-heading font-bold text-foreground flex items-center gap-2">
          <HelpCircle className="h-4 w-4 text-accent" />
          Help &amp; Documentation
        </h3>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-opacity">
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="space-y-3">
        {[
          { icon: BookOpen, label: "REST API Reference", desc: "Full API docs for backend integration" },
          { icon: Code, label: "Agent SDK Guide", desc: "Build and register custom agents" },
          { icon: Database, label: "HCS Data Schema", desc: "Hedera Consensus Service message formats" },
          { icon: MessageSquare, label: "Support Chat", desc: "Talk to the TruthForge team" },
        ].map(item => (
          <div
            key={item.label}
            className="flex items-start gap-3 p-3 rounded-lg border border-border hover:bg-secondary/50 transition-colors cursor-pointer"
          >
            <item.icon className="h-4 w-4 text-accent mt-0.5 shrink-0" />
            <div>
              <div className="text-sm font-medium text-foreground">{item.label}</div>
              <div className="text-xs text-muted-foreground">{item.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

// ─── Header ───────────────────────────────────────────────────────────────────

const Header = () => {
  const { isMockMode, toggleMockMode } = useMockMode();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [helpOpen, setHelpOpen] = useState(false);

  // Live integration badge state
  const [wcConnected, setWcConnected] = useState(true);
  const [fedexConnected, setFedexConnected] = useState(true);

  const fetchBadges = useCallback(async () => {
    if (isMockMode) { setWcConnected(true); setFedexConnected(true); return; }
    try {
      const res = await fetch(`${RAILWAY}/api/integrations/status`, {
        signal: AbortSignal.timeout(6000),
      });
      if (!res.ok) return;
      const data = await res.json() as { woocommerce: { connected: boolean }; fedex: { connected: boolean } };
      setWcConnected(data.woocommerce.connected);
      setFedexConnected(data.fedex.connected);
    } catch {
      // keep previous state on error
    }
  }, [isMockMode]);

  useEffect(() => { fetchBadges(); }, [fetchBadges]);

  const portalItems: DropdownItem[] = [
    { path: "/merchant", label: "Merchant Portal", icon: Package },
    { path: "/carrier", label: "Carrier Portal", icon: Ship },
    { path: "/port-authority", label: "Port Authority Portal", icon: Anchor },
  ];

  const dashboardItems: DropdownItem[] = [
    { path: "/tracking", label: "Operational Oversight", icon: BarChart3 },
    { path: "/dashboard", label: "Analytics", icon: BarChart3 },
    { path: "/verification", label: "Verification", icon: FileText },
    { path: "/reports", label: "Reports", icon: FileText, disabled: true, badge: "Soon" },
  ];

  const agentItems: DropdownItem[] = [
    { path: "/agents", label: "Agent Registry", icon: Cpu },
    { label: "Coming Soon", icon: Cpu, disabled: true },
  ];

  const integrationItems: DropdownItem[] = [
    {
      path: "/integrations/woocommerce",
      label: "WooCommerce",
      icon: Plug,
      badge: wcConnected ? "Connected" : "Disconnected",
      badgeColor: wcConnected ? "border-success/40 text-success" : "border-destructive/40 text-destructive",
    },
    {
      path: "/integrations/fedex",
      label: "FedEx",
      icon: Package,
      badge: fedexConnected ? "Connected" : "Disconnected",
      badgeColor: fedexConnected ? "border-success/40 text-success" : "border-destructive/40 text-destructive",
    },
    { path: "/settings", label: "Settings & Docs", icon: Building2 },
  ];

  return (
    <>
      {/*
        overflow-visible is critical — without it the sticky header clips
        the absolutely-positioned dropdown panels.
        h-14 is fixed — no padding/height changes on hover.
      */}
      <header className="sticky top-0 z-50 bg-[#0a1628]/95 backdrop-blur overflow-visible">
        <div className="container flex h-14 items-center justify-between gap-3 overflow-visible">

          {/* Logo — transition-opacity only, no layout shift */}
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-2.5 shrink-0 transition-opacity duration-150 hover:opacity-80"
          >
            <img src={logo} alt="TruthForge" className="h-8 w-8 object-contain" />
            <div className="hidden sm:block">
              <h1 className="text-sm font-bold text-white leading-tight tracking-wide">TruthForge</h1>
              <p className="text-[9px] text-slate-400 leading-none tracking-widest uppercase">The Verifiable Intelligence Layer</p>
            </div>
          </button>

          {/* Nav — overflow-visible so dropdowns escape the header */}
          <nav
            className="flex items-center gap-0.5 overflow-visible"
            role="navigation"
            aria-label="Main navigation"
          >
            <DropdownMenu label="Portal" icon={Anchor} items={portalItems} />
            <DropdownMenu label="Dashboard" icon={BarChart3} items={dashboardItems} />
            <DropdownMenu label="Agents" icon={Cpu} items={agentItems} />
            <DropdownMenu label="Integrations" icon={Plug} items={integrationItems} />
            <button
              onClick={() => setHelpOpen(true)}
              className="flex items-center gap-1 px-1.5 h-9 text-xs font-semibold uppercase tracking-wide rounded whitespace-nowrap transition-colors duration-150 text-slate-300 hover:text-white hover:bg-white/10"
            >
              <HelpCircle className="h-3.5 w-3.5 shrink-0" />
              <span className="hidden lg:inline">Help</span>
            </button>
          </nav>

          {/* Right Controls — all grouped, tight gap, overflow-visible for wallet dropdown */}
          <div className="ml-auto flex items-center gap-2 shrink-0 overflow-visible z-40">

            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="p-1 rounded transition-colors duration-150 text-slate-400 hover:text-white hover:bg-white/10 shrink-0"
            >
              {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
            </button>

            {/* Wallet */}
            <WalletConnectCard />

            {/* Mock / Live toggle */}
            <div className={`flex items-center gap-0.5 px-1.5 h-7 rounded border text-[10px] font-bold tracking-wide uppercase shrink-0 ${
              isMockMode
                ? "border-warning/40 bg-warning/10 text-warning"
                : "border-success/40 bg-success/10 text-success"
            }`}>
              <Database className="h-3 w-3 shrink-0" />
              <span className="hidden sm:inline">{isMockMode ? "Mock" : "Live"}</span>
              <Switch
                checked={!isMockMode}
                onCheckedChange={toggleMockMode}
                aria-label="Toggle data mode"
                className="scale-[0.6] shrink-0"
              />
            </div>
          </div>

        </div>
      </header>

      {helpOpen && <HelpModal onClose={() => setHelpOpen(false)} />}
    </>
  );
};

export default Header;
