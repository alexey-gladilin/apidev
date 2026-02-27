# Дорожная Карта APIDev

Статус: `Historical`

Снимок состояния: 26 февраля 2026.

Этот документ не является нормативным описанием текущего поведения. Он фиксирует состояние проекта на дату снимка, основные gaps и направление развития.

## Что уже реализовано к дате снимка

- installable CLI binary `apidev`;
- команды `init`, `validate`, `diff`, `gen` и compatibility alias `generate`;
- базовый pipeline `load -> validate -> plan -> render -> write/check`;
- deterministic generation базовых generated-артефактов;
- write-boundary policy внутри configured generated root;
- drift check через `apidev gen --check`;
- архитектурные guardrail-тесты;
- unit, contract и integration test foundation.

## Основные gaps на дату снимка

- глубокая семантическая валидация контрактов еще не реализована;
- transport generation пока ограничен skeleton-уровнем;
- в generation plan отсутствует полноценный `REMOVE`;
- compatibility rules и `--fail-on-breaking` находятся в target state;
- machine-readable diagnostics и richer CLI observability еще не завершены;
- release automation не закреплена как repository-wide process.

## Текущая стадия

`MVP Foundation / Architecture Baseline Complete`

Проект уже пригоден как внутренний инструмент для init/validate/diff/gen workflow, но еще не завершил путь до production-grade transport generator полного цикла.

## Направление развития

### Этап A — Contract Validation Hardening

- строгая схема контракта;
- семантические проверки;
- диагностические коды;
- `--json` вывод.

### Этап B — Transport Generation MVP+

- request/response/error model generation;
- минимально runnable transport layer;
- стабильный operation registry и handler bridge contract.

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
