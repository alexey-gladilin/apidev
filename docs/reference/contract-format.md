# Формат Контрактов APIDev

Статус: `Authoritative`

Этот документ задает нормативный формат YAML-контрактов APIDev для аналитиков и разработчиков.
Все требования в этом документе должны выполняться для успешного `apidev validate`.

## Назначение контракта

Контракт описывает один endpoint и используется как вход для:

- валидации (`apidev validate`);
- генерации (`apidev gen`);
- diff-предпросмотра (`apidev diff`).

Один файл контракта = одна операция.

## Канонические форматы контрактов в APIDev

В проекте используются три нормативных формата контрактов:

- API contract: YAML-файл операции в `.apidev/contracts/<domain>/<operation>.yaml` (этот документ).
- Evolution contract: JSON release-state в `.apidev/release-state.json` (раздел ниже).
- CLI diagnostics contract: machine-readable JSON envelope для `validate|diff|gen` в [docs/reference/cli-contract.md](docs/reference/cli-contract.md).

## Размещение файлов

- Базовая директория контрактов: `.apidev/contracts` (или кастомная `contracts.dir` в `.apidev/config.toml`).
- Рекомендуемая структура: `<domain>/<operation>.yaml`.
- Поддерживаемое расширение: `.yaml`.
- `operation_id` вычисляется из относительного пути и должен быть уникален.

Пример:

- `.apidev/contracts/system/health.yaml`
- `.apidev/contracts/billing/create_invoice.yaml`

## Целевая структура generated output

Для контракта `.apidev/contracts/<domain>/<operation>.yaml` команды `apidev diff` и `apidev gen` работают с domain-first структурой generated-зоны:

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

Где `<generated_dir>` — значение `generator.generated_dir` из `.apidev/config.toml` (по умолчанию `.apidev/output/api`).

Пример для `billing/get_invoice.yaml`:

```text
.apidev/output/api/
├── operation_map.py
├── openapi_docs.py
└── billing/
    ├── routes/
    │   └── get_invoice.py
    └── models/
        ├── get_invoice_request.py
        ├── get_invoice_response.py
        └── get_invoice_error.py
```

## Параметры scaffold-интеграции в config

`apidev init` добавляет в `.apidev/config.toml` параметры scaffold-интеграции:

```toml
[generator]
generated_dir = ".apidev/output/api"
postprocess = "auto"
scaffold = true
scaffold_dir = "integration"
scaffold_write_policy = "create-missing"
```

Семантика:

- `generator.scaffold`: `boolean`, включает/выключает генерацию integration scaffold по умолчанию.
- `generator.scaffold_dir`: `string`, относительный путь от `project_dir` для scaffold-файлов.
- Абсолютные пути в `generator.scaffold_dir` запрещены.
- `generator.scaffold_dir` должен оставаться в пределах `project_dir`.
- `generator.generated_dir` и `generator.scaffold_dir` не должны пересекаться (равенство и вложенность запрещены).
- `generator.scaffold_write_policy`: `string`, политика записи scaffold-шаблонов.
  - `create-missing` (default): создавать только отсутствующие scaffold-файлы.
  - `skip-existing`: существующие scaffold-файлы не изменяются, отсутствующие создаются.
  - `fail-on-conflict`: если целевой scaffold-файл уже существует, генерация завершается с ошибкой.
- Недопустимое значение `generator.scaffold_write_policy` приводит к ошибке валидации конфигурации.

## Конфигурация Evolution и release-state

Для compatibility/deprecation policy используется `.apidev/config.toml` (секция `[evolution]`) и release-state файл.

Поля `[evolution]`:

- `compatibility_policy`: `warn | strict` (по умолчанию `warn`).
- `grace_period_releases`: `integer >= 1` (по умолчанию `2`).
- `release_state_file`: путь к release-state JSON (по умолчанию `.apidev/release-state.json`, не пустая строка).

Формат release-state (`.apidev/release-state.json` по умолчанию):

- JSON-объект.
- Обязательные поля:
  - `release_number`: `integer >= 1`.
  - `baseline_ref`: непустая строка (git tag или git commit).
- Опциональные поля:
  - `released_at`: `string`.
  - `git_commit`: `string`.
  - `tag`: `string`.
  - `deprecated_operations`: `object`, где ключ — `operation_id`, значение — `deprecated_since_release_number (integer >= 1)`.

При невалидном `config.toml` или `release-state.json` команда должна возвращать явную ошибку с указанием некорректного поля.

Семантика baseline и policy:

- Источник `baseline_ref` по умолчанию — `release-state.json`.
- CLI override `--baseline-ref` имеет приоритет над `release-state baseline_ref`.
- Для `gen apply` и compare используется единый deterministic precedence: `CLI --baseline-ref -> release-state.baseline_ref -> git HEAD`.
- Compatibility classification в `diff` и `gen --check` выполняется только при валидном baseline snapshot.
- Для невалидного/отсутствующего baseline используются diagnostics `baseline-invalid`/`baseline-missing`.

Семантика lifecycle release-state в `gen apply`:

- Write-owner для release-state только `apidev gen` без `--check`; `diff` и `gen --check` остаются read-only.
- Auto-create: если configured release-state отсутствует, `gen apply` создает JSON `{"release_number": 1, "baseline_ref": <resolved>}` только при успешном resolve baseline по precedence.
- Baseline sync: если release-state существует и `baseline_ref` отличается от resolved baseline, поле `baseline_ref` обновляется на resolved значение.
- `fail-without-write`: если baseline нерезолвим/невалиден (`baseline-missing` или `baseline-invalid`), `gen apply` завершается с ошибкой и не создает/не изменяет release-state.
- Bump semantics: `release_number` увеличивается на `1` только когда в apply действительно были изменения (`ADD|UPDATE|REMOVE`) и release-state существовал до запуска apply.
- No-op semantics: при отсутствии примененных изменений (`SAME`/пустой plan) `release_number` не меняется.
- Ошибка записи release-state после начала apply приводит к `release-state-apply-failed`; pre-run snapshot release-state восстанавливается (включая удаление auto-created файла, если его не было до запуска).

Семантика deprecation lifecycle:

- `deprecated_operations` фиксирует момент депрекации operation в релизах.
- При удалении operation до истечения `grace_period_releases` формируется `deprecation-window-violation` (breaking).
- При удалении после окна формируется `deprecation-window-satisfied` (non-breaking).
- Для operation, отмеченных в `deprecated_operations`, generated metadata/artifacts должны отражать статус `deprecated`; иначе статус `active`.

## Минимальный валидный контракт

```yaml
method: GET
path: /v1/health
auth: public
summary: Health endpoint
description: Returns health status.
response:
  status: 200
  body:
    type: object
    properties:
      status:
        type: string
        required: true
errors:
  - code: INTERNAL_ERROR
    http_status: 500
    body:
      type: object
      properties:
        error_code:
          type: string
          required: true
        message:
          type: string
          required: true
```

## Контракт верхнего уровня

Обязательные поля root-объекта:

- `method`
- `path`
- `auth`
- `summary`
- `description`
- `response`
- `errors`

Неизвестные root-поля запрещены.

### `method`

- Тип: `string`
- Обязательное
- Допустимые значения: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`
- Значение нормализуется в uppercase

### `path`

- Тип: `string`
- Обязательное
- Должно начинаться с `/`
- Не должно быть пустым
- Не должно содержать пробелы

### `auth`

- Тип: `string`
- Обязательное
- Допустимые значения: `public`, `bearer`
- Значение нормализуется в lowercase

### `summary` и `description`

- Тип: `string`
- Обязательные
- Не должны быть пустыми строками

## Блок `response`

Обязательные поля:

- `status`
- `body`

Неизвестные поля запрещены.

### `response.status`

- Тип: `integer`
- Диапазон: `100..599`

### `response.body`

- Тип: `object`
- Должен соответствовать правилам schema-фрагмента (см. раздел ниже)

## Блок `errors`

- Тип: `array`
- Каждый элемент массива должен быть объектом со строго заданными полями:
  - `code`
  - `http_status`
  - `body`

Неизвестные поля в `errors[*]` запрещены.

### `errors[*].code`

- Тип: `string`
- Не пустой
- Формат: `UPPER_SNAKE_CASE` (буквы `A-Z`, цифры, `_`)
- Должен быть уникален в пределах `errors` одного контракта

### `errors[*].http_status`

- Тип: `integer`
- Диапазон: `400..599`

### `errors[*].body`

- Тип: `object`
- Должен соответствовать правилам schema-фрагмента

## Формат schema-фрагмента (`response.body`, `errors[*].body`, вложенные узлы)

Под schema-фрагментом понимается объект, который может встречаться в:

- `response.body`
- `errors[*].body`
- `*.properties.<field>`
- `*.items`

Допустимые поля schema-фрагмента:

- `type`
- `properties`
- `items`
- `required`
- `description`
- `enum`
- `example`

Неизвестные поля запрещены.

### `type`

- Обязательное поле
- Тип: `string`
- Допустимые значения: `object`, `array`, `string`, `integer`, `number`, `boolean`, `null`

### `properties`

- Тип: `object`
- Допустимо только если `type: object`
- Значения `properties.<name>` должны быть schema-фрагментами

### `items`

- Тип: `object`
- Допустимо только если `type: array`
- Значение `items` должно быть schema-фрагментом

### `required` (property-level)

- Тип: `boolean`
- Используется внутри `properties.<name>`
- Определяет обязательность конкретного поля на уровне свойства

### `enum`

- Тип: `array`
- Если задан, не должен быть пустым

### `example`

- Опциональное поле
- Допустимо в schema-фрагментах (`response.body`, `errors[*].body`, `properties.<name>`, `items`)
- Должно быть совместимо с `type` узла
- Если задан `enum`, значение `example` должно входить в `enum`
- Для `object` значение `example` должно быть объектом и рекурсивно соответствовать вложенным правилам
- Для `array` значение `example` должно быть массивом и рекурсивно соответствовать `items`

Пример:

```yaml
response:
  status: 200
  body:
    type: object
    example:
      invoice_id: inv-001
    properties:
      invoice_id:
        type: string
        example: inv-001
```

Root-level блок `examples` в контракте не поддерживается и валидатор трактует его как unknown field.

## Семантические правила (между контрактами)

Проверяются после schema-валидации:

- уникальность `operation_id`;
- уникальность endpoint signature (`method + path`).

Если два контракта описывают одинаковые `method + path`, валидация завершается ошибкой.

## Форматы вывода validate

### Human mode (по умолчанию)

- команда: `apidev validate`
- читабельные сообщения об ошибках
- `exit code 1`, если есть ошибки

### JSON mode

- команда: `apidev validate --json`
- валидный JSON с полями:
  - `diagnostics`: массив диагностик
  - `summary`: агрегированная сводка
- `exit code 1`, если есть ошибки

Минимальная структура одной диагностики:

- `code`
- `severity`
- `message`
- `location`
- `rule`

Нормативный cross-command формат machine-readable diagnostics для всех ключевых CLI-режимов (`validate|diff|gen`) задается в [docs/reference/cli-contract.md](docs/reference/cli-contract.md), раздел `Контракт machine-readable diagnostics (JSON)`.

## Примеры невалидных сценариев

### Неверный метод

```yaml
method: GETоооо
```

Результат: ошибка `SCHEMA_INVALID_VALUE` для `method`.

### Неверный тип в schema-фрагменте

```yaml
response:
  status: 200
  body:
    type: object11
```

Результат: ошибка `SCHEMA_INVALID_VALUE` для `response.body.type`.

### Неизвестное поле

```yaml
x_custom: true
```

Результат: ошибка `SCHEMA_UNKNOWN_FIELD`.

### Неподдерживаемый root-level `examples`

```yaml
examples: []
```

Результат: ошибка `SCHEMA_UNKNOWN_FIELD` для `contract.examples`.

## Диагностические коды (текущий набор)

Schema-level:

- `SCHEMA_INVALID_YAML`
- `SCHEMA_ROOT_NOT_MAPPING`
- `SCHEMA_MISSING_FIELD`
- `SCHEMA_INVALID_TYPE`
- `SCHEMA_INVALID_VALUE`
- `SCHEMA_UNKNOWN_FIELD`

Semantic-level:

- `SEMANTIC_DUPLICATE_OPERATION_ID`
- `SEMANTIC_DUPLICATE_ENDPOINT_SIGNATURE`

## Практический чеклист перед PR

- контракт лежит в корректной директории;
- root-поля заполнены и не содержат неизвестных ключей;
- `method/auth/path/status` соответствуют допустимым значениям;
- `response.body` и `errors[*].body` имеют корректные schema-фрагменты;
- `errors[*].code` уникальны и в формате `UPPER_SNAKE_CASE`;
- `apidev validate` проходит в human и `--json` режимах.

## Связанные документы

- `docs/reference/cli-contract.md`
- `docs/reference/glossary.md`
- `docs/process/testing-strategy.md`
