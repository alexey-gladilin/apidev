## ADDED Requirements

### Requirement: Strict Contract Schema Validation
`apidev validate` SHALL perform strict schema validation for each YAML contract before semantic validation starts.

#### Scenario: Missing required schema field
- **WHEN** a contract misses a required field defined by the contract schema
- **THEN** validation SHALL emit a structured diagnostic with stable `code`
- **AND** the diagnostic SHALL include contract `location` and violated `rule`

#### Scenario: Invalid field type in schema
- **WHEN** a contract field contains a value with invalid type for the schema
- **THEN** validation SHALL emit a structured diagnostic with severity `error`
- **AND** the command SHALL finish with exit code `1`

### Requirement: Semantic Validation Layer
`apidev validate` SHALL execute semantic checks after successful parsing/schema stage and SHALL report semantic violations as structured diagnostics.

#### Scenario: Duplicate operation identifier
- **WHEN** two contracts resolve to the same `operation_id`
- **THEN** validation SHALL report a semantic diagnostic with a dedicated stable `code`
- **AND** diagnostic output SHALL identify both conflicting contract locations

#### Scenario: Semantic rule set is distinguishable
- **WHEN** semantic and schema violations are present in the same run
- **THEN** each diagnostic SHALL expose `rule` metadata
- **AND** consumers SHALL be able to distinguish schema-level vs semantic-level failures

### Requirement: Structured Diagnostics Contract
Validation diagnostics SHALL be represented in a structured model rather than free-form strings.

#### Scenario: Required diagnostic fields are present
- **WHEN** a validation violation is emitted
- **THEN** diagnostic SHALL contain `code`, `severity`, `message`, `location`, and `rule`
- **AND** diagnostics ordering SHALL be deterministic for stable CI outputs

### Requirement: JSON Output Mode for Validate Command
The CLI SHALL support machine-readable diagnostics output via `apidev validate --json`.

#### Scenario: JSON output in failure mode
- **WHEN** user runs `apidev validate --json` and there are validation errors
- **THEN** stdout SHALL be valid JSON with diagnostics array and summary
- **AND** process exit code SHALL be `1`

#### Scenario: JSON output in success mode
- **WHEN** user runs `apidev validate --json` and there are no errors
- **THEN** stdout SHALL be valid JSON with empty diagnostics and success summary
- **AND** process exit code SHALL be `0`

### Requirement: Backward-Compatible Human Output
Human-readable output SHALL remain the default behavior for `apidev validate` without `--json`.

#### Scenario: Default text output remains available
- **WHEN** user runs `apidev validate` without flags
- **THEN** command SHALL print human-readable diagnostics/results
- **AND** command SHALL not require JSON parsing for interactive use
