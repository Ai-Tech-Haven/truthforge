import { useState } from 'react';
import { useWallet } from '@/contexts/WalletContext';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Wallet, Shield, Vote, FileCheck, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const GovernancePage = () => {
  const { wallet, isWalletConnected, connectWallet, disconnectWallet } = useWallet();
  const { user } = useAuth();
  const { toast } = useToast();
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnectWallet = async () => {
    setIsConnecting(true);
    try {
      const success = await connectWallet();
      if (success) {
        toast({
          title: 'Wallet connected',
          description: 'You can now access governance features',
        });
      } else {
        toast({
          title: 'Connection failed',
          description: 'Failed to connect wallet',
          variant: 'destructive',
        });
      }
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnectWallet = () => {
    disconnectWallet();
    toast({
      title: 'Wallet disconnected',
      description: 'Governance features are now restricted',
    });
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Governance & Advanced</h1>
          <p className="text-muted-foreground mt-1">
            High-assurance attestations and governance controls
          </p>
        </div>
        {user?.role === 'admin' && (
          <Badge variant="destructive">Admin Access</Badge>
        )}
      </div>

      {/* Wallet Connection Card */}
      <Card className={isWalletConnected ? 'border-primary' : ''}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Wallet className="h-6 w-6 text-primary" />
              <div>
                <CardTitle>Wallet Connection</CardTitle>
                <CardDescription>
                  {isWalletConnected
                    ? 'Wallet connected for governance operations'
                    : 'Connect wallet for governance and high-assurance attestations'}
                </CardDescription>
              </div>
            </div>
            {isWalletConnected && (
              <Badge variant="outline" className="gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Connected
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {isWalletConnected ? (
            <div className="space-y-4">
              <div className="p-4 bg-muted rounded-lg space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Address:</span>
                  <span className="font-mono">{wallet?.address}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Network:</span>
                  <span className="capitalize">{wallet?.network}</span>
                </div>
              </div>
              <Button
                variant="outline"
                onClick={handleDisconnectWallet}
                className="w-full"
              >
                Disconnect Wallet
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Wallet connection is optional but required for governance voting and high-assurance attestations.
                </AlertDescription>
              </Alert>
              <Button
                onClick={handleConnectWallet}
                disabled={isConnecting}
                className="w-full"
              >
                <Wallet className="mr-2 h-4 w-4" />
                {isConnecting ? 'Connecting...' : 'Connect Wallet'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Governance Features */}
      <Tabs defaultValue="proposals" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="proposals">Proposals</TabsTrigger>
          <TabsTrigger value="attestations">Attestations</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Proposals Tab */}
        <TabsContent value="proposals" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Vote className="h-5 w-5 text-primary" />
                <CardTitle>Governance Proposals</CardTitle>
              </div>
              <CardDescription>
                Vote on system upgrades and policy changes
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!isWalletConnected ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Shield className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Connect wallet to view and vote on proposals</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Mock Proposal 1 */}
                  <div className="p-4 border rounded-lg space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold">Upgrade Agent Verification Threshold</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          Increase minimum confidence threshold from 95% to 97%
                        </p>
                      </div>
                      <Badge>Active</Badge>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="default">Vote Yes</Button>
                      <Button size="sm" variant="outline">Vote No</Button>
                    </div>
                  </div>

                  {/* Mock Proposal 2 */}
                  <div className="p-4 border rounded-lg space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold">Add New Carrier Integration</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          Integrate COSCO shipping carrier API
                        </p>
                      </div>
                      <Badge variant="secondary">Pending</Badge>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="default">Vote Yes</Button>
                      <Button size="sm" variant="outline">Vote No</Button>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Attestations Tab */}
        <TabsContent value="attestations" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <FileCheck className="h-5 w-5 text-primary" />
                <CardTitle>High-Assurance Attestations</CardTitle>
              </div>
              <CardDescription>
                Sign critical verification results with your wallet
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!isWalletConnected ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Shield className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Connect wallet to create high-assurance attestations</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <Alert>
                    <CheckCircle2 className="h-4 w-4" />
                    <AlertDescription>
                      Your wallet signature adds an additional layer of verification to critical operations.
                    </AlertDescription>
                  </Alert>

                  {/* Mock Attestation Request */}
                  <div className="p-4 border rounded-lg space-y-3">
                    <div>
                      <h3 className="font-semibold">Shipment SHP-8821A Verification</h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        High-value shipment requires wallet attestation
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="default">
                        <Wallet className="mr-2 h-4 w-4" />
                        Sign Attestation
                      </Button>
                      <Button size="sm" variant="outline">Decline</Button>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Governance Settings</CardTitle>
              <CardDescription>
                Configure governance and attestation preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <h4 className="font-medium">Notification Preferences</h4>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" defaultChecked />
                    Notify me of new proposals
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" defaultChecked />
                    Notify me of attestation requests
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" />
                    Notify me of voting deadlines
                  </label>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">Attestation Settings</h4>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" defaultChecked />
                    Require wallet confirmation for high-value shipments
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" />
                    Auto-sign routine attestations
                  </label>
                </div>
              </div>

              <Button className="w-full">Save Settings</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default GovernancePage;
