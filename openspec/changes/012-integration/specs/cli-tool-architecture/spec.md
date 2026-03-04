## ADDED Requirements

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
- **THEN** init SHALL создавать/обновлять integration-artifacts согласно выбранному профилю
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
- **THEN** documentation SHALL содержать явную matrix для `create|repair|force` x `integration-mode`
- **AND** matrix SHALL фиксировать, что именно создается/обновляется и какие комбинации завершаются validation error

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
