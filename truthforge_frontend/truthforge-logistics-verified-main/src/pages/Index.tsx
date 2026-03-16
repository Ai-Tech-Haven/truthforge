import { useState } from "react";
import type { ComponentType } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import DashboardPage from "@/pages/DashboardPage";
import VerificationPage from "@/pages/VerificationPage";
import AgentsPage from "@/pages/AgentsPage";
import TrackingPage from "@/pages/TrackingPage";
import SettingsPage from "@/pages/SettingsPage";
import CarrierPortalPage from "@/pages/CarrierPortalPage";
import MerchantPortalPage from "@/pages/MerchantPortalPage";
import PortAuthorityPortalPage from "@/pages/PortAuthorityPortalPage";
import FloatingChat from "@/components/FloatingChat";
import { MockModeProvider } from "@/contexts/MockModeContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { WalletProvider } from "@/contexts/WalletContext";

type PortalRole = "merchant" | "carrier" | "port-authority" | null;

const pages: Record<string, ComponentType> = {
  dashboard: DashboardPage,
  verification: VerificationPage,
  "portal-carrier": CarrierPortalPage,
  "portal-merchant": MerchantPortalPage,
  "portal-port-authority": PortAuthorityPortalPage,
  agents: AgentsPage,
  tracking: TrackingPage,
  settings: SettingsPage,
  // integration dropdown items all resolve to SettingsPage
  "integration-woocommerce": SettingsPage,
  "integration-fedex": SettingsPage,
  // legacy alias
  carrier: CarrierPortalPage,
};

const portalRoleMap: Record<string, PortalRole> = {
  "portal-merchant": "merchant",
  "portal-carrier": "carrier",
  "portal-port-authority": "port-authority",
  carrier: "carrier",
};

const Index = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const ActivePage = pages[activeTab] || DashboardPage;
  const portalRole = portalRoleMap[activeTab] ?? null;

  return (
    <ThemeProvider>
      <MockModeProvider>
        <WalletProvider>
          <div className="min-h-screen bg-background flex flex-col">
            <Header activeTab={activeTab} onTabChange={setActiveTab} portalRole={portalRole} />
            <main className="container py-6 md:py-8 flex-grow">
              <ActivePage />
            </main>
            <Footer />
            <FloatingChat />
          </div>
        </WalletProvider>
      </MockModeProvider>
    </ThemeProvider>
  );
};

export default Index;
