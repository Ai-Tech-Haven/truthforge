# Quick Start: API Keys & Port Filter

## 3-Step Setup

### Step 1: Initialize Database
```bash
# Windows
init_database.bat

# Or direct Python
python init_database.py
```

### Step 2: Run Tests & Generate Keys
```bash
# Windows
test_api_keys.bat

# Or direct Python
python test_api_keys.py
```

This generates test keys for all roles. Save the output!

### Step 3: Test API Endpoints
```bash
# Start server
python main.py

# Generate a new key
curl -X POST http://localhost:5000/api/v1/keys/generate \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Key", "role": "port_authority"}'

# Get shipment proof
curl http://localhost:5000/api/v1/proof/SHP-8821A \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Port Filter Usage

The dashboard now has a port filter dropdown above the clearance queue.
Select a port to filter shipments by destination.

## Available Roles

- `port_authority`: Access proof data
- `enterprise`: Submit verifications
- `admin`: Full access

## Files Created

- Database: `database/api_keys.py`
- Utils: `utils/api_keys.py`
- Auth: `api/auth.py`
- Tests: `test_api_keys.py`
- Docs: `API_KEYS_PORT_FILTER_IMPLEMENTATION.md`

See full documentation in `API_KEYS_PORT_FILTER_IMPLEMENTATION.md`
