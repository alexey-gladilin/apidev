## ADDED Requirements

### Requirement: Compatibility classification for contract evolution
`apidev diff` and `apidev gen --check` SHALL classify detected contract changes into compatibility categories and expose this classification in diagnostics.

#### Scenario: Diff reports breaking and non-breaking groups
- **WHEN** user runs `apidev diff` after modifying contracts
- **THEN** output SHALL include categorized compatibility summary
- **AND** each detected change SHALL be assigned to a deterministic compatibility category

#### Scenario: Check mode can fail on breaking changes
- **WHEN** configured breaking-aware policy is active and `apidev gen --check` detects `breaking` changes
- **THEN** command SHALL return non-zero exit code
- **AND** diagnostics SHALL explicitly list breaking change reasons

### Requirement: Optional read-only DBSpec integration
APIDev SHALL support optional integration with `dbspec` as a read-only source of schema hints without requiring `dbspec` for baseline workflows.

#### Scenario: Workflow stays operational without DBSpec
- **WHEN** `dbspec` artifacts are unavailable
- **THEN** `apidev validate`, `apidev diff`, and `apidev gen` SHALL continue in baseline mode
- **AND** tool SHALL NOT require DBSpec as mandatory dependency

#### Scenario: Contract data has priority over external hints
- **WHEN** both contract fields and optional dbspec hints provide values for the same schema attribute
- **THEN** deterministic merge policy SHALL apply
- **AND** contract-declared value SHALL take priority

### Requirement: Formal deprecation lifecycle
The system SHALL enforce a formal deprecation lifecycle for evolving contract elements to reduce unmanaged breaking removals.

#### Scenario: Deprecated element is tracked before removal
- **WHEN** contract element is marked as deprecated
- **THEN** diagnostics and generated metadata SHALL expose deprecation status
- **AND** lifecycle state SHALL be preserved across subsequent diff/generate runs

#### Scenario: Removing without deprecation window is breaking
- **WHEN** a previously active element is removed without passing through a defined deprecation period
- **THEN** change SHALL be classified as `breaking`
- **AND** diagnostics SHALL include policy violation details
