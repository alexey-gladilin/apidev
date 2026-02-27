## ADDED Requirements

### Requirement: Contract supports endpoint-level `examples` block
`apidev validate` SHALL accept optional root-level block `examples` for operation payload examples used by generated OpenAPI metadata.

#### Scenario: Endpoint-level request and success response examples are accepted
- **WHEN** contract defines `examples.request` and `examples.response`
- **THEN** validation SHALL accept these fields when payload shape is compatible with declared schemas

#### Scenario: Endpoint-level error example is accepted per declared error code
- **WHEN** contract defines `examples.errors.<ERROR_CODE>`
- **THEN** validation SHALL ensure `<ERROR_CODE>` exists in `errors[*].code`
- **AND** example payload SHALL be compatible with corresponding `errors[*].body`

### Requirement: Contract schema supports optional `example` field
`apidev validate` SHALL accept optional field `example` inside supported schema fragments (`response.body`, `errors[*].body`, nested `properties`, and `items`) without reporting unknown-field diagnostics.

#### Scenario: Example is accepted in response schema
- **WHEN** contract defines `response.body.properties.<field>.example`
- **THEN** schema validation SHALL pass for this field if `example` matches declared schema constraints
- **AND** diagnostics SHALL NOT include `SCHEMA_UNKNOWN_FIELD` for `example`

#### Scenario: Example is accepted in nested array item schema
- **WHEN** contract defines `response.body.items.example` for `type: array`
- **THEN** schema validation SHALL treat this node as valid schema field

### Requirement: `example` value is validated against schema constraints
Validation SHALL enforce compatibility of `example` with the declared schema node (`type`, `enum`, and container shape).

#### Scenario: Primitive type mismatch is rejected
- **WHEN** schema node has `type: integer` and `example: "42"`
- **THEN** validation SHALL produce an error diagnostic for invalid example type

#### Scenario: Enum mismatch is rejected
- **WHEN** schema node has `enum: ["NEW", "DONE"]` and `example: "ARCHIVED"`
- **THEN** validation SHALL produce an error diagnostic for enum incompatibility

### Requirement: Generated transport/OpenAPI metadata preserves examples deterministically
`apidev diff` and `apidev gen` SHALL include accepted examples in generated metadata so that unchanged contracts keep byte-stable outputs and changed examples produce detectable drift.

#### Scenario: Regeneration remains stable
- **WHEN** contracts and templates are unchanged between two generation runs
- **THEN** generated artifacts containing examples SHALL remain byte-identical

#### Scenario: Example change affects fingerprint and diff
- **WHEN** only `example` value changes in contract schema
- **THEN** operation metadata fingerprint SHALL change
- **AND** `apidev diff` SHALL report corresponding generated updates

#### Scenario: Endpoint-level examples are rendered in OpenAPI operation metadata
- **WHEN** contract contains `examples.request` and/or `examples.response`
- **THEN** generated OpenAPI metadata SHALL expose these examples on operation request/response content
