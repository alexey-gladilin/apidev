# Change: Horizon 1 — Diagnostics Contract Hardening

## Почему
Сейчас machine-readable diagnostics в CLI непоследовательны между режимами `apidev validate`, `apidev diff`, `apidev gen --check` и `apidev gen`:
- только `validate` поддерживает `--json` как явно документированный контрактный вывод;
- `diff` и `gen` выводят diagnostics преимущественно как человеко-читаемый текст;
- структуры diagnostics DTO различаются (`ValidationDiagnostic` vs `GenerationDiagnostic` vs compatibility diagnostics), что усложняет стабильный CI parsing.

Это противоречит цели Horizon 1 из `docs/roadmap.md`: единый и предсказуемый diagnostics contract для всех ключевых режимов CLI.

## Что изменится
- Модифицируется capability `cli-tool-architecture`:
  - вводится единый machine-readable diagnostics envelope для `validate`, `diff`, `gen --check`, `gen`;
  - фиксируется общий минимальный набор полей diagnostics (`code`, `severity`, `location`, `message`, `category`, `detail`, `source`) с режим-специфичными опциональными полями;
  - фиксируется стабильная таксономия diagnostics codes по namespace (validation, compatibility, generation, runtime/config);
  - добавляется явный CLI контракт для JSON-режима в `diff`/`gen` (паритет с `validate`);
  - синхронизируются reference docs и regression test matrix.
- Сохраняются существующие drift/exit semantics и compatibility policy behavior; change направлен на контракт вывода, а не на изменение базовой бизнес-логики pipeline.

## Влияние
- Затронутые спеки: `cli-tool-architecture` (MODIFIED).
- Затронутый код (target implement-фазы):
  - `src/apidev/commands/validate_cmd.py`
  - `src/apidev/commands/diff_cmd.py`
  - `src/apidev/commands/generate_cmd.py`
  - `src/apidev/commands/common/compatibility.py`
  - `src/apidev/application/dto/diagnostics.py`
  - `src/apidev/application/dto/generation_plan.py`
  - `src/apidev/core/models/diagnostic.py`
  - `tests/unit/test_cli_conventions.py`
  - `tests/integration/test_compatibility_policy_cli.py`
  - `docs/reference/cli-contract.md`
  - `docs/process/testing-strategy.md`
- Breaking:
  - для plain-text UX — нет;
  - для JSON-потребителей — возможен controlled breaking в виде формализации полей и envelope (мигрируется через явный контракт в docs/spec).

## Linked Artifacts
- Research: [artifacts/research/2026-03-02-diagnostics-contract-baseline.md](./artifacts/research/2026-03-02-diagnostics-contract-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/cli-tool-architecture/spec.md](./specs/cli-tool-architecture/spec.md)

## Границы этапа
Этот change-пакет покрывает Proposal/Design/Plan и readiness к implement.
Implementation выполняется отдельно через `/openspec-implement` или `/openspec-implement-single` после review/approval.
