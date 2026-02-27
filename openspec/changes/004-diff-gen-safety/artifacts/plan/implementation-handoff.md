# Implementation Handoff: 004-diff-gen-safety

## Порядок выполнения
1. Выполнить Phase 01: validate-first pipeline и read-only drift preview contract.
2. Выполнить Phase 02: write-boundary enforcement и deterministic planning invariants.
3. Выполнить Phase 03: verification matrix, CLI contract sync и финальная readiness-проверка.
4. После implement-фазы синхронизировать статус Stage C в `docs/roadmap.md` и связанных reference-документах.

## Зависимости
- `P2` стартует после фиксации validate/check governance из `P1`.
- `P3` стартует после фиксации boundary/determinism решений из `P2`.
- Финальный merge допустим только после прохождения тестового минимума из `artifacts/design/04-testing.md`.

## Scope implement-фазы
- Включено: safety governance для `diff`/`gen --check`/`gen`, boundary enforcement, deterministic drift semantics, тестовое покрытие и CLI contract alignment.
- Исключено: расширение transport/domain генерации вне safety-периметра, новые продуктовые capabilities, архитектурный redesign вне `DiffService`/`GenerateService`/`SafeWriter` контекста.

## Минимальные verification-команды
- `uv run pytest tests/unit tests/contract tests/integration -k "diff or gen or writer"`
- `uv run pytest tests/integration/test_generate_roundtrip.py`
- `openspec validate 004-diff-gen-safety --strict --no-interactive`

## Команда запуска
Implement выполняется отдельной командой: `/openspec-implement 004-diff-gen-safety` (или `/openspec-implement-single 004-diff-gen-safety`).
