## Контекст
Текущий формат контракта APIDev не поддерживает root-блок `request` как нормативную часть модели.
Это блокирует schema-driven генерацию request-части transport/OpenAPI: path/query/body параметры не описываются и не проецируются детерминированно.

Цель design-пакета: зафиксировать архитектуру расширения контракта, где `request` становится first-class частью API contract.

## Цели / Не-цели
- Цели:
  - добавить в контракт поддержку `request.path`, `request.query`, `request.body`;
  - синхронизировать validation -> model -> operation_map -> OpenAPI projection;
  - ввести проверку согласованности `request.path` с `{param}` в `path`;
  - сохранить strict validation и deterministic generation.
- Не-цели:
  - реализация feature в рамках текущего документационного этапа (`proposal/design/plan`);
  - изменение бизнес-логики runtime beyond contract projection.

## Решения
- Root-блок `request` добавляется в нормативный контракт и в контрактную модель.
- Request-подблоки ограничиваются `path`, `query`, `body`.
- Unknown fields в request-ветке запрещаются.
- `request.path` и path-template согласуются на этапе валидации (fail-fast на mismatch).
- Generated `operation_map` публикует request metadata.
- OpenAPI projection формирует `parameters`/`requestBody` из request metadata.
- Request transport model генерируется из request schema fragment, а не из `{}`.

## Риски / Компромиссы
- Более строгая валидация может потребовать обновления существующих контрактов.
- Некорректные path placeholders начнут детектироваться раньше (до генерации).
- Потребуется аккуратная совместимость для операций без `query` и/или `body`.

## Linked Artifacts
- Design package index: [artifacts/design/README.md](./artifacts/design/README.md)
- Architecture: [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md)
- Behavior: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md)
- Decisions: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md)
- Testing: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md)
- Spec delta: [specs/cli-tool-architecture/spec.md](./specs/cli-tool-architecture/spec.md)

## Готовность к Implement
После approval реализация выполняется отдельной командой `/openspec-implement` (или `/openspec-implement-single`).
Функциональная возможность поддержки расширенного request-контракта входит в scope implement-этапа этого change.
