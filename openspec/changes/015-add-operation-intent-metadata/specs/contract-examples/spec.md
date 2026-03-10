## MODIFIED Requirements

### Requirement: Generated transport/OpenAPI metadata детерминированно сохраняет `example`
`apidev diff` и `apidev gen` SHALL включать принятый schema-level `example` в generated metadata так, чтобы неизменные контракты сохраняли byte-stable output, а изменение `example` приводило к обнаруживаемому drift. Example contracts с explicit `intent` и `access_pattern` SHALL сохранять эти поля без coercion, чтобы examples оставались согласованными с canonical contract.

#### Scenario: Explicit POST-read example stays deterministic
- **WHEN** example contract defines `method: POST`, `intent: read`, and `access_pattern: imperative`
- **THEN** validate/generate outputs SHALL preserve this metadata without coercing operation to write semantics
- **AND** repeated generation on unchanged inputs SHALL remain byte-stable

#### Scenario: Explicit GET-read example stays deterministic
- **WHEN** example contract defines `method: GET`, `intent: read`, and `access_pattern: cached`
- **THEN** validate/generate outputs SHALL preserve this metadata without coercing operation through transport heuristics
- **AND** repeated generation on unchanged inputs SHALL remain byte-stable

#### Scenario: Example documentation distinguishes POST-read from POST-write
- **WHEN** reviewer reads canonical contract examples
- **THEN** examples SHALL include at least one `GET` operation with `intent=read`
- **THEN** examples SHALL include at least one `POST` operation with `intent=read`
- **AND** examples SHALL include at least one `POST` operation with `intent=write`
- **AND** examples SHALL make the difference explicit through metadata rather than transport method alone

#### Scenario: Invalid metadata example is documented as rejected
- **WHEN** reviewer reads canonical contract examples or reference docs
- **THEN** documentation SHALL include at least one invalid `intent/access_pattern` combination
- **AND** the example SHALL be marked as rejected by `apidev validate`
