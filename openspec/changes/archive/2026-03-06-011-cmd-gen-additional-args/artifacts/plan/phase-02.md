# Phase 02: Endpoint selection в generation pipeline

## Цель фазы
Внедрить deterministic фильтрацию endpoint-ов в generation plan для `apidev gen`.

## Scope
- Include/exclude selection перед построением планов `ADD|UPDATE|REMOVE`.
- Diagnostics для invalid pattern и empty effective set.
- Контроль stale-remove semantics при частичной генерации.

## Выходы
- Измененный selection path в `DiffService`/`GenerateService`.
- Набор unit/integration тестов на happy/error path.

## Verification Gate
- `uv run pytest tests/unit -k "diff_service and endpoint_filter"`
- `uv run pytest tests/integration -k "gen and endpoint_filter and diagnostics"`
- `uv run pytest tests/integration -k "remove and endpoint_filter"`

## Риски
- Непредсказуемое удаление файлов вне выбранного scope.
- Расхождение детерминированности результата при одинаковом наборе фильтров.

## Definition of Done
- Effective set рассчитывается по правилу `include -> exclude`.
- Пустой effective set приводит к явному fail-fast diagnostics.
- Safety boundary удаления не ослабляется.
- Повторные запуски с одинаковыми фильтрами дают идентичный план.
