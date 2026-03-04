# Implementation Handoff: 012-integration

## Что реализовать
1. Добавить независимый `scaffold_dir` и `scaffold_write_policy` (`create-missing|skip-existing|fail-on-conflict`).
2. Реализовать runtime/OpenAPI adapter projection на базе operation metadata.
3. Поддержать short-form `errors[].example` с нормализацией.
4. Расширить `apidev init` integration profile-флагами.
5. Добавить `openapi.include_extensions` toggle.
6. Усилить strict validation release-state (legacy key/type mismatch -> validation error) без миграции.

## Ключевые файлы
- `src/apidev/core/models/config.py`
- `src/apidev/application/services/diff_service.py`
- `src/apidev/application/services/generate_service.py`
- `src/apidev/application/services/init_service.py`
- `src/apidev/infrastructure/config/toml_loader.py`
- `src/apidev/commands/init_cmd.py`
- `src/apidev/templates/integration_router_factory.py.j2`
- `src/apidev/templates/generated_openapi_docs.py.j2`
- `src/apidev/templates/generated_operation_map.py.j2`
- `docs/reference/contract-format.md`
- `docs/reference/cli-contract.md`

## Критерии приемки
- Без новых опций поведение остается прежним.
- `scaffold_dir` и `scaffold_write_policy` работают детерминированно и безопасно.
- Default `generator.scaffold_write_policy` зафиксирован как `create-missing`.
- Runtime/OpenAPI metadata согласованы и покрыты тестами.
- Домен в Swagger определяется из domain layout операции; наличие manual `tags` завершает генерацию с validation error.
- Невалидный release-state завершается явной ошибкой валидации без fallback.
- Profile-флаги `init` валидируются по enum-контракту: `--runtime=<fastapi|none>`, `--integration-mode=<off|scaffold|full>`, documented precedence с `--repair/--force`.
- Для `errors[].example` зафиксирована единая семантика: эквивалентные short/nested значения валидны, конфликтующие значения дают fail-fast validation error.
- `openspec validate 012-integration --strict --no-interactive` проходит.

## Functional vs Non-Blocking Scope
- Функциональный acceptance scope для запуска `/openspec-implement`: пункты 1-6 в разделе "Что реализовать" и соответствующие задачи фаз 01-03.
- Non-blocking cleanup: внутренний rename `generated_root` в задачах phase 04 выполняется отдельно и не блокирует functional approval/implement.

## Readiness Checklist (pre-implement)
- `openspec validate 012-integration --strict --no-interactive` проходит.
- Path-boundary правило синхронизировано между delta-спекой и `docs/architecture/*` (AR-006).
- Для `init` задокументирована явная precedence matrix (`create|repair|force` x `integration-mode`).
- Для `init` задокументирована file-scope matrix (`integration-mode` x `runtime` -> managed artifacts/forbidden mutations).
- Для fail-fast зафиксирован diagnostics contract (`code`, `message`, `context`).
- Для fail-fast зафиксированы стабильные error codes и canonical serialization diagnostics envelope.
- Функциональные задачи фаз 01-03 однозначны по scope, Verification и DoD.

## Связи
- Core tasks: [../../tasks.md](../../tasks.md)
- Design summary: [../../design.md](../../design.md)
- Design package: [../design/README.md](../design/README.md)

## Уточнение по архитектурным правилам
- Источником истины по write-boundary остаются синхронизированные `docs/architecture/*` и delta-спека `012-integration`.
- Для implement-review проверяется отсутствие расхождения между:
  - `docs/architecture/architecture-rules.md` (AR-006),
  - `docs/architecture/architecture-overview.md`,
  - `docs/architecture/generated-integration.md`,
  - `openspec/changes/012-integration/specs/cli-tool-architecture/spec.md`.
