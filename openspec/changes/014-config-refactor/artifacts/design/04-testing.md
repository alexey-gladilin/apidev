# Testing Strategy

## Unit
- Валидация канонической структуры секций.
- Отказ на `version` и любых legacy-ключах.
- Проверка path-boundary правил.

## Integration
- `apidev init` materialize-ит только новый конфиг.
- `validate/diff/gen` читают одинаковый resolved config.

## Regression
- Детеминированность diagnostics при ошибках загрузки.
- Отсутствие побочных изменений файлов при fail-fast валидации.

## Quality Gates
- `uv run pytest`
- `uv run ruff check src tests`
- `uv run mypy src`
