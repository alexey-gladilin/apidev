# Change: Этап C — Diff/Generate Safety & Drift Governance

## Why

Этап C из дорожной карты требует формализовать и усилить safety-контур вокруг `apidev diff` и `apidev gen`, чтобы drift governance был проверяемым и предсказуемым.
Текущая реализация уже содержит базовые механизмы (validate-before-run, check-mode drift detection, write boundary), но правила и гарантии должны быть закреплены как отдельный capability-контракт для implement-фазы.

## What Changes

- Добавляется capability `diff-gen-safety` с нормативными требованиями по безопасному циклу `validate -> diff -> gen`.
- Формализуется drift governance для `diff`/`gen --check`/`gen` с едиными ожиданиями по mutability и exit semantics.
- Формализуются safety-инварианты write-boundary и deterministic generation как обязательные контракты поведения.
- Фиксируются обязательные verification-gates (unit/contract/integration, negative safety scenarios) для implement-фазы этапа C.

## Impact

- Affected specs: `diff-gen-safety` (new)
- Affected code (target for implement phase): `src/apidev/commands/diff_cmd.py`, `src/apidev/commands/generate_cmd.py`, `src/apidev/application/services/diff_service.py`, `src/apidev/application/services/generate_service.py`, `src/apidev/infrastructure/output/writer.py`, `tests/unit/**`, `tests/integration/**`, `docs/reference/cli-contract.md`
- Breaking: нет (укрепление governance и safety-контрактов в рамках существующих команд)

## Linked Artifacts

- Research baseline: [artifacts/research/2026-02-27-diff-gen-safety-baseline.md](./artifacts/research/2026-02-27-diff-gen-safety-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
