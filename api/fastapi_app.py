"""
TruthForge FastAPI Application for WebSocket Support

This module provides WebSocket endpoints for real-time tracking
while maintaining compatibility with the existing Flask API.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from websocket.routes import router as websocket_router
from agents.config import Config

logger = logging.getLogger(__name__)


def create_fastapi_app(config: Config = None) -> FastAPI:
    """
    Create and configure FastAPI application for WebSocket support.
    
    Args:
        config: TruthForge configuration
        
    Returns:
        FastAPI: Configured FastAPI application
    """
    if config is None:
        config = Config()
    
    app = FastAPI(
        title="TruthForge WebSocket API",
        description="Real-time tracking and updates for TruthForge",
        version="2.0.0"
    )
    
    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store config
    app.state.config = config
    
    # Include WebSocket routes
    app.include_router(websocket_router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "websocket",
            "mock_mode": config.mock_mode
        }
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "TruthForge WebSocket API",
            "version": "2.0.0",
            "endpoints": {
                "tracking": "/ws/tracking/{shipment_id}",
                "port_clearance": "/ws/port/{port_id}/clearance",
                "global_dashboard": "/ws/dashboard/global",
                "metrics": "/ws/metrics/{metric_type}",
                "stats": "/ws/stats"
            }
        }
    
    logger.info(f"FastAPI app created (mock_mode={config.mock_mode})")
    
    return app


# Create app instance
app = create_fastapi_app()
