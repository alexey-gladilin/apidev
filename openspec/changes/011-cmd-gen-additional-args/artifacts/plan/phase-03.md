# Phase 03: Документация, regression и readiness

## Цель фазы
Синхронизировать документацию/тесты с новым CLI-контрактом и закрыть change strict-валидацией.

## Scope
- Обновление `docs/reference/cli-contract.md` и связанных user-facing инструкций.
- Добавление regression tests для include/exclude semantics.
- Финальная OpenSpec strict validation.

## Выходы
- Актуализированная документация CLI контракта.
- Regression-покрытие unit + integration.
- Готовность пакета к implement-фазе.

## Verification Gate
- `make docs-check`
- `uv run pytest tests/unit tests/integration -k "endpoint_filter"`
- `openspec validate 011-cmd-gen-additional-args --strict --no-interactive`

## Риски
- Документация и фактическое поведение могут разойтись.
- Частичное покрытие edge-кейсов фильтрации.

## Definition of Done
- Документация описывает флаги, precedence и error semantics.
- Regression tests защищают от дрейфа контракта.
- Strict validation проходит без ошибок.
