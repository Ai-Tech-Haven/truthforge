"""
TruthForge Flask API Server

This module implements the REST API server for TruthForge, providing endpoints
for verification requests, status checks, agent discovery, dashboard metrics,
clearance queue, and WooCommerce webhooks. Updated for 5-agent system.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from functools import wraps

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from agents.config import Config
from agents.orchestrator_agent import OrchestratorAgent
from hol_registry.registry import HOLRegistry
from database.database import test_connection, get_stats


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(
    app_config: Config,
    orchestrator: OrchestratorAgent,
    hol_registry: HOLRegistry
) -> Flask:
    """
    Create and configure Flask application.
    
    Args:
        app_config: TruthForge configuration
        orchestrator: Orchestrator agent instance for request processing
        hol_registry: HOL registry for agent discovery
        
    Returns:
        Flask: Configured Flask application
    """
    import os
    
    # Set static folder to frontend directory
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Store references in app config
    app.config['TRUTHFORGE_CONFIG'] = app_config
    app.config['ORCHESTRATOR'] = orchestrator
    app.config['HOL_REGISTRY'] = hol_registry
    app.config['VERIFICATION_HISTORY'] = {}
    
    logger.info(f"Flask app created (mock_mode={app_config.mock_mode})")
    
    # Register WooCommerce webhook blueprint
    from woocommerce.webhooks.order_webhook import webhook_bp
    app.register_blueprint(webhook_bp)
    logger.info("WooCommerce webhook blueprint registered")
    
    # Register routes
    register_routes(app)
    

    @app.route('/api/operational/metrics', methods=['GET'])
    def get_operational_metrics():
        """GET /api/operational/metrics - Real-time chart data for operational oversight"""
        try:
            config = app.config['TRUTHFORGE_CONFIG']

            if not config.mock_mode:
                # LIVE MODE: build from real shipment data
                from database.services import ShipmentService
                from collections import defaultdict
                import calendar
                try:
                    shipments, _ = ShipmentService.list_shipments(limit=500, offset=0)
                    day_buckets = defaultdict(lambda: {"cleared": 0, "pending": 0, "flagged": 0})
                    for s in shipments:
                        if s.created_at:
                            day_name = calendar.day_abbr[s.created_at.weekday()]
                            status = (s.verification_status or "").lower()
                            if status in ("verified", "cleared"):
                                day_buckets[day_name]["cleared"] += 1
                            elif "flag" in status:
                                day_buckets[day_name]["flagged"] += 1
                            else:
                                day_buckets[day_name]["pending"] += 1
                    throughput = [
                        {"day": d, "cleared": v["cleared"], "pending": v["pending"], "flagged": v["flagged"]}
                        for d, v in day_buckets.items()
                    ]
                    # HCS data: empty until real HCS tracking is wired
                    return jsonify({"throughput": throughput, "hcs": []}), 200
                except Exception as e:
                    logger.error(f"Error fetching operational metrics: {e}")
                    # Return empty — never fall back to mock data in live mode
                    return jsonify({"throughput": [], "hcs": []}), 200

            # MOCK MODE: return sample chart data
            return jsonify({
                "throughput": [
                    {"day": "Mon", "cleared": 48, "pending": 5, "flagged": 2},
                    {"day": "Tue", "cleared": 52, "pending": 8, "flagged": 1},
                    {"day": "Wed", "cleared": 61, "pending": 4, "flagged": 3},
                    {"day": "Thu", "cleared": 55, "pending": 6, "flagged": 2},
                    {"day": "Fri", "cleared": 67, "pending": 3, "flagged": 1},
                    {"day": "Sat", "cleared": 42, "pending": 7, "flagged": 0},
                    {"day": "Sun", "cleared": 38, "pending": 2, "flagged": 1},
                ],
                "hcs": [
                    {"hour": "00:00", "messages": 42},
                    {"hour": "04:00", "messages": 28},
                    {"hour": "08:00", "messages": 95},
                    {"hour": "12:00", "messages": 134},
                    {"hour": "16:00", "messages": 178},
                    {"hour": "20:00", "messages": 112},
                    {"hour": "23:59", "messages": 67},
                ]
            }), 200

        except Exception as e:
            logger.error(f"Error retrieving operational metrics: {e}", exc_info=True)
            return handle_error("INTERNAL_ERROR", "An internal error occurred", 500)

    # ── Merchant auth endpoints ──────────────────────────────────────────────
    @app.route('/api/merchant/auth', methods=['POST'])
    def merchant_auth():
        """POST /api/merchant/auth - Sign in a merchant by site URL"""
        data = request.get_json(silent=True) or {}
        site = data.get("site", "https://a-thi.online")
        merchant = {
            "name": site.replace("https://", "").replace("http://", "").rstrip("/"),
            "logoUrl": f"{site.rstrip('/')}/wp-content/uploads/2024/01/cropped-a-thi-logo-192x192.png",
            "siteUrl": site,
        }
        return jsonify({"merchant": merchant, "status": "authenticated"}), 200

    @app.route('/api/merchant/logout', methods=['POST'])
    def merchant_logout():
        """POST /api/merchant/logout - Sign out merchant"""
        return jsonify({"status": "logged_out"}), 200

    # ── Carrier status endpoint ──────────────────────────────────────────────
    @app.route('/api/carrier/status', methods=['GET'])
    def carrier_status():
        """GET /api/carrier/status?carrier=fedex - Live carrier connection check"""
        carrier = request.args.get("carrier", "fedex").lower()
        config = app.config['TRUTHFORGE_CONFIG']
        if not config.mock_mode and carrier == "fedex":
            try:
                from agents.fedex_client import FedExClient
                client = FedExClient(config)
                ok = client.health_check() if hasattr(client, 'health_check') else True
                return jsonify({"carrier": carrier, "status": "connected" if ok else "disconnected"}), 200
            except Exception as e:
                logger.warning(f"FedEx health check failed: {e}")
                return jsonify({"carrier": carrier, "status": "disconnected"}), 200
        return jsonify({"carrier": carrier, "status": "connected"}), 200

    # ── HCS proof endpoint ───────────────────────────────────────────────────
    @app.route('/api/hcs/messages', methods=['GET'])
    def get_hcs_messages():
        """
        GET /api/hcs/messages?limit=20
        Returns recent HCS topic messages from the Hedera Mirror Node.
        In live mode: real on-chain messages with consensus timestamps.
        In mock mode: returns empty list (no real topic).
        """
        try:
            config = app.config['TRUTHFORGE_CONFIG']
            limit = min(int(request.args.get("limit", 20)), 100)
            topic_id = request.args.get("topic_id", config.hcs_topic_id)

            if config.mock_mode:
                return jsonify({
                    "topic_id": topic_id or "0.0.12345",
                    "network": config.hedera_network,
                    "messages": [],
                    "mock": True,
                    "note": "Switch to Live mode to see real HCS messages",
                }), 200

            # Live mode: fetch from mirror node
            network = config.hedera_network
            mirror_base = (
                "https://testnet.mirrornode.hedera.com"
                if network == "testnet"
                else "https://mainnet-public.mirrornode.hedera.com"
            )
            url = f"{mirror_base}/api/v1/topics/{topic_id}/messages"
            resp = requests.get(
                url,
                params={"limit": limit, "order": "desc"},
                timeout=10,
            )

            if resp.status_code == 200:
                raw_messages = resp.json().get("messages", [])
                messages = []
                for m in raw_messages:
                    import base64
                    decoded = ""
                    try:
                        decoded = base64.b64decode(m.get("message", "")).decode("utf-8")
                    except Exception:
                        decoded = m.get("message", "")

                    tx_id = m.get("transaction_id", "")
                    messages.append({
                        "sequence_number": m.get("sequence_number"),
                        "consensus_timestamp": m.get("consensus_timestamp"),
                        "transaction_id": tx_id,
                        "message": decoded,
                        "hashscan_url": (
                            f"https://hashscan.io/{network}/transaction/{tx_id}"
                            if tx_id else None
                        ),
                    })

                return jsonify({
                    "topic_id": topic_id,
                    "network": network,
                    "count": len(messages),
                    "messages": messages,
                    "topic_url": f"https://hashscan.io/{network}/topic/{topic_id}",
                }), 200
            else:
                logger.warning(f"Mirror node returned {resp.status_code} for topic {topic_id}")
                return jsonify({
                    "topic_id": topic_id,
                    "network": network,
                    "messages": [],
                    "error": f"Mirror node returned {resp.status_code}",
                }), 200

        except Exception as e:
            logger.error(f"Error fetching HCS messages: {e}", exc_info=True)
            return handle_error("INTERNAL_ERROR", "Failed to fetch HCS messages", 500)

    # Register error handlers
    register_error_handlers(app)
    
    return app


def require_auth(f):
    """
    Decorator to require authentication for protected endpoints.
    
    Validates the Authorization header token against the configured API token.
    Returns 401 Unauthorized if token is missing or invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import current_app
        
        config = current_app.config.get('TRUTHFORGE_CONFIG')
        
        # Skip auth check if no token is configured
        if not config or not config.api_auth_token:
            return f(*args, **kwargs)
        
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                "error": {
                    "code": "MISSING_AUTH_TOKEN",
                    "message": "Authorization header is required",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }), 401
        
        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                "error": {
                    "code": "INVALID_AUTH_FORMAT",
                    "message": "Authorization header must be in format: Bearer <token>",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }), 401
        
        token = parts[1]
        
        # Validate token
        if token != config.api_auth_token:
            return jsonify({
                "error": {
                    "code": "INVALID_AUTH_TOKEN",
                    "message": "Invalid authentication token",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def handle_error(error_code: str, message: str, status_code: int, details: Optional[Dict] = None) -> tuple:
    """
    Create standardized error response.
    
    Args:
        error_code: Error code identifier
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details (optional)
        
    Returns:
        tuple: (response_dict, status_code)
    """
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    return jsonify(error_response), status_code


def register_routes(app: Flask) -> None:
    """
    Register all API routes with the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/')
    def index():
        """Serve the frontend index.html"""
        from flask import send_from_directory
        import os
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        return send_from_directory(frontend_dir, 'index.html')
    
    @app.route('/api/verify', methods=['POST'])
    @require_auth
    def verify():
        """POST /api/verify - Submit verification request"""
        try:
            orchestrator = app.config['ORCHESTRATOR']
            verification_history = app.config['VERIFICATION_HISTORY']
            
            # Parse request body
            data = request.get_json(silent=True)
            
            if not data:
                return handle_error(
                    "INVALID_REQUEST",
                    "Request body is required",
                    400
                )
            
            # Handle natural language message from frontend
            message = data.get('message')
            if message:
                # Convert natural language to structured request
                data = {
                    "type": "natural_language",
                    "message": message,
                    "timestamp": data.get('timestamp', datetime.now(timezone.utc).isoformat())
                }
            else:
                # Validate action for structured requests
                action = data.get('action')
                if not action:
                    return handle_error(
                        "MISSING_ACTION",
                        "Either 'message' or 'action' field is required",
                        400,
                        {"field": "action"}
                    )
                
                # Convert to orchestrator format
                data['type'] = 'verification'
            
            # Generate request ID
            request_id = str(uuid.uuid4())
            data['request_id'] = request_id
            
            logger.info(f"Processing verification request {request_id}: {data.get('type', 'unknown')}")
            
            # Process request through orchestrator
            result = orchestrator.process_request(data)
            
            # Store in history
            verification_history[request_id] = {
                "request": data,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "completed" if result.get("success", False) else "error"
            }
            
            # Return response with natural language response if available
            response = {
                "request_id": request_id,
                "status": "completed" if result.get("success", False) else "error",
                "success": result.get("success", False)
            }
            
            # Add natural language response if available
            if "natural_language_response" in result:
                response["response"] = result["natural_language_response"]
            
            # Add unified report if available
            if "unified_report" in result:
                response["unified_report"] = result["unified_report"]
            elif "error" not in result and result.get("success"):
                response["verification_result"] = result
            
            # Add error if present
            if "error" in result:
                response["error"] = result["error"]
            
            return jsonify(response), 200
        
        except Exception as e:
            logger.error(f"Error processing verification request: {e}", exc_info=True)
            return handle_error(
                "INTERNAL_ERROR",
                "An internal error occurred while processing the request",
                500,
                {"error_type": type(e).__name__}
            )
    
    @app.route('/api/status/<request_id>', methods=['GET'])
    def get_status(request_id: str):
        """GET /api/status/<request_id> - Get verification status"""
        try:
            verification_history = app.config['VERIFICATION_HISTORY']
            
            # Check if request exists in history
            if request_id not in verification_history:
                return handle_error(
                    "REQUEST_NOT_FOUND",
                    f"Request {request_id} not found",
                    404,
                    {"request_id": request_id}
                )
            
            # Get verification data
            verification = verification_history[request_id]
            
            response = {
                "request_id": request_id,
                "status": verification["status"],
                "timestamp": verification["timestamp"]
            }
            
            # Include result if completed
            if verification["status"] in ["completed", "error"]:
                response["result"] = verification["result"]
            
            return jsonify(response), 200
        
        except Exception as e:
            logger.error(f"Error retrieving status for {request_id}: {e}", exc_info=True)
            return handle_error(
                "INTERNAL_ERROR",
                "An internal error occurred while retrieving status",
                500
            )
    
    @app.route('/api/history', methods=['GET'])
    @require_auth
    def get_history():
        """GET /api/history - Get verification history"""
        try:
            verification_history = app.config['VERIFICATION_HISTORY']
            
            # Get pagination parameters
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            # Validate parameters
            if limit < 1 or limit > 100:
                return handle_error(
                    "INVALID_LIMIT",
                    "Limit must be between 1 and 100",
                    400,
                    {"limit": limit}
                )
            
            if offset < 0:
                return handle_error(
                    "INVALID_OFFSET",
                    "Offset must be >= 0",
                    400,
                    {"offset": offset}
                )
            
            # Get all verifications sorted by timestamp (newest first)
            all_verifications = sorted(
                [
                    {
                        "request_id": req_id,
                        "action": v["request"].get("action"),
                        "status": v["status"],
                        "timestamp": v["timestamp"]
                    }
                    for req_id, v in verification_history.items()
                ],
                key=lambda x: x["timestamp"],
                reverse=True
            )
            
            # Apply pagination
            paginated = all_verifications[offset:offset + limit]
            
            response = {
                "verifications": paginated,
                "total": len(all_verifications),
                "limit": limit,
                "offset": offset
            }
            
            return jsonify(response), 200
        
        except ValueError as e:
            return handle_error(
                "INVALID_PARAMETER",
                "Invalid query parameter",
                400,
                {"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Error retrieving history: {e}", exc_info=True)
            return handle_error(
                "INTERNAL_ERROR",
                "An internal error occurred while retrieving history",
                500
            )
    
    @app.route('/api/agents', methods=['GET'])
    def get_agents():
        """GET /api/agents - Get registered agent status"""
        try:
            import os
            config = app.config['TRUTHFORGE_CONFIG']

            # ── Canonical 5-agent list sourced directly from env vars ──────────
            # This is always fast — no DB, no HOL registry, no network calls.
            # The env vars are set at deploy time from .env / Railway variables.
            CANONICAL_AGENTS = [
                {
                    "id": "agent-001",
                    "name": "Orchestrator Agent",
                    "agentId": os.getenv("AGENT_01_ID", "truthforge-orch-001"),
                    "uaid": os.getenv("AGENT_01_UAID", ""),
                    "hcsTopic": os.getenv("AGENT_01_HCS_TOPIC", "0.0.8161244"),
                    "primaryFunction": "Workflow coordination and decision execution",
                    "capabilities": ["workflow_coordination", "decision_execution", "agent_routing"],
                },
                {
                    "id": "agent-002",
                    "name": "Verification & Compliance Agent",
                    "agentId": os.getenv("AGENT_02_ID", "truthforge-verify-001"),
                    "uaid": os.getenv("AGENT_02_UAID", ""),
                    "hcsTopic": os.getenv("AGENT_02_HCS_TOPIC", "0.0.8161247"),
                    "primaryFunction": "Document validation and compliance assessment",
                    "capabilities": ["document_validation", "compliance_assessment", "deepfake_detection"],
                },
                {
                    "id": "agent-003",
                    "name": "Carrier Adapter Agent (Council-Grade)",
                    "agentId": os.getenv("AGENT_03_ID", "truthforge-carrier-001"),
                    "uaid": os.getenv("AGENT_03_UAID", ""),
                    "hcsTopic": os.getenv("AGENT_03_HCS_TOPIC", "0.0.8161248"),
                    "primaryFunction": "Carrier data ingestion and normalization",
                    "capabilities": ["carrier_data_ingestion", "data_normalization", "multi_carrier_support"],
                },
                {
                    "id": "agent-004",
                    "name": "Registry & Discovery Agent",
                    "agentId": os.getenv("AGENT_04_ID", "truthforge-registry-001"),
                    "uaid": os.getenv("AGENT_04_UAID", ""),
                    "hcsTopic": os.getenv("AGENT_04_HCS_TOPIC", "0.0.8161249"),
                    "primaryFunction": "Agent discovery, health reporting, registry sync",
                    "capabilities": ["agent_discovery", "health_reporting", "registry_sync"],
                },
                {
                    "id": "agent-005",
                    "name": "Evidence & Settlement Agent",
                    "agentId": os.getenv("AGENT_05_ID", "truthforge-evidence-001"),
                    "uaid": os.getenv("AGENT_05_UAID", ""),
                    "hcsTopic": os.getenv("AGENT_05_HCS_TOPIC", "0.0.8161250"),
                    "primaryFunction": "Consensus submission and audit reference generation",
                    "capabilities": ["consensus_submission", "audit_reference_generation", "settlement_processing"],
                },
            ]

            # ── Try to enrich with live DB health/status (non-blocking) ────────
            db_health: dict = {}
            if not config.mock_mode:
                try:
                    from database.services import AgentService
                    db_agents = AgentService.list_agents()
                    db_health = {
                        a.agent_id: {
                            "status": a.status,
                            "health": a.health_score,
                            "lastActive": a.last_heartbeat.strftime("%H:%M:%S") if a.last_heartbeat else None,
                        }
                        for a in db_agents
                    }
                except Exception as e:
                    logger.warning(f"DB agent enrichment skipped: {e}")

            # ── Build response ───────────────────────────────────────────────
            agent_list = []
            for a in CANONICAL_AGENTS:
                live = db_health.get(a["agentId"], {})
                raw_status = live.get("status", "online")
                status = "online" if raw_status in ("online", "active", "ONLINE") else "offline"
                agent_list.append({
                    "id": a["id"],
                    "name": a["name"],
                    "agentId": a["agentId"],
                    "uaid": a["uaid"],
                    "hcsTopic": a["hcsTopic"],
                    "status": status,
                    "health": live.get("health") or 95,
                    "lastActive": live.get("lastActive") or "Active now",
                    "primaryFunction": a["primaryFunction"],
                    "capabilities": a["capabilities"],
                    "endpoints": [],
                })

            return jsonify({"agents": agent_list, "count": len(agent_list)}), 200

        except Exception as e:
            logger.error(f"Error retrieving agents: {e}", exc_info=True)
            return handle_error("INTERNAL_ERROR", "An internal error occurred while retrieving agents", 500)
    
    @app.route('/api/dashboard/metrics', methods=['GET'])
    def get_dashboard_metrics():
        """GET /api/dashboard/metrics - Get operational metrics for dashboard"""
        try:
            config = app.config['TRUTHFORGE_CONFIG']
            
            # Get metrics from database or return mock data
            if not config.mock_mode:
                # LIVE MODE: Use database
                from database.services import MetricsService
                
                try:
                    metrics_record = MetricsService.get_latest_metrics()
                    if not metrics_record:
                        # Calculate fresh metrics if none exist
                        metrics_record = MetricsService.calculate_and_store_metrics()
                    
                    return jsonify(metrics_record.to_dict()), 200
                except Exception as e:
                    logger.error(f"Error fetching live metrics: {e}")
                    # Fallback to mock on error
                    pass
            
            if config.mock_mode:
                # Return mock metrics matching frontend structure
                metrics = {
                    "totalVerifications": 12847,
                    "avgClearanceTime": "3.2 min",
                    "costSavings": "$2.4M", 
                    "activeAgents": 5,
                    "successRate": 99.7,
                    "shipmentsToday": 342,
                    "documentsPreArrival": 8421,
                    "shipmentsPreCleared": 6293
                }
            else:
                # Use mock metrics for now since database queries need to be updated
                metrics = {
                    "totalVerifications": 0,
                    "avgClearanceTime": "0 min",
                    "costSavings": "$0",
                    "activeAgents": 5,
                    "successRate": 0,
                    "shipmentsToday": 0,
                    "documentsPreArrival": 0,
                    "shipmentsPreCleared": 0
                }
            
            return jsonify(metrics), 200
            
        except Exception as e:
            logger.error(f"Error retrieving dashboard metrics: {e}", exc_info=True)
            return handle_error(
                "INTERNAL_ERROR",
                "An internal error occurred while retrieving metrics",
                500
            )
    
    @app.route('/api/clearance/queue', methods=['GET'])
    def get_clearance_queue():
        """GET /api/clearance/queue - Get pre-arrival clearance queue"""
        try:
            config = app.config['TRUTHFORGE_CONFIG']
            
            # Get pagination parameters
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            if not config.mock_mode:
                # LIVE MODE: Use database
                from database.services import ShipmentService
                
                try:
                    shipments, total = ShipmentService.list_shipments(limit=limit, offset=offset)
                    
                    shipment_list = []
                    for shipment in shipments:
                        shipment_data = {
                            "id": shipment.shipment_id,
                            "carrier": shipment.carrier or "Unknown",
                            "vessel": shipment.vessel_name or "Unknown",
                            "origin": shipment.origin_port or "Unknown",
                            "destination": shipment.destination_port or "Unknown",
                            "status": shipment.verification_status.title() if shipment.verification_status else "Pending",
                            "eta": f"T-{((shipment.estimated_arrival - datetime.now(timezone.utc)).total_seconds() / 3600):.0f}h" if shipment.estimated_arrival else "Unknown",
                            "fedexTracking": shipment.tracking_number,
                            "woocommerceOrder": shipment.order_id
                        }
                        shipment_list.append(shipment_data)
                    
                    return jsonify({
                        "shipments": shipment_list,
                        "total": total,
                        "limit": limit,
                        "offset": offset,
                        "live": True,
                        "empty_reason": None if shipment_list else "No shipments in database yet"
                    }), 200
                except Exception as e:
                    logger.error(f"Error fetching live shipments: {e}")
                    # Return live-connected empty response — never fall back to mock
                    return jsonify({
                        "shipments": [],
                        "total": 0,
                        "limit": limit,
                        "offset": offset,
                        "live": True,
                        "empty_reason": "Database unavailable — no shipments loaded yet"
                    }), 200
            
            # MOCK MODE
            mock_shipments = [
                {
                    "id": "SHP-8821A",
                    "carrier": "Maersk",
                    "vessel": "Mumbai Maersk",
                    "origin": "Shanghai, CN",
                    "destination": "Los Angeles, US",
                    "status": "Verified",
                    "eta": "T-14h",
                    "fedexTracking": "7749 1234 5678",
                    "woocommerceOrder": "WC-10234"
                },
                {
                    "id": "SHP-8822B",
                    "carrier": "MSC",
                    "vessel": "MSC Oscar",
                    "origin": "Rotterdam, NL",
                    "destination": "New York, US",
                    "status": "Pending Consensus",
                    "eta": "T-18h",
                    "woocommerceOrder": "WC-10235"
                },
                {
                    "id": "SHP-8823C",
                    "carrier": "CMA CGM",
                    "vessel": "Jade",
                    "origin": "Tokyo, JP",
                    "destination": "Chicago, US",
                    "status": "Flagged Exception",
                    "eta": "T-22h"
                },
                {
                    "id": "SHP-8824D",
                    "carrier": "FedEx",
                    "vessel": "FX992 (Air)",
                    "origin": "Mumbai, IN",
                    "destination": "London, UK",
                    "status": "Verified",
                    "eta": "T-04h"
                }
            ]

            # Apply pagination
            paginated_shipments = mock_shipments[offset:offset + limit]

            return jsonify({
                "shipments": paginated_shipments,
                "total": len(mock_shipments),
                "limit": limit,
                "offset": offset,
                "live": False
            }), 200
            
        except ValueError as e:
            return handle_error(
                "INVALID_PARAMETER",
                "Invalid query parameter",
                400,
                {"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Error retrieving clearance queue: {e}", exc_info=True)
            return handle_error(
                "INTERNAL_ERROR",
                "An internal error occurred while retrieving clearance queue",
                500
            )
    
    @app.route('/api/port-trust-receipts', methods=['GET'])
    def get_port_trust_receipts():
        """GET /api/port-trust-receipts - Get port trust receipts"""
        try:
            config = app.config['TRUTHFORGE_CONFIG']
            
            # Get query parameters
            shipment_id = request.args.get('shipment_id')
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            if not config.mock_mode:
                # LIVE MODE: query DB for real receipts
                try:
                    receipts_list: list = []
                    try:
                        from database import models
                        from database.database import db_session
                        if hasattr(models, 'PortTrustReceipt'):
                            q = db_session.query(models.PortTrustReceipt)
                            if shipment_id:
                                q = q.filter(models.PortTrustReceipt.shipment_id == shipment_id)
                            rows = q.offset(offset).limit(limit).all()
                            receipts_list = [r.to_dict() for r in rows if hasattr(r, 'to_dict')]
                    except Exception:
                        pass  # table doesn't exist yet

                    return jsonify({
                        "receipts": receipts_list,
                        "total": len(receipts_list),
                        "limit": limit,
                        "offset": offset,
                        "live": True,
                        "empty_reason": None if receipts_list else "No trust receipts issued yet"
                    }), 200
                except Exception as e:
                    logger.error(f"Error fetching live receipts: {e}")
                    return jsonify({
                        "receipts": [],
                        "total": 0,
                        "limit": limit,
                        "offset": offset,
                        "live": True,
                        "empty_reason": "Database unavailable"
                    }), 200

            # MOCK MODE
            mock_receipts = [
                {
                    "id": "PTR-001",
                    "shipmentId": "SHP-8821A",
                    "clearanceStatus": "cleared",
                    "agentSignatures": [
                        {"agentName": "Orchestrator Agent", "agentId": "truthforge-orch-001"},
                        {"agentName": "Verification & Compliance Agent", "agentId": "truthforge-verify-001"},
                        {"agentName": "Carrier Adapter Agent (Council-Grade)", "agentId": "truthforge-carrier-001"},
                        {"agentName": "Registry & Discovery Agent", "agentId": "truthforge-registry-001"},
                        {"agentName": "Evidence & Settlement Agent", "agentId": "truthforge-evidence-001"}
                    ],
                    "hederaTxRef": "0.0.453211@1698754321.123456789",
                    "issuedAt": "2024-01-15 14:35:00",
                    "vessel": "Mumbai Maersk",
                    "port": "Port of Los Angeles"
                },
                {
                    "id": "PTR-002",
                    "shipmentId": "SHP-8824D",
                    "clearanceStatus": "cleared",
                    "agentSignatures": [
                        {"agentName": "Orchestrator Agent", "agentId": "truthforge-orch-001"},
                        {"agentName": "Verification & Compliance Agent", "agentId": "truthforge-verify-001"},
                        {"agentName": "Evidence & Settlement Agent", "agentId": "truthforge-evidence-001"}
                    ],
                    "hederaTxRef": "0.0.453211@1698754400.987654321",
                    "issuedAt": "2024-01-14 09:12:00",
                    "vessel": "FX992 (Air)",
                    "port": "Port of Felixstowe"
                }
            ]

            if shipment_id:
                mock_receipts = [r for r in mock_receipts if r["shipmentId"] == shipment_id]

            paginated_receipts = mock_receipts[offset:offset + limit]
            return jsonify({
                "receipts": paginated_receipts,
                "total": len(mock_receipts),
                "limit": limit,
                "offset": offset,
                "live": False
            }), 200
            
        except ValueError as e:
            return handle_error(
                "INVALID_PARAMETER",
                "Invalid query parameter",
                400,
                {"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Error retrieving port trust receipts: {e}", exc_info=True)
            return handle_error(
                "INTERNAL_ERROR",
                "An internal error occurred while retrieving port trust receipts",
                500
            )
    
    @app.route('/api/woocommerce/webhook', methods=['POST'])
    def woocommerce_webhook():
        """POST /api/woocommerce/webhook - Receive WooCommerce webhooks"""
        try:
            config = app.config['TRUTHFORGE_CONFIG']
            orchestrator = app.config['ORCHESTRATOR']
            verification_history = app.config['VERIFICATION_HISTORY']
            
            # Get webhook signature
            signature = request.headers.get('X-WC-Webhook-Signature')
            
            # Validate signature if webhook secret is configured
            if config.woocommerce_webhook_secret:
                if not signature:
                    return handle_error(
                        "MISSING_SIGNATURE",
                        "X-WC-Webhook-Signature header is required",
                        401
                    )
                
                # TODO: Implement signature validation
                # For now, we'll accept all webhooks in development
                logger.warning("Webhook signature validation not yet implemented")
            
            # Parse webhook payload
            payload = request.get_json(silent=True)
            
            if not payload:
                return handle_error(
                    "INVALID_PAYLOAD",
                    "Webhook payload is required",
                    400
                )
            
            # Extract order ID
            order_id = payload.get('id')
            if not order_id:
                return handle_error(
                    "MISSING_ORDER_ID",
                    "Order ID not found in webhook payload",
                    400,
                    {"payload_keys": list(payload.keys())}
                )
            
            logger.info(f"Received WooCommerce webhook for order {order_id}")
            
            # Queue verification request
            verification_request = {
                "action": "verify_order",
                "order_id": str(order_id),
                "source": "woocommerce_webhook",
                "webhook_payload": payload
            }
            
            # Process asynchronously (for now, process synchronously)
            # TODO: Implement async queue processing
            request_id = str(uuid.uuid4())
            verification_request['request_id'] = request_id
            
            result = orchestrator.process_request(verification_request)
            
            # Store in history
            verification_history[request_id] = {
                "request": verification_request,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "completed" if "error" not in result else "error"
            }
            
            # Return 200 OK to acknowledge webhook
            return jsonify({
                "status": "received",
                "request_id": request_id,
                "order_id": str(order_id)  # Ensure order_id is string
            }), 200
        
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            # Still return 200 to prevent webhook retries
            return jsonify({
                "status": "error",
                "message": "Webhook received but processing failed"
            }), 200
    
    @app.route('/api/verifications', methods=['GET'])
    def get_verifications():
        """GET /api/verifications - Get verification history"""
        try:
            config = app.config['TRUTHFORGE_CONFIG']
            
            # Get pagination parameters
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            shipment_id = request.args.get('shipment_id')
            
            if config.mock_mode:
                # Return mock verification data matching frontend structure
                mock_verifications = [
                    {
                        "id": "v-001",
                        "shipmentId": "SHP-8821A",
                        "type": "Bill of Lading",
                        "status": "verified",
                        "agent": "Verification & Compliance Agent",
                        "timestamp": "2024-01-15 14:32:00",
                        "hcsProof": "hcs-verify-001#1705312320",
                        "confidence": 99.7
                    },
                    {
                        "id": "v-002",
                        "shipmentId": "SHP-8822B",
                        "type": "Customs Declaration",
                        "status": "pending",
                        "agent": "Verification & Compliance Agent",
                        "timestamp": "2024-01-15 14:28:00",
                        "hcsProof": "pending",
                        "confidence": 0
                    },
                    {
                        "id": "v-003",
                        "shipmentId": "SHP-8823C",
                        "type": "Certificate of Origin",
                        "status": "failed",
                        "agent": "Verification & Compliance Agent",
                        "timestamp": "2024-01-15 14:25:00",
                        "hcsProof": "N/A",
                        "confidence": 23.4
                    },
                    {
                        "id": "v-004",
                        "shipmentId": "SHP-8824D",
                        "type": "Phytosanitary Cert",
                        "status": "verified",
                        "agent": "Verification & Compliance Agent",
                        "timestamp": "2024-01-15 14:20:00",
                        "hcsProof": "hcs-verify-001#1705311600",
                        "confidence": 99.1
                    },
                    {
                        "id": "v-005",
                        "shipmentId": "SHP-8821A",
                        "type": "Commercial Invoice",
                        "status": "verified",
                        "agent": "Orchestrator Agent",
                        "timestamp": "2024-01-15 14:15:00",
                        "hcsProof": "hcs-orch-001#1705311300",
                        "confidence": 97.8
                    },
                    {
                        "id": "v-006",
                        "shipmentId": "SHP-8824D",
                        "type": "Packing List",
                        "status": "verified",
                        "agent": "Carrier Adapter Agent (Council-Grade)",
                        "timestamp": "2024-01-15 14:10:00",
                        "hcsProof": "hcs-carrier-001#1705311000",
                        "confidence": 98.2
                    }
                ]
                
                # Filter by shipment ID if provided
                if shipment_id:
                    mock_verifications = [v for v in mock_verifications if v["shipmentId"] == shipment_id]
                
                # Apply pagination
                paginated_verifications = mock_verifications[offset:offset + limit]
                
                response = {
                    "verifications": paginated_verifications,
                    "total": len(mock_verifications),
                    "limit": limit,
                    "offset": offset
                }
            else:
                # Use mock data for now since database queries need to be updated
                response = {
                    "verifications": [],
                    "total": 0,
                    "limit": limit,
                    "offset": offset
                }
            
            return jsonify(response), 200
            
        except ValueError as e:
            return handle_error(
                "INVALID_PARAMETER",
                "Invalid query parameter",
                400,
                {"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Error retrieving verifications: {e}", exc_info=True)
            return handle_error(
                "INTERNAL_ERROR",
                "An internal error occurred while retrieving verifications",
                500
            )
    
    @app.route('/api/status/system', methods=['GET'])
    def system_status():
        """GET /api/status/system - Get system status"""
        config = app.config.get('TRUTHFORGE_CONFIG')
        hol_registry = app.config.get('HOL_REGISTRY')
        
        # Get agent count
        agent_count = 0
        if hol_registry:
            agents = hol_registry.query_agents()
            agent_count = len(agents)
        
        # Check database connection
        db_connected = test_connection()
        
        # Get database stats
        db_stats = get_stats()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "live" if not config.mock_mode else "mock",
            "mock_mode": config.mock_mode if config else True,
            "agent_count": agent_count,
            "expected_agents": 5,
            "database_connected": db_connected,
            "database_type": db_stats.get('type'),
            "hedera_network": config.hedera_network if config else "unknown",
            "version": "2.0.0"
        }), 200
    
    @app.route('/api/mode', methods=['GET'])
    def get_mode():
        """GET /api/mode - Get current operating mode"""
        config = app.config.get('TRUTHFORGE_CONFIG')
        return jsonify({
            "mode": "live" if not config.mock_mode else "mock",
            "mock_mode": config.mock_mode,
            "can_toggle": True,
            "description": "Mock mode uses simulated data. Live mode uses real Hedera blockchain and database."
        }), 200
    
    @app.route('/api/health/db')
    def db_health():
        """Database health check endpoint"""
        status = test_connection()
        stats = get_stats()
        
        return jsonify({
            'status': 'healthy' if status else 'unhealthy',
            'database': stats,
            'mock_mode': app.config['TRUTHFORGE_CONFIG'].mock_mode,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """GET /health - Health check endpoint"""
        config = app.config.get('TRUTHFORGE_CONFIG')
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mock_mode": config.mock_mode if config else True
        }), 200
    
    @app.route('/api/v1/keys/generate', methods=['POST'])
    def generate_api_key_endpoint():
        """
        POST /api/v1/keys/generate - Generate a new API key (demo/testing only)
        
        Request body:
        {
            "name": "My API Key",
            "role": "port_authority" | "enterprise" | "admin",
            "created_by": "admin_user" (optional)
        }
        
        Response:
        {
            "api_key": "plain_text_key_here",
            "key_info": {
                "name": "My API Key",
                "role": "port_authority",
                "created_at": "2024-01-15T14:32:00Z",
                "is_active": true
            },
            "warning": "Store this key securely. It will not be shown again."
        }
        """
        try:
            from utils.api_keys import create_api_key
            from database.api_keys import APIKeyRole
            
            data = request.get_json(silent=True)
            
            if not data:
                return handle_error(
                    "INVALID_REQUEST",
                    "Request body is required",
                    400
                )
            
            # Validate required fields
            name = data.get('name')
            role_str = data.get('role', 'enterprise')
            created_by = data.get('created_by')
            
            if not name:
                return handle_error(
                    "MISSING_FIELD",
                    "Field 'name' is required",
                    400,
                    {"field": "name"}
                )
            
            # Parse role
            try:
                role = APIKeyRole[role_str.upper()]
            except (KeyError, AttributeError):
                return handle_error(
                    "INVALID_ROLE",
                    f"Invalid role. Must be one of: {', '.join(r.value for r in APIKeyRole)}",
                    400,
                    {"provided_role": role_str, "valid_roles": [r.value for r in APIKeyRole]}
                )
            
            # Generate API key
            plain_key, api_key_record = create_api_key(
                name=name,
                role=role,
                created_by=created_by
            )
            
            logger.info(f"Generated new API key: {name} (role: {role.value})")
            
            return jsonify({
                "api_key": plain_key,
                "key_info": {
                    "name": api_key_record.name,
                    "role": api_key_record.role.value,
                    "created_at": api_key_record.created_at.isoformat(),
                    "is_active": api_key_record.is_active,
                    "created_by": api_key_record.created_by
                },
                "warning": "Store this key securely. It will not be shown again."
            }), 201
        
        except Exception as e:
            logger.error(f"Error generating API key: {e}", exc_info=True)
            return handle_error(
                "INTERNAL_ERROR",
                "An internal error occurred while generating API key",
                500,
                {"error_type": type(e).__name__}
            )
    
    # ─── Integration State (in-memory store, replace with DB in production) ──────
    _integration_state: Dict[str, Any] = {
        "hedera": {"connected": True, "detail": "Testnet — HCS Topics Active"},
        "carrier_council": {"connected": True, "detail": "Council-grade data adapters enabled"},
        "woocommerce": {"connected": True, "detail": "REST API — a-thi.online"},
        "fedex": {"connected": True, "detail": "FedEx Ship API"},
        "webhooks": {
            "merchant_url": "",
            "carrier_url": "",
            "port_authority_url": "",
        },
    }

    @app.route('/api/integrations/status', methods=['GET'])
    def get_integrations_status():
        """GET /api/integrations/status — Return live integration states"""
        return jsonify({
            "hedera": _integration_state["hedera"],
            "carrier_council": _integration_state["carrier_council"],
            "woocommerce": _integration_state["woocommerce"],
            "fedex": _integration_state["fedex"],
            "webhooks": _integration_state["webhooks"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 200

    @app.route('/api/integrations/hedera/connect', methods=['POST'])
    def hedera_connect():
        _integration_state["hedera"]["connected"] = True
        _integration_state["hedera"]["detail"] = "Testnet — HCS Topics Active"
        logger.info("Hedera connected")
        return jsonify({"success": True, "state": _integration_state["hedera"]}), 200

    @app.route('/api/integrations/hedera/disconnect', methods=['POST'])
    def hedera_disconnect():
        _integration_state["hedera"]["connected"] = False
        _integration_state["hedera"]["detail"] = "Disconnected"
        logger.info("Hedera disconnected")
        return jsonify({"success": True, "state": _integration_state["hedera"]}), 200

    @app.route('/api/integrations/carrier-council/connect', methods=['POST'])
    def carrier_council_connect():
        _integration_state["carrier_council"]["connected"] = True
        _integration_state["carrier_council"]["detail"] = "Council-grade data adapters enabled"
        logger.info("Carrier Council connected")
        return jsonify({"success": True, "state": _integration_state["carrier_council"]}), 200

    @app.route('/api/integrations/carrier-council/disconnect', methods=['POST'])
    def carrier_council_disconnect():
        _integration_state["carrier_council"]["connected"] = False
        _integration_state["carrier_council"]["detail"] = "Disconnected"
        logger.info("Carrier Council disconnected")
        return jsonify({"success": True, "state": _integration_state["carrier_council"]}), 200

    @app.route('/api/integrations/woocommerce/connect', methods=['POST'])
    def woocommerce_connect():
        _integration_state["woocommerce"]["connected"] = True
        _integration_state["woocommerce"]["detail"] = "REST API — a-thi.online"
        logger.info("WooCommerce connected")
        return jsonify({"success": True, "state": _integration_state["woocommerce"]}), 200

    @app.route('/api/integrations/woocommerce/disconnect', methods=['POST'])
    def woocommerce_disconnect():
        _integration_state["woocommerce"]["connected"] = False
        _integration_state["woocommerce"]["detail"] = "Disconnected"
        logger.info("WooCommerce disconnected")
        return jsonify({"success": True, "state": _integration_state["woocommerce"]}), 200

    @app.route('/api/integrations/fedex/connect', methods=['POST'])
    def fedex_connect():
        _integration_state["fedex"]["connected"] = True
        _integration_state["fedex"]["detail"] = "FedEx Ship API"
        logger.info("FedEx connected")
        return jsonify({"success": True, "state": _integration_state["fedex"]}), 200

    @app.route('/api/integrations/fedex/disconnect', methods=['POST'])
    def fedex_disconnect():
        _integration_state["fedex"]["connected"] = False
        _integration_state["fedex"]["detail"] = "Disconnected"
        logger.info("FedEx disconnected")
        return jsonify({"success": True, "state": _integration_state["fedex"]}), 200

    @app.route('/api/integrations/webhook/configure', methods=['POST'])
    def configure_webhooks():
        """POST /api/integrations/webhook/configure — Save webhook URLs"""
        data = request.get_json(silent=True) or {}
        if "merchant_url" in data:
            _integration_state["webhooks"]["merchant_url"] = data["merchant_url"]
        if "carrier_url" in data:
            _integration_state["webhooks"]["carrier_url"] = data["carrier_url"]
        if "port_authority_url" in data:
            _integration_state["webhooks"]["port_authority_url"] = data["port_authority_url"]
        logger.info(f"Webhook URLs updated: {_integration_state['webhooks']}")
        return jsonify({"success": True, "webhooks": _integration_state["webhooks"]}), 200

    # ─────────────────────────────────────────────────────────────────────────────

    @app.route('/api/v1/proof/<shipment_id>', methods=['GET'])
    def get_shipment_proof(shipment_id: str):
        """
        GET /api/v1/proof/<shipment_id> - Get verification proof for a shipment
        
        This endpoint returns the complete verification proof package for a shipment,
        including all agent verifications, consensus data, and Hedera transaction references.
        
        Response:
        {
            "shipment_id": "SHP-8821A",
            "status": "verified",
            "proof": {
                "port_trust_receipt": {...},
                "verifications": [...],
                "hedera_references": [...],
                "consensus_timestamp": "2024-01-15T14:35:00Z"
            }
        }
        """
        try:
            from api.auth import optional_auth
            
            config = app.config['TRUTHFORGE_CONFIG']
            verification_history = app.config['VERIFICATION_HISTORY']
            
            logger.info(f"Proof request for shipment: {shipment_id}")
            
            if config.mock_mode:
                # Return mock proof data
                mock_proofs = {
                    "SHP-8821A": {
                        "shipment_id": "SHP-8821A",
                        "status": "verified",
                        "proof": {
                            "port_trust_receipt": {
                                "id": "PTR-001",
                                "shipmentId": "SHP-8821A",
                                "clearanceStatus": "cleared",
                                "vessel": "Mumbai Maersk",
                                "port": "Port of Los Angeles",
                                "issuedAt": "2024-01-15 14:35:00",
                                "hederaTxRef": "0.0.453211@1698754321.123456789",
                                "agentSignatures": [
                                    {"agentName": "Orchestrator Agent", "agentId": "truthforge-orch-001"},
                                    {"agentName": "Verification & Compliance Agent", "agentId": "truthforge-verify-001"},
                                    {"agentName": "Carrier Adapter Agent (Council-Grade)", "agentId": "truthforge-carrier-001"},
                                    {"agentName": "Registry & Discovery Agent", "agentId": "truthforge-registry-001"},
                                    {"agentName": "Evidence & Settlement Agent", "agentId": "truthforge-evidence-001"}
                                ]
                            },
                            "verifications": [
                                {
                                    "type": "Bill of Lading",
                                    "status": "verified",
                                    "confidence": 99.7,
                                    "agent": "Verification & Compliance Agent",
                                    "timestamp": "2024-01-15 14:32:00",
                                    "hcsProof": "hcs-verify-001#1705312320"
                                },
                                {
                                    "type": "Commercial Invoice",
                                    "status": "verified",
                                    "confidence": 97.8,
                                    "agent": "Orchestrator Agent",
                                    "timestamp": "2024-01-15 14:15:00",
                                    "hcsProof": "hcs-orch-001#1705311300"
                                }
                            ],
                            "hedera_references": [
                                {
                                    "topic_id": "0.0.453211",
                                    "sequence_number": 1234,
                                    "consensus_timestamp": "1698754321.123456789",
                                    "message_type": "verification_result"
                                },
                                {
                                    "topic_id": "0.0.453211",
                                    "sequence_number": 1235,
                                    "consensus_timestamp": "1698754400.987654321",
                                    "message_type": "port_trust_receipt"
                                }
                            ],
                            "consensus_timestamp": "2024-01-15T14:35:00Z",
                            "verification_summary": {
                                "total_checks": 5,
                                "passed": 5,
                                "failed": 0,
                                "overall_confidence": 98.5
                            }
                        }
                    },
                    "SHP-8824D": {
                        "shipment_id": "SHP-8824D",
                        "status": "verified",
                        "proof": {
                            "port_trust_receipt": {
                                "id": "PTR-002",
                                "shipmentId": "SHP-8824D",
                                "clearanceStatus": "cleared",
                                "vessel": "FX992 (Air)",
                                "port": "Port of Felixstowe",
                                "issuedAt": "2024-01-14 09:12:00",
                                "hederaTxRef": "0.0.453211@1698754400.987654321",
                                "agentSignatures": [
                                    {"agentName": "Orchestrator Agent", "agentId": "truthforge-orch-001"},
                                    {"agentName": "Verification & Compliance Agent", "agentId": "truthforge-verify-001"},
                                    {"agentName": "Evidence & Settlement Agent", "agentId": "truthforge-evidence-001"}
                                ]
                            },
                            "verifications": [
                                {
                                    "type": "Phytosanitary Cert",
                                    "status": "verified",
                                    "confidence": 99.1,
                                    "agent": "Verification & Compliance Agent",
                                    "timestamp": "2024-01-15 14:20:00",
                                    "hcsProof": "hcs-verify-001#1705311600"
                                },
                                {
                                    "type": "Packing List",
                                    "status": "verified",
                                    "confidence": 98.2,
                                    "agent": "Carrier Adapter Agent (Council-Grade)",
                                    "timestamp": "2024-01-15 14:10:00",
                                    "hcsProof": "hcs-carrier-001#1705311000"
                                }
                            ],
                            "hedera_references": [
                                {
                                    "topic_id": "0.0.453211",
                                    "sequence_number": 1240,
                                    "consensus_timestamp": "1698754400.987654321",
                                    "message_type": "verification_result"
                                }
                            ],
                            "consensus_timestamp": "2024-01-14T09:12:00Z",
                            "verification_summary": {
                                "total_checks": 3,
                                "passed": 3,
                                "failed": 0,
                                "overall_confidence": 98.7
                            }
                        }
                    }
                }
                
                # Check if shipment exists
                if shipment_id not in mock_proofs:
                    return handle_error(
                        "SHIPMENT_NOT_FOUND",
                        f"No proof data found for shipment {shipment_id}",
                        404,
                        {"shipment_id": shipment_id}
                    )
                
                return jsonify(mock_proofs[shipment_id]), 200
            
            else:
                # Live mode: query database for actual proof data
                # For now, return mock data structure
                return handle_error(
                    "NOT_IMPLEMENTED",
                    "Live mode proof retrieval not yet implemented",
                    501
                )
        
        except Exception as e:
            logger.error(f"Error retrieving proof for {shipment_id}: {e}", exc_info=True)
            return handle_error(
                "INTERNAL_ERROR",
                "An internal error occurred while retrieving proof",
                500,
                {"error_type": type(e).__name__}
            )


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers for common HTTP exceptions.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request(e):
        """Handle 400 Bad Request errors."""
        return handle_error(
            "BAD_REQUEST",
            str(e.description) if hasattr(e, 'description') else "Bad request",
            400
        )
    
    @app.errorhandler(401)
    def unauthorized(e):
        """Handle 401 Unauthorized errors."""
        return handle_error(
            "UNAUTHORIZED",
            str(e.description) if hasattr(e, 'description') else "Unauthorized",
            401
        )
    
    @app.errorhandler(403)
    def forbidden(e):
        """Handle 403 Forbidden errors."""
        return handle_error(
            "FORBIDDEN",
            str(e.description) if hasattr(e, 'description') else "Forbidden",
            403
        )
    
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 Not Found errors."""
        return handle_error(
            "NOT_FOUND",
            str(e.description) if hasattr(e, 'description') else "Resource not found",
            404
        )
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        """Handle 405 Method Not Allowed errors."""
        return handle_error(
            "METHOD_NOT_ALLOWED",
            str(e.description) if hasattr(e, 'description') else "Method not allowed",
            405
        )
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {e}", exc_info=True)
        return handle_error(
            "INTERNAL_SERVER_ERROR",
            "An internal server error occurred",
            500
        )
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return handle_error(
            "INTERNAL_ERROR",
            "An unexpected error occurred",
            500,
            {"error_type": type(e).__name__}
        )

