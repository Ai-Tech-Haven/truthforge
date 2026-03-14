# TruthForge WebSocket Implementation Guide

## Overview

TruthForge now includes real-time WebSocket support for live tracking, metrics, and dashboard updates. The system runs two servers:

1. **Flask Server** (Port 5000) - REST API for verification requests
2. **FastAPI Server** (Port 8000) - WebSocket endpoints for real-time updates

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TruthForge System                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐              ┌──────────────┐        │
│  │ Flask Server │              │FastAPI Server│        │
│  │  (Port 5000) │              │  (Port 8000) │        │
│  │              │              │              │        │
│  │  REST API    │              │  WebSockets  │        │
│  └──────────────┘              └──────────────┘        │
│         │                              │                │
│         └──────────────┬───────────────┘                │
│                        │                                │
│              ┌─────────▼─────────┐                     │
│              │ Connection Manager │                     │
│              │   (Rooms & Broadcast)                    │
│              └─────────┬─────────┘                     │
│                        │                                │
│              ┌─────────▼─────────┐                     │
│              │  Tracking Agent   │                     │
│              │ (Real-time Updates)                     │
│              └───────────────────┘                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start the Servers

```bash
# Start both Flask and FastAPI servers
python run_servers.py
```

This will start:
- Flask REST API on `http://localhost:5000`
- FastAPI WebSocket on `ws://localhost:8000`

### 2. Test WebSocket Connection

```bash
# Run WebSocket tests
python test_websocket.py
```

### 3. Connect from Frontend

```javascript
// Connect to tracking WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/tracking/SHIP123');

ws.onopen = () => {
    console.log('Connected to tracking');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Position update:', data);
};
```

## WebSocket Endpoints

### 1. Shipment Tracking

**Endpoint**: `/ws/tracking/{shipment_id}`

**Purpose**: Real-time shipment position updates

**Messages Sent by Server**:
```json
{
    "type": "initial",
    "data": {
        "shipment_id": "SHIP123",
        "position": {"lat": 1.3521, "lng": 103.8198},
        "status": "in_transit",
        "eta": "2026-03-15T14:30:00Z"
    }
}

{
    "type": "position_update",
    "shipment_id": "SHIP123",
    "timestamp": "2026-01-09T10:30:00Z",
    "position": {
        "lat": 1.3521,
        "lng": 103.8198,
        "speed": 20.5,
        "heading": 45.0
    },
    "eta": "2026-03-15T14:30:00Z",
    "status": "in_transit"
}
```

**Messages Sent by Client**:
```json
// Ping
{"type": "ping"}

// Request immediate update
{"type": "request_update"}

// Subscribe to events
{
    "type": "subscribe_events",
    "events": ["status_change", "eta_update"]
}
```

### 2. Port Clearance Queue

**Endpoint**: `/ws/port/{port_id}/clearance`

**Purpose**: Real-time port clearance queue updates

**Messages Sent by Server**:
```json
{
    "type": "initial",
    "data": {
        "port_id": "USLAX",
        "queue_length": 15,
        "average_clearance_time": 45,
        "shipments": [...]
    }
}
```

### 3. Global Dashboard

**Endpoint**: `/ws/dashboard/global`

**Purpose**: Aggregated real-time updates for all shipments

**Messages Sent by Client**:
```json
// Subscribe to topics
{
    "type": "subscribe",
    "topics": ["shipment:SHIP123", "metric:clearance_time"]
}

// Unsubscribe from topics
{
    "type": "unsubscribe",
    "topics": ["shipment:SHIP123"]
}
```

### 4. Metrics Streaming

**Endpoint**: `/ws/metrics/{metric_type}`

**Metric Types**:
- `clearance_time` - Average port clearance time
- `shipment_volume` - Live shipment volume
- `risk_score` - Global risk score

**Messages Sent by Server**:
```json
{
    "type": "initial",
    "metric_type": "clearance_time",
    "value": 42.5
}
```

## Connection Manager

The Connection Manager handles all WebSocket connections and provides:

### Features

1. **Connection Management**
   - Accept new connections
   - Handle disconnections
   - Track connection metadata

2. **Room-Based Broadcasting**
   - Join/leave rooms
   - Broadcast to specific rooms
   - User-specific messaging

3. **Statistics**
   - Total connections
   - Active rooms
   - Connected users

### Usage

```python
from websocket.manager import manager

# Connect client
await manager.connect(websocket, user_id="user123")

# Join room
await manager.join_room(websocket, "shipment:SHIP123")

# Broadcast to room
await manager.broadcast_to_room("shipment:SHIP123", {
    "type": "update",
    "data": {...}
})

# Get statistics
stats = manager.get_stats()
```

## Tracking Agent

The Tracking Agent provides real-time position updates for shipments.

### Features

1. **Real-Time Tracking**
   - Position updates every 5 seconds
   - ETA calculations
   - Status determination

2. **Mock Mode**
   - Simulated movement along routes
   - Realistic position interpolation
   - Random variations for testing

3. **Live Mode**
   - Integration with carrier APIs
   - Real position data
   - Actual ETA calculations

### Usage

```python
from agents.tracking_agent import TrackingAgent

# Initialize agent
agent = TrackingAgent(config=config)

# Start tracking
await agent.start_tracking("SHIP123", db_session)

# Stop tracking
await agent.stop_tracking("SHIP123")

# Get current position
position = agent.get_current_position("SHIP123")
```

## Configuration

### Environment Variables

```bash
# WebSocket Configuration
WS_PORT=8000
WS_HOST=0.0.0.0

# Flask Configuration
PORT=5000

# Mode
MOCK_MODE=true  # or false for live mode
```

### Mock Mode vs Live Mode

**Mock Mode** (`MOCK_MODE=true`):
- Simulated position updates
- No carrier API calls
- Perfect for development and testing
- No external dependencies

**Live Mode** (`MOCK_MODE=false`):
- Real carrier API integration
- Actual position data
- Real ETA calculations
- Requires carrier API credentials

## Testing

### Manual Testing

```bash
# Using wscat
wscat -c ws://localhost:8000/ws/tracking/SHIP123

# Send ping
> {"type": "ping"}

# Request update
> {"type": "request_update"}
```

### Automated Testing

```bash
# Run WebSocket tests
python test_websocket.py
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test (create locustfile.py first)
locust -f locustfile.py
```

## Frontend Integration

### React Example

```typescript
import { useEffect, useState } from 'react';

function useShipmentTracking(shipmentId: string) {
    const [position, setPosition] = useState(null);
    const [ws, setWs] = useState(null);
    
    useEffect(() => {
        const websocket = new WebSocket(
            `ws://localhost:8000/ws/tracking/${shipmentId}`
        );
        
        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'position_update') {
                setPosition(data.position);
            }
        };
        
        setWs(websocket);
        
        return () => websocket.close();
    }, [shipmentId]);
    
    return { position, ws };
}
```

### Vue Example

```javascript
export default {
    data() {
        return {
            position: null,
            ws: null
        }
    },
    mounted() {
        this.ws = new WebSocket(
            `ws://localhost:8000/ws/tracking/${this.shipmentId}`
        );
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'position_update') {
                this.position = data.position;
            }
        };
    },
    beforeUnmount() {
        if (this.ws) {
            this.ws.close();
        }
    }
}
```

## Troubleshooting

### Connection Refused

**Problem**: Cannot connect to WebSocket

**Solution**:
1. Ensure server is running: `python run_servers.py`
2. Check port is not in use: `netstat -an | findstr 8000`
3. Verify firewall settings

### No Updates Received

**Problem**: Connected but no position updates

**Solution**:
1. Check tracking agent is started
2. Verify shipment ID is correct
3. Check server logs for errors

### High Latency

**Problem**: Slow update delivery

**Solution**:
1. Check network connection
2. Reduce update frequency
3. Use connection pooling
4. Enable compression

## Best Practices

1. **Connection Management**
   - Always handle disconnections gracefully
   - Implement reconnection logic
   - Use heartbeat/ping messages

2. **Error Handling**
   - Catch and log all errors
   - Provide user feedback
   - Implement fallback mechanisms

3. **Performance**
   - Limit update frequency
   - Use message batching
   - Implement client-side caching

4. **Security**
   - Validate all messages
   - Implement authentication
   - Use WSS in production

## Production Deployment

### Using Docker

```yaml
# docker-compose.yml
version: '3.8'

services:
  truthforge:
    build: .
    ports:
      - "5000:5000"
      - "8000:8000"
    environment:
      - MOCK_MODE=false
      - DATABASE_URL=${DATABASE_URL}
    restart: always
```

### Using Nginx

```nginx
# nginx.conf
upstream websocket {
    server localhost:8000;
}

server {
    listen 80;
    
    location /ws/ {
        proxy_pass http://websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Support

For issues or questions:
1. Check logs: `truthforge.log`
2. Run diagnostics: `python check_status.py`
3. Test WebSocket: `python test_websocket.py`

---

**Status**: Production Ready
**Version**: 2.0.0
**Last Updated**: 2025-01-09
