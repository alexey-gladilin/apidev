## MODIFIED Requirements

### Requirement: Transport Model Generation
`apidev gen` SHALL generate deterministic transport models for request, response, and declared error payloads from validated contracts in domain-first generated layout.

#### Scenario: Request/response/error модели генерируются в доменных каталогах
- **WHEN** контракт расположен по пути `<domain>/<operation>.yaml`
- **THEN** generation SHALL produce model artifacts in `<domain>/models/<operation>_{request|response|error}.py`
- **AND** regenerated output SHALL remain byte-stable for unchanged contract inputs

#### Scenario: Router wiring генерируется в доменном каталоге
- **WHEN** контракт расположен по пути `<domain>/<operation>.yaml`
- **THEN** generation SHALL produce router artifact in `<domain>/routes/<operation>.py`
- **AND** generated code SHALL not contain business logic implementations

### Requirement: Stable Operation Registry Contract
Generation SHALL maintain a stable operation registry contract that maps `operation_id` to transport metadata used by runtime and tests, including domain-qualified module references.

#### Scenario: Registry references domain-qualified modules
- **WHEN** операция присутствует в contracts
- **THEN** registry entry SHALL include router/model module paths in domain-qualified format
- **AND** consumers SHALL resolve operation wiring using registry data without runtime contract parsing

#### Scenario: Registry includes auth signal for runtime wiring
- **WHEN** операция присутствует в contracts
- **THEN** registry entry SHALL include auth metadata derived from contract (`public` or `bearer`)
- **AND** target integration layer SHALL be able to resolve auth dependency without reparsing YAML

#### Scenario: Registry ordering and content remain deterministic
- **WHEN** generation runs multiple times on unchanged contracts/templates
- **THEN** operation registry output SHALL preserve deterministic ordering and content
- **AND** drift checks SHALL report no differences for unchanged inputs

### Requirement: Clean Break Layout Policy
Transport generation SHALL treat domain-first generated layout as the only canonical output format for this change.

#### Scenario: No backward-compatibility requirements for old layout
- **WHEN** change is implemented in pre-release stage
- **THEN** system SHALL NOT require compatibility layer for operation-first generated file paths
- **AND** tests and documentation SHALL validate only domain-first layout contract

#### Scenario: `operation_id` remains stable across layout change
- **WHEN** only physical generated layout changes
- **THEN** operation identity for compatibility/deprecation logic SHALL remain based on contract identity rules
- **AND** layout refactoring SHALL NOT introduce operation id churn

### Requirement: Generated-to-Manual Integration Contract
Transport generation SHALL provide explicit integration contract for target FastAPI applications via registry/factory pattern without generating business logic.

#### Scenario: Endpoint registration uses generated registry and manual handlers
- **WHEN** target app composes API routes
- **THEN** operation metadata SHALL be consumable from generated registry for path/method/wiring resolution
- **AND** handler implementations SHALL remain manual-owned and bound by `operation_id`

#### Scenario: Auth integration remains manual with contract metadata as input
- **WHEN** operation requires auth
- **THEN** generated metadata SHALL expose auth-relevant contract signal for wiring
- **AND** concrete auth policy and dependencies SHALL remain manual-owned

#### Scenario: Authenticated user context is passed via manual integration layer
- **WHEN** auth dependency resolves authenticated user
- **THEN** manual endpoint/factory layer SHALL pass user context into handler input payload/request model
- **AND** generated transport layer SHALL NOT decode token or own user identity policy

#### Scenario: Error mapping remains manual with generated contract hints
- **WHEN** manual handler raises domain exception
- **THEN** integration layer SHALL map error to contract-compatible response using manual policy
- **AND** generated artifacts SHALL NOT encode domain-specific error behavior

#### Scenario: OpenAPI integration is assembled from generated metadata
- **WHEN** target app configures OpenAPI
- **THEN** generated OpenAPI builder SHALL produce deterministic `paths` fragment from registry metadata
- **AND** application composition root SHALL decide how this fragment is attached to runtime OpenAPI schema

#### Scenario: OpenAPI success status matches contract response status
- **WHEN** contract defines success `response.status`
- **THEN** generated OpenAPI operation SHALL use that exact HTTP status code in `responses`
- **AND** generation SHALL NOT hardcode status `200` for all operations

### Requirement: Optional Integration Scaffold Generation
Transport generation SHALL support configurable integration scaffold generation without overwriting existing manual files.

#### Scenario: Config defaults are created by init
- **WHEN** user runs `apidev init`
- **THEN** generated `.apidev/config.toml` SHALL include `generator.scaffold = true`
- **AND** generated `.apidev/config.toml` SHALL include `generator.scaffold_dir = "integration"`

#### Scenario: Scaffold generation is controlled by exact CLI flags
- **WHEN** user runs `apidev gen` or `apidev diff` with `--scaffold` or `--no-scaffold`
- **THEN** CLI flag SHALL override config value `generator.scaffold` for current run

#### Scenario: Scaffold generation uses config when no CLI override
- **WHEN** user runs generation without `--scaffold` and without `--no-scaffold`
- **THEN** tool SHALL use `generator.scaffold` from `.apidev/config.toml`

#### Scenario: Effective scaffold mode has deterministic precedence
- **WHEN** both config and CLI inputs are available
- **THEN** effective scaffold mode SHALL be resolved as `CLI flag -> config -> default`
- **AND** default mode produced by `apidev init` SHALL be `generator.scaffold = true`

#### Scenario: Scaffold generation writes only missing files
- **WHEN** scaffold generation is enabled by CLI or config
- **THEN** tool SHALL create predefined scaffold files for registry/factory/auth/error integration
- **AND** created files SHALL remain inside configured generated root

#### Scenario: Existing scaffold file is not overwritten
- **WHEN** scaffold generation is enabled and target scaffold file already exists
- **THEN** tool SHALL keep existing file unchanged
- **AND** generation SHALL continue without destructive overwrite

#### Scenario: Scaffold directory path is relative and bounded
- **WHEN** `generator.scaffold_dir` is resolved
- **THEN** it SHALL be interpreted as relative to `generator.generated_dir`
- **AND** absolute paths or path traversal outside generated root SHALL be rejected

#### Scenario: Existing scaffold files are not removed as stale
- **WHEN** scaffold generation is enabled and scaffold files already exist under scaffold directory
- **THEN** stale-remove planning SHALL NOT mark these scaffold files as `REMOVE`
- **AND** repeated `diff/gen --check` SHALL remain stable for unchanged scaffold files

#### Scenario: Scaffold files are removable when scaffold is explicitly disabled
- **WHEN** effective scaffold mode is disabled (`--no-scaffold` or `generator.scaffold = false`)
- **THEN** stale-remove planning SHALL treat scaffold files under configured scaffold directory as removable stale artifacts
- **AND** remove behavior SHALL remain bounded by generated-root safety policy

### Requirement: Domain Package Import Policy
Transport generation SHALL define deterministic import/package policy for single-level domain layout.

#### Scenario: Generated domain modules are importable for runtime wiring
- **WHEN** generation produces paths `<domain>/routes/*` and `<domain>/models/*`
- **THEN** generated tree SHALL follow one consistent package policy for imports
- **AND** runtime wiring imports from registry metadata SHALL resolve without manual path hacks

#### Scenario: Nested domain contracts are rejected
- **WHEN** contract path contains nested domain directories (for example `billing/invoices/get_invoice.yaml`)
- **THEN** generation SHALL fail with deterministic validation diagnostic
- **AND** diagnostic SHALL explain single-level domain constraint (`<domain>/<operation>.yaml`)

#### Scenario: Domain packages include explicit `__init__.py`
- **WHEN** generation builds domain transport modules
- **THEN** tool SHALL create missing `__init__.py` files for importable packages under `<domain>/`, `<domain>/routes/`, and `<domain>/models/`
- **AND** repeated generation on unchanged inputs SHALL keep package artifacts byte-stable

#### Scenario: Domain segments are normalized deterministically
- **WHEN** domain or operation segment contains non-Python-safe characters
- **THEN** generation SHALL normalize segment to Python-safe snake_case deterministically
- **AND** identical inputs SHALL always produce identical normalized module paths

#### Scenario: Normalized path collision is rejected deterministically
- **WHEN** two different contracts resolve to the same normalized generated target path
- **THEN** generation SHALL fail with deterministic collision diagnostic
- **AND** no ambiguous overwrite between operations SHALL be allowed
