# Архитектура: Safety/Drift Completion (REMOVE)

## Baseline и целевое изменение
Текущий pipeline детектирует drift по `ADD/UPDATE`. Целевое изменение добавляет `REMOVE` как first-class операцию в plan/build/check/apply цепочке без нарушения write-boundary.

## C4 Level 1: System Context

```mermaid
C4Context
title Safety/Drift REMOVE Governance - System Context (L1)
Person(dev, "Developer / CI", "Запускает validate/diff/gen в локальном и CI контуре")
System(cli, "apidev CLI", "Оркестрирует planning, drift-check и apply")
System_Ext(contracts, "Contract Inputs", "Контракты и конфигурация")
System_Ext(workspace, "Workspace", "Generated root + manual зона")
System_Ext(ci, "CI Gate", "Проверяет drift-status и exit codes")

Rel(dev, cli, "Запуск команд")
Rel(cli, contracts, "Чтение контрактов")
Rel(cli, workspace, "Read-only preview / controlled apply")
Rel(cli, ci, "Машинно-парсируемые diagnostics и exit signals")
```

## C4 Level 2: Container

```mermaid
C4Container
title Safety/Drift REMOVE Governance - Containers (L2)
Person(dev, "Developer / CI")
System_Boundary(apidev, "apidev") {
  Container(cmd, "CLI Commands", "Python", "diff_cmd / generate_cmd")
  Container(diff, "DiffService", "Python", "Построение generation plan с ADD/UPDATE/REMOVE")
  Container(gen, "GenerateService", "Python", "check/apply orchestration")
  Container(writer, "SafeWriter", "Python", "Write-boundary enforcement")
  Container(renderer, "Template Engine", "Jinja2", "Формирование expected generated artifacts")
}
System_Ext(fs, "Filesystem", "generated root + manual files")

Rel(dev, cmd, "Вызов")
Rel(cmd, diff, "Preview planning")
Rel(cmd, gen, "Check / Apply")
Rel(diff, renderer, "Build expected artifact set")
Rel(gen, diff, "Получение плана")
Rel(gen, writer, "ADD/UPDATE/REMOVE apply через safety guard")
Rel(writer, fs, "Ограниченная мутация только внутри generated root")
```

## C4 Level 3: Component

```mermaid
C4Component
title Safety/Drift REMOVE Governance - Components (L3)
Container_Boundary(pipe, "Diff/Gen Pipeline") {
  Component(c1, "Expected Artifact Builder", "Component", "Строит детерминированный expected set из контрактов")
  Component(c2, "Stale Artifact Detector", "Component", "Определяет stale files внутри generated root")
  Component(c3, "Plan Composer", "Component", "Формирует ADD/UPDATE/REMOVE/SAME")
  Component(c4, "Drift Evaluator", "Component", "Определяет drift-status с учетом REMOVE")
  Component(c5, "Apply Executor", "Component", "Выполняет ADD/UPDATE/REMOVE в apply-режиме")
  Component(c6, "Boundary Guard", "Component", "Проверяет запрет выхода за generated root")
}
Rel(c1, c2, "Expected set")
Rel(c2, c3, "REMOVE candidates")
Rel(c3, c4, "Unified plan")
Rel(c4, c5, "Apply only in gen mode")
Rel(c5, c6, "Каждая операция проходит safety check")
```

## Архитектурные инварианты
- Все `REMOVE` вычисляются только относительно generated root.
- `diff` и `gen --check` не выполняют файловых мутаций.
- Apply для `REMOVE` использует те же safety-check принципы, что и запись.
- Порядок операций в плане стабилен при неизменных входах.
