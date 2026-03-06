# Архитектура: Unified Diagnostics Contract

## Контекст
Цель — добавить единый machine-readable diagnostics contract для CLI команд без изменения базовых drift/policy семантик.

## C4 Level 1: System Context
```mermaid
C4Context
title APIDev Diagnostics Contract (L1)
Person(dev, "Developer / CI", "Запускает validate/diff/gen и парсит diagnostics")
System(apidev, "apidev CLI", "Contract-driven API dev tool")
System_Ext(ci, "CI Orchestrator", "Потребляет machine-readable diagnostics")
System_Ext(fs, "Project Filesystem", "Contracts/config/generated artifacts")

Rel(dev, apidev, "Executes CLI commands")
Rel(apidev, fs, "Reads contracts/config, writes generated files in apply mode")
Rel(ci, apidev, "Parses diagnostics envelope")
```

## C4 Level 2: Container
```mermaid
C4Container
title APIDev Containers for Diagnostics Contract (L2)
Person(dev, "Developer / CI")
System_Boundary(apidev_boundary, "apidev") {
  Container(cli, "CLI Commands", "Typer", "validate/diff/gen interfaces")
  Container(app_services, "Application Services", "Python", "ValidateService/DiffService/GenerateService")
  Container(diag_mapper, "Diagnostics Mapper", "Python", "Unified diagnostics envelope builder")
  Container(config_runtime, "Runtime + Config", "Python", "Path/config/baseline resolution")
}
System_Ext(fs, "Filesystem", "Contracts + generated + release-state")

Rel(dev, cli, "Runs command")
Rel(cli, app_services, "Delegates execution")
Rel(app_services, diag_mapper, "Maps domain/service diagnostics")
Rel(app_services, config_runtime, "Loads config and runtime context")
Rel(app_services, fs, "Reads/writes data")
Rel(cli, diag_mapper, "Serializes JSON output for machine-readable mode")
```

## C4 Level 3: Component
```mermaid
C4Component
title Diagnostics Mapper Components (L3)
Container_Boundary(diag, "Unified Diagnostics Mapper") {
  Component(envelope_builder, "Envelope Builder", "Serializer", "Builds command-level payload: command/summary/diagnostics/meta")
  Component(item_normalizer, "Diagnostic Item Normalizer", "Mapper", "Normalizes validation/compatibility/generation diagnostics")
  Component(code_taxonomy, "Code Taxonomy Resolver", "Policy", "Enforces namespace and stable code formatting")
  Component(ordering_guard, "Deterministic Ordering Guard", "Sorter", "Sorts diagnostics for stable output")
}
Rel(envelope_builder, item_normalizer, "Maps raw diagnostics")
Rel(item_normalizer, code_taxonomy, "Validates code namespace")
Rel(envelope_builder, ordering_guard, "Stabilizes diagnostics order")
```

## Архитектурные инварианты
- JSON diagnostics contract должен быть единым для `validate|diff|gen --check|gen`.
- Plain-text UX остается поддерживаемым по умолчанию.
- Drift/policy semantics не меняются в рамках hardening diagnostics.
- Вывод diagnostics детерминирован для одинакового входа.
