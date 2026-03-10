## MODIFIED Requirements

### Requirement: Stable Operation Registry Contract
Generation SHALL maintain a stable operation registry contract that maps `operation_id` to transport metadata used by runtime and tests, including domain-qualified module references and downstream-facing operation semantics metadata.

#### Scenario: Registry publishes operation intent and access pattern
- **WHEN** operation contract declares `intent` and `access_pattern`
- **THEN** generated registry entry SHALL include both values verbatim
- **AND** downstream consumers SHALL be able to read them without reparsing YAML

#### Scenario: Registry generation requires explicit metadata
- **WHEN** operation contract omits `intent` or `access_pattern`
- **THEN** generation SHALL fail before emitting registry metadata for that operation
- **AND** generated outputs SHALL NOT invent metadata from HTTP method

### Requirement: OpenAPI integration is assembled from generated metadata
Generated OpenAPI integration SHALL preserve downstream-facing operation semantics metadata via deterministic vendor extensions.

#### Scenario: OpenAPI publishes intent and access pattern
- **WHEN** operation contract declares `intent` and `access_pattern`
- **THEN** generated OpenAPI operation SHALL include vendor extensions `x-apidev-intent` and `x-apidev-access-pattern`
- **AND** generated values SHALL match the registry metadata for the same operation

#### Scenario: OpenAPI generation rejects missing metadata
- **WHEN** operation contract omits `intent` or `access_pattern`
- **THEN** OpenAPI generation SHALL fail via the same explicit metadata requirement as registry generation
- **AND** repeated generation on unchanged invalid contracts SHALL remain deterministic
