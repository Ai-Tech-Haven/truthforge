import { Switch } from "@/components/ui/switch";
import { useMockMode } from "@/contexts/MockModeContext";
import { useTheme } from "@/contexts/ThemeContext";
import logo from "@/assets/truthforge-logo.png";
import { Database, Sun, Moon, Anchor, FileCheck, Cpu, BarChart3, Settings, Vote, Package } from "lucide-react";

interface HeaderProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  showGovernance?: boolean;
}

const baseTabs = [
  { id: "dashboard", label: "Port Clearance Dashboard", icon: Anchor },
  { id: "verification", label: "Verification & Compliance", icon: FileCheck },
  { id: "carrier", label: "Carrier Portal", icon: Package },
  { id: "agents", label: "Agent Registry", icon: Cpu },
  { id: "tracking", label: "Operational Oversight", icon: BarChart3 },
];

const governanceTab = { id: "governance", label: "Governance & Advanced", icon: Vote };

const settingsTab = { id: "settings", label: "Settings & Doc", icon: Settings };

const Header = ({ activeTab, onTabChange, showGovernance = false }: HeaderProps) => {
  const { isMockMode, toggleMockMode } = useMockMode();
  const { theme, toggleTheme } = useTheme();

  // Build tabs array based on showGovernance prop
  const tabs = [
    ...baseTabs,
    ...(showGovernance ? [governanceTab] : []),
    settingsTab,
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="container flex h-14 items-center justify-between gap-4">
        {/* Logo */}
        <div className="flex items-center gap-2.5 shrink-0">
          <img src={logo} alt="TruthForge" className="h-8 w-8 object-contain" />
          <div className="hidden sm:block">
            <h1 className="text-sm font-heading font-bold text-foreground leading-tight">TruthForge</h1>
            <p className="text-[9px] text-muted-foreground leading-none tracking-wide uppercase">The Verifiable Intelligence Layer</p>
          </div>
        </div>

        {/* Tabs */}
        <nav className="flex items-center gap-0.5 overflow-x-auto" role="tablist" aria-label="Main navigation">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span className="hidden lg:inline">{tab.label}</span>
                <span className="lg:hidden">{tab.label.split(" ")[0]}</span>
              </button>
            );
          })}
        </nav>

        {/* Mode Badge + Controls */}
        <div className="flex items-center gap-2 shrink-0">
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
