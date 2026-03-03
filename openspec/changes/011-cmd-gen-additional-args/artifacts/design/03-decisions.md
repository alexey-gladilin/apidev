# Решения и компромиссы

## DEC-01: Scope ограничен `apidev gen`

- Решение: включить include/exclude endpoint только в `apidev gen`.
- Почему: запрос пользователя адресован генерации кода; это снижает риск расширения change scope.
- Компромисс: `apidev diff` временно остается без аналогичной фильтрации.

## DEC-02: Повторяемые CLI-флаги вместо config-параметров

- Решение: фильтры задаются runtime-аргументами `--include-endpoint`/`--exclude-endpoint`.
- Почему: фильтрация чаще нужна как локальный/CI override для конкретного запуска.
- Компромисс: без параметров в config нет persistent profile фильтрации.

## DEC-03: Precedence `include -> exclude`

- Решение: include формирует candidate set, exclude выполняет вычитание.
- Почему: модель совпадает с типичной практикой whitelist/blacklist и проще для предсказания.
- Компромисс: пользователю нужно учитывать, что exclude всегда имеет финальный приоритет.

## DEC-04: Filter-matching по `operation_id` и `contract_relpath`

- Решение: pattern матчится к стабильным строковым идентификаторам операции.
- Почему: обе сущности уже детерминированно формируются и доступны в pipeline.
- Компромисс: отсутствует прямой матчинг по HTTP method/path, если это не отражено в pattern-значениях.

## DEC-05: Явные diagnostics для invalid/empty filter outcome

- Решение: ввести отдельные диагностические коды для невалидного pattern и пустого effective set.
- Почему: это дает проверяемый CI-contract и понятный fail-fast UX.
- Компромисс: потребуется синхронизация docs/tests и taxonomy code namespace.

