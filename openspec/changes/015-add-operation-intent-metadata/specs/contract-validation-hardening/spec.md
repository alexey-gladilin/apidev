## MODIFIED Requirements

### Requirement: Strict Contract Schema Validation
`apidev validate` SHALL perform strict schema validation for each YAML contract before semantic validation starts, including root-level operation metadata fields `intent` and `access_pattern`.

#### Scenario: Operation metadata fields are accepted by schema validation
- **WHEN** operation contract defines valid root-level fields `intent` and `access_pattern`
- **THEN** schema validation SHALL accept them without unknown-field diagnostics

#### Scenario: Allowed read metadata combination is accepted
- **WHEN** operation contract defines `intent=read` and `access_pattern` as one of `cached | imperative | both | none`
- **THEN** schema and semantic validation SHALL accept the combination
- **AND** command SHALL finish with exit code `0`

#### Scenario: Allowed write metadata combination is accepted
- **WHEN** operation contract defines `intent=write` and `access_pattern` as one of `imperative | none`
- **THEN** schema and semantic validation SHALL accept the combination
- **AND** command SHALL finish with exit code `0`

### Requirement: Semantic Validation Layer
`apidev validate` SHALL execute semantic checks after successful parsing/schema stage and SHALL report semantic violations as structured diagnostics, including invalid combinations of `intent` and `access_pattern`.

#### Scenario: Invalid intent value is rejected
- **WHEN** operation contract defines `intent` outside the allowed set `read | write`
- **THEN** validation SHALL emit a semantic diagnostic with stable `code`
- **AND** command SHALL finish with exit code `1`

#### Scenario: Invalid access pattern value is rejected
- **WHEN** operation contract defines `access_pattern` outside the allowed set `cached | imperative | both | none`
- **THEN** validation SHALL emit a semantic diagnostic with stable `code`
- **AND** command SHALL finish with exit code `1`

#### Scenario: Write operation cannot declare cached access
- **WHEN** operation contract defines `intent=write` and `access_pattern=cached`
- **THEN** validation SHALL emit a semantic diagnostic with stable `code`
- **AND** command SHALL explain that cached access is incompatible with write intent in the first version

#### Scenario: Write operation cannot declare both access patterns
- **WHEN** operation contract defines `intent=write` and `access_pattern=both`
- **THEN** validation SHALL emit a semantic diagnostic with stable `code`
- **AND** command SHALL finish with exit code `1`

#### Scenario: Missing intent is rejected
- **WHEN** operation contract omits required field `intent`
- **THEN** validation SHALL emit a structured schema diagnostic with stable `code`
- **AND** diagnostic `rule` SHALL classify the failure as schema validation rather than semantic validation
- **AND** command SHALL finish with exit code `1`

#### Scenario: Missing access pattern is rejected
- **WHEN** operation contract omits required field `access_pattern`
- **THEN** validation SHALL emit a structured schema diagnostic with stable `code`
- **AND** diagnostic `rule` SHALL classify the failure as schema validation rather than semantic validation
- **AND** command SHALL finish with exit code `1`
