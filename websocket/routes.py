"""
WebSocket routes for real-time tracking and updates
"""
import logging
import json
import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter()

# Connection managers for different channels
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        logger.info(f"Client connected to channel: {channel}")
    
    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        logger.info(f"Client disconnected from channel: {channel}")
    
    async def broadcast(self, message: dict, channel: str):
        if channel in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn, channel)

manager = ConnectionManager()


@router.websocket("/ws/tracking/{shipment_id}")
async def websocket_tracking(websocket: WebSocket, shipment_id: str):
    """Real-time shipment tracking updates"""
    channel = f"tracking_{shipment_id}"
    await manager.connect(websocket, channel)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "shipment_id": shipment_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Echo back for now (can add custom handling)
            await websocket.send_json({
                "type": "ack",
                "message": "received",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, channel)


@router.websocket("/ws/port/{port_id}/clearance")
async def websocket_port_clearance(websocket: WebSocket, port_id: str):
    """Real-time port clearance updates"""
    channel = f"port_{port_id}"
    await manager.connect(websocket, channel)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "port_id": port_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "ack",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, channel)


@router.websocket("/ws/dashboard/global")
async def websocket_global_dashboard(websocket: WebSocket):
    """Real-time global dashboard updates"""
    channel = "global_dashboard"
    await manager.connect(websocket, channel)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "channel": "global_dashboard",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "ack",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, channel)


@router.websocket("/ws/metrics/{metric_type}")
async def websocket_metrics(websocket: WebSocket, metric_type: str):
    """Real-time metrics updates"""
    channel = f"metrics_{metric_type}"
    await manager.connect(websocket, channel)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "metric_type": metric_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "ack",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, channel)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics"""
    stats = {
        "active_channels": len(manager.active_connections),
        "total_connections": sum(len(conns) for conns in manager.active_connections.values()),
        "channels": {
            channel: len(conns) 
            for channel, conns in manager.active_connections.items()
        }
    }
    return stats


# Broadcast helper function for agents to push updates
async def broadcast_shipment_update(shipment_id: str, update_data: dict):
    """Broadcast shipment update to all connected clients"""
    channel = f"tracking_{shipment_id}"
    message = {
        "type": "shipment_update",
        "shipment_id": shipment_id,
        "data": update_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast(message, channel)


async def broadcast_port_update(port_id: str, update_data: dict):
    """Broadcast port clearance update"""
    channel = f"port_{port_id}"
    message = {
        "type": "port_update",
        "port_id": port_id,
        "data": update_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast(message, channel)


async def broadcast_dashboard_update(update_data: dict):
    """Broadcast global dashboard update"""
    message = {
        "type": "dashboard_update",
        "data": update_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast(message, "global_dashboard")


async def broadcast_metrics_update(metric_type: str, update_data: dict):
    """Broadcast metrics update"""
    channel = f"metrics_{metric_type}"
    message = {
        "type": "metrics_update",
        "metric_type": metric_type,
        "data": update_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast(message, channel)
