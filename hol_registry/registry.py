"""
TruthForge HOL Registry

This module implements the Hashgraph Online (HOL) registry for agent
registration, discovery, and status management. The registry maintains
an in-memory store of all registered agents with optional persistence.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


logger = logging.getLogger(__name__)


@dataclass
class AgentMetadata:
    """
    Metadata for a registered agent.
    
    Contains all information needed for agent discovery and communication.
    
    Attributes:
        agent_id: Unique identifier for the agent
        capabilities: List of capabilities this agent provides
        endpoints: Dictionary of endpoint URLs for agent communication
        hcs_topic_id: HCS topic ID for messaging
        status: Current agent status (ONLINE, OFFLINE, BUSY, ERROR)
        registered_at: Timestamp when agent was registered
        last_updated: Timestamp of last registration update
        metadata: Additional metadata (version, network, etc.)
    """
    agent_id: str
    capabilities: List[str]
    endpoints: Dict[str, str] = field(default_factory=dict)
    hcs_topic_id: str = ""
    status: str = "ONLINE"
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert agent metadata to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all metadata fields
        """
        return {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "endpoints": self.endpoints,
            "hcs_topic_id": self.hcs_topic_id,
            "status": self.status,
            "registered_at": self.registered_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata
        }


class HOLRegistry:
    """
    Hashgraph Online (HOL) registry for agent management.
    
    Provides centralized registration, discovery, and status management
    for all TruthForge agents. Maintains an in-memory store with optional
    persistence to disk.
    
    Attributes:
        agents: Dictionary mapping agent IDs to AgentMetadata
        persistence_enabled: Whether to persist registry to disk
        persistence_path: Path to persistence file (if enabled)
    """
    
    def __init__(self, persistence_enabled: bool = False, persistence_path: Optional[str] = None):
        """
        Initialize HOL registry.
        
        Args:
            persistence_enabled: Whether to enable persistence to disk
            persistence_path: Path to persistence file (optional)
        """
        self.agents: Dict[str, AgentMetadata] = {}
        self.persistence_enabled = persistence_enabled
        self.persistence_path = persistence_path
        
        logger.info(
            f"Initialized HOL registry (persistence: {persistence_enabled})"
        )
    
    def register_agent(
        self,
        agent_id: str,
        capabilities: List[str],
        endpoints: Optional[Dict[str, str]] = None,
        hcs_topic_id: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register an agent with the HOL registry.
        
        If the agent is already registered, this method updates the existing
        registration (idempotent operation). All agent metadata is stored
        for discovery and status queries.
        
        Args:
            agent_id: Unique identifier for the agent
            capabilities: List of capabilities this agent provides
            endpoints: Dictionary of endpoint URLs (optional)
            hcs_topic_id: HCS topic ID for messaging (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            bool: True if registration successful, False otherwise
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Validate required parameters
        if not agent_id:
            raise ValueError("agent_id is required")
        
        if not capabilities:
            raise ValueError("capabilities list cannot be empty")
        
        # Check if agent already exists
        if agent_id in self.agents:
            logger.info(f"Agent {agent_id} already registered. Updating registration.")
            existing_agent = self.agents[agent_id]
            
            # Update existing registration
            existing_agent.capabilities = capabilities
            existing_agent.endpoints = endpoints or {}
            existing_agent.hcs_topic_id = hcs_topic_id
            existing_agent.last_updated = datetime.now(timezone.utc)
            existing_agent.metadata = metadata or {}
            
            logger.info(f"Updated registration for agent {agent_id}")
            return True
        
        # Create new agent metadata
        agent_metadata = AgentMetadata(
            agent_id=agent_id,
            capabilities=capabilities,
            endpoints=endpoints or {},
            hcs_topic_id=hcs_topic_id,
            metadata=metadata or {}
        )
        
        # Store agent in registry
        self.agents[agent_id] = agent_metadata
        
        logger.info(
            f"Registered agent {agent_id} with capabilities: "
            f"{', '.join(capabilities)}"
        )
        
        # Persist if enabled
        if self.persistence_enabled:
            self._persist()
        
        return True
    
    def query_agents(
        self,
        capability_filter: Optional[List[str]] = None,
        status_filter: Optional[str] = None
    ) -> List[AgentMetadata]:
        """
        Query registered agents with optional filtering.
        
        Returns a list of agents matching the specified filters. If no
        filters are provided, returns all registered agents.
        
        Args:
            capability_filter: List of capabilities to filter by (optional)
                              Returns agents with at least one matching capability
            status_filter: Status to filter by (optional)
                          Returns only agents with matching status
            
        Returns:
            List[AgentMetadata]: List of matching agent metadata objects
        """
        results = []
        
        for agent_metadata in self.agents.values():
            # Apply capability filter
            if capability_filter:
                # Check if agent has at least one matching capability
                has_matching_capability = any(
                    cap in agent_metadata.capabilities
                    for cap in capability_filter
                )
                if not has_matching_capability:
                    continue
            
            # Apply status filter
            if status_filter and agent_metadata.status != status_filter:
                continue
            
            results.append(agent_metadata)
        
        logger.debug(
            f"Query returned {len(results)} agents "
            f"(capability_filter={capability_filter}, status_filter={status_filter})"
        )
        
        return results
    
    def get_agent_status(self, agent_id: str) -> Optional[str]:
        """
        Get the current status of a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Optional[str]: Agent status (ONLINE, OFFLINE, BUSY, ERROR),
                          or None if agent not found
        """
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found in registry")
            return None
        
        status = self.agents[agent_id].status
        logger.debug(f"Agent {agent_id} status: {status}")
        return status
    
    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """
        Update the status of a registered agent.
        
        Args:
            agent_id: Unique identifier for the agent
            status: New status (ONLINE, OFFLINE, BUSY, ERROR)
            
        Returns:
            bool: True if update successful, False if agent not found
        """
        if agent_id not in self.agents:
            logger.warning(f"Cannot update status: Agent {agent_id} not found")
            return False
        
        self.agents[agent_id].status = status
        self.agents[agent_id].last_updated = datetime.now(timezone.utc)
        
        logger.info(f"Updated agent {agent_id} status to {status}")
        
        # Persist if enabled
        if self.persistence_enabled:
            self._persist()
        
        return True
    
    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """
        Get complete metadata for a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Optional[AgentMetadata]: Agent metadata, or None if not found
        """
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found in registry")
            return None
        
        return self.agents[agent_id]
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the registry.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            bool: True if agent was removed, False if not found
        """
        if agent_id not in self.agents:
            logger.warning(f"Cannot unregister: Agent {agent_id} not found")
            return False
        
        del self.agents[agent_id]
        logger.info(f"Unregistered agent {agent_id}")
        
        # Persist if enabled
        if self.persistence_enabled:
            self._persist()
        
        return True
    
    def get_all_agents(self) -> List[AgentMetadata]:
        """
        Get all registered agents.
        
        Returns:
            List[AgentMetadata]: List of all agent metadata objects
        """
        return list(self.agents.values())
    
    def count_agents(self) -> int:
        """
        Get the total number of registered agents.
        
        Returns:
            int: Number of registered agents
        """
        return len(self.agents)
    
    def _persist(self) -> None:
        """
        Persist registry to disk.
        
        Internal method to save registry state to disk when persistence
        is enabled. This is a placeholder for future implementation.
        """
        # TODO: Implement persistence to disk
        # This would serialize self.agents to JSON and write to self.persistence_path
        logger.debug("Persistence not yet implemented")
    
    def _load(self) -> None:
        """
        Load registry from disk.
        
        Internal method to restore registry state from disk when persistence
        is enabled. This is a placeholder for future implementation.
        """
        # TODO: Implement loading from disk
        # This would read from self.persistence_path and deserialize to self.agents
        logger.debug("Loading from disk not yet implemented")
    
    def __repr__(self) -> str:
        """
        String representation of the registry.
        
        Returns:
            str: Human-readable registry representation
        """
        return f"HOLRegistry(agents={len(self.agents)}, persistence={self.persistence_enabled})"
