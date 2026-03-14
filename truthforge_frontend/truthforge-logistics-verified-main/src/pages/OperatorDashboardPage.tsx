import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import DashboardPage from '@/pages/DashboardPage';
import VerificationPage from '@/pages/VerificationPage';
import AgentsPage from '@/pages/AgentsPage';
import TrackingPage from '@/pages/TrackingPage';
import SettingsPage from '@/pages/SettingsPage';
import GovernancePage from '@/pages/GovernancePage';
import FloatingChat from '@/components/FloatingChat';
import { MockModeProvider } from '@/contexts/MockModeContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { WalletProvider } from '@/contexts/WalletContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LogOut, Shield } from 'lucide-react';

const pages: Record<string, React.FC> = {
  dashboard: DashboardPage,
  verification: VerificationPage,
  agents: AgentsPage,
  tracking: TrackingPage,
  governance: GovernancePage,
  settings: SettingsPage,
};

const OperatorDashboardPage = () => {
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (!user) {
    navigate('/signin');
    return null;
  }

  const ActivePage = pages[activeTab] || DashboardPage;

  // Role-based badge color
  const getRoleBadgeVariant = () => {
    switch (user.role) {
      case 'admin':
        return 'destructive';
      case 'operator':
        return 'default';
      case 'viewer':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  return (
    <ThemeProvider>
      <MockModeProvider>
        <WalletProvider>
          <div className="min-h-screen bg-background flex flex-col">
            {/* Operator Header Bar */}
            <div className="border-b bg-muted/50">
              <div className="container flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                  <Shield className="h-5 w-5 text-primary" />
                  <span className="text-sm font-medium">Operator Dashboard</span>
                  <Badge variant={getRoleBadgeVariant()}>
                    {user.role.toUpperCase()}
                  </Badge>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-muted-foreground">
                    {user.name}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleLogout}
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign Out
                  </Button>
                </div>
              </div>
            </div>

            {/* Main Header with Navigation */}
            <Header 
              activeTab={activeTab} 
              onTabChange={setActiveTab}
              showGovernance={hasRole(['operator', 'admin'])}
            />

            {/* Main Content */}
            <main className="container py-6 md:py-8 flex-grow">
              {/* Role-based access control */}
              {activeTab === 'verification' && !hasRole(['operator', 'admin']) ? (
                <div className="text-center py-12">
                  <Shield className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <h2 className="text-2xl font-bold mb-2">Access Restricted</h2>
                  <p className="text-muted-foreground">
                    You need operator or admin role to access verification controls.
                  </p>
                </div>
              ) : activeTab === 'governance' && !hasRole(['operator', 'admin']) ? (
                <div className="text-center py-12">
                  <Shield className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <h2 className="text-2xl font-bold mb-2">Access Restricted</h2>
                  <p className="text-muted-foreground">
                    You need operator or admin role to access governance features.
                  </p>
                </div>
              ) : (
                <ActivePage />
              )}
            </main>

            {/* Footer */}
            <Footer />

            {/* Floating Chat - available to all authenticated users */}
            <FloatingChat />
          </div>
        </WalletProvider>
      </MockModeProvider>
    </ThemeProvider>
  );
};

export default OperatorDashboardPage;
