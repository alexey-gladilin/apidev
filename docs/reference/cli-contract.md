# CLI Контракт APIDev

Статус: `Authoritative`

Этот документ задает проверяемый контракт CLI и используется как единый источник истины для PR review, тестов и изменений help/UX.

## Канонические команды

Набор верхнего уровня:

- `apidev init`
- `apidev validate`
- `apidev diff`
- `apidev gen`
- `apidev version`

Каноническая команда генерации:

- `apidev gen`

Compatibility alias:

- `apidev generate`

Во всех нормативных документах, walkthroughs и примерах должна использоваться команда `apidev gen`. Алиас `apidev generate` упоминается только как compatibility mechanism.

## Контракт синтаксиса CLI-опций

- Каноническая форма записи опций с аргументом в документации, тестах и примерах: `--option value`.
- Форма `--option=value` может поддерживаться CLI-парсером, но не используется как канонический стиль в репозитории.
- Для флагов без аргумента используется только форма `--flag`.

## Контракт profile-флагов `apidev init`

Поддерживаемые profile-флаги:

- `--runtime <fastapi|none>`
- `--integration-mode <off|scaffold|full>`
- `--integration-dir <path>`

Нормативные правила:

- в документации и примерах используется канонический синтаксис `--flag value`;
- `--runtime` принимает только `fastapi` или `none`;
- `--integration-mode` принимает только `off`, `scaffold` или `full`;
- `--integration-mode full` с `--runtime none` запрещена (`config.INIT_MODE_CONFLICT`);
- `--integration-dir` должен быть непустым относительным путем внутри `project_dir` (`validation.PATH_BOUNDARY_VIOLATION`);
- невалидные enum-значения profile-флагов завершаются ошибкой валидации (`config.INIT_PROFILE_INVALID_ENUM`) до файловых операций.

Канонические примеры:

```bash
apidev init --runtime fastapi --integration-mode scaffold --integration-dir integration
apidev init --runtime none --integration-mode off --integration-dir integration
```

## UX profile-based bootstrap для `apidev init`

Контур bootstrap profile-режимов работает без миграционного fallback:

- `apidev init` управляет только init-managed файлами (`.apidev/config.toml`, sample contract и profile-managed templates);
- команда не выполняет автоматическую миграцию legacy-структур и не переписывает произвольные пользовательские файлы вне init-managed scope.

Precedence и режимы:

- default режим: `create`;
- `--repair` переключает режим в `repair`;
- `--force` переключает режим в `force`;
- одновременная передача `--repair` и `--force` запрещена и завершается CLI parsing ошибкой (exit code `2`);
- profile-валидация (`--runtime`, `--integration-mode`, `--integration-dir`) выполняется до файловых операций.

Поведение режимов в profile scope:

- `create`: создает отсутствующие managed-файлы; при измененных managed-файлах завершает команду ошибкой и рекомендует `--repair` или `--force`;
- `repair`: восстанавливает только невалидные/измененные managed-файлы в пределах выбранного profile scope;
- `force`: перезаписывает все managed-файлы выбранного profile scope независимо от текущего содержимого.

Matrix: mode precedence (`create|repair|force` x profile):

| Режим | Profile-условие | Нормативное поведение |
|---|---|---|
| `create` | Валидный профиль (`runtime`, `integration-mode`, `integration-dir`) | Создаются только отсутствующие profile-managed templates; измененные managed templates не перезаписываются автоматически |
| `repair` | Валидный профиль | Восстанавливаются только проблемные profile-managed templates из текущего profile-scope |
| `force` | Валидный профиль | Перезаписывается весь profile-managed template-набор текущего profile-scope |
| Любой | `--repair` + `--force` | CLI parsing error (exit code `2`) до файловых операций |
| Любой | Невалидный enum в `--runtime`/`--integration-mode` | Fail-fast validation error `config.INIT_PROFILE_INVALID_ENUM` до файловых операций |
| Любой | Невалидный `--integration-dir` (пустой/absolute/outside `project_dir`) | Fail-fast validation error `validation.PATH_BOUNDARY_VIOLATION` до файловых операций |

Matrix: file-scope для profile-managed templates (`integration-mode` x `runtime`):

| `integration-mode` | `runtime` | Profile-managed templates (`.apidev/templates`) | Forbidden mutations |
|---|---|---|---|
| `off` | `fastapi` / `none` | Нет integration templates в profile-scope | Любые записи integration template-файлов вне init-managed scope |
| `scaffold` | `none` | `integration_handler_registry.py.j2`, `integration_error_mapper.py.j2` | Создание runtime-specific templates (`integration_router_factory.py.j2`, `integration_auth_registry.py.j2`) |
| `scaffold` | `fastapi` | `integration_handler_registry.py.j2`, `integration_router_factory.py.j2`, `integration_auth_registry.py.j2`, `integration_error_mapper.py.j2` | Запись generated template-набора (`generated_operation_map.py.j2`, `generated_openapi_docs.py.j2`, `generated_router.py.j2`, `generated_schema.py.j2`) |
| `full` | `fastapi` | Scaffold-набор + `generated_operation_map.py.j2`, `generated_openapi_docs.py.j2`, `generated_router.py.j2`, `generated_schema.py.j2` | Запись файлов вне profile-scope и вне init-managed scope |
| `full` | `none` | Нет (комбинация запрещена) | Fail-fast validation error `config.INIT_MODE_CONFLICT` до файловых операций |

## Контракт структуры generated output

Каноническая структура generated output для `apidev diff`/`apidev gen` — domain-first:

```text
<generated_dir>/
├── operation_map.py
├── openapi_docs.py
└── <domain>/
    ├── routes/
    │   └── <operation>.py
    └── models/
        ├── <operation>_request.py
        ├── <operation>_response.py
        └── <operation>_error.py
```

Здесь `<generated_dir>` определяется через `generator.generated_dir` в `.apidev/config.toml`.

## Контракт scaffold-флагов

Для `apidev gen` и `apidev diff` поддерживаются CLI overrides:

- `--scaffold` — включить генерацию integration scaffold в текущем запуске;
- `--no-scaffold` — отключить генерацию integration scaffold в текущем запуске.

Правила:

- если ни один флаг не указан, используется `generator.scaffold` из `.apidev/config.toml`;
- при указании флага CLI имеет приоритет над config;
- итоговая политика записи scaffold-файлов определяется `generator.scaffold_write_policy`;
- поддерживаемые политики `generator.scaffold_write_policy`:
  - `create-missing` (default): создаются только отсутствующие scaffold-файлы;
  - `skip-existing`: существующие scaffold-файлы пропускаются, отсутствующие создаются;
  - `fail-on-conflict`: при наличии целевого scaffold-файла генерация завершается fail-fast ошибкой.

## Контракт OpenAPI extensions

Параметр `.apidev/config.toml`:

```toml
[openapi]
include_extensions = true
```

Правила:

- `openapi.include_extensions` управляет только extension-полями `x-apidev-*` в `openapi_docs.py`;
- при `include_extensions = false` extension-поля `x-apidev-*` не генерируются;
- базовые OpenAPI-поля (`operationId`, `summary`, `description`, `deprecated`, `tags`, `security`, `responses`) не меняются;
- default `include_extensions = true` сохраняет прежнее поведение генерации.

## Контракт `request.path/query/body` для CLI

Поддерживаемая структура request-блока в контракте:

- разрешены только `request.path`, `request.query`, `request.body`;
- каждый из трех фрагментов должен быть schema-object;
- неизвестные поля внутри `request` приводят к `validation.request-unknown-field`.

Fail-fast правила path-consistency:

- если route path содержит placeholder (`{...}`), а `request.path` отсутствует, `validate` возвращает `validation.missing-request-path`;
- если placeholder-ы route и `request.path.properties` не совпадают, `validate` возвращает `validation.request-path-mismatch`;
- при дублирующихся placeholder-ах в route используется `validation.duplicate-path-placeholder`.

Контракт ожидаемой OpenAPI-проекции из `request`:

- `request.path.properties` публикуются в `parameters` с `in=path`, обязательность всегда `true`;
- `request.query.properties` публикуются в `parameters` с `in=query`, обязательность вычисляется из `required: true` на property-level;
- `request.body` публикуется как `requestBody.content.application/json.schema`;
- если request metadata пустая, `parameters` и `requestBody` отсутствуют в operation.

## Контракт endpoint-фильтров для `apidev gen`

`apidev gen` поддерживает повторяемые фильтры:

- `--include-endpoint <pattern>`
- `--exclude-endpoint <pattern>`

Семантика фильтрации:

- `include` формирует исходный candidate set;
- `exclude` применяется после include и вычитает endpoint-ы из candidate set;
- если include не задан, candidate set = полный набор endpoint-ов;
- порядок применения всегда `include -> exclude`.

Что именно матчится:

- `pattern` применяется к `operation_id`;
- `pattern` применяется к `contract_relpath` (относительный путь YAML-контракта);
- endpoint считается совпавшим, если pattern совпал хотя бы с одним из двух значений (`operation_id OR contract_relpath`).

Тип pattern:

- используется `case-sensitive glob`;
- пустой pattern считается невалидным;
- malformed glob pattern (например, незакрытый `[` в character class) считается невалидным.

Diagnostics contract для endpoint-фильтров:

- невалидный pattern возвращает `generation.invalid-endpoint-pattern`;
- пустой effective set после include/exclude возвращает `generation.empty-endpoint-selection`;
- оба diagnostics публикуются с полями `code`, `location`, `detail` в text и JSON режимах `apidev gen`.

Примеры:

```bash
# Включить только endpoint-ы по operation_id
apidev gen --include-endpoint "billing.*"

# Включить endpoint-ы по относительному пути контракта
apidev gen --include-endpoint "contracts/v1/users/*.yaml"

# Комбинация include/exclude: include -> exclude
apidev gen \
  --include-endpoint "contracts/v1/**" \
  --exclude-endpoint "*admin*"

# Несколько include-фильтров
apidev gen \
  --include-endpoint "billing.*" \
  --include-endpoint "contracts/v1/payments/*.yaml"
```

## Примеры `validate` и `gen` для request-сценариев

### `validate`: корректный request-контракт

```bash
apidev validate --project-dir /tmp/apidev-request-ok --json
```

Ожидание:

- exit code `0`;
- `summary.status = ok`;
- diagnostics пустой массив.

### `validate`: path placeholder без `request.path`

```bash
apidev validate --project-dir /tmp/apidev-request-missing-path --json
```

Ожидание:

- exit code `1`;
- в diagnostics есть `validation.missing-request-path`;
- location указывает на `<contract>.yaml:request.path`.

### `validate`: неизвестное поле в `request`

```bash
apidev validate --project-dir /tmp/apidev-request-unknown-field --json
```

Ожидание:

- exit code `1`;
- в diagnostics есть `validation.request-unknown-field`;
- location указывает на `<contract>.yaml:request.<field>`.

### `gen` + `gen --check`: OpenAPI-проекция request

```bash
# 0) Preconditions: git baseline + release-state должны существовать.
cd /tmp/apidev-request-openapi
git init
git add .
git commit -m "baseline for request-openapi scenario"
git tag v0.1.0

# 1) Первый apply-прогон создает/синхронизирует release-state
#    (по умолчанию .apidev/release-state.json) и фиксирует baseline_ref.
apidev gen --project-dir /tmp/apidev-request-openapi --baseline-ref v0.1.0

# 2) Повторный check-прогон выполняется на неизмененном состоянии.
apidev gen --check --project-dir /tmp/apidev-request-openapi --json
```

Ожидание:

- precondition выполнен: существует git baseline (`v0.1.0`) и `.apidev/release-state.json` после первого `gen`;
- после `gen` в `<generated_dir>/openapi_docs.py` operation содержит `parameters` и `requestBody`, если они заданы в `request`;
- `request.path` проецируется в `parameters[*].in = "path"` и `required = true`;
- `request.query` проецируется в `parameters[*].in = "query"` с property-level required;
- `request.body` проецируется в `requestBody`;
- `gen --check` на неизмененном состоянии возвращает `drift_status = no-drift` и exit code `0`.

## Контракт help и UX

Обязательные требования:

- каждый уровень команды поддерживает `-h` и `--help`;
- root-команда поддерживает `-v` и `--version` для печати версии и немедленного завершения;
- root help содержит секции `Usage`, `Options`, `Commands`;
- у каждой команды есть краткое и однозначное описание;
- ожидаемые пользовательские ошибки выводятся без traceback;
- формулировки ошибок пригодны для CI-логов и дают следующий шаг, если это применимо.

## Контракт совместимости

Правила алиасов:

- скрытый алиас сохраняется минимум на один минорный релиз после переименования;
- каноническое имя и алиасы должны быть отражены в документации;
- удаление алиаса возможно только после явного периода депрекации.

Текущий alias policy:

- `apidev gen` — canonical command
- `apidev generate` — hidden compatibility alias

## Контракт кодов выхода

- `0` — успешное выполнение;
- `1` — бизнес-ошибка, validation failure, blocking drift (например, `gen --check`), invalid input на уровне домена;
- `2` — ошибка парсинга CLI или неверной сигнатуры команды.

## Контракт machine-readable diagnostics (JSON)

Цель этого контракта — обеспечить единый и предсказуемый формат для CI/automation.
Human-readable вывод остается default-режимом CLI.

### Envelope (верхний уровень)

Machine-readable payload должен быть валидным JSON-объектом с полями:

- `command`: строка, одно из `validate`, `diff`, `gen`;
- `mode`: строка, одно из `apply`, `check`, `preview`, `validate`;
- `summary`: объект агрегатов;
- `diagnostics`: массив diagnostics item;
- `drift_status`: строка `drift | no-drift | error` (для `diff` и `gen`);
- `compatibility`: объект compatibility summary (для `diff` и `gen`);
- `meta`: объект технических метаданных (опционально).

Правило unified compatibility reporting:

- для `diff` и `gen` compatibility diagnostics дублируются в двух местах:
- в top-level `diagnostics` (единый поток для CI parsing);
- в `compatibility.diagnostics` (специализированный compatibility-блок).

Правило preflight failure envelope:

- при `preflight validation failure` команды `diff` и `gen` не переходят к pipeline;
- в режиме JSON (`diff --json` и `gen --json`/`gen --check --json`) возвращается единый envelope с `drift_status = error`, `summary.status = failed` и validation diagnostics;
- в этом сценарии `compatibility` присутствует с пустым `diagnostics` и `overall = non-breaking`.

Минимальный пример:

```json
{
  "command": "gen",
  "mode": "check",
  "drift_status": "drift",
  "summary": {
    "status": "failed",
    "errors": 1,
    "warnings": 0,
    "diagnostics_total": 1
  },
  "diagnostics": [
    {
      "code": "generation.drift-detected",
      "severity": "error",
      "location": "generated-root",
      "message": "Drift detected in check mode",
      "category": "generation",
      "detail": "ADD=1,UPDATE=0,REMOVE=0",
      "source": "generate-service"
    }
  ],
  "compatibility": {
    "policy": "warn",
    "overall": "non-breaking",
    "counts": {
      "non-breaking": 0,
      "potentially-breaking": 0,
      "breaking": 0
    },
    "diagnostics": []
  }
}
```

### Diagnostics item schema

Обязательные поля каждого diagnostics item:

- `code`: строка, стабильный diagnostic identifier;
- `severity`: строка `error | warning | info`;
- `location`: строка, logical location или путь;
- `message`: строка, краткое человеко-читаемое описание.

Опциональные стандартизованные поля:

- `category`: строка (например, `validation`, `compatibility`, `generation`, `runtime`, `config`);
- `detail`: строка с расширенным контекстом;
- `source`: строка источника (`validate-service`, `diff-service`, `generate-service`, `cli`);
- `rule`: строка идентификатора правила (главным образом для schema/semantic validation);
- `hint`: строка с рекомендуемым следующим шагом.

### Таксономия diagnostic codes

Коды должны быть стабильны и принадлежать одному namespace:

- `validation.*` — schema/semantic ошибки контрактов;
- `compatibility.*` — baseline/policy/deprecation классификация;
- `generation.*` — generation/apply/remove/check сценарии;
- `runtime.*` — runtime ошибки pipeline;
- `config.*` — config/release-state ошибки.

### Нормативный каталог fail-fast error codes

Для fail-fast diagnostics в рамках delta-spec `012-integration` код `diagnostics[*].code` должен быть одним из нормативных значений:

- `validation.PATH_BOUNDARY_VIOLATION`
- `validation.OUTPUT_CONTOUR_CONFLICT`
- `validation.INVALID_SCAFFOLD_WRITE_POLICY`
- `validation.MANUAL_TAGS_FORBIDDEN`
- `validation.RELEASE_STATE_INVALID_KEY`
- `validation.RELEASE_STATE_TYPE_MISMATCH`
- `config.INIT_PROFILE_INVALID_ENUM`
- `config.INIT_MODE_CONFLICT`

Перечень выше является контрактно-стабильным для fail-fast сценариев `012-integration`.

Для этих fail-fast сценариев diagnostics item дополнительно должен включать:

- `message`: человеко-читаемое описание причины ошибки;
- `context`: объект релевантных полей ошибки (`field`, `expected_type`, `actual_type`, `generated_dir`, `scaffold_dir`, `project_dir`, `operation_id`) без пустых/отсутствующих значений.

Правило канонической сериализации `context`:

- ключи `context` сериализуются в лексикографическом порядке;
- одинаковые входы должны давать байтово-идентичный JSON envelope.

### Summary schema

`summary` должен содержать:

- `status`: `ok | failed`;
- `errors`: integer >= 0;
- `warnings`: integer >= 0;
- `diagnostics_total`: integer >= 0.

Для `gen` (apply mode) дополнительно может включаться:

- `applied_changes`: integer >= 0.

### Exit code matrix для machine-readable режима

- `validate`: `status=failed` с `errors > 0` -> exit `1`, иначе `0`.
- `diff`: `drift_status=drift` -> exit `0` (preview), `error` -> exit `1`, strict policy gate -> exit `1`.
- `gen --check`: `drift_status=drift|error` -> exit `1`, `no-drift` -> exit `0`.
- `gen` (apply): `error` -> exit `1`, успешное применение/отсутствие drift -> exit `0`.

## Контракт drift-status и exit semantics

Нормализованные drift-статусы:

- `drift` — обнаружены изменения относительно generated artifacts;
- `no-drift` — изменения не обнаружены или успешно применены;
- `error` — ошибка pipeline (включая validation/business failure).

Матрица режимов:

- `apidev diff`
  - `drift` -> exit `0` (read-only preview);
  - `no-drift` -> exit `0`;
  - `error` -> exit `1`.
- `apidev gen --check`
  - `drift` -> exit `1` (CI gate);
  - `no-drift` -> exit `0`;
  - `error` -> exit `1`.
- `apidev gen`
  - successful apply / no changes -> `no-drift`, exit `0`;
  - `error` -> exit `1`.

Правило для remove-only сценариев:

- `remove-only` изменения считаются `drift`;
- для `apidev diff` это informational drift с exit `0` (если не сработал compatibility policy gate);
- для `apidev gen --check` это blocking drift с exit `1`.

## Контракт compatibility policy и baseline

- `--compatibility-policy` поддерживает значения `warn` (по умолчанию) и `strict`.
- В `warn` команда выводит compatibility diagnostics, но не фейлит запуск только из-за policy.
- В `strict` команда завершает выполнение с `exit 1`, если итоговая compatibility-категория `breaking`.
- `--baseline-ref` (git tag/commit) переопределяет `baseline_ref` из release-state.
- Baseline precedence для compare/apply: `CLI --baseline-ref -> release-state.baseline_ref -> git HEAD`.
- При отсутствии baseline или невалидном baseline используются diagnostics `baseline-missing` и `baseline-invalid`.
- При применении baseline выводится diagnostic `baseline-ref-applied` с деталями источника (`cli` или `release-state`).

## Контракт release-state lifecycle в `gen apply`

- `apidev diff` и `apidev gen --check` не пишут release-state (strict read-only).
- `apidev gen` (без `--check`) — единственный CLI-режим, где разрешены create/sync/bump операции release-state.
- Auto-create: если release-state отсутствует, `gen apply` создает его с `release_number=1` и resolved `baseline_ref` (по precedence).
- `fail-without-write`: если baseline не удалось резолвить/валидировать, `gen apply` завершается с `error` (`baseline-missing` или `baseline-invalid`) до release-state записи.
- Bump semantics: `release_number` увеличивается ровно на `1` только при реально примененных drift-изменениях (`ADD|UPDATE|REMOVE`) и только если release-state существовал до запуска apply.
- Если изменений нет, bump не выполняется.
- При ошибке записи release-state команда завершается с `error` и diagnostic `release-state-apply-failed`, а release-state откатывается к pre-run состоянию.

## Контракт deprecation semantics

- APIDev использует lifecycle `active -> deprecated -> removed`.
- Для `diff` и `gen --check` удаление operation до конца grace window классифицируется как `deprecation-window-violation` (breaking).
- Если grace window соблюдено, выводится `deprecation-window-satisfied` (non-breaking).
- Статус deprecation должен быть отражен в generated metadata/artifacts.

## Минимальные тесты для любого CLI-изменения

- тест на root help;
- тест на help хотя бы одной подкоманды;
- тест доступности канонической команды `gen`;
- если затрагивается алиас, тест, что alias ведет к тому же поведению;
- если затрагиваются ошибки, тест на соответствующий exit code и сообщение.

Рекомендуемая команда запуска:

- `uv run pytest tests/unit/test_cli_conventions.py`

## PR checklist для CLI-изменений

- [ ] Обновлены help-описания команд.
- [ ] Поддерживаются `-h` и `--help`.
- [ ] Не сломана команда `apidev gen`.
- [ ] Compatibility alias отражен в документации, если он менялся.
- [ ] Обновлены или добавлены CLI-тесты.

## Связанные документы

- `docs/process/testing-strategy.md`
- `docs/reference/glossary.md`
- `docs/architecture/architecture-overview.md`
- `docs/architecture/generated-integration.md`
