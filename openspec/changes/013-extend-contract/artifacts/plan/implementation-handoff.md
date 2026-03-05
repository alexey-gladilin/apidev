# Implementation Handoff: 013-extend-contract

## Назначение
Пакет фиксирует handoff для implement-команды по расширению contract format APIDev поддержкой schema-driven request.

## Functional Scope (обязательный)
1. Добавить root-блок `request` в нормативную схему контракта.
2. Поддержать `request.path`, `request.query`, `request.body` со strict запретом unknown fields.
3. Реализовать fail-fast проверку согласованности `request.path` и route `{param}`.
4. Расширить `EndpointContract` request-полями.
5. Публиковать request metadata в generated `operation_map`.
6. Генерировать request transport model из request schema fragment.
7. Расширить OpenAPI projection (`parameters`, `requestBody`) из request metadata.
8. Обновить документацию и регрессионные тесты.

## Ключевые файлы
- `src/apidev/core/rules/contract_schema.py`
- `src/apidev/core/models/contract.py`
- `src/apidev/application/services/diff_service.py`
- `src/apidev/templates/generated_operation_map.py.j2`
- `src/apidev/templates/generated_schema.py.j2`
- `src/apidev/templates/generated_openapi_docs.py.j2`
- `docs/reference/contract-format.md`
- `docs/reference/cli-contract.md`
- `tests/unit/**`
- `tests/integration/**`
- `tests/contract/**`

## Критерии приемки
- `apidev validate` принимает `request` как нормативный root-блок и отклоняет unknown fields.
- Path-template и `request.path` строго согласованы; mismatch дает fail-fast error.
- `operation_map` содержит request metadata (`path/query/body`) как канонический источник.
- Generated request model больше не опирается на фиксированное `{}`.
- OpenAPI корректно формирует `parameters`/`requestBody` из контракта и не добавляет лишнего.
- Поведение генерации детерминировано.
- `openspec validate 013-extend-contract --strict --no-interactive` проходит.

## Readiness Checklist (pre-implement gate)
- `proposal.md`, `design.md`, `artifacts/design/*`, `artifacts/plan/*`, `tasks.md` согласованы.
- `artifacts/plan/*` трактуются как planning-stage snapshot; фактический implementation-tracking ведется в `tasks.md` через `[x]/[ ]` и обновляется только orchestrator (single-writer rule).
- Verification/DoD у каждой задачи формализованы и проверяемы.
- Нетривиальные риски (strict validation, path consistency, optional query/body) отражены в фазах.

## Связи
- Core tasks: [../../tasks.md](../../tasks.md)
- Design summary: [../../design.md](../../design.md)
- Design package: [../design/README.md](../design/README.md)
- Spec delta: [../../specs/cli-tool-architecture/spec.md](../../specs/cli-tool-architecture/spec.md)
