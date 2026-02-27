## Контекст
Текущее состояние зафиксировано в research-артефакте: `example` отсутствует в `SCHEMA_ALLOWED_FIELDS`, из-за чего поле считается неизвестным и отклоняется валидацией.
Также generated OpenAPI paths сейчас не включают схему request/response/error примеров, даже если такие данные могли бы приходить из контрактов.

## Цели / Не-цели
- Цели:
  - добавить декларативный `example` в schema-фрагменты контракта;
  - добавить endpoint-level блок `examples` для operation payload examples в Swagger/OpenAPI;
  - обеспечить строгую валидацию и deterministic сериализацию примеров;
  - пробросить examples в generated transport/OpenAPI артефакты без генерации бизнес-логики.
- Не-цели:
  - поддержка `examples` (множественные примеры) в рамках этой change;
  - автоматическая генерация примеров на основе DB/runtime данных;
  - изменение auth/error policy вручную управляемого слоя.

## Решения
- `example` вводится как опциональное поле schema-фрагмента и разрешается в тех же узлах, где разрешены `type/properties/items/enum`.
- В root контракта вводится опциональный блок `examples`:
  - `examples.request` - пример request payload;
  - `examples.response` - пример success response payload;
  - `examples.errors.<ERROR_CODE>` - пример payload для конкретного error code.
- Валидация `example` остается schema-first:
  - примитивные типы должны совпадать с declared `type`;
  - для `enum` значение `example` должно входить в перечисление;
  - для `object/array` проверяется форма (mapping/list) и рекурсивная совместимость.
- Для endpoint-level `examples` валидация проверяет связь с контрактом:
  - `examples.errors.<ERROR_CODE>` допустим только для объявленных `errors[*].code`;
  - payload examples должны быть совместимы с соответствующими body schema.
- Diff/Gen pipeline расширяется так, чтобы metadata с `example` детерминированно попадала в generated модели и OpenAPI fragment.

## Риски / Компромиссы
- Риск: усложнение рекурсивной валидации schema-узлов.
  - Митигация: изолировать проверку `example` в отдельные helper-функции и покрыть table-driven тестами.
- Риск: недетерминированный вывод при object examples.
  - Митигация: canonical serialization (`sort_keys=True`) и стабильный порядок обхода.
- Компромисс: на первом шаге поддерживается только `example`, не `examples`, чтобы сохранить минимальный изменяемый контракт.

## Linked Artifacts
- Research baseline: [artifacts/research/2026-02-27-example-field-baseline.md](./artifacts/research/2026-02-27-example-field-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/contract-examples/spec.md](./specs/contract-examples/spec.md)

## Готовность к Implement
Технические решения и ограничения зафиксированы; после approval change готова к отдельной implementation-команде.
