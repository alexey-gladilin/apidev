# Change: Этап B — Transport Generation MVP+

## Why

Текущее поколение transport-артефактов в `apidev` ограничено skeleton-уровнем: формируется `operation_map.py` и базовые router-файлы без request/response/error моделей и без runnable transport bridge.
`docs/roadmap.md` фиксирует для этапа B целевой сдвиг к `Transport Generation MVP+`: model generation, минимально runnable transport layer и стабильный operation registry/handler bridge contract.

## What Changes

- Добавляется capability `transport-generation` с нормативными требованиями для этапа B.
- Формализуется generation contract для request/response/error model generation в generated-зоне.
- Формализуется минимально runnable transport layer с bridge-контрактом между generated transport и manual business handlers.
- Формализуется стабильный operation registry как deterministic source of operation metadata для runtime wiring и тестов.
- Фиксируется использование baseline-исследования по external API как style/structure reference перед implement-фазой.

## Impact

- Affected specs: `transport-generation` (new)
- Affected code (target for implement phase): `src/apidev/application/services/diff_service.py`, `src/apidev/application/services/generate_service.py`, `src/apidev/templates/*.j2`, `src/apidev/core/models/**`, `src/apidev/core/rules/**`, `tests/**`
- Breaking: нет (расширение генерации в рамках существующей CLI команды `apidev gen`)

## Linked Artifacts

- Research baseline (repo): [artifacts/research/2026-02-27-transport-generation-baseline.md](./artifacts/research/2026-02-27-transport-generation-baseline.md)
- Research baseline (external style reference): [../001-contract-validation/artifacts/research/2026-02-27-external-api-codegen-baseline.md](../001-contract-validation/artifacts/research/2026-02-27-external-api-codegen-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)

