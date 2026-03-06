# Change: Переиспользуемые модели контрактов в `apidev`

## Почему
В `apidev` контракты операций сегодня в основном описывают request/response структуры как inline-shape деревья. Это неудобно для сценариев, где одни и те же модели повторяются в нескольких API: сортировка, пагинация, page-info, диапазоны дат, money-like объекты, стандартные error item и другие value objects.

Из-за отсутствия first-class reusable model abstraction аналитики и разработчики вынуждены дублировать одни и те же структуры в нескольких операциях. Это нарушает DRY, усложняет эволюцию контрактов и не дает downstream-инструментам, в том числе `uidev`, надежного сигнала о том, что речь идет об одной и той же семантической модели.

## Что меняется
- В контрактный формат `apidev` вводится отдельный вид YAML-контракта для shared models с собственным расположением в файловой структуре.
- Вводится ссылочный механизм (`$ref`) и scalar-shorthand для обращения к shared model из request/response и их вложенных узлов API-контрактов.
- Фиксируется различие между shared models и operation-local models.
- Фиксируются directory layout и правила, по которым аналитики, разработчики и инструменты различают API contracts и shared model contracts.
- Добавляются правила валидации ссылок, scope boundaries, conflicts и cycle policy.
- Команда `apidev validate` получает явную обязанность находить циклические зависимости и другие нарушения графа ссылок.
- Добавляется CLI-возможность introspection графа зависимостей контрактов и shared models с human-readable и machine-readable выводом.
- Появляется нормализованное graph-based представление моделей, пригодное для downstream-потребителей.
- Подготавливается migration guide для аналитиков и backend-команд по выносу типовых общих моделей.

## Влияние
- Affected specs:
  - `apidev-shared-contract-models` (new)
- Affected docs:
  - `openspec/changes/014-shared-contract-models/design.md`
  - `openspec/changes/014-shared-contract-models/tasks.md`
- Affected code (planned):
  - contract schema and semantic validation in `apidev`
  - contract normalization/model registry in `apidev`
  - CLI graph/introspection command in `apidev`
  - authoring guidance for reusable models

## Ожидаемый результат
Автор контракта сможет один раз объявить `SortDescriptor`, `PaginationRequest`, `PageInfo` и другие общие модели и ссылаться на них из разных операций без повторного inline-описания.
