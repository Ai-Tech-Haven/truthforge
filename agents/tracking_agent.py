"""
Tracking Agent for Real-Time Shipment Positions

Integrates with carrier APIs and broadcasts position updates
via WebSocket for live tracking visualization.
"""
import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from agents.base_agent import BaseAgent
from agents.config import Config
from agents.hedera_client import HederaClientBase

logger = logging.getLogger(__name__)


class TrackingAgent(BaseAgent):
    """Agent responsible for real-time shipment tracking"""
    
    def __init__(
        self,
        agent_id: str = "truthforge-tracking-001",
        capabilities: List[str] = None,
        hcs_topic_id: str = "",
        config: Config = None,
        hedera_client: HederaClientBase = None
    ):
        if capabilities is None:
            capabilities = [
                "real_time_tracking",
                "position_updates",
                "eta_calculation",
                "route_optimization"
            ]
        
        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            hcs_topic_id=hcs_topic_id,
            config=config or Config(),
            hedera_client=hedera_client
        )
        
        self.active_trackers: Dict[str, asyncio.Task] = {}
        self.shipment_routes: Dict[str, List[Dict[str, float]]] = {}
        
        # Mock route data for testing
        self.mock_routes = {
            'default': [
                {'lat': 1.3521, 'lng': 103.8198},  # Singapore
                {'lat': 22.3193, 'lng': 114.1694},  # Hong Kong
                {'lat': 35.6762, 'lng': 139.6503},  # Tokyo
                {'lat': 37.7749, 'lng': -122.4194},  # San Francisco
            ]
        }
        
        logger.info(f"Initialized {self.__class__.__name__} with ID {agent_id}")
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process tracking requests"""
        request_type = request.get('type', 'unknown')
        
        if request_type == 'start_tracking':
            return self._handle_start_tracking(request)
        elif request_type == 'stop_tracking':
            return self._handle_stop_tracking(request)
        elif request_type == 'get_position':
            return self._handle_get_position(request)
        elif request_type == 'get_route':
            return self._handle_get_route(request)
        else:
            return {
                'success': False,
                'error': f'Unknown request type: {request_type}'
            }
    
    def _handle_start_tracking(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle start tracking request"""
        shipment_id = request.get('shipment_id')
        if not shipment_id:
            return {'success': False, 'error': 'shipment_id required'}
        
        return {
            'success': True,
            'message': f'Tracking started for {shipment_id}',
            'shipment_id': shipment_id
        }
    
    def _handle_stop_tracking(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle stop tracking request"""
        shipment_id = request.get('shipment_id')
        if not shipment_id:
            return {'success': False, 'error': 'shipment_id required'}
        
        return {
            'success': True,
            'message': f'Tracking stopped for {shipment_id}',
            'shipment_id': shipment_id
        }
    
    def _handle_get_position(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get position request"""
        shipment_id = request.get('shipment_id')
        if not shipment_id:
            return {'success': False, 'error': 'shipment_id required'}
        
        position = self.get_current_position(shipment_id)
        
        return {
            'success': True,
            'shipment_id': shipment_id,
            'position': position
        }
    
    def _handle_get_route(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get route request"""
        shipment_id = request.get('shipment_id')
        if not shipment_id:
            return {'success': False, 'error': 'shipment_id required'}
        
        route = self.shipment_routes.get(shipment_id, self.mock_routes['default'])
        
        return {
            'success': True,
            'shipment_id': shipment_id,
            'route': route
        }
    
    async def start_tracking(self, shipment_id: str, db: Optional[Session] = None):
        """Start real-time tracking for a shipment"""
        if shipment_id in self.active_trackers:
            logger.warning(f"Tracking already active for {shipment_id}")
            return
        
        # Create tracking task
        task = asyncio.create_task(
            self._track_shipment_loop(shipment_id, db)
        )
        self.active_trackers[shipment_id] = task
        logger.info(f"Started tracking shipment {shipment_id}")
    
    async def stop_tracking(self, shipment_id: str):
        """Stop tracking a shipment"""
        if shipment_id in self.active_trackers:
            self.active_trackers[shipment_id].cancel()
            del self.active_trackers[shipment_id]
            logger.info(f"Stopped tracking shipment {shipment_id}")
    
    async def _track_shipment_loop(self, shipment_id: str, db: Optional[Session]):
        """Main tracking loop - updates position every 5 seconds"""
        try:
            step = 0
            route = self.mock_routes['default']
            
            while True:
                # Get latest position
                position = await self._get_current_position(shipment_id, step, route)
                
                # Calculate ETA
                eta = await self._calculate_eta(shipment_id, position, route, step)
                
                # Determine status
                status = self._determine_status(position, step, len(route))
                
                # Create update message
                update = {
                    'type': 'position_update',
                    'shipment_id': shipment_id,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'position': position,
                    'eta': eta,
                    'status': status,
                    'progress': (step / len(route)) * 100 if route else 0
                }
                
                # Broadcast via WebSocket (will be handled by routes)
                logger.debug(f"Position update for {shipment_id}: {position}")
                
                # Save to database if provided
                if db:
                    self._save_position(shipment_id, position, db)
                
                # Increment step
                step += 1
                if step >= len(route):
                    step = 0  # Loop for demo
                
                # Wait 5 seconds before next update
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            logger.info(f"Tracking cancelled for {shipment_id}")
        except Exception as e:
            logger.error(f"Tracking error for {shipment_id}: {e}")
    
    async def _get_current_position(
        self,
        shipment_id: str,
        step: int,
        route: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """Get current position from carrier API or mock data"""
        if self.config.mock_mode:
            # Simulate movement along route
            if not route:
                route = self.mock_routes['default']
            
            # Interpolate between waypoints
            current_idx = step % len(route)
            next_idx = (step + 1) % len(route)
            
            current = route[current_idx]
            next_point = route[next_idx]
            
            # Add some randomness for realistic movement
            lat = current['lat'] + (next_point['lat'] - current['lat']) * 0.1
            lng = current['lng'] + (next_point['lng'] - current['lng']) * 0.1
            
            # Add small random variation
            lat += (random.random() - 0.5) * 0.01
            lng += (random.random() - 0.5) * 0.01
            
            return {
                'lat': lat,
                'lng': lng,
                'speed': random.uniform(15, 25),  # knots
                'heading': random.uniform(0, 360),
                'altitude': 0,  # sea level for ships
                'accuracy': random.uniform(5, 15)  # meters
            }
        else:
            # Call actual carrier API
            # TODO: Implement real carrier API integration
            return await self._fetch_from_carrier_api(shipment_id)
    
    async def _fetch_from_carrier_api(self, shipment_id: str) -> Dict[str, Any]:
        """Fetch position from actual carrier API"""
        # Placeholder for real API integration
        logger.warning("Real carrier API not implemented, using mock data")
        return await self._get_current_position(shipment_id, 0, self.mock_routes['default'])
    
    async def _calculate_eta(
        self,
        shipment_id: str,
        current_position: Dict[str, float],
        route: List[Dict[str, float]],
        step: int
    ) -> str:
        """Calculate estimated time of arrival"""
        if self.config.mock_mode:
            # Simple ETA calculation for demo
            remaining_waypoints = len(route) - (step % len(route))
            hours_remaining = remaining_waypoints * 24  # 24 hours per waypoint
            
            eta = datetime.now(timezone.utc) + timedelta(hours=hours_remaining)
            return eta.isoformat()
        else:
            # Real ETA calculation based on distance and speed
            # TODO: Implement real ETA calculation
            return (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    
    def _determine_status(
        self,
        position: Dict[str, float],
        step: int,
        total_steps: int
    ) -> str:
        """Determine shipment status based on position"""
        progress = (step / total_steps) * 100 if total_steps > 0 else 0
        
        if progress < 10:
            return 'departed'
        elif progress < 90:
            return 'in_transit'
        elif progress < 100:
            return 'approaching_destination'
        else:
            return 'arrived'
    
    def _save_position(
        self,
        shipment_id: str,
        position: Dict[str, Any],
        db: Session
    ):
        """Save position to database for history"""
        try:
            from database.models import VerificationLog
            
            log = VerificationLog(
                request_id=f"position-{shipment_id}-{int(datetime.now().timestamp())}",
                agent_id=self.agent_id,
                action='position_update',
                details={
                    'shipment_id': shipment_id,
                    'position': position,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            db.add(log)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to save position: {e}")
            db.rollback()
    
    def get_current_position(self, shipment_id: str) -> Dict[str, Any]:
        """Get current position synchronously"""
        if self.config.mock_mode:
            return {
                'lat': 1.3521 + (random.random() - 0.5) * 0.1,
                'lng': 103.8198 + (random.random() - 0.5) * 0.1,
                'speed': random.uniform(15, 25),
                'heading': random.uniform(0, 360),
                'altitude': 0,
                'accuracy': random.uniform(5, 15)
            }
        else:
            # TODO: Implement real API call
            return self.get_current_position(shipment_id)
    
    def get_shipment_status(
        self,
        shipment_id: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Get complete shipment status"""
        position = self.get_current_position(shipment_id)
        route = self.shipment_routes.get(shipment_id, self.mock_routes['default'])
        
        return {
            'shipment_id': shipment_id,
            'position': position,
            'route': route,
            'status': 'in_transit',
            'eta': (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
            'last_update': datetime.now(timezone.utc).isoformat()
        }
    
    def force_update(self, shipment_id: str) -> Dict[str, Any]:
        """Force immediate position update"""
        return self.get_shipment_status(shipment_id)
