# CLI Контракт APIDev

Статус: `Authoritative`

Этот документ задает проверяемый контракт CLI и используется как единый источник истины для PR review, тестов и изменений help/UX.

## Канонические команды

Набор верхнего уровня:

- `apidev init`
- `apidev validate`
- `apidev diff`
- `apidev gen`

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

Матрица profile scope:

- `--integration-mode off`: integration templates не bootstrap-ятся;
- `--integration-mode scaffold --runtime none`: только `integration_handler_registry.py.j2` и `integration_error_mapper.py.j2`;
- `--integration-mode scaffold --runtime fastapi`: `integration_handler_registry.py.j2`, `integration_router_factory.py.j2`, `integration_auth_registry.py.j2`, `integration_error_mapper.py.j2`;
- `--integration-mode full --runtime fastapi`: scaffold-набор + `generated_operation_map.py.j2`, `generated_openapi_docs.py.j2`, `generated_router.py.j2`, `generated_schema.py.j2`;
- `--integration-mode full --runtime none` невалиден (`config.INIT_MODE_CONFLICT`).

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
- scaffold-файлы создаются только в режиме `create-if-missing` (существующие не перезаписываются).

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

## Контракт help и UX

Обязательные требования:

- каждый уровень команды поддерживает `-h` и `--help`;
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
