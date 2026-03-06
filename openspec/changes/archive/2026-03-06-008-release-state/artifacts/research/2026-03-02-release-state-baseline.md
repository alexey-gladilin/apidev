# Research Baseline: release-state lifecycle и baseline-ref resolution (2026-03-02)

## Scope

- Команды: `apidev gen`, `apidev gen --check`, `apidev diff`.
- Области: источники `baseline_ref`, чтение/запись `release-state`, no-git и invalid baseline сценарии.
- Источники: production-код и integration tests репозитория.

## Факт 1: Приоритет источников baseline_ref уже формализован для compare

- В `gen` доступен CLI `--baseline-ref`, который передается в `GenerateService.run(..., baseline_ref=...)`.
- В `DiffService` порядок резолва: `CLI baseline_ref` -> `release-state baseline_ref` -> `None`.
- Оба источника проходят `validate_baseline_ref`.

Evidence:

- `src/apidev/commands/generate_cmd.py` (опция `--baseline-ref`, передача в service).
- `src/apidev/application/services/diff_service.py` (`_resolve_baseline_ref`).
- `src/apidev/core/models/release_state.py` (`validate_baseline_ref`).

## Факт 2: release-state в production-пайплайне сейчас читается, но не управляется lifecycle'ом `gen`

- `DiffService.run` читает release-state через `config_loader.load_release_state`.
- Загрузка включает existence/size/json/schema валидацию.
- В read-only контрактах `diff` и `gen --check` release-state не должен модифицироваться.

Evidence:

- `src/apidev/application/services/diff_service.py` (load release-state + diagnostics aggregation).
- `src/apidev/infrastructure/config/toml_loader.py` (`load_release_state` contract).
- `tests/integration/test_compatibility_policy_cli.py` (проверка, что `diff`/`gen --check` не изменяют release-state).

## Факт 3: Baseline snapshot резолвится из cache/VCS и имеет явные diagnostics

- При отсутствии baseline_ref возвращается `baseline-missing`.
- При невалидном baseline snapshot возвращается `baseline-invalid`.
- При невалидном/отсутствующем release-state добавляется `release-state-invalid`.

Evidence:

- `src/apidev/application/services/diff_service.py` (`_load_baseline_snapshot`, `_load_baseline_snapshot_from_vcs`, `_build_compatibility_summary`).
- `src/apidev/core/rules/compatibility.py` (taxonomy для baseline/release-state diagnostics).

## Факт 4: Exit semantics CLI завязаны на `drift-status` и policy gate

- `gen --check` в drift возвращает non-zero.
- В strict policy при `overall=breaking` срабатывает policy gate.
- `diff` может завершаться с `exit 0` при informational drift.

Evidence:

- `src/apidev/commands/generate_cmd.py`.
- `tests/integration/test_compatibility_policy_cli.py`.

## Вывод по фактам (без рекомендаций)

- Контракт чтения release-state и baseline compare уже определен.
- Контракт write lifecycle для release-state в `gen apply` требует явной спецификации и планирования implement-фазы.

