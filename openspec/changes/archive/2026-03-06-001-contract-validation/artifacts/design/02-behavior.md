# Поведение Validate После Hardening

## Цели поведения
1. Валидация формирует структурированные diagnostics вместо `list[str]`.
2. Проверки выполняются в два шага: `schema` затем `semantic`.
3. CLI поддерживает два режима вывода:
   - human-readable (по умолчанию);
   - JSON (`--json`) для CI и интеграций.
4. Exit code остается совместимым: `0` при успехе, `1` при validation errors.

## Минимальный контракт диагностики
Каждая запись diagnostics содержит:
- `code`
- `severity` (`error` | `warning`)
- `message`
- `location`
- `rule`

## Acceptance Criteria
1. `apidev validate` без флагов печатает только human-readable вывод.
2. `apidev validate --json` печатает валидный JSON (diagnostics + summary).
3. Каждая JSON-диагностика содержит `code`, `severity`, `message`, `location`, `rule`.
4. Duplicate `operation_id` репортится как структурированная диагностика со стабильным кодом.
5. Schema-level и semantic-level нарушения различимы по `rule`/`code`.
6. Любая ошибка (`severity=error`) приводит к `exit code 1`.
7. Отсутствие ошибок приводит к `exit code 0`.
