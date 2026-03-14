# Implementation Plan: TruthForge

## Overview

This implementation plan breaks down the TruthForge reality-verified trade platform into discrete, incremental coding tasks. The approach follows a bottom-up strategy: build core infrastructure first (messaging, agent base classes, database), then implement the 5 specialized agents, integrate carrier services, and finally wire everything together through the orchestrator and responsive frontend interface.

Each task builds on previous work, ensuring no orphaned code. Testing tasks are marked as optional (*) to enable faster MVP delivery while maintaining the option for comprehensive testing.

## Tasks

- [x] 1. Set up project structure and core dependencies
  - Create directory structure: agents/, api/, frontend/, database/, tests/
  - Create requirements.txt with dependencies: hedera-sdk-python, flask, flask-cors, pillow, langchain, pytest, hypothesis, sqlalchemy, psycopg2
  - Create .env.example with all required configuration variables including database settings
  - Create README.md with setup instructions
  - _Requirements: 18.1, 18.2, 18.3, 18.4_

- [x] 2. Implement configuration management and database setup
  - [x] 2.1 Create Config class to load environment variables
    - Implement Config dataclass with all required fields (Hedera, database, carriers, system settings)
    - Implement load() method to read from .env file
    - Implement validation to check required fields based on mode (mock vs live)
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.7_
  
  - [x] 2.2 Create Database class for persistent storage
    - Implement Database class with connection management
    - Implement basic CRUD operations (insert, update, delete, query)
    - Implement table creation and schema migration methods
    - Support both SQLite (development) and PostgreSQL (production)
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 18.5_
  
  - [x] 2.3 Write unit tests for configuration loading and database operations
    - Test successful config loading with all fields
    - Test validation failures for missing required fields
    - Test mock mode allows missing API credentials
    - Test live mode requires all credentials
    - Test database connection and basic operations
    - _Requirements: 11.5, 11.6, 15.7_

- [x] 3. Implement HCS-10 messaging protocol
  - [x] 3.1 Create HCS10Message class with all required fields
    - Implement MessageType enum (REQUEST, RESPONSE, QUERY, NOTIFY, DISCOVER)
    - Implement HCS10Message dataclass with validation
    - Implement to_hcs_format() and from_hcs_format() serialization methods
    - Implement signature generation and validation
    - _Requirements: 5.1, 5.2_
  
  - [x] 3.2 Write property test for HCS-10 message structure

    - **Property 17: HCS-10 Message Structure**
    - **Validates: Requirements 5.2**
  
  - [x] 3.3 Write property test for invalid message rejection

    - **Property 19: Invalid Message Rejection**
    - **Validates: Requirements 5.4**

- [x] 4. Implement Hedera client with mock mode support
  - [x] 4.1 Create HederaClient class for blockchain operations
    - Implement authenticate() method using account ID and private key
    - Implement submit_message() method to send HCS messages
    - Implement get_transaction_receipt() method
    - Implement balance checking before transactions
    - _Requirements: 12.1, 12.2, 12.5_
  
  - [x] 4.2 Create MockHederaClient for development
    - Implement mock submit_message() that returns fake transaction IDs
    - Implement mock get_transaction_receipt() with simulated timestamps
    - Track mock transaction costs without real HBAR spending
    - _Requirements: 11.1_
  
  - [x] 4.3 Write property test for HCS message submission


    - **Property 18: HCS Message Submission**
    - **Validates: Requirements 5.3**
  
  - [x] 4.4 Write property test for production mode cost tracking

    - **Property 46: Production Mode Cost Tracking**
    - **Validates: Requirements 12.4**

- [x] 5. Implement base agent class with database integration
  - [x] 5.1 Create BaseAgent abstract class
    - Implement __init__ with agent_id, capabilities, hcs_topic_id, database
    - Implement register_with_hol() method
    - Implement send_message() and receive_message() methods using HederaClient
    - Implement abstract process_request() method
    - Implement health_check() method returning AgentStatus
    - Implement persist_data() method for database operations
    - _Requirements: 1.1, 1.3, 1.4, 15.5_
  
  - [x] 5.2 Write property test for agent registration persistence

    - **Property 3: Agent Registration Persistence**
    - **Validates: Requirements 1.3, 1.4**
  
  - [x] 5.3 Write property test for agent re-registration idempotence

    - **Property 4: Agent Re-registration Idempotence**
    - **Validates: Requirements 1.5**

- [x] 6. Implement HOL registry with 5-agent support
  - [x] 6.1 Create HOLRegistry class for agent registration
    - Implement register_agent() method to store agent metadata
    - Implement query_agents() method with capability filtering
    - Implement get_agent_status() method
    - Implement in-memory storage with optional database persistence
    - _Requirements: 1.2, 1.3_
  
  - [x] 6.2 Write property test for agent registration uniqueness and count

    - **Property 1: Agent Registration Count**
    - **Property 2: Agent Registration Uniqueness**
    - **Validates: Requirements 1.1, 1.2**
  
  - [x] 6.3 Write unit test for 5 agent registration
    - Test that system initializes with exactly 5 registered agents
    - Verify all agent IDs match expected values: truthforge-orch-001, truthforge-verify-001, truthforge-carrier-001, truthforge-registry-001, truthforge-evidence-001
    - _Requirements: 1.1, 1.2_

- [x] 7. Implement Verification & Compliance Agent (combined deepfake detection and document verification)
  - [x] 7.1 Create VerificationComplianceAgent class extending BaseAgent
    - Implement analyze_image() orchestration method
    - Implement exif_analysis() using Pillow to extract EXIF data
    - Implement lighting_analysis() to detect lighting inconsistencies
    - Implement ai_artifact_detection() to find AI-generated artifacts
    - Implement metadata_verification() to check metadata consistency
    - Implement compute_authenticity_score() to aggregate layer scores
    - Implement generate_forensic_report() to compile all findings
    - Implement extract_bol_fields() to parse BOL documents
    - Implement validate_compliance() to check compliance requirements
    - Implement cross_reference_shipment() to compare BOL with carrier data
    - Implement flag_discrepancies() to identify mismatches
    - Implement generate_verification_report() to compile results
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8_
  
  - [ ]* 7.2 Write property test for 4-layer execution
    - **Property 5: Verification 4-Layer Execution**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
  
  - [ ]* 7.3 Write property test for authenticity score bounds
    - **Property 6: Authenticity Score Bounds**
    - **Validates: Requirements 2.5**
  
  - [ ] 7.4 Write property test for analysis report completeness

    - **Property 7: Analysis Report Completeness**
    - **Validates: Requirements 2.6**
  
  - [x] 7.5 Integrate HCS timestamping for verification results
    - Call HederaClient.submit_message() after analysis completes
    - Store HCS transaction ID in AnalysisResult and VerificationReport
    - _Requirements: 2.7_
  
  - [x] 7.6 Write property test for HCS timestamping consistency

    - **Property 8: HCS Timestamping Consistency**
    - **Validates: Requirements 2.7, 3.7, 5.1**

- [x] 8. Checkpoint - Ensure Verification & Compliance Agent tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement Carrier Adapter Agent (Council-Grade multi-carrier support)
  - [x] 9.1 Create CarrierAdapterAgent class extending BaseAgent
    - Implement authenticate_carrier() for multiple carriers (FedEx, UPS, DHL)
    - Implement normalize_tracking_data() to convert carrier-specific data to unified schema
    - Implement query_shipment() to fetch tracking data from appropriate carrier API
    - Implement get_supported_carriers() to return list of supported carriers
    - Implement handle_rate_limits() for carrier-specific rate limiting
    - Implement validate_tracking_format() to identify carrier from tracking number
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 9.2 Create MockCarrierAdapter for development
    - Implement mock query_shipment() returning predefined data for multiple carriers
    - Support test tracking numbers with realistic responses
    - _Requirements: 3.6_
  
  - [x] 9.3 Write property test for carrier data normalization

    - **Property 9: Carrier Data Normalization**
    - **Validates: Requirements 3.1, 3.3**
  
  - [x] 9.4 Write property test for multi-carrier query execution

    - **Property 10: Multi-Carrier Query Execution**
    - **Validates: Requirements 3.2**
  
  - [x] 9.5 Write property test for carrier error handling

    - **Property 11: Carrier Error Handling**
    - **Validates: Requirements 3.4, 3.5**
  
  - [x] 9.6 Write property test for mock mode data simulation

    - **Property 12: Mock Mode Data Simulation**
    - **Validates: Requirements 3.6, 12.1, 12.2, 12.3, 12.4, 12.5**
  
  - [x] 9.7 Integrate HCS timestamping for carrier operations
    - Call HederaClient.submit_message() after carrier verification completes
    - Store HCS transaction ID in carrier operation results
    - _Requirements: 3.7_

- [x] 10. Implement Registry & Discovery Agent
  - [x] 10.1 Create RegistryDiscoveryAgent class extending BaseAgent
    - Implement sync_with_hol() to synchronize with HOL registry
    - Implement monitor_agent_health() to check all 5 agents
    - Implement discover_agents() to find agents by capabilities
    - Implement update_agent_status() to maintain current status
    - Implement get_agent_capabilities() to return agent capabilities
    - Implement handle_discover_message() to process DISCOVER messages
    - Implement cache_agent_info() with TTL-based caching
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  
  - [x] 10.2 Write property test for registry agent health monitoring

    - **Property 13: Registry Agent Health Monitoring**
    - **Validates: Requirements 4.2, 4.4**
  
  - [x] 10.3 Write property test for agent discovery response matching

    - **Property 14: Agent Discovery Response Matching**
    - **Validates: Requirements 4.6**
  
  - [x] 10.4 Write property test for agent discovery caching

    - **Property 15: Agent Discovery Caching**
    - **Validates: Requirements 4.7**

- [x] 11. Implement Evidence & Settlement Agent
  - [x] 11.1 Create EvidenceSettlementAgent class extending BaseAgent
    - Implement submit_consensus() to submit verification data to Hedera blockchain
    - Implement generate_audit_reference() to create audit reference numbers
    - Implement create_audit_trail() to maintain compliance audit trails
    - Implement track_transaction_costs() to monitor HBAR costs in Live Mode
    - Implement retry_failed_transaction() with exponential backoff
    - Implement validate_account_balance() to check sufficient HBAR
    - Implement get_transaction_receipt() to retrieve transaction confirmations
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_
  
  - [x] 11.2 Write property test for evidence settlement audit trail

    - **Property 16: Evidence Settlement Audit Trail**
    - **Validates: Requirements 5.2, 5.3, 5.4**
  
  - [x] 11.3 Write property test for transaction receipt handling

    - **Property 17: Transaction Receipt Handling**
    - **Validates: Requirements 5.5, 5.7, 13.4, 13.5**
  
  - [x] 11.4 Write property test for transaction retry logic

    - **Property 18: Transaction Retry Logic**
    - **Validates: Requirements 5.6, 13.3**

- [x] 12. Checkpoint - Ensure all agent tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement Orchestrator Agent with workflow coordination
  - [x] 13.1 Create OrchestratorAgent class extending BaseAgent
    - Implement parse_intent() to analyze natural language messages
    - Implement route_request() to determine required agents
    - Implement coordinate_agents() for parallel agent execution
    - Implement aggregate_results() to compile unified reports
    - Implement handle_agent_failure() with retry logic
    - Implement execute_workflow() for different workflow types
    - Implement request-response timeout handling
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [x] 13.2 Write property test for HCS-10 message structure

    - **Property 19: HCS-10 Message Structure**
    - **Validates: Requirements 6.1, 6.2**
  
  - [x] 13.3 Write property test for HCS message submission

    - **Property 20: HCS Message Submission**
    - **Validates: Requirements 6.3**
  
  - [x] 13.4 Write integration test for complete verification flow

    - Test end-to-end: request → routing → agents → aggregation → response
    - Verify all agents are called correctly
    - Verify results are properly aggregated
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.6_

- [x] 14. Implement error handling and resilience
  - [x] 14.1 Add exponential backoff retry logic
    - Implement retry_with_backoff() utility function
    - Apply to network operations and API calls
    - _Requirements: 16.2_
  
  - [x] 14.2 Add network error retry logic
    - Wrap network operations with retry decorator (max 3 attempts)
    - Log each retry attempt
    - _Requirements: 16.3_
  
  - [x] 14.3 Add blockchain transaction error handling
    - Implement transaction retry logic for Live_Mode
    - Log transaction failures with details
    - _Requirements: 13.3, 16.4_
  
  - [x] 14.4 Write unit tests for error handling
    - Test exponential backoff timing
    - Test network error retry count
    - Test transaction failure logging
    - Test Live mode transaction retry
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 13.3_

- [x] 15. Implement Flask API server with new endpoints
  - [x] 15.1 Create Flask app with CORS support
    - Set up Flask application with CORS configuration
    - Implement POST /api/verify endpoint
    - Implement GET /api/status/{request_id} endpoint
    - Implement GET /api/history endpoint
    - Implement GET /api/agents endpoint
    - Implement GET /api/dashboard/metrics endpoint for operational metrics
    - Implement GET /api/clearance/queue endpoint for pre-arrival clearance data
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_
  
  - [x] 15.2 Add authentication middleware
    - Implement token validation for protected endpoints
    - Return 401 for missing/invalid tokens
    - _Requirements: 14.7_
  
  - [x] 15.3 Add structured error response handling
    - Implement error handler middleware
    - Return consistent JSON error format
    - Map exceptions to appropriate HTTP status codes
    - _Requirements: 14.8_
  
  - [x] 15.4 Write unit tests for API endpoints
    - Test POST /api/verify with valid request
    - Test GET /api/status returns correct status
    - Test GET /api/history returns verification list
    - Test GET /api/agents returns agent status
    - Test GET /api/dashboard/metrics returns operational data
    - Test GET /api/clearance/queue returns clearance data
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [x] 16. Implement responsive frontend interface
  - [x] 16.1 Update HTML structure for responsive design
    - Modify existing chat interface to be responsive
    - Add Agent Registry Table for desktop view
    - Add Agent Registry Cards for mobile view
    - Add Port Trust Receipt Card with 4-step verification process
    - Add Pre-Arrival Clearance Queue with shipment tracking
    - Add Dashboard with operational metrics and port overview map
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [x] 16.2 Update CSS styling for responsive behavior
    - Add responsive breakpoints for desktop/mobile layouts
    - Style Agent Registry Table (desktop) and Cards (mobile)
    - Style Port Trust Receipt Card with step indicators
    - Style Pre-Arrival Clearance Queue with status indicators
    - Style Dashboard with metrics and map components
    - Add touch-friendly interface elements for mobile
    - _Requirements: 8.6, 8.7_
  
  - [x] 16.3 Update JavaScript for new functionality
    - Implement responsive layout switching based on viewport
    - Implement displayAgentRegistryTable() for desktop
    - Implement displayAgentRegistryCards() for mobile
    - Implement displayPortTrustReceipt() with 4-step process
    - Implement displayClearanceQueue() with shipment tracking
    - Implement displayDashboardMetrics() with real-time updates
    - Implement updateOperationalMetrics() for dashboard
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 10.1, 10.2, 10.4_
  
  - [x] 16.4 Write property test for frontend responsive behavior
    - **Property 21: Frontend Responsive Behavior**
    - **Validates: Requirements 8.1, 8.2, 8.6, 8.7**
  
  - [x] 16.5 Write property test for port trust receipt 4-step process
    - **Property 22: Port Trust Receipt 4-Step Process**
    - **Validates: Requirements 8.3**
  
  - [x] 16.6 Write property test for dashboard metrics display
    - **Property 23: Dashboard Metrics Display**
    - **Validates: Requirements 10.1, 10.2, 10.4**

- [x] 17. Checkpoint - Ensure API and frontend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Wire all components together
  - [x] 18.1 Create main application entry point
    - Initialize Config from environment
    - Initialize Database connection
    - Initialize HederaClient (mock or live based on config)
    - Initialize HOLRegistry
    - Register all 5 agents with HOL
    - Start Flask API server
    - _Requirements: 1.1, 11.1, 15.1_
  
  - [x] 18.2 Connect Orchestrator to all agents
    - Wire Orchestrator to Verification & Compliance Agent
    - Wire Orchestrator to Carrier Adapter Agent
    - Wire Orchestrator to Registry & Discovery Agent
    - Wire Orchestrator to Evidence & Settlement Agent
    - _Requirements: 7.2_
  
  - [x] 18.3 Connect API endpoints to agents
    - Wire /api/verify to Orchestrator.process_request()
    - Wire /api/agents to Registry & Discovery Agent
    - Wire /api/dashboard/metrics to Database queries
    - Wire /api/clearance/queue to Database queries
    - _Requirements: 14.1, 14.4, 14.5, 14.6_
  
  - [x] 18.4 Connect database to all agents
    - Wire all agents to Database for persistence
    - Wire verification results to Database storage
    - Wire audit trails to Database storage
    - Wire agent status to Database storage
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

- [ ] 19. Final checkpoint - End-to-end testing
  - [ ]* 19.1 Run complete verification workflow test
    - Test: User request → Orchestrator → Verification & Compliance → HCS → Response
    - Verify authenticity score is returned
    - Verify HCS transaction ID is present
    - _Requirements: 2.5, 2.7, 7.6_
  
  - [ ]* 19.2 Run carrier integration test
    - Test: Tracking number → Carrier Adapter → Multi-carrier query → Normalized data
    - Verify carrier data is normalized to unified schema
    - Verify error handling for unavailable carriers
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ]* 19.3 Run agent discovery test
    - Test: DISCOVER message → Registry & Discovery Agent → HOL query → Response
    - Verify all 5 agents are discoverable
    - Verify capability filtering works
    - _Requirements: 4.1, 4.2, 4.3, 4.6_
  
  - [ ]* 19.4 Run evidence settlement test
    - Test: Verification complete → Evidence & Settlement → Blockchain → Audit reference
    - Verify audit references are generated
    - Verify audit trails are maintained
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ]* 19.5 Run responsive frontend test
    - Test: Desktop viewport → Agent Registry Table displayed
    - Test: Mobile viewport → Agent Registry Cards displayed
    - Test: Port Trust Receipt Card shows 4-step process
    - Test: Dashboard displays operational metrics
    - _Requirements: 8.1, 8.2, 8.3, 10.1, 10.2_
  
  - [ ]* 19.6 Run database persistence test
    - Test: Verification complete → Database storage → Data retrieval
    - Verify verification history is maintained
    - Verify audit trails are stored
    - Verify Mock/Live mode data segregation
    - _Requirements: 15.1, 15.5, 15.7_
  
  - [ ]* 19.7 Run mock mode validation
    - Test system operates without real API credentials
    - Verify mock HCS transactions return fake IDs
    - Verify mock carriers return predefined data
    - Verify mock evidence settlement uses simulated data
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ]* 19.8 Run live mode validation (if credentials available)
    - Test real HCS message submission to testnet
    - Test real transaction receipt retrieval
    - Test HBAR cost tracking
    - Test balance validation
    - _Requirements: 13.1, 13.2, 13.4, 13.5_
  
  - [ ]* 19.9 Test splash screen functionality
    - Test: Application loads → Splash screen displays for 2.5 seconds → Fades to main app
    - Verify TruthForge logo displays correctly with zoom-out animation
    - Verify "Initializing Verification Network..." text appears with fade-in
    - Verify loading dots animate correctly
    - Verify splash screen is responsive on mobile, tablet, and desktop
    - Verify smooth fade-out transition to main application
    - Verify logo asset loads correctly from src/assets/truthforge-logo.png
    - _Component: src/components/SplashScreen.tsx_
    - _Documentation: SPLASH_SCREEN.md_
  
  - [ ]* 19.10 Test footer functionality and layout
    - Test: Footer appears on all pages (WelcomePage, Index, OperatorDashboardPage, SignInPage)
    - Verify footer stays at bottom of page with short content
    - Verify footer doesn't overlap with page content
    - Verify footer is responsive on mobile (single column), tablet (3 columns), and desktop (3 columns)
    - Verify all navigation links work correctly:
      - Platform section: Dashboard, Port Operations, Supply Chain Intelligence
      - Resources section: Documentation, Privacy
    - Verify footer displays correct branding:
      - TruthForge logo and name
      - Tagline: "The Verifiable Intelligence Layer for Global Trade"
      - Subline: "AI-powered verification for global supply chain operations"
      - Copyright: "© 2026 TruthForge. Built on Hedera."
    - Verify hover states work on all links (teal accent color)
    - Verify footer uses correct TruthForge theme colors (navy background, teal accents)
    - Verify no horizontal scrolling on mobile devices
    - _Component: src/components/Footer.tsx_
    - _Documentation: FOOTER_IMPLEMENTATION.md_
    - _Pages Updated: Index.tsx, WelcomePage.tsx, OperatorDashboardPage.tsx, SignInPage.tsx_
  
  - [ ]* 19.11 Test frontend layout structure
    - Test: All pages use proper flexbox layout (min-h-screen flex flex-col)
    - Verify main content area uses flex-grow to fill available space
    - Verify footer uses mt-auto to push to bottom
    - Verify no content overlap between main content and footer
    - Verify consistent spacing across all pages
    - _Requirements: 8.6, 8.7_
  
  - [ ]* 19.12 Test tagline updates across the application
    - Test: WelcomePage displays correct tagline under TruthForge logo
      - Verify tagline reads: "The Verifiable Intelligence Layer for Global Trade"
      - Verify tagline is properly styled and responsive
      - _Component: src/pages/WelcomePage.tsx_
    - Test: Header component displays correct tagline under logo
      - Verify tagline reads: "The Verifiable Intelligence Layer"
      - Verify tagline is visible on desktop (hidden on mobile due to space)
      - Verify tagline uses uppercase styling
      - _Component: src/components/Header.tsx_
  
  - [ ]* 19.13 Test Container Intelligence Panel functionality
    - Test: Pre-Clearance Intelligence Panel displays Container Intelligence section
      - Verify Vessel Trust Score calculation is accurate (0-100 based on verification rate)
      - Verify Container Visualization Grid displays color-coded squares (green/red/gray)
      - Verify Container Verification Table shows all containers with status and risk level
      - Verify table supports scrolling for 50+ containers
      - Verify emoji icons display correctly (🚢 📦 📊 🧾)
      - Verify trust score color coding (green 80-100, yellow 50-79, red <50)
      - Verify trust score interpretation text updates correctly
    - Test: Container data flows correctly from mock-data
      - Verify generateContainers() creates proper container arrays
      - Verify container status badges display correctly (verified/flagged/pending)
      - Verify risk level badges display correctly (low/medium/high)
    - _Component: src/components/PreClearanceIntelligencePanel.tsx_
    - _Mock Data: src/lib/mock-data.ts_
    - _Documentation: CONTAINER_INTELLIGENCE_IMPLEMENTATION.md_
  
  - [ ]* 19.14 Test Global Trade Risk Command Center functionality
    - Test: Command Center displays at top of dashboard
      - Verify Global Shipment Map shows route visualization
      - Verify routes display correct status colors (green/yellow/red)
      - Verify route legend displays correctly
      - Verify route list shows origin → destination with status
    - Test: Active Shipment Feed displays live events
      - Verify events display with correct icons (verified/flagged/completed)
      - Verify timestamps and locations display correctly
      - Verify feed scrolls properly with multiple events
    - Test: AI Risk Alerts panel displays alerts
      - Verify alerts display with correct severity badges (high/medium/low)
      - Verify alert types display correctly (risk/compliance/inspection)
      - Verify alert icons and colors match alert type
    - Test: Responsive layout on mobile/tablet/desktop
      - Verify 3-column layout on desktop (map + feed + alerts)
      - Verify stacked layout on mobile
      - Verify all emoji icons display correctly (🌍 📡 ⚠️)
    - _Component: src/components/GlobalTradeRiskCommandCenter.tsx_
    - _Mock Data: src/lib/mock-data.ts (mockShipmentRoutes, mockActivityEvents, mockRiskAlerts)_
    - _Page: src/pages/DashboardPage.tsx_
  
  - [ ]* 19.15 Test Verification Fee & Wallet Integration functionality
    - Test: Port Trust Receipt displays verification fees
      - Verify Verification Fee Summary section displays correctly
      - Verify itemized costs (shipment/container/network fees)
      - Verify total paid calculation is accurate
      - Verify payment network and currency display
      - Verify Payment Transaction section shows status
      - Verify transaction ID and timestamp display
      - Verify wallet used information displays
    - Test: Pre-Clearance Request Modal functionality
      - Verify modal opens from "Request Pre-Clearance" button
      - Verify wallet connection check works
      - Verify warning banner displays when wallet not connected
      - Verify success banner displays when wallet connected
      - Verify estimated cost displays and updates dynamically
      - Verify cost calculation for sea freight (per container)
      - Verify cost calculation for air freight (per cargo unit)
      - Verify cost calculation for land freight (flat rate)
    - Test: Transport mode selection
      - Verify sea/air/land mode buttons work
      - Verify form fields change based on mode
      - Verify all required fields validate
    - Test: Payment confirmation workflow
      - Verify payment dialog appears after form submission
      - Verify final cost displays correctly
      - Verify confirm/cancel buttons work
      - Verify transaction processes on confirmation
    - Test: Wallet integration
      - Verify useWallet() hook integration
      - Verify wallet address displays correctly
      - Verify network information displays
      - Verify submission blocked without wallet
    - _Components: src/components/PortTrustReceipt.tsx, src/components/PreClearanceRequestModal.tsx_
    - _Page: src/pages/TrackingPage.tsx_
    - _Mock Data: src/lib/mock-data.ts (PortTrustReceipt interface extended)_
    - _Context: src/contexts/WalletContext.tsx_
    - _Documentation: VERIFICATION_FEE_WALLET_INTEGRATION.md_
  
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases
- Integration tests validate component interactions
- Mock implementations enable development without blockchain costs
- All 25 correctness properties from the design document have corresponding test tasks
- Database integration provides persistent storage for verification history and audit trails
- Responsive frontend supports both desktop (tables) and mobile (cards) layouts
- Multi-carrier support enables Council-Grade carrier data integration
