# Migration Guide: вынос reusable shared models

## Назначение

Этот гайд описывает пошаговую миграцию от inline-дублирования schema-фрагментов к shared model contracts.
Целевая аудитория:

- аналитики, которые сопровождают контрактную модель API;
- backend-команды, которые поддерживают endpoint-контракты и валидацию.

Гайд покрывает task `2.2` для change `014-shared-contract-models` и использует правила из `docs/reference/contract-format.md`.

## Когда модель нужно выносить в shared

Вынос в `.apidev/models/<namespace>/<model>.yaml` рекомендуется, если выполняется хотя бы одно условие:

- один и тот же объект повторяется в двух и более operation contracts;
- изменение shape должно происходить синхронно для нескольких операций;
- модель является доменной сущностью (`PaginationRequest`, `SortDescriptor`, `PageInfo`, `Money`, `DateRange`).

Оставляйте модель в `local_models`, если она используется только внутри одной операции и не планируется к reuse.

## Единый pipeline миграции (аналитик + backend)

### Шаг 1. Найти кандидатов на вынос

1. Сформируйте список повторяющихся блоков в `.apidev/contracts/**`:
   - пагинация (`page`, `size`);
   - сортировка (`field`, `direction`);
   - page-info в response.
2. Зафиксируйте, в каких операциях блок повторяется и где различается.

Артефакт шага: таблица `модель -> операции-потребители`.

### Шаг 2. Согласовать canonical shape и namespace

1. Выберите namespace по доменной ответственности (`common`, `billing`, `users`).
2. Зафиксируйте canonical имя модели в PascalCase (`PaginationRequest`, `SortDescriptor`).
3. Согласуйте обязательность полей (`required`) и ограничения (`minimum`, `enum`, `maximum`).

Артефакт шага: согласованный контракт shared-модели без operation-специфичных полей.

### Шаг 3. Создать shared model contract

Создайте файл `.apidev/models/<namespace>/<model>.yaml`.

Минимальный шаблон:

```yaml
contract_type: shared_model
name: PaginationRequest
description: Used by paginated list operations
model:
  type: object
  properties:
    page:
      type: integer
      minimum: 1
      required: true
    size:
      type: integer
      minimum: 1
      maximum: 500
      required: true
```

Проверки шага:

- файл расположен в `.apidev/models`;
- `contract_type: shared_model` задан явно;
- отсутствуют поля operation-контракта (`method`, `path`, `request`, `response`, `errors`).

### Шаг 4. Заменить inline-блоки на ссылки

В operation contracts замените дублирующийся inline shape на `$ref`.

```yaml
request:
  body:
    type: object
    properties:
      pagination:
        $ref: common.PaginationRequest
```

Допустимы:

- fully-qualified ref: `$ref: common.PaginationRequest`;
- shorthand в edge/scalar-позициях: `$users.UserSummary`.

Недопустимо:

- смешивать `$ref` и inline-shape в одном узле;
- ссылаться из shared model на `local_models`.

Явная проверка reference-узлов:

- валидно: узел содержит только `$ref`;
- невалидно: в том же узле вместе с `$ref` заданы `type`, `properties`, `items`, `required`, `description`, `enum`, `example`.

### Шаг 5. Провести проверку совместимости

1. Убедитесь, что после замены ссылок API-семантика не изменилась.
2. Запустите валидацию:

```bash
apidev validate
```

`openspec validate 014-shared-contract-models --strict --no-interactive` используйте только для проверки spec-change артефактов OpenSpec.

3. Исправьте диагностические ошибки по категориям:
   - missing ref;
   - scope leak (`shared` -> `local`);
   - contract_type/location mismatch;
   - cycles/ambiguous refs.

### Шаг 6. Зафиксировать rollout-стратегию

1. Мигрируйте сначала самые повторяемые модели (`PaginationRequest`, `SortDescriptor`).
2. Затем переведите response-метаданные (`PageInfo`) и менее частые value objects.
3. Для крупных доменов выполняйте миграцию по батчам (по namespace), чтобы упростить review.

## Чек-лист для аналитика

- [ ] Для каждой вынесенной модели описано доменное назначение (`description`).
- [ ] Namespace и имя модели согласованы и не конфликтуют с существующими ключами.
- [ ] Во всех операциях-потребителях удален дублирующий inline-shape.
- [ ] Границы `shared` vs `local_models` задокументированы в change notes.

## Чек-лист для backend-команды

- [ ] Все новые shared files лежат в `.apidev/models/**`.
- [ ] Все operation contracts остались в `.apidev/contracts/**`.
- [ ] В референс-узлах не смешаны `$ref` и inline-поля.
- [ ] `apidev validate` проходит без ошибок для контрактов.
- [ ] `openspec validate 014-shared-contract-models --strict --no-interactive` (при необходимости) проходит для spec-change артефактов.

## Типовые ошибки миграции

- Shared model создается в `.apidev/contracts` вместо `.apidev/models`.
- В shared model добавляют operation-атрибуты (`method`, `path`).
- Модель фактически operation-local, но вынесена в shared преждевременно.
- Используется short-name ref без учета неоднозначности имен между namespace.

## Example 1: Pagination

### Before

`billing/list_invoices.yaml`

```yaml
method: POST
path: /v1/invoices/search
auth: bearer
description: Returns paginated invoices
request:
  body:
    type: object
    properties:
      pagination:
        type: object
        required: false
        properties:
          page:
            type: integer
            minimum: 1
            required: true
          size:
            type: integer
            minimum: 1
            maximum: 500
            required: true
response:
  status: 200
  body:
    type: object
errors: []
```

`users/list_users.yaml`

```yaml
method: POST
path: /v1/users/search
auth: bearer
description: Returns paginated users
request:
  body:
    type: object
    properties:
      pagination:
        type: object
        required: false
        properties:
          page:
            type: integer
            minimum: 1
            required: true
          size:
            type: integer
            minimum: 1
            maximum: 500
            required: true
response:
  status: 200
  body:
    type: object
errors: []
```

### After

`.apidev/models/common/pagination_request.yaml`

```yaml
contract_type: shared_model
name: PaginationRequest
description: Used by paginated list operations
model:
  type: object
  properties:
    page:
      type: integer
      minimum: 1
      required: true
    size:
      type: integer
      minimum: 1
      maximum: 500
      required: true
```

`billing/list_invoices.yaml`

```yaml
contract_type: operation
method: POST
path: /v1/invoices/search
auth: bearer
description: Returns paginated invoices
request:
  body:
    type: object
    properties:
      pagination:
        $ref: common.PaginationRequest
response:
  status: 200
  body:
    type: object
errors: []
```

`users/list_users.yaml`

```yaml
contract_type: operation
method: POST
path: /v1/users/search
auth: bearer
description: Returns paginated users
request:
  body:
    type: object
    properties:
      pagination:
        $ref: common.PaginationRequest
response:
  status: 200
  body:
    type: object
errors: []
```

## Example 2: Sort Descriptor

### Before

```yaml
request:
  body:
    type: object
    properties:
      sort:
        type: object
        required: false
        properties:
          field:
            type: string
            required: true
          direction:
            type: string
            enum: [asc, desc]
            required: true
```

### After

`.apidev/models/common/sort_descriptor.yaml`

```yaml
contract_type: shared_model
name: SortDescriptor
description: Used by search and list operations
model:
  type: object
  properties:
    field:
      type: string
      required: true
    direction:
      type: string
      enum: [asc, desc]
      required: true
```

Operation contract excerpt:

```yaml
request:
  body:
    type: object
    properties:
      sort:
        $ref: common.SortDescriptor
```

## Example 3: Page Info In Response

### Before

```yaml
response:
  status: 200
  body:
    type: object
    properties:
      pageInfo:
        type: object
        properties:
          page:
            type: integer
            required: true
          size:
            type: integer
            required: true
          total:
            type: integer
            required: true
```

### After

`.apidev/models/common/page_info.yaml`

```yaml
contract_type: shared_model
name: PageInfo
description: Paging metadata for list responses
model:
  type: object
  properties:
    page:
      type: integer
      required: true
    size:
      type: integer
      required: true
    total:
      type: integer
      required: true
```

Operation contract excerpt:

```yaml
response:
  status: 200
  body:
    type: object
    properties:
      pageInfo:
        $ref: common.PageInfo
```

## Критерии завершения миграции

Миграция по домену считается завершенной, если:

- все согласованные reusable-модели вынесены в `.apidev/models/**`;
- в operation contracts удалено дублирование inline-деревьев для этих моделей;
- ссылки разрешаются детерминированно и проходят validate;
- команда может объяснить, почему оставшиеся `local_models` не вынесены в shared.
