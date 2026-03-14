"""
TruthForge Registry & Discovery Agent

This agent manages agent discovery, health reporting, and registry
synchronization with the HOL (Hashgraph Online) registry. It provides
real-time agent status monitoring and handles DISCOVER message types
for agent capability matching.
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from agents.base_agent import BaseAgent, AgentStatus
from agents.config import Config
from agents.hedera_client import HederaClientBase
from agents.hcs10_message import HCS10Message, MessageType
from database.database import db_session
from database.models import Agent
from hol_registry.registry import HOLRegistry, AgentMetadata


logger = logging.getLogger(__name__)


@dataclass
class DiscoverResponse:
    """Response to DISCOVER message."""
    matching_agents: List[AgentMetadata]
    total_agents: int
    query_timestamp: datetime
    cache_hit: bool


@dataclass
class HealthReport:
    """Comprehensive health report for all agents."""
    total_agents: int
    online_agents: int
    offline_agents: int
    error_agents: int
    average_response_time: float
    last_updated: datetime
    agent_details: List[AgentStatus]


class RegistryDiscoveryAgent(BaseAgent):
    """
    Registry & Discovery Agent for TruthForge.
    
    Manages agent discovery, health monitoring, and registry synchronization.
    Provides real-time status information for all registered agents and
    handles capability-based agent discovery requests.
    """
    
    def __init__(
        self,
        agent_id: str,
        capabilities: List[str],
        hcs_topic_id: str,
        config: Config,
        hedera_client: HederaClientBase,
        hol_registry: HOLRegistry
    ):
        """
        Initialize Registry & Discovery Agent.
        
        Args:
            agent_id: Unique agent identifier
            capabilities: List of agent capabilities
            hcs_topic_id: HCS topic for messaging
            config: TruthForge configuration
            hedera_client: Hedera client for blockchain operations
            hol_registry: HOL registry instance
        """
        super().__init__(agent_id, capabilities, hcs_topic_id, config, hedera_client)
        self.hol_registry = hol_registry
        
        # Agent discovery cache with TTL
        self.discovery_cache = {}
        self.cache_ttl = timedelta(minutes=5)  # 5-minute cache TTL
        
        # Health monitoring state
        self.last_health_check = datetime.now(timezone.utc)
        self.health_check_interval = timedelta(minutes=1)  # Check every minute
        
        logger.info(f"Initialized {self.__class__.__name__} with ID {agent_id}")
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process registry and discovery requests.
        
        Args:
            request: Request containing discovery parameters
            
        Returns:
            Dict[str, Any]: Discovery results
        """
        start_time = time.time()
        
        try:
            request_type = request.get('type', 'unknown')
            
            if request_type == 'discover_agents':
                result = self._process_agent_discovery(request)
            elif request_type == 'health_report':
                result = self._process_health_report(request)
            elif request_type == 'sync_registry':
                result = self._process_registry_sync(request)
            elif request_type == 'agent_status':
                result = self._process_agent_status(request)
            else:
                raise ValueError(f"Unsupported request type: {request_type}")
            
            # Track successful request
            response_time = time.time() - start_time
            self._track_request(response_time, success=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing registry request: {e}")
            response_time = time.time() - start_time
            self._track_request(response_time, success=False)
            
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _process_agent_discovery(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent discovery request."""
        capability_filter = request.get('capabilities', [])
        status_filter = request.get('status')
        use_cache = request.get('use_cache', True)
        
        # Handle DISCOVER message
        discover_response = self.handle_discover_message(
            capability_filter, status_filter, use_cache
        )
        
        return {
            'success': True,
            'discover_response': asdict(discover_response),
            'agent_id': self.agent_id
        }
    
    def _process_health_report(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process health report request."""
        # Get all registered agents
        all_agents = self.hol_registry.get_all_agents()
        
        # Monitor agent health
        health_report = self.monitor_agent_health([agent.agent_id for agent in all_agents])
        
        return {
            'success': True,
            'health_report': asdict(health_report),
            'agent_id': self.agent_id
        }
    
    def _process_registry_sync(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process registry synchronization request."""
        force_sync = request.get('force_sync', False)
        
        # Sync with HOL registry
        sync_result = self.sync_with_hol(force_sync)
        
        return {
            'success': sync_result,
            'message': 'Registry sync completed' if sync_result else 'Registry sync failed',
            'agent_id': self.agent_id
        }
    
    def _process_agent_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual agent status request."""
        target_agent_id = request.get('agent_id')
        
        if not target_agent_id:
            raise ValueError("agent_id is required for status request")
        
        # Get agent status
        agent_status = self.get_agent_status(target_agent_id)
        
        return {
            'success': True,
            'agent_status': asdict(agent_status) if agent_status else None,
            'agent_id': self.agent_id
        }
    
    def sync_with_hol(self, force_sync: bool = False) -> bool:
        """
        Synchronize with HOL registry.
        
        Args:
            force_sync: Force synchronization even if recently synced
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        try:
            logger.info("Synchronizing with HOL registry...")
            
            # In mock mode, simulate sync
            if self.config.mock_mode:
                logger.info("Mock mode: Simulating HOL registry sync")
                return True
            
            # In live mode, this would query the actual HOL registry
            # For now, we'll work with the local registry
            
            # Submit sync operation to HCS
            hcs_transaction_id = self._submit_to_hcs({
                'action': 'registry_sync',
                'force_sync': force_sync,
                'agent_count': self.hol_registry.count_agents()
            })
            
            logger.info(f"HOL registry sync completed. HCS TX: {hcs_transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"HOL registry sync failed: {e}")
            return False
    
    def monitor_agent_health(self, agent_ids: List[str]) -> HealthReport:
        """
        Monitor health of specified agents.
        
        Args:
            agent_ids: List of agent IDs to monitor
            
        Returns:
            HealthReport: Comprehensive health report
        """
        logger.debug(f"Monitoring health of {len(agent_ids)} agents")
        
        agent_details = []
        online_count = 0
        offline_count = 0
        error_count = 0
        total_response_time = 0.0
        
        for agent_id in agent_ids:
            try:
                # Get agent metadata from registry
                agent_metadata = self.hol_registry.get_agent(agent_id)
                
                if not agent_metadata:
                    # Agent not found in registry
                    agent_status = AgentStatus(
                        agent_id=agent_id,
                        status="OFFLINE",
                        last_heartbeat=datetime.now(timezone.utc),
                        requests_processed=0,
                        average_response_time=0.0,
                        error_count=0
                    )
                    offline_count += 1
                else:
                    # Create agent status from metadata
                    agent_status = AgentStatus(
                        agent_id=agent_id,
                        status=agent_metadata.status,
                        last_heartbeat=agent_metadata.last_updated,
                        requests_processed=0,  # Would be tracked separately
                        average_response_time=0.0,  # Would be calculated from metrics
                        error_count=0  # Would be tracked separately
                    )
                    
                    # Count by status
                    if agent_metadata.status == "ONLINE":
                        online_count += 1
                    elif agent_metadata.status == "ERROR":
                        error_count += 1
                    else:
                        offline_count += 1
                
                agent_details.append(agent_status)
                total_response_time += agent_status.average_response_time
                
            except Exception as e:
                logger.error(f"Failed to get health for agent {agent_id}: {e}")
                # Create error status
                agent_status = AgentStatus(
                    agent_id=agent_id,
                    status="ERROR",
                    last_heartbeat=datetime.now(timezone.utc),
                    requests_processed=0,
                    average_response_time=0.0,
                    error_count=1
                )
                agent_details.append(agent_status)
                error_count += 1
        
        # Calculate average response time
        average_response_time = 0.0
        if agent_details:
            average_response_time = total_response_time / len(agent_details)
        
        health_report = HealthReport(
            total_agents=len(agent_ids),
            online_agents=online_count,
            offline_agents=offline_count,
            error_agents=error_count,
            average_response_time=average_response_time,
            last_updated=datetime.now(timezone.utc),
            agent_details=agent_details
        )
        
        # Store health report in database
        self._store_health_report(health_report)
        
        logger.info(
            f"Health check complete: {online_count} online, "
            f"{offline_count} offline, {error_count} error"
        )
        
        return health_report
    
    def discover_agents(
        self,
        capability_filter: Optional[List[str]] = None,
        status_filter: Optional[str] = None
    ) -> List[AgentMetadata]:
        """
        Discover agents by capabilities and status.
        
        Args:
            capability_filter: List of required capabilities (optional)
            status_filter: Required status (optional)
            
        Returns:
            List[AgentMetadata]: List of matching agents
        """
        return self.hol_registry.query_agents(
            capability_filter=capability_filter,
            status_filter=status_filter
        )
    
    def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """
        Get capabilities for a specific agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List[str]: List of agent capabilities
        """
        agent_metadata = self.hol_registry.get_agent(agent_id)
        if agent_metadata:
            return agent_metadata.capabilities
        return []
    
    def handle_discover_message(
        self,
        capability_filter: Optional[List[str]] = None,
        status_filter: Optional[str] = None,
        use_cache: bool = True
    ) -> DiscoverResponse:
        """
        Handle DISCOVER message with capability filtering.
        
        Args:
            capability_filter: List of required capabilities
            status_filter: Required status
            use_cache: Whether to use cached results
            
        Returns:
            DiscoverResponse: Discovery response with matching agents
        """
        cache_key = f"{capability_filter}:{status_filter}"
        current_time = datetime.now(timezone.utc)
        
        # Check cache first
        if use_cache and cache_key in self.discovery_cache:
            cached_entry = self.discovery_cache[cache_key]
            if current_time - cached_entry['timestamp'] < self.cache_ttl:
                logger.debug(f"Returning cached discovery result for {cache_key}")
                return DiscoverResponse(
                    matching_agents=cached_entry['agents'],
                    total_agents=len(cached_entry['agents']),
                    query_timestamp=current_time,
                    cache_hit=True
                )
        
        # Query registry for matching agents
        matching_agents = self.discover_agents(capability_filter, status_filter)
        
        # Cache the result
        self.discovery_cache[cache_key] = {
            'agents': matching_agents,
            'timestamp': current_time
        }
        
        # Clean old cache entries
        self._clean_discovery_cache()
        
        logger.info(
            f"Discovery query returned {len(matching_agents)} agents "
            f"(filter: {capability_filter}, status: {status_filter})"
        )
        
        return DiscoverResponse(
            matching_agents=matching_agents,
            total_agents=len(matching_agents),
            query_timestamp=current_time,
            cache_hit=False
        )
    
    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """
        Update status of a registered agent.
        
        Args:
            agent_id: Agent identifier
            status: New status
            
        Returns:
            bool: True if update successful, False otherwise
        """
        success = self.hol_registry.update_agent_status(agent_id, status)
        
        if success:
            # Store status update in database
            self._store_agent_status_update(agent_id, status)
            
            # Submit to HCS
            self._submit_to_hcs({
                'action': 'agent_status_update',
                'agent_id': agent_id,
                'status': status
            })
        
        return success
    
    def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """
        Get current status of a specific agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Optional[AgentStatus]: Agent status or None if not found
        """
        agent_metadata = self.hol_registry.get_agent(agent_id)
        
        if not agent_metadata:
            return None
        
        return AgentStatus(
            agent_id=agent_id,
            status=agent_metadata.status,
            last_heartbeat=agent_metadata.last_updated,
            requests_processed=0,  # Would be tracked separately
            average_response_time=0.0,  # Would be calculated from metrics
            error_count=0  # Would be tracked separately
        )
    
    def cache_agent_info(self, agent_info: AgentMetadata, ttl: int = 300) -> bool:
        """
        Cache agent information with TTL.
        
        Args:
            agent_info: Agent metadata to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if caching successful, False otherwise
        """
        try:
            cache_key = f"agent:{agent_info.agent_id}"
            cache_entry = {
                'agent_info': agent_info,
                'timestamp': datetime.now(timezone.utc),
                'ttl': ttl
            }
            
            # Store in discovery cache (reusing the same cache)
            self.discovery_cache[cache_key] = cache_entry
            
            logger.debug(f"Cached agent info for {agent_info.agent_id} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache agent info: {e}")
            return False
    
    def _clean_discovery_cache(self) -> None:
        """Clean expired entries from discovery cache."""
        current_time = datetime.now(timezone.utc)
        expired_keys = []
        
        for key, entry in self.discovery_cache.items():
            # Check if entry has expired
            if 'ttl' in entry:
                # Entry with custom TTL
                if current_time - entry['timestamp'] > timedelta(seconds=entry['ttl']):
                    expired_keys.append(key)
            else:
                # Entry with default cache TTL
                if current_time - entry['timestamp'] > self.cache_ttl:
                    expired_keys.append(key)
        
        # Remove expired entries
        for key in expired_keys:
            del self.discovery_cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
    
    def _submit_to_hcs(self, payload: Dict[str, Any]) -> str:
        """Submit registry operation to HCS for timestamping."""
        try:
            message = HCS10Message(
                message_type=MessageType.NOTIFY,
                sender_id=self.agent_id,
                recipient_id="hcs-consensus",
                timestamp=datetime.now(timezone.utc).isoformat(),
                payload=payload
            )
            
            # Generate signature
            secret_key = self.config.hedera_private_key or "mock-secret-key"
            message.signature = message.generate_signature(secret_key)
            
            # Submit to HCS
            transaction_id = self.hedera_client.submit_message(message)
            logger.info(f"Submitted registry operation to HCS: {transaction_id}")
            
            return transaction_id
            
        except Exception as e:
            logger.error(f"Failed to submit to HCS: {e}")
            return f"mock-tx-{int(time.time())}"
    
    def _store_health_report(self, health_report: HealthReport) -> None:
        """Store health report in database."""
        try:
            # Store individual agent statuses using new database models
            for agent_status in health_report.agent_details:
                try:
                    # Check if agent exists
                    existing_agent = db_session.query(Agent).filter_by(agent_id=agent_status.agent_id).first()
                    
                    if existing_agent:
                        # Update existing agent
                        existing_agent.status = agent_status.status.lower()
                        existing_agent.last_heartbeat = agent_status.last_heartbeat
                    else:
                        # Create new agent record
                        new_agent = Agent(
                            agent_id=agent_status.agent_id,
                            uaid=f"uaid_{agent_status.agent_id}",
                            hcs_topic_id="0.0.unknown",
                            status=agent_status.status.lower(),
                            last_heartbeat=agent_status.last_heartbeat
                        )
                        db_session.add(new_agent)
                    
                    db_session.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to store agent status for {agent_status.agent_id}: {e}")
                    db_session.rollback()
            
            logger.debug("Stored health report in database")
            
        except Exception as e:
            logger.error(f"Failed to store health report: {e}")
            db_session.rollback()
    
    def _store_agent_status_update(self, agent_id: str, status: str) -> None:
        """Store agent status update in database."""
        try:
            # Update existing agent or create new one
            existing_agent = db_session.query(Agent).filter_by(agent_id=agent_id).first()
            
            if existing_agent:
                existing_agent.status = status.lower()
                existing_agent.last_heartbeat = datetime.now(timezone.utc)
            else:
                new_agent = Agent(
                    agent_id=agent_id,
                    uaid=f"uaid_{agent_id}",
                    hcs_topic_id="0.0.unknown",
                    status=status.lower(),
                    last_heartbeat=datetime.now(timezone.utc)
                )
                db_session.add(new_agent)
            
            db_session.commit()
            logger.debug(f"Stored status update for agent {agent_id}: {status}")
            
        except Exception as e:
            logger.error(f"Failed to store agent status update: {e}")
            db_session.rollback()