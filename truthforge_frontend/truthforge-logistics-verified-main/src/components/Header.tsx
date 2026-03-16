import { useState, useRef, useEffect } from "react";
import { Switch } from "@/components/ui/switch";
import { useMockMode } from "@/contexts/MockModeContext";
import { useTheme } from "@/contexts/ThemeContext";
import { useWallet } from "@/contexts/WalletContext";
import logo from "@/assets/truthforge-logo.png";
import {
  Database, Sun, Moon, ChevronDown, Wallet, Anchor, BarChart3,
  FileText, Cpu, Plug, HelpCircle, LogOut, Building2, Package, Ship
} from "lucide-react";

interface HeaderProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  portalRole?: "merchant" | "carrier" | "port-authority" | null;
}

interface DropdownItem {
  id: string;
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
  activeTab: string;
  onSelect: (id: string) => void;
}

const DropdownMenu = ({ label, icon: Icon, items, activeTab, onSelect }: DropdownMenuProps) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const isActive = items.some(i => i.id === activeTab);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        className={`flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded transition-colors whitespace-nowrap ${
          isActive
            ? "bg-primary text-primary-foreground"
            : "text-muted-foreground hover:text-foreground hover:bg-secondary"
        }`}
      >
        {Icon && <Icon className="h-3.5 w-3.5" />}
        <span className="hidden lg:inline">{label}</span>
        <ChevronDown className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 min-w-[180px] rounded-lg border border-border bg-card shadow-elevated z-50 py-1">
          {items.map(item => {
            const ItemIcon = item.icon;
            return (
              <button
                key={item.id}
                disabled={item.disabled}
                onClick={() => {
                  if (!item.disabled) {
                    onSelect(item.id);
                    setOpen(false);
                  }
                }}
                className={`w-full flex items-center justify-between gap-2 px-3 py-2 text-xs transition-colors ${
                  item.disabled
                    ? "text-muted-foreground/40 cursor-not-allowed"
                    : activeTab === item.id
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-foreground hover:bg-secondary"
                }`}
              >
                <span className="flex items-center gap-2">
                  {ItemIcon && <ItemIcon className="h-3.5 w-3.5 shrink-0" />}
                  {item.label}
                </span>
                {item.badge && (
                  <span className={`text-[9px] font-heading font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${item.badgeColor || "border-border text-muted-foreground"}`}>
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

const WalletStatus = ({ portalRole }: { portalRole?: "merchant" | "carrier" | "port-authority" | null }) => {
  const { wallet, isWalletConnected, connectWallet, disconnectWallet } = useWallet();
  const [hover, setHover] = useState(false);
  const [connecting, setConnecting] = useState(false);

  if (!portalRole || portalRole === "port-authority") return null;

  const roleLabel = portalRole === "merchant" ? "Merchant" : "Carrier";

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
        className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-accent/40 bg-accent/10 text-accent text-xs font-heading font-bold uppercase tracking-wider hover:bg-accent/20 transition-colors disabled:opacity-50"
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
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-success/40 bg-success/10 text-success text-xs font-heading font-bold cursor-pointer">
        <Wallet className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">Wallet Connected – {wallet?.address}</span>
      </div>

      {hover && (
        <div className="absolute top-full right-0 mt-1 w-56 rounded-lg border border-border bg-card shadow-elevated z-50 p-3 space-y-2">
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Network</div>
          <div className="text-xs text-foreground font-medium">Hedera Testnet</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider mt-2">Role Context</div>
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

const Header = ({ activeTab, onTabChange, portalRole }: HeaderProps) => {
  const { isMockMode, toggleMockMode } = useMockMode();
  const { theme, toggleTheme } = useTheme();

  const portalItems: DropdownItem[] = [
    { id: "portal-merchant", label: "Merchant Portal", icon: Package },
    { id: "portal-carrier", label: "Carrier Portal", icon: Ship },
    { id: "portal-port-authority", label: "Port Authority Portal", icon: Anchor },
  ];

  const dashboardItems: DropdownItem[] = [
    { id: "tracking", label: "Operational Oversight", icon: BarChart3 },
    { id: "dashboard", label: "Analytics", icon: BarChart3 },
    { id: "reports", label: "Reports", icon: FileText, disabled: true, badge: "Soon", badgeColor: "border-muted text-muted-foreground" },
  ];

  const agentItems: DropdownItem[] = [
    { id: "agents", label: "Agent Registry", icon: Cpu },
    { id: "agent-health", label: "Agent Health", icon: Cpu, disabled: true, badge: "Soon", badgeColor: "border-muted text-muted-foreground" },
    { id: "hcs-topics", label: "HCS Topics", icon: Database, disabled: true, badge: "Soon", badgeColor: "border-muted text-muted-foreground" },
  ];

  const integrationItems: DropdownItem[] = [
    { id: "integration-woocommerce", label: "WooCommerce", icon: Plug, badge: "Connected", badgeColor: "border-success/40 text-success" },
    { id: "integration-fedex", label: "FedEx", icon: Package, badge: "Connected", badgeColor: "border-success/40 text-success" },
    { id: "settings", label: "Settings & Docs", icon: Building2 },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="container flex h-14 items-center justify-between gap-2">
        {/* Logo */}
        <div className="flex items-center gap-2.5 shrink-0">
          <img src={logo} alt="TruthForge" className="h-8 w-8 object-contain" />
          <div className="hidden sm:block">
            <h1 className="text-sm font-heading font-bold text-foreground leading-tight">TruthForge</h1>
            <p className="text-[9px] text-muted-foreground leading-none tracking-wide uppercase">The Verifiable Intelligence Layer</p>
          </div>
        </div>

        {/* Dropdown Nav */}
        <nav className="flex items-center gap-0.5 overflow-x-auto" role="navigation" aria-label="Main navigation">
          <DropdownMenu label="Portal" icon={Anchor} items={portalItems} activeTab={activeTab} onSelect={onTabChange} />
          <DropdownMenu label="Dashboard" icon={BarChart3} items={dashboardItems} activeTab={activeTab} onSelect={onTabChange} />
          <DropdownMenu label="Agents" icon={Cpu} items={agentItems} activeTab={activeTab} onSelect={onTabChange} />
          <DropdownMenu label="Integrations" icon={Plug} items={integrationItems} activeTab={activeTab} onSelect={onTabChange} />
          <button
            onClick={() => onTabChange("help")}
            className={`flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded transition-colors whitespace-nowrap ${
              activeTab === "help"
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-secondary"
            }`}
          >
            <HelpCircle className="h-3.5 w-3.5" />
            <span className="hidden lg:inline">Help</span>
          </button>
        </nav>

        {/* Right Controls */}
        <div className="flex items-center gap-2 shrink-0">
          <WalletStatus portalRole={portalRole} />

          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="p-1.5 rounded hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
          >
            {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
          </button>

          <div className={`flex items-center gap-2 px-3 py-1 rounded border text-xs font-heading font-bold tracking-wide uppercase ${
            isMockMode
              ? "border-warning/40 bg-warning/10 text-warning"
              : "border-success/40 bg-success/10 text-success"
          }`}>
            <Database className="h-3 w-3" />
            <span>{isMockMode ? "Mock" : "Live"}</span>
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
  );
};

export default Header;
