# Архитектура: Diff/Generate Safety & Drift Governance

## Baseline и целевое изменение

Baseline уже содержит preflight validation, diff/check режимы и write-boundary в `SafeWriter`.  
Целевое изменение: формализовать это как capability-контракт с явной трассировкой на `REQ-1..REQ-4`.

## C4 Level 1: System Context

```mermaid
C4Context
title Diff/Generate Safety Governance - System Context (L1)
Person(dev, "Developer / CI", "Запускает validate/diff/gen как локально, так и в pipeline")
System(cli, "apidev CLI", "Оркестрирует validation, planning, drift и apply")
System_Ext(contracts, "Contract Inputs", "OpenAPI/metadata и конфигурация")
System_Ext(workspace, "Workspace", "Generated root и manual-owned зона")
System_Ext(ci, "CI Pipeline", "Drift gates и quality gates")

Rel(dev, cli, "Запускает команды")
Rel(cli, contracts, "Читает и валидирует")
Rel(cli, workspace, "Читает/пишет по policy")
Rel(cli, ci, "Возвращает deterministic status/exit signal")
```

## C4 Level 2: Container

```mermaid
C4Container
title Diff/Generate Safety Governance - Containers (L2)
Person(dev, "Developer / CI")
System_Boundary(apidev, "apidev") {
  Container(cmd, "CLI Commands", "Python", "diff_cmd/gen_cmd: thin orchestration")
  Container(val, "Validation Layer", "Python", "Preflight validation и failure signaling")
  Container(diff, "DiffService", "Python", "Построение deterministic diff-плана")
  Container(gen, "GenerateService", "Python", "Drift check и apply orchestration")
  Container(writer, "SafeWriter", "Python", "Boundary-safe filesystem writes")
  Container(tpl, "Template/Renderer", "Python + Jinja", "Render target artifacts")
}
System_Ext(fs, "Filesystem Workspace", "generated root + manual-owned files")

Rel(dev, cmd, "Запуск")
Rel(cmd, val, "REQ-1: validate first")
Rel(cmd, diff, "REQ-2/REQ-4: preview planning")
Rel(cmd, gen, "REQ-2: check/apply mode")
Rel(diff, tpl, "Render plan")
Rel(gen, diff, "Получает plan")
Rel(gen, writer, "REQ-3: apply only allowed writes")
Rel(writer, fs, "Write only under generated root")
```

## C4 Level 3: Component (Safety Pipeline)

```mermaid
C4Component
title Diff/Generate Safety Governance - Components (L3)
Container_Boundary(pipe, "Safety Pipeline") {
  Component(c1, "Preflight Validator", "Component", "Блокирует выполнение при невалидном входе (REQ-1)")
  Component(c2, "Plan Builder", "Component", "Строит diff-план без мутации workspace (REQ-2)")
  Component(c3, "Drift Evaluator", "Component", "Определяет drift-status для diff/check/apply (REQ-2, REQ-4)")
  Component(c4, "Deterministic Orderer", "Component", "Стабилизирует порядок операций (REQ-4)")
  Component(c5, "Apply Executor", "Component", "Применяет только разрешенные ADD/UPDATE (REQ-2)")
  Component(c6, "Boundary Guard", "Component", "Отклоняет записи вне generated root (REQ-3)")
}
Rel(c1, c2, "Только при успешной валидации")
Rel(c2, c4, "Нормализация порядка")
Rel(c4, c3, "Стабильный план -> стабильный drift signal")
Rel(c3, c5, "Apply only when mode=gen")
Rel(c5, c6, "Каждая запись проходит boundary-check")
```

## Архитектурные инварианты

- `REQ-1`: validation всегда предшествует diff/apply шагам.
- `REQ-2`: `diff` и `gen --check` не инициируют filesystem writes.
- `REQ-3`: `SafeWriter` является единой точкой записи и enforcing write-boundary.
- `REQ-4`: порядок и состав diff-плана детерминированы для неизменных входов.

## Assumptions

- Все записи в generated artifacts идут только через `SafeWriter`.
- Типы операций `ADD/UPDATE/SAME` остаются базовой моделью изменений.
- Канонизация контрактной metadata достаточна для стабильного fingerprint.

## Unresolved Questions

- Нужен ли отдельный компонент для нормализации failure-code semantics между `diff` и `gen`.
- Следует ли формально выделить read-only filesystem adapter для `diff`/`check` для упрощения доказательства non-mutation.
- Нужна ли явная архитектурная граница между drift-evaluation и console-reporting.
