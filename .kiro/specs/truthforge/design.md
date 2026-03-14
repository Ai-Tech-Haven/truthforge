# Design Document: TruthForge

## Overview

TruthForge is a distributed AI agent network built on Hedera's Hashgraph Online (HOL) platform that provides reality verification for global trade. The system combines advanced deepfake detection, document verification, and blockchain-based proof generation to create an immutable trust layer for port clearance and shipment verification.

The architecture follows a microservices pattern where 5 specialized agents communicate via the HCS-10 messaging protocol. Each agent is registered on HOL, making them discoverable and independently scalable. The system features a responsive web interface with agent registry tables (desktop) and stacked cards (mobile), port trust receipt cards with 4-step verification, pre-arrival clearance queues, and comprehensive operational dashboards.

Key innovation: The Verification & Compliance Engine uses a novel 4-layer deepfake detection approach combined with document compliance validation, achieving higher accuracy than single-method approaches while maintaining regulatory compliance.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Responsive Frontend                       │
│         Desktop: Agent Registry Table                       │
│         Mobile: Agent Registry Cards                        │
│    Port Trust Receipt | Pre-Arrival Queue | Dashboard       │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Flask API Server                        │
│                   (api/app.py)                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Orchestrator Agent                           │
│                (truthforge-orch-001)                        │
│           Workflow coordination & decision execution         │
└──┬──────────┬──────────┬──────────┬─────────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│Verify│  │Carrier│  │Regist│  │Eviden│  │Databa│
│Compli│  │Adapt │  │Discov│  │Settle│  │se    │
│ance  │  │er    │  │ery   │  │ment  │  │      │
└───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘
    │         │         │         │         │
    └─────────┴─────────┴─────────┴─────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │   HCS-10 Messaging   │
            │   (Hedera Topics)    │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │    HOL Registry      │
            │  (Agent Discovery)   │
            └──────────────────────┘
```

### Agent Network

1. **Orchestrator Agent (truthforge-orch-001)**
   - Workflow coordination and decision execution
   - Parses natural language intents
   - Routes requests to specialized agents
   - Aggregates results into unified reports
   - Manages agent lifecycle and health checks

2. **Verification & Compliance Agent (truthforge-verify-001)**
   - Document validation and compliance assessment
   - Implements 4-layer deepfake detection pipeline
   - Validates Bills of Lading and shipping documents
   - Computes authenticity scores and compliance ratings
   - Generates detailed forensic and compliance reports

3. **Carrier Adapter Agent (Council-Grade) (truthforge-carrier-001)**
   - Carrier data ingestion and normalization
   - Integrates with multiple carrier APIs (FedEx, UPS, DHL, etc.)
   - Normalizes data formats into unified schema
   - Provides shipment tracking and status updates
   - Handles carrier-specific authentication and rate limiting

4. **Registry & Discovery Agent (truthforge-registry-001)**
   - Agent discovery, health reporting, and registry sync
   - Maintains agent capability registry
   - Handles DISCOVER message types
   - Provides real-time agent health status
   - Syncs with HOL registry for agent discovery

5. **Evidence & Settlement Agent (truthforge-evidence-001)**
   - Consensus submission and audit reference generation
   - Submits verification results to Hedera blockchain
   - Generates audit reference numbers for compliance
   - Maintains immutable audit trails
   - Handles transaction cost tracking and retry logic

### Communication Flow

```
User Request → Responsive Frontend → API → Orchestrator Agent
                                              ↓
                                    Parse Intent & Route
                                              ↓
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
        Verification & Compliance     Carrier Adapter          Registry & Discovery
                    │                         │                         │
        4-Layer Analysis + Compliance  Multi-Carrier Integration   Agent Health Monitoring
                    │                         │                         │
                    ▼                         ▼                         ▼
        Authenticity Score + Compliance   Normalized Shipment Data   Agent Status Updates
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              ▼
                                    Evidence & Settlement
                                              ↓
                                    HCS Consensus Submission
                                              ↓
                                    Audit Reference Generation
                                              ↓
                                    Return to Frontend
```

## Components and Interfaces

### Base Agent Interface

All agents inherit from a common base class that provides:

```python
class BaseAgent:
    agent_id: str          # Unique HOL identifier
    capabilities: List[str] # What this agent can do
    hcs_topic_id: str      # Topic for messaging
    database: Database     # Persistent storage connection
    
    def register_with_hol() -> bool
    def send_message(recipient: str, message: HCS10Message) -> str
    def receive_message() -> HCS10Message
    def process_request(request: dict) -> dict
    def health_check() -> AgentStatus
    def persist_data(data: dict) -> bool
```

### HCS-10 Message Structure

```python
class HCS10Message:
    message_type: MessageType  # REQUEST, RESPONSE, QUERY, NOTIFY, DISCOVER
    sender_id: str
    recipient_id: str
    timestamp: datetime
    payload: dict
    signature: str  # Cryptographic signature for authenticity
    
    def to_hcs_format() -> bytes
    def from_hcs_format(data: bytes) -> HCS10Message
    def validate_signature() -> bool
```

### Verification & Compliance Agent Interface

```python
class VerificationComplianceAgent(BaseAgent):
    def analyze_image(image_data: bytes) -> AnalysisResult
    def exif_analysis(image_data: bytes) -> ExifReport
    def lighting_analysis(image_data: bytes) -> LightingReport
    def ai_artifact_detection(image_data: bytes) -> ArtifactReport
    def metadata_verification(image_data: bytes) -> MetadataReport
    def compute_authenticity_score(reports: List[Report]) -> float
    def generate_forensic_report(reports: List[Report]) -> ForensicReport
    def extract_bol_fields(document: bytes) -> BOLData
    def validate_compliance(bol_data: BOLData) -> ComplianceResult
    def cross_reference_shipment(bol_data: BOLData, shipment_data: ShipmentData) -> ComparisonResult
    def flag_discrepancies(comparison: ComparisonResult) -> List[Discrepancy]
    def generate_verification_report(results: dict) -> VerificationReport
```

### Carrier Adapter Agent Interface

```python
class CarrierAdapterAgent(BaseAgent):
    supported_carriers: List[str]  # FedEx, UPS, DHL, etc.
    
    def authenticate_carrier(carrier: str) -> bool
    def normalize_tracking_data(carrier: str, raw_data: dict) -> ShipmentData
    def query_shipment(carrier: str, tracking_number: str) -> ShipmentData
    def get_supported_carriers() -> List[str]
    def handle_rate_limits(carrier: str, error: Exception) -> bool
    def validate_tracking_format(carrier: str, tracking_number: str) -> bool
```

### Registry & Discovery Agent Interface

```python
class RegistryDiscoveryAgent(BaseAgent):
    def sync_with_hol() -> bool
    def monitor_agent_health(agent_ids: List[str]) -> Dict[str, AgentStatus]
    def discover_agents(capabilities: List[str] = None) -> List[AgentInfo]
    def update_agent_status(agent_id: str, status: AgentStatus) -> bool
    def get_agent_capabilities(agent_id: str) -> List[str]
    def handle_discover_message(message: HCS10Message) -> DiscoverResponse
    def cache_agent_info(agent_info: AgentInfo, ttl: int) -> bool
```

### Evidence & Settlement Agent Interface

```python
class EvidenceSettlementAgent(BaseAgent):
    def submit_consensus(verification_data: dict) -> str  # Returns transaction ID
    def generate_audit_reference(verification_id: str) -> str
    def create_audit_trail(verification_data: dict) -> AuditTrail
    def track_transaction_costs(transaction_id: str, cost: float) -> bool
    def retry_failed_transaction(transaction_data: dict) -> str
    def validate_account_balance() -> bool
    def get_transaction_receipt(transaction_id: str) -> TransactionReceipt
```

### Orchestrator Agent Interface

```python
class OrchestratorAgent(BaseAgent):
    def parse_intent(user_message: str) -> Intent
    def route_request(intent: Intent) -> List[str]  # Returns agent IDs
    def coordinate_agents(agent_ids: List[str], request: dict) -> dict
    def aggregate_results(results: List[dict]) -> UnifiedReport
    def handle_agent_failure(agent_id: str, error: Exception) -> dict
    def execute_workflow(workflow_type: str, request: dict) -> dict
```

## Data Models

### AnalysisResult

```python
class AnalysisResult:
    image_id: str
    authenticity_score: float  # 0-100
    compliance_score: float    # 0-100
    exif_report: ExifReport
    lighting_report: LightingReport
    artifact_report: ArtifactReport
    metadata_report: MetadataReport
    overall_assessment: str
    confidence_level: float
    timestamp: datetime
    hcs_transaction_id: str
    audit_reference: str
```

### ExifReport

```python
class ExifReport:
    has_exif_data: bool
    camera_make: Optional[str]
    camera_model: Optional[str]
    capture_timestamp: Optional[datetime]
    gps_coordinates: Optional[Tuple[float, float]]
    software_used: Optional[str]
    tampering_indicators: List[str]
    confidence_score: float  # 0-100
```

### LightingReport

```python
class LightingReport:
    lighting_consistency: float  # 0-100
    shadow_analysis: dict
    reflection_analysis: dict
    color_temperature: float
    anomalies_detected: List[str]
    confidence_score: float
```

### ArtifactReport

```python
class ArtifactReport:
    ai_artifacts_detected: bool
    artifact_locations: List[BoundingBox]
    artifact_types: List[str]  # e.g., "blurring", "unnatural edges"
    generation_probability: float  # 0-100
    confidence_score: float
```

### MetadataReport

```python
class MetadataReport:
    metadata_consistent: bool
    file_format: str
    file_size: int
    dimensions: Tuple[int, int]
    compression_artifacts: bool
    edit_history: List[str]
    confidence_score: float
```

### BOLData

```python
class BOLData:
    tracking_number: str
    origin_address: Address
    destination_address: Address
    shipper_name: str
    consignee_name: str
    cargo_description: str
    weight: float
    declared_value: float
    shipment_date: datetime
    expected_delivery: datetime
```

### VerificationReport

```python
class VerificationReport:
    verification_id: str
    bol_data: BOLData
    shipment_data: Optional[ShipmentData]
    discrepancies: List[Discrepancy]
    verification_status: str  # "PASS", "FAIL", "WARNING"
    compliance_status: str    # "COMPLIANT", "NON_COMPLIANT", "PENDING"
    confidence_level: float
    timestamp: datetime
    hcs_transaction_id: str
    audit_reference: str
```

### Order

```python
class Order:
    order_id: str
    order_number: str
    customer_name: str
    customer_email: str
    shipping_address: Address
    items: List[OrderItem]
    total_amount: float
    order_status: str
    cargo_photo_urls: List[str]
    verification_status: Optional[str]
    verification_data: Optional[dict]
```

### PortTrustReceipt

```python
class PortTrustReceipt:
    receipt_id: str
    vessel_name: str
    port_of_origin: str
    port_of_destination: str
    verification_steps: List[VerificationStep]  # 4-step process
    current_step: int
    overall_status: str  # "IN_PROGRESS", "COMPLETED", "FAILED"
    timestamp: datetime
    estimated_completion: datetime
```

### VerificationStep

```python
class VerificationStep:
    step_number: int
    step_name: str
    status: str  # "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"
    agent_id: str
    start_time: Optional[datetime]
    completion_time: Optional[datetime]
    result_data: Optional[dict]
```

### PreArrivalClearanceItem

```python
class PreArrivalClearanceItem:
    clearance_id: str
    vessel_name: str
    tracking_number: str
    origin_port: str
    destination_port: str
    estimated_arrival: datetime
    clearance_status: str  # "PENDING", "IN_PROGRESS", "CLEARED", "REJECTED"
    priority: str  # "HIGH", "MEDIUM", "LOW"
    verification_progress: float  # 0-100
    assigned_agent: str
```

### DashboardMetrics

```python
class DashboardMetrics:
    total_clearances_today: int
    average_clearance_time: float  # in hours
    success_rate: float  # 0-100
    active_verifications: int
    port_throughput: int  # vessels per day
    compliance_rate: float  # 0-100
    cost_per_verification: float  # in HBAR
    timestamp: datetime
```

### AgentRegistryEntry

```python
class AgentRegistryEntry:
    agent_id: str
    agent_name: str
    capabilities: List[str]
    status: str  # "ONLINE", "OFFLINE", "BUSY", "ERROR"
    last_heartbeat: datetime
    requests_processed_today: int
    average_response_time: float  # in seconds
    success_rate: float  # 0-100
    current_load: float  # 0-100
```

### AgentStatus

```python
class AgentStatus:
    agent_id: str
    status: str  # "ONLINE", "OFFLINE", "BUSY", "ERROR"
    last_heartbeat: datetime
    requests_processed: int
    average_response_time: float
    error_count: int
```

### Configuration

```python
class Config:
    # Hedera Configuration
    hedera_account_id: str
    hedera_private_key: str
    hedera_network: str  # "testnet", "mainnet"
    hcs_topic_id: str
    
    # Database Configuration
    database_url: str
    database_type: str  # "postgresql", "sqlite", "mysql"
    database_pool_size: int
    database_timeout: int
    
    # Carrier Configuration
    fedex_api_key: str
    fedex_secret_key: str
    fedex_account_number: str
    ups_api_key: str
    dhl_api_key: str
    
    # System Configuration
    mock_mode: bool
    log_level: str
    api_port: int
    max_retries: int
    timeout_seconds: int
    frontend_responsive_breakpoints: dict
```

### Database

```python
class Database:
    connection_url: str
    pool_size: int
    
    def connect() -> Connection
    def execute_query(query: str, params: dict) -> List[dict]
    def insert_record(table: str, data: dict) -> str
    def update_record(table: str, record_id: str, data: dict) -> bool
    def delete_record(table: str, record_id: str) -> bool
    def create_tables() -> bool
    def migrate_schema(version: str) -> bool
```

### AuditTrail

```python
class AuditTrail:
    audit_id: str
    verification_id: str
    agent_id: str
    action: str
    timestamp: datetime
    input_data: dict
    output_data: dict
    hcs_transaction_id: str
    audit_reference: str
    compliance_flags: List[str]
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

After analyzing all acceptance criteria, several patterns emerged that allow us to consolidate redundant properties:

1. **All 4-layer analysis requirements (2.1-2.4)** can be combined into a single property that verifies all layers execute
2. **HCS timestamping requirements (2.7, 3.7, 5.1)** share the same pattern and can be generalized
3. **Agent registration requirements (1.1-1.5)** follow similar validation patterns
4. **Frontend responsive requirements (8.1-8.7)** can be consolidated into responsive behavior properties
5. **Error handling requirements across agents** share common retry and logging patterns

The following properties represent the unique, non-redundant correctness guarantees for TruthForge:

### Property 1: Agent Registration Count

*For any* system initialization, exactly 5 agents must be registered with HOL, no more and no less.

**Validates: Requirements 1.1**

### Property 2: Agent Registration Uniqueness

*For any* set of agent registration attempts, all successfully registered agent IDs must be unique and match the expected identifiers: truthforge-orch-001, truthforge-verify-001, truthforge-carrier-001, truthforge-registry-001, truthforge-evidence-001.

**Validates: Requirements 1.2**

### Property 3: Agent Registration Persistence

*For any* agent registration with capabilities, endpoints, and metadata, querying the HOL registry immediately after registration shall return all provided registration data unchanged.

**Validates: Requirements 1.3, 1.4**

### Property 4: Agent Re-registration Idempotence

*For any* agent that is already registered, attempting to re-register with the same agent ID shall succeed and update the registration without creating duplicates.

**Validates: Requirements 1.5**

### Property 5: Verification 4-Layer Execution

*For any* submitted cargo photo, the Verification & Compliance Agent shall execute all four analysis layers (EXIF, lighting, AI artifacts, metadata) and include results from each layer in the final report.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 6: Authenticity Score Bounds

*For any* cargo photo analysis, the computed Authenticity_Score shall be a numeric value between 0 and 100 inclusive.

**Validates: Requirements 2.5**

### Property 7: Analysis Report Completeness

*For any* completed image analysis, the generated report shall contain all four sub-reports (EXIF, lighting, artifacts, metadata), an overall assessment, compliance score, and a confidence level.

**Validates: Requirements 2.6**

### Property 8: HCS Timestamping Consistency

*For any* verification operation (image analysis, document verification, or evidence settlement), upon completion, an HCS transaction ID shall be present in the result, indicating the verification was timestamped on Hedera.

**Validates: Requirements 2.7, 3.7, 5.1**

### Property 9: Carrier Data Normalization

*For any* carrier data received from different carriers, the Carrier Adapter Agent shall normalize all data into a unified schema containing origin, destination, current status, and estimated delivery fields.

**Validates: Requirements 3.1, 3.3**

### Property 10: Multi-Carrier Query Execution

*For any* tracking number provided, the Carrier Adapter Agent shall attempt to query appropriate carrier APIs based on tracking number format and carrier identification.

**Validates: Requirements 3.2**

### Property 11: Carrier Error Handling

*For any* carrier API error (rate limits, authentication failures, unavailable data), the Carrier Adapter Agent shall return structured error responses with specific reason codes and handle errors gracefully.

**Validates: Requirements 3.4, 3.5**

### Property 12: Mock Mode Data Simulation

*For any* operation in Mock Mode, all agents shall return simulated data instead of making real API calls or blockchain transactions, while maintaining the same data structure as live mode.

**Validates: Requirements 3.6, 12.1, 12.2, 12.3, 12.4, 12.5**

### Property 13: Registry Agent Health Monitoring

*For any* health check operation, the Registry & Discovery Agent shall monitor all 5 agents and provide current status information for each agent.

**Validates: Requirements 4.2, 4.4**

### Property 14: Agent Discovery Response Matching

*For any* DISCOVER message with capability filters, all agents returned in the response shall possess at least one of the requested capabilities.

**Validates: Requirements 4.6**

### Property 15: Agent Discovery Caching

*For any* repeated agent discovery request with identical filters within the TTL period, the Registry & Discovery Agent shall return cached results without querying the HOL registry again.

**Validates: Requirements 4.7**

### Property 16: Evidence Settlement Audit Trail

*For any* verification process completion, the Evidence & Settlement Agent shall create an audit trail linking the audit reference to the original verification request with all required compliance data.

**Validates: Requirements 5.2, 5.3, 5.4**

### Property 17: Transaction Receipt Handling

*For any* blockchain transaction submission in Live Mode, the Evidence & Settlement Agent shall wait for transaction receipts before confirming operations and track HBAR costs.

**Validates: Requirements 5.5, 5.7, 13.4, 13.5**

### Property 18: Transaction Retry Logic

*For any* failed blockchain transaction, the Evidence & Settlement Agent shall implement exponential backoff retry logic up to the configured maximum retry count.

**Validates: Requirements 5.6, 13.3**

### Property 19: HCS-10 Message Structure

*For any* message sent between agents, the message shall contain all required HCS-10 fields: message_type, sender_id, recipient_id, timestamp, payload, and signature.

**Validates: Requirements 6.1, 6.2**

### Property 20: HCS Message Submission

*For any* agent-to-agent message, the message shall be submitted to the configured HCS topic and an HCS transaction ID shall be returned.

**Validates: Requirements 6.3**

### Property 21: Frontend Responsive Behavior

*For any* viewport size change, the Frontend shall adapt its layout appropriately: desktop displays Agent Registry Table, mobile displays Agent Registry Cards, and all components maintain touch-friendly interfaces on mobile.

**Validates: Requirements 8.1, 8.2, 8.6, 8.7**

### Property 22: Port Trust Receipt 4-Step Process

*For any* verification in progress, the Frontend shall display a Port Trust Receipt Card showing the current step in the 4-step verification process with appropriate status indicators.

**Validates: Requirements 8.3**

### Property 23: Dashboard Metrics Display

*For any* dashboard load, the Frontend shall display operational metrics including clearance times, throughput, port overview map, and real-time updates when data changes.

**Validates: Requirements 10.1, 10.2, 10.4**

### Property 24: Database Persistence

*For any* verification completion, the Database shall store all verification details including timestamps, authenticity scores, HCS transaction references, and audit trails for future reference.

**Validates: Requirements 15.1, 15.5**

### Property 25: Database Mode Segregation

*For any* data storage operation, the Database shall properly segregate Mock Mode and Live Mode data to prevent cross-contamination between development and production environments.

**Validates: Requirements 15.7**


## Error Handling

### Error Categories

TruthForge implements a hierarchical error handling strategy with the following categories:

1. **Validation Errors**: Invalid input data, malformed requests, missing required fields
2. **Authentication Errors**: Invalid credentials, expired tokens, insufficient permissions
3. **Network Errors**: Connection timeouts, DNS failures, unreachable services
4. **Rate Limit Errors**: API quota exceeded, too many requests
5. **Blockchain Errors**: Transaction failures, insufficient balance, network congestion
6. **Agent Errors**: Agent unavailable, agent timeout, agent internal failure
7. **Integration Errors**: External API failures (FedEx, WooCommerce)
8. **System Errors**: Internal server errors, database failures, unexpected exceptions

### Error Handling Strategies

**Validation Errors**:
- Fail fast with descriptive error messages
- Return 400 Bad Request with structured error details
- Log validation failures for monitoring
- No retries (user must correct input)

**Authentication Errors**:
- Return 401 Unauthorized for invalid credentials
- Return 403 Forbidden for insufficient permissions
- Log authentication attempts for security monitoring
- No automatic retries (user must re-authenticate)

**Network Errors**:
- Implement exponential backoff retry (1s, 2s, 4s, 8s)
- Maximum 3 retry attempts
- Log each retry attempt with timing
- Fail with clear error message after max retries
- Circuit breaker pattern for repeated failures

**Rate Limit Errors**:
- Respect Retry-After headers from APIs
- Implement exponential backoff with jitter
- Queue requests when rate limited
- Log rate limit events for capacity planning

**Blockchain Errors**:
- Retry transaction submission up to 3 times
- Check account balance before operations
- Log transaction hashes for debugging
- Provide clear error messages about blockchain state
- Fall back to mock mode if configured

**Agent Errors**:
- Timeout after configured duration (default 30s)
- Retry with alternate agent if available
- Log agent failures for health monitoring
- Return partial results if some agents succeed
- Graceful degradation (continue with available agents)

**Integration Errors**:
- Retry with exponential backoff
- Cache successful responses to reduce API calls
- Provide mock data in development mode
- Log integration failures with request/response details
- Return structured errors to clients

**System Errors**:
- Log full stack traces for debugging
- Return generic 500 error to clients (no internal details)
- Send alerts to monitoring systems
- Attempt graceful shutdown if critical
- Preserve request context for debugging

### Error Response Format

All API errors follow a consistent structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      "field": "specific_field_name",
      "reason": "why this failed"
    },
    "request_id": "unique-request-identifier",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Logging Strategy

**Log Levels**:
- DEBUG: Detailed diagnostic information (development only)
- INFO: General informational messages (agent actions, requests)
- WARNING: Recoverable errors, retries, degraded functionality
- ERROR: Failures that prevent operation completion
- CRITICAL: System-wide failures requiring immediate attention

**Structured Logging**:
All logs include:
- Timestamp (ISO 8601 format)
- Log level
- Component/agent identifier
- Request ID (for tracing)
- Message
- Contextual data (JSON format)

**Log Retention**:
- Development: 7 days
- Production: 30 days
- Critical errors: 90 days

## Testing Strategy

TruthForge employs a comprehensive testing approach combining unit tests, integration tests, and property-based tests to ensure system correctness and reliability.

### Testing Approach

**Dual Testing Philosophy**:
- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs
- Both approaches are complementary and necessary for comprehensive coverage

**Unit Testing Balance**:
- Focus on specific examples that demonstrate correct behavior
- Test integration points between components
- Test edge cases and error conditions
- Avoid excessive unit tests for scenarios covered by property tests
- Property tests handle comprehensive input coverage through randomization

### Unit Testing

**Scope**: Individual functions, classes, and methods in isolation

**Coverage Areas**:
1. Agent initialization and configuration
2. Message parsing and serialization
3. Data model validation
4. Error handling paths
5. Mock implementations for external services
6. Configuration loading and validation

**Example Unit Tests**:
- Test that BaseAgent.register_with_hol() returns True with valid config
- Test that HCS10Message.validate_signature() rejects tampered messages
- Test that BOLData validation catches missing required fields
- Test that Config.load() raises error when Hedera credentials are missing
- Test that WooCommerceAdapter handles 404 responses gracefully

**Testing Framework**: pytest with fixtures for common test data

### Integration Testing

**Scope**: Interactions between multiple components

**Coverage Areas**:
1. Agent-to-agent communication via HCS-10
2. Orchestrator routing to specialized agents
3. WooCommerce webhook processing end-to-end
4. Reality Engine pipeline (all 4 layers)
5. Document verification with FedEx integration
6. Frontend API interactions

**Example Integration Tests**:
- Test complete verification flow: webhook → adapter → orchestrator → reality engine → HCS → response
- Test agent discovery: DISCOVER message → marketplace → HOL query → response
- Test error propagation: agent failure → orchestrator retry → alternate agent → success
- Test WooCommerce order update: verification complete → adapter → WooCommerce API → order updated

**Testing Framework**: pytest with docker-compose for service dependencies

### Property-Based Testing

**Scope**: Universal properties that must hold for all valid inputs

**Framework**: Hypothesis (Python property-based testing library)

**Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each test references its design document property
- Tag format: `# Feature: truthforge, Property {number}: {property_text}`

**Property Test Implementation**:

Each correctness property from the design document must be implemented as a property-based test. Examples:

```python
from hypothesis import given, strategies as st

# Property 5: Authenticity Score Bounds
@given(image_data=st.binary(min_size=1024, max_size=1024*1024))
def test_authenticity_score_bounds(image_data):
    """
    Feature: truthforge, Property 5: Authenticity Score Bounds
    For any cargo photo analysis, the computed Authenticity_Score 
    shall be between 0 and 100 inclusive.
    """
    engine = RealityEngine()
    result = engine.analyze_image(image_data)
    assert 0 <= result.authenticity_score <= 100

# Property 17: HCS-10 Message Structure
@given(
    msg_type=st.sampled_from(MessageType),
    sender=st.text(min_size=1, max_size=50),
    recipient=st.text(min_size=1, max_size=50),
    payload=st.dictionaries(st.text(), st.text())
)
def test_hcs10_message_structure(msg_type, sender, recipient, payload):
    """
    Feature: truthforge, Property 17: HCS-10 Message Structure
    For any message sent between agents, the message shall contain 
    all required fields.
    """
    msg = HCS10Message(
        message_type=msg_type,
        sender_id=sender,
        recipient_id=recipient,
        payload=payload
    )
    assert msg.message_type is not None
    assert msg.sender_id is not None
    assert msg.recipient_id is not None
    assert msg.timestamp is not None
    assert msg.payload is not None
    assert msg.signature is not None
```

**Property Test Coverage**:
- All 46 correctness properties must have corresponding property tests
- Each test must run at least 100 iterations
- Tests must use Hypothesis strategies to generate diverse inputs
- Tests must clearly document which property they validate

### Mock Mode Testing

**Purpose**: Enable development and demonstration without blockchain costs

**Mock Implementations**:
1. **MockHederaClient**: Simulates HCS message submission without real transactions
   - Returns fake transaction IDs
   - Simulates consensus timestamps
   - No actual HBAR costs

2. **MockCarrierAdapters**: Returns predefined shipment data for multiple carriers
   - Recognizes test tracking numbers for FedEx, UPS, DHL
   - Returns realistic shipment data
   - Simulates API delays and rate limits

3. **MockDatabase**: Uses in-memory storage for testing
   - Simulates database operations without persistent storage
   - Maintains data consistency within test sessions
   - Supports both Mock and Live mode data segregation

4. **MockVerificationComplianceAgent**: Returns deterministic scores
   - Scores based on image hash and content patterns
   - Consistent results for same input
   - Fast execution (no actual analysis)

5. **MockEvidenceSettlementAgent**: Simulates blockchain operations
   - Generates fake audit references
   - Simulates transaction costs
   - No actual blockchain submissions

**Mock Mode Configuration**:
```python
# .env
MOCK_MODE=true
MOCK_AUTHENTICITY_SCORE=85.5
MOCK_HCS_TRANSACTION_ID=0.0.12345@1234567890.123456789
DATABASE_URL=sqlite:///:memory:
CARRIER_APIS_MOCK=true
```

### End-to-End Testing

**Scope**: Complete user workflows from frontend to blockchain

**Test Scenarios**:
1. User submits verification request via responsive interface → receives authenticity score
2. Agent registry displays correctly on desktop (table) and mobile (cards)
3. Port Trust Receipt Card shows 4-step verification process with real-time updates
4. Pre-Arrival Clearance Queue displays shipment tracking with proper status updates
5. Dashboard metrics update in real-time with operational data
6. Agent discovery → capability filtering → agent selection → request routing
7. Multi-carrier data normalization → unified schema validation → shipment tracking
8. Evidence settlement → audit reference generation → blockchain submission
9. Database persistence → audit trail maintenance → compliance reporting
10. Error scenarios → retry logic → fallback behavior → user notification

**Testing Environment**:
- Hedera testnet for blockchain operations
- Test database with sample port and shipment data
- Mock carrier APIs for predictable responses
- Responsive design testing across multiple viewport sizes
- Touch interaction testing on mobile devices

### Continuous Integration

**CI Pipeline**:
1. Lint code (flake8, black)
2. Run unit tests with coverage reporting (target: 80%+)
3. Run integration tests
4. Run property-based tests (100 iterations minimum)
5. Build Docker images
6. Deploy to staging environment
7. Run end-to-end tests
8. Generate test reports

**Test Execution Time Targets**:
- Unit tests: < 2 minutes
- Integration tests: < 5 minutes
- Property tests: < 10 minutes
- End-to-end tests: < 15 minutes
- Total CI pipeline: < 30 minutes

### Test Data Management

**Test Fixtures**:
- Sample cargo photos (authentic and manipulated)
- Sample BOL documents (valid and invalid)
- Sample carrier data from multiple providers (FedEx, UPS, DHL)
- Sample port clearance data and operational metrics
- Sample HCS messages and blockchain transaction data
- Responsive design test cases for different viewport sizes

**Data Generation**:
- Use Hypothesis for property test data generation
- Use factories for consistent test object creation
- Use fixtures for reusable test data
- Avoid hardcoded test data where possible

### Coverage Goals

**Code Coverage Targets**:
- Overall: 80%+
- Critical paths (verification, messaging): 95%+
- Error handling: 90%+
- Configuration: 70%+

**Property Coverage**:
- All 25 correctness properties must have property tests
- Each property test must pass with 100+ iterations
- Property tests must cover edge cases through generation
- Frontend responsive properties must test multiple viewport sizes

### Testing Documentation

**Test Documentation Requirements**:
- Each test must have a docstring explaining what it tests
- Property tests must reference their design document property number
- Integration tests must document the components involved
- End-to-end tests must document the complete user workflow
- Mock implementations must document what they simulate

