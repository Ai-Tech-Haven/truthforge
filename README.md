<p align="center">
  <img src="assets/truthforge-logo.png" alt="TruthForge Logo" width="180"/>
</p>

<h1 align="center">TruthForge</h1>
<p align="center"><strong>The Verifiable Intelligence Layer for Global Trade</strong></p>
<p align="center">
  <em>Hedera Hello Future Apex Hackathon 2026 — AI & Agentic Track + HOL Bounty</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Hedera-HCS--10-blue?logo=hedera" alt="Hedera HCS-10"/>
  <img src="https://img.shields.io/badge/HOL-5%20Agents%20Registered-green" alt="HOL Agents"/>
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/React-Vite-61DAFB?logo=react" alt="React"/>
  <img src="https://img.shields.io/badge/FedEx-Sandbox%20API-orange" alt="FedEx"/>
  <img src="https://img.shields.io/badge/WooCommerce-REST%20API-96588A?logo=woocommerce" alt="WooCommerce"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License"/>
</p>

---

TruthForge is a production-grade, multi-agent verification platform built on Hedera's Hashgraph Online (HOL) protocol. It delivers cryptographically anchored pre-arrival clearance for global shipments — connecting merchants, carriers, and port authorities through a unified, tamper-proof intelligence layer.

---

## Why TruthForge

| Problem | TruthForge Solution |
|---|---|
| Port clearance takes days | Pre-arrival verification in minutes |
| Document fraud costs $billions | Immutable HCS-anchored proof |
| Siloed carrier/merchant data | Unified agent network on Hedera |
| No carrier self-service | Carrier Portal with independent verification |
| Manual compliance checks | 5 autonomous HOL-registered agents |

---

## Live Demo

- **Public Dashboard** — `/public` — Port clearance, verification, agent registry, tracking
- **Operator Dashboard** — `/operator` — Role-based access (viewer / operator / admin)
- **Carrier Portal** — `/public` → Carrier Portal tab — Independent document upload & pickup scheduling
- **Mock/Live Toggle** — Switch between simulated and live Hedera data in real time

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TruthForge Platform                       │
├──────────────┬──────────────────────────────────────────────┤
│  React/Vite  │  Public Dashboard  │  Operator Dashboard     │
│  Frontend    │  Carrier Portal    │  Role-Based Access       │
├──────────────┴──────────────────────────────────────────────┤
│                    Flask REST API (Python)                    │
│         /api/v1/*  │  WebSocket  │  WooCommerce Webhook      │
├─────────────────────────────────────────────────────────────┤
│              5 HOL-Registered AI Agents                      │
│  Orchestrator │ Verification │ Carrier │ Registry │ Evidence │
├─────────────────────────────────────────────────────────────┤
│         Hedera Consensus Service (HCS-10 Protocol)           │
│              Immutable Audit Trail on Testnet                │
├──────────────────────────┬──────────────────────────────────┤
│   WooCommerce REST API   │   FedEx Sandbox API              │
│   a-thi.online           │   OAuth 2.0 + Shipment Creation  │
└──────────────────────────┴──────────────────────────────────┘
```

---

## The 5 HOL-Registered Agents

### 1. Orchestrator Agent — `truthforge-orch-001`
**HCS Topic**: `0.0.8161244`

The central brain. Coordinates the full order-to-clearance workflow.

- Receives orders from WooCommerce webhook
- Dispatches tasks to all downstream agents
- Aggregates results and issues final clearance decision
- Exposes `process_order()` for end-to-end automation

```python
orchestrator.process_order({
    "order_id": "WC-10234",
    "source": "woocommerce"
})
```

---

### 2. Verification & Compliance Agent — `truthforge-verify-001`
**HCS Topic**: `0.0.8161247`

Document intelligence and compliance enforcement.

- Validates Bill of Lading, Commercial Invoice, Packing List
- Runs sanctions screening and restricted party checks
- 4-layer deepfake detection (EXIF, lighting, AI artifacts, metadata)
- Produces confidence scores (0–100%) per document
- Signs verification outcomes anchored to HCS

---

### 3. Carrier Adapter Agent — `truthforge-carrier-001`
**HCS Topic**: `0.0.8161248`

Council-grade carrier data ingestion and FedEx integration.

- Normalizes carrier data across Maersk, MSC, CMA CGM, FedEx
- Creates FedEx shipments via OAuth 2.0 sandbox API
- Tracks shipments in real time
- Validates delivery addresses
- Supports carrier-initiated independent verification via Carrier Portal

```python
carrier.process_order_shipment(order_data)
# Returns: tracking_number, shipment_id, label_url
```

---

### 4. Registry & Discovery Agent — `truthforge-registry-001`
**HCS Topic**: `0.0.8161249`

Agent health monitoring and HOL registry synchronization.

- Maintains live registry of all 5 agents
- Reports health scores and last-active timestamps
- Handles agent discovery requests with capability filtering
- Syncs with HOL registry on Hedera testnet
- Caches discovery results with configurable TTL

---

### 5. Evidence & Settlement Agent — `truthforge-evidence-001`
**HCS Topic**: `0.0.8161250`

Immutable proof generation and audit trail management.

- Submits consensus records to Hedera HCS
- Generates Port Trust Receipts with full fee breakdown
- Creates cryptographic audit references (`TX-0.0.453211@...`)
- Manages HBAR-denominated verification fee settlement
- Produces receipts readable by port authorities and customs

---

## Project Structure

```
truthforge/
├── agents/                          # 5 HOL-registered AI agents
│   ├── base_agent.py                # Abstract base with HCS-10 messaging
│   ├── orchestrator_agent.py        # Workflow coordinator
│   ├── verification_compliance_agent.py  # Document validation + deepfake detection
│   ├── carrier_adapter_agent.py     # FedEx + multi-carrier integration
│   ├── registry_discovery_agent.py  # HOL registry sync
│   ├── evidence_settlement_agent.py # HCS proof generation
│   ├── marketplace_agent.py         # WooCommerce order management
│   ├── fedex_client.py              # FedEx OAuth 2.0 client
│   ├── hedera_client.py             # Hedera SDK wrapper
│   ├── hcs10_message.py             # HCS-10 protocol messages
│   ├── config.py                    # Centralized configuration
│   └── error_handling.py            # Retry and error management
│
├── api/                             # Flask REST API
│   ├── app.py                       # Main app + all endpoints
│   ├── fastapi_app.py               # FastAPI alternative
│   └── auth.py                      # API key auth + role decorators
│
├── database/                        # Data persistence
│   ├── database.py                  # SQLAlchemy setup (PostgreSQL + SQLite)
│   ├── models.py                    # ORM models
│   ├── api_keys.py                  # API key model + roles
│   ├── services.py                  # Business logic layer
│   └── db_manager.py                # Connection management
│
├── woocommerce/webhooks/
│   └── order_webhook.py             # HMAC-verified webhook handler
│
├── hol_registry/
│   └── registry.py                  # Agent registration + discovery
│
├── utils/
│   └── api_keys.py                  # Key generation, hashing, validation
│
├── websocket/
│   └── routes.py                    # Real-time WebSocket updates
│
├── truthforge_frontend/             # React/Vite frontend
│   └── truthforge-logistics-verified-main/
│       └── src/
│           ├── pages/               # 6 dashboard pages
│           ├── components/          # UI components
│           ├── contexts/            # Auth, MockMode, Theme, Wallet
│           └── lib/mock-data.ts     # Mock data definitions
│
├── tests/                           # Full test suite (19 test files)
├── assets/                          # Project logo and static assets
├── .env.example                     # Configuration template
├── requirements.txt                 # Python dependencies
└── README.md
```

---

## Implementation Progress

### Backend — Complete ✅

| Module | Status | Details |
|---|---|---|
| Project structure & config | ✅ Done | Config dataclass, env loading, validation |
| Database layer | ✅ Done | SQLAlchemy ORM, PostgreSQL + SQLite, CRUD |
| HCS-10 messaging protocol | ✅ Done | MessageType enum, serialization, signatures |
| Hedera client | ✅ Done | Mock + Live modes, balance checking |
| Base agent class | ✅ Done | HOL registration, HCS messaging, health checks |
| HOL registry | ✅ Done | 5-agent registration, capability filtering |
| Verification & Compliance Agent | ✅ Done | 4-layer deepfake detection, BOL validation |
| Carrier Adapter Agent | ✅ Done | FedEx OAuth 2.0, multi-carrier normalization |
| Registry & Discovery Agent | ✅ Done | Health monitoring, TTL caching, DISCOVER messages |
| Evidence & Settlement Agent | ✅ Done | HCS submission, audit references, retry logic |
| Orchestrator Agent | ✅ Done | Intent parsing, workflow coordination, aggregation |
| Error handling & resilience | ✅ Done | Exponential backoff, retry decorators |
| Flask REST API | ✅ Done | All endpoints, CORS, auth middleware |
| WooCommerce webhook | ✅ Done | HMAC-verified order ingestion |
| API key management | ✅ Done | Role-based (PORT_AUTHORITY / ENTERPRISE / ADMIN) |
| WebSocket routes | ✅ Done | Real-time shipment updates |

### Frontend — Complete ✅

| Component | Status | Details |
|---|---|---|
| Welcome / Landing page | ✅ Done | Splash screen, tagline, product overview |
| Public Dashboard | ✅ Done | 5 tabs — clearance, verification, carrier, agents, tracking |
| Operator Dashboard | ✅ Done | Role-gated 6-tab dashboard |
| Carrier Portal | ✅ Done | Document upload + FedEx pickup scheduling |
| Agent Registry | ✅ Done | Desktop table + mobile cards, live health status |
| Port Trust Receipt | ✅ Done | 4-step verification card with HBAR fee breakdown |
| Pre-Arrival Clearance Queue | ✅ Done | Shipment queue with port filter |
| Global Trade Risk Command Center | ✅ Done | Shipment map, activity feed, AI risk alerts |
| Container Intelligence Panel | ✅ Done | Vessel trust score, container grid, verification table |
| Verification Fee & Wallet | ✅ Done | HBAR fee settlement, wallet integration |
| Pre-Clearance Request Modal | ✅ Done | Sea/air/land modes, cost estimation, payment flow |
| Governance Page | ✅ Done | Admin-only governance controls |
| Responsive design | ✅ Done | Desktop tables + mobile stacked cards |
| Mock/Live toggle | ✅ Done | Header toggle, context-driven data switching |
| Footer | ✅ Done | All pages, responsive 3-column layout |
| Splash screen | ✅ Done | 2.5s animated intro with logo |

### Testing — Complete ✅

| Suite | Tests | Status |
|---|---|---|
| `tests/test_base_agent.py` | Agent registration, HCS messaging | ✅ |
| `tests/test_config.py` | Config loading, validation | ✅ |
| `tests/test_hcs10_message.py` | Message structure, serialization | ✅ |
| `tests/test_hedera_client.py` | Mock/Live client, cost tracking | ✅ |
| `tests/test_registry.py` | 5-agent registration, uniqueness | ✅ |
| `tests/test_verification_compliance_agent.py` | Deepfake detection, BOL validation | ✅ |
| `tests/test_fedex_adapter.py` | FedEx OAuth, shipment creation | ✅ |
| `tests/test_orchestrator.py` | Intent parsing, workflow routing | ✅ |
| `tests/test_orchestrator_integration.py` | End-to-end flow | ✅ |
| `tests/test_error_handling.py` | Retry logic, backoff | ✅ |
| `tests/test_api.py` | All REST endpoints | ✅ |
| `tests/test_marketplace_agent.py` | WooCommerce order handling | ✅ |
| `tests/test_woocommerce_integration.py` | Webhook HMAC verification | ✅ |
| `tests/test_frontend_properties.py` | Responsive layout properties | ✅ |
| **Total** | **30 tests** | **✅ All passing** |

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Hedera testnet account

### 1. Backend Setup

```bash
git clone https://github.com/Ai-Tech-Haven/truthforge.git
cd truthforge

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials
```

### 2. Frontend Setup

```bash
cd truthforge_frontend/truthforge-logistics-verified-main
npm install
npm run dev
# Opens at http://localhost:5173
```

### 3. Start the API

```bash
python api/app.py
# API at http://localhost:5000
```

### 4. Register Agents on HOL

```bash
node register-agents.js
```

---

## Mock vs Live Mode

| Setting | Mock Mode (`MOCK_MODE=true`) | Live Mode (`MOCK_MODE=false`) |
|---|---|---|
| Hedera | Simulated HCS transactions | Real testnet transactions |
| FedEx | Mock tracking numbers | Live sandbox API |
| WooCommerce | Sample order data | Real store orders |
| Cost | Free | ~0.01 HBAR per verification |

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/v1/agents` | List all 5 registered agents | Optional |
| `GET` | `/api/v1/shipments` | Get shipment list | Optional |
| `GET` | `/api/v1/proof/<shipment_id>` | Get Port Trust Receipt | API Key |
| `POST` | `/api/v1/carrier/verify` | Carrier-initiated verification | API Key |
| `POST` | `/api/v1/keys/generate` | Generate API key | Admin |
| `POST` | `/webhook/woocommerce/order` | WooCommerce order webhook | HMAC |
| `GET` | `/health` | System health check | None |

### API Key Roles

| Role | Access |
|---|---|
| `PORT_AUTHORITY` | Read shipments, view proofs |
| `ENTERPRISE` | Full verification + carrier endpoints |
| `ADMIN` | All endpoints + key management |

---

## Verification Workflow

```
WooCommerce Order Created
        │
        ▼
Webhook → OrchestratorAgent.process_order()
        │
        ├─► MarketplaceAgent.get_order_details()
        │
        ├─► CarrierAdapterAgent.process_order_shipment()
        │         └─► FedExClient.create_shipment()
        │
        ├─► VerificationComplianceAgent (document checks)
        │
        └─► EvidenceSettlementAgent.submit_to_hcs()
                  └─► Port Trust Receipt issued
                        (HBAR fee settled on Hedera)
```

---

## Hedera Integration

- **Network**: Testnet (`0.0.7974354`)
- **Protocol**: HCS-10 for agent messaging
- **Topics**: 5 dedicated HCS topics (one per agent)
- **Fees**: ~0.01–0.24 HBAR per verification
- **HOL Registry**: All 5 agents registered with UAIDs

---

## Environment Variables

```bash
# Hedera
HEDERA_ACCOUNT_ID=0.0.7974354
HEDERA_NETWORK=testnet
HCS_TOPIC_ID=0.0.8109600

# FedEx Sandbox
FEDEX_ENVIRONMENT=sandbox
FEDEX_API_URL=https://apis-sandbox.fedex.com

# WooCommerce
WOOCOMMERCE_STORE_URL=https://www.a-thi.online
WOOCOMMERCE_ENABLED=false

# System
MOCK_MODE=false
PORT=5000
DATABASE_URL=postgresql://...
```

---

## Hackathon Tracks

- **AI & Agentic Track** — 5 autonomous HOL-registered agents with HCS-10 messaging
- **HOL Bounty** — Full HOL agent registration, discovery, and consensus anchoring
- **Real-World Impact** — Live WooCommerce store integration (`a-thi.online`)

---

## Links

- [Hedera Documentation](https://docs.hedera.com/)
- [HOL Documentation](https://docs.hedera.com/hol/)
- [WooCommerce REST API](https://woocommerce.github.io/woocommerce-rest-api-docs/)
- [FedEx Developer Portal](https://developer.fedex.com/)
- [Hedera Hello Future Hackathon](https://hellofuture.hedera.com/)

---

<p align="center"><em>Built for the Hedera Hello Future Apex Hackathon 2026</em></p>
