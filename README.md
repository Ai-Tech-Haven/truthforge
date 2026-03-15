<p align="center">
  <img src="assets/truthforge-logo.png" alt="TruthForge Logo" width="180"/>
</p>

<h1 align="center">TruthForge</h1>
<p align="center"><strong>The Verifiable Intelligence Layer for Global Trade</strong></p>
<p align="center">
  <em>Hedera Hello Future Apex Hackathon 2026 â€” AI & Agentic Track + HOL Bounty</em>
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

TruthForge is a production-grade, multi-agent verification platform built on Hedera's Hashgraph Online (HOL) protocol. It delivers cryptographically anchored pre-arrival clearance for global shipments â€” connecting merchants, carriers, and port authorities through a unified, tamper-proof intelligence layer.

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

| Layer | URL | Status |
|---|---|---|
| Frontend | Deployed via Vercel / Netlify | âœ… Live |
| Backend API | Deployed on [Railway](https://railway.app) | âœ… Live |
| Hedera Network | Testnet (account `0.0.7974354`) | âœ… Connected |
| Database | Supabase PostgreSQL | âœ… Connected |

- **Public Dashboard** â€” `/public` â€” Port clearance, verification, agent registry, tracking
- **Operator Dashboard** â€” `/operator` â€” Role-based access (viewer / operator / admin)
- **Carrier Portal** â€” `/public` â†’ Carrier Portal tab â€” Independent document upload & pickup scheduling
- **Mock/Live Toggle** â€” Switch between simulated and live Hedera data in real time

### Backend API Endpoints (Railway)

| Endpoint | Method | Description |
|---|---|---|
| `/api/verify` | POST | Submit document/shipment verification |
| `/api/status/<id>` | GET | Get verification status |
| `/api/agents` | GET | List all 5 HOL-registered agents |
| `/api/dashboard/metrics` | GET | Live operational metrics |
| `/api/clearance/queue` | GET | Pre-arrival clearance queue |
| `/webhook/woocommerce/order` | POST | WooCommerce order webhook (HMAC-verified) |

---

## Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    TruthForge Platform                       â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  React/Vite  â”‚  Public Dashboard  â”‚  Operator Dashboard     â”‚
â”‚  Frontend    â”‚  Carrier Portal    â”‚  Role-Based Access       â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                    Flask REST API (Python)                    â”‚
â”‚         /api/v1/*  â”‚  WebSocket  â”‚  WooCommerce Webhook      â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚              5 HOL-Registered AI Agents                      â”‚
â”‚  Orchestrator â”‚ Verification â”‚ Carrier â”‚ Registry â”‚ Evidence â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚         Hedera Consensus Service (HCS-10 Protocol)           â”‚
â”‚              Immutable Audit Trail on Testnet                â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚   WooCommerce REST API   â”‚   FedEx Sandbox API              â”‚
â”‚   a-thi.online           â”‚   OAuth 2.0 + Shipment Creation  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## The 5 HOL-Registered Agents

### 1. Orchestrator Agent â€” `truthforge-orch-001`
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

### 2. Verification & Compliance Agent â€” `truthforge-verify-001`
**HCS Topic**: `0.0.8161247`

Document intelligence and compliance enforcement.

- Validates Bill of Lading, Commercial Invoice, Packing List
- Runs sanctions screening and restricted party checks
- 4-layer deepfake detection (EXIF, lighting, AI artifacts, metadata)
- Produces confidence scores (0â€“100%) per document
- Signs verification outcomes anchored to HCS

---

### 3. Carrier Adapter Agent â€” `truthforge-carrier-001`
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

### 4. Registry & Discovery Agent â€” `truthforge-registry-001`
**HCS Topic**: `0.0.8161249`

Agent health monitoring and HOL registry synchronization.

- Maintains live registry of all 5 agents
- Reports health scores and last-active timestamps
- Handles agent discovery requests with capability filtering
- Syncs with HOL registry on Hedera testnet
- Caches discovery results with configurable TTL

---

### 5. Evidence & Settlement Agent â€” `truthforge-evidence-001`
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
â”œâ”€â”€ agents/                          # 5 HOL-registered AI agents
â”‚   â”œâ”€â”€ base_agent.py                # Abstract base with HCS-10 messaging
â”‚   â”œâ”€â”€ orchestrator_agent.py        # Workflow coordinator
â”‚   â”œâ”€â”€ verification_compliance_agent.py  # Document validation + deepfake detection
â”‚   â”œâ”€â”€ carrier_adapter_agent.py     # FedEx + multi-carrier integration
â”‚   â”œâ”€â”€ registry_discovery_agent.py  # HOL registry sync
â”‚   â”œâ”€â”€ evidence_settlement_agent.py # HCS proof generation
â”‚   â”œâ”€â”€ marketplace_agent.py         # WooCommerce order management
â”‚   â”œâ”€â”€ fedex_client.py              # FedEx OAuth 2.0 client
â”‚   â”œâ”€â”€ hedera_client.py             # Hedera SDK wrapper
â”‚   â”œâ”€â”€ hcs10_message.py             # HCS-10 protocol messages
â”‚   â”œâ”€â”€ config.py                    # Centralized configuration
â”‚   â””â”€â”€ error_handling.py            # Retry and error management
â”‚
â”œâ”€â”€ api/                             # Flask REST API
â”‚   â”œâ”€â”€ app.py                       # Main app + all endpoints
â”‚   â”œâ”€â”€ fastapi_app.py               # FastAPI alternative
â”‚   â””â”€â”€ auth.py                      # API key auth + role decorators
â”‚
â”œâ”€â”€ database/                        # Data persistence
â”‚   â”œâ”€â”€ database.py                  # SQLAlchemy setup (PostgreSQL + SQLite)
â”‚   â”œâ”€â”€ models.py                    # ORM models
â”‚   â”œâ”€â”€ api_keys.py                  # API key model + roles
â”‚   â”œâ”€â”€ services.py                  # Business logic layer
â”‚   â””â”€â”€ db_manager.py                # Connection management
â”‚
â”œâ”€â”€ woocommerce/webhooks/
â”‚   â””â”€â”€ order_webhook.py             # HMAC-verified webhook handler
â”‚
â”œâ”€â”€ hol_registry/
â”‚   â””â”€â”€ registry.py                  # Agent registration + discovery
â”‚
â”œâ”€â”€ utils/
â”‚   â””â”€â”€ api_keys.py                  # Key generation, hashing, validation
â”‚
â”œâ”€â”€ websocket/
â”‚   â””â”€â”€ routes.py                    # Real-time WebSocket updates
â”‚
â”œâ”€â”€ truthforge_frontend/             # React/Vite frontend
â”‚   â””â”€â”€ truthforge-logistics-verified-main/
â”‚       â””â”€â”€ src/
â”‚           â”œâ”€â”€ pages/               # 6 dashboard pages
â”‚           â”œâ”€â”€ components/          # UI components
â”‚           â”œâ”€â”€ contexts/            # Auth, MockMode, Theme, Wallet
â”‚           â””â”€â”€ lib/mock-data.ts     # Mock data definitions
â”‚
â”œâ”€â”€ tests/                           # Full test suite (19 test files)
â”œâ”€â”€ assets/                          # Project logo and static assets
â”œâ”€â”€ .env.example                     # Configuration template
â”œâ”€â”€ requirements.txt                 # Python dependencies
â””â”€â”€ README.md
```

---

## Implementation Progress

### Backend â€” Complete âœ…

| Module | Status | Details |
|---|---|---|
| Project structure & config | âœ… Done | Config dataclass, env loading, validation |
| Database layer | âœ… Done | SQLAlchemy ORM, PostgreSQL + SQLite, CRUD |
| HCS-10 messaging protocol | âœ… Done | MessageType enum, serialization, signatures |
| Hedera client | âœ… Done | Mock + Live modes, balance checking |
| Base agent class | âœ… Done | HOL registration, HCS messaging, health checks |
| HOL registry | âœ… Done | 5-agent registration, capability filtering |
| Verification & Compliance Agent | âœ… Done | 4-layer deepfake detection, BOL validation |
| Carrier Adapter Agent | âœ… Done | FedEx OAuth 2.0, multi-carrier normalization |
| Registry & Discovery Agent | âœ… Done | Health monitoring, TTL caching, DISCOVER messages |
| Evidence & Settlement Agent | âœ… Done | HCS submission, audit references, retry logic |
| Orchestrator Agent | âœ… Done | Intent parsing, workflow coordination, aggregation |
| Error handling & resilience | âœ… Done | Exponential backoff, retry decorators |
| Flask REST API | âœ… Done | All endpoints, CORS, auth middleware |
| WooCommerce webhook | âœ… Done | HMAC-verified order ingestion |
| API key management | âœ… Done | Role-based (PORT_AUTHORITY / ENTERPRISE / ADMIN) |
| WebSocket routes | âœ… Done | Real-time shipment updates |

### Frontend â€” Complete âœ…

| Component | Status | Details |
|---|---|---|
| Welcome / Landing page | âœ… Done | Splash screen, tagline, product overview |
| Public Dashboard | âœ… Done | 5 tabs â€” clearance, verification, carrier, agents, tracking |
| Operator Dashboard | âœ… Done | Role-gated 6-tab dashboard |
| Carrier Portal | âœ… Done | Document upload + FedEx pickup scheduling |
| Agent Registry | âœ… Done | Desktop table + mobile cards, live health status |
| Port Trust Receipt | âœ… Done | 4-step verification card with HBAR fee breakdown |
| Pre-Arrival Clearance Queue | âœ… Done | Shipment queue with port filter |
| Global Trade Risk Command Center | âœ… Done | Shipment map, activity feed, AI risk alerts |
| Container Intelligence Panel | âœ… Done | Vessel trust score, container grid, verification table |
| Verification Fee & Wallet | âœ… Done | HBAR fee settlement, wallet integration |
| Pre-Clearance Request Modal | âœ… Done | Sea/air/land modes, cost estimation, payment flow |
| Governance Page | âœ… Done | Admin-only governance controls |
| Responsive design | âœ… Done | Desktop tables + mobile stacked cards |
| Mock/Live toggle | âœ… Done | Header toggle, context-driven data switching |
| Footer | âœ… Done | All pages, responsive 3-column layout |
| Splash screen | âœ… Done | 2.5s animated intro with logo |

### Testing â€” Complete âœ…

| Suite | Tests | Status |
|---|---|---|
| `tests/test_base_agent.py` | Agent registration, HCS messaging | âœ… |
| `tests/test_config.py` | Config loading, validation | âœ… |
| `tests/test_hcs10_message.py` | Message structure, serialization | âœ… |
| `tests/test_hedera_client.py` | Mock/Live client, cost tracking | âœ… |
| `tests/test_registry.py` | 5-agent registration, uniqueness | âœ… |
| `tests/test_verification_compliance_agent.py` | Deepfake detection, BOL validation | âœ… |
| `tests/test_fedex_adapter.py` | FedEx OAuth, shipment creation | âœ… |
| `tests/test_orchestrator.py` | Intent parsing, workflow routing | âœ… |
| `tests/test_orchestrator_integration.py` | End-to-end flow | âœ… |
| `tests/test_error_handling.py` | Retry logic, backoff | âœ… |
| `tests/test_api.py` | All REST endpoints | âœ… |
| `tests/test_marketplace_agent.py` | WooCommerce order handling | âœ… |
| `tests/test_woocommerce_integration.py` | Webhook HMAC verification | âœ… |
| `tests/test_frontend_properties.py` | Responsive layout properties | âœ… |
| **Total** | **30 tests** | **âœ… All passing** |

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
        â”‚
        â–¼
Webhook â†’ OrchestratorAgent.process_order()
        â”‚
        â”œâ”€â–º MarketplaceAgent.get_order_details()
        â”‚
        â”œâ”€â–º CarrierAdapterAgent.process_order_shipment()
        â”‚         â””â”€â–º FedExClient.create_shipment()
        â”‚
        â”œâ”€â–º VerificationComplianceAgent (document checks)
        â”‚
        â””â”€â–º EvidenceSettlementAgent.submit_to_hcs()
                  â””â”€â–º Port Trust Receipt issued
                        (HBAR fee settled on Hedera)
```

---

## Hedera Integration

- **Network**: Testnet (`0.0.7974354`)
- **Protocol**: HCS-10 for agent messaging
- **Topics**: 5 dedicated HCS topics (one per agent)
- **Fees**: ~0.01â€“0.24 HBAR per verification
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

- **AI & Agentic Track** â€” 5 autonomous HOL-registered agents with HCS-10 messaging
- **HOL Bounty** â€” Full HOL agent registration, discovery, and consensus anchoring
- **Real-World Impact** â€” Live WooCommerce store integration (`a-thi.online`)

---

## Links

- [Hedera Documentation](https://docs.hedera.com/)
- [HOL Documentation](https://docs.hedera.com/hol/)
- [WooCommerce REST API](https://woocommerce.github.io/woocommerce-rest-api-docs/)
- [FedEx Developer Portal](https://developer.fedex.com/)
- [Hedera Hello Future Hackathon](https://hellofuture.hedera.com/)

---

<p align="center"><em>Built for the Hedera Hello Future Apex Hackathon 2026</em></p>
