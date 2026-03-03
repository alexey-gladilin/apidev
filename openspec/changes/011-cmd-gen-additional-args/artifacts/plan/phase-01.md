# Phase 01: CLI Surface и контракт фильтрации endpoint-ов

## Цель фазы
Зафиксировать CLI-поверхность include/exclude endpoint аргументов и безопасно провести их до application-слоя.

## Scope
- Добавление `--include-endpoint` и `--exclude-endpoint` в `apidev gen`.
- Нормализация/валидация флагов.
- Передача фильтров в generate pipeline DTO/service contract.

## Выходы
- Обновленный CLI command contract в коде.
- Unit tests для parsing и передачи аргументов.

## Verification Gate
- `uv run pytest tests/unit/test_cli_conventions.py -k "include_endpoint or exclude_endpoint"`
- `uv run pytest tests/unit -k "generate and endpoint_filter"`

## Риски
- Некорректный parsing множественных флагов.
- Потеря обратной совместимости старого запуска без фильтров.

## Definition of Done
- Новые флаги документированы в help.
- CLI корректно обрабатывает несколько include/exclude значений.
- Слой сервисов получает нормализованный набор фильтров.
- Без флагов поведение полностью совместимо с текущим контрактом.
