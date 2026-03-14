# TruthForge Setup Guide

## Quick Start (5 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
The `.env` file is already configured with:
- ✅ Hedera testnet credentials
- ✅ All 5 HOL agent registrations
- ✅ HCS topic IDs
- ✅ Database connection (PostgreSQL + SQLite fallback)

**Important**: Set your operating mode:
- For **LIVE MODE**: `MOCK_MODE=false`
- For **MOCK MODE**: `MOCK_MODE=true`

### Step 3: Initialize Database
```bash
python init_database.py
```

This creates all required tables in your database.

### Step 4: Start the System
```bash
# Option 1: Use the startup script
start_production.bat

# Option 2: Run directly
python main.py
```

### Step 5: Verify System
```bash
# In another terminal
python test_production.py
```

## System URLs

- **API Server**: http://localhost:5000
- **WebSocket**: ws://localhost:8000
- **Health Check**: http://localhost:5000/health
- **System Status**: http://localhost:5000/api/status/system

## Operating Modes

### Mock Mode (Development/Demo)
- Uses simulated data
- No blockchain transactions
- No HBAR costs
- Perfect for development and demos

**Enable**: Set `MOCK_MODE=true` in `.env`

### Live Mode (Production)
- Real Hedera blockchain integration
- PostgreSQL database
- Actual HCS message submissions
- Transaction costs in HBAR

**Enable**: Set `MOCK_MODE=false` in `.env`

## Architecture

```
TruthForge System
├── 5 AI Agents (HOL Registered)
│   ├── Orchestrator Agent
│   ├── Verification & Compliance Agent
│   ├── Carrier Adapter Agent
│   ├── Registry & Discovery Agent
│   └── Evidence & Settlement Agent
├── Hedera Integration
│   ├── HCS Topics (5 topics)
│   ├── Transaction Management
│   └── Consensus Timestamping
├── Database Layer
│   ├── PostgreSQL (Primary)
│   └── SQLite (Fallback)
└── API Layer
    ├── REST API (Flask)
    └── WebSocket (FastAPI)
```

## Database Tables

1. **verifications** - Verification requests and results
2. **agent_status** - Agent health and metrics
3. **shipments** - Shipment tracking data
4. **port_trust_receipts** - Port clearance receipts
5. **audit_trails** - Compliance audit trails
6. **dashboard_metrics** - Operational metrics
7. **api_keys** - API authentication

## API Endpoints

### Core Endpoints
- `POST /api/verify` - Submit verification request
- `GET /api/status/<request_id>` - Get verification status
- `GET /api/agents` - List all agents
- `GET /api/dashboard/metrics` - Get operational metrics
- `GET /api/clearance/queue` - Get clearance queue
- `GET /api/status/system` - System health check
- `GET /api/mode` - Get current operating mode

### WebSocket Endpoints
- `/ws/tracking/{shipment_id}` - Real-time tracking
- `/ws/port/{port_id}/clearance` - Port updates
- `/ws/dashboard/global` - Dashboard updates
- `/ws/metrics/{metric_type}` - Metrics updates

## Troubleshooting

### Database Connection Failed
1. Check `DATABASE_URL` in `.env`
2. Ensure PostgreSQL is running
3. System will fallback to SQLite automatically

### Agents Not Registering
1. Check Hedera credentials in `.env`
2. Verify HCS topic IDs are correct
3. Check network connectivity
4. Try mock mode first: `MOCK_MODE=true`

### API Errors
1. Check if server is running: `curl http://localhost:5000/health`
2. View logs in `truthforge.log`
3. Run test suite: `python test_production.py`

### Mode Toggle Not Working
1. Restart the system after changing `MOCK_MODE`
2. Check `/api/mode` endpoint to verify current mode
3. Clear any cached data

## Configuration Files

### `.env` - Main Configuration
Contains all credentials and settings:
- Hedera account and private key
- HCS topic IDs
- HOL agent UAIDs
- Database connection
- Mode toggle

### `database/database.py` - Database Setup
- Connection pooling
- PostgreSQL/SQLite support
- Automatic fallback

### `main.py` - System Entry Point
- Agent initialization
- HOL registration
- Server startup

### `api/app.py` - API Routes
- Live/mock mode handling
- Database integration
- Error handling

## Development Workflow

### 1. Development (Mock Mode)
```bash
# Set mock mode
# In .env: MOCK_MODE=true

# Start system
python main.py

# Test endpoints
curl http://localhost:5000/api/agents
```

### 2. Testing (Live Mode)
```bash
# Set live mode
# In .env: MOCK_MODE=false

# Initialize database
python init_database.py

# Start system
python main.py

# Run tests
python test_production.py
```

### 3. Production Deployment
```bash
# Verify configuration
cat .env

# Run migrations
python migrate_database.py

# Start production
start_production.bat
```

## Adding API Keys (Optional)

### WooCommerce Integration
Add to `.env`:
```
WOOCOMMERCE_STORE_URL=https://your-store.com
WOOCOMMERCE_CONSUMER_KEY=ck_your_key
WOOCOMMERCE_CONSUMER_SECRET=cs_your_secret
WOOCOMMERCE_ENABLED=true
```

### FedEx Integration
Add to `.env`:
```
FEDEX_API_KEY=your_api_key
FEDEX_SECRET_KEY=your_secret_key
FEDEX_ACCOUNT_NUMBER=your_account_number
```

## Monitoring

### Check System Health
```bash
curl http://localhost:5000/api/status/system
```

### Check Database
```bash
curl http://localhost:5000/api/health/db
```

### Check Agents
```bash
curl http://localhost:5000/api/agents
```

### View Logs
```bash
# Windows
type truthforge.log

# Linux/Mac
tail -f truthforge.log
```

## Performance Tips

1. **Database**: Use PostgreSQL for production (better performance)
2. **Connection Pooling**: Already configured (10 connections)
3. **Caching**: Agent data cached with TTL
4. **Async Operations**: WebSocket for real-time updates
5. **Error Handling**: Automatic fallback to mock data

## Security Notes

1. **Never commit `.env`** - Contains sensitive credentials
2. **Use API authentication** - Set `API_AUTH_TOKEN` in `.env`
3. **Secure database** - Use strong passwords
4. **HTTPS in production** - Use reverse proxy (nginx/Apache)
5. **Rate limiting** - Implement for production

## Support

### Documentation
- `PRODUCTION_READY.md` - Production checklist
- `API_KEYS_README.md` - API key management
- `DATABASE_GUIDE.md` - Database details

### Logs
- `truthforge.log` - Application logs
- Console output - Real-time status

### Testing
- `test_production.py` - Production test suite
- `tests/` - Unit and integration tests

## Next Steps

1. ✅ System is ready for hackathon submission
2. ✅ Both mock and live modes working
3. ✅ All 5 agents registered
4. ✅ Database configured
5. ✅ API endpoints functional
6. ✅ WebSocket support enabled

**You're ready to go! 🚀**
