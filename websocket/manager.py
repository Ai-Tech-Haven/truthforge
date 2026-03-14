"""
WebSocket Connection Manager for TruthForge

Handles WebSocket connections, broadcasting, and room management
for real-time tracking and updates.
"""
import asyncio
import json
import logging
from typing import Dict, Set, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        # Active connections
        self.active_connections: Set[Any] = set()
        # Room-based connections (e.g., by shipment ID)
        self.rooms: Dict[str, Set[Any]] = {}
        # User-specific connections
        self.user_connections: Dict[str, Any] = {}
        # Connection metadata
        self.connection_metadata: Dict[Any, Dict[str, Any]] = {}
        
    async def connect(self, websocket: Any, user_id: Optional[str] = None):
        """Accept and store new connection"""
        try:
            await websocket.accept()
            self.active_connections.add(websocket)
            
            # Store metadata
            self.connection_metadata[websocket] = {
                'connected_at': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'rooms': set()
            }
            
            if user_id:
                self.user_connections[user_id] = websocket
            
            logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
            
            # Send welcome message
            await websocket.send_json({
                'type': 'connected',
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'Connected to TruthForge real-time updates'
            })
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
        
    def disconnect(self, websocket: Any):
        """Remove closed connection"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            # Remove from all rooms
            if websocket in self.connection_metadata:
                rooms = self.connection_metadata[websocket].get('rooms', set())
                for room in rooms:
                    if room in self.rooms:
                        self.rooms[room].discard(websocket)
                        if not self.rooms[room]:
                            del self.rooms[room]
                
                # Remove from user connections
                user_id = self.connection_metadata[websocket].get('user_id')
                if user_id and user_id in self.user_connections:
                    del self.user_connections[user_id]
                
                del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
            
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
        
    async def join_room(self, websocket: Any, room_id: str):
        """Add connection to specific room"""
        try:
            if room_id not in self.rooms:
                self.rooms[room_id] = set()
            
            self.rooms[room_id].add(websocket)
            
            # Update metadata
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]['rooms'].add(room_id)
            
            logger.info(f"WebSocket joined room: {room_id}")
            
            # Confirm join
            await websocket.send_json({
                'type': 'room_joined',
                'room_id': room_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Join room error: {e}")
        
    async def leave_room(self, websocket: Any, room_id: str):
        """Remove connection from room"""
        try:
            if room_id in self.rooms:
                self.rooms[room_id].discard(websocket)
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
            
            # Update metadata
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]['rooms'].discard(room_id)
            
            logger.info(f"WebSocket left room: {room_id}")
            
        except Exception as e:
            logger.error(f"Leave room error: {e}")
        
    async def broadcast(self, message: Dict[str, Any]):
        """Send message to all connected clients"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
        
    async def broadcast_to_room(self, room_id: str, message: Dict[str, Any]):
        """Send message to all clients in a room"""
        if room_id not in self.rooms:
            return
        
        disconnected = []
        
        for connection in list(self.rooms[room_id]):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Room broadcast error: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
        
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user"""
        if user_id not in self.user_connections:
            logger.warning(f"User {user_id} not connected")
            return
        
        try:
            await self.user_connections[user_id].send_json(message)
        except Exception as e:
            logger.error(f"User send error: {e}")
            self.disconnect(self.user_connections[user_id])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            'total_connections': len(self.active_connections),
            'total_rooms': len(self.rooms),
            'total_users': len(self.user_connections),
            'rooms': {
                room_id: len(connections) 
                for room_id, connections in self.rooms.items()
            }
        }


# Singleton instance
manager = ConnectionManager()
