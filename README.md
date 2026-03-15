<p align="center">
  <img src="assets/truthforge-logo.png" alt="TruthForge Logo" width="180"/>
</p>

<h1 align="center">TruthForge</h1>
<p align="center"><strong>The Verifiable Intelligence Layer for Global Trade</strong></p>
<p align="center">
  <em>Hedera Hello Future Apex Hackathon 2026 Ã¢â‚¬â€ AI & Agentic Track + HOL Bounty</em>
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

TruthForge is a production-grade, multi-agent verification platform built on Hedera's Hashgraph Online (HOL) protocol. It delivers cryptographically anchored pre-arrival clearance for global shipments Ã¢â‚¬â€ connecting merchants, carriers, and port authorities through a unified, tamper-proof intelligence layer.

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
| Frontend | Deployed on [Vercel](https://vercel.com) â€” `truthforge_frontend/truthforge-logistics-verified-main` | âœ… Live |
| Backend API | [https://web-production-dcd43.up.railway.app](https://web-production-dcd43.up.railway.app) | âœ… Live |
| Hedera Network | Testnet (account `0.0.7974354`) | âœ… Connected |
| Database | Supabase PostgreSQL | âœ… Connected |

- **Public Dashboard** Ã¢â‚¬â€ `/public` Ã¢â‚¬â€ Port clearance, verification, agent registry, tracking
- **Operator Dashboard** Ã¢â‚¬â€ `/operator` Ã¢â‚¬â€ Role-based access (viewer / operator / admin)
- **Carrier Portal** Ã¢â‚¬â€ `/public` Ã¢â€ â€™ Carrier Portal tab Ã¢â‚¬â€ Independent document upload & pickup scheduling
- **Mock/Live Toggle** Ã¢â‚¬â€ Switch between simulated and live Hedera data in real time

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
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š                    TruthForge Platform                       Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¤
Ã¢â€â€š  React/Vite  Ã¢â€â€š  Public Dashboard  Ã¢â€â€š  Operator Dashboard     Ã¢â€â€š
Ã¢â€â€š  Frontend    Ã¢â€â€š  Carrier Portal    Ã¢â€â€š  Role-Based Access       Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â´Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¤
Ã¢â€â€š                    Flask REST API (Python)                    Ã¢â€â€š
Ã¢â€â€š         /api/v1/*  Ã¢â€â€š  WebSocket  Ã¢â€â€š  WooCommerce Webhook      Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¤
Ã¢â€â€š              5 HOL-Registered AI Agents                      Ã¢â€â€š
Ã¢â€â€š  Orchestrator Ã¢â€â€š Verification Ã¢â€â€š Carrier Ã¢â€â€š Registry Ã¢â€â€š Evidence Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¤
Ã¢â€â€š         Hedera Consensus Service (HCS-10 Protocol)           Ã¢â€â€š
Ã¢â€â€š              Immutable Audit Trail on Testnet                Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¤
Ã¢â€â€š   WooCommerce REST API   Ã¢â€â€š   FedEx Sandbox API              Ã¢â€â€š
Ã¢â€â€š   a-thi.online           Ã¢â€â€š   OAuth 2.0 + Shipment Creation  Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â´Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
```

---

## The 5 HOL-Registered Agents

### 1. Orchestrator Agent Ã¢â‚¬â€ `truthforge-orch-001`
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

### 2. Verification & Compliance Agent Ã¢â‚¬â€ `truthforge-verify-001`
**HCS Topic**: `0.0.8161247`

Document intelligence and compliance enforcement.

- Validates Bill of Lading, Commercial Invoice, Packing List
- Runs sanctions screening and restricted party checks
- 4-layer deepfake detection (EXIF, lighting, AI artifacts, metadata)
- Produces confidence scores (0Ã¢â‚¬â€œ100%) per document
- Signs verification outcomes anchored to HCS

---

### 3. Carrier Adapter Agent Ã¢â‚¬â€ `truthforge-carrier-001`
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

### 4. Registry & Discovery Agent Ã¢â‚¬â€ `truthforge-registry-001`
**HCS Topic**: `0.0.8161249`

Agent health monitoring and HOL registry synchronization.

- Maintains live registry of all 5 agents
- Reports health scores and last-active timestamps
- Handles agent discovery requests with capability filtering
- Syncs with HOL registry on Hedera testnet
- Caches discovery results with configurable TTL

---

### 5. Evidence & Settlement Agent Ã¢â‚¬â€ `truthforge-evidence-001`
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
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ agents/                          # 5 HOL-registered AI agents
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ base_agent.py                # Abstract base with HCS-10 messaging
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ orchestrator_agent.py        # Workflow coordinator
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ verification_compliance_agent.py  # Document validation + deepfake detection
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ carrier_adapter_agent.py     # FedEx + multi-carrier integration
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ registry_discovery_agent.py  # HOL registry sync
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ evidence_settlement_agent.py # HCS proof generation
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ marketplace_agent.py         # WooCommerce order management
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ fedex_client.py              # FedEx OAuth 2.0 client
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ hedera_client.py             # Hedera SDK wrapper
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ hcs10_message.py             # HCS-10 protocol messages
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ config.py                    # Centralized configuration
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ error_handling.py            # Retry and error management
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ api/                             # Flask REST API
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ app.py                       # Main app + all endpoints
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ fastapi_app.py               # FastAPI alternative
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ auth.py                      # API key auth + role decorators
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ database/                        # Data persistence
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ database.py                  # SQLAlchemy setup (PostgreSQL + SQLite)
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ models.py                    # ORM models
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ api_keys.py                  # API key model + roles
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ services.py                  # Business logic layer
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ db_manager.py                # Connection management
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ woocommerce/webhooks/
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ order_webhook.py             # HMAC-verified webhook handler
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ hol_registry/
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ registry.py                  # Agent registration + discovery
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ utils/
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ api_keys.py                  # Key generation, hashing, validation
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ websocket/
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ routes.py                    # Real-time WebSocket updates
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ truthforge_frontend/             # React/Vite frontend
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ truthforge-logistics-verified-main/
Ã¢â€â€š       Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ src/
Ã¢â€â€š           Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ pages/               # 6 dashboard pages
Ã¢â€â€š           Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ components/          # UI components
Ã¢â€â€š           Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ contexts/            # Auth, MockMode, Theme, Wallet
Ã¢â€â€š           Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ lib/mock-data.ts     # Mock data definitions
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ tests/                           # Full test suite (19 test files)
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ assets/                          # Project logo and static assets
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ .env.example                     # Configuration template
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ requirements.txt                 # Python dependencies
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ README.md
```

---

## Implementation Progress

### Backend Ã¢â‚¬â€ Complete Ã¢Å“â€¦

| Module | Status | Details |
|---|---|---|
| Project structure & config | Ã¢Å“â€¦ Done | Config dataclass, env loading, validation |
| Database layer | Ã¢Å“â€¦ Done | SQLAlchemy ORM, PostgreSQL + SQLite, CRUD |
| HCS-10 messaging protocol | Ã¢Å“â€¦ Done | MessageType enum, serialization, signatures |
| Hedera client | Ã¢Å“â€¦ Done | Mock + Live modes, balance checking |
| Base agent class | Ã¢Å“â€¦ Done | HOL registration, HCS messaging, health checks |
| HOL registry | Ã¢Å“â€¦ Done | 5-agent registration, capability filtering |
| Verification & Compliance Agent | Ã¢Å“â€¦ Done | 4-layer deepfake detection, BOL validation |
| Carrier Adapter Agent | Ã¢Å“â€¦ Done | FedEx OAuth 2.0, multi-carrier normalization |
| Registry & Discovery Agent | Ã¢Å“â€¦ Done | Health monitoring, TTL caching, DISCOVER messages |
| Evidence & Settlement Agent | Ã¢Å“â€¦ Done | HCS submission, audit references, retry logic |
| Orchestrator Agent | Ã¢Å“â€¦ Done | Intent parsing, workflow coordination, aggregation |
| Error handling & resilience | Ã¢Å“â€¦ Done | Exponential backoff, retry decorators |
| Flask REST API | Ã¢Å“â€¦ Done | All endpoints, CORS, auth middleware |
| WooCommerce webhook | Ã¢Å“â€¦ Done | HMAC-verified order ingestion |
| API key management | Ã¢Å“â€¦ Done | Role-based (PORT_AUTHORITY / ENTERPRISE / ADMIN) |
| WebSocket routes | Ã¢Å“â€¦ Done | Real-time shipment updates |

### Frontend Ã¢â‚¬â€ Complete Ã¢Å“â€¦

| Component | Status | Details |
|---|---|---|
| Welcome / Landing page | Ã¢Å“â€¦ Done | Splash screen, tagline, product overview |
| Public Dashboard | Ã¢Å“â€¦ Done | 5 tabs Ã¢â‚¬â€ clearance, verification, carrier, agents, tracking |
| Operator Dashboard | Ã¢Å“â€¦ Done | Role-gated 6-tab dashboard |
| Carrier Portal | Ã¢Å“â€¦ Done | Document upload + FedEx pickup scheduling |
| Agent Registry | Ã¢Å“â€¦ Done | Desktop table + mobile cards, live health status |
| Port Trust Receipt | Ã¢Å“â€¦ Done | 4-step verification card with HBAR fee breakdown |
| Pre-Arrival Clearance Queue | Ã¢Å“â€¦ Done | Shipment queue with port filter |
| Global Trade Risk Command Center | Ã¢Å“â€¦ Done | Shipment map, activity feed, AI risk alerts |
| Container Intelligence Panel | Ã¢Å“â€¦ Done | Vessel trust score, container grid, verification table |
| Verification Fee & Wallet | Ã¢Å“â€¦ Done | HBAR fee settlement, wallet integration |
| Pre-Clearance Request Modal | Ã¢Å“â€¦ Done | Sea/air/land modes, cost estimation, payment flow |
| Governance Page | Ã¢Å“â€¦ Done | Admin-only governance controls |
| Responsive design | Ã¢Å“â€¦ Done | Desktop tables + mobile stacked cards |
| Mock/Live toggle | Ã¢Å“â€¦ Done | Header toggle, context-driven data switching |
| Footer | Ã¢Å“â€¦ Done | All pages, responsive 3-column layout |
| Splash screen | Ã¢Å“â€¦ Done | 2.5s animated intro with logo |

### Testing Ã¢â‚¬â€ Complete Ã¢Å“â€¦

| Suite | Tests | Status |
|---|---|---|
| `tests/test_base_agent.py` | Agent registration, HCS messaging | Ã¢Å“â€¦ |
| `tests/test_config.py` | Config loading, validation | Ã¢Å“â€¦ |
| `tests/test_hcs10_message.py` | Message structure, serialization | Ã¢Å“â€¦ |
| `tests/test_hedera_client.py` | Mock/Live client, cost tracking | Ã¢Å“â€¦ |
| `tests/test_registry.py` | 5-agent registration, uniqueness | Ã¢Å“â€¦ |
| `tests/test_verification_compliance_agent.py` | Deepfake detection, BOL validation | Ã¢Å“â€¦ |
| `tests/test_fedex_adapter.py` | FedEx OAuth, shipment creation | Ã¢Å“â€¦ |
| `tests/test_orchestrator.py` | Intent parsing, workflow routing | Ã¢Å“â€¦ |
| `tests/test_orchestrator_integration.py` | End-to-end flow | Ã¢Å“â€¦ |
| `tests/test_error_handling.py` | Retry logic, backoff | Ã¢Å“â€¦ |
| `tests/test_api.py` | All REST endpoints | Ã¢Å“â€¦ |
| `tests/test_marketplace_agent.py` | WooCommerce order handling | Ã¢Å“â€¦ |
| `tests/test_woocommerce_integration.py` | Webhook HMAC verification | Ã¢Å“â€¦ |
| `tests/test_frontend_properties.py` | Responsive layout properties | Ã¢Å“â€¦ |
| **Total** | **30 tests** | **Ã¢Å“â€¦ All passing** |

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
        Ã¢â€â€š
        Ã¢â€“Â¼
Webhook Ã¢â€ â€™ OrchestratorAgent.process_order()
        Ã¢â€â€š
        Ã¢â€Å“Ã¢â€â‚¬Ã¢â€“Âº MarketplaceAgent.get_order_details()
        Ã¢â€â€š
        Ã¢â€Å“Ã¢â€â‚¬Ã¢â€“Âº CarrierAdapterAgent.process_order_shipment()
        Ã¢â€â€š         Ã¢â€â€Ã¢â€â‚¬Ã¢â€“Âº FedExClient.create_shipment()
        Ã¢â€â€š
        Ã¢â€Å“Ã¢â€â‚¬Ã¢â€“Âº VerificationComplianceAgent (document checks)
        Ã¢â€â€š
        Ã¢â€â€Ã¢â€â‚¬Ã¢â€“Âº EvidenceSettlementAgent.submit_to_hcs()
                  Ã¢â€â€Ã¢â€â‚¬Ã¢â€“Âº Port Trust Receipt issued
                        (HBAR fee settled on Hedera)
```

---

## Hedera Integration

- **Network**: Testnet (`0.0.7974354`)
- **Protocol**: HCS-10 for agent messaging
- **Topics**: 5 dedicated HCS topics (one per agent)
- **Fees**: ~0.01Ã¢â‚¬â€œ0.24 HBAR per verification
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

- **AI & Agentic Track** Ã¢â‚¬â€ 5 autonomous HOL-registered agents with HCS-10 messaging
- **HOL Bounty** Ã¢â‚¬â€ Full HOL agent registration, discovery, and consensus anchoring
- **Real-World Impact** Ã¢â‚¬â€ Live WooCommerce store integration (`a-thi.online`)

---

## Links

- [Hedera Documentation](https://docs.hedera.com/)
- [HOL Documentation](https://docs.hedera.com/hol/)
- [WooCommerce REST API](https://woocommerce.github.io/woocommerce-rest-api-docs/)
- [FedEx Developer Portal](https://developer.fedex.com/)
- [Hedera Hello Future Hackathon](https://hellofuture.hedera.com/)

---

<p align="center"><em>Built for the Hedera Hello Future Apex Hackathon 2026</em></p>
