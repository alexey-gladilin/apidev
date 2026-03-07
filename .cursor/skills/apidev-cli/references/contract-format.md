# Формат контрактов APIDev (SSOT YAML) для работы в чате

## Источник истины

- Нормативный документ по формату контрактов: `docs/reference/contract-format.md`.
- Этот файл внутри скилла — компактная рабочая выжимка для LLM-агента.
- При сомнениях, спорных случаях и расширении формата приоритет всегда у `docs/reference/contract-format.md`.

## Когда читать этот документ

Открывать этот справочник, когда задача связана не с запуском CLI, а с содержимым SSOT YAML-контрактов:

- разбор или исправление operation contract;
- разбор или исправление shared model contract;
- сравнение человеко-читаемого описания API с текущими SSOT YAML-файлами;
- проверка структуры, обязательных полей, `$ref`, `local_models`, размещения файлов;
- подготовка списка расхождений и изменений, которые нужно внести в SSOT или в исходное описание.

## Канонические виды контрактов

В APIDev для YAML-контрактов важны два contract kind:

- `operation`:
  - размещение: `.apidev/contracts/<domain>/<operation>.yaml`
  - назначение: описание одной API-операции;
- `shared_model`:
  - размещение: `.apidev/models/<namespace>/<model>.yaml`
  - назначение: описание переиспользуемой модели.

Источник истины для типа файла: сочетание `расположение файла + contract_type`.

Правила:

- operation contract должен лежать в `.apidev/contracts`;
- shared model contract должен лежать в `.apidev/models`;
- `contract_type: shared_model` обязателен для shared model contract;
- `contract_type: operation` допустим и рекомендуется для operation contract; в legacy/transition-режиме может отсутствовать, но файл все равно должен лежать в `.apidev/contracts`.

Невалидно:

- shared model в `.apidev/contracts`;
- operation contract в `.apidev/models`.

## Минимум для operation contract

Обязательные root-поля:

- `method`
- `path`
- `auth`
- `description`
- `response`
- `errors`

Опциональные root-поля:

- `request`
- `local_models`

Неизвестные root-поля запрещены.

Краткая семантика:

- `method`: `GET | POST | PUT | PATCH | DELETE | HEAD | OPTIONS`
- `path`: строка, начинается с `/`, без пробелов
- `auth`: `public | bearer`
- `description`: непустое текстовое описание операции

Минимальный пример:

```yaml
method: GET
path: /v1/health
auth: public
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

## Минимум для shared model contract

Обязательные root-поля:

- `contract_type`
- `name`
- `description`
- `model`

Нормативное значение:

- `contract_type: shared_model`

`model` должен соответствовать обычным правилам schema fragment.

Запрещены operation-поля:

- `method`
- `path`
- `auth`
- `request`
- `response`
- `errors`

Минимальный пример:

```yaml
contract_type: shared_model
name: PaginationRequest
description: Used by list endpoints.
model:
  type: object
  properties:
    page:
      type: integer
      required: true
    size:
      type: integer
      required: true
```

## Структура operation contract

### `request`

Поддерживаемые блоки:

- `request.path`
- `request.query`
- `request.body`

Если `request` отсутствует, используется пустая request-модель.

### `response`

Обязательные поля:

- `response.status`
- `response.body`

### `errors`

`errors` — список error-описаний.

Для каждого элемента обычно используются:

- `code`
- `http_status`
- `body`

Допустим short-form:

- `example` нормализуется в `errors[*].body.example`

## Schema fragment: что можно ожидать внутри `model`, `request`, `response`, `errors`

Типовые поля schema fragment:

- `type`
- `properties`
- `items`
- `required`
- `enum`
- `minimum`
- `maximum`
- `example`
- `$ref`

Базовые правила:

- `type` задает тип узла;
- `properties` используется для `object`;
- `items` используется для `array`;
- `required` задается на уровне свойства;
- `example` должен соответствовать типу;
- если есть `enum`, `example` должен входить в `enum`.

## Правило `$ref`

Reference node должен содержать только `$ref`.

Валидно:

```yaml
request:
  body:
    type: object
    properties:
      pagination:
        $ref: common.PaginationRequest
```

Невалидно:

```yaml
request:
  body:
    type: object
    properties:
      pagination:
        $ref: common.PaginationRequest
        type: object
```

То есть inline-поля рядом с `$ref` запрещены:

- `type`
- `properties`
- `items`
- `required`
- `description`
- `enum`
- `example`
- `minimum`
- `maximum`

Допустим shorthand input sugar вида `$users.UserSummary`, но до валидации он должен нормализоваться в обычный узел `{ "$ref": "users.UserSummary" }`.

## Shared models и переиспользование

Когда shape повторяется в нескольких operation contracts, его стоит выносить в shared model contract:

1. найти повторяющийся inline schema fragment;
2. согласовать имя и namespace;
3. создать `.apidev/models/<namespace>/<model>.yaml`;
4. заменить дублирование в operation contracts на `$ref`;
5. проверить ссылки и границы scope.

Практическое правило:

- shared model влияет на типовую модель и граф зависимостей;
- operation contract описывает runtime-сигнатуру endpoint: `method`, `path`, `auth`, `request`, `response`, `errors`.

## `local_models`

`local_models` — это operation-local модели, которые живут внутри одного operation contract.

Короткая граница ответственности:

- `shared_model` используется повторно между несколькими контрактами;
- `local_models` применяются только внутри одного operation contract.

Ограничения:

- `shared models` не могут ссылаться на `local_models`;
- operation contract в `.apidev/contracts` не может объявлять `contract_type: shared_model`.

## Сценарий: сравнение документа с SSOT YAML

Типовой вход:

- человеко-читаемое описание API или change request;
- существующие YAML-контракты SSOT в `.apidev/contracts` и `.apidev/models`.

Ожидаемый результат от агента:

- перечислить расхождения между описанием и текущим SSOT;
- указать, что именно нужно поправить в SSOT YAML;
- если описание противоречиво или неполно, отдельно указать, что стоит поправить в самом описании.

Чеклист сравнения:

1. Состав операций:
   - есть ли нужный endpoint;
   - нет ли лишних endpoint.
2. Идентичность operation:
   - `method`
   - `path`
   - `auth`
   - `description`
3. Request:
   - `request.path`
   - `request.query`
   - `request.body`
4. Response:
   - `response.status`
   - `response.body`
5. Errors:
   - список ошибок
   - `code`
   - `http_status`
   - `body`
6. Переиспользование моделей:
   - нужен ли `shared_model`;
   - корректны ли `$ref`;
   - не должен ли фрагмент стать `local_models`.
7. Границы формата:
   - правильная директория;
   - корректный `contract_type`;
   - нет ли неизвестных полей;
   - нет ли inline-полей рядом с `$ref`.

Форма ответа по расхождениям должна быть прикладной:

- что изменилось в документе по сравнению с SSOT;
- какие YAML-файлы надо создать, изменить, перенести или удалить;
- какие поля в них надо скорректировать;
- что выглядит как ошибка в исходном описании, а не в SSOT.

## Другие поддерживаемые сценарии

Этот справочник можно использовать и в других задачах:

- валидация описания против формата контрактов;
- обновление только части operation contract;
- обновление только shared model contract;
- вынос повторяющегося inline-schema в `shared_model`;
- проверка `local_models` и границ переиспользования;
- подготовка изменений перед `apidev validate`, `apidev diff` или `apidev gen --check`.

## Что особенно важно помнить

- Один YAML operation contract описывает одну операцию.
- `shared_model` живет в `.apidev/models` и обязан иметь `contract_type: shared_model`.
- Для operation contract обязательны `method`, `path`, `auth`, `description`, `response`, `errors`.
- Для shared model contract обязательны `contract_type`, `name`, `description`, `model`.
- `$ref`-узел содержит только `$ref`.
- `local_models` ограничены рамками одного operation contract.
- Приоритет по всем спорным деталям у `docs/reference/contract-format.md`.
