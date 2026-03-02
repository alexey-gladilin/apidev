# Change: Domain-first layout для generated transport артефактов

## Почему
Фактический output `apidev gen` сейчас организован как operation-first (плоские файлы по `operation_id`), например `routers/billing_get_invoice.py` и `transport/models/billing_get_invoice_response.py`.

Это не совпадает с ожидаемой feature/domain-first структурой целевых API-проектов (single-level модуль на домен с `routes/schemas/wiring`) и усложняет интеграцию generated слоя в существующие кодовые базы, где доменная группировка уже является архитектурным стандартом.

## Что изменится
- Модифицируется capability `transport-generation`: generated layout переходит на domain-first структуру.
- `apidev gen` и `apidev diff` формируют router/model артефакты в доменном корне `<generated_dir>/<domain>/` с подпапками `routes/` и `models/`.
- Operation registry (`operation_map.py`) и bridge metadata начинают ссылаться на новые domain-qualified module paths.
- Фиксируется канонический mapping для single-level domain путей и нормализация Python module segments (deterministic и collision-safe).
- Фиксируется ограничение contract layout: поддерживается только `<domain>/<operation>.yaml`; вложенные домены отклоняются с детерминированной диагностикой.
- Фиксируется package policy: генерация создает `__init__.py` для `<domain>/`, `<domain>/routes/`, `<domain>/models/`.
- Формализуется integration contract для target app: registry/factory wiring, auth integration, error mapping, OpenAPI integration.
- Добавляется конфигурируемая генерация integration scaffold с точным контрактом:
  - config: `generator.scaffold`, `generator.scaffold_dir`;
  - CLI overrides: `--scaffold`, `--no-scaffold`;
  - policy: `create-if-missing` без перезаписи существующих manual файлов;
  - deterministic precedence: `CLI flag -> config -> default`, где default после `apidev init` равен `generator.scaffold = true`.
- Документация CLI/contract/testing синхронизируется с новым expected output.

Целевая структура:

```text
<generated_dir>/
├── operation_map.py
├── openapi_docs.py
└── <domain>/
    ├── routes/
    │   └── <operation>.py
    └── models/
        ├── <operation>_request.py
        ├── <operation>_response.py
        └── <operation>_error.py
```

## Влияние
- Затронутые спеки: `transport-generation` (MODIFIED).
- Затронутый код (target implement-фазы):
  - `src/apidev/application/services/diff_service.py`
  - `src/apidev/templates/generated_operation_map.py.j2`
  - `src/apidev/templates/generated_router.py.j2`
  - `src/apidev/templates/generated_schema.py.j2`
  - `tests/unit/**`, `tests/contract/**`, `tests/integration/**`
  - `docs/reference/contract-format.md`
  - `docs/reference/cli-contract.md`
  - `docs/process/testing-strategy.md`
- Breaking: да, изменяются пути generated файлов и module-path references в metadata.

## Compatibility Policy
- Обратная совместимость со старым operation-first layout в рамках этой change **не обеспечивается**.
- Change ориентирован на pre-release стадию инструмента и допускает прямой переход к новой структуре output.

## Dependency & Sequencing Policy
- В части `transport-generation` change заменяет operation-first контракт из `002-transport-generation` новым domain-first canonical layout.
- В части stale-remove policy change дополняет safety семантику `006-safety-drift`: scaffold-поддерево регулируется отдельным правилом keep/remove в зависимости от `scaffold` effective mode.
- В части compatibility/deprecation metadata change должен оставаться согласованным с `005-contract-evolution-integration` (без изменения стабильности `operation_id` и baseline-driven governance).

## Dependency Order
1. `002-transport-generation` является базовым контрактом transport-capability (исходный ownership boundary, stable registry, transport generation contract).
2. `007-update-domain-first-transport-layout` выполняет layout-level replacement внутри `transport-generation` и вводит domain-first canonical mapping.
3. `006-safety-drift` применяется поверх нового layout как remove-governance слой; `007` добавляет scoped-правило для scaffold subtree при сохранении boundary-инвариантов `006`.
4. `005-contract-evolution-integration` остается governance-слоем совместимости поверх обоих изменений; физический layout не меняет identity/compatibility baseline.

## Точки замещения/дополнения соседних change-контрактов
- `002-transport-generation` (замещение):
  - замещается path-semantics для generation artifacts: operation-first -> domain-first (`<domain>/routes`, `<domain>/models`);
  - замещается module-path contract в registry: plain transport refs -> domain-qualified refs (`<domain>.routes.*`, `<domain>.models.*`);
  - сохраняются без изменений: отсутствие business logic в generated transport и manual ownership boundary.
- `006-safety-drift` (дополнение):
  - дополняется remove-semantics для scaffold subtree: при enabled scaffold файлы исключаются из stale-remove, при disabled (`--no-scaffold`/`generator.scaffold=false`) снова считаются stale в пределах generated-root;
  - сохраняются без изменений: канонические diagnostics (`remove-conflict`, `remove-boundary-violation`) и machine-readable поля (`code`, `location`, `detail`).
- `005-contract-evolution-integration` (совместимость без замещения):
  - подтверждается стабильность `operation_id` и baseline-driven classification независимо от физического layout generated файлов;
  - change `007` не изменяет policy/exit semantics `warn|strict`, deprecation lifecycle и release-state контракт `005`.

## Linked Artifacts
- Research baseline: [artifacts/research/2026-03-01-domain-layout-gap-baseline.md](./artifacts/research/2026-03-01-domain-layout-gap-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/transport-generation/spec.md](./specs/transport-generation/spec.md)
- Target integration docs: `docs/architecture/generated-integration.md`

## Границы этапа
Этот change-пакет покрывает Proposal/Design/Plan и readiness к implement.
Implementation выполняется отдельно через `/openspec-implement` или `/openspec-implement-single` после review/approval.
