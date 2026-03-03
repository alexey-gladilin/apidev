# Архитектура: Endpoint Include/Exclude для `apidev gen`

## Контекст
Требуется добавить фильтрацию endpoint-ов в generation pipeline без изменения структуры контрактов и без нарушения deterministic generation.

## C4 Level 1: System Context
```mermaid
C4Context
title APIDev Endpoint Filtering (L1)
Person(dev, "Developer / CI", "Запускает apidev gen с include/exclude")
System(apidev, "apidev CLI", "Contract-driven API generation")
System_Ext(fs, "Project Filesystem", "Contracts, config, generated artifacts")

Rel(dev, apidev, "Runs gen command with filters")
Rel(apidev, fs, "Reads contracts/config, writes generated output")
```

## C4 Level 2: Container
```mermaid
C4Container
title APIDev Containers for Endpoint Filtering (L2)
Person(dev, "Developer / CI")
System_Boundary(apidev_boundary, "apidev") {
  Container(cli, "CLI Commands", "Typer", "Parses include/exclude args")
  Container(gen_service, "Generate Service", "Python", "Apply/check orchestration")
  Container(diff_service, "Diff Service", "Python", "Builds deterministic generation plan")
  Container(loader, "Contract Loader", "YAML loader", "Loads all endpoint contracts")
}
System_Ext(fs, "Filesystem", "contracts/config/generated")

Rel(dev, cli, "Invokes apidev gen")
Rel(cli, gen_service, "Passes normalized filter args")
Rel(gen_service, diff_service, "Delegates plan generation")
Rel(diff_service, loader, "Loads operations and applies endpoint selection")
Rel(loader, fs, "Reads contracts/*.yaml")
Rel(diff_service, fs, "Compares against generated files")
Rel(gen_service, fs, "Writes/removes files in apply mode")
```

## C4 Level 3: Component
```mermaid
C4Component
title Endpoint Selection Components (L3)
Container_Boundary(endpoint_filtering, "Endpoint Selection in generation pipeline") {
  Component(flag_parser, "CLI Flag Parser", "generate_cmd", "Parses --include-endpoint/--exclude-endpoint")
  Component(filter_normalizer, "Filter Normalizer", "application DTO", "Normalizes and validates user patterns")
  Component(selector, "Operation Selector", "diff_service", "Builds effective operation set include->exclude")
  Component(plan_builder, "Generation Plan Builder", "diff_service", "Builds planned changes only for selected operations")
  Component(diagnostics_mapper, "Diagnostics Mapper", "commands/services", "Produces deterministic diagnostics for filter errors")
}

Rel(flag_parser, filter_normalizer, "Pass raw arguments")
Rel(filter_normalizer, selector, "Pass normalized include/exclude")
Rel(selector, plan_builder, "Pass selected operations")
Rel(selector, diagnostics_mapper, "Reports invalid pattern/empty selection")
Rel(plan_builder, diagnostics_mapper, "Reports drift and apply diagnostics")
```

## Архитектурные инварианты
- Фильтрация применяется до построения generation plan.
- Без include/exclude флагов поведение `apidev gen` остается полностью совместимым.
- Порядок операций после фильтрации остается детерминированным.
- Safety boundaries для write/remove сохраняются без ослабления.
