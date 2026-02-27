# 02. Behavior Contract

## Validate behavior

- `example` разрешается в schema-фрагментах: `response.body`, `errors[*].body`, `properties.<field>`, `items`.
- Root-level `examples` блок не поддерживается и отклоняется как unknown field.
- Если `example` не задан, поведение полностью обратно совместимо.
- Если `example` задан, выполняются проверки:
  - primitive type compatibility с declared `type`;
  - membership check для `enum`;
  - shape compatibility для `object/array`.

## Diff/Gen behavior

- Изменение только `example` в контракте должно менять fingerprint операции.
- `apidev diff` должен показывать соответствующие update-изменения generated файлов.
- `apidev gen` должен выдавать byte-stable output при неизменных контрактах с `example`.

## OpenAPI behavior

- Generated OpenAPI fragment должен содержать schema-level `example` в response/error metadata на основе контрактной schema.
- Отсутствие `example` не меняет текущий минимальный output, кроме внутренних структур для унификации рендера.

## Error behavior

- Некорректный `example` вызывает schema-level diagnostics (`SCHEMA_INVALID_TYPE`/`SCHEMA_INVALID_VALUE`) с точной `location`.
- Diagnostics ordering остается deterministic.
