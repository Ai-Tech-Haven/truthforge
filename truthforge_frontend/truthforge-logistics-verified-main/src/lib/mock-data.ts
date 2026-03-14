export interface Agent {
  id: string;
  name: string;
  agentId: string;
  hcsTopic: string;
  status: "online" | "offline" | "processing";
  health: number;
  lastActive: string;
  primaryFunction: string;
}

export interface Verification {
  id: string;
  shipmentId: string;
  type: string;
  status: "verified" | "pending" | "failed";
  agent: string;
  timestamp: string;
  hcsProof: string;
  confidence: number;
}

export interface ShipmentRoute {
  id: string;
  origin: string;
  destination: string;
  status: "verified" | "under_review" | "flagged";
  vessel: string;
  carrier: string;
}

export interface ActivityEvent {
  id: string;
  type: "verified" | "flagged" | "completed";
  message: string;
  timestamp: string;
  location: string;
}

export interface RiskAlert {
  id: string;
  type: "risk" | "compliance" | "inspection";
  title: string;
  message: string;
  severity: "high" | "medium" | "low";
  timestamp: string;
}

export interface Container {
  id: string;
  status: "verified" | "flagged" | "pending";
  riskLevel: "low" | "medium" | "high";
}

export interface ShipmentTracking {
  id: string;
  carrier: string;
  vessel?: string;
  origin: string;
  destination: string;
  status: string;
  eta: string;
  fedexTracking?: string;
  woocommerceOrder?: string;
  freightMode?: "sea" | "air" | "land";
  containerCount?: number;
  verifiedContainers?: number;
  flaggedContainers?: number;
  containers?: Container[];
}

export interface PortTrustReceipt {
  id: string;
  shipmentId: string;
  clearanceStatus: "cleared" | "pending" | "flagged";
  agentSignatures: { agentName: string; agentId: string }[];
  hederaTxRef: string;
  issuedAt: string;
  vessel: string;
  port: string;
  riskScore?: number;
  riskLevel?: "LOW" | "MEDIUM" | "HIGH";
  clearanceRecommendation?: string;
  verificationFees?: {
    shipmentVerification: number;
    containerChecks: number;
    networkRecordingFee: number;
    total: number;
    currency: string;
    paymentNetwork: string;
  };
  paymentTransaction?: {
    status: "confirmed" | "pending" | "failed";
    transactionId: string;
    timestamp: string;
    walletUsed?: string;
  };
}

export const mockAgents: Agent[] = [
  { id: "agent-001", name: "Orchestrator Agent", agentId: "truthforge-orch-001", hcsTopic: "hcs-orch-001", status: "online", health: 98, lastActive: "2 min ago", primaryFunction: "Workflow coordination and decision execution" },
  { id: "agent-002", name: "Verification & Compliance Agent", agentId: "truthforge-verify-001", hcsTopic: "hcs-verify-001", status: "online", health: 95, lastActive: "30 sec ago", primaryFunction: "Document validation and compliance assessment" },
  { id: "agent-003", name: "Carrier Adapter Agent (Council-Grade)", agentId: "truthforge-carrier-001", hcsTopic: "hcs-carrier-001", status: "online", health: 99, lastActive: "1 min ago", primaryFunction: "Carrier data ingestion and normalization" },
  { id: "agent-004", name: "Registry & Discovery Agent", agentId: "truthforge-registry-001", hcsTopic: "hcs-registry-001", status: "online", health: 92, lastActive: "45 sec ago", primaryFunction: "Agent discovery, health reporting, registry sync" },
  { id: "agent-005", name: "Evidence & Settlement Agent", agentId: "truthforge-evidence-001", hcsTopic: "hcs-evidence-001", status: "online", health: 97, lastActive: "Active now", primaryFunction: "Consensus submission and audit reference generation" },
];

export const mockVerifications: Verification[] = [
  { id: "v-001", shipmentId: "SHP-8821A", type: "Bill of Lading", status: "verified", agent: "Verification & Compliance Agent", timestamp: "2024-01-15 14:32:00", hcsProof: "hcs-verify-001#1705312320", confidence: 99.7 },
  { id: "v-002", shipmentId: "SHP-8822B", type: "Customs Declaration", status: "pending", agent: "Verification & Compliance Agent", timestamp: "2024-01-15 14:28:00", hcsProof: "pending", confidence: 0 },
  { id: "v-003", shipmentId: "SHP-8823C", type: "Certificate of Origin", status: "failed", agent: "Verification & Compliance Agent", timestamp: "2024-01-15 14:25:00", hcsProof: "N/A", confidence: 23.4 },
  { id: "v-004", shipmentId: "SHP-8824D", type: "Phytosanitary Cert", status: "verified", agent: "Verification & Compliance Agent", timestamp: "2024-01-15 14:20:00", hcsProof: "hcs-verify-001#1705311600", confidence: 99.1 },
  { id: "v-005", shipmentId: "SHP-8821A", type: "Commercial Invoice", status: "verified", agent: "Orchestrator Agent", timestamp: "2024-01-15 14:15:00", hcsProof: "hcs-orch-001#1705311300", confidence: 97.8 },
  { id: "v-006", shipmentId: "SHP-8824D", type: "Packing List", status: "verified", agent: "Carrier Adapter Agent (Council-Grade)", timestamp: "2024-01-15 14:10:00", hcsProof: "hcs-carrier-001#1705311000", confidence: 98.2 },
];

// Generate mock containers for shipments
const generateContainers = (total: number, verified: number, flagged: number): Container[] => {
  const containers: Container[] = [];
  const prefix = "MSCU";
  
  // Add verified containers
  for (let i = 0; i < verified; i++) {
    containers.push({
      id: `${prefix}${12345 + i}`,
      status: "verified",
      riskLevel: "low"
    });
  }
  
  // Add flagged containers
  for (let i = 0; i < flagged; i++) {
    containers.push({
      id: `${prefix}${12345 + verified + i}`,
      status: "flagged",
      riskLevel: i % 2 === 0 ? "medium" : "high"
    });
  }
  
  // Add pending containers
  const pending = total - verified - flagged;
  for (let i = 0; i < pending; i++) {
    containers.push({
      id: `${prefix}${12345 + verified + flagged + i}`,
      status: "pending",
      riskLevel: "low"
    });
  }
  
  return containers;
};

export const mockShipments: ShipmentTracking[] = [
  { 
    id: "SHP-8821A", 
    carrier: "Maersk", 
    vessel: "Mumbai Maersk", 
    origin: "Shanghai, CN", 
    destination: "Los Angeles, US", 
    status: "Verified", 
    eta: "T-14h", 
    fedexTracking: "7749 1234 5678", 
    woocommerceOrder: "WC-10234", 
    freightMode: "sea", 
    containerCount: 42, 
    verifiedContainers: 41, 
    flaggedContainers: 1,
    containers: generateContainers(42, 41, 1)
  },
  { 
    id: "SHP-8822B", 
    carrier: "MSC", 
    vessel: "MSC Oscar", 
    origin: "Rotterdam, NL", 
    destination: "New York, US", 
    status: "Pending Consensus", 
    eta: "T-18h", 
    woocommerceOrder: "WC-10235", 
    freightMode: "sea", 
    containerCount: 38, 
    verifiedContainers: 35, 
    flaggedContainers: 0,
    containers: generateContainers(38, 35, 0)
  },
  { 
    id: "SHP-8823C", 
    carrier: "CMA CGM", 
    vessel: "Jade", 
    origin: "Tokyo, JP", 
    destination: "Chicago, US", 
    status: "Flagged Exception", 
    eta: "T-22h", 
    freightMode: "sea", 
    containerCount: 28, 
    verifiedContainers: 25, 
    flaggedContainers: 3,
    containers: generateContainers(28, 25, 3)
  },
  { 
    id: "SHP-8824D", 
    carrier: "FedEx", 
    vessel: "FX992 (Air)", 
    origin: "Mumbai, IN", 
    destination: "London, UK", 
    status: "Verified", 
    eta: "T-04h", 
    freightMode: "air" 
  },
];

export const mockPortTrustReceipts: PortTrustReceipt[] = [
  {
    id: "PTR-001",
    shipmentId: "SHP-8821A",
    clearanceStatus: "cleared",
    agentSignatures: [
      { agentName: "Orchestrator Agent", agentId: "truthforge-orch-001" },
      { agentName: "Verification & Compliance Agent", agentId: "truthforge-verify-001" },
      { agentName: "Carrier Adapter Agent (Council-Grade)", agentId: "truthforge-carrier-001" },
      { agentName: "Registry & Discovery Agent", agentId: "truthforge-registry-001" },
      { agentName: "Evidence & Settlement Agent", agentId: "truthforge-evidence-001" },
    ],
    hederaTxRef: "0.0.453211@1698754321.123456789",
    issuedAt: "2024-01-15 14:35:00",
    vessel: "Mumbai Maersk",
    port: "Port of Los Angeles",
    riskScore: 12,
    riskLevel: "LOW",
    clearanceRecommendation: "Fast-Track Port Clearance",
    verificationFees: {
      shipmentVerification: 0.02,
      containerChecks: 0.21,
      networkRecordingFee: 0.01,
      total: 0.24,
      currency: "HBAR",
      paymentNetwork: "Hedera"
    },
    paymentTransaction: {
      status: "confirmed",
      transactionId: "0.0.4521983-1719329922-000000001",
      timestamp: "2026-03-08 14:02 UTC",
      walletUsed: "Connected Enterprise Wallet"
    }
  },
  {
    id: "PTR-002",
    shipmentId: "SHP-8824D",
    clearanceStatus: "cleared",
    agentSignatures: [
      { agentName: "Orchestrator Agent", agentId: "truthforge-orch-001" },
      { agentName: "Verification & Compliance Agent", agentId: "truthforge-verify-001" },
      { agentName: "Evidence & Settlement Agent", agentId: "truthforge-evidence-001" },
    ],
    hederaTxRef: "0.0.453211@1698754400.987654321",
    issuedAt: "2024-01-14 09:12:00",
    vessel: "FX992 (Air)",
    port: "Port of Felixstowe",
    riskScore: 8,
    riskLevel: "LOW",
    clearanceRecommendation: "Fast-Track Port Clearance",
    verificationFees: {
      shipmentVerification: 0.02,
      containerChecks: 0.08,
      networkRecordingFee: 0.01,
      total: 0.11,
      currency: "HBAR",
      paymentNetwork: "Hedera"
    },
    paymentTransaction: {
      status: "confirmed",
      transactionId: "0.0.4521983-1719329800-000000002",
      timestamp: "2026-03-07 18:45 UTC",
      walletUsed: "Connected Enterprise Wallet"
    }
  },
];

export const mockMetrics = {
  totalVerifications: 12847,
  avgClearanceTime: "3.2 min",
  costSavings: "$2.4M",
  activeAgents: 5,
  successRate: 99.7,
  shipmentsToday: 342,
  documentsPreArrival: 8421,
  shipmentsPreCleared: 6293,
};

export const mockShipmentRoutes: ShipmentRoute[] = [
  { id: "RT-001", origin: "Shanghai", destination: "Rotterdam", status: "verified", vessel: "Mumbai Maersk", carrier: "Maersk" },
  { id: "RT-002", origin: "Singapore", destination: "Dubai", status: "under_review", vessel: "MSC Oscar", carrier: "MSC" },
  { id: "RT-003", origin: "Los Angeles", destination: "Hamburg", status: "verified", vessel: "CMA Jade", carrier: "CMA CGM" },
  { id: "RT-004", origin: "Tokyo", destination: "Long Beach", status: "flagged", vessel: "Evergreen Ever Given", carrier: "Evergreen" },
  { id: "RT-005", origin: "Mumbai", destination: "London", status: "verified", vessel: "FX992 (Air)", carrier: "FedEx" },
];

export const mockActivityEvents: ActivityEvent[] = [
  { id: "EVT-001", type: "verified", message: "Shipment Verified — MSC Aurora — Singapore Port", timestamp: "2 min ago", location: "Singapore" },
  { id: "EVT-002", type: "flagged", message: "Container Flagged — MSCU12347 — Rotterdam", timestamp: "5 min ago", location: "Rotterdam" },
  { id: "EVT-003", type: "completed", message: "Verification Complete — CMA Horizon — Dubai", timestamp: "8 min ago", location: "Dubai" },
  { id: "EVT-004", type: "verified", message: "Shipment Verified — Mumbai Maersk — Shanghai", timestamp: "12 min ago", location: "Shanghai" },
  { id: "EVT-005", type: "completed", message: "Pre-Clearance Issued — FX992 — London Heathrow", timestamp: "15 min ago", location: "London" },
];

export const mockRiskAlerts: RiskAlert[] = [
  { 
    id: "ALT-001", 
    type: "risk", 
    title: "Risk Alert", 
    message: "Container MSCU12347 flagged for documentation mismatch.", 
    severity: "high", 
    timestamp: "5 min ago" 
  },
  { 
    id: "ALT-002", 
    type: "compliance", 
    title: "Compliance Notice", 
    message: "Shipment cleared for fast-track port entry.", 
    severity: "low", 
    timestamp: "10 min ago" 
  },
  { 
    id: "ALT-003", 
    type: "inspection", 
    title: "Inspection Notice", 
    message: "Manual inspection recommended for vessel MSC Aurora.", 
    severity: "medium", 
    timestamp: "18 min ago" 
  },
];

// ─── Carrier Verification ────────────────────────────────────────────────────

export interface CarrierVerification {
  id: string;
  shipmentId: string;
  carrierName: string;
  status: "verified" | "pending" | "failed";
  documents: { name: string; type: string; size?: string }[];
  submittedAt: string;
  verificationFee: { amount: number; currency: string; paymentNetwork: string };
  hcsRef: string | null;
  agentUsed: string;
}

export const mockCarrierVerifications: CarrierVerification[] = [
  {
    id: "CV-001",
    shipmentId: "SHP-8821A",
    carrierName: "Maersk",
    status: "verified",
    documents: [
      { name: "Bill_of_Lading_SHP-8821A.pdf", type: "Bill of Lading", size: "1.2 MB" },
      { name: "Commercial_Invoice_SHP-8821A.pdf", type: "Commercial Invoice", size: "0.8 MB" },
      { name: "Packing_List_SHP-8821A.pdf", type: "Packing List", size: "0.5 MB" },
    ],
    submittedAt: "2026-03-08 13:45:00",
    verificationFee: { amount: 0.24, currency: "HBAR", paymentNetwork: "Hedera" },
    hcsRef: "hcs-carrier-001#1741437900",
    agentUsed: "truthforge-carrier-001",
  },
  {
    id: "CV-002",
    shipmentId: "SHP-8822B",
    carrierName: "MSC",
    status: "pending",
    documents: [
      { name: "Bill_of_Lading_SHP-8822B.pdf", type: "Bill of Lading", size: "1.1 MB" },
      { name: "Customs_Declaration_SHP-8822B.pdf", type: "Customs Declaration", size: "0.9 MB" },
    ],
    submittedAt: "2026-03-08 14:10:00",
    verificationFee: { amount: 0.18, currency: "HBAR", paymentNetwork: "Hedera" },
    hcsRef: null,
    agentUsed: "truthforge-carrier-001",
  },
  {
    id: "CV-003",
    shipmentId: "SHP-8823C",
    carrierName: "CMA CGM",
    status: "failed",
    documents: [
      { name: "Certificate_of_Origin_SHP-8823C.pdf", type: "Certificate of Origin", size: "0.7 MB" },
    ],
    submittedAt: "2026-03-08 12:30:00",
    verificationFee: { amount: 0.12, currency: "HBAR", paymentNetwork: "Hedera" },
    hcsRef: null,
    agentUsed: "truthforge-carrier-001",
  },
  {
    id: "CV-004",
    shipmentId: "SHP-8824D",
    carrierName: "FedEx",
    status: "verified",
    documents: [
      { name: "Commercial_Invoice_SHP-8824D.pdf", type: "Commercial Invoice", size: "0.6 MB" },
      { name: "Phytosanitary_SHP-8824D.pdf", type: "Phytosanitary Certificate", size: "0.4 MB" },
    ],
    submittedAt: "2026-03-07 18:20:00",
    verificationFee: { amount: 0.11, currency: "HBAR", paymentNetwork: "Hedera" },
    hcsRef: "hcs-carrier-001#1741370400",
    agentUsed: "truthforge-carrier-001",
  },
];

export const mockChatMessages = [
  { role: "system" as const, content: "TruthForge verification interface ready. Enter a shipment ID to query status." },
  { role: "user" as const, content: "Check status of shipment SHP-8821A" },
  { role: "assistant" as const, content: "Shipment SHP-8821A (Maersk / Mumbai Maersk): Bill of Lading verified at 99.7% confidence. HCS proof recorded at topic hcs-verify-001. Port Trust Receipt issued. ETA: T-14h." },
];
