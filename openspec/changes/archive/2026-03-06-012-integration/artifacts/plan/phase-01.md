# Phase 01: Основа конфигурации и валидации

## Цель фазы
Зафиксировать безопасную модель конфигурации для integration output и валидацию входных контрактов.

## Scope
- Разделить `scaffold_dir` и `generated_dir` как независимые output roots.
- Добавить `generator.scaffold_write_policy` с детерминированными режимами записи.
- Поддержать short-form `errors[].example` с нормализацией в каноническую модель.
- Усилить strict validation release-state по ключам и типам без миграционного fallback.

## Выходы
- Обновленные config/rules контракты для новой интеграционной модели.
- Unit/integration тесты на path-boundaries, policy semantics, нормализацию примеров ошибок и release-state validation error-path.

## Verification Gate
- `uv run pytest tests/unit -k "config or scaffold or example"`
- `uv run pytest tests/integration -k "scaffold"`
- `uv run pytest tests/unit -k "release_state and validation"`
- `uv run ruff check src tests`
- `uv run mypy src`

## Риски
- Непреднамеренная перезапись scaffold-файлов при неверном policy default.
- Неочевидные конфигурационные ошибки release-state без явной диагностики.

## Definition of Done
- Новые config semantics детерминированы и покрыты тестами.
- Невалидный release-state детектируется через строгую валидацию с понятным сообщением об ошибке.
- Проверки фазы проходят полностью.
