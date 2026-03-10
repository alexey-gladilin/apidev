# Тестирование

## Обязательные проверки
- unit tests на parse/required-field validation новых metadata полей;
- contract tests на invalid combinations и deterministic diagnostics;
- integration tests на operation map и OpenAPI vendor extensions;
- migration-failure tests на legacy contracts без новых полей;
- final gates:
  - `uv run pytest`
  - `openspec validate add-operation-intent-metadata --strict --no-interactive`

## Критические сценарии
- `POST` + `intent=read` + `access_pattern=imperative` проходит validate и публикуется в metadata.
- `intent=write` + `access_pattern=cached` отклоняется.
- contract без `intent` отклоняется required-field diagnostic.
- contract без `access_pattern` отклоняется required-field diagnostic.
