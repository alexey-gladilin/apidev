# Draft Patch For `apidev/docs/reference/contract-format.md`

Ниже приведен готовый черновик разделов, которые следует добавить или адаптировать в `apidev/docs/reference/contract-format.md`.

## 1. Обновить раздел `Канонические форматы контрактов в APIDev`

Заменить список из одного YAML-вида на два YAML-вида:

```md
В проекте используются четыре нормативных формата контрактов:

- API operation contract: YAML-файл операции в `.apidev/contracts/<domain>/<operation>.yaml`.
- Shared model contract: YAML-файл переиспользуемой модели в `.apidev/models/<namespace>/<model>.yaml`.
- Evolution contract: JSON release-state в `.apidev/release-state.json`.
- CLI diagnostics contract: machine-readable JSON envelope для `validate|diff|gen` в `cli-contract.md`.
```

## 2. Добавить раздел `Виды YAML-контрактов`

```md
## Виды YAML-контрактов

В APIDev поддерживаются два вида YAML-контрактов:

### API operation contract
- расположение: `.apidev/contracts/<domain>/<operation>.yaml`
- описывает ровно одну API-операцию;
- `contract_type: operation` рекомендуется, но в transition mode может отсутствовать для backward compatibility.

### Shared model contract
- расположение: `.apidev/models/<namespace>/<model>.yaml`
- описывает ровно одну переиспользуемую модель данных;
- `contract_type: shared_model` обязательно.

По директории размещения и root field `contract_type` tooling MUST однозначно различать operation contracts и shared model contracts.
```

## 3. Добавить раздел `Размещение shared model contracts`

```md
## Размещение shared model contracts

- Базовая директория shared models: `.apidev/models` (или кастомная `contracts.shared_models_dir` в `.apidev/config.toml`).
- Рекомендуемая структура: `<namespace>/<model>.yaml`.
- Поддерживаемое расширение: `.yaml`.
- Namespace shared model выводится из имени директории внутри `.apidev/models`.
- Идентификатор shared model вычисляется как `<namespace>.<name>`.

Примеры:
- `.apidev/models/common/pagination_request.yaml`
- `.apidev/models/common/sort_descriptor.yaml`
- `.apidev/models/billing/page_info.yaml`
```

## 4. Добавить раздел `Формат shared model contract`

```md
## Формат shared model contract

Обязательные поля root-объекта:
- `contract_type`
- `name`
- `description`
- `model`

### `contract_type`
- Тип: `string`
- Обязательное
- Допустимое значение: `shared_model`

### `name`
- Тип: `string`
- Обязательное
- Не пустое
- PascalCase рекомендуется как canonical naming style

### `description`
- Тип: `string`
- Обязательное
- Не пустое

### `model`
- Тип: `object`
- Обязательное
- Должно соответствовать правилам schema-фрагмента

Shared model contract не должен содержать поля `method`, `path`, `auth`, `request`, `response`, `errors`.
```

Пример:

```yaml
contract_type: shared_model
name: PaginationRequest
description: Used by list endpoints
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

## 5. Добавить раздел `Использование shared models в operation contracts`

```md
## Использование shared models в operation contracts

В API operation contracts schema node может быть либо inline schema fragment, либо reference node.

### Inline schema fragment
Содержит `type`, `properties`, `items` и другие shape-поля.

### Reference node
Содержит `$ref` и не содержит собственного inline-shape.

Поле `$ref`:
- Тип: `string`
- Значение: short-name или fully-qualified model id
- Fully-qualified формат: `<namespace>.<name>`

Дополнительно допускается scalar shorthand в позициях, где не нужны соседние атрибуты:
- `items: $users.UserSummary`
- `pageInfo: $common.PageInfo`

Reference node допускается в:
- `request.path.properties.*`
- `request.query.properties.*`
- `request.body.properties.*`
- `response.body.properties.*`
- `errors[*].body.properties.*`
- `*.items`
```

Пример:

```yaml
contract_type: operation
method: POST
path: /v1/users/search
auth: bearer
summary: Search users
description: Returns paginated user list
request:
  body:
    type: object
    properties:
      sort:
        $ref: common.SortDescriptor
        required: false
      pagination:
        $ref: common.PaginationRequest
        required: false
response:
  status: 200
  body:
    type: object
    properties:
      pageInfo:
        $ref: common.PageInfo
      items:
        type: array
        items: $users.UserSummary
errors: []
```

## 6. Добавить раздел `Operation-local models`

```md
## Operation-local models

API operation contract MAY содержать блок `local_models` для именованных моделей, используемых только внутри одной операции.

- `local_models` не создают отдельные файлы;
- `local_models` доступны только внутри owning operation;
- shared models не могут ссылаться на `local_models`;
- другие операции не могут ссылаться на `local_models`.
```

## 7. Добавить раздел `Семантические правила для shared models`

```md
## Семантические правила для shared models

Проверяются после schema-валидации:
- уникальность `operation_id`;
- уникальность endpoint signature (`method + path`);
- уникальность shared model id (`namespace + name`);
- существование target model для каждого `$ref` и shorthand `$...`;
- отсутствие ambiguous resolution для short-name refs;
- запрет scope leak из operation-local model во внешний shared scope;
- запрет unsupported cycles;
- соответствие директории размещения значению `contract_type`.
```

## 8. Добавить раздел `Примеры миграции`

```md
## Примеры миграции

### До: inline pagination повторяется в нескольких operation contracts
[пример inline-only]

### После: pagination вынесена в `.apidev/models/common/pagination_request.yaml`
[пример shared_model + `$ref`]
```
