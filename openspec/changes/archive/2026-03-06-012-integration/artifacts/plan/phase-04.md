# Phase 04: Стабилизация, документация, выпускной gate

## Цель фазы
Закрыть change финальной документацией, regression coverage и strict validation.

## Scope
- Синхронизировать docs/spec deltas с фактическим контрактом изменений.
- Сформировать regression matrix по затронутым подсистемам.
- Подготовить implementation handoff для отдельной implement-команды.
- Выполнить non-functional cleanup терминологии: унифицировать внутренний naming `generated_root` -> `generated_dir_path` в коде и тестах без изменения внешних пользовательских терминов.
- Non-functional cleanup терминологии не блокирует функциональный acceptance по scope фаз 01-03.
- Functional readiness для `/openspec-implement` оценивается по задачам фаз 01-03; cleanup-пункт выполняется отдельно.

## Выходы
- Обновленные `docs/reference/*` и финальные delta-спеки.
- Полный handoff-пакет в `artifacts/plan/*` и `tasks.md`.
- Согласованный внутренний naming в `src/**` и `tests/**` для путей generated output.

## Verification Gate
- `uv run pytest tests/unit tests/integration -k "scaffold or openapi or init"`
- `uv run ruff check src tests`
- `uv run mypy src`
- `openspec validate 012-integration --strict --no-interactive`

## Риски
- Несогласованность документации и реального контракта.

## Definition of Done
- Документация и спеки консистентны с планом реализации.
- Strict validation проходит.
- Handoff готов для запуска `/openspec-implement`.
- Внутренний термин `generated_root` не используется как основной в новом/обновленном коде; внешние контракты (`generator.generated_dir`) не меняются.
