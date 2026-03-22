# TruthForge — Complete Project Status
**Date:** March 15, 2026
**Repo:** `Ai-Tech-Haven/truthforge` | **Branch:** `main` | **HEAD:** `de73977`
**Event:** Hedera Hello Future Apex Hackathon 2026 — AI & Agentic Track + HOL Bounty

---

## Live Deployments

| Layer | URL | Status |
|---|---|---|
| Backend API | https://web-production-dcd43.up.railway.app | ✅ Live — Railway |
| Frontend | Vercel (manual deploy from `truthforge_frontend/truthforge-logistics-verified-main/`) | ✅ Live — Vercel |
| Hedera Network | Testnet — Account `0.0.7974354` | ✅ Connected |
| Database | Supabase PostgreSQL | ✅ Connected |
| WooCommerce Store | https://www.a-thi.online | ✅ Integrated |

---

## Backend — Railway Deployment

| Item | File | Status |
|---|---|---|
| WSGI entry point | `main.py` → `app = create_wsgi_app()` | ✅ |
| Process config | `Procfile` → `gunicorn main:app` | ✅ |
| Python version | `runtime.txt` → `python-3.11.x` | ✅ |
| Dependencies | `requirements.txt` — no Java SDK | ✅ |
| Build config | `nixpacks.toml` → `pip install --no-cache-dir` | ✅ |
| Logging | `main.py` — stdout only, no FileHandler | ✅ Fixed |
| Hedera client | `agents/hedera_client.py` — pure REST API | ✅ Fixed |
| Mock/Live mode | `MOCK_MODE=false` in Railway env vars | ✅ |
| CORS | `/api/*` open, all origins | ✅ |

### Railway Environment Variables Required
```
HEDERA_ACCOUNT_ID=0.0.7974354
HEDERA_PRIVATE_KEY=<key>
HEDERA_NETWORK=testnet
HCS_TOPIC_ID=0.0.8109600
MOCK_MODE=false
DATABASE_URL=postgresql://...
FEDEX_API_KEY=<key>
FEDEX_SECRET_KEY=<key>
FEDEX_ACCOUNT_NUMBER=<number>
WOOCOMMERCE_STORE_URL=https://www.a-thi.online
WOOCOMMERCE_CONSUMER_KEY=<key>
WOOCOMMERCE_CONSUMER_SECRET=<secret>
WOOCOMMERCE_WEBHOOK_SECRET=<secret>
PORT=5000
```

---

## The 5 HOL-Registered Agents

| Agent ID | Name | HCS Topic | Capabilities |
|---|---|---|---|
| `truthforge-orch-001` | Orchestrator Agent | `0.0.8161244` | workflow_coordination, decision_execution, agent_routing |
| `truthforge-verify-001` | Verification & Compliance Agent | `0.0.8161247` | document_validation, compliance_assessment, deepfake_detection |
| `truthforge-carrier-001` | Carrier Adapter Agent (Council-Grade) | `0.0.8161248` | carrier_data_ingestion, data_normalization, multi_carrier_support |
| `truthforge-registry-001` | Registry & Discovery Agent | `0.0.8161249` | agent_discovery, health_reporting, registry_sync |
| `truthforge-evidence-001` | Evidence & Settlement Agent | `0.0.8161250` | consensus_submission, audit_reference_generation, settlement_processing |

All 5 agents registered with HOL registry. Each has a dedicated HCS topic on Hedera testnet.

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/verify` | Bearer token | Submit verification request |
| GET | `/api/status/<id>` | None | Get verification status |
| GET | `/api/history` | Bearer token | Verification history |
| GET | `/api/agents` | None | List all 5 HOL agents |
| GET | `/api/dashboard/metrics` | None | Live operational metrics |
| GET | `/api/clearance/queue` | None | Pre-arrival clearance queue |
| GET | `/api/port-trust-receipts` | None | Port trust receipts |
| POST | `/webhook/woocommerce/order` | HMAC-SHA256 | WooCommerce order webhook |
| GET | `/health` | None | System health check |

### API Key Roles
| Role | Access |
|---|---|
| `PORT_AUTHORITY` | Read shipments, view proofs |
| `ENTERPRISE` | Full verification + carrier endpoints |
| `ADMIN` | All endpoints + key management |

---

## Frontend — Vercel

### Production Config
| File | Status | Notes |
|---|---|---|
| `.env.production` | ✅ | `VITE_API_URL=https://web-production-dcd43.up.railway.app` |
| `src/lib/api-client.ts` | ✅ | Central API config, env-var driven, no hardcoded URLs |
| `vite.config.ts` | ✅ | Dev proxy to `localhost:5000`, production uses env var |
| `index.html` | ✅ | Favicon linked — `/favicon.png` (real TruthForge logo) |

### Logo — All Fixed
| Location | Status | Notes |
|---|---|---|
| Browser tab favicon | ✅ | Real logo via `<link rel="icon" href="/favicon.png">` |
| Header | ✅ | `src/assets/truthforge-logo.png` |
| Footer | ✅ | Real logo — was Shield icon, now fixed |
| WelcomePage | ✅ | Real logo — was Shield icon, now fixed |
| OperatorDashboardPage | ✅ | Real logo — was Shield icon, now fixed |
| SplashScreen | ✅ | Real logo, animated intro |

### Pages & Routes
| Page | Route | Access | Status |
|---|---|---|---|
| Welcome / Landing | `/` | Public | ✅ |
| Public Dashboard | `/public` | Public | ✅ |
| Sign In | `/signin` | Public | ✅ |
| Operator Dashboard | `/operator` | Authenticated | ✅ Role-gated |
| Carrier Portal | `/public` → Carrier tab | Public | ✅ |
| Governance | `/operator` → Governance tab | Operator/Admin only | ✅ |

### Dashboard Tabs (Public)
| Tab | Status |
|---|---|
| Port Clearance Dashboard | ✅ Pre-arrival queue, shipment map |
| Verification & Compliance | ✅ Document validation, deepfake detection |
| Carrier Portal | ✅ Document upload, FedEx pickup scheduling |
| Agent Registry | ✅ 5-agent health table, live status |
| Operational Oversight | ✅ Metrics, tracking, activity feed |

### Key Components
| Component | Status |
|---|---|
| `Header.tsx` | ✅ Logo, tabs, mock/live toggle, theme switch |
| `Footer.tsx` | ✅ Real logo, 3-column layout, responsive |
| `SplashScreen.tsx` | ✅ 2.5s animated intro |
| `CarrierPortal.tsx` | ✅ Doc upload, FedEx pickup, live API calls |
| `PortTrustReceipt.tsx` | ✅ 4-step verification, HBAR fee breakdown |
| `GlobalTradeRiskCommandCenter.tsx` | ✅ Shipment map, AI risk alerts |
| `PreClearanceIntelligencePanel.tsx` | ✅ Vessel trust score, container grid |
| `PreClearanceRequestModal.tsx` | ✅ Sea/air/land modes, cost estimation |
| `FloatingChat.tsx` | ✅ Available to authenticated users |

---

## Security

| Item | Status |
|---|---|
| WooCommerce webhook HMAC-SHA256 verification | ✅ `woocommerce/webhooks/order_webhook.py` |
| Webhook skips verification in mock mode | ✅ Safe for dev/test |
| API Bearer token auth decorator | ✅ `require_auth` in `api/app.py` |
| Role-based access control | ✅ `api/auth.py` |
| CORS restricted to `/api/*` | ✅ |
| API key hashing | ✅ `utils/api_keys.py` |
| `.env` gitignored | ✅ |

---

## Database

| Item | Status |
|---|---|
| Engine | SQLAlchemy — PostgreSQL (prod) / SQLite (dev fallback) |
| Models | `Agent`, `Shipment`, `Verification`, `Metrics`, `ApiKey` |
| Services | `AgentService`, `ShipmentService`, `MetricsService` |
| Init script | `init_database.py` / `init_database.bat` |
| Connection test | `test_connection()` on startup |

---

## Hedera Integration

| Item | Status |
|---|---|
| SDK | Pure REST API — no Java, no `hedera-sdk-py` | ✅ |
| Mirror node | `https://testnet.mirrornode.hedera.com` | ✅ |
| HCS-10 protocol | `agents/hcs10_message.py` — full message types | ✅ |
| Mock client | `MockHederaClient` — dev/test without real network | ✅ |
| Live client | `HederaClient` — REST-based, graceful fallback | ✅ |
| Account balance check | Mirror node `/api/v1/accounts/{id}` | ✅ |
| Topic messages | Mirror node `/api/v1/topics/{id}/messages` | ✅ |
| Cost tracking | `total_cost_hbar` per client instance | ✅ |

---

## Integrations

### FedEx
| Item | Status |
|---|---|
| OAuth 2.0 token flow | ✅ `agents/fedex_client.py` |
| Shipment creation | ✅ Sandbox API |
| Real-time tracking | ✅ |
| Address validation | ✅ |
| Environment | Sandbox (`apis-sandbox.fedex.com`) |

### WooCommerce
| Item | Status |
|---|---|
| REST API client | ✅ `woocommerce==3.0.0` |
| Order webhook ingestion | ✅ HMAC-verified |
| Order processing via orchestrator | ✅ |
| Store URL | `https://www.a-thi.online` |

---

## Test Suite — 30 Tests

| Test File | What It Covers | Status |
|---|---|---|
| `test_base_agent.py` | HOL registration, HCS messaging, health checks | ✅ |
| `test_config.py` | Config loading, env vars, validation | ✅ |
| `test_hcs10_message.py` | Message types, serialization, signatures | ✅ |
| `test_hedera_client.py` | Mock/Live client, balance, cost tracking | ✅ |
| `test_registry.py` | 5-agent registration, uniqueness, capability filter | ✅ |
| `test_verification_compliance_agent.py` | Deepfake detection, BOL validation, confidence scores | ✅ |
| `test_fedex_adapter.py` | FedEx OAuth, shipment creation, tracking | ✅ |
| `test_orchestrator.py` | Intent parsing, workflow routing | ✅ |
| `test_orchestrator_integration.py` | End-to-end order-to-clearance flow | ✅ |
| `test_error_handling.py` | Retry logic, exponential backoff | ✅ |
| `test_api.py` | All REST endpoints, auth, CORS | ✅ |
| `test_marketplace_agent.py` | WooCommerce order handling | ✅ |
| `test_woocommerce_integration.py` | Webhook HMAC verification | ✅ |
| `test_frontend_properties.py` | Responsive layout properties | ✅ |

Run all tests:
```bash
pytest tests/ -v
```

---

## Recent Git History

```
de73977  Fix: Replace all placeholder icons with real TruthForge logo, add favicon
cfee7ad  Fix: Remove FileHandler to prevent Railway read-only filesystem crash
da1f2d7  Docs: Update live demo with Railway URL and Vercel frontend info
2b781a2  Feat: Add dev proxy in vite.config.ts for local backend
2d8a2e1  Fix: Use API_BASE from api-client in CarrierPortal fetch call
504182f  Feat: Add central api-client.ts with VITE_API_URL support
866b463  Feat: Add .env.production with Railway backend URL
fee27aa  Fix: Secure WooCommerce webhook with HMAC-SHA256 base64 verification
dee4dfe  Fix: Expose module-level app for gunicorn (main:app)
523dabd  Fix: Replace hedera-sdk-py with pure REST API client (no Java required)
```

---

## Project Structure

```
truthforge/
├── agents/                          # 5 HOL-registered AI agents
│   ├── base_agent.py                # Abstract base, HCS-10 messaging
│   ├── orchestrator_agent.py        # Workflow coordinator
│   ├── verification_compliance_agent.py
│   ├── carrier_adapter_agent.py     # FedEx + multi-carrier
│   ├── registry_discovery_agent.py
│   ├── evidence_settlement_agent.py
│   ├── marketplace_agent.py         # WooCommerce orders
│   ├── fedex_client.py              # FedEx OAuth 2.0
│   ├── hedera_client.py             # REST API client (no SDK)
│   ├── hcs10_message.py             # HCS-10 protocol
│   ├── config.py                    # Centralized config
│   └── error_handling.py            # Retry + backoff
├── api/
│   ├── app.py                       # Flask REST API + all endpoints
│   ├── auth.py                      # API key auth + roles
│   └── fastapi_app.py               # FastAPI alternative
├── database/
│   ├── database.py                  # SQLAlchemy setup
│   ├── models.py                    # ORM models
│   ├── services.py                  # Business logic
│   ├── api_keys.py                  # API key model
│   └── db_manager.py
├── woocommerce/webhooks/
│   └── order_webhook.py             # HMAC-verified webhook
├── hol_registry/
│   └── registry.py                  # Agent registration + discovery
├── utils/
│   └── api_keys.py                  # Key generation + hashing
├── websocket/
│   └── routes.py                    # Real-time WebSocket updates
├── tests/                           # 30 test files
├── truthforge_frontend/
│   └── truthforge-logistics-verified-main/
│       ├── src/
│       │   ├── pages/               # 6 dashboard pages
│       │   ├── components/          # UI components
│       │   ├── contexts/            # Auth, MockMode, Theme, Wallet
│       │   ├── assets/              # truthforge-logo.png (real logo)
│       │   └── lib/
│       │       ├── api-client.ts    # Central API config
│       │       └── mock-data.ts     # Mock data definitions
│       ├── public/
│       │   └── favicon.png          # Real TruthForge logo
│       ├── .env.production          # Vercel production env vars
│       └── vite.config.ts           # Dev proxy config
├── assets/
│   └── truthforge-logo.png          # Real logo (used in README)
├── main.py                          # WSGI entry + system bootstrap
├── Procfile                         # gunicorn main:app
├── runtime.txt                      # python-3.11.x
├── requirements.txt                 # Python deps (no Java SDK)
├── nixpacks.toml                    # Railway build config
└── .env.example                     # Config template
```

---

## Hackathon Tracks

| Track | Qualification |
|---|---|
| AI & Agentic Track | 5 autonomous HOL-registered agents with HCS-10 messaging |
| HOL Bounty | Full HOL agent registration, discovery, consensus anchoring |
| Real-World Impact | Live WooCommerce store (`a-thi.online`) + FedEx sandbox integration |

---

## Pending Manual Actions

| Action | Who |
|---|---|
| Trigger Vercel redeploy to pick up favicon + logo fixes | You |
| Verify Railway deployment is healthy (check logs) | You |

---

*Working tree clean. All changes committed and pushed to `origin/main`.*
