## MODIFIED Requirements

### Requirement: Validate-First Safety Pipeline
`apidev diff` и `apidev gen` SHALL выполнять preflight validation перед вычислением diff-плана и перед применением изменений, включая обязательные operation metadata fields `intent` и `access_pattern`.

#### Scenario: Missing operation metadata blocks diff and generation
- **WHEN** любой operation contract omits required field `intent` or `access_pattern`
- **THEN** `apidev diff`, `apidev gen --check`, and `apidev gen` SHALL fail in preflight validation before diff/apply planning
- **AND** commands SHALL NOT invent metadata from HTTP method
- **AND** human-readable and JSON outputs SHALL preserve deterministic failure semantics for the validation error
