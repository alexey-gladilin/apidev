## ADDED Requirements

### Requirement: Transport Model Generation
`apidev gen` SHALL generate deterministic transport models for request, response, and declared error payloads from validated contracts.

#### Scenario: Request and response models are generated
- **WHEN** a contract defines request and success response schemas
- **THEN** generation SHALL produce corresponding model artifacts in generated transport zone
- **AND** regenerated output SHALL remain byte-stable for unchanged contract inputs

#### Scenario: Error models are generated from declared error contracts
- **WHEN** a contract declares explicit error responses
- **THEN** generation SHALL produce structured error model artifacts linked to the operation
- **AND** generated transport metadata SHALL expose the error mapping for OpenAPI/runtime wiring

### Requirement: Minimal Runnable Transport Layer
`apidev gen` SHALL generate a minimal runnable transport layer that can route validated operations to manual handler bridge implementations.

#### Scenario: Generated endpoint wiring is runnable
- **WHEN** generation completes for a project with valid contracts
- **THEN** generated router artifacts SHALL provide endpoint signatures and wiring stubs required for runtime startup
- **AND** generated code SHALL not contain business logic implementations

#### Scenario: Manual handler bridge contract is explicit
- **WHEN** a developer integrates generated transport with manual handlers
- **THEN** generated artifacts SHALL expose stable bridge signatures for handler invocation
- **AND** missing handler implementations SHALL fail deterministically during integration checks

### Requirement: Stable Operation Registry Contract
Generation SHALL maintain a stable operation registry contract that maps `operation_id` to transport metadata used by runtime and tests.

#### Scenario: Registry ordering is deterministic
- **WHEN** generation runs multiple times on the same contract set
- **THEN** operation registry output SHALL preserve deterministic ordering and content
- **AND** drift checks SHALL report no differences for unchanged inputs

#### Scenario: Registry includes transport metadata
- **WHEN** an operation is present in contracts
- **THEN** registry entries SHALL include method/path linkage and references to generated transport artifacts
- **AND** consumers SHALL resolve operation wiring using registry data without parsing contract files at runtime

### Requirement: Generated/Manual Ownership Boundary for Transport
Transport generation SHALL preserve clear ownership boundaries between generated transport artifacts and manual domain logic.

#### Scenario: Generated output does not overwrite manual logic
- **WHEN** `apidev gen` applies changes
- **THEN** writer behavior SHALL remain restricted to configured generated root
- **AND** manual application modules outside generated root SHALL not be modified

#### Scenario: Business logic remains manual-owned
- **WHEN** transport artifacts are regenerated
- **THEN** generated files SHALL contain only transport-facing contracts, routing, and schema metadata
- **AND** repository/service policy logic SHALL stay in manual-owned files
