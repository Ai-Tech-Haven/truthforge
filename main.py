#!/usr/bin/env python3
"""
TruthForge Main Application Entry Point

This module initializes and starts the complete TruthForge system with
5 specialized agents, HOL registry, and Flask API server. It supports
both mock and live modes for development and production deployment.

The system includes:
- Orchestrator Agent (truthforge-orch-001)
- Verification & Compliance Agent (truthforge-verify-001)  
- Carrier Adapter Agent (Council-Grade) (truthforge-carrier-001)
- Registry & Discovery Agent (truthforge-registry-001)
- Evidence & Settlement Agent (truthforge-evidence-001)
"""

import logging
import sys
import signal
import threading
from typing import Dict, Any

from agents.config import Config
from agents.hedera_client import HederaClient, MockHederaClient
from hol_registry.registry import HOLRegistry
from agents.orchestrator_agent import OrchestratorAgent
from agents.verification_compliance_agent import VerificationComplianceAgent
from agents.carrier_adapter_agent import CarrierAdapterAgent
from agents.registry_discovery_agent import RegistryDiscoveryAgent
from agents.evidence_settlement_agent import EvidenceSettlementAgent
from database.database import init_db, test_connection, get_stats
from api.app import create_app


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


class TruthForgeSystem:
    """
    Main TruthForge system orchestrator.
    
    Manages the lifecycle of all system components including agents,
    registry, database, and API server. Provides graceful startup
    and shutdown with proper error handling.
    """
    
    def __init__(self):
        """Initialize TruthForge system."""
        self.config = None
        self.database = None
        self.hedera_client = None
        self.hol_registry = None
        self.agents = {}
        self.flask_app = None
        self.api_thread = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self) -> bool:
        """
        Initialize all system components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing TruthForge system...")
            
            # Load configuration
            logger.info("Loading configuration...")
            self.config = Config.load()
            
            # Set logging level from config
            logging.getLogger().setLevel(getattr(logging, self.config.log_level))
            
            logger.info(f"TruthForge starting in {'MOCK' if self.config.mock_mode else 'LIVE'} mode")
            
            # Initialize database
            logger.info("Initializing database...")
            init_db()
            
            # Test database connection
            if not test_connection():
                logger.warning("Database connection test failed - check configuration")
            
            # Log database stats
            stats = get_stats()
            logger.info(f"Database: {stats['type']} @ {stats['url']}")
            
            # Initialize Hedera client
            logger.info("Initializing Hedera client...")
            if self.config.mock_mode:
                self.hedera_client = MockHederaClient(self.config)
            else:
                self.hedera_client = HederaClient(self.config)
            
            # Authenticate Hedera client
            if not self.hedera_client.authenticate():
                logger.error("Failed to authenticate Hedera client")
                return False
            
            # Initialize HOL registry
            logger.info("Initializing HOL registry...")
            self.hol_registry = HOLRegistry(
                persistence_enabled=True,
                persistence_path="hol_registry.json"
            )
            
            # Initialize all 5 agents
            logger.info("Initializing agents...")
            self._initialize_agents()
            
            # Register all agents with HOL
            logger.info("Registering agents with HOL...")
            self._register_agents()
            
            # Initialize Flask API
            logger.info("Initializing Flask API...")
            self.flask_app = create_app(
                app_config=self.config,
                orchestrator=self.agents['orchestrator'],
                hol_registry=self.hol_registry
            )
            
            logger.info("TruthForge system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize TruthForge system: {e}")
            return False
    
    def _initialize_agents(self) -> None:
        """Initialize all 5 TruthForge agents."""
        
        # 1. Orchestrator Agent (truthforge-orch-001)
        logger.info("Initializing Orchestrator Agent...")
        self.agents['orchestrator'] = OrchestratorAgent(
            agent_id="truthforge-orch-001",
            capabilities=["workflow_coordination", "decision_execution", "agent_routing"],
            hcs_topic_id=self.config.hcs_topic_id,
            config=self.config,
            hedera_client=self.hedera_client
        )
        
        # 2. Verification & Compliance Agent (truthforge-verify-001)
        logger.info("Initializing Verification & Compliance Agent...")
        self.agents['verification_compliance'] = VerificationComplianceAgent(
            agent_id="truthforge-verify-001",
            capabilities=["document_validation", "compliance_assessment", "deepfake_detection"],
            hcs_topic_id=self.config.hcs_topic_id,
            config=self.config,
            hedera_client=self.hedera_client
        )
        
        # 3. Carrier Adapter Agent (Council-Grade) (truthforge-carrier-001)
        logger.info("Initializing Carrier Adapter Agent (Council-Grade)...")
        self.agents['carrier_adapter'] = CarrierAdapterAgent(
            agent_id="truthforge-carrier-001",
            capabilities=["carrier_data_ingestion", "data_normalization", "multi_carrier_support"],
            hcs_topic_id=self.config.hcs_topic_id,
            config=self.config,
            hedera_client=self.hedera_client
        )
        
        # 4. Registry & Discovery Agent (truthforge-registry-001)
        logger.info("Initializing Registry & Discovery Agent...")
        self.agents['registry_discovery'] = RegistryDiscoveryAgent(
            agent_id="truthforge-registry-001",
            capabilities=["agent_discovery", "health_reporting", "registry_sync"],
            hcs_topic_id=self.config.hcs_topic_id,
            config=self.config,
            hedera_client=self.hedera_client,
            hol_registry=self.hol_registry
        )
        
        # 5. Evidence & Settlement Agent (truthforge-evidence-001)
        logger.info("Initializing Evidence & Settlement Agent...")
        self.agents['evidence_settlement'] = EvidenceSettlementAgent(
            agent_id="truthforge-evidence-001",
            capabilities=["consensus_submission", "audit_reference_generation", "settlement_processing"],
            hcs_topic_id=self.config.hcs_topic_id,
            config=self.config,
            hedera_client=self.hedera_client
        )
        
        # Wire agents together in orchestrator
        self.agents['orchestrator'].set_agents({
            'verification_compliance': self.agents['verification_compliance'],
            'carrier_adapter': self.agents['carrier_adapter'],
            'registry_discovery': self.agents['registry_discovery'],
            'evidence_settlement': self.agents['evidence_settlement']
        })
        
        logger.info("All 5 agents initialized successfully")
    
    def _register_agents(self) -> None:
        """Register all agents with HOL registry and database."""
        import os
        from database.services import AgentService
        
        # Real per-agent data from environment (set during HOL registration)
        agent_env_data = {
            'orchestrator': {
                'name': 'Orchestrator Agent',
                'agent_id': os.getenv('AGENT_01_ID', 'truthforge-orch-001'),
                'uaid': os.getenv('AGENT_01_UAID', ''),
                'hcs_topic': os.getenv('AGENT_01_HCS_TOPIC', ''),
                'capabilities': ['workflow_coordination', 'decision_execution', 'agent_routing']
            },
            'verification_compliance': {
                'name': 'Verification & Compliance Agent',
                'agent_id': os.getenv('AGENT_02_ID', 'truthforge-verify-001'),
                'uaid': os.getenv('AGENT_02_UAID', ''),
                'hcs_topic': os.getenv('AGENT_02_HCS_TOPIC', ''),
                'capabilities': ['document_validation', 'compliance_assessment', 'deepfake_detection']
            },
            'carrier_adapter': {
                'name': 'Carrier Adapter Agent (Council-Grade)',
                'agent_id': os.getenv('AGENT_03_ID', 'truthforge-carrier-001'),
                'uaid': os.getenv('AGENT_03_UAID', ''),
                'hcs_topic': os.getenv('AGENT_03_HCS_TOPIC', ''),
                'capabilities': ['carrier_data_ingestion', 'data_normalization', 'multi_carrier_support']
            },
            'registry_discovery': {
                'name': 'Registry & Discovery Agent',
                'agent_id': os.getenv('AGENT_04_ID', 'truthforge-registry-001'),
                'uaid': os.getenv('AGENT_04_UAID', ''),
                'hcs_topic': os.getenv('AGENT_04_HCS_TOPIC', ''),
                'capabilities': ['agent_discovery', 'health_reporting', 'registry_sync']
            },
            'evidence_settlement': {
                'name': 'Evidence & Settlement Agent',
                'agent_id': os.getenv('AGENT_05_ID', 'truthforge-evidence-001'),
                'uaid': os.getenv('AGENT_05_UAID', ''),
                'hcs_topic': os.getenv('AGENT_05_HCS_TOPIC', ''),
                'capabilities': ['consensus_submission', 'audit_reference_generation', 'settlement_processing']
            }
        }
        
        for agent_name, agent in self.agents.items():
            try:
                env = agent_env_data.get(agent_name, {})
                # Use per-agent HCS topic from env if available, else fall back to global
                per_agent_hcs = env.get('hcs_topic') or agent.hcs_topic_id

                # Register with HOL (in-memory registry)
                self.hol_registry.register_agent(
                    agent_id=env.get('agent_id', agent.agent_id),
                    capabilities=env.get('capabilities', []),
                    hcs_topic_id=per_agent_hcs,
                    metadata={'uaid': env.get('uaid', '')}
                )
                logger.info(f"Registered {agent.agent_id} with HOL (topic={per_agent_hcs})")

                # Upsert into database (live mode only)
                if not self.config.mock_mode:
                    try:
                        AgentService.upsert_agent(
                            agent_id=env.get('agent_id', agent.agent_id),
                            agent_name=env.get('name', agent.agent_id),
                            status='online',
                            hol_uaid=env.get('uaid') or None,
                            hcs_topic_id=per_agent_hcs,
                            capabilities=env.get('capabilities', [])
                        )
                        logger.info(f"Upserted {agent.agent_id} in database (uaid={env.get('uaid', 'N/A')})")
                    except Exception as e:
                        logger.error(f"Error upserting {agent.agent_id} in database: {e}")

            except Exception as e:
                logger.error(f"Error registering {agent.agent_id}: {e}")
        
        # Verify all 5 agents are registered
        registered_count = self.hol_registry.count_agents()
        if registered_count >= 5:
            logger.info(f"All 5 agents successfully registered with HOL")
        else:
            logger.warning(f"Expected 5 agents, but {registered_count} are registered")
    
    def start(self) -> bool:
        """
        Start the TruthForge system.
        
        Returns:
            bool: True if startup successful, False otherwise
        """
        try:
            if not self.initialize():
                return False
            
            logger.info("Starting TruthForge system...")
            self.running = True
            
            # Start Flask API server in separate thread
            logger.info(f"Starting API server on port {self.config.api_port}...")
            self.api_thread = threading.Thread(
                target=self._run_api_server,
                daemon=True
            )
            self.api_thread.start()
            
            logger.info("TruthForge system started successfully")
            logger.info(f"API server running on http://localhost:{self.config.api_port}")
            logger.info(f"Mode: {'MOCK' if self.config.mock_mode else 'LIVE'}")
            logger.info(f"Registered agents: {list(self.agents.keys())}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start TruthForge system: {e}")
            return False
    
    def _run_api_server(self) -> None:
        """Run Flask API server."""
        try:
            self.flask_app.run(
                host='0.0.0.0',
                port=self.config.api_port,
                debug=self.config.debug,
                use_reloader=False  # Disable reloader in production
            )
        except Exception as e:
            logger.error(f"API server error: {e}")
    
    def stop(self) -> None:
        """Stop the TruthForge system gracefully."""
        logger.info("Stopping TruthForge system...")
        self.running = False
        
        # Stop agents
        for agent_name, agent in self.agents.items():
            try:
                logger.info(f"Stopping {agent_name}...")
                # Agents don't have explicit stop methods, but we could add cleanup here
            except Exception as e:
                logger.error(f"Error stopping {agent_name}: {e}")
        
        # Close database connection
        logger.info("Database connections closed")
        
        logger.info("TruthForge system stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status.
        
        Returns:
            Dict[str, Any]: System status information
        """
        agent_statuses = {}
        for agent_name, agent in self.agents.items():
            try:
                status = agent.health_check()
                agent_statuses[agent_name] = status.to_dict()
            except Exception as e:
                agent_statuses[agent_name] = {
                    "agent_id": agent.agent_id,
                    "status": "ERROR",
                    "error": str(e)
                }
        
        return {
            "system_status": "RUNNING" if self.running else "STOPPED",
            "mode": "MOCK" if self.config.mock_mode else "LIVE",
            "registered_agents": self.hol_registry.count_agents(),
            "agents": agent_statuses,
            "database_connected": test_connection(),
            "hedera_authenticated": self.hedera_client.authenticated if self.hedera_client else False
        }


def main():
    """Main entry point for TruthForge system."""
    logger.info("Starting TruthForge Reality-Verified Trade Platform")
    
    # Create and start system
    system = TruthForgeSystem()
    
    try:
        if system.start():
            logger.info("TruthForge system is running. Press Ctrl+C to stop.")
            
            # Keep main thread alive
            while system.running:
                try:
                    import time
                    time.sleep(1)
                except KeyboardInterrupt:
                    break
        else:
            logger.error("Failed to start TruthForge system")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        system.stop()


def create_wsgi_app():
    """
    Create and return the WSGI app for gunicorn.
    Heavy initialization (Hedera auth, agent registration) runs in a
    background thread so gunicorn workers start serving immediately.
    """
    import threading
    import os

    # Fast path: build Flask app with minimal deps so gunicorn starts immediately
    try:
        from database.database import init_db as _init_db
        _init_db()
    except Exception as e:
        logger.warning(f"DB init skipped at startup: {e}")

    _cfg = Config.load()
    _registry = HOLRegistry()

    # Minimal orchestrator stub so Flask can start without Hedera auth
    from agents.orchestrator_agent import OrchestratorAgent as _Orch
    _orch = _Orch(
        agent_id=os.getenv("AGENT_01_ID", "truthforge-orch-001"),
        capabilities=["workflow_coordination"],
        hcs_topic_id=_cfg.hcs_topic_id,
        config=_cfg,
        hedera_client=None,
    )

    flask_app = create_app(
        app_config=_cfg,
        orchestrator=_orch,
        hol_registry=_registry,
    )

    # Slow path: full system init (Hedera auth, agent DB upsert) in background
    def _full_init():
        try:
            system = TruthForgeSystem()
            if system.initialize():
                system.running = True
                logger.info("Full TruthForge system initialized in background")
            else:
                logger.error("Background TruthForge initialization failed")
        except Exception as e:
            logger.error(f"Background init error: {e}")

    threading.Thread(target=_full_init, daemon=True).start()
    return flask_app


# Module-level app for gunicorn: `gunicorn main:app`
app = create_wsgi_app()


if __name__ == "__main__":
    main()