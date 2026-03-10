## MODIFIED Requirements

### Requirement: Generated transport/OpenAPI metadata детерминированно сохраняет contract metadata
`apidev diff` и `apidev gen` SHALL детерминированно сохранять author-declared operation metadata, включая explicit `intent` и `access_pattern`, так чтобы downstream consumers и examples оставались согласованными с canonical contract.

#### Scenario: Explicit POST-read example stays deterministic
- **WHEN** example contract defines `method: POST`, `intent: read`, and `access_pattern: imperative`
- **THEN** validate/generate outputs SHALL preserve this metadata without coercing operation to write semantics
- **AND** repeated generation on unchanged inputs SHALL remain byte-stable

#### Scenario: Example documentation distinguishes POST-read from POST-write
- **WHEN** reviewer reads canonical contract examples
- **THEN** examples SHALL include at least one `POST` operation with `intent=read`
- **AND** examples SHALL include at least one `POST` operation with `intent=write`
- **AND** examples SHALL make the difference explicit through metadata rather than transport method alone
