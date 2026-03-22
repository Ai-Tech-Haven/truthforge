# 🔐 TruthForge API Keys & Port Filter

## Quick Overview

This implementation adds enterprise-grade API key authentication and port filtering to TruthForge.

## 🎯 What's New

### 1. Role-Based API Keys
- **Port Authority**: Access verification proofs
- **Enterprise**: Submit and track shipments  
- **Admin**: Full system access

### 2. Secure Authentication
- SHA-256 hashed storage
- Bearer token authentication
- Usage tracking and auditing

### 3. Port Filter Dashboard
- Filter shipments by destination port
- Real-time filtering
- Clean UI integration

## 🚀 One-Command Setup

```bash
RUN_API_KEYS_SETUP.bat
```

This will:
1. ✅ Initialize database
2. ✅ Run all tests
3. ✅ Generate test keys
4. ✅ Display keys for testing

## 📖 Quick Examples

### Generate API Key
```bash
curl -X POST http://localhost:5000/api/v1/keys/generate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Port of Los Angeles",
    "role": "port_authority"
  }'
```

### Get Shipment Proof
```bash
curl http://localhost:5000/api/v1/proof/SHP-8821A \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Use Port Filter
Open dashboard → Select port from dropdown → View filtered shipments

## 📁 Project Structure

```
TruthForge/
├── database/
│   └── api_keys.py          # Database model
├── utils/
│   └── api_keys.py          # Key utilities
├── api/
│   └── auth.py              # Auth decorators
├── init_database.py         # DB setup
├── test_api_keys.py         # Test suite
├── RUN_API_KEYS_SETUP.bat   # One-click setup
└── API_KEYS_PORT_FILTER_IMPLEMENTATION.md  # Full docs
```

## 🔒 Security Features

- ✅ Hashed key storage (SHA-256)
- ✅ Role-based access control
- ✅ Usage tracking
- ✅ Key revocation support
- ✅ Audit logging ready

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `QUICK_START_API_KEYS.md` | 3-step quick start |
| `API_KEYS_PORT_FILTER_IMPLEMENTATION.md` | Complete guide |
| `IMPLEMENTATION_SUMMARY.md` | What was built |
| `API_KEYS_README.md` | This file |

## 🧪 Testing

All tests pass with zero errors:
- ✅ Database initialization
- ✅ Key generation (all roles)
- ✅ Key validation
- ✅ Role-based access
- ✅ Frontend integration

## 💡 Use Cases

### Port Authority
```python
# Get proof for incoming shipment
proof = get_proof("SHP-8821A", port_authority_key)
verify_hedera_consensus(proof['hedera_references'])
```

### Enterprise
```python
# Submit verification request
result = verify_shipment("SHP-8821A", enterprise_key)
track_status(result['request_id'])
```

### Admin
```python
# Generate keys for new users
key = create_api_key("New Port", "port_authority")
send_to_user(key)
```

## 🎨 Frontend Features

- Port filter dropdown with icon
- Real-time shipment filtering
- Maintains existing design
- Responsive layout

## ⚡ Performance

- Indexed database queries
- Efficient key validation
- Minimal overhead
- Production-ready

## 🔧 Troubleshooting

**Database error?**
```bash
python init_database.py
```

**Import error?**
```bash
pip install -r requirements.txt
```

**Test failed?**
```bash
python test_api_keys.py
```

## 🌟 Next Steps

1. Run setup: `RUN_API_KEYS_SETUP.bat`
2. Save generated keys
3. Start server: `python main.py`
4. Test endpoints
5. Try port filter on dashboard

## 📞 Support

Check these files for help:
- Test output: Run `test_api_keys.py`
- Logs: `truthforge.log`
- Docs: `API_KEYS_PORT_FILTER_IMPLEMENTATION.md`

---

**Built for TruthForge** | Secure • Scalable • Production-Ready
