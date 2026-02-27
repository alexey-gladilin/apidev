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

## Размещение файлов

- Базовая директория контрактов: `.apidev/contracts` (или кастомная `contracts.dir` в `.apidev/config.toml`).
- Рекомендуемая структура: `<domain>/<operation>.yaml`.
- Поддерживаемое расширение: `.yaml`.
- `operation_id` вычисляется из относительного пути и должен быть уникален.

Пример:

- `.apidev/contracts/system/health.yaml`
- `.apidev/contracts/billing/create_invoice.yaml`

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
