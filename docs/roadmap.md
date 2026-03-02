# Дорожная Карта APIDev

Статус: `Current`

Снимок состояния: 2 марта 2026.

Этот документ фиксирует актуальный статус реализации и ближайшие продуктовые горизонты. Нормативные контракты поведения остаются в `docs/reference/*` и `docs/architecture/*`.

## Что уже реализовано

- installable CLI binary `apidev` с командами `init`, `validate`, `diff`, `gen` и compatibility alias `generate`;
- validate-first pipeline `load -> validate -> plan -> render -> write/check`;
- deterministic generation в domain-first layout (`<domain>/routes`, `<domain>/models`);
- generation/update/remove plan (`ADD|UPDATE|REMOVE`) с детерминированным порядком изменений;
- strict write-boundary policy внутри configured generated root;
- drift check через `apidev diff` и `apidev gen --check` с нормализованными exit semantics;
- compatibility policy (`warn|strict`), baseline precedence (`CLI -> release-state -> git`) и deprecation lifecycle checks;
- release-state lifecycle в `gen apply` (auto-create, bump policy, fail-without-write);
- integration scaffold contract (`--scaffold`, `--no-scaffold`, `create-if-missing`);
- unified machine-readable diagnostics contract для `validate`, `diff`, `gen --check`, `gen` (единый JSON envelope, стабилизированная taxonomy codes, deterministic ordering);
- архитектурные guardrails и regression-наборы unit/contract/integration.

## Закрытые gaps предыдущего среза

- gap по отсутствию `REMOVE` в generation plan закрыт;
- базовый integration contract расширен и закреплен в документации;
- release-state lifecycle и baseline semantics формализованы и внедрены;
- Horizon 1 (Diagnostics Contract Hardening) реализован и синхронизирован с docs/tests;
- roadmap переведен из historical snapshot в рабочий текущий статус.

## Текущая стадия

`Foundation Complete -> Productization Execution`

Этапы A+B+C+D завершены, этап E выполняется. По OpenSpec в `openspec/changes/*/tasks.md` незакрытых чекбоксов нет на срез 2 марта 2026.

## Статус этапов

| Этап | Статус на 2 марта 2026 | Что уже реализовано | Фокус следующего шага |
|---|---|---|---|
| A — Contract Validation Hardening | `Done` | strict schema checks, semantic baseline, unified machine-readable diagnostics contract | semantic deepening правил validation и улучшение triage UX |
| B — Transport Generation MVP+ | `Done` | domain-first generation, stable operation map, router/models templates, OpenAPI metadata | generated test scaffolds и расширение интеграционных шаблонов |
| C — Diff/Generate Safety & Drift Governance | `Done` | validate-first, read-only semantics, deterministic `ADD|UPDATE|REMOVE`, write-boundary enforcement | richer reporting для CI и triage |
| D — Contract Evolution & Integrations | `Done` | compatibility classification, baseline compare, deprecation lifecycle, integration boundary contracts | операционализация policy в release/process контуре |
| E — Productization | `In Progress` | release-state lifecycle, CLI/docs/test baseline, scaffold controls | release automation, onboarding path, production-ready observability |

## Ближайшие горизонты

### Horizon 1 — Diagnostics Contract Hardening (`Done`)

Статус: закрыт в change `009-diagnostics-contract`.

Результат:
- единый machine-readable envelope для `validate`, `diff`, `gen --check`, `gen`;
- стабилизированная taxonomy `validation.*|compatibility.*|generation.*|runtime.*|config.*`;
- выравненные drift/policy semantics между text/json режимами;
- обновленные reference docs и regression matrix.

### Horizon 2 — Release Automation

Цель: закрепить повторяемый release-процесс инструмента как repository-wide практику.

- Scope:
  - формализовать versioning/publish/checklist flow;
  - определить обязательные quality gates перед релизом;
  - выровнять release docs с фактическими CI-проверками.
- Критерии готовности:
  - reproducible release cycle без персонально-зависимых шагов;
  - прозрачный gate от тестов и contracts до публикации;
  - сокращение ручных действий при выпуске.

### Horizon 3 — Onboarding и Integration Playbook

Цель: уменьшить время интеграции APIDev в новый сервис.

- Scope:
  - пошаговый onboarding path для target app;
  - примеры wiring для handler/auth/error integration;
  - расширение e2e/contract сценариев под типовые профили внедрения.
- Критерии готовности:
  - новый сервис проходит путь от `init` до runnable skeleton по документации;
  - отсутствуют неявные integration шаги;
  - regressions в integration layer детектируются ранними тестами.

## KPI готовности

- `validate` на типовом проекте: < 2 сек для 100 контрактов;
- `gen --check` в CI: стабильный детерминированный результат без ложных срабатываний;
- доля ручных правок в generated-зоне: 0;
- время от нового контракта до runnable endpoint skeleton: < 10 минут.

## Связанные документы

- `docs/product/vision.md`
- `docs/architecture/architecture-overview.md`
- `docs/architecture/generated-integration.md`
- `docs/architecture/architecture-rules.md`
- `docs/reference/cli-contract.md`
- `docs/process/testing-strategy.md`
- `openspec/changes/006-safety-drift/specs/safety-drift/spec.md`
- `openspec/changes/007-update-domain-first-transport-layout/specs/transport-generation/spec.md`
- `openspec/changes/008-release-state/specs/contract-evolution-integration/spec.md`
