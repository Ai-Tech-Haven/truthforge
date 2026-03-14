import { useState } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import DashboardPage from "@/pages/DashboardPage";
import VerificationPage from "@/pages/VerificationPage";
import AgentsPage from "@/pages/AgentsPage";
import TrackingPage from "@/pages/TrackingPage";
import SettingsPage from "@/pages/SettingsPage";
import CarrierPortalPage from "@/pages/CarrierPortalPage";
import FloatingChat from "@/components/FloatingChat";
import { MockModeProvider } from "@/contexts/MockModeContext";
import { ThemeProvider } from "@/contexts/ThemeContext";

const pages: Record<string, React.FC> = {
  dashboard: DashboardPage,
  verification: VerificationPage,
  carrier: CarrierPortalPage,
  agents: AgentsPage,
  tracking: TrackingPage,
  settings: SettingsPage,
};

const Index = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const ActivePage = pages[activeTab] || DashboardPage;

  return (
    <ThemeProvider>
      <MockModeProvider>
        <div className="min-h-screen bg-background flex flex-col">
          <Header activeTab={activeTab} onTabChange={setActiveTab} />
          <main className="container py-6 md:py-8 flex-grow">
            <ActivePage />
          </main>
          <Footer />
          <FloatingChat />
        </div>
      </MockModeProvider>
    </ThemeProvider>
  );
};

export default Index;
