import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Switch } from "@/components/ui/switch";
import { useMockMode } from "@/contexts/MockModeContext";
import { useTheme } from "@/contexts/ThemeContext";
import { useWallet } from "@/contexts/WalletContext";
import logo from "@/assets/truthforge-logo.png";
import {
  Database, Sun, Moon, ChevronDown, Wallet, Anchor, BarChart3,
  FileText, Cpu, Plug, HelpCircle, LogOut, Building2, Package,
  Ship, X, BookOpen, Code, MessageSquare,
} from "lucide-react";

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
    closeTimer.current = setTimeout(() => setOpen(false), 100);
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
      <button
        onClick={() => setOpen(o => !o)}
        className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium uppercase tracking-wide rounded transition-colors whitespace-nowrap ${
          isActive
            ? "bg-primary text-primary-foreground"
            : "text-muted-foreground hover:text-foreground hover:bg-secondary"
        }`}
      >
        {Icon && <Icon className="h-4 w-4" />}
        <span>{label}</span>
        <ChevronDown className={`h-3.5 w-3.5 transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div
          className="absolute top-full left-0 mt-1 min-w-[200px] rounded-lg border border-border bg-card shadow-elevated z-[100] py-1"
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
                className={`w-full flex items-center justify-between gap-2 px-4 py-2.5 text-sm transition-colors ${
                  item.disabled
                    ? "text-muted-foreground/40 cursor-not-allowed"
                    : isItemActive
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-foreground hover:bg-white/5"
                }`}
              >
                <span className="flex items-center gap-2.5">
                  {ItemIcon && <ItemIcon className="h-4 w-4 shrink-0" />}
                  {item.label}
                </span>
                {item.badge && (
                  <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${item.badgeColor || "border-border text-muted-foreground"}`}>
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
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
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
          <div key={item.label} className="flex items-start gap-3 p-3 rounded-lg border border-border hover:bg-secondary/50 transition-colors cursor-pointer">
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

// ─── Wallet Status ────────────────────────────────────────────────────────────

const WalletStatus = () => {
  const { wallet, isWalletConnected, connectWallet, disconnectWallet } = useWallet();
  const location = useLocation();
  const [hover, setHover] = useState(false);
  const [connecting, setConnecting] = useState(false);

  // Only show on portal pages
  const isPortalPage = ["/merchant", "/carrier", "/port-authority"].includes(location.pathname);
  const isPortAuthority = location.pathname === "/port-authority";
  if (!isPortalPage || isPortAuthority) return null;

  const roleLabel = location.pathname === "/merchant" ? "Merchant" : "Carrier";

  const handleConnect = async () => {
    setConnecting(true);
    await connectWallet();
    setConnecting(false);
  };

  if (!isWalletConnected) {
    return (
      <button
        onClick={handleConnect}
        disabled={connecting}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-accent/40 bg-accent/10 text-accent text-xs font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-50"
      >
        <Wallet className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">{connecting ? "Connecting..." : "Connect Wallet"}</span>
      </button>
    );
  }

  return (
    <div
      className="relative"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-success/40 bg-success/10 text-success text-xs font-bold cursor-pointer">
        <Wallet className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">Wallet — {wallet?.address}</span>
      </div>
      {hover && (
        <div className="absolute top-full right-0 mt-1 w-56 rounded-lg border border-border bg-card shadow-elevated z-[100] p-3 space-y-2">
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Network</div>
          <div className="text-xs text-foreground font-medium">Hedera Testnet</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider mt-2">Role</div>
          <div className="text-xs text-foreground font-medium">{roleLabel}</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider mt-2">Account</div>
          <div className="text-xs font-mono text-accent">{wallet?.address}</div>
          <button
            onClick={disconnectWallet}
            className="w-full mt-2 flex items-center gap-1.5 px-2 py-1.5 rounded border border-destructive/30 bg-destructive/10 text-destructive text-xs font-medium hover:bg-destructive/20 transition-colors"
          >
            <LogOut className="h-3 w-3" />
            Disconnect
          </button>
        </div>
      )}
    </div>
  );
};

// ─── Header ───────────────────────────────────────────────────────────────────

const Header = () => {
  const { isMockMode, toggleMockMode } = useMockMode();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [helpOpen, setHelpOpen] = useState(false);

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
    { path: "/agent-health", label: "Agent Health", icon: Cpu, disabled: true, badge: "Soon" },
    { path: "/hcs-topics", label: "HCS Topics", icon: Database, disabled: true, badge: "Soon" },
  ];

  const integrationItems: DropdownItem[] = [
    { path: "/integrations/woocommerce", label: "WooCommerce", icon: Plug, badge: "Connected", badgeColor: "border-success/40 text-success" },
    { path: "/integrations/fedex", label: "FedEx", icon: Package, badge: "Connected", badgeColor: "border-success/40 text-success" },
    { path: "/settings", label: "Settings & Docs", icon: Building2 },
  ];

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
        <div className="container flex h-14 items-center justify-between gap-2">

          {/* Logo */}
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-2.5 shrink-0 hover:opacity-80 transition-opacity"
          >
            <img src={logo} alt="TruthForge" className="h-8 w-8 object-contain" />
            <div className="hidden sm:block">
              <h1 className="text-sm font-heading font-bold text-foreground leading-tight">TruthForge</h1>
              <p className="text-[9px] text-muted-foreground leading-none tracking-wide uppercase">The Verifiable Intelligence Layer</p>
            </div>
          </button>

          {/* Nav */}
          <nav className="flex items-center gap-0.5 overflow-x-auto" role="navigation" aria-label="Main navigation">
            <DropdownMenu label="Portal" icon={Anchor} items={portalItems} />
            <DropdownMenu label="Dashboard" icon={BarChart3} items={dashboardItems} />
            <DropdownMenu label="Agents" icon={Cpu} items={agentItems} />
            <DropdownMenu label="Integrations" icon={Plug} items={integrationItems} />
            <button
              onClick={() => setHelpOpen(true)}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium uppercase tracking-wide rounded transition-colors whitespace-nowrap ${
                helpOpen
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary"
              }`}
            >
              <HelpCircle className="h-4 w-4" />
              <span className="hidden lg:inline">Help</span>
            </button>
          </nav>

          {/* Right Controls */}
          <div className="flex items-center gap-2 shrink-0">
            <WalletStatus />

            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="p-1.5 rounded hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            <div className={`flex items-center gap-2 px-3 py-1 rounded border text-xs font-bold tracking-wide uppercase ${
              isMockMode
                ? "border-warning/40 bg-warning/10 text-warning"
                : "border-success/40 bg-success/10 text-success"
            }`}>
              <Database className="h-3 w-3" />
              <span className="hidden sm:inline">{isMockMode ? "Mock" : "Live"}</span>
              <Switch
                checked={!isMockMode}
                onCheckedChange={toggleMockMode}
                aria-label="Toggle data mode"
                className="scale-[0.65]"
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
