# Change: Расширение формата контракта APIDev для schema-driven request

## Почему
Текущий контракт APIDev нормативно описывает `response` и `errors`, но не содержит отдельного `request`-блока.
Из-за этого нельзя детерминированно и типобезопасно генерировать request-часть transport-артефактов и OpenAPI (`parameters`, `requestBody`) на основе контракта.

Потребность change: добавить в контракт поддержку request-параметризации на уровне формата и генерации:
- `request body`
- `query params` (пример: `/somepath/?args=10&arg2=ddd`)
- `path params` (пример: `/{path_param}/10/{path_param2}/ddd`)

## Что изменится
- В API contract format добавляется root-блок `request`.
- В `request` добавляются подблоки:
  - `path` (описание path-параметров)
  - `query` (описание query-параметров)
  - `body` (описание body schema)
- Валидатор контракта расширяется правилами для `request`.
- Модель `EndpointContract` расширяется request-полями.
- Generated metadata (`operation_map`) получает request schema/params metadata.
- OpenAPI projection начинает строить `parameters` и `requestBody` из request-контракта.
- Generated request transport model перестает быть пустым `{}` и строится из контракта.

## Влияние
- Затронутые спеки: `cli-tool-architecture`.
- Затронутая документация:
  - `docs/reference/contract-format.md`
  - `docs/reference/cli-contract.md` (при необходимости для diagnostics/JSON-контрактов)
- Затронутый код (implement-фаза):
  - `src/apidev/core/models/contract.py`
  - `src/apidev/core/rules/contract_schema.py`
  - `src/apidev/application/services/diff_service.py`
  - `src/apidev/templates/generated_operation_map.py.j2`
  - `src/apidev/templates/generated_openapi_docs.py.j2`
  - `src/apidev/templates/generated_schema.py.j2`

## Ограничения и принципы
- Контракт остается строгим: unknown fields запрещены.
- Требуется детерминированная генерация на одинаковом входе.
- Path/query/body должны иметь однозначное отображение в OpenAPI и transport-model.

## Linked Artifacts
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/cli-tool-architecture/spec.md](./specs/cli-tool-architecture/spec.md)

## Готовность к Implement
После approval реализация выполняется отдельной командой: `/openspec-implement` или `/openspec-implement-single`.
