# Phase 04 - Implementation (Execution Blueprint)

## Цель
Определить последовательность реализации для `/openspec-implement` без смешения с proposal/design работами.

## Workstreams
1. Compatibility core
- Реализовать taxonomy и deterministic classifier в `src/apidev/core/rules/compatibility.py`.
- Зафиксировать вход/выход classifier как контракт для application services.

2. Application integration
- Внедрить classifier в `diff_service` и `generate_service`.
- Сохранить backward-compatible default policy `warn`.
- Выполнять compare только как `current_normalized_model` vs baseline snapshot, резолвленный по `baseline_ref`.

3. Config + release-state contract
- Добавить/проверить параметры `compatibility_policy`, `evolution.grace_period_releases`, `evolution.release_state_file` в `.apidev/config.toml`.
- Реализовать чтение release state из default `.apidev/release-state.json` с override через конфиг.
- Валидировать формат release state как JSON-объект: обязательные `release_number` (`int >= 1`) и `baseline_ref` (`git tag|sha`) + опциональные `released_at` (`RFC3339 UTC`), `git_commit` (`40-hex`), `tag` (`string`).
- Запретить любые write side effects для `apidev diff` и `apidev gen --check`.

4. Baseline snapshot handling
- Реализовать резолв baseline snapshot через `baseline_ref` (VCS/CI source of truth), с локальным файлом как optional cache.
- Добавить CLI override `--baseline-ref` с приоритетом над значением из release state.
- Валидировать формат snapshot и детерминированную нормализацию модели перед compare.
- Ввести diagnostics `baseline-missing`/`baseline-invalid`; в `strict` policy фейлить команду.

5. Optional dbspec enrichment
- Реализовать read-only adapter загрузки hints.
- Добавить deterministic merge с приоритетом contract data.
- Гарантировать graceful fallback при недоступности `dbspec`.

6. Deprecation governance
- Реализовать lifecycle checks `active -> deprecated -> removed`.
- Реализовать правило deprecation window через `grace_period_releases`.
- Обеспечить compatibility classification для removals до/после окна.

7. CLI/docs sync
- Обновить команды `diff/gen` и diagnostics, включая отображение примененной policy.
- Синхронизировать `docs/reference/cli-contract.md` и `docs/reference/contract-format.md`.

## Verification Gates
- Unit: `uv run pytest tests/unit`
- Contract: `uv run pytest tests/contract`
- Integration: `uv run pytest tests/integration`
- CLI conventions: `uv run pytest tests/unit/test_cli_conventions.py`

## Definition of Done
- Реализация покрывает все требования `specs/contract-evolution-integration/spec.md`.
- Для одинаковых входов generation/diff результаты остаются детерминированными.
- Read-only режимы (`diff`, `gen --check`) не модифицируют release state и generated artifacts.
- Документация и CLI-help отражают финальный поведенческий контракт.
