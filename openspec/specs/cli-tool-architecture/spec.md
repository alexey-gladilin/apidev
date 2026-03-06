# cli-tool-architecture Specification

## Purpose
TBD - created by archiving change 000-apidev-cli-tool-architecture. Update Purpose after archive.
## Requirements
### Requirement: Binary CLI Packaging
`apidev` SHALL be packaged as an installable CLI binary that can run inside external target projects.

#### Scenario: CLI entrypoint is available after install
- **WHEN** a user installs `apidev`
- **THEN** command `apidev` SHALL be available in PATH
- **AND** command execution SHALL start in `apidev.cli` entrypoint

### Requirement: Layered Internal Architecture for CLI Tool
The codebase SHALL separate CLI adapters, application services, core rules/models, and infrastructure adapters.

#### Scenario: Command delegates to application service
- **WHEN** user runs any supported CLI command
- **THEN** command module SHALL parse flags and delegate business workflow to application service layer
- **AND** core models/rules SHALL remain independent from CLI framework details

### Requirement: MVP Command Surface

CLI SHALL предоставлять минимальные команды для инициализации workspace, валидации контрактов, preview изменений и применения deterministic generation, а также единообразный machine-readable diagnostics contract для `validate`, `diff`, `gen --check`, `gen` при сохранении существующего plain-text UX.

#### Scenario: Init creates tool workspace

- **WHEN** пользователь запускает `apidev init` в целевом проекте
- **THEN** tool SHALL создавать `.apidev/config.toml`, `.apidev/contracts/` и `.apidev/templates/` при их отсутствии

#### Scenario: Validate reports diagnostics without writing output

- **WHEN** пользователь запускает `apidev validate`
- **THEN** tool SHALL парсить все контракты и публиковать diagnostics
- **AND** tool SHALL не записывать generated source files

#### Scenario: Diff previews planned changes

- **WHEN** пользователь запускает `apidev diff`
- **THEN** tool SHALL вычислять детерминированный generation plan
- **AND** tool SHALL публиковать file-level add/update/remove preview без записи файлов

#### Scenario: Generate applies deterministic output

- **WHEN** пользователь запускает `apidev gen`
- **THEN** tool SHALL записывать файлы согласно вычисленному плану
- **AND** повторный запуск с неизменными входами SHALL не создавать дополнительных content changes

#### Scenario: Все ключевые команды публикуют единый diagnostics envelope

- **WHEN** пользователь запускает `apidev validate`, `apidev diff`, `apidev gen --check` или `apidev gen` в machine-readable режиме
- **THEN** команда SHALL возвращать единый JSON envelope c полями верхнего уровня `command`, `summary`, `diagnostics`
- **AND** `drift_status` SHALL присутствовать для `diff`/`gen --check`/`gen`, а `compatibility` SHALL присутствовать для `diff`/`gen --check`/`gen`

#### Scenario: Базовые поля diagnostics стабилизированы для CI

- **WHEN** любая команда публикует diagnostics item
- **THEN** item SHALL содержать обязательные поля `code`, `severity`, `location`, `message`
- **AND** item MAY содержать опциональные стандартизированные поля `category`, `detail`, `source`, `rule`, `hint`

#### Scenario: Таксономия diagnostics codes унифицирована

- **WHEN** система эмитит diagnostic code
- **THEN** code SHALL принадлежать одному из namespace: `validation.`*, `compatibility.*`, `generation.*`, `runtime.*`, `config.*`
- **AND** код SHALL оставаться детерминированным для одинакового входа и одинакового failure mode

#### Scenario: Drift и policy семантика не меняется при hardening diagnostics

- **WHEN** пользователь запускает `apidev diff`, `apidev gen --check`, `apidev gen` после внедрения unified diagnostics contract
- **THEN** drift-status/exit code SHALL сохранять действующую матрицу поведения
- **AND** compatibility policy gate (`warn|strict`) SHALL сохранять текущую blocking семантику

#### Scenario: Plain-text UX остается совместимым

- **WHEN** пользователь запускает команды без machine-readable флага
- **THEN** CLI SHALL выводить человеко-читаемые diagnostics и статусные сообщения
- **AND** формат вывода SHALL оставаться пригодным для ручного triage без обязательного JSON parsing

### Requirement: Safe Write Boundaries in Target Projects
Граница записи SHALL использовать двухконтурную модель output-каталогов (`generated_dir` и `scaffold_dir`) внутри `project_dir`.

Примечание supersede:
- Эта норма уточняет и supersede-ит historical fallback-формулировку про единственный generated root.
- Для `012-integration` source of truth по boundary-контракту: `generated_dir` и `scaffold_dir` как независимые output-контуры с единым path-boundary контролем внутри `project_dir`.

#### Scenario: Write attempt outside project_dir boundaries
- **WHEN** план генерации включает путь вне `project_dir` для `generated_dir` или `scaffold_dir`
- **THEN** генерация SHALL завершаться fail-fast policy error
- **AND** tool SHALL не записывать out-of-policy файлы

#### Scenario: Output contour conflict is forbidden
- **WHEN** `generated_dir` и `scaffold_dir` совпадают или один является подкаталогом другого
- **THEN** `apidev` SHALL завершаться fail-fast validation error до файловых операций
- **AND** diagnostics SHALL включать оба исходных пути и правило запрета пересечения output-контуров

### Requirement: Endpoint Include/Exclude Selection for Code Generation
`apidev gen` SHALL поддерживать выборочную генерацию endpoint-ов через CLI-фильтры include/exclude без нарушения детерминированности generation pipeline.

#### Scenario: Pattern grammar и matching policy детерминированы
- **WHEN** пользователь передает `--include-endpoint <pattern>` или `--exclude-endpoint <pattern>`
- **THEN** `pattern` SHALL интерпретироваться как case-sensitive glob-expression над строками `operation_id` и `contract_relpath`
- **AND** endpoint SHALL считаться matching, если pattern совпал хотя бы с одним из двух идентификаторов (`operation_id OR contract_relpath`)
- **AND** пустая строка pattern SHALL считаться невалидной
- **AND** syntactically malformed glob pattern (например, незакрытый `[` в character-class) SHALL считаться невалидной

#### Scenario: Include-фильтр ограничивает набор endpoint-ов
- **WHEN** пользователь запускает `apidev gen` с одним или несколькими `--include-endpoint <pattern>`
- **THEN** generation SHALL строить план только для endpoint-ов, matching include-pattern набору
- **AND** endpoint-ы вне include-набора SHALL не попадать в effective generation set

#### Scenario: Exclude-фильтр применяется после include
- **WHEN** пользователь запускает `apidev gen` одновременно с `--include-endpoint` и `--exclude-endpoint`
- **THEN** effective endpoint set SHALL рассчитываться по правилу `include -> exclude`
- **AND** endpoint-ы, matching exclude-pattern, SHALL исключаться из итогового набора даже если были включены include-pattern

#### Scenario: Невалидный pattern вызывает fail-fast diagnostics
- **WHEN** пользователь передает синтаксически невалидный pattern в `--include-endpoint` или `--exclude-endpoint`
- **THEN** команда SHALL завершаться с ошибкой
- **AND** diagnostics SHALL содержать детерминированный `code`/`location`/`detail`, позволяющие машинную проверку
- **AND** diagnostics code SHALL принадлежать namespace `generation.*`

#### Scenario: Пустой effective set после фильтрации
- **WHEN** после применения include/exclude фильтров не остается ни одного endpoint-а
- **THEN** `apidev gen` SHALL завершаться с ошибкой валидации фильтра
- **AND** команда SHALL не выполнять apply-запись generated artifacts
- **AND** diagnostics code SHALL принадлежать namespace `generation.*`

#### Scenario: Remove semantics ограничена выбранным endpoint scope
- **WHEN** пользователь запускает `apidev gen` с include/exclude фильтрами
- **THEN** stale-remove SHALL применяться только к generated artifacts, соответствующим effective endpoint set
- **AND** artifacts вне effective endpoint set SHALL не помечаться на удаление только из-за отсутствия endpoint-а в фильтрованном запуске
- **AND** safety boundary удаления SHALL оставаться неизменной относительно базового `apidev gen` контракта

#### Scenario: Backward compatibility без фильтров
- **WHEN** пользователь запускает `apidev gen` без `--include-endpoint` и `--exclude-endpoint`
- **THEN** команда SHALL использовать полный набор endpoint-контрактов как и до изменения
- **AND** повторные запуски на неизменном входе SHALL сохранять byte-stable output

### Requirement: Integration-Oriented Generation and Runtime Projection
`apidev` SHALL предоставлять интеграционный контракт генерации и runtime-projection, позволяющий безопасно разделять generated/scaffold outputs и автоматически проецировать operation metadata в runtime/OpenAPI.

#### Scenario: Независимый `scaffold_dir` в пределах project-root
- **WHEN** пользователь задает `generator.scaffold_dir` отдельно от `generator.generated_dir`
- **THEN** `apidev` SHALL разрешать независимые каталоги вывода
- **AND** обе директории SHALL проходить общий path-boundary контроль внутри `project_dir`
- **AND** выход за границы `project_dir` SHALL завершаться fail-fast диагностикой

#### Scenario: Недопустимое пересечение output-контуров
- **WHEN** `generator.generated_dir` и `generator.scaffold_dir` совпадают или один путь вложен в другой
- **THEN** `apidev` SHALL завершаться fail-fast validation error до записи файлов
- **AND** diagnostics SHALL содержать исходные пути и правило о запрете пересечения output-контуров

#### Scenario: Управляемая scaffold write policy
- **WHEN** пользователь задает `generator.scaffold_write_policy`
- **THEN** `apidev` SHALL поддерживать только значения `create-missing`, `skip-existing`, `fail-on-conflict`
- **AND** поведение записи scaffold SHALL быть детерминированным и соответствовать выбранной policy
- **AND** неверное значение policy SHALL завершаться ошибкой валидации

#### Scenario: Значение scaffold write policy по умолчанию
- **WHEN** пользователь не задает `generator.scaffold_write_policy`
- **THEN** `apidev` SHALL использовать значение `create-missing` по умолчанию
- **AND** поведение без новых опций SHALL сохранять текущую семантику scaffold-записи

#### Scenario: Runtime/OpenAPI adapter из operation metadata
- **WHEN** выполняется генерация integration-слоя
- **THEN** runtime adapter SHALL формировать маршруты на основе operation metadata
- **AND** adapter SHALL проецировать `operation_id`, summary, description, deprecated, auth и error/success responses в runtime/OpenAPI contract
- **AND** Swagger tags SHALL вычисляться автоматически из домена операции (domain-based grouping)
- **AND** порядок проекции SHALL оставаться детерминированным между повторными запусками на одинаковом входе

#### Scenario: Runtime adapter реализует референсный integration-контракт
- **WHEN** реализуется runtime wiring для FastAPI integration-layer
- **THEN** generated adapter SHALL соответствовать reference-контракту из `artifacts/design/05-integration-reference.md`
- **AND** endpoint registration SHALL использовать `APIRouter.add_api_route(...)` с пробросом `operation_id`, `responses`, domain-derived `tags`, auth-dependencies и operation metadata
- **AND** добавление нового endpoint в `operation_map` SHALL подключаться автоматически без ручного редактирования router definition
- **AND** для нового endpoint ручная работа SHALL ограничиваться handler-реализацией и mapping-конфигурацией

#### Scenario: Доменная группировка Swagger без ручного `tags`
- **WHEN** metadata операции не содержит ручного `tags`
- **THEN** Swagger tag SHALL определяться по домену операции, полученному из структуры operation map / domain layout
- **AND** generated OpenAPI SHALL оставаться детерминированным между повторными запусками

#### Scenario: Ручной `tags` в metadata операции
- **WHEN** metadata операции содержит пользовательское поле `tags`
- **THEN** генерация SHALL завершаться validation error (fail-fast)
- **AND** diagnostics SHALL указывать operation id и правило, что доменная группировка Swagger формируется автоматически

#### Scenario: Поддержка short-form `errors[].example`
- **WHEN** контракт использует `errors[].example`
- **THEN** `apidev validate` SHALL принимать этот синтаксис
- **AND** значение SHALL нормализоваться в каноническую error-example модель
- **AND** OpenAPI projection SHALL публиковать примеры ошибок в детерминированной форме

#### Scenario: Одновременное использование short-form и nested-form error example
- **WHEN** в одном error-item заданы и `errors[].example`, и nested-form example
- **THEN** при эквивалентных значениях `apidev` SHALL считать запись валидной и использовать каноническую nested-модель
- **AND** при конфликтующих значениях `apidev` SHALL завершаться fail-fast validation error с явной диагностикой

#### Scenario: Strict validation release-state формата и типа
- **WHEN** release-state содержит legacy ключ (`current_release`) или `release_number` неверного типа
- **THEN** `apidev` SHALL завершаться ошибкой валидации
- **AND** diagnostics SHALL содержать явное указание на проблемный ключ и ожидаемый тип
- **AND** автоматическая миграция или fallback SHALL не выполняться

#### Scenario: Integration profile для `apidev init`
- **WHEN** пользователь запускает `apidev init` с `--runtime`, `--integration-mode`, `--integration-dir`
- **THEN** init SHALL управлять только profile-managed integration templates в init-managed scope
- **AND** поведение в режимах `--repair` и `--force` SHALL быть детерминированным и документированным

#### Scenario: Допустимые значения integration profile-флагов
- **WHEN** пользователь задает `--runtime` и `--integration-mode`
- **THEN** `--runtime` SHALL принимать только `fastapi` или `none`
- **AND** `--integration-mode` SHALL принимать только `off`, `scaffold` или `full`
- **AND** недопустимое значение любого из флагов SHALL завершаться CLI validation error

#### Scenario: Precedence profile-флагов и режимов init
- **WHEN** пользователь запускает `apidev init` с profile-флагами и одним из режимов `create|repair|force`
- **THEN** profile-флаги SHALL управлять только integration-артефактами в рамках выбранного режима
- **AND** `--repair` и `--force` SHALL оставаться взаимоисключающими
- **AND** правила precedence SHALL быть задокументированы и детерминированы для повторных запусков

#### Scenario: Документированная матрица precedence
- **WHEN** описывается поведение `apidev init` для profile-флагов
- **THEN** documentation SHALL содержать явную matrix для `create|repair|force` x profile-условий (`runtime`, `integration-mode`, `integration-dir`)
- **AND** matrix SHALL фиксировать, что именно создается/обновляется в profile-managed template scope и какие комбинации завершаются validation error

#### Scenario: Документированная file-scope матрица profile-managed artifacts
- **WHEN** описываются profile-managed integration templates для `apidev init`
- **THEN** documentation SHALL содержать matrix `integration-mode` x `runtime` c явным перечнем managed templates
- **AND** matrix SHALL фиксировать forbidden mutations вне profile-scope и запрет runtime wiring для `runtime=none`

#### Scenario: Запрещенная комбинация `integration-mode=full` и `runtime=none`
- **WHEN** пользователь задает `--integration-mode full` и `--runtime none`
- **THEN** `apidev init` SHALL завершаться fail-fast validation error до файловых операций
- **AND** diagnostics SHALL использовать стабильный `code = config.INIT_MODE_CONFLICT`

#### Scenario: Невалидные enum-значения init profile-флагов
- **WHEN** пользователь передает недопустимое значение в `--runtime` или `--integration-mode`
- **THEN** `apidev init` SHALL завершаться fail-fast validation error до файловых операций
- **AND** diagnostics SHALL использовать стабильный `code = config.INIT_PROFILE_INVALID_ENUM`

#### Scenario: Управление OpenAPI extensions
- **WHEN** пользователь задает `openapi.include_extensions = false`
- **THEN** итоговый OpenAPI SHALL исключать `x-apidev-*` extensions
- **AND** базовые OpenAPI поля SHALL оставаться неизменными
- **AND** значение по умолчанию SHALL сохранять прежнее поведение

#### Scenario: Стабильный diagnostics envelope для fail-fast
- **WHEN** возникает fail-fast validation error на path-boundary, metadata или type-mismatch
- **THEN** diagnostics SHALL включать `code`, `message` и структурированный `context`
- **AND** `context` SHALL содержать релевантные поля (`operation_id`, `field`, `expected_type`, `actual_type`, `generated_dir`, `scaffold_dir`, `project_dir`) в зависимости от типа ошибки

#### Scenario: Нормативные fail-fast error codes
- **WHEN** формируется fail-fast diagnostics
- **THEN** `code` SHALL быть одним из нормативных значений:
  - `validation.PATH_BOUNDARY_VIOLATION`
  - `validation.OUTPUT_CONTOUR_CONFLICT`
  - `validation.INVALID_SCAFFOLD_WRITE_POLICY`
  - `validation.MANUAL_TAGS_FORBIDDEN`
  - `validation.RELEASE_STATE_INVALID_KEY`
  - `validation.RELEASE_STATE_TYPE_MISMATCH`
  - `config.INIT_PROFILE_INVALID_ENUM`
  - `config.INIT_MODE_CONFLICT`
- **AND** перечисленные `code` SHALL оставаться стабильными в рамках этого change

#### Scenario: Каноническая сериализация diagnostics envelope
- **WHEN** `apidev` публикует diagnostics envelope
- **THEN** `code` SHALL быть машинно-стабильным, а `message` SHALL оставаться человекочитаемым
- **AND** `context` SHALL сериализоваться с лексикографическим порядком ключей без вывода отсутствующих полей
- **AND** одинаковые входы SHALL давать байтово-идентичный diagnostics envelope

### Requirement: Contract-Level Request Model

`apidev` SHALL поддерживать schema-driven описание request в YAML-контракте через root-блок `request`.

#### Scenario: Root-контракт включает `request`

- **WHEN** контракт содержит блок `request`
- **THEN** `apidev validate` SHALL рассматривать его как нормативный root-поле
- **AND** блок SHALL поддерживать только разрешенную структуру request-контракта

#### Scenario: `request` отсутствует для операций без входных параметров

- **WHEN** операция любого HTTP-метода не требует path/query/body входных данных
- **THEN** отсутствие root-блока `request` SHALL считаться валидным
- **AND** generated OpenAPI SHALL не добавлять `parameters` и `requestBody`

#### Scenario: Unknown поля в `request`

- **WHEN** в `request` или его подблоках присутствуют неизвестные поля
- **THEN** `apidev validate` SHALL завершаться ошибкой schema-валидации
- **AND** diagnostics SHALL указывать точный путь до невалидного поля

### Requirement: Request Schema Fragment Dialect

`apidev` SHALL использовать единый schema dialect для `request.path`, `request.query`, `request.body`, согласованный с уже существующим dialect для `response.body`/`errors[*].body`.

#### Scenario: Допустимая структура request schema fragment

- **WHEN** контракт содержит `request.path`, `request.query` или `request.body`
- **THEN** каждый из этих узлов SHALL быть валидным schema fragment с поддержкой только нормативных ключей (`type`, `properties`, `items`, `required`, `example`)
- **AND** для object-узлов `type: object` SHALL быть обязательным при наличии `properties`
- **AND** значения в `properties.<field>` SHALL быть schema fragments того же dialect

#### Scenario: Невалидный request schema fragment

- **WHEN** в `request.path`, `request.query`, `request.body` или вложенных узлах встречаются неразрешенные ключи, отсутствует обязательный `type`, либо нарушены правила `properties/items/required`
- **THEN** `apidev validate` SHALL завершаться fail-fast schema error
- **AND** diagnostics SHALL содержать стабильный path до невалидного поля

### Requirement: Request Path Parameters Support

`apidev` SHALL поддерживать декларативное описание path parameters и согласованность с HTTP path-шаблоном.

#### Scenario: Path params описаны и соответствуют шаблону пути

- **WHEN** путь контракта содержит placeholder-параметры в формате `{param}`
- **AND** `request.path` описывает те же параметры
- **THEN** контракт SHALL считаться валидным
- **AND** generated OpenAPI SHALL содержать соответствующие `in: path` parameters

#### Scenario: Path params не согласованы с path-шаблоном

- **WHEN** в `request.path` отсутствует параметр из path-шаблона или указан лишний параметр
- **THEN** `apidev validate` SHALL завершаться fail-fast validation error

#### Scenario: Placeholder-путь без `request.path`

- **WHEN** `path` содержит хотя бы один placeholder `{param}`, а `request.path` не задан
- **THEN** `apidev validate` SHALL завершаться fail-fast validation error
- **AND** неявный auto-infer path-params SHALL не выполняться

#### Scenario: Edge-case правила path placeholders

- **WHEN** выполняется сравнение `{param}` из `path` и полей `request.path`
- **THEN** сопоставление имен SHALL быть case-sensitive и выполняться по точному имени без нормализации
- **AND** дубли placeholder-имен в `path` SHALL считаться невалидным контрактом

### Requirement: Request Query Parameters Support

`apidev` SHALL поддерживать декларативное описание query parameters.

#### Scenario: Query params описаны в `request.query`

- **WHEN** контракт содержит `request.query`
- **THEN** generated OpenAPI SHALL проецировать эти параметры в `parameters` с `in: query`
- **AND** generated request-model metadata SHALL включать query schema fragment

#### Scenario: Query params отсутствуют

- **WHEN** операция не требует query-параметров
- **THEN** отсутствие `request.query` SHALL считаться валидным
- **AND** generated OpenAPI SHALL не добавлять лишние query parameters

### Requirement: Request Body Support

`apidev` SHALL поддерживать декларативное описание request body.

#### Scenario: Body описан в `request.body`

- **WHEN** контракт содержит `request.body` schema fragment
- **THEN** generated OpenAPI SHALL содержать `requestBody` для операции
- **AND** generated request-model SHALL использовать schema fragment из `request.body`

#### Scenario: Body отсутствует для body-less операций

- **WHEN** операция не предполагает request body
- **THEN** отсутствие `request.body` SHALL считаться валидным
- **AND** generated OpenAPI SHALL не добавлять `requestBody`

### Requirement: Request Metadata In Operation Map

`apidev` SHALL публиковать request metadata в generated `operation_map`.

#### Scenario: Operation map содержит request metadata

- **WHEN** выполнен `apidev gen`
- **THEN** `operation_map` SHALL включать request metadata (path/query/body schema fragments)
- **AND** эти данные SHALL использоваться генераторами transport/OpenAPI без дополнительных эвристик

### Requirement: Legacy Contract Backward Compatibility

`apidev` SHALL сохранять обратную совместимость для валидных legacy-контрактов, не содержащих root-блок `request`.

#### Scenario: Legacy контракт без `request`

- **WHEN** контракт не содержит `request`, валиден по историческим правилам `method/path/auth/summary/description/response/errors` и не содержит placeholder-параметров в `path`
- **THEN** `apidev validate` SHALL принимать такой контракт без migration-переходника
- **AND** generated OpenAPI SHALL не добавлять `parameters`/`requestBody`, если они не заданы контрактом

### Requirement: Request Validation Diagnostics Contract

Request-related fail-fast валидация SHALL публиковать стабильные machine-readable diagnostics codes в namespace `validation.*`.

#### Scenario: Request validation emits stable diagnostics codes

- **WHEN** `apidev validate` обнаруживает request-related ошибку (`unknown-field`, `schema-invalid`, `path-mismatch`, `missing-request-path`, `duplicate-path-placeholder`)
- **THEN** diagnostics item SHALL содержать обязательные поля `code`, `severity`, `location`, `message`
- **AND** `code` SHALL принадлежать namespace `validation.*` и оставаться детерминированным для одинакового failure mode

### Requirement: Request-Aware OpenAPI Projection

Generated OpenAPI projection SHALL строиться из полной контрактной модели операции (request + response + errors).

#### Scenario: OpenAPI projection включает request и response

- **WHEN** контракт валиден и содержит request/response блоки
- **THEN** generated OpenAPI SHALL включать:
  - `parameters` для path/query
  - `requestBody` для body
  - `responses` для success/error
- **AND** проекция SHALL оставаться детерминированной между повторными запусками

