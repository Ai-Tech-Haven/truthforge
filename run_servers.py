"""
TruthForge Unified Server

Runs both Flask (REST API) and FastAPI (WebSocket) servers
in a production-ready configuration.
"""
import os
import logging
import asyncio
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_flask_server():
    """Run Flask REST API server"""
    try:
        from api.app import create_app
        from agents.config import Config
        from agents.orchestrator_agent import OrchestratorAgent
        from agents.hedera_client import HederaClient
        from hol_registry.registry import HOLRegistry
        
        # Initialize configuration
        config = Config()
        
        # Initialize Hedera client
        hedera_client = HederaClient(config)
        
        # Initialize HOL registry
        hol_registry = HOLRegistry(config)
        
        # Initialize orchestrator
        orchestrator = OrchestratorAgent(
            agent_id=config.agent_01_id,
            capabilities=["orchestration", "workflow", "coordination"],
            hcs_topic_id=config.agent_01_hcs_topic,
            config=config,
            hedera_client=hedera_client
        )
        
        # Create Flask app
        app = create_app(config, orchestrator, hol_registry)
        
        # Get port from config
        port = int(os.getenv('PORT', 5000))
        
        logger.info(f"Starting Flask server on port {port}")
        
        # Run Flask server
        app.run(
            host='0.0.0.0',
            port=port,
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Flask server error: {e}", exc_info=True)


def run_fastapi_server():
    """Run FastAPI WebSocket server"""
    try:
        import uvicorn
        from agents.config import Config
        
        # Initialize configuration
        config = Config()
        
        # Get WebSocket port from config
        ws_port = int(os.getenv('WS_PORT', 8000))
        ws_host = os.getenv('WS_HOST', '0.0.0.0')
        
        logger.info(f"Starting FastAPI WebSocket server on {ws_host}:{ws_port}")
        
        # Run FastAPI server
        uvicorn.run(
            "api.fastapi_app:app",
            host=ws_host,
            port=ws_port,
            log_level=os.getenv('LOG_LEVEL', 'info').lower(),
            reload=os.getenv('DEBUG', 'false').lower() == 'true'
        )
        
    except Exception as e:
        logger.error(f"FastAPI server error: {e}", exc_info=True)


def main():
    """Main entry point - runs both servers"""
    logger.info("=" * 60)
    logger.info("TruthForge Unified Server Starting")
    logger.info("=" * 60)
    
    # Display configuration
    logger.info(f"Mock Mode: {os.getenv('MOCK_MODE', 'true')}")
    logger.info(f"Flask Port: {os.getenv('PORT', 5000)}")
    logger.info(f"WebSocket Port: {os.getenv('WS_PORT', 8000)}")
    logger.info(f"Database: {os.getenv('DB_TYPE', 'sqlite')}")
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    logger.info("Flask server thread started")
    
    # Run FastAPI server in main thread
    # This blocks until server is stopped
    run_fastapi_server()


if __name__ == "__main__":
    main()
