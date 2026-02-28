# Implementation Handoff: 006-safety-drift

## Порядок выполнения
1. Выполнить Phase 01: ввести `REMOVE` в plan-модель и drift-предикат read-only режимов.
2. Выполнить Phase 02: реализовать apply-семантику `REMOVE` с boundary enforcement и diagnostics.
3. Выполнить Phase 03: синхронизировать docs/contracts/tests и закрыть verification.
4. Подтвердить готовность к merge по quality gates.

## Зависимости
- `Phase 02` стартует после фиксации deterministic REMOVE planning из `Phase 01`.
- `Phase 03` стартует после интеграции apply/remove diagnostics из `Phase 02`.

## Scope implement-фазы
- Включено: `REMOVE` в diff/check/gen, drift/exit alignment, remove diagnostics, тесты и docs sync.
- Исключено: redesign pipeline вне safety/drift периметра, новые продуктовые capabilities.

## Минимальные verification-команды
- `uv run pytest tests/unit tests/contract tests/integration -k "remove or drift or writer"`
- `uv run pytest tests/integration/test_generate_roundtrip.py`
- `uv run pytest tests/unit/test_cli_conventions.py`
- `openspec validate 006-safety-drift --strict --no-interactive`

## Команда запуска
Implementation выполняется отдельно: `/openspec-implement 006-safety-drift` (или `/openspec-implement-single 006-safety-drift`).
