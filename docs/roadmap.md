# Дорожная Карта APIDev

Статус: `Historical`

Снимок состояния: 28 февраля 2026 (актуализация версии от 27 февраля 2026).

Этот документ не является нормативным описанием текущего поведения. Он фиксирует состояние проекта на дату снимка, основные gaps и направление развития.

## Что уже реализовано к дате снимка

- installable CLI binary `apidev`;
- команды `init`, `validate`, `diff`, `gen` и compatibility alias `generate`;
- базовый pipeline `load -> validate -> plan -> render -> write/check`;
- deterministic generation transport-артефактов (operation map, route wrappers, request/response/error schema templates, OpenAPI metadata);
- minimal runnable transport layer с explicit handler bridge contract;
- write-boundary policy внутри configured generated root;
- drift check через `apidev gen --check`;
- compatibility classification, baseline/deprecation semantics и policy-режимы для `diff` и `gen --check`;
- архитектурные guardrail-тесты;
- unit, contract и integration test foundation.

## Основные gaps на дату снимка

- глубокая семантическая валидация контрактов еще не реализована;
- в generation plan отсутствует полноценный `REMOVE`;
- machine-readable diagnostics и richer CLI observability еще не завершены;
- контрактно-ориентированные тестовые заготовки пока находятся в target state (следующие фазы);
- release automation не закреплена как repository-wide process.

## Текущая стадия

`Safety/Compatibility Baseline Complete`

Проект реализует этапы A+B+C+D (contract validation hardening, transport generation MVP+, safety/drift governance, contract evolution integration) и находится в переходе к productization-фокусу этапа E.

## Статус этапов (что сделано / что впереди)

| Этап | Статус на 28 февраля 2026 | Что уже реализовано | Что осталось |
|---|---|---|---|
| A — Contract Validation Hardening | `Done` | schema validation, базовые semantic checks, diagnostics foundation | углубление semantic-правил и richer diagnostics |
| B — Transport Generation MVP+ | `Done` | operation map/registry, route wrappers, request/response/error schema templates, OpenAPI metadata, handler bridge contract | расширение generated surface в сторону test scaffolds (следующие фазы) |
| C — Diff/Generate Safety & Drift Governance | `Done` | validate-first pipeline, read-only semantics для `diff` и `gen --check`, write-boundary policy, deterministic plan/apply | полноценный `REMOVE` в generation plan и richer dry-run/reporting |
| D — Contract Evolution & Integrations | `Done` | compatibility classification, baseline snapshot contract, deprecation policy, policy modes | дальнейшая операционализация в release-процессе и observability |
| E — Productization | `Planned` | baseline для CLI/docs/tests уже есть | release automation, onboarding path, расширенные e2e/contract кейсы |

## Направление развития

### Этап A — Contract Validation Hardening

- статус: `Done (baseline), Next: semantic deepening`;
- строгая схема контракта;
- семантические проверки;
- диагностические коды;
- `--json` вывод.

### Этап B — Transport Generation MVP+

- статус: `Done (27 февраля 2026)`;
- реализованы request/response/error schema template generation;
- реализован минимально runnable transport layer;
- реализованы стабильные operation map/registry и handler bridge contract;
- перед implementation использовать research-артефакт:
`openspec/changes/001-contract-validation/artifacts/research/2026-02-27-external-api-codegen-baseline.md`
как baseline структуры и style guardrails для шаблонов генерации.

### Этап C — Diff/Generate Safety & Drift Governance

- статус: `Done (28 февраля 2026)`;
- validate-first и read-only semantics для `diff` и `gen --check`;
- write-boundary enforcement и deterministic planning/apply;
- нормализованные drift-status и exit semantics.

### Этап D — Contract Evolution & Integrations

- статус: `Done (28 февраля 2026)`;
- compatibility classification (`non-breaking`, `potentially-breaking`, `breaking`);
- formal deprecation policy, baseline snapshot contract, configurable compatibility policy.

## Интеграция сгенерированных артефактов

Интеграция в целевую кодовую базу строится вокруг жесткой границы ownership между generated и manual зонами.

### 1. Как артефакты попадают в target app

- APIDev читает пути contracts/templates/generated из единого config source (`.apidev/config.toml`, см. AR-007).
- `apidev diff` строит план изменений без записи файлов.
- `apidev gen` применяет только `ADD/UPDATE` внутри configured generated root.
- `apidev gen --check` проверяет drift без записи.
- Любая запись за пределами generated root считается нарушением write-boundary policy (AR-006).

### 2. Связь generated transport и manual handlers

- Generated transport публикует стабильный operation map/registry и route wrappers для runtime wiring.
- Generated router слой обращается к manual-реализациям только через handler bridge contract.
- Wiring выполняется через явные import paths между generated transport-модулями и manual bridge-слоем target приложения.
- Отсутствующая bridge-реализация должна проявляться детерминированно в интеграционном контуре, без silent fallback.
- Generated слой формирует точки интеграции (integration points) для:
  - подключения manual handler implementations;
  - auth wiring на transport-границе;
  - error handling и mapping transport/domain ошибок в контрактный формат ответа.

### 3. Границы ответственности

- Генерируется: transport skeleton, operation map/registry, route wrappers, request/response/error schema templates, OpenAPI metadata.
- Генерируется: explicit integration points для handler wiring, auth wiring и error mapping на transport-уровне.
- Ручной код: бизнес-правила, domain/use-case логика, data access, auth/policy на уровне домена, интеграции с внешними системами.
- Граница проходит по handler bridge: generated слой задает стабильные контракты вызова, manual слой владеет реализацией поведения.
- В следующих фазах roadmap добавляются контрактно-ориентированные тестовые заготовки как generated-only артефакты.

### Этап E — Productization

- статус: `Planned`;
- release checklist и automation;
- onboarding documentation;
- расширенные e2e и contract кейсы.

## Ближайшие шаги планирования

### Horizon 1 — Safety/Drift Completion (ближайший цикл)

Цель: закрыть критичный функциональный gap в детерминированной эволюции generated-зоны.

- Scope:
  - добавить полноценный `REMOVE` в generation plan с сохранением write-boundary;
  - синхронизировать поведение `diff` и `gen --check` для удалений;
  - зафиксировать expected diagnostics при удалении и конфликтных сценариях.
- Артефакты результата:
  - обновленный roadmap/status;
  - OpenSpec traceability в change-пакете safety/governance;
  - обновленный verification checklist в testing strategy/CLI contract (без противоречий).
- Критерии готовности:
  - deterministic diff для сценариев удаления;
  - отсутствие записи вне generated root;
  - предсказуемый CI-gate при drift с удалениями.

### Horizon 2 — Integration Contracts Expansion

Цель: сделать интеграционный контур target app более явным и повторяемым.

- Scope:
  - расширить описанный контракт integration points между generated transport и manual bridge;
  - формализовать integration points для handler wiring, auth wiring, error mapping;
  - зафиксировать допустимые точки расширения без нарушения ownership boundary.
- Артефакты результата:
  - обновленный integration-раздел roadmap;
  - синхронизация формулировок с `vision.md`, `architecture-overview.md`, glossary (`bridge layer`);
  - согласованный integration walkthrough на уровне документации процесса.
- Критерии готовности:
  - у каждой generated operation есть однозначная точка вызова manual bridge;
  - auth/error integration описаны как explicit transport boundary contract;
  - отсутствуют неявные fallback-механизмы.

### Horizon 3 — Observability и CI-Ready Diagnostics

Цель: повысить управляемость pipeline в CI и ускорить triage регрессий.

- Scope:
  - machine-readable diagnostics для validate/diff/gen-check;
  - richer dry-run/check отчеты для drift/compatibility/deprecation;
  - нормализация кодов и структуры сигналов для автоматизированных quality gates.
- Артефакты результата:
  - согласованный diagnostics contract в reference-документации;
  - обновленные CI-гайды и минимальные regression-сценарии;
  - единые примеры интерпретации diagnostics для команды.
- Критерии готовности:
  - CI может надежно парсить и классифицировать результаты pipeline;
  - ручной разбор логов для типовых сценариев минимизирован;
  - diagnostics стабильны между повторными запусками на одинаковом входе.

### Horizon 4 — Productization и Onboarding

Цель: закрепить APIDev как регулярный engineering-процесс, а не ad-hoc tool usage.

- Scope:
  - release automation (versioning, quality gates, publish checklist);
  - onboarding path для интеграции generated transport в target app;
  - расширенные e2e/contract наборы под типовые интеграционные профили.
- Артефакты результата:
  - формализованный release playbook;
  - reproducible onboarding walkthrough;
  - матрица e2e/contract сценариев для продуктовых команд.
- Критерии готовности:
  - новый сервис интегрирует APIDev по documented path без ручного reverse engineering;
  - release cycle воспроизводим и не зависит от персонального знания;
  - доля ручных исправлений в generated-зоне остается нулевой.

## KPI готовности

- `validate` на типовом проекте: < 2 сек для 100 контрактов;
- `gen --check` в CI: стабильный детерминированный результат без ложных срабатываний;
- доля ручных правок в generated-зоне: 0;
- время от нового контракта до runnable endpoint skeleton: < 10 минут.

## Связанные документы

- `docs/product/vision.md`
- `docs/architecture/architecture-overview.md`
- `docs/architecture/architecture-rules.md`
- `docs/reference/cli-contract.md`
- `docs/process/testing-strategy.md`
- `openspec/changes/001-contract-validation/artifacts/research/2026-02-27-external-api-codegen-baseline.md`
- `openspec/changes/002-transport-generation/artifacts/design/01-architecture.md`
- `openspec/changes/002-transport-generation/artifacts/design/02-behavior.md`
- `openspec/changes/005-contract-evolution-integration/specs/contract-evolution-integration/spec.md`
