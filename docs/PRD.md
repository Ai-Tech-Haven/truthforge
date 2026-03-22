add # TruthForge — Product Requirements Document

**Version:** 1.0  
**Status:** Hackathon Submission (Hedera Hello Future Apex 2026)  
**Track:** AI & Agentic + HOL Bounty  

---

## 1. Problem

Global trade clearance is broken:

- Pre-arrival document verification is manual, taking days instead of minutes
- Document fraud (fake Bills of Lading, forged certificates) costs the industry billions annually
- Carrier, customs, and merchant data live in isolated silos with no shared trust layer
- Port authorities have no cryptographic proof of document authenticity at time of arrival

---

## 2. Solution

TruthForge is a **multi-agent verification platform** that automates pre-arrival clearance for global shipments. It connects merchants, carriers, and port authorities through a tamper-proof intelligence layer anchored on the **Hedera Hashgraph** blockchain.

Core value proposition: a shipment's documents are verified, signed by autonomous agents, and committed to HCS *before* the vessel arrives at port — producing a **Port Trust Receipt** that customs can verify in seconds.

---

## 3. Users

| User | Need |
|---|---|
| **Merchant** | Automated shipment creation and pre-clearance from their WooCommerce store |
| **Port Authority** | Cryptographic proof of document authenticity before vessel arrival |
| **Logistics Operator** | Real-time visibility into clearance queue and agent health |
| **Compliance Auditor** | Immutable, timestamped audit trail for every verification event |

---

## 4. Agent Network (HOL-Registered)

Five specialized agents, each registered on the Hedera HOL protocol:

### 4.1 Orchestrator Agent (`truthforge-orch-001`)
- Parses natural language and structured verification requests
- Routes requests to the correct agent combination
- Coordinates sequential/parallel agent execution
- Aggregates results into a `UnifiedReport`
- Handles the full order-to-clearance workflow triggered by WooCommerce webhooks

### 4.2 Verification & Compliance Agent (`truthforge-verify-001`)
- **4-layer deepfake detection** for cargo photos:
  1. EXIF metadata analysis (camera make/model, editing software detection)
  2. Lighting consistency analysis (shadow/reflection anomalies)
  3. AI artifact detection (dimension alignment, compression patterns)
  4. File metadata verification (format/size consistency)
- Bill of Lading field extraction and cross-validation
- Produces an `AnalysisResult` with a weighted `authenticity_score` (0–100)
- All results timestamped on HCS

### 4.3 Carrier Adapter Agent (`truthforge-carrier-001`)
- Multi-carrier integration: FedEx, UPS, DHL, Maersk, MSC
- Auto-detects carrier from tracking number format via regex
- Normalizes all carrier responses into a unified `CarrierShipmentData` schema
- Live mode: FedEx Sandbox API (OAuth 2.0) for shipment creation and tracking
- Mock mode: deterministic simulated responses for all carriers

### 4.4 Registry & Discovery Agent (`truthforge-registry-001`)
- Manages the HOL registry of all TruthForge agents
- Handles `DISCOVER` messages with capability and status filtering
- 5-minute TTL discovery cache with automatic expiry
- Periodic health monitoring across all registered agents
- Syncs agent status to Hedera HCS and PostgreSQL

### 4.5 Evidence & Settlement Agent (`truthforge-evidence-001`)
- Submits all verification outcomes to Hedera HCS with exponential-backoff retry (up to 3 attempts)
- Generates deterministic `audit_reference` IDs (SHA-256 based)
- Creates `AuditTrail` records with compliance flags (`NON_COMPLIANT`, `LOW_AUTHENTICITY`, `DISCREPANCIES_FOUND`)
- Produces `PortTrustReceipt` — the final clearance artifact
- Tracks per-transaction HBAR costs

---

## 5. Core Workflows

### 5.1 WooCommerce Order → Shipment → Clearance
1. Merchant's WooCommerce store fires `order.created` webhook → `/api/woocommerce/webhook`
2. Orchestrator fetches full order details via Marketplace Agent
3. Carrier Adapter creates FedEx shipment, returns tracking number
4. Orchestrator updates WooCommerce order status with tracking info
5. HCS transaction anchors the order processing event
6. Verification ID issued for future document upload

### 5.2 Document Verification
1. Client POSTs to `/api/verify` with `image_data` or `document_data`
2. Orchestrator parses intent, routes to Verification + Evidence agents
3. Verification Agent runs 4-layer analysis, produces `authenticity_score`
4. Evidence Agent creates audit trail, submits to HCS
5. Response includes `UnifiedReport` with HCS transaction ID

### 5.3 Natural Language Query
1. Client POSTs `{ "message": "verify shipment SHP-8821A" }` to `/api/verify`
2. Orchestrator extracts intent, shipment ID, tracking number via regex
3. If parameters missing, returns `needs_parameters: true` with a prompt
4. Otherwise executes full verification workflow
5. Returns human-readable `natural_language_response` alongside structured report

---

## 6. API Surface

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/verify` | Submit verification (structured or natural language) |
| GET | `/api/status/<request_id>` | Poll verification status |
| GET | `/api/agents` | List registered agents with health metrics |
| GET | `/api/dashboard/metrics` | Operational KPIs |
| GET | `/api/clearance/queue` | Pre-arrival shipment queue |
| GET | `/api/verifications` | Verification history |
| GET | `/api/port-trust-receipts` | Issued Port Trust Receipts |
| GET | `/api/v1/proof/<shipment_id>` | Full cryptographic proof package |
| GET | `/api/hcs/messages` | Live HCS topic messages from mirror node |
| GET | `/api/integrations/status` | Integration health (Hedera, FedEx, WooCommerce) |
| POST | `/api/woocommerce/webhook` | WooCommerce order webhook receiver |

All endpoints return JSON. Protected endpoints require `Authorization: Bearer <token>`.

---

## 7. Data Models

| Model | Purpose |
|---|---|
| `Verification` | Verification request lifecycle and results |
| `Shipment` | Shipment tracking, clearance status, ETA |
| `PortTrustReceipt` | Final clearance artifact with agent signatures |
| `AuditTrail` | Immutable per-action compliance log |
| `AgentStatus` | Agent health, metrics, HOL registration |
| `DashboardMetrics` | Aggregated operational KPIs |

---

## 8. Operating Modes

| | Mock Mode | Live Mode |
|---|---|---|
| Hedera | Simulated TX IDs | Real Testnet HCS submissions |
| FedEx | Mock tracking/shipment data | FedEx Sandbox API (OAuth 2.0) |
| WooCommerce | Simulated orders | REST API against `a-thi.online` |
| Database | SQLite fallback | PostgreSQL (Supabase) |
| Toggle | `MOCK_MODE=true` env var | `MOCK_MODE=false` + credentials |

---

## 9. Key Metrics (Dashboard)

- `totalVerifications` — cumulative verifications processed
- `avgClearanceTime` — average minutes from submission to Port Trust Receipt
- `costSavings` — estimated USD savings vs. manual clearance
- `activeAgents` — HOL-registered agents currently online (target: 5/5)
- `successRate` — percentage of verifications completing without error
- `shipmentsPreCleared` — shipments cleared before vessel arrival

---

## 10. Non-Functional Requirements

- **Immutability:** Every verification outcome is anchored to Hedera HCS. No result can be altered post-submission.
- **Resilience:** Evidence Agent retries failed HCS submissions with exponential backoff (1s, 2s, 4s).
- **Auditability:** Every agent action produces a `VerificationLog` entry with full input/output JSON.
- **Security:** API auth via Bearer token. WooCommerce webhook signature validation (HMAC-SHA256).
- **Scalability:** Agent coordination is designed for parallel execution; current implementation is sequential with parallel-ready interfaces.

---

## 11. Infrastructure

| Component | Platform |
|---|---|
| Backend API | Railway (Flask, Python 3.9+) |
| Frontend Dashboard | Vercel (React + Vite + Tailwind) |
| Database | Supabase (PostgreSQL) |
| Blockchain | Hedera Testnet — HCS Topic `0.0.8161249` |
| Agent Registry | HOL Protocol (Hedera Testnet) |

---

## 12. Out of Scope (Hackathon MVP)

- Mainnet deployment
- Real ML models for deepfake detection (current: heuristic-based)
- Async job queue for webhook processing (current: synchronous)
- Full HMAC webhook signature validation
- Live mode proof retrieval (`/api/v1/proof/<id>` returns 501 in live mode)
- Prediction markets for logistics delay hedging (Phase 2 roadmap)
