## ADDED Requirements

### Requirement: Контрактная схема поддерживает опциональное поле `example`
`apidev validate` SHALL принимать опциональное поле `example` внутри поддерживаемых schema-фрагментов (`response.body`, `errors[*].body`, вложенные `properties` и `items`) без диагностики unknown-field.

#### Scenario: Пример принимается в схеме ответа
- **WHEN** контракт содержит `response.body.properties.<field>.example`
- **THEN** schema validation SHALL успешно проходить для этого узла, если `example` совместим с ограничениями схемы
- **AND** diagnostics SHALL NOT содержать `SCHEMA_UNKNOWN_FIELD` для `example`

#### Scenario: Пример принимается во вложенном элементе массива
- **WHEN** контракт содержит `response.body.items.example` для `type: array`
- **THEN** schema validation SHALL считать этот узел валидным schema field

### Requirement: Значение `example` валидируется по ограничениям схемы
Validation SHALL проверять совместимость `example` с объявленным schema node (`type`, `enum` и container shape).

#### Scenario: Несовпадение примитивного типа отклоняется
- **WHEN** schema node имеет `type: integer` и `example: "42"`
- **THEN** validation SHALL вернуть диагностическое сообщение об ошибочном типе примера

#### Scenario: Несовпадение enum отклоняется
- **WHEN** schema node имеет `enum: ["NEW", "DONE"]` и `example: "ARCHIVED"`
- **THEN** validation SHALL вернуть диагностическое сообщение о несовместимости с enum

### Requirement: Root-level `examples` не поддерживается
`apidev validate` SHALL отклонять root-level блок `examples` как неизвестное поле контракта в рамках этой change.

#### Scenario: Контракт с `examples` на root уровне отклоняется
- **WHEN** контракт содержит root-level `examples`
- **THEN** validation SHALL вернуть unknown-field диагностику для `examples`

### Requirement: Generated transport/OpenAPI metadata детерминированно сохраняет `example`
`apidev diff` и `apidev gen` SHALL включать принятый schema-level `example` в generated metadata так, чтобы неизменные контракты сохраняли byte-stable output, а изменение `example` приводило к обнаруживаемому drift.

#### Scenario: Повторная генерация остается стабильной
- **WHEN** контракты и шаблоны не менялись между двумя запусками генерации
- **THEN** generated artifacts с `example` SHALL оставаться byte-identical

#### Scenario: Изменение `example` влияет на fingerprint и diff
- **WHEN** в schema меняется только значение `example`
- **THEN** operation metadata fingerprint SHALL измениться
- **AND** `apidev diff` SHALL показать соответствующие generated updates

#### Scenario: Schema-level `example` отображается в OpenAPI metadata
- **WHEN** контракт содержит `example` в response/error schema
- **THEN** generated OpenAPI metadata SHALL включать этот пример в соответствующий schema fragment
