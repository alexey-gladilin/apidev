# Implementation Handoff: 012-integration

## Назначение
Пакет фиксирует финальный handoff для отдельной implement-команды и подтверждает готовность change к запуску `/openspec-implement` в режиме implementation-continuation.

## Functional Scope (обязательный)
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
- Функциональный acceptance scope для запуска `/openspec-implement`: пункты 1-6 в разделе "Functional Scope (обязательный)" и соответствующие задачи фаз 01-03.
- Non-blocking cleanup: внутренний rename `generated_root` в задачах phase 04 выполняется отдельно и не блокирует functional approval/implement.

## Implementation-Continuation Status Audit
- Фазы 01-03: задачи `1.1-3.3` закрыты (`[x]`) и отражают baseline, повторно не открываются.
- В phase 04 задачи `4.1` и `4.2` закрыты (`[x]`) как pre-handoff stabilization.
- `4.3` закрывает финальный handoff-пакет и готовность к execution.
- `4.4`, `4.5`, `4.6` остаются открытыми как post-handoff execution scope.
- Вывод аудита: статус-трекер консистентен с режимом implementation-continuation; remaining scope однозначно локализован в phase 04.

## Readiness Checklist (pre-implement gate)
- `openspec validate 012-integration --strict --no-interactive` проходит.
- Path-boundary правило синхронизировано между delta-спекой и implementation scope фаз 01-03; repository-wide sync с `docs/architecture/*` выполняется в phase 04 (task 4.4) как release-gate.
- Для `init` задокументирована явная precedence matrix (`create|repair|force` x `integration-mode`).
- Для `init` задокументирована file-scope matrix (`integration-mode` x `runtime` -> managed artifacts/forbidden mutations).
- Для fail-fast зафиксирован diagnostics contract (`code`, `message`, `context`).
- Для fail-fast запланированы стабильные error codes и canonical serialization diagnostics envelope (task 4.6 с тестовым покрытием).
- Функциональные задачи фаз 01-03 однозначны по scope, Verification и DoD.

## Cross-link Integrity Audit
- Проверены основные связи plan/design/tasks и артефактов change-пакета:
- `tasks.md` -> `artifacts/plan/phase-01.md`, `phase-02.md`, `phase-03.md`, `phase-04.md`.
- `artifacts/plan/README.md` -> `phase-01.md`, `phase-02.md`, `phase-03.md`, `phase-04.md`, `implementation-handoff.md`.
- `artifacts/plan/implementation-handoff.md` -> `../../tasks.md`, `../../design.md`, `../design/README.md`.
- `design.md` и `proposal.md` -> `artifacts/plan/README.md`, `specs/cli-tool-architecture/spec.md`.
- Результат: битых внутренних ссылок в проверенном plan/design/tasks контуре не обнаружено.

## Readiness Review
- Change-пакет готов к запуску `/openspec-implement`: scope, acceptance, verification и cross-links согласованы.
- Риск неоднозначного продолжения снижен: baseline-задачи отмечены, remaining execution scope ограничен задачами `4.4-4.6`.
- Single writer tracker соблюден: источник статуса выполнения остается `tasks.md`.

## HANDOFF PROTOCOL (обязательный)
- Task ID: `4.3`
- Task Description: `Phase: 04; Scope: подготовить финальный handoff для отдельной implement-команды`
- Files Changed: [`openspec/changes/012-integration/artifacts/plan/implementation-handoff.md`]
- Test Files: `[]`
- Tests Written: `0`
- All Tests Passing: `YES`
- Summary: `Добавлен явный HANDOFF protocol-блок с обязательными полями для задачи 4.3 и сохранена консистентность plan/tasks связей.`

## HANDOFF PROTOCOL (Task 4.4)
- Task ID: `4.4`
- Task Description: `Phase: 04; Scope: синхронизировать repository-wide архитектурные документы с новым write-boundary правилом (generated_dir/scaffold_dir в пределах project_dir)`
- Files Changed: [`docs/architecture/architecture-overview.md`, `docs/architecture/architecture-rules.md`, `docs/architecture/validation-blueprint.md`, `docs/architecture/generated-integration.md`]
- Test Files: `[]`
- Tests Written: `0`
- All Tests Passing: `YES`
- Summary: `Добавлен отдельный handoff-блок для Task 4.4 с фиксацией scope, затронутых архитектурных документов и статуса проверок.`

## HANDOFF PROTOCOL (Task 4.5)
- Task ID: `4.5`
- Task Description: `Phase: 04; Scope: [Non-blocking cleanup] провести non-functional рефакторинг внутреннего нейминга generated_root -> generated_dir_path (или эквивалент) в src/** и tests/** без изменения внешнего контракта generator.generated_dir`
- Files Changed: [`src/apidev/application/services/diff_service.py`, `src/apidev/infrastructure/output/writer.py`, `tests/unit/test_diff_service_remove_planning_challenge.py`, `tests/unit/architecture/test_generated_dir_path_naming.py`, `openspec/changes/012-integration/artifacts/plan/implementation-handoff.md`]
- Test Files: [`tests/unit/test_diff_service_remove_planning_challenge.py`, `tests/unit/architecture/test_generated_dir_path_naming.py`]
- Tests Written: `0`
- All Tests Passing: `YES`
- Summary: `Добавлен отдельный handoff-блок для Task 4.5; verification выполнен: pytest (371 passed), ruff (all checks passed), mypy (no issues).`

## HANDOFF PROTOCOL (Task 4.6)
- Task ID: `4.6`
- Task Description: `Phase: 04; Scope: зафиксировать стабильный diagnostics envelope для fail-fast (code/message/context) с канонической сериализацией context и неизменяемым каталогом нормативных fail-fast error codes`
- Files Changed: [`src/apidev/application/dto/diagnostics.py`, `src/apidev/application/dto/generation_plan.py`, `docs/reference/cli-contract.md`, `tests/unit/test_fail_fast_diagnostics_envelope.py`, `tests/contract/architecture/test_fail_fast_codes_contract.py`, `openspec/changes/012-integration/tasks.md`, `openspec/changes/012-integration/artifacts/plan/implementation-handoff.md`]
- Test Files: [`tests/unit/test_fail_fast_diagnostics_envelope.py`, `tests/contract/architecture/test_fail_fast_codes_contract.py`]
- Tests Written: `2`
- All Tests Passing: `YES`
- Summary: `Добавлены контрактно-стабильный каталог fail-fast кодов, канонизация context (лексикографический порядок + исключение пустых полей) и тесты на байтовую стабильность JSON envelope и неизменность documented code catalog.`

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
