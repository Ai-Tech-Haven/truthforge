# TruthForge Database Setup Guide

## Quick Start

### 1. Verify Database Configuration

Your `.env` file is already configured with PostgreSQL:

```bash
DATABASE_URL=postgresql://postgres.svwujphciukwvwsdavqf:PHkOgTyOWwf34gi@aws-1-eu-west-1.pooler.supabase.com:5432/postgres
DB_TYPE=postgresql
```

### 2. Test Database Connection

```bash
python test_db_connection.py
```

This will verify your database credentials and connection.

### 3. Initialize Database Tables

```bash
python init_database.py
```

This creates all necessary tables:
- `verification_requests` - Stores verification requests
- `agents` - Registered agent information
- `verification_logs` - Audit logs for all operations
- `shipment_data` - Shipment tracking information

## Database Operations

### Using Database Sessions

#### Method 1: Direct Session (Manual Management)
```python
from database import db_session
from database.models import VerificationRequest

# Create
request = VerificationRequest(
    request_id="req-123",
    user_id="user-456",
    status="pending"
)
db_session.add(request)
db_session.commit()

# Query
requests = db_session.query(VerificationRequest).filter_by(status="pending").all()

# Update
request.status = "completed"
db_session.commit()

# Always close when done
db_session.close()
```

#### Method 2: Context Manager (Recommended)
```python
from database.db_manager import DatabaseManager
from database.models import VerificationRequest

with DatabaseManager.session_scope() as session:
    request = VerificationRequest(
        request_id="req-123",
        user_id="user-456",
        status="pending"
    )
    session.add(request)
    # Automatically commits on success, rolls back on error
```

#### Method 3: Decorator
```python
from database.db_manager import with_db_session
from database.models import VerificationRequest

@with_db_session
def create_verification(session, request_id, user_id):
    request = VerificationRequest(
        request_id=request_id,
        user_id=user_id,
        status="pending"
    )
    session.add(request)
    return request

# Usage
result = create_verification("req-123", "user-456")
```

## Database Models

### VerificationRequest
Stores verification requests and results.

**Fields:**
- `request_id` (str) - Unique request identifier
- `user_id` (str) - User who made the request
- `image_url` (str) - URL to image being verified
- `document_url` (str) - URL to document being verified
- `shipment_id` (str) - Associated shipment ID
- `status` (str) - Request status (pending, processing, completed, failed)
- `authenticity_score` (float) - Verification score (0-100)
- `analysis_results` (JSON) - Detailed analysis results
- `hcs_transaction_id` (str) - Hedera transaction ID
- `created_at` (datetime) - Creation timestamp
- `updated_at` (datetime) - Last update timestamp

### Agent
Stores registered agent information.

**Fields:**
- `agent_id` (str) - Unique agent identifier
- `uaid` (str) - Universal Agent ID from HOL
- `hcs_topic_id` (str) - HCS topic for agent messaging
- `status` (str) - Agent status (active, inactive)
- `last_heartbeat` (datetime) - Last heartbeat timestamp
- `created_at` (datetime) - Registration timestamp

### VerificationLog
Audit trail for all verification operations.

**Fields:**
- `request_id` (str) - Associated request ID
- `agent_id` (str) - Agent that performed the action
- `action` (str) - Action performed
- `details` (JSON) - Action details
- `timestamp` (datetime) - Action timestamp

### ShipmentData
Stores shipment tracking information.

**Fields:**
- `shipment_id` (str) - Unique shipment identifier
- `carrier` (str) - Carrier name (FedEx, UPS, etc.)
- `tracking_number` (str) - Tracking number
- `origin` (str) - Origin location
- `destination` (str) - Destination location
- `status` (str) - Shipment status
- `estimated_delivery` (datetime) - Estimated delivery date
- `shipment_data` (JSON) - Full shipment data
- `created_at` (datetime) - Creation timestamp
- `updated_at` (datetime) - Last update timestamp

## Health Checks

```python
from database.db_manager import DatabaseManager

# Check database health
health = DatabaseManager.health_check()
print(health)
# Output: {'status': 'healthy', 'connected': True, 'stats': {...}}
```

## Troubleshooting

### Connection Issues

**Error: "could not connect to server"**
- Verify DATABASE_URL in `.env` is correct
- Check network connectivity to Supabase
- Ensure Supabase project is active

**Error: "password authentication failed"**
- Verify password in DATABASE_URL is correct
- Check if password contains special characters that need URL encoding

**Error: "SSL connection required"**
- Supabase requires SSL by default
- Add `?sslmode=require` to DATABASE_URL if needed

### Performance Issues

**Slow queries:**
- Check connection pool settings (DB_POOL_SIZE, DB_MAX_OVERFLOW)
- Monitor active connections
- Consider adding indexes to frequently queried fields

**Connection pool exhausted:**
- Increase DB_POOL_SIZE in `.env`
- Ensure sessions are properly closed
- Use context managers to auto-close sessions

## Migration from SQLite

If you were using SQLite and want to migrate to PostgreSQL:

1. Export data from SQLite:
```python
from database import db_session
from database.models import VerificationRequest
import json

# Export to JSON
requests = db_session.query(VerificationRequest).all()
data = [{'request_id': r.request_id, ...} for r in requests]
with open('export.json', 'w') as f:
    json.dump(data, f)
```

2. Switch to PostgreSQL in `.env`:
```bash
DB_TYPE=postgresql
DATABASE_URL=postgresql://...
```

3. Initialize PostgreSQL tables:
```bash
python init_database.py
```

4. Import data:
```python
import json
from database import db_session
from database.models import VerificationRequest

with open('export.json', 'r') as f:
    data = json.load(f)

for item in data:
    request = VerificationRequest(**item)
    db_session.add(request)
db_session.commit()
```

## Best Practices

1. **Always use context managers** for database operations
2. **Close sessions** when done to prevent connection leaks
3. **Use transactions** for multi-step operations
4. **Handle exceptions** properly with try/except blocks
5. **Monitor connection pool** usage in production
6. **Use indexes** on frequently queried fields
7. **Backup regularly** - Supabase provides automatic backups
8. **Test queries** before deploying to production

## Support

For database-related issues:
1. Check logs for detailed error messages
2. Run `python test_db_connection.py` to verify connectivity
3. Check Supabase dashboard for connection statistics
4. Review PostgreSQL logs in Supabase
