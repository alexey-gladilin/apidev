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
- Canonical mapping фиксируется как `contract_relpath -> domain segment + operation stem`:
  - поддерживается только single-level layout контракта `<domain>/<operation>.yaml`;
  - вложенные каталоги контракта (`billing/invoices/get.yaml`) отклоняются deterministic validation error;
  - domain и operation segment нормализуются в Python-safe snake_case (`-` -> `_`, недопустимые символы удаляются);
  - если нормализация приводит к target-path коллизии, generation завершается deterministic validation error.
- Package/import policy фиксируется как единый namespace-contract:
  - metadata/import references всегда строятся относительно `generated_root`;
  - runtime wiring использует эти references без ручных path hacks;
  - generation создает `__init__.py` в `<domain>/`, `<domain>/routes/`, `<domain>/models/` для стабильной importability.
- Интеграция в target app фиксируется через manual `registry/factory` паттерн: generated metadata + manual handlers/auth/error wiring.
- `operation_id` остается стабильным идентификатором operation contract и не становится функцией generated layout.

## Dependency Order
1. Сначала принимается baseline `002-transport-generation` как источник исходного transport-контракта и ownership-границ.
2. Затем `007-update-domain-first-transport-layout` выполняет targeted replacement только layout/module-path части capability `transport-generation`.
3. После фиксации нового layout применяется `006-safety-drift`: remove-governance и diagnostics остаются каноничными, `007` добавляет scaffold-aware branch для stale-remove.
4. Поверх этого сохраняется совместимость с `005-contract-evolution-integration`: compatibility/deprecation governance работает по неизменному identity (`operation_id`) и baseline snapshot.

## Точки замещения/дополнения соседних change-контрактов
- Точки замещения `002-transport-generation`:
  - `Transport Model Generation`: замещение target-path контракта на `<domain>/models/<operation>_{request|response|error}.py`;
  - `Stable Operation Registry Contract`: замещение формата ссылок на domain-qualified module paths;
  - `Minimal Runnable Transport Layer`: уточнение router layout на `<domain>/routes/<operation>.py` без расширения ownership generated/manual.
- Точки дополнения `006-safety-drift`:
  - добавляется scoped-rule для scaffold subtree в stale-remove plan (`keep` при scaffold enabled, `remove` при scaffold disabled);
  - сохраняются неизменными каталоги diagnostic codes и write-boundary инварианты `REMOVE`.
- Точки совместимости `005-contract-evolution-integration`:
  - layout refactor не изменяет identity операции (`operation_id`) и не вносит churn в compatibility classification;
  - deprecation lifecycle, `baseline_ref`, release-state storage и policy precedence (`CLI -> config -> default`) остаются под контрактом `005` без замещения.

## Риски / Компромиссы
- Риск: breaking для интеграций, которые импортируют старые module paths.
  - Митигация: явно зафиксированный clean break в proposal/spec/docs.
- Риск: коллизии при нормализации имен domain/operation сегментов.
  - Митигация: единый canonical mapping `contract_relpath -> generated domain path`, deterministic collision diagnostics и contract-тесты на уникальность output paths.
- Риск: расхождение expected paths в тестах и runtime wiring.
  - Митигация: синхронное обновление unit/contract/integration тестов и operation registry assertions.
- Риск: scaffold-файлы могут ошибочно удаляться stale-remove логикой.
  - Митигация: отдельное правило keep для scaffold-поддерева при включенном scaffold.
- Риск: OpenAPI может расходиться с контрактом по success status.
  - Митигация: генерация `responses` строго из `response.status` контракта.
- Риск: отсутствует единая import policy для generated domain модулей.
  - Митигация: зафиксировать deterministic package/import policy с `__init__.py` и покрыть runtime-import regression тестами.
- Риск: неоднозначная трактовка scaffold как "opt-in" при default `true` после `init`.
  - Митигация: явно зафиксировать effective mode policy (`CLI -> config -> default`) и remove semantics для `--no-scaffold`.

## Linked Artifacts
- Research: [artifacts/research/2026-03-01-domain-layout-gap-baseline.md](./artifacts/research/2026-03-01-domain-layout-gap-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/transport-generation/spec.md](./specs/transport-generation/spec.md)

## Готовность к Implement
После approval этот change-пакет является входом для отдельной implement-команды (`/openspec-implement` или `/openspec-implement-single`).
