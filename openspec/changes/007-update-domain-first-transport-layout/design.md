## Контекст
Существующая реализация transport generation использует operation-first layout: файлы роутеров и моделей лежат в плоской структуре и именуются через `<operation_id>`. При этом входные контракты уже организуются по доменам (`<domain>/<operation>.yaml`), а целевые API-проекты обычно используют feature/domain-first структуру модулей.

## Цели / Не-цели
- Цели:
  - перейти к domain-first layout generated transport артефактов;
  - сохранить deterministic output, write-boundary policy и safety-инварианты;
  - синхронизировать metadata и тестовый контракт с новой структурой.
- Не-цели:
  - генерация бизнес-логики (`services`, `repositories`) в generated-зоне;
  - изменение ownership boundary generated/manual;
  - поддержка backward compatibility со старым operation-first output.

## Решения
- Генерация router-файлов переносится в `<domain>/routes/<operation>.py`.
- Генерация transport моделей переносится в `<domain>/models/<operation>_{request|response|error}.py`.
- `operation_map.py` хранит domain-qualified module paths (`<domain>.routes.<operation>`, `<domain>.models.<operation>_response...`).
- Canonical mapping фиксируется как `contract_relpath -> domain segments + operation stem`:
  - вложенные каталоги контракта (`billing/invoices/get.yaml`) сохраняются как вложенные domain segments;
  - каждый segment нормализуется в Python-safe snake_case (`-` -> `_`, недопустимые символы удаляются);
  - если нормализация приводит к target-path коллизии, generation завершается deterministic validation error.
- Package/import policy фиксируется как единый namespace-contract:
  - metadata/import references всегда строятся относительно `generated_root`;
  - runtime wiring использует эти references без ручных path hacks;
  - policy одинакова для single-level и nested domains.
- Интеграция в target app фиксируется через manual `registry/factory` паттерн: generated metadata + manual handlers/auth/error wiring.
- `operation_id` остается стабильным идентификатором operation contract и не становится функцией generated layout.

## Риски / Компромиссы
- Риск: breaking для интеграций, которые импортируют старые module paths.
  - Митигация: явно зафиксированный clean break в proposal/spec/docs.
- Риск: коллизии при одинаковых именах операций в разных вложенных контекстах.
  - Митигация: единый canonical mapping `contract_relpath -> generated domain path` и contract-тесты на уникальность output paths.
- Риск: расхождение expected paths в тестах и runtime wiring.
  - Митигация: синхронное обновление unit/contract/integration тестов и operation registry assertions.
- Риск: scaffold-файлы могут ошибочно удаляться stale-remove логикой.
  - Митигация: отдельное правило keep для scaffold-поддерева при включенном scaffold.
- Риск: OpenAPI может расходиться с контрактом по success status.
  - Митигация: генерация `responses` строго из `response.status` контракта.
- Риск: отсутствует единая import policy для nested domain модулей.
  - Митигация: зафиксировать deterministic package/import policy и покрыть runtime-import regression тестами.
- Риск: неоднозначная трактовка scaffold как "opt-in" при default `true` после `init`.
  - Митигация: явно зафиксировать effective mode policy (`CLI -> config -> default`) и remove semantics для `--no-scaffold`.

## Linked Artifacts
- Research: [artifacts/research/2026-03-01-domain-layout-gap-baseline.md](./artifacts/research/2026-03-01-domain-layout-gap-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/transport-generation/spec.md](./specs/transport-generation/spec.md)

## Готовность к Implement
После approval этот change-пакет является входом для отдельной implement-команды (`/openspec-implement` или `/openspec-implement-single`).
