import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { MockModeProvider } from "@/contexts/MockModeContext";
import { WalletProvider } from "@/contexts/WalletContext";
import SplashScreen from "@/components/SplashScreen";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import FloatingChat from "@/components/FloatingChat";

// Pages
import LandingPage from "@/pages/LandingPage";
import MerchantPortalPage from "@/pages/MerchantPortalPage";
import CarrierPortalPage from "@/pages/CarrierPortalPage";
import PortAuthorityPortalPage from "@/pages/PortAuthorityPortalPage";
import AgentsPage from "@/pages/AgentsPage";
import TrackingPage from "@/pages/TrackingPage";
import VerificationPage from "@/pages/VerificationPage";
import SettingsPage from "@/pages/SettingsPage";
import DashboardPage from "@/pages/DashboardPage";
import PrivacyPage from "@/pages/PrivacyPage";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient();

const AppShell = () => (
  <div className="min-h-screen bg-background flex flex-col">
    <Header />
    <main className="container py-6 md:py-8 flex-grow">
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/merchant" element={<MerchantPortalPage />} />
        <Route path="/carrier" element={<CarrierPortalPage />} />
        <Route path="/port-authority" element={<PortAuthorityPortalPage />} />
        <Route path="/agents" element={<AgentsPage />} />
        <Route path="/tracking" element={<TrackingPage />} />
        <Route path="/verification" element={<VerificationPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/integrations/woocommerce" element={<SettingsPage />} />
        <Route path="/integrations/fedex" element={<SettingsPage />} />
        {/* Legacy tab-based paths redirect to new routes */}
        <Route path="/portal/merchant" element={<MerchantPortalPage />} />
        <Route path="/portal/carrier" element={<CarrierPortalPage />} />
        <Route path="/portal/port-authority" element={<PortAuthorityPortalPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </main>
    <Footer />
    <FloatingChat />
  </div>
);

const App = () => {
  const [showSplash, setShowSplash] = useState(true);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <ThemeProvider>
          <MockModeProvider>
            <WalletProvider>
              <Toaster />
              <Sonner />
              <BrowserRouter>
                {/* Splash overlays the app — app is already mounted underneath */}
                {showSplash && (
                  <SplashScreen
                    onLoadingComplete={() => setShowSplash(false)}
                    minDisplayTime={2000}
                  />
                )}
                <AppShell />
              </BrowserRouter>
            </WalletProvider>
          </MockModeProvider>
        </ThemeProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
