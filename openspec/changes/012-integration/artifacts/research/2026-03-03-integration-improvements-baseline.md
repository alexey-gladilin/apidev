# Исследование baseline: 012-integration

## Scope
- Baseline собран по 6 областям из входного документа: `scaffold_dir`/scaffold write, runtime OpenAPI adapter, syntax error examples, release-state compatibility/migration, init integration profile, `x-apidev-*` extensions.
- Источники: текущий репозиторий и входной документ `/Users/alex/1.PROJECTS/ALFA/orbit/docs/apidev-integration-improvements.md`.

## Метод
- Проверены: модель конфигурации, сервисы `diff/gen/init`, шаблоны генерации, CLI-команды, архитектурная и reference-документация, unit/integration/contract тесты.
- Для каждого утверждения указаны ссылки на код и документацию.
- В этом baseline используются исторические термины на момент исследования (включая `generated_root`); актуальная терминология change-пакета — `generated_dir`.

## Наблюдения
- `generator.scaffold_dir` валидируется как непустая строка, но в `DiffService` запрещены absolute path и выход за `generated_root`.
  - `src/apidev/core/models/config.py:10`
  - `src/apidev/application/services/diff_service.py:813`
  - `docs/reference/contract-format.md:87`
  - `tests/unit/test_diff_service_scaffold_generation.py:86`
- Политика записи scaffold сейчас фиксированная (`create-if-missing`): существующие scaffold-файлы не перезаписываются.
  - `src/apidev/application/services/diff_service.py:790`
  - `docs/reference/cli-contract.md:56`
  - `tests/integration/test_scaffold_cli_and_generation.py:92`
- Runtime integration scaffold (`integration_router_factory.py.j2`) формирует metadata-структуру, но не создает `APIRouter.add_api_route(...)`.
  - `src/apidev/templates/integration_router_factory.py.j2:11`
- `operation_map` уже содержит ключевые operation metadata (`method/path/auth/summary/description/deprecation`).
  - `src/apidev/application/services/diff_service.py:942`
  - `src/apidev/templates/generated_operation_map.py.j2:8`
- `openapi_docs` формирует `summary`, `description`, `deprecated`, success-response и `x-apidev-*` extensions; отдельные HTTP error responses и tags не формируются как часть маршрутизации runtime.
  - `src/apidev/templates/generated_openapi_docs.py.j2:16`
  - `src/apidev/templates/generated_openapi_docs.py.j2:25`
  - `src/apidev/templates/generated_openapi_docs.py.j2:36`
- Для ошибок поддерживается `errors[].body.example`; short-form `errors[].example` не входит в allowlist полей error-item.
  - `src/apidev/core/rules/contract_schema.py:29`
  - `src/apidev/core/rules/contract_schema.py:276`
  - `src/apidev/application/services/diff_service.py:1122`
- Release-state читается через strict schema `ReleaseState` (`extra="forbid"`, обязательный `release_number`) без migration-слоя.
  - `src/apidev/infrastructure/config/toml_loader.py:39`
  - `src/apidev/core/models/release_state.py:25`
  - `tests/unit/test_config_release_state_validation.py:66`
- CLI включает `init/validate/diff/gen` и alias `generate`; команд `doctor`/`migrate-config` нет.
  - `src/apidev/cli.py:61`
- `init` сейчас поддерживает только `--repair` и `--force`; integration profile флагов нет.
  - `src/apidev/commands/init_cmd.py:7`
- `init` управляет `config`, sample-contract и `generated_*` templates; integration scaffold templates не входят в init-managed список.
  - `src/apidev/application/services/init_service.py:66`
  - `src/apidev/application/services/init_service.py:115`
- `x-apidev-deprecation` и `x-apidev-errors` вставляются в OpenAPI без конфиг-переключателя.
  - `src/apidev/templates/generated_openapi_docs.py.j2:21`
  - `src/apidev/templates/generated_openapi_docs.py.j2:36`
  - `src/apidev/core/models/config.py:48`

## Подтвержденные разрывы
- `scaffold_dir` как независимый output-root из документа не совпадает с текущим ограничением на `generated_root`.
- Требуемые режимы `scaffold_write_policy` отсутствуют.
- Runtime OpenAPI adapter из документа (единый `add_api_route` с errors/tags/auth metadata) сейчас отсутствует.
- Short-form `errors[].example` не поддерживается.
- Миграция legacy release-state (`current_release` -> `release_number`) отсутствует.
- Профили `apidev init --runtime ... --integration-mode ... --integration-dir ...` отсутствуют.
- Переключатель `openapi.include_extensions` отсутствует.

## Риски данных/неопределенности
- В репозитории не найден отдельный тест, который явно проверяет `errors[].example` с конкретным diagnostic code; вывод сделан по allowlist/unknown-field механике валидации.
- В репозитории не найден отдельный тест legacy release-state с ключом `current_release`; вывод сделан по текущей strict schema.

## Evidence Index
- Входной baseline-документ: `/Users/alex/1.PROJECTS/ALFA/orbit/docs/apidev-integration-improvements.md:11`
- Scaffold behavior: `src/apidev/application/services/diff_service.py:790`, `docs/reference/contract-format.md:72`
- OpenAPI/runtime artifacts: `src/apidev/templates/generated_operation_map.py.j2:5`, `src/apidev/templates/generated_openapi_docs.py.j2:6`, `src/apidev/templates/integration_router_factory.py.j2:11`
- Error example syntax: `src/apidev/core/rules/contract_schema.py:27`, `src/apidev/application/services/diff_service.py:1122`
- Release-state lifecycle: `src/apidev/infrastructure/config/toml_loader.py:39`, `src/apidev/core/models/release_state.py:25`
- Init/CLI surface: `src/apidev/commands/init_cmd.py:7`, `src/apidev/application/services/init_service.py:115`, `src/apidev/cli.py:61`
