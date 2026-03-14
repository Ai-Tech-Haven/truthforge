# Requirements Document: TruthForge

## Introduction

TruthForge is a reality-verified global trade platform that combines AI-powered deepfake detection with blockchain-based verification for cargo shipments and global port clearance network. The system uses a network of 5 specialized AI agents registered on Hedera's Hashgraph Online (HOL) to detect manipulated cargo photos, verify shipping documents, and create immutable proofs on the Hedera blockchain. The platform features a responsive web interface with agent registry tables, port trust receipt cards, pre-arrival clearance queues, and comprehensive dashboard with operational metrics.

The system supports both mock and live modes, with full responsive design including desktop agent registry tables and mobile stacked cards. All agent actions generate auditable Hedera transaction references with HCS-10 messaging protocol.

This project is designed for the Hedera Hello Future Apex Hackathon 2026, targeting the AI & Agentic track and HOL Bounty, with emphasis on real-world impact through integration with Ports, Air/Sea Carrier, 6M+ WooCommerce stores worldwide.

## Glossary

- **TruthForge**: The complete reality-verified trade platform system
- **Orchestrator_Agent**: The main coordinator agent (truthforge-orch-001) that handles workflow coordination and decision execution
- **Verification_Compliance_Agent**: Agent (truthforge-verify-001) that performs document validation and compliance assessment
- **Carrier_Adapter_Agent**: Council-Grade agent (truthforge-carrier-001) that handles carrier data ingestion and normalization
- **Registry_Discovery_Agent**: Agent (truthforge-registry-001) that manages agent discovery, health reporting, and registry sync
- **Evidence_Settlement_Agent**: Agent (truthforge-evidence-001) that handles consensus submission and audit reference generation
- **HOL**: Hashgraph Online - Hedera's agent registry system
- **HCS**: Hedera Consensus Service - provides immutable timestamping
- **HCS-10**: The messaging protocol for agent-to-agent communication on Hedera
- **Port_Trust_Receipt**: 4-step verification process card displayed in the frontend
- **Pre_Arrival_Clearance_Queue**: Shipment tracking interface with queue management
- **Agent_Registry_Table**: Desktop view showing agent status in tabular format
- **Agent_Registry_Cards**: Mobile view showing agent status in stacked card format
- **Authenticity_Score**: A 0-100 numerical score indicating photo authenticity
- **BOL**: Bill of Lading - shipping document that needs verification
- **Deepfake**: Manipulated or AI-generated image that misrepresents reality
- **Mock_Mode**: Development mode using simulated data without real blockchain transactions
- **Live_Mode**: Production mode with actual Hedera blockchain integration and real carrier data
- **Database**: Backend data storage system for persistent data management

## Requirements

### Requirement 1: Agent Registration and HOL Integration

**User Story:** As a system administrator, I want all TruthForge agents registered on Hedera's HOL, so that they can be discovered and trusted by the network.

#### Acceptance Criteria

1. WHEN the system initializes, THE TruthForge System SHALL register exactly 5 agents with HOL
2. THE TruthForge System SHALL register agents with unique identifiers: truthforge-orch-001, truthforge-verify-001, truthforge-carrier-001, truthforge-registry-001, truthforge-evidence-001
3. WHEN an agent registers, THE HOL_Registry SHALL store the agent's capabilities, endpoints, and metadata
4. WHEN an agent registration completes, THE TruthForge System SHALL receive a confirmation with the agent's HOL identifier
5. THE TruthForge System SHALL maintain agent registration status and allow re-registration if needed

### Requirement 2: Verification & Compliance Engine

**User Story:** As a trade platform user, I want cargo photos and documents analyzed for authenticity and compliance, so that I can trust the shipment documentation.

#### Acceptance Criteria

1. WHEN a cargo photo is submitted, THE Verification_Compliance_Agent SHALL perform EXIF metadata analysis to detect tampering
2. WHEN a cargo photo is submitted, THE Verification_Compliance_Agent SHALL analyze lighting consistency across the image
3. WHEN a cargo photo is submitted, THE Verification_Compliance_Agent SHALL detect AI-generated artifacts and anomalies
4. WHEN a cargo photo is submitted, THE Verification_Compliance_Agent SHALL verify metadata consistency with claimed capture details
5. WHEN all four analysis layers complete, THE Verification_Compliance_Agent SHALL compute an Authenticity_Score between 0 and 100
6. WHEN the Authenticity_Score is computed, THE Verification_Compliance_Agent SHALL generate a detailed analysis report with findings from each layer
7. WHEN the analysis completes, THE Verification_Compliance_Agent SHALL timestamp the verification result on HCS
8. WHEN a BOL document is submitted, THE Verification_Compliance_Agent SHALL extract key fields and validate compliance requirements

### Requirement 3: Carrier Data Integration

**User Story:** As a logistics manager, I want carrier data ingested and normalized from multiple sources, so that I can have unified shipment tracking across carriers.

#### Acceptance Criteria

1. WHEN carrier data is received, THE Carrier_Adapter_Agent SHALL normalize data formats from different carriers into a unified schema
2. WHEN tracking numbers are provided, THE Carrier_Adapter_Agent SHALL query multiple carrier APIs for shipment verification
3. WHEN carracking number is present, THE Document_Verifier SHALL query the FedEx_Adapter for shipment verification
4. WHEN FedEx data is retrieved, THE Document_Verifier SHALL compare BOL details against actual shipment records
5. WHEN discrepancies are detected, THE Document_Verifier SHALL flag specific mismatches with severity levels
6. WHEN verification completes, THE Document_Verifier SHALL generate a verification report with pass/fail status
7. WHEN the verification report is gearrier_Adapter_Agent SHALL timestamp the result on HCS

### Requirement 4: Agent Registry & Discovery

**User Story:** As a system operator, I want comprehensive agent discovery and health monitoring, so that I can maintain system reliability and performance.

#### Acceptance Criteria

1. WHEN the Registry_Discovery_Agent initializes, THE Registry_Discovery_Agent SHALL sync with HOL registry for agent discovery
2. WHEN agent health checks are performed, THE Registry_Discovery_Agent SHALL monitor all 5 agents and report status
3. WHEN agent capabilities are queried, THE Registry_Discovery_Agent SHALL return current agent capabilities and availability
4. WHEN the frontend requests agent status, THE Registry_Discovery_Agent SHALL provide real-time agent health data
5. WHEN agents go offline, THE Registry_Discovery_Agent SHALL detect failures and update registry status
6. WHEN DISCOVER messages are received, THE Registry_Discovery_Agent SHALL respond with matching agent capabilities
7. THE Registry_Discovery_Agent SHALL cache agent information with TTL to reduce HOL queries

### Requirement 5: Evidence & Settlement Processing

**User Story:** As a compliance officer, I want consensus submission and audit reference generation, so that I can maintain immutable proof of all verification activities.

#### Acceptance Criteria

1. WHEN verification processes complete, THE Evidence_Settlement_Agent SHALL submit consensus data to Hedera blockchain
2. WHEN consensus is submitted, THE Evidence_Settlement_Agent SHALL generate audit reference numbers for tracking
3. WHEN audit references are created, THE Evidence_Settlement_Agent SHALL link them to original verification requests
4. WHEN settlement data is processed, THE Evidence_Settlement_Agent SHALL maintain audit trails for compliance reporting
5. WHEN blockchain transactions are submitted, THE Evidence_Settlement_Agent SHALL wait for transaction receipts
6. WHEN transaction failures occur, THE Evidence_Settlement_Agent SHALL implement retry logic with exponential backoff
7. THE Evidence_Settlement_Agent SHALL track HBAR costs for each transaction in Live_Mode

### Requirement 6: HCS-10 Messaging Protocol

**User Story:** As a system architect, I want standardized agent-to-agent communication, so that agents can interoperate reliably.

#### Acceptance Criteria

1. THE TruthForge System SHALL implement HCS-10 message types: REQUEST, RESPONSE, QUERY, NOTIFY, DISCOVER
2. WHEN an agent sends a message, THE TruthForge System SHALL include message type, sender ID, recipient ID, timestamp, and payload
3. WHEN a message is sent, THE TruthForge System SHALL submit the message to an HCS topic for immutable recording
4. WHEN a message is received, THE TruthForge System SHALL validate the message structure against HCS-10 schema
5. WHEN a REQUEST message is sent, THE TruthForge System SHALL expect a RESPONSE message within a timeout period
6. WHEN a DISCOVER message is sent, THE Registry_Discovery_Agent SHALL respond with matching agent capabilities

### Requirement 7: Orchestrator Coordination

**User Story:** As a system user, I want a single entry point for verification requests, so that I don't need to manage multiple agents directly.

#### Acceptance Criteria

1. WHEN a verification request is received, THE Orchestrator_Agent SHALL parse the request to determine required agent capabilities
2. WHEN agent capabilities are determined, THE Orchestrator_Agent SHALL route the request to appropriate specialized agents
3. WHEN multiple agents are needed, THE Orchestrator_Agent SHALL coordinate parallel execution and aggregate results
4. WHEN an agent fails to respond, THE Orchestrator_Agent SHALL implement retry logic with exponential backoff
5. WHEN all agent responses are collected, THE Orchestrator_Agent SHALL compile a unified verification report
6. WHEN the unified report is ready, THE Orchestrator_Agent SHALL return results to the requesting client

### Requirement 8: Responsive Frontend Interface

**User Story:** As a platform user, I want a responsive web interface that adapts to different devices, so that I can monitor port operations from desktop and mobile devices.

#### Acceptance Criteria

1. WHEN the frontend loads on desktop, THE Frontend SHALL display Agent Registry Table with tabular agent status view
2. WHEN the frontend loads on mobile, THE Frontend SHALL display Agent Registry Cards with stacked card layout
3. WHEN verification is in progress, THE Frontend SHALL show Port Trust Receipt Card with 4-step verification process
4. WHEN shipments are tracked, THE Frontend SHALL display Pre-Arrival Clearance Queue with shipment status
5. WHEN the dashboard loads, THE Frontend SHALL show operational metrics and port overview map
6. WHEN touch interactions occur on mobile, THE Frontend SHALL provide touch-friendly interface elements
7. WHEN the interface updates, THE Frontend SHALL maintain responsive behavior across all screen sizes

### Requirement 9: Natural Language Chat Interface

**User Story:** As a platform user, I want to interact with TruthForge using natural language, so that I can request verifications conversationally.

#### Acceptance Criteria

1. WHEN a user sends a chat message, THE Orchestrator_Agent SHALL analyze the message to extract verification intent
2. WHEN verification intent is detected, THE Orchestrator_Agent SHALL identify required parameters such as order ID or tracking number
3. WHEN parameters are missing, THE Orchestrator_Agent SHALL prompt the user for required information
4. WHEN all parameters are collected, THE Orchestrator_Agent SHALL construct a structured request for processing
5. WHEN verification results are received, THE Orchestrator_Agent SHALL format results into natural language responses
6. WHEN errors occur, THE Orchestrator_Agent SHALL explain the issue in user-friendly language

### Requirement 10: Dashboard and Operational Metrics

**User Story:** As a port operator, I want comprehensive dashboard with operational metrics, so that I can monitor port performance and clearance efficiency.

#### Acceptance Criteria

1. WHEN the dashboard loads, THE Frontend SHALL display operational metrics including clearance times and throughput
2. WHEN port data is available, THE Frontend SHALL show port overview map with current vessel positions
3. WHEN clearance comparisons are requested, THE Frontend SHALL display port clearance comparison charts
4. WHEN operational data updates, THE Frontend SHALL refresh metrics in real-time
5. WHEN HCS proofs are generated, THE Frontend SHALL display clickable links to view transactions on Hedera explorer
6. WHEN multiple verifications exist, THE Frontend SHALL maintain a transaction history with timestamps
7. WHEN system status changes, THE Frontend SHALL show integration status indicators

### Requirement 11: Configuration Management

**User Story:** As a system administrator, I want centralized configuration, so that I can manage API keys and settings securely.

#### Acceptance Criteria

1. THE TruthForge System SHALL load configuration from environment variables and .env files
2. THE TruthForge System SHALL require Hedera account ID, private key, and network configuration
3. THE TruthForge System SHALL require carrier API credentials for multiple shipping providers
4. THE TruthForge System SHALL require database connection parameters for persistent storage
5. WHERE sensitive credentials are missing, THE TruthForge System SHALL fail startup with clear error messages
6. WHERE Mock_Mode is enabled, THE TruthForge System SHALL allow operation without real API credentials
7. THE TruthForge System SHALL validate configuration completeness on startup

### Requirement 12: Mock Mode for Development

**User Story:** As a developer, I want to run TruthForge without real blockchain transactions, so that I can develop and demo without costs.

#### Acceptance Criteria

1. WHERE Mock_Mode is enabled, THE TruthForge System SHALL simulate HCS message submissions without blockchain transactions
2. WHERE Mock_Mode is enabled, THE Verification_Compliance_Agent SHALL return simulated authenticity scores based on test patterns
3. WHERE Mock_Mode is enabled, THE Carrier_Adapter_Agent SHALL return predefined shipment data for known tracking numbers
4. WHERE Mock_Mode is enabled, THE Evidence_Settlement_Agent SHALL use simulated consensus data instead of live blockchain calls
5. WHERE Mock_Mode is enabled, THE Frontend SHALL display a prominent indicator showing mock mode status
6. THE TruthForge System SHALL allow toggling between Mock_Mode and Live_Mode via configuration

### Requirement 13: Live Mode with Hedera Integration

**User Story:** As a platform operator, I want full Hedera blockchain integration, so that verifications are immutably recorded.

#### Acceptance Criteria

1. WHERE Live_Mode is enabled, THE TruthForge System SHALL submit all HCS-10 messages to configured HCS topics
2. WHERE Live_Mode is enabled, THE TruthForge System SHALL wait for transaction receipts before confirming operations
3. WHERE Live_Mode is enabled, THE TruthForge System SHALL handle transaction failures with retry logic
4. WHERE Live_Mode is enabled, THE Evidence_Settlement_Agent SHALL track HBAR costs for each transaction
5. WHERE Live_Mode is enabled, THE TruthForge System SHALL validate sufficient account balance before operations
6. WHERE Live_Mode is enabled, THE Frontend SHALL display actual HCS transaction IDs and consensus timestamps

### Requirement 14: API Endpoints

**User Story:** As a frontend developer, I want REST API endpoints, so that I can build user interfaces for TruthForge.

#### Acceptance Criteria

1. THE API SHALL provide POST /api/verify endpoint for submitting verification requests
2. THE API SHALL provide GET /api/status/{request_id} endpoint for checking verification progress
3. THE API SHALL provide GET /api/history endpoint for retrieving past verifications
4. THE API SHALL provide GET /api/agents endpoint for listing registered agent status
5. THE API SHALL provide GET /api/dashboard/metrics endpoint for operational metrics
6. THE API SHALL provide GET /api/clearance/queue endpoint for pre-arrival clearance data
7. WHEN API requests are received, THE API SHALL validate authentication tokens where required
8. WHEN API errors occur, THE API SHALL return structured error responses with HTTP status codes

### Requirement 15: Database Integration

**User Story:** As a system administrator, I want persistent data storage, so that verification history and agent status are maintained across system restarts.

#### Acceptance Criteria

1. THE Database SHALL store verification requests with timestamps, authenticity scores, and HCS transaction references
2. THE Database SHALL maintain agent registration data including capabilities, status, and health metrics
3. THE Database SHALL persist port clearance data for operational metrics and historical analysis
4. THE Database SHALL store audit trails for compliance reporting and evidence settlement
5. WHEN verification completes, THE Database SHALL record all verification details for future reference
6. WHEN agents update status, THE Database SHALL maintain current and historical agent health data
7. THE Database SHALL support both Mock_Mode and Live_Mode data segregation

### Requirement 16: Error Handling and Resilience

**User Story:** As a system operator, I want graceful error handling, so that temporary failures don't crash the system.

#### Acceptance Criteria

1. WHEN an agent fails to respond, THE Orchestrator_Agent SHALL log the failure and attempt alternate agents if available
2. WHEN API rate limits are hit, THE TruthForge System SHALL implement exponential backoff retry logic
3. WHEN network errors occur, THE TruthForge System SHALL retry operations up to 3 times before failing
4. WHEN blockchain transactions fail, THE Evidence_Settlement_Agent SHALL log transaction hashes and error details
5. WHEN critical errors occur, THE TruthForge System SHALL send notifications to configured monitoring endpoints
6. WHEN errors are returned to users, THE TruthForge System SHALL provide actionable error messages without exposing internal details

### Requirement 17: Testing Infrastructure

**User Story:** As a developer, I want comprehensive test coverage, so that I can validate system correctness.

#### Acceptance Criteria

1. THE TruthForge System SHALL include unit tests for each agent's core functionality
2. THE TruthForge System SHALL include integration tests for agent-to-agent communication
3. THE TruthForge System SHALL include end-to-end tests for complete verification workflows
4. THE TruthForge System SHALL include mock implementations for external APIs (carriers, Hedera)
5. THE TruthForge System SHALL include frontend property tests for responsive behavior
6. WHEN tests are run, THE TruthForge System SHALL generate coverage reports showing tested code percentage
7. THE TruthForge System SHALL include property-based tests for critical verification logic

### Requirement 18: Project Structure and Setup

**User Story:** As a developer, I want clear project organization, so that I can navigate and contribute to the codebase easily.

#### Acceptance Criteria

1. THE TruthForge System SHALL organize code into logical directories: agents/, api/, frontend/, database/, tests/
2. THE TruthForge System SHALL provide a requirements.txt file listing all Python dependencies
3. THE TruthForge System SHALL provide a .env.example file showing required configuration variables
4. THE TruthForge System SHALL include a README.md with setup instructions and architecture overview
5. THE TruthForge System SHALL include database migration scripts for schema management
6. THE TruthForge System SHALL include installation scripts for setting up development environments
7. THE TruthForge System SHALL document API endpoints in OpenAPI/Swagger format
