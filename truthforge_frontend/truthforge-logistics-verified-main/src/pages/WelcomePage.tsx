import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Shield, Eye, Lock } from 'lucide-react';
import Footer from '@/components/Footer';

const WelcomePage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex flex-col">
      <div className="flex-grow flex items-center justify-center p-4">
        <div className="w-full max-w-4xl space-y-8">
          {/* Logo and Title */}
          <div className="text-center space-y-4">
            <div className="flex justify-center">
              <Shield className="h-16 w-16 text-primary" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
              TruthForge
            </h1>
            <p className="text-xl text-muted-foreground">
              The Verifiable Intelligence Layer for Global Trade
            </p>
          </div>

          {/* Access Options */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Public Dashboard */}
            <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate('/public')}>
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <Eye className="h-8 w-8 text-primary" />
                  <CardTitle className="text-2xl">Public Dashboard</CardTitle>
                </div>
                <CardDescription className="text-base">
                  View real-time verification metrics and system status
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-muted-foreground mb-4">
                  <li>• Live verification statistics</li>
                  <li>• Agent health monitoring</li>
                  <li>• Port clearance queue</li>
                  <li>• No authentication required</li>
                </ul>
                <Button className="w-full" size="lg" onClick={() => navigate('/public')}>
                  View Public Dashboard
                </Button>
              </CardContent>
            </Card>

            {/* Operator Sign In */}
            <Card className="hover:shadow-lg transition-shadow cursor-pointer border-primary/50" onClick={() => navigate('/signin')}>
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <Lock className="h-8 w-8 text-primary" />
                  <CardTitle className="text-2xl">Operator Access</CardTitle>
                </div>
                <CardDescription className="text-base">
                  Sign in to access operator dashboard and controls
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-muted-foreground mb-4">
                  <li>• Full verification controls</li>
                  <li>• Agent management</li>
                  <li>• Advanced analytics</li>
                  <li>• Role-based permissions</li>
                </ul>
                <Button className="w-full" size="lg" variant="default" onClick={() => navigate('/signin')}>
                  Operator Sign In
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Footer Info */}
          <div className="text-center text-sm text-muted-foreground">
            <p>Powered by Hedera Consensus Service • 5-Agent Architecture</p>
            <p className="mt-1">99.7% Success Rate • $2.4M Cost Savings</p>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default WelcomePage;
