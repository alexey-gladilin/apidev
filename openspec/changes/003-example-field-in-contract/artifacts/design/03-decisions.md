# 03. Decisions

## D1. Поддерживать `example`, но не `examples`

- Статус: Accepted
- Причина: минимальный и контролируемый шаг эволюции формата.
- Последствия: расширение до `examples` возможно отдельной change без ломки текущего контракта.

## D1a. Явно не поддерживать root-level `examples` в этой change

- Статус: Accepted
- Причина: ограничение объема реализации до одиночного schema-level `example`.
- Последствия: root-level `examples` продолжает отклоняться как unknown field.

## D2. Валидация `example` должна быть strict

- Статус: Accepted
- Причина: проект следует validate-first подходу; silent acceptance недопустим.
- Последствия: потребуется дополнительная рекурсивная проверка типов/shape/enum.

## D3. Fingerprint учитывает example-изменения

- Статус: Accepted
- Причина: изменения API примеров должны детектироваться как drift и быть reviewable в diff.
- Последствия: тесты diff/gen должны проверять update при изменении only-example.

## D4. Примеры пробрасываются через generated metadata

- Статус: Accepted
- Причина: примеры имеют ценность только если доходят до OpenAPI/transport артефактов.
- Последствия: обновление шаблонов генерации и integration regression.

## Considered Alternatives

- Альтернатива A: хранить `example` только в docs, не в контракте.
  - Отклонено: теряется single source of truth и deterministic pipeline.
- Альтернатива B: принимать любой `example` без валидации.
  - Отклонено: нарушает strict quality bar и делает контракты ненадежными.
