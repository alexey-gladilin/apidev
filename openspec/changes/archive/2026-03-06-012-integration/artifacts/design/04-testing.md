# Тестирование: Integration Improvements

## Цели
- Подтвердить безопасность path-boundary и отсутствие записи вне разрешенных границ.
- Подтвердить детерминированность результата и диагностики.
- Подтвердить отсутствие регрессий по текущему поведению.
- Подтвердить корректность новых интеграционных веток поведения.

## Unit-тесты
- Path policy:
  - независимость `scaffold_dir` от `generated_dir`;
  - запрет выхода за project-root;
  - детерминированная нормализация путей.
- Scaffold write policy:
  - `create-missing`, `skip-existing`, `fail-on-conflict`;
  - default behavior без явного `scaffold_write_policy` (`create-missing`);
  - одинаковый результат при повторных запусках.
- Error example normalizer:
  - short-form only;
  - nested-form only;
  - обе формы с совпадающими значениями;
  - конфликт значений.
- Release-state validation:
  - legacy key (`current_release`) -> validation error;
  - `release_number` type mismatch -> validation error;
  - diagnostics содержит ключ и ожидаемый тип.
- Extension toggle:
  - включено: присутствуют `x-apidev-*`;
  - выключено: отсутствуют `x-apidev-*`, core OpenAPI неизменен.

## Integration-тесты
- `init` профили:
  - enum validation для `--runtime` (`fastapi|none`) и `--integration-mode` (`off|scaffold|full`);
  - профильный bootstrap создает ожидаемый набор integration-артефактов;
  - повторный `init` с тем же профилем идемпотентен;
  - взаимодействие с `--repair` и `--force` соответствует правилам precedence.
- Runtime/OpenAPI adapter:
  - маршрут и OpenAPI metadata согласованы для одной и той же операции;
  - стабильный порядок операций;
  - корректная обработка ошибок и deprecated/auth/domain-derived tags metadata.
  - наличие manual `tags` в metadata операции завершает генерацию с validation error.
- End-to-end генерация:
  - отдельные `generated_dir` и `scaffold_dir`;
  - соблюдение выбранной scaffold policy;
  - отсутствие побочных изменений вне управляемого scope.

## Regression-тесты
- Без новых параметров поведение остается совместимым с текущей версией.
- Существующие контракты без `errors[].example` продолжают проходить без изменений.
- Текущие pipeline `init/diff/gen` не деградируют по exit semantics и диагностике.

## Property/Determinism проверки
- Идентичные входы дают идентичные выходные артефакты и diagnostics envelope.
- Повторные прогоны не создают дрейф при отсутствии изменений входов.

## Security-проверки
- Невозможность записи за пределы project-root при любых комбинациях `scaffold_dir`.
- Политики записи scaffold не позволяют нежелательную перезапись файлов в режиме `skip-existing`.
- Конфликтные и неоднозначные состояния завершаются fail-fast без частичной записи.

## Acceptance mapping
- `scaffold_dir independence`: покрыт boundary и e2e сценариями.
- `scaffold_write_policy`: покрыт unit и integration policy-сценариями.
- `runtime openapi adapter`: покрыт integration-сценариями согласованности маршрутов и metadata.
- `errors example short-form`: покрыт unit и regression нормализации.
- `release-state strict validation`: покрыт negative unit-сценариями на ключ и тип.
- `init integration profiles`: покрыт integration профилями и precedence.
- `openapi extension toggle`: покрыт unit + regression совместимости.
