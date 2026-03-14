import { useState } from "react";
import { X, Ship, Plane, Truck, DollarSign, Wallet, AlertCircle, CheckCircle } from "lucide-react";
import { useWallet } from "@/contexts/WalletContext";

interface PreClearanceRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: PreClearanceFormData) => void;
}

export interface PreClearanceFormData {
  transportMode: "sea" | "air" | "land";
  vesselName?: string;
  airline?: string;
  carrier: string;
  containerList?: string;
  cargoUnits?: string;
  departurePort: string;
  destinationPort: string;
  airWaybill?: string;
  truckingCompany?: string;
  trailerNumber?: string;
}

const PreClearanceRequestModal = ({ isOpen, onClose, onSubmit }: PreClearanceRequestModalProps) => {
  const { wallet, isWalletConnected } = useWallet();
  const [transportMode, setTransportMode] = useState<"sea" | "air" | "land">("sea");
  const [showPaymentConfirm, setShowPaymentConfirm] = useState(false);
  const [formData, setFormData] = useState<PreClearanceFormData>({
    transportMode: "sea",
    carrier: "",
    departurePort: "",
    destinationPort: "",
  });

  // Calculate estimated cost based on transport mode and cargo
  const calculateEstimatedCost = (): number => {
    const baseFee = 0.02; // Shipment verification
    const networkFee = 0.01; // Network recording
    
    let containerFee = 0;
    if (transportMode === "sea" && formData.containerList) {
      const containerCount = formData.containerList.split(",").length;
      containerFee = containerCount * 0.005; // $0.005 per container
    } else if (transportMode === "air" && formData.cargoUnits) {
      const unitCount = parseInt(formData.cargoUnits) || 0;
      containerFee = unitCount * 0.003; // $0.003 per cargo unit
    } else if (transportMode === "land") {
      containerFee = 0.05; // Flat fee for land freight
    }
    
    return baseFee + containerFee + networkFee;
  };

  const estimatedCost = calculateEstimatedCost();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isWalletConnected) {
      alert("Please connect your wallet via the Governance Dashboard before requesting verification.");
      return;
    }
    
    setShowPaymentConfirm(true);
  };

  const handlePaymentConfirm = () => {
    setShowPaymentConfirm(false);
    onSubmit({ ...formData, transportMode });
    onClose();
  };

  const handleInputChange = (field: keyof PreClearanceFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div 
        className="bg-card border border-border rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-elevated"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 border-b border-border flex items-center justify-between sticky top-0 bg-card z-10">
          <div>
            <h3 className="font-heading font-bold text-foreground">Request Pre-Arrival Clearance</h3>
            <p className="text-xs text-muted-foreground mt-1">Submit shipment details for verification</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Wallet Status Banner */}
        {!isWalletConnected && (
          <div className="mx-5 mt-5 rounded-lg border border-warning/30 bg-warning/10 p-3 flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-warning mt-0.5 shrink-0" />
            <div className="text-xs">
              <p className="text-warning font-medium">Wallet Not Connected</p>
              <p className="text-muted-foreground mt-1">
                Please connect your wallet via the Governance Dashboard to process verification payments.
              </p>
            </div>
          </div>
        )}

        {isWalletConnected && (
          <div className="mx-5 mt-5 rounded-lg border border-success/30 bg-success/10 p-3 flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-success mt-0.5 shrink-0" />
            <div className="text-xs flex-1">
              <p className="text-success font-medium">Wallet Connected</p>
              <p className="text-muted-foreground mt-1">
                Account: <span className="font-mono">{wallet?.address}</span> • Network: {wallet?.network}
              </p>
            </div>
          </div>
        )}

        {/* Estimated Cost Display */}
        <div className="mx-5 mt-4 rounded-lg border border-accent/30 bg-accent/5 p-4">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="h-4 w-4 text-accent" />
            <h4 className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">Estimated Verification Cost</h4>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-heading font-black text-accent">${estimatedCost.toFixed(2)}</span>
            <span className="text-sm text-muted-foreground">USD equivalent in HBAR</span>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Final cost calculated based on container count and verification complexity
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {/* Transport Mode */}
          <div>
            <label className="text-xs font-heading font-bold text-foreground uppercase tracking-wider block mb-2">
              Transport Mode
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: "sea", icon: Ship, label: "Sea Freight" },
                { value: "air", icon: Plane, label: "Air Cargo" },
                { value: "land", icon: Truck, label: "Land Freight" },
              ].map(({ value, icon: Icon, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => {
                    setTransportMode(value as "sea" | "air" | "land");
                    setFormData(prev => ({ ...prev, transportMode: value as "sea" | "air" | "land" }));
                  }}
                  className={`p-3 rounded-lg border transition-all ${
                    transportMode === value
                      ? "border-accent bg-accent/10 text-accent"
                      : "border-border bg-secondary/30 text-muted-foreground hover:border-accent/50"
                  }`}
                >
                  <Icon className="h-5 w-5 mx-auto mb-1" />
                  <span className="text-xs font-medium block">{label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Sea Freight Fields */}
          {transportMode === "sea" && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Vessel Name</label>
                  <input
                    type="text"
                    value={formData.vesselName || ""}
                    onChange={(e) => handleInputChange("vesselName", e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                    placeholder="e.g., Mumbai Maersk"
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Carrier</label>
                  <input
                    type="text"
                    value={formData.carrier}
                    onChange={(e) => handleInputChange("carrier", e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                    placeholder="e.g., Maersk"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Container List (comma-separated)</label>
                <input
                  type="text"
                  value={formData.containerList || ""}
                  onChange={(e) => handleInputChange("containerList", e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  placeholder="e.g., MSCU12345, MSCU12346, MSCU12347"
                  required
                />
              </div>
            </>
          )}

          {/* Air Freight Fields */}
          {transportMode === "air" && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Airline</label>
                  <input
                    type="text"
                    value={formData.airline || ""}
                    onChange={(e) => handleInputChange("airline", e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                    placeholder="e.g., FedEx"
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Flight Number</label>
                  <input
                    type="text"
                    value={formData.carrier}
                    onChange={(e) => handleInputChange("carrier", e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                    placeholder="e.g., FX992"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Cargo Units</label>
                  <input
                    type="number"
                    value={formData.cargoUnits || ""}
                    onChange={(e) => handleInputChange("cargoUnits", e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                    placeholder="e.g., 25"
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Air Waybill (optional)</label>
                  <input
                    type="text"
                    value={formData.airWaybill || ""}
                    onChange={(e) => handleInputChange("airWaybill", e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                    placeholder="e.g., AWB-123456"
                  />
                </div>
              </div>
            </>
          )}

          {/* Land Freight Fields */}
          {transportMode === "land" && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Trucking Company</label>
                  <input
                    type="text"
                    value={formData.truckingCompany || ""}
                    onChange={(e) => handleInputChange("truckingCompany", e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                    placeholder="e.g., Swift Transport"
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Trailer Number</label>
                  <input
                    type="text"
                    value={formData.trailerNumber || ""}
                    onChange={(e) => handleInputChange("trailerNumber", e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                    placeholder="e.g., TRL-789012"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Carrier/Driver</label>
                <input
                  type="text"
                  value={formData.carrier}
                  onChange={(e) => handleInputChange("carrier", e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  placeholder="e.g., John Smith"
                  required
                />
              </div>
            </>
          )}

          {/* Common Fields */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Departure Port/Location</label>
              <input
                type="text"
                value={formData.departurePort}
                onChange={(e) => handleInputChange("departurePort", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="e.g., Shanghai, CN"
                required
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Destination Port/Location</label>
              <input
                type="text"
                value={formData.destinationPort}
                onChange={(e) => handleInputChange("destinationPort", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="e.g., Los Angeles, US"
                required
              />
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex gap-3 pt-4 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 rounded-lg border border-border text-foreground text-sm font-medium hover:bg-secondary/50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isWalletConnected}
              className="flex-1 px-4 py-2 rounded-lg bg-accent text-white text-sm font-heading font-bold uppercase tracking-wider hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Request Pre-Clearance
            </button>
          </div>
        </form>

        {/* Payment Confirmation Modal */}
        {showPaymentConfirm && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center p-4 rounded-xl">
            <div className="bg-card border border-border rounded-lg p-6 max-w-md w-full shadow-elevated">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-10 w-10 rounded-full bg-accent/10 flex items-center justify-center">
                  <Wallet className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <h4 className="font-heading font-bold text-foreground">Confirm Payment</h4>
                  <p className="text-xs text-muted-foreground">Authorize verification fee</p>
                </div>
              </div>

              <div className="rounded-lg border border-border bg-secondary/30 p-4 mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-muted-foreground">Verification Fee:</span>
                  <span className="text-lg font-heading font-bold text-accent">${estimatedCost.toFixed(2)}</span>
                </div>
                <div className="text-xs text-muted-foreground">
                  <p>USD equivalent in HBAR</p>
                  <p className="mt-1">Network: Hedera</p>
                </div>
              </div>

              <p className="text-xs text-muted-foreground mb-4">
                Pay with connected wallet?
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowPaymentConfirm(false)}
                  className="flex-1 px-4 py-2 rounded-lg border border-border text-foreground text-sm font-medium hover:bg-secondary/50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handlePaymentConfirm}
                  className="flex-1 px-4 py-2 rounded-lg bg-accent text-white text-sm font-heading font-bold uppercase tracking-wider hover:bg-accent/90 transition-colors"
                >
                  Confirm Payment
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PreClearanceRequestModal;
