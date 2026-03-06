# Design Artifact Package: 004-diff-gen-safety

## Контекст

Пакет описывает проектирование safety-контура для этапа C: `validate -> diff -> gen`, с фокусом на governance дрейфа и гарантии безопасной записи.

## Входы

- Proposal: `openspec/changes/004-diff-gen-safety/proposal.md`
- Design summary: `openspec/changes/004-diff-gen-safety/design.md`
- Spec delta: `openspec/changes/004-diff-gen-safety/specs/diff-gen-safety/spec.md`
- Research baseline: `openspec/changes/004-diff-gen-safety/artifacts/research/2026-02-27-diff-gen-safety-baseline.md`

## Состав пакета

- [01-architecture.md](./01-architecture.md)
- [02-behavior.md](./02-behavior.md)
- [03-decisions.md](./03-decisions.md)
- [04-testing.md](./04-testing.md)

## Трассировка на spec delta

- `REQ-1` Validate-First Safety Pipeline  
  Покрытие: `01-architecture.md`, `02-behavior.md`, `04-testing.md`
- `REQ-2` Drift Governance Modes  
  Покрытие: `01-architecture.md`, `02-behavior.md`, `04-testing.md`
- `REQ-3` Generated Write Boundary Safety  
  Покрытие: `01-architecture.md`, `03-decisions.md`, `04-testing.md`
- `REQ-4` Deterministic Drift Signal  
  Покрытие: `01-architecture.md`, `02-behavior.md`, `04-testing.md`

## Assumptions

- Архитектурные роли `DiffService`, `GenerateService`, `SafeWriter` сохраняются без фундаментального пересмотра.
- Контрактные входы остаются единственным источником истины для вычисления diff-плана.
- Check-mode (`gen --check`) остается строго read-only режимом.

## Unresolved Questions

- Нужен ли отдельный унифицированный код/enum для drift-status между CLI и сервисным слоем.
- Требуется ли отдельный аудит-лог write-attempts на уровне инфраструктуры для CI артефактов.
- Нужно ли формально зафиксировать правила сортировки diff-операций в публичном CLI-контракте.
