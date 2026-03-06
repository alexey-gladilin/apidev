# Change: Улучшения интеграции `apidev` для внешнего runtime-слоя

## Почему
В реальном сценарии внедрения выявлены повторяющиеся проблемы: `scaffold_dir` жестко связан с generated-root, OpenAPI/runtime wiring требует ручной доработки, short-form examples для ошибок не поддерживаются.
Это увеличивает ручной труд и риск регрессий при интеграции `apidev` в существующие проекты.

## Что изменится
- Добавляется независимая модель output-контуров:
  - `generator.generated_dir` и `generator.scaffold_dir` как отдельные каталоги в пределах `project_dir`.
- Добавляется управляемая политика записи scaffold:
  - `generator.scaffold_write_policy = "create-missing" | "skip-existing" | "fail-on-conflict"`.
  - default: `create-missing` (сохранение текущего поведения без новых опций).
- Формализуется runtime/OpenAPI adapter из operation metadata:
  - маршрутизация endpoint-ов через единый generated integration-layer;
  - проброс `operation_id`, summary/description/deprecated, errors/responses и auth metadata;
  - доменная группировка в Swagger вычисляется автоматически из домена операции (manual `tags` не являются source of truth).
- Поддерживается short-form синтаксис `errors[].example` с нормализацией к канонической форме.
- Расширяется `apidev init` для integration profile:
  - `--runtime <fastapi|none>`, `--integration-mode <off|scaffold|full>`, `--integration-dir <path>`.
  - для примеров и документации используется канонический CLI-синтаксис через пробел: `--flag value` (форма `--flag=value` допускается, но не является канонической в проекте).
  - правила precedence: `--force` и `--repair` остаются взаимоисключающими; profile-флаги управляют только integration-артефактами и применяются в выбранном режиме (`create|repair|force`) детерминированно.
- Добавляется флаг OpenAPI extensions:
  - `openapi.include_extensions = true|false`.
- Уточняется strict validation release-state:
  - старый ключ (`current_release`) и неверный тип `release_number` приводят к явной ошибке валидации.
- Обновляются архитектурные документы под новое write-boundary правило:
  - `generated_dir` и `scaffold_dir` как независимые контуры в пределах `project_dir`;
  - единый path-boundary policy для generated/scaffold outputs.
- Явно исключается из scope:
  - миграция release-state;
  - backward compatibility для legacy release-state форматов.

## Влияние
- Затронутые спеки: `cli-tool-architecture` (ADDED + MODIFIED requirements для write-boundary контракта).
- Затронутый код (на implement-фазе):
  - `src/apidev/core/models/config.py`
  - `src/apidev/application/services/diff_service.py`
  - `src/apidev/application/services/generate_service.py`
  - `src/apidev/application/services/init_service.py`
  - `src/apidev/commands/init_cmd.py`
  - `src/apidev/templates/integration_router_factory.py.j2`
  - `src/apidev/templates/generated_openapi_docs.py.j2`
  - `src/apidev/templates/generated_operation_map.py.j2`
  - `docs/reference/contract-format.md`, `docs/reference/cli-contract.md`
- Breaking:
  - не планируется; поведение по умолчанию остается прежним.

## Linked Artifacts
- Research: [artifacts/research/2026-03-03-integration-improvements-baseline.md](./artifacts/research/2026-03-03-integration-improvements-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Integration reference: [artifacts/design/05-integration-reference.md](./artifacts/design/05-integration-reference.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/cli-tool-architecture/spec.md](./specs/cli-tool-architecture/spec.md)

## Границы этапа
Этот change ведется в режиме implementation-continuation: часть задач уже закрыта в текущем baseline репозитория, оставшиеся пункты выполняются отдельной implement-командой.
Implement выполняется через `/openspec-implement` или `/openspec-implement-single` для незавершенных задач из `tasks.md`.
