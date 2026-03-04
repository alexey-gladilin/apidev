# Phase 03: Профили `init` и UX интеграции

## Цель фазы
Сделать bootstrap integration-сценариев через `apidev init` предсказуемым и минимально ручным.

## Scope
- Добавить profile-флаги `--runtime`, `--integration-mode`, `--integration-dir`.
- Зафиксировать допустимые значения profile-флагов:
  - `--runtime`: `fastapi|none`;
  - `--integration-mode`: `off|scaffold|full`.
- Синхронизировать lifecycle integration templates с режимами `--repair`/`--force`.
- Зафиксировать precedence-матрицу для `create|repair|force` и profile-флагов.
- Зафиксировать идемпотентное поведение повторного `init`.

## Выходы
- Обновленный CLI-контракт `init`.
- Integration tests для матрицы профилей/режимов.

## Verification Gate
- `uv run pytest tests/integration -k "init and integration"`
- `uv run pytest tests/unit -k "init_cmd"`
- `uv run ruff check src tests`
- `uv run mypy src`

## Риски
- Конфликт новых флагов с текущими сценариями `init`.
- Неочевидное precedence поведение между profile flags и repair/force.

## Definition of Done
- Профили `init` документированы и покрыты тестами.
- Поведение repair/force детерминировано и проверяемо.
- Проверки фазы проходят полностью.
