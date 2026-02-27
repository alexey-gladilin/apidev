# 02. Behavior Contract

## Validate behavior

- `example` разрешается в schema-фрагментах: `response.body`, `errors[*].body`, `properties.<field>`, `items`.
- Root-level `examples` блок разрешается в формате:
  - `examples.request`
  - `examples.response`
  - `examples.errors.<ERROR_CODE>`
- Если `example` не задан, поведение полностью обратно совместимо.
- Если `example` задан, выполняются проверки:
  - primitive type compatibility с declared `type`;
  - membership check для `enum`;
  - shape compatibility для `object/array`.
- Для endpoint-level `examples.errors.<ERROR_CODE>` проверяется существование `<ERROR_CODE>` в `errors[*].code`.

## Diff/Gen behavior

- Изменение только `example` в контракте должно менять fingerprint операции.
- `apidev diff` должен показывать соответствующие update-изменения generated файлов.
- `apidev gen` должен выдавать byte-stable output при неизменных контрактах с examples.

## OpenAPI behavior

- Generated OpenAPI fragment должен содержать examples в response/error metadata на основе контрактного schema.
- Generated OpenAPI operation metadata должен отражать endpoint-level `examples.request` и `examples.response`.
- Отсутствие `example` не меняет текущий минимальный output, кроме внутренних структур для унификации рендера.

## Error behavior

- Некорректный `example` вызывает schema-level diagnostics (`SCHEMA_INVALID_TYPE`/`SCHEMA_INVALID_VALUE`) с точной `location`.
- Diagnostics ordering остается deterministic.
