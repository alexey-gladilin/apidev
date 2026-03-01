# Change: Domain-first layout для generated transport артефактов

## Почему
Фактический output `apidev gen` сейчас организован как operation-first (плоские файлы по `operation_id`), например `routers/billing_get_invoice.py` и `transport/models/billing_get_invoice_response.py`.

Это не совпадает с ожидаемой feature/domain-first структурой целевых API-проектов (модуль на домен с вложенными `routes/schemas/wiring`) и усложняет интеграцию generated слоя в существующие кодовые базы, где доменная группировка уже является архитектурным стандартом.

## Что изменится
- Модифицируется capability `transport-generation`: generated layout переходит на domain-first структуру.
- `apidev gen` и `apidev diff` формируют router/model артефакты в доменном корне `<generated_dir>/<domain>/` с подпапками `routes/` и `models/`.
- Operation registry (`operation_map.py`) и bridge metadata начинают ссылаться на новые domain-qualified module paths.
- Фиксируется канонический mapping для nested domain путей и нормализация Python module segments (deterministic и collision-safe).
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

## Linked Artifacts
- Research baseline: [artifacts/research/2026-03-01-domain-layout-gap-baseline.md](./artifacts/research/2026-03-01-domain-layout-gap-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/transport-generation/spec.md](./specs/transport-generation/spec.md)
- Target integration docs: `docs/architecture/generated-integration.md`

## Границы этапа
Этот change-пакет покрывает Proposal/Design/Plan и readiness к implement.
Implementation выполняется отдельно через `/openspec-implement` или `/openspec-implement-single` после review/approval.
