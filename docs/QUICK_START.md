# TruthForge Quick Start Guide

## ✓ Setup Complete

Your TruthForge environment is configured and ready to use!

## What's Working

- ✓ Hedera testnet connection configured
- ✓ PostgreSQL database connected (Supabase)
- ✓ Database tables created
- ✓ 5 AI agents registered on HOL
- ✓ HCS topics configured
- ✓ All dependencies installed

## Quick Commands

### Database Operations

```bash
# Test database connection
python test_db_connection.py

# Initialize database (already done)
python init_database.py

# Test read/write operations
python test_db_operations.py
```

### Hedera Operations

```bash
# Test Hedera connection
python test_hedera_connection.py

# Create new HCS topic (if needed)
python create_hcs_topic.py
```

### Start the System

```bash
# Start the API server
python api/app.py
```

The API will be available at `http://localhost:5000`

## Your Configuration

### Hedera
- Account ID: `0.0.7974354`
- Network: `testnet`
- HCS Topic: `0.0.8109600`
- Mode: `Production` (MOCK_MODE=false)

### Database
- Type: `PostgreSQL`
- Host: `aws-1-eu-west-1.pooler.supabase.com`
- Status: `Connected ✓`
- Tables: 4 tables created

### Registered Agents
1. **truthforge-orch-001** - Orchestrator (Topic: 0.0.8161244)
2. **truthforge-verify-001** - Document Verifier (Topic: 0.0.8161247)
3. **truthforge-carrier-001** - Carrier Adapter (Topic: 0.0.8161248)
4. **truthforge-registry-001** - Registry Agent (Topic: 0.0.8161249)
5. **truthforge-evidence-001** - Evidence & Settlement (Topic: 0.0.8161250)

## Project Structure

```
TruthForge/
├── agents/                    # AI agent implementations
│   ├── orchestrator.py       # Main coordinator
│   ├── document_verifier.py  # Document validation
│   ├── carrier_adapter.py    # Shipment integration
│   ├── registry_agent.py     # Agent discovery
│   └── evidence_settlement_agent.py  # Consensus & audit
├── database/                  # Database layer
│   ├── database.py           # Core database setup
│   ├── models.py             # Data models
│   └── db_manager.py         # Database utilities
├── api/                       # REST API
│   ├── app.py                # Flask application
│   └── routes.py             # API endpoints
├── frontend/                  # Web interface
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── tests/                     # Test suite
├── .env                       # Configuration (DO NOT COMMIT)
└── requirements.txt           # Python dependencies
```

## Common Tasks

### 1. Create a Verification Request

```python
from database.db_manager import DatabaseManager
from database.models import VerificationRequest

with DatabaseManager.session_scope() as session:
    request = VerificationRequest(
        request_id="req-001",
        user_id="user-123",
        image_url="https://example.com/image.jpg",
        status="pending"
    )
    session.add(request)
```

### 2. Submit to Hedera Consensus

```python
from agents.evidence_settlement_agent import EvidenceSettlementAgent
from agents.config import Config
from agents.hedera_client import HederaClient

config = Config()
hedera_client = HederaClient(config)

agent = EvidenceSettlementAgent(
    agent_id="truthforge-evidence-001",
    capabilities=["consensus", "audit"],
    hcs_topic_id=config.agent_05_hcs_topic,
    config=config,
    hedera_client=hedera_client
)

# Submit verification data
verification_data = {
    "verification_id": "ver-001",
    "authenticity_score": 95.5,
    "status": "verified"
}

transaction_id = agent.submit_consensus(verification_data)
print(f"Submitted to HCS: {transaction_id}")
```

### 3. Query Verification History

```python
from database import db_session
from database.models import VerificationRequest

# Get all pending requests
pending = db_session.query(VerificationRequest)\
    .filter_by(status="pending")\
    .all()

for req in pending:
    print(f"{req.request_id}: {req.status}")
```

## API Endpoints

Once the API server is running:

- `POST /api/verify` - Submit verification request
- `GET /api/status/{request_id}` - Check verification status
- `GET /api/history` - Get verification history
- `GET /api/agents` - List registered agents
- `GET /api/health` - System health check

## Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=. --cov-report=html
```

## Development Mode vs Production Mode

### Current: Production Mode
- Real Hedera blockchain transactions
- Actual HCS timestamping (costs HBAR)
- Live database operations

### Switch to Development Mode
Set in `.env`:
```bash
MOCK_MODE=true
```

Benefits:
- No blockchain costs
- Simulated transactions
- Faster testing

## Monitoring

### Database Health
```python
from database.db_manager import DatabaseManager

health = DatabaseManager.health_check()
print(health)
```

### Agent Status
```python
from database import db_session
from database.models import Agent

agents = db_session.query(Agent).all()
for agent in agents:
    print(f"{agent.agent_id}: {agent.status}")
```

### Transaction Costs
```python
from database import db_session
from database.models import VerificationLog

costs = db_session.query(VerificationLog)\
    .filter_by(action="transaction_cost")\
    .all()

total = sum(float(log.details.get('metric_value', 0)) for log in costs)
print(f"Total HBAR spent: {total}")
```

## Troubleshooting

### Database Issues
```bash
python test_db_connection.py
```

### Hedera Issues
```bash
python test_hedera_connection.py
```

### Check Logs
Logs are written to console with INFO level by default.
Change in `.env`:
```bash
LOG_LEVEL=DEBUG
```

## Next Steps

1. **Start the API server**: `python api/app.py`
2. **Open the frontend**: Open `frontend/index.html` in browser
3. **Submit a test verification**: Use the web interface or API
4. **Monitor the database**: Check verification logs
5. **View on Hedera**: Check transactions on HashScan

## Resources

- **Database Guide**: `DATABASE_GUIDE.md`
- **Setup Complete**: `DATABASE_SETUP_COMPLETE.md`
- **Project README**: `README.md`
- **Hedera Docs**: https://docs.hedera.com/
- **HOL Docs**: https://docs.hedera.com/hol/

## Support

For issues or questions:
1. Check the relevant guide (DATABASE_GUIDE.md, README.md)
2. Run the test scripts to diagnose issues
3. Check Hedera testnet status
4. Verify Supabase project is active

---

**Status**: Ready to use ✓
**Last Updated**: 2025-01-09
**Environment**: Production (testnet)
