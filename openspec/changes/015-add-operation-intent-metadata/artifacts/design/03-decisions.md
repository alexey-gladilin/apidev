# Решения

## Решение 1: использовать два поля вместо одного
- Выбор: `intent` и `access_pattern`.
- Почему: `POST`-read и imperative read нельзя выразить одним binary flag.

## Решение 2: оставить поля на root-level
- Выбор: не вводить вложенный metadata block.
- Почему: operation contract уже использует flat metadata shape; это проще для authoring и validation.

## Решение 3: не привязывать vocabulary к React Query
- Выбор: `cached | imperative | both | none`, а не `query | mutation`.
- Почему: `apidev` остается SSOT transport/contract tool, а не UI runtime generator.

## Решение 4: обязательный explicit metadata contract
- Выбор: fallback не поддерживается; `intent` и `access_pattern` обязательны для всех operation contracts.
- Почему: команда выбирает сразу целевой contract и не хочет поддерживать mixed mode.
