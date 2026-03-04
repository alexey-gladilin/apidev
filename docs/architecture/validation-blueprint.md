# План Архитектурной Валидации

Статус: `Reference`

Этот документ описывает, как архитектурные правила из `architecture-rules.md` превращаются в исполняемые guardrails в тестах и CI.

## Входные артефакты

- `docs/architecture/architecture-overview.md`
- `docs/architecture/architecture-rules.md`
- `docs/process/testing-strategy.md`
- исходный код `src/apidev/*`

## Фазы валидации

### Фаза 1. Static import checks

- парсинг Python AST для модулей под `src/apidev`;
- построение import graph между `apidev.commands`, `apidev.application`, `apidev.core`, `apidev.infrastructure`;
- проверка правил `AR-001` и частично `AR-004`.

### Фаза 2. Forbidden dependency checks

- проверка `AR-002` для запрета concrete infra imports в `application/*`;
- проверка `AR-003` для запрета direct I/O и format parsing в `core/*`;
- в будущем — проверка `AR-008` для raw YAML/TOML parsing в core.

### Фаза 3. Behavioral architecture checks

- проверка `AR-005` через сценарии без side effects для `diff` и `apidev gen --check`;
- проверка `AR-006` через negative tests для write boundary (`generated_dir`/`scaffold_dir` внутри `project_dir`) и запрета contour conflict (`generated_dir == scaffold_dir`, nested пересечение);
- проверка `AR-007` через tests на single source path policy;
- в будущем — review-oriented heuristics для `AR-009`.

### Фаза 4. Convention checks

- review-checks для `AR-010`;
- при необходимости — lightweight grep/AST checks для языка документации и code artifacts.

## Текущая матрица traceability

| Rule ID | Основная проверка | Текущий тест |
|---|---|---|
| AR-001 | import graph allowed edges | `test_layering_imports.py` |
| AR-002 | no infra imports in app layer | `test_application_no_infra_imports.py` |
| AR-003 | no direct I/O/format handling in core | `test_core_purity.py` |
| AR-005 | side-effect safety | `test_pipeline_contract.py` |
| AR-006 | out-of-bound write rejection + contour conflict rejection for project-dir bounded generated/scaffold outputs | `test_write_boundary_policy.py` |
| AR-007 | config path consistency | `test_config_path_single_source.py` |

## Целевые расширения

- `AR-004` — test или metric guard на thinness commands
- `AR-008` — автоматическая проверка raw format parsing в core
- `AR-009` — heuristic guard против service bloat
- `AR-010` — repository-level policy checks после стабилизации baseline

## Целевой layout тестов

```text
tests/
  unit/
    architecture/
      test_layering_imports.py
      test_application_no_infra_imports.py
      test_core_purity.py
  contract/
    architecture/
      test_pipeline_contract.py
      test_write_boundary_policy.py
      test_config_path_single_source.py
```

## Изменение правил

Если меняется архитектурное правило:

1. обновить `architecture-rules.md`;
2. обновить `architecture-overview.md`, если меняется baseline;
3. обновить этот документ, если меняется стратегия валидации;
4. обновить тесты, если правило должно быть test-backed;
5. при behavior-level изменении синхронизировать change с OpenSpec.

## Связанные документы

- `docs/architecture/architecture-rules.md`
- `docs/architecture/architecture-overview.md`
- `docs/process/testing-strategy.md`
