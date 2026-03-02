## ADDED Requirements

### Requirement: Scaffold-aware REMOVE precedence
Для scaffold subtree система SHALL применять scaffold-aware remove policy как уточнение `REMOVE`-семантики внутри generated root.

#### Scenario: Scaffold subtree is kept when scaffold mode is enabled
- **WHEN** effective scaffold mode resolved as enabled (`--scaffold` or `generator.scaffold = true`)
- **AND** stale candidate path belongs to `<generated_dir>/<scaffold_dir>/`
- **THEN** `apidev diff` SHALL NOT планировать `REMOVE` для этого пути
- **AND** базовые safety diagnostics `remove-conflict`/`remove-boundary-violation` SHALL оставаться неизменными

#### Scenario: Scaffold subtree is removable when scaffold mode is disabled
- **WHEN** effective scaffold mode resolved as disabled (`--no-scaffold` or `generator.scaffold = false`)
- **AND** stale candidate path belongs to `<generated_dir>/<scaffold_dir>/`
- **THEN** `apidev diff` SHALL планировать `REMOVE` для этого пути
- **AND** remove semantics SHALL оставаться ограниченными write-boundary внутри generated root
