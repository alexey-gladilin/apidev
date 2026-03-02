# Архитектура: Auto release-state lifecycle в `apidev gen`

## Контекст
Цель — формализовать write lifecycle release-state только для `gen apply`, сохранив strict read-only поведение для `diff` и `gen --check`.

## C4 Level 1: System Context
```mermaid
C4Context
title APIDev Release-State Lifecycle (L1)
Person(dev, "Developer / CI", "Запускает validate/diff/gen")
System(apidev, "apidev CLI", "Контракт-ориентированный генератор API")
System_Ext(fs, "Project Filesystem", ".apidev/contracts/.apidev/release-state/.apidev/output")
System_Ext(git, "Git (optional)", "Baseline source для ref/tag/sha")

Rel(dev, apidev, "CLI commands")
Rel(apidev, fs, "Read contracts + read/write generated + release-state")
Rel(apidev, git, "Resolve baseline snapshot by baseline_ref")
```

## C4 Level 2: Container
```mermaid
C4Container
title APIDev Containers for Release-State Lifecycle (L2)
Person(dev, "Developer / CI")
System_Boundary(apidev_boundary, "apidev") {
  Container(cli, "CLI Commands", "Typer", "diff/gen/gen --check")
  Container(diff_service, "DiffService", "Python", "Builds generation plan + compatibility summary")
  Container(gen_service, "GenerateService", "Python", "Apply/check orchestration and post-apply sync")
  Container(config_loader, "TomlConfigLoader", "Python", "Config + release-state load/validate")
  Container(writer, "SafeWriter", "Python", "Boundary-safe writes/removes for generated files")
}
System_Ext(fs, "Filesystem", "Workspace files")
System_Ext(git, "Git", "Baseline snapshots")

Rel(dev, cli, "Runs")
Rel(cli, diff_service, "Plan/diagnostics")
Rel(cli, gen_service, "Apply/check workflow")
Rel(diff_service, config_loader, "Load config and release-state (read)")
Rel(diff_service, git, "Resolve baseline snapshot")
Rel(gen_service, writer, "Apply generated changes")
Rel(gen_service, config_loader, "Read config/release-state")
Rel(gen_service, fs, "Write release-state in apply mode")
```

## C4 Level 3: Component
```mermaid
C4Component
title GenerateService Components - Release-State Sync (L3)
Container_Boundary(gen, "GenerateService") {
  Component(plan_eval, "Plan Evaluator", "Compute changed paths", "Определяет applied changes")
  Component(apply_exec, "Apply Executor", "SafeWriter adapter", "Применяет ADD/UPDATE/REMOVE")
  Component(sync_guard, "Sync Guard", "Mode gate", "Разрешает release-state write только в apply")
  Component(sync_policy, "Baseline/Version Policy", "Resolver", "CLI->release-state->git fallback, bump rules")
  Component(sync_writer, "Release-State Writer", "Filesystem adapter", "Create/update release-state JSON")
}
Rel(plan_eval, apply_exec, "Execute when not --check")
Rel(apply_exec, sync_guard, "After successful apply")
Rel(sync_guard, sync_policy, "If write allowed")
Rel(sync_policy, sync_writer, "Prepared payload")
```

## Архитектурные инварианты
- `diff` и `gen --check` не модифицируют release-state.
- `gen apply` может писать release-state только после успешного apply-пайплайна.
- baseline compare контракт в `DiffService` сохраняет приоритет `CLI -> release-state`.
