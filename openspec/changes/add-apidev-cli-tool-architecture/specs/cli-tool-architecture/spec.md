## ADDED Requirements

### Requirement: Binary CLI Packaging
`apidev` SHALL be packaged as an installable CLI binary that can run inside external target projects.

#### Scenario: CLI entrypoint is available after install
- **WHEN** a user installs `apidev`
- **THEN** command `apidev` SHALL be available in PATH
- **AND** command execution SHALL start in `apidev.cli` entrypoint

### Requirement: Layered Internal Architecture for CLI Tool
The codebase SHALL separate CLI adapters, application services, core rules/models, and infrastructure adapters.

#### Scenario: Command delegates to application service
- **WHEN** user runs any supported CLI command
- **THEN** command module SHALL parse flags and delegate business workflow to application service layer
- **AND** core models/rules SHALL remain independent from CLI framework details

### Requirement: MVP Command Surface
The CLI SHALL provide minimal commands for initializing config, validating contracts, previewing generated changes, and writing generated output.

#### Scenario: Init creates tool workspace
- **WHEN** user runs `apidev init` in a target project
- **THEN** tool SHALL create `.apidev/config.toml`, `.apidev/contracts/`, and `.apidev/templates/` if absent

#### Scenario: Validate reports diagnostics without writing output
- **WHEN** user runs `apidev validate`
- **THEN** tool SHALL parse all contracts and report validation diagnostics
- **AND** tool SHALL not write generated source files

#### Scenario: Diff previews planned changes
- **WHEN** user runs `apidev diff`
- **THEN** tool SHALL compute deterministic generation plan
- **AND** tool SHALL report file-level adds/updates/removals without writing files

#### Scenario: Generate applies deterministic output
- **WHEN** user runs `apidev gen`
- **THEN** tool SHALL write planned files deterministically
- **AND** repeated generation with unchanged inputs SHALL produce no content changes

### Requirement: Safe Write Boundaries in Target Projects
The generator SHALL restrict writes to configured generated directories and SHALL protect manual user code from overwrite.

#### Scenario: Write attempt outside generated root
- **WHEN** generation plan includes a file path outside configured generated root
- **THEN** generator SHALL fail with explicit policy error
- **AND** tool SHALL not write any out-of-policy file

#### Scenario: Check mode detects drift
- **WHEN** user runs generation check mode in CI
- **THEN** tool SHALL return non-zero exit code if committed generated files differ from deterministic output
