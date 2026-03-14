"""
TruthForge Orchestrator Agent

This agent serves as the central coordinator for all verification requests.
It parses natural language intents, routes requests to specialized agents,
coordinates parallel execution, and aggregates results into unified reports.
"""

import logging
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from agents.base_agent import BaseAgent
from agents.config import Config
from agents.hedera_client import HederaClientBase
from agents.hcs10_message import HCS10Message, MessageType
from database.database import db_session
from database.models import VerificationRequest, VerificationLog


logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """Parsed user intent."""
    intent_type: str
    parameters: Dict[str, Any]
    confidence: float
    missing_parameters: List[str]


@dataclass
class UnifiedReport:
    """Unified verification report from multiple agents."""
    report_id: str
    request_id: str
    intent: Intent
    agent_results: Dict[str, Any]
    overall_status: str
    confidence_level: float
    timestamp: datetime
    processing_time: float
    hcs_transaction_id: str


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent for TruthForge.
    
    Central coordinator that handles workflow coordination and decision
    execution. Routes requests to specialized agents and aggregates
    results into unified reports.
    """
    
    def __init__(
        self,
        agent_id: str,
        capabilities: List[str],
        hcs_topic_id: str,
        config: Config,
        hedera_client: HederaClientBase
    ):
        """
        Initialize Orchestrator Agent.
        
        Args:
            agent_id: Unique agent identifier
            capabilities: List of agent capabilities
            hcs_topic_id: HCS topic for messaging
            config: TruthForge configuration
            hedera_client: Hedera client for blockchain operations
        """
        super().__init__(agent_id, capabilities, hcs_topic_id, config, hedera_client)
        
        # Agent references (set by main application)
        self.agents = {}
        
        # Request timeout configuration
        self.request_timeout = config.timeout_seconds
        
        logger.info(f"Initialized {self.__class__.__name__} with ID {agent_id}")
    
    def set_agents(self, agents: Dict[str, BaseAgent]) -> None:
        """
        Set references to other agents.
        
        Args:
            agents: Dictionary of agent name to agent instance
        """
        self.agents = agents
        logger.info(f"Orchestrator connected to {len(agents)} agents: {list(agents.keys())}")
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process orchestration requests.
        
        Args:
            request: Request containing orchestration parameters
            
        Returns:
            Dict[str, Any]: Orchestration results
        """
        start_time = time.time()
        request_id = request.get('request_id', f"req-{int(time.time())}")
        
        try:
            request_type = request.get('type', 'verification')
            
            if request_type == 'verification':
                result = self._process_verification_request(request, request_id)
            elif request_type == 'natural_language':
                result = self._process_natural_language_request(request, request_id)
            elif request_type == 'agent_coordination':
                result = self._process_agent_coordination(request, request_id)
            else:
                raise ValueError(f"Unsupported request type: {request_type}")
            
            # Track successful request
            response_time = time.time() - start_time
            self._track_request(response_time, success=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing orchestration request: {e}")
            response_time = time.time() - start_time
            self._track_request(response_time, success=False)
            
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id,
                'request_id': request_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _process_verification_request(self, request: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Process standard verification request."""
        # Parse intent from request
        intent = self._parse_verification_intent(request)
        
        # Route to appropriate agents
        agent_ids = self.route_request(intent)
        
        # Coordinate agent execution
        agent_results = self.coordinate_agents(agent_ids, request)
        
        # Aggregate results
        unified_report = self.aggregate_results(request_id, intent, agent_results)
        
        return {
            'success': True,
            'unified_report': asdict(unified_report),
            'agent_id': self.agent_id
        }
    
    def _process_natural_language_request(self, request: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Process natural language request."""
        user_message = request.get('message', '')
        
        if not user_message:
            raise ValueError("message is required for natural language processing")
        
        # Parse natural language intent
        intent = self.parse_intent(user_message)
        
        # Check for missing parameters
        if intent.missing_parameters:
            return {
                'success': True,
                'needs_parameters': True,
                'missing_parameters': intent.missing_parameters,
                'prompt': self._generate_parameter_prompt(intent),
                'agent_id': self.agent_id
            }
        
        # Route and execute
        agent_ids = self.route_request(intent)
        agent_results = self.coordinate_agents(agent_ids, intent.parameters)
        unified_report = self.aggregate_results(request_id, intent, agent_results)
        
        return {
            'success': True,
            'unified_report': asdict(unified_report),
            'natural_language_response': self._format_natural_language_response(unified_report),
            'agent_id': self.agent_id
        }
    
    def _process_agent_coordination(self, request: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Process agent coordination request."""
        agent_ids = request.get('agent_ids', [])
        coordination_data = request.get('data', {})
        
        if not agent_ids:
            raise ValueError("agent_ids list is required for coordination")
        
        # Coordinate specified agents
        agent_results = self.coordinate_agents(agent_ids, coordination_data)
        
        return {
            'success': True,
            'agent_results': agent_results,
            'coordinated_agents': len(agent_ids),
            'agent_id': self.agent_id
        }
    
    def parse_intent(self, user_message: str) -> Intent:
        """
        Parse natural language message to extract intent.
        
        Args:
            user_message: User's natural language message
            
        Returns:
            Intent: Parsed intent with parameters
        """
        message_lower = user_message.lower()
        
        # Intent classification (simplified)
        if any(keyword in message_lower for keyword in ['verify', 'check', 'analyze', 'validate']):
            intent_type = 'verification'
        elif any(keyword in message_lower for keyword in ['track', 'status', 'shipment']):
            intent_type = 'tracking'
        elif any(keyword in message_lower for keyword in ['agent', 'health', 'status']):
            intent_type = 'agent_status'
        else:
            intent_type = 'general'
        
        # Parameter extraction (simplified)
        parameters = {}
        missing_parameters = []
        
        # Extract shipment ID
        import re
        shipment_match = re.search(r'(SHP-\w+|\w{10,})', user_message)
        if shipment_match:
            parameters['shipment_id'] = shipment_match.group(1)
        elif intent_type in ['verification', 'tracking']:
            missing_parameters.append('shipment_id')
        
        # Extract tracking number
        tracking_match = re.search(r'(\d{12,20}|1Z\w{16})', user_message)
        if tracking_match:
            parameters['tracking_number'] = tracking_match.group(1)
        
        # Extract order ID
        order_match = re.search(r'(order|WC-)[\s-]?(\w+)', message_lower)
        if order_match:
            parameters['order_id'] = order_match.group(2)
        
        confidence = 0.8 if not missing_parameters else 0.6
        
        return Intent(
            intent_type=intent_type,
            parameters=parameters,
            confidence=confidence,
            missing_parameters=missing_parameters
        )
    
    def _parse_verification_intent(self, request: Dict[str, Any]) -> Intent:
        """Parse structured verification request into intent."""
        intent_type = 'verification'
        parameters = {}
        missing_parameters = []
        
        # Extract parameters from structured request
        if 'image_data' in request:
            parameters['image_data'] = request['image_data']
            parameters['verification_type'] = 'image_analysis'
        elif 'document_data' in request:
            parameters['document_data'] = request['document_data']
            parameters['verification_type'] = 'document_verification'
        elif 'tracking_number' in request:
            parameters['tracking_number'] = request['tracking_number']
            parameters['verification_type'] = 'shipment_tracking'
        else:
            missing_parameters.append('verification_data')
        
        return Intent(
            intent_type=intent_type,
            parameters=parameters,
            confidence=0.9,
            missing_parameters=missing_parameters
        )
    
    def route_request(self, intent: Intent) -> List[str]:
        """
        Determine which agents are needed for the intent.
        
        Args:
            intent: Parsed intent
            
        Returns:
            List[str]: List of agent names to involve
        """
        agent_ids = []
        
        if intent.intent_type == 'verification':
            verification_type = intent.parameters.get('verification_type', 'unknown')
            
            if verification_type == 'image_analysis':
                agent_ids.extend(['verification_compliance', 'evidence_settlement'])
            elif verification_type == 'document_verification':
                agent_ids.extend(['verification_compliance', 'carrier_adapter', 'evidence_settlement'])
            elif verification_type == 'shipment_tracking':
                agent_ids.extend(['carrier_adapter', 'evidence_settlement'])
            else:
                # Default verification workflow
                agent_ids.extend(['verification_compliance', 'evidence_settlement'])
        
        elif intent.intent_type == 'tracking':
            agent_ids.extend(['carrier_adapter'])
        
        elif intent.intent_type == 'agent_status':
            agent_ids.extend(['registry_discovery'])
        
        # Always include registry agent for health monitoring
        if 'registry_discovery' not in agent_ids:
            agent_ids.append('registry_discovery')
        
        logger.info(f"Routed {intent.intent_type} request to agents: {agent_ids}")
        return agent_ids
    
    def coordinate_agents(self, agent_ids: List[str], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinate parallel execution across multiple agents.
        
        Args:
            agent_ids: List of agent names to coordinate
            request_data: Request data to send to agents
            
        Returns:
            Dict[str, Any]: Results from all agents
        """
        logger.info(f"Coordinating {len(agent_ids)} agents: {agent_ids}")
        
        agent_results = {}
        
        # Execute agents sequentially (could be parallelized in production)
        for agent_name in agent_ids:
            try:
                if agent_name not in self.agents:
                    logger.warning(f"Agent {agent_name} not available")
                    agent_results[agent_name] = {
                        'success': False,
                        'error': f'Agent {agent_name} not available'
                    }
                    continue
                
                agent = self.agents[agent_name]
                
                # Prepare agent-specific request
                agent_request = self._prepare_agent_request(agent_name, request_data)
                
                # Execute with timeout
                start_time = time.time()
                result = self._execute_agent_with_timeout(agent, agent_request)
                execution_time = time.time() - start_time
                
                result['execution_time'] = execution_time
                agent_results[agent_name] = result
                
                logger.debug(f"Agent {agent_name} completed in {execution_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Agent {agent_name} execution failed: {e}")
                agent_results[agent_name] = {
                    'success': False,
                    'error': str(e),
                    'agent_id': agent_name
                }
                
                # Handle agent failure
                self.handle_agent_failure(agent_name, e)
        
        return agent_results
    
    def aggregate_results(self, request_id: str, intent: Intent, agent_results: Dict[str, Any]) -> UnifiedReport:
        """
        Aggregate results from multiple agents into unified report.
        
        Args:
            request_id: Request identifier
            intent: Original intent
            agent_results: Results from all agents
            
        Returns:
            UnifiedReport: Unified verification report
        """
        report_id = f"report-{request_id}-{int(time.time())}"
        
        # Determine overall status
        overall_status = "SUCCESS"
        successful_agents = 0
        total_agents = len(agent_results)
        
        for agent_name, result in agent_results.items():
            if result.get('success', False):
                successful_agents += 1
            else:
                if successful_agents == 0:
                    overall_status = "FAILED"
                else:
                    overall_status = "PARTIAL_SUCCESS"
        
        # Calculate confidence level
        confidence_level = (successful_agents / total_agents) * 100 if total_agents > 0 else 0
        
        # Calculate total processing time
        processing_time = sum(
            result.get('execution_time', 0) 
            for result in agent_results.values()
        )
        
        # Submit unified report to HCS
        hcs_transaction_id = self._submit_unified_report({
            'report_id': report_id,
            'request_id': request_id,
            'intent_type': intent.intent_type,
            'overall_status': overall_status,
            'successful_agents': successful_agents,
            'total_agents': total_agents
        })
        
        unified_report = UnifiedReport(
            report_id=report_id,
            request_id=request_id,
            intent=intent,
            agent_results=agent_results,
            overall_status=overall_status,
            confidence_level=confidence_level,
            timestamp=datetime.now(timezone.utc),
            processing_time=processing_time,
            hcs_transaction_id=hcs_transaction_id
        )
        
        # Store unified report
        self._store_unified_report(unified_report)
        
        logger.info(
            f"Aggregated results for {request_id}: "
            f"{successful_agents}/{total_agents} agents successful"
        )
        
        return unified_report
    
    def handle_agent_failure(self, agent_id: str, error: Exception) -> Dict[str, Any]:
        """
        Handle agent failure with retry logic.
        
        Args:
            agent_id: Failed agent identifier
            error: Exception that caused failure
            
        Returns:
            Dict[str, Any]: Failure handling result
        """
        logger.warning(f"Handling failure for agent {agent_id}: {error}")
        
        # Log the failure
        failure_data = {
            'agent_id': agent_id,
            'error': str(error),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'orchestrator_id': self.agent_id
        }
        
        # Store failure in database
        try:
            verification_log = VerificationLog(
                request_id=f"failure-{agent_id}-{int(time.time())}",
                agent_id=agent_id,
                action='agent_failure',
                details=failure_data
            )
            db_session.add(verification_log)
            db_session.commit()
        except Exception as e:
            logger.error(f"Failed to store agent failure: {e}")
            db_session.rollback()
        
        # Submit failure to HCS
        self._submit_to_hcs({
            'action': 'agent_failure',
            'failed_agent': agent_id,
            'error': str(error),
            'orchestrator_id': self.agent_id
        })
        
        return {
            'failure_handled': True,
            'agent_id': agent_id,
            'error': str(error),
            'logged': True
        }
    
    def _prepare_agent_request(self, agent_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare agent-specific request data."""
        # Base request structure
        agent_request = {
            'orchestrator_id': self.agent_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Agent-specific request preparation
        if agent_name == 'verification_compliance':
            if 'image_data' in request_data:
                agent_request.update({
                    'type': 'image_analysis',
                    'image_data': request_data['image_data'],
                    'image_id': request_data.get('image_id', f"img-{int(time.time())}")
                })
            elif 'document_data' in request_data:
                agent_request.update({
                    'type': 'document_verification',
                    'document_data': request_data['document_data'],
                    'document_type': request_data.get('document_type', 'bol')
                })
        
        elif agent_name == 'carrier_adapter':
            agent_request.update({
                'type': 'query_shipment',
                'tracking_number': request_data.get('tracking_number'),
                'carrier': request_data.get('carrier')
            })
        
        elif agent_name == 'registry_discovery':
            agent_request.update({
                'type': 'health_report'
            })
        
        elif agent_name == 'evidence_settlement':
            agent_request.update({
                'type': 'create_audit_trail',
                'verification_data': request_data
            })
        
        return agent_request
    
    def _execute_agent_with_timeout(self, agent: BaseAgent, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent request with timeout."""
        try:
            # Simple timeout implementation (could use asyncio in production)
            start_time = time.time()
            result = agent.process_request(request)
            execution_time = time.time() - start_time
            
            if execution_time > self.request_timeout:
                logger.warning(f"Agent {agent.agent_id} exceeded timeout ({execution_time:.2f}s)")
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Agent execution failed: {e}")
    
    def _generate_parameter_prompt(self, intent: Intent) -> str:
        """Generate prompt for missing parameters."""
        if 'shipment_id' in intent.missing_parameters:
            return "Please provide a shipment ID (e.g., SHP-8821A) to proceed with verification."
        elif 'tracking_number' in intent.missing_parameters:
            return "Please provide a tracking number to check shipment status."
        elif 'verification_data' in intent.missing_parameters:
            return "Please provide image data or document data for verification."
        else:
            return f"Please provide the following information: {', '.join(intent.missing_parameters)}"
    
    def _format_natural_language_response(self, unified_report: UnifiedReport) -> str:
        """Format unified report as natural language response."""
        if unified_report.overall_status == "SUCCESS":
            response = f"Verification completed successfully with {unified_report.confidence_level:.1f}% confidence. "
        elif unified_report.overall_status == "PARTIAL_SUCCESS":
            response = f"Verification partially completed with {unified_report.confidence_level:.1f}% confidence. "
        else:
            response = "Verification failed. "
        
        # Add specific results
        for agent_name, result in unified_report.agent_results.items():
            if result.get('success') and 'analysis_result' in result:
                analysis = result['analysis_result']
                if 'authenticity_score' in analysis:
                    response += f"Authenticity score: {analysis['authenticity_score']:.1f}%. "
            elif result.get('success') and 'carrier_response' in result:
                carrier = result['carrier_response']
                if carrier.get('success'):
                    response += f"Shipment status: {carrier.get('shipment_data', {}).get('current_status', 'Unknown')}. "
        
        response += f"HCS proof: {unified_report.hcs_transaction_id}"
        return response
    
    def _submit_unified_report(self, report_data: Dict[str, Any]) -> str:
        """Submit unified report to HCS."""
        return self._submit_to_hcs({
            'action': 'unified_report',
            'report_data': report_data
        })
    
    def _submit_to_hcs(self, payload: Dict[str, Any]) -> str:
        """Submit orchestrator operation to HCS for timestamping."""
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
            logger.info(f"Submitted orchestrator operation to HCS: {transaction_id}")
            
            return transaction_id
            
        except Exception as e:
            logger.error(f"Failed to submit to HCS: {e}")
            return f"mock-tx-{int(time.time())}"
    
    def _store_unified_report(self, unified_report: UnifiedReport) -> None:
        """Store unified report in database."""
        try:
            verification_request = VerificationRequest(
                request_id=unified_report.request_id,
                user_id='system',
                status=unified_report.overall_status.lower(),
                authenticity_score=unified_report.confidence_level,
                analysis_results=asdict(unified_report),
                hcs_transaction_id=unified_report.hcs_transaction_id
            )
            
            db_session.add(verification_request)
            db_session.commit()
            logger.debug(f"Stored unified report {unified_report.report_id}")
            
        except Exception as e:
            logger.error(f"Failed to store unified report: {e}")
            db_session.rollback()
    
    def process_order(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an order received from a merchant (e.g., via WooCommerce webhook).
        
        This method coordinates the complete order-to-shipment-to-verification workflow:
        1. Fetch full order details via marketplace agent
        2. Create shipment via carrier adapter
        3. Trigger verification (if needed)
        4. Store results and return
        
        Args:
            order_payload: Order data from webhook containing:
                - order_id: WooCommerce order ID
                - order_data: Optional full order data
                - source: Source system (e.g., 'woocommerce')
                
        Returns:
            Dict containing order processing result with tracking number
        """
        start_time = time.time()
        order_id = order_payload.get('order_id')
        source = order_payload.get('source', 'unknown')
        
        logger.info(f"Processing order {order_id} from {source}")
        
        try:
            # Step 1: Get order details via marketplace agent
            if 'marketplace_agent' in self.agents:
                market_agent = self.agents['marketplace_agent']
            else:
                # Fallback: create marketplace agent instance
                from agents.marketplace_agent import MarketplaceAgent
                market_agent = MarketplaceAgent(mock_mode=self.config.mock_mode)
            
            order = market_agent.get_order_details(order_id)
            
            if not order:
                logger.error(f"Order {order_id} not found")
                return {
                    'success': False,
                    'error': 'Order not found',
                    'order_id': order_id
                }
            
            logger.info(f"Retrieved order {order_id} details")
            
            # Step 2: Create shipment via carrier adapter
            if 'carrier_adapter' in self.agents:
                carrier_agent = self.agents['carrier_adapter']
            else:
                # Fallback: create carrier adapter instance
                from agents.carrier_adapter_agent import CarrierAdapterAgent
                carrier_agent = CarrierAdapterAgent(
                    agent_id="truthforge-carrier-001",
                    capabilities=["create_shipment", "track_shipment"],
                    hcs_topic_id=self.hcs_topic_id,
                    config=self.config,
                    hedera_client=self.hedera_client
                )
            
            shipment = carrier_agent.process_order_shipment(order)
            
            if not shipment.get('success'):
                logger.error(f"Shipment creation failed for order {order_id}")
                return {
                    'success': False,
                    'error': 'Shipment creation failed',
                    'details': shipment,
                    'order_id': order_id
                }
            
            logger.info(f"Created shipment for order {order_id}: {shipment.get('tracking_number')}")
            
            # Step 3: Generate verification ID for future verification
            # In a real scenario, verification would happen when documents are uploaded
            verification_id = f"verif_{order_id}_{int(time.time())}"
            
            # Step 4: Update order with shipment info (optional)
            try:
                market_agent.update_order_status(
                    order_id,
                    'processing',
                    f"Shipment created. Tracking: {shipment.get('tracking_number')}"
                )
            except Exception as e:
                logger.warning(f"Could not update order status: {e}")
            
            # Step 5: Submit to HCS for timestamping
            hcs_tx = self._submit_to_hcs({
                'action': 'order_processed',
                'order_id': order_id,
                'tracking_number': shipment.get('tracking_number'),
                'source': source,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Step 6: Prepare result
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'order_id': order_id,
                'tracking_number': shipment.get('tracking_number'),
                'shipment_id': shipment.get('shipment_id'),
                'label_url': shipment.get('label_url'),
                'carrier': shipment.get('carrier', 'FedEx'),
                'status': 'processing',
                'verification_id': verification_id,
                'hcs_transaction_id': hcs_tx,
                'processing_time': f"{processing_time:.2f}s",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Order {order_id} processed successfully in {processing_time:.2f}s")
            
            # Track successful request
            self._track_request(processing_time, success=True)
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing order {order_id}: {e}", exc_info=True)
            
            # Track failed request
            self._track_request(processing_time, success=False)
            
            return {
                'success': False,
                'error': str(e),
                'order_id': order_id,
                'processing_time': f"{processing_time:.2f}s",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }