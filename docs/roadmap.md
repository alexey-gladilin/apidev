# Дорожная Карта APIDev

Статус: `Historical`

Снимок состояния: 27 февраля 2026.

Этот документ не является нормативным описанием текущего поведения. Он фиксирует состояние проекта на дату снимка, основные gaps и направление развития.

## Что уже реализовано к дате снимка

- installable CLI binary `apidev`;
- команды `init`, `validate`, `diff`, `gen` и compatibility alias `generate`;
- базовый pipeline `load -> validate -> plan -> render -> write/check`;
- deterministic generation transport-артефактов (operation registry, routers, request/response/error models);
- minimal runnable transport layer с explicit handler bridge contract;
- write-boundary policy внутри configured generated root;
- drift check через `apidev gen --check`;
- архитектурные guardrail-тесты;
- unit, contract и integration test foundation.

## Основные gaps на дату снимка

- глубокая семантическая валидация контрактов еще не реализована;
- в generation plan отсутствует полноценный `REMOVE`;
- compatibility rules и `--fail-on-breaking` находятся в target state;
- machine-readable diagnostics и richer CLI observability еще не завершены;
- release automation не закреплена как repository-wide process.

## Текущая стадия

`Transport Generation MVP+ Complete`

Проект реализует этапы A+B (contract validation hardening + transport generation MVP+) и готов для следующего шага по safety/drift governance этапа C.

## Направление развития

### Этап A — Contract Validation Hardening

- строгая схема контракта;
- семантические проверки;
- диагностические коды;
- `--json` вывод.

### Этап B — Transport Generation MVP+

- статус: `Done (27 февраля 2026)`;
- реализованы request/response/error model generation;
- реализован минимально runnable transport layer;
- реализованы стабильный operation registry и handler bridge contract;
- перед implementation использовать research-артефакт:
  `openspec/changes/001-contract-validation/artifacts/research/2026-02-27-external-api-codegen-baseline.md`
  как baseline структуры и style guardrails для шаблонов генерации.

### Этап C — Diff/Generate Safety & Drift Governance

- `REMOVE` в generation plan;
- richer dry-run/check отчеты;
- breaking-aware safety modes.

### Этап D — Contract Evolution & Integrations

- compatibility classification;
- optional `dbspec` integration;
- formal deprecation policy.

### Этап E — Productization

- release checklist и automation;
- onboarding documentation;
- расширенные e2e и contract кейсы.

## KPI готовности

- `validate` на типовом проекте: < 2 сек для 100 контрактов;
- `gen --check` в CI: стабильный детерминированный результат без ложных срабатываний;
- доля ручных правок в generated-зоне: 0;
- время от нового контракта до runnable endpoint skeleton: < 10 минут.

## Связанные документы

- `docs/product/vision.md`
- `docs/reference/cli-contract.md`
- `docs/process/testing-strategy.md`
- `openspec/changes/001-contract-validation/artifacts/research/2026-02-27-external-api-codegen-baseline.md`
